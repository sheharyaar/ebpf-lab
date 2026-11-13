#!/bin/bash
# Chapter "schedext" (struct_ops through sched_ext): every run behind the chapter's numbers.
#   1. scx_simple from tools/sched_ext of the v7.2 tree: sysfs, bpftool, the loader's bpf() calls, the trampolines
#   2. the write counter under scx_simple (unchanged, from book/program/maps/02-hash-map)
#   3. load and unload time of scx_simple, five runs
#   4. perf bench sched messaging and pipe, and pipe under a CPU hog per vCPU: fair class, scx_simple, scx_simple -f
#   5. per-callback cost (kernel.bpf_stats_enabled) and memory of the scheduler
#   6. failures: a dispatch that never moves a task, scx_bpf_error(), two wrong signatures, a sleepable enqueue
#   7. failures: an empty name, a second scheduler, the loader killed, sysrq-S; tcp_congestion_ops with and without ssthresh
#   STEPS="1 6" runs only those steps.
# Build on the host (no root; clang, gcc, make, python3, libelf and zlib headers; the v7.2 tree in $KSRC).
# A sparse clone of the tree needs these paths as well (git sparse-checkout add ...): tools/sched_ext tools/lib/bpf
#   tools/bpf/bpftool tools/include tools/build tools/scripts tools/arch/x86 tools/lib/subcmd /tools/lib/*.c
#   /scripts/Makefile.include /scripts/subarch.include /scripts/bpf_doc.py include/uapi/linux/bpf.h
#   bash book/labs/schedext-root.sh build
# Then, as root in a throwaway VM:
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- 'bash /tmp/schedext-w/schedext-root.sh'
# Output: /tmp/book-labs/schedext/*.txt
HERE=$(cd "$(dirname "$0")" && pwd)
KSRC=${KSRC:-/tmp/linux-src-iTa3/linux}
W=/tmp/schedext-w
O=/tmp/book-labs/schedext
B=$W/build

if [ "${1:-}" = build ]; then
  mkdir -p $W/var && cp "$0" $W/schedext-root.sh && cd $W || exit 1
  # the tree's own build: libbpf, bpftool, vmlinux.h, the schedulers (about 7 s on 16 cores)
  make -C $KSRC/tools/sched_ext O=$W -j"$(nproc)" scx_simple scx_qmap scx_sdt > build.txt 2>&1 || { tail build.txt; exit 1; }
  S=$KSRC/tools/sched_ext
  BPF_CFLAGS="-g -D__TARGET_ARCH_x86 -mlittle-endian -I$S/include -I$S/include/bpf-compat -I$B/include \
    -I$KSRC/tools/include/uapi -Wall -Wno-compare-distinct-pointer-types -Wno-microsoft-anon-tag -fms-extensions \
    -O2 -mcpu=v3 -target bpf"
  CFLAGS="-g -O2 -pthread -Wall -I$B/include -I$KSRC/tools/lib -I$KSRC/tools/include -I$KSRC/tools/include/uapi -I$S/include"
  # one change each to scx_simple.bpf.c; the loader scx_simple.c is used unchanged with each variant's skeleton
  var() {  # $1 = name, rest = sed arguments
    local n=$1; shift
    mkdir -p var/$n
    sed "$@" $S/scx_simple.bpf.c > var/$n/$n.bpf.c
    clang $BPF_CFLAGS -c var/$n/$n.bpf.c -o var/$n/$n.bpf.o 2>> var/build.txt || { echo "clang failed: $n" >> var/build.txt; return; }
    $B/sbin/bpftool gen object var/$n/$n.l.o var/$n/$n.bpf.o
    $B/sbin/bpftool gen skeleton var/$n/$n.l.o name scx_simple > var/$n/scx_simple.bpf.skel.h
    gcc -iquote var/$n $CFLAGS -c $S/scx_simple.c -o var/$n/loader.o
    gcc -o var/$n/simple_$n var/$n/loader.o $W/build/obj/libbpf/libbpf.a -lelf -lz -lpthread
    diff -u $S/scx_simple.bpf.c var/$n/$n.bpf.c | tail -n +3 > var/$n/$n.diff
  }
  : > var/build.txt
  # a dispatch that never moves a task out of the shared DSQ
  var stall -e 's|^\tscx_bpf_dsq_move_to_local(SHARED_DSQ, 0);|\t/* bug: no task ever leaves SHARED_DSQ */|'
  # scx_bpf_error() on the thousandth enqueue
  var scxerr -e 's|^static u64 vtime_now;|&\nstatic u64 nr_enq;|' \
    -e 's|^\tstat_inc(1);\t/\* count global queueing \*/|&\n\tif (++nr_enq == 1000)\n\t\tscx_bpf_error("enqueue %llu: giving up on purpose", nr_enq);|'
  # enqueue declared with an argument the member does not have
  var extraarg -e 's|simple_enqueue, struct task_struct \*p, u64 enq_flags)|simple_enqueue, struct task_struct *p, u64 enq_flags, u64 extra)|' \
    -e 's|^\tstat_inc(1);\t/\* count global queueing \*/|&\n\tenq_flags \|= extra;|'
  # dispatch with its two arguments swapped, so the CPU number is read as a task pointer
  var swapargs -e 's|simple_dispatch, s32 cpu, struct task_struct \*prev)|simple_dispatch, struct task_struct *prev, s32 cpu)|' \
    -e 's|^\tscx_bpf_dsq_move_to_local(SHARED_DSQ, 0);|\tif (prev \&\& prev->pid == 1)\n\t\treturn;\n&|'
  # a sleepable program in a member that runs with the runqueue lock held
  var sleepy -e 's|^void BPF_STRUCT_OPS(simple_enqueue|void BPF_STRUCT_OPS_SLEEPABLE(simple_enqueue|'
  # an empty name, the one member sched_ext requires
  var noname -e 's|\.name\([[:space:]]*\)= "simple"|.name\1= ""|'
  # tcp_congestion_ops, with and without ssthresh
  cp "$HERE/schedext/tcp_mini.bpf.c" $B/include/vmlinux.h $W/
  clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -Wno-missing-declarations -I$W -I$B/include -c tcp_mini.bpf.c -o tcp_mini.bpf.o 2>> var/build.txt
  clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -DNO_SSTHRESH -I$W -I$B/include -c tcp_mini.bpf.c -o tcp_noss.bpf.o 2>> var/build.txt
  cp "$HERE/../program/maps/02-hash-map/hashmap.bpf.o" $W/
  # a busy loop for the CPU hogs
  printf 'int main(void){for(;;);}\n' > spin.c && gcc -O2 -o spin spin.c
  ls var/*/simple_* tcp_*.bpf.o $B/bin/
  cat var/build.txt
  exit 0
fi

[ "$(id -u)" = 0 ] || { echo "run as root inside the VM"; exit 1; }
mkdir -p $O && cd $W || exit 1
mount -t bpf bpf /sys/fs/bpf 2>/dev/null
STEPS=${STEPS:-1 2 3 4 5 6 7}
run() { case " $STEPS " in *" $1 "*) return 0 ;; esac; return 1; }
now() { date +%s%N; }
wait_state() {  # $1 = enabled|disabled; prints milliseconds waited (gives up after 60 s)
  local t0=$(now)
  until [ "$(cat /sys/kernel/sched_ext/state)" = "$1" ]; do
    [ $(( ($(now) - t0) / 1000000 )) -gt 60000 ] && { echo timeout; return 1; }
    sleep 0.002
  done
  echo $(( ($(now) - t0) / 1000000 ))
}
start_simple() {  # $@ = extra arguments; leaves $SP set
  $B/bin/scx_simple "$@" > $W/simple.out 2>&1 & SP=$!
  wait_state enabled > /dev/null
}
stop_simple() { kill -INT $SP 2>/dev/null; wait $SP 2>/dev/null; wait_state disabled > /dev/null; }

if run 1; then
  exec > $O/1-see.txt 2>&1
  echo "## kernel $(uname -r), $(nproc) vCPUs, $(date -I)"
  echo "## before"; cat /sys/kernel/sched_ext/state; grep -H . /sys/kernel/sched_ext/enable_seq
  strace -f -e trace=bpf -s 64 -o $W/strace.txt $B/bin/scx_simple > $W/simple.out 2>&1 & SP=$!
  wait_state enabled > /dev/null
  echo "## after the loader started"
  grep -H . /sys/kernel/sched_ext/state /sys/kernel/sched_ext/root/ops /sys/kernel/sched_ext/enable_seq /sys/kernel/sched_ext/switch_all
  ls /sys/kernel/sched_ext /sys/kernel/sched_ext/root
  echo "## root/events"; cat /sys/kernel/sched_ext/root/events
  echo "## this shell"; grep ext /proc/$$/sched
  echo "## struct_ops list"; bpftool struct_ops list
  echo "## struct_ops dump (members with a program)"; bpftool struct_ops dump name simple_ops | grep -E 'prog_id|"state"|"type"|value_size|"name"'
  echo "## prog show"; bpftool prog show | grep -A3 ': struct_ops'
  echo "## link and map"; bpftool link show; bpftool map show
  echo "## trampolines in kallsyms"; grep -E 'bpf__sched_ext_ops_' /proc/kallsyms | sort
  sleep 3; pkill -INT -x scx_simple; wait $SP
  echo "## loader output"; cat $W/simple.out
  echo "## bpf() calls of the loader (strace)"
  grep -oE 'bpf\(BPF_[A-Z_]+|map_type=BPF_MAP_TYPE_[A-Z_]+|prog_type=BPF_PROG_TYPE_STRUCT_OPS|prog_name="[a-z_]+"|expected_attach_type=[A-Z_0-9x]+|attach_type=BPF_STRUCT_OPS|= -?[0-9]+$' $W/strace.txt | tr '\n' ' ' | sed 's/ bpf(/\nbpf(/g'
  echo; echo "## dmesg"; dmesg | grep sched_ext | tail -3
fi

if run 2; then
  exec > $O/2-counter.txt 2>&1
  bpftool prog load hashmap.bpf.o /sys/fs/bpf/sx_wc autoattach || exit 1
  sysctl -q -w kernel.bpf_stats_enabled=1
  for cls in fair simple; do
    [ $cls = simple ] && start_simple
    bpftool prog show name count_writes | grep -o 'run_time_ns [0-9]* run_cnt [0-9]*' > $W/before
    sh -c 'grep ext.enabled /proc/self/sched; dd if=/dev/zero of=/dev/null bs=1 count=200000 2>&1 | tail -1' &
    P=$!; wait $P
    bpftool prog show name count_writes | grep -o 'run_time_ns [0-9]* run_cnt [0-9]*' > $W/after
    read _ t0 _ c0 < $W/before; read _ t1 _ c1 < $W/after
    echo "$cls: count_writes ran $((c1 - c0)) times, $(( (t1 - t0) / (c1 - c0) )) ns a run, state $(cat /sys/kernel/sched_ext/state)"
    [ $cls = simple ] && stop_simple
  done
  echo "map entries with 200000 or more writes:"; bpftool -j map dump name write_counts | grep -oE '"value": ?[0-9]+' | awk -F: '$2>=200000' | head
  sysctl -q -w kernel.bpf_stats_enabled=0
  rm -f /sys/fs/bpf/sx_wc
fi

if run 3; then
  exec > $O/3-loadtime.txt 2>&1
  for i in 1 2 3 4 5; do
    t0=$(now); $B/bin/scx_simple > /dev/null 2>&1 & SP=$!
    up=$(wait_state enabled)
    sleep 1
    t1=$(now); kill -INT $SP; down=$(wait_state disabled); wait $SP
    echo "run $i: start to enabled ${up} ms, SIGINT to disabled ${down} ms"
  done
  dmesg | grep 'sched_ext: BPF scheduler' | tail -4
fi

bench() {  # $1 = label
  local l=$1 i
  for i in 1 2 3 4 5; do
    echo "$l messaging $(perf bench sched messaging -g 10 -l 200 2>&1 | grep 'Total time' | grep -oE '[0-9.]+') s"
  done
  for i in 1 2 3 4 5; do
    echo "$l pipe $(perf bench sched pipe -l 200000 2>&1 | grep 'usecs/op' | grep -oE '[0-9.]+ usecs/op')"
  done
  local n=$(nproc) pids=""
  for i in $(seq $n); do ./spin & pids="$pids $!"; done
  sleep 1
  for i in 1 2 3; do
    echo "$l pipe-under-load $(timeout 90 perf bench sched pipe -l 300 2>&1 | grep 'usecs/op' | grep -oE '[0-9.]+ usecs/op')"
  done
  kill $pids; wait $pids 2>/dev/null
}

if run 4; then
  exec > $O/4-bench.txt 2>&1
  echo "## kernel $(uname -r), $(nproc) vCPUs, $(date -I)"
  bench fair
  start_simple; bench simple; stop_simple
  start_simple -f; bench simple-fifo; stop_simple
fi

if run 5; then
  exec > $O/5-cost.txt 2>&1
  m0=$(grep -E '^(Percpu|Slab|MemAvailable):' /proc/meminfo | tr -s ' ' | tr '\n' ' ')
  sysctl -q -w kernel.bpf_stats_enabled=1
  start_simple
  m1=$(grep -E '^(Percpu|Slab|MemAvailable):' /proc/meminfo | tr -s ' ' | tr '\n' ' ')
  perf bench sched messaging -g 10 -l 200 > /dev/null 2>&1
  perf bench sched pipe -l 200000 > /dev/null 2>&1
  echo "## per program, after messaging and pipe"
  bpftool prog show | grep -A1 ': struct_ops' | paste - - - 2>/dev/null | \
    awk '{n="";t=0;c=0;for(i=1;i<=NF;i++){if($i=="name")n=$(i+1);if($i=="run_time_ns")t=$(i+1);if($i=="run_cnt")c=$(i+1)}; if(c>0) printf "%-18s run_cnt %10d  %6.1f ns a run\n", n, c, t/c; else printf "%-18s run_cnt 0\n", n}'
  echo "## memlock"; bpftool -j prog show | grep -oE '"name":"simple_[a-z_]+"|"bytes_memlock":[0-9]+' | paste - -
  bpftool -j map show | grep -oE '"name":"[a-z_.]+"|"bytes_memlock":[0-9]+|"type":"[a-z_]+"' | paste - - -
  echo "## loader RSS"; grep -E 'VmRSS' /proc/$SP/status
  echo "## meminfo before: $m0"; echo "## meminfo loaded: $m1"
  stop_simple
  sysctl -q -w kernel.bpf_stats_enabled=0
fi

if run 6; then
  exec > $O/6-wrong.txt 2>&1
  V=$W/var
  echo "## stall: dispatch never moves a task (watchdog default 30 s)"
  t0=$(now); $V/stall/simple_stall > $W/stall.out 2>&1 & SP=$!
  wait_state enabled > /dev/null
  # two busy loops pinned to one CPU: the first keeps the CPU, the second waits in SHARED_DSQ
  taskset -c 5 ./spin & S1=$!; sleep 0.5; taskset -c 5 ./spin & S2=$!
  for i in $(seq 70); do [ "$(cat /sys/kernel/sched_ext/state)" = disabled ] && break; sleep 1; done
  t1=$(now); echo "state $(cat /sys/kernel/sched_ext/state) after $(( (t1 - t0) / 1000000 )) ms"
  [ "$(cat /sys/kernel/sched_ext/state)" = enabled ] && { echo "no ejection: sysrq-S"; echo S > /proc/sysrq-trigger; }
  kill $S1 $S2; wait $SP
  tr -d '\0' < $W/stall.out | grep -v '^local=' | head -40
  dmesg | grep -E 'sched_ext' | tail -4
  grep -E '^EXIT' $W/stall.out
  echo "## scx_bpf_error on the 1000th enqueue"
  $V/scxerr/simple_scxerr > $W/err.out 2>&1 & SP=$!
  wait_state enabled > /dev/null
  for i in 1 2 3 4 5; do
    [ "$(cat /sys/kernel/sched_ext/state)" = disabled ] && break
    perf bench sched messaging -g 4 -l 50 > /dev/null 2>&1
  done
  [ "$(cat /sys/kernel/sched_ext/state)" = enabled ] && kill -INT $SP
  wait $SP; tr -d '\0' < $W/err.out | grep -v '^local=' | head -12; grep -E '^EXIT' $W/err.out; dmesg | grep -A1 'sched_ext' | tail -4
  for v in extraarg swapargs sleepy; do
    echo "## $v"
    timeout 30 $V/$v/simple_$v 2>&1 | grep -vE '^local=|^libbpf: prog .*: -- BEGIN|^libbpf: prog .*: -- END' | \
      grep -E 'libbpf|func |R[0-9]|invalid|unsupported|attach|Error|error|EXIT|failed|^[0-9]+: ' | tail -12
    echo "state: $(cat /sys/kernel/sched_ext/state)"
  done
fi

if run 7; then
  exec > $O/7-wrong.txt 2>&1
  V=$W/var
  echo "## noname"
  timeout 30 $V/noname/simple_noname 2>&1 | grep -v '^local=' | tail -6; dmesg | tail -2
  echo "## a second scheduler while one runs"
  start_simple
  timeout 30 $B/bin/scx_simple 2>&1 | tail -4
  echo "state: $(cat /sys/kernel/sched_ext/state), ops $(cat /sys/kernel/sched_ext/root/ops)"
  dmesg | grep -iE 'sched_ext' | tail -2
  echo "## the loader killed with SIGKILL"
  kill -KILL $SP; wait $SP 2>/dev/null; echo "waited $(wait_state disabled) ms for disabled"
  dmesg | grep sched_ext | tail -1
  echo "## sysrq-S"
  start_simple; echo S > /proc/sysrq-trigger; echo "waited $(wait_state disabled) ms"; wait $SP
  tail -3 $W/simple.out; dmesg | grep -E 'sysrq|sched_ext' | tail -3
  echo "## tcp_congestion_ops without ssthresh"
  bpftool struct_ops register tcp_noss.bpf.o 2>&1 | tail -3; dmesg | tail -1
  echo "## tcp_congestion_ops complete, link pinned"
  mkdir -p /sys/fs/bpf/sx_tcp
  bpftool struct_ops register tcp_mini.bpf.o /sys/fs/bpf/sx_tcp 2>&1 | tail -2
  echo "after bpftool exited: $(cat /proc/sys/net/ipv4/tcp_available_congestion_control)"
  bpftool struct_ops list; ls /sys/fs/bpf/sx_tcp; grep bpf__tcp_congestion_ops /proc/kallsyms | sort
  rm -rf /sys/fs/bpf/sx_tcp; sleep 0.5
  echo "after the pin was removed: $(cat /proc/sys/net/ipv4/tcp_available_congestion_control)"
fi
