#!/bin/bash
# Chapter 15: choosing a map. Memory, update cost under sharing, streaming, and what each
# context may use, measured on one kernel.
# Build on the host (no root):  bash book/labs/ch15-root.sh build      (run `make` in book/program first)
# Then, as root in a throwaway VM:
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- 'bash /tmp/c15/ch15-root.sh'
# Output: /tmp/book-labs/ch15/*.txt
#   versions.txt  kernel, CPUs, preemption mode
#   mem.txt       memlock from fdinfo and memory-cgroup charge per map layout at 1,024 entries
#   upd.txt       ns per event for ten ways of counting, 1 and 8 writers, own key and shared key;
#                 five rounds each, round 0 is a warm-up and is left out of the medians
#   stream.txt    ring buffer against perf buffer: events, losses, reader wake-ups and switches
#   reenter.txt   a nested update of a hash whose bucket lock this CPU already holds
#   lock.txt      the counter with a bpf_spin_lock at a tracepoint, at fentry, and with a call inside
#   sleep.txt     a sleepable program with a perf buffer, then with a ring buffer (logs in load-*.txt)
#   jit-atomic.txt  __sync_fetch_and_add() on a map value, after the verifier and after the JIT
#   lab.txt       lab 15.1: the counter as written, without bpf_printk, and with the chosen map
# Arguments after the VM command line: none = everything; "mem" = step 1 and the lab; "lab" = the lab only.
# On the host, `bash book/labs/ch15-root.sh hostclock` (no root) runs one, then eight, busy loops
# and prints the core clocks: this book's laptop held one busy core near 5 GHz but every core
# near 870 MHz once eight were busy, which inflates every eight-writer number in upd.txt.
HERE=$(cd "$(dirname "$0")" && pwd)
W=/tmp/c15
CF="-g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I."
if [ "${1:-}" = hostclock ]; then
  cd $W || exit 1
  taskset -c 2 ./spin u 300000000
  for c in 0 2 4 6 8 10 12 14; do taskset -c $c ./spin u 1000000000 & done
  sleep 1.5; echo "MHz with eight busy: $(grep MHz /proc/cpuinfo | awk '{printf "%d ", $4}')"; wait
  exit 0
fi
if [ "${1:-}" = build ]; then
  set -e
  mkdir -p $W && cp "$0" $W/ch15-root.sh && cp "$HERE"/ch15/* $W/
  cp "$HERE/../program/vmlinux.h" $W/
  cp "$HERE/../program/maps/02-hash-map/hashmap.bpf.o" $W/
  cd $W
  # the counter as written, minus its bpf_printk line, for the lab
  sed -e '/bpf_printk/d' -e 's#"../../vmlinux.h"#"vmlinux.h"#' \
      "$HERE/../program/maps/02-hash-map/hashmap.bpf.c" > wc_noprintk.bpf.c
  for o in upd stream reenter counter_lru wc_noprintk; do clang $CF -c $o.bpf.c -o $o.bpf.o; done
  clang $CF -DHOOK_TP -c lock.bpf.c -o lock_tp.bpf.o
  clang $CF -DHOOK_FE -c lock.bpf.c -o lock_fe.bpf.o
  clang $CF -DHOOK_FE -DCALL_INSIDE -c lock.bpf.c -o lock_call.bpf.o
  clang $CF -DPERF -c sleep.bpf.c -o sleep_perf.bpf.o
  clang $CF -c sleep.bpf.c -o sleep_rb.bpf.o
  gcc -O2 -Wall bench.c -o bench -lbpf -lpthread
  gcc -O2 -Wall stream.c -o stream -lbpf -lpthread
  gcc -O2 -Wall mem.c -o mem -lbpf
  gcc -O2 -Wall spin.c -o spin
  cat > wloop.c <<'EOF'
#include <fcntl.h>
#include <stdlib.h>
#include <unistd.h>
int main(int argc, char **argv) { long n = atol(argv[1]); int fd = open("/dev/null", O_WRONLY);
  for (long i = 0; i < n; i++) write(fd, "x", 1); return 0; }
EOF
  gcc -O2 wloop.c -o wloop
  cat > msum.py <<'EOF'
import json, sys
t = 0
for e in json.load(sys.stdin):
    v = e.get('formatted', e)['value']
    t += v if isinstance(v, int) else int.from_bytes(bytes(int(x, 16) for x in v), 'little')
print(t)
EOF
  echo "built in $W"
  exit 0
fi

set -u
ONLY=${1:-all}
OUT=/tmp/book-labs/ch15; mkdir -p $OUT; cd $W || exit 1
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
mountpoint -q /sys/kernel/debug || mount -t debugfs debugfs /sys/kernel/debug
{ uname -r; echo "nproc $(nproc)"; echo "preempt: $(cat /sys/kernel/debug/sched/preempt)"
  grep -m1 'model name' /proc/cpuinfo; bpftool version | head -1; clang --version | head -1
} > $OUT/versions.txt 2>&1

if [ "$ONLY" = all ] || [ "$ONLY" = mem ]; then
# 1. memory per layout: fdinfo's memlock, and what the memory cgroup was charged
echo +memory > /sys/fs/cgroup/cgroup.subtree_control
mkdir -p /sys/fs/cgroup/c15
bash -c "echo \$\$ > /sys/fs/cgroup/c15/cgroup.procs; exec ./mem /sys/fs/cgroup/c15" > $OUT/mem.txt 2>&1
bpftool map show > /dev/null   # nothing left: mem's maps closed with it
fi
if [ "$ONLY" = all ]; then

# 2. ns per event for each way of counting; mode 0 own key, 1 shared key, 2 arrays one line each
: > $OUT/upd.txt
for mode in 0 1; do
  ./bench upd.bpf.o $mode 1 1000000 5 >> $OUT/upd.txt 2>&1
  ./bench upd.bpf.o $mode 8 500000 5 >> $OUT/upd.txt 2>&1
done
./bench upd.bpf.o 2 8 500000 5 t_empty t_arr_atomic t_arr_plain t_pcarr >> $OUT/upd.txt 2>&1

# 3. streaming: ring buffer and perf buffer, full speed and one event per 20 us per writer
: > $OUT/stream.txt
for pace in 0 20000; do
  for n in 1 4; do
    [ $pace = 0 ] && calls=1000000 || calls=100000
    for m in rb rbnw pb pb64; do ./stream stream.bpf.o $m $n $calls $pace >> $OUT/stream.txt 2>&1; done
  done
done

# 4. a nested update on a bucket this CPU has locked
{
  bpftool prog load reenter.bpf.o /sys/fs/bpf/re autoattach && echo "loaded"
  Z="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"
  bpftool map update name htab key 0 0 0 0 value $Z && echo "first update (insert): ok"
  bpftool map update name htab key 0 0 0 0 value $Z && echo "second update (replace): ok"
  bpftool map dump name reenter.data
  bpftool map dump name reenter.bss
  grep -w EDEADLK /usr/include/asm-generic/errno.h
  rm -f /sys/fs/bpf/re
} > $OUT/reenter.txt 2>&1

# 5. bpf_spin_lock: refused at a tracepoint, accepted at fentry, no calls while held
# 6. a sleepable program may use a ring buffer and may not use a perf buffer
# (full output in load-*.txt; the verdicts in lock.txt and sleep.txt)
for v in lock_tp lock_fe lock_call sleep_perf sleep_rb; do
  bpftool prog load $v.bpf.o /sys/fs/bpf/t_$v > $OUT/load-$v.txt 2>&1; echo "exit $?" >> $OUT/load-$v.txt
  rm -f /sys/fs/bpf/t_$v
done
for v in lock_tp lock_fe lock_call; do echo "--- $v"; grep -E 'cannot|not allowed|exit' $OUT/load-$v.txt; done > $OUT/lock.txt
for v in sleep_perf sleep_rb; do echo "--- $v"; grep -E 'Sleepable|cannot|exit' $OUT/load-$v.txt; done > $OUT/sleep.txt

# what the JIT made of the atomic add in place
bpftool prog loadall upd.bpf.o /sys/fs/bpf/u15 > /dev/null 2>&1
{ echo "--- xlated t_hash_atomic"; bpftool prog dump xlated pinned /sys/fs/bpf/u15/t_hash_atomic | grep -E 'lock|call'
  echo "--- jited t_hash_atomic"; bpftool prog dump jited pinned /sys/fs/bpf/u15/t_hash_atomic | grep -E 'lock'
} > $OUT/jit-atomic.txt 2>&1
rm -rf /sys/fs/bpf/u15
fi

# 7. lab 15.1: the write counter three ways, one writer on CPU 1, 2,000,000 writes; three rounds
sysctl -q -w kernel.bpf_stats_enabled=1
{
for r in 1 2 3; do
for o in hashmap wc_noprintk counter_lru; do
  bpftool prog load $o.bpf.o /sys/fs/bpf/wc autoattach
  taskset -c 1 ./wloop 2000000
  bpftool -j prog show name count_writes | python3 -I -c "import json,sys; p=json.load(sys.stdin); p=p[0] if isinstance(p,list) else p; print('round $r $o: run_cnt %d, %.1f ns per run, recursion_misses %d' % (p['run_cnt'], p['run_time_ns']/p['run_cnt'], p.get('recursion_misses', 0)))"
  echo "round $r $o: map total $(bpftool -j map dump name write_counts | python3 -I msum.py), $(bpftool map show name write_counts | grep -o 'memlock [0-9]*B')"
  rm -f /sys/fs/bpf/wc; sleep 1
done
done
} > $OUT/lab.txt 2>&1
sysctl -q -w kernel.bpf_stats_enabled=0

chmod -R a+r $OUT; echo done > $OUT/done.txt
