#!/bin/bash
# Chapter 11: the load path, traced in the kernel. The steps that need root.
# On the host:        sudo bash book/labs/ch11-root.sh
# In a throwaway VM:  vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- "bash $PWD/book/labs/ch11-root.sh"
# Output: /tmp/book-labs/ch11/*.txt. Builds in /tmp/ch11; the program folder is only read.
# One pin under /sys/fs/bpf, removed again. Leaves the ftrace tracer set to nop.
set -u
OUT=/tmp/book-labs/ch11; W=/tmp/ch11
PROG=$(cd "$(dirname "$0")/../program" && pwd)
T=/sys/kernel/tracing
mkdir -p "$OUT" "$W"; chmod 755 "$W"
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
mountpoint -q $T || mount -t tracefs tracefs $T
{ uname -r; bpftool version | head -1; bpftrace --version; echo "lsm: $(cat /sys/kernel/security/lsm 2>/dev/null)";
  sysctl kernel.unprivileged_bpf_disabled kernel.perf_event_paranoid; } > "$OUT/versions.txt" 2>&1

# 0. a copy of the loader in /tmp, readable by an unprivileged user
if [ ! -x "$W/hashmap" ]; then
  ( cd "$PROG" && clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I. \
      -c maps/02-hash-map/hashmap.bpf.c -o "$W/hashmap.bpf.o" 2>/dev/null &&
    bpftool gen skeleton "$W/hashmap.bpf.o" > "$W/hashmap.skel.h" &&
    cp maps/02-hash-map/hashmap.c "$W/" &&
    cd "$W" && gcc -g -O2 -Wall -I. hashmap.c -o hashmap -lbpf -lelf -lz ) > "$OUT/build.txt" 2>&1
fi
chmod 755 "$W/hashmap"; cd "$W" || exit 1

# the user "nobody" with only the capabilities named, carried across exec as ambient capabilities
as_nobody() { local caps=$1; shift; setpriv --reuid=65534 --regid=65534 --clear-groups --inh-caps="$caps" --ambient-caps="$caps" "$@"; }

# 1. the symptom: CAP_BPF alone. Then CAP_BPF and CAP_PERFMON.
as_nobody +bpf grep -E '^Cap(Eff|Amb)' /proc/self/status > "$OUT/caps-bpf.txt" 2>&1
S=$(mktemp -d /dev/shm/ch11.XXXX); chmod 1777 "$S"   # strace, running as nobody, writes its log here (a shared /tmp may refuse nobody)
as_nobody +bpf strace -f -o "$S/strace-bpf-only.txt" -e trace=bpf,perf_event_open ./hashmap > "$OUT/run-bpf-only.txt" 2>&1
echo "exit=$?" >> "$OUT/run-bpf-only.txt"; cp "$S/strace-bpf-only.txt" "$OUT/"
as_nobody +bpf,+perfmon strace -f -o "$S/strace-bpf-perfmon.txt" -e trace=bpf,perf_event_open,openat timeout -k 1 4 ./hashmap > /dev/null 2>&1
cp "$S/strace-bpf-perfmon.txt" "$OUT/"
as_nobody +bpf,+perfmon timeout -k 1 4 ./hashmap 2>&1 | head -n 6 > "$OUT/run-bpf-perfmon.txt"

# 2. function_graph on bpf_prog_load: the refused load, then a load that succeeds
graph() {  # $1 = output file, $2 = depth, rest = command
  local f=$1 d=$2; shift 2
  echo 0 > $T/tracing_on; echo nop > $T/current_tracer
  echo bpf_prog_load > $T/set_graph_function
  echo "$d" > $T/max_graph_depth
  echo 1 > $T/options/funcgraph-retval 2>/dev/null
  echo function_graph > $T/current_tracer; echo > $T/trace
  echo 1 > $T/tracing_on; "$@" > /dev/null 2>&1; echo 0 > $T/tracing_on
  cat $T/trace > "$f"
  echo nop > $T/current_tracer; echo > $T/set_graph_function; echo 0 > $T/max_graph_depth
}
graph "$OUT/graph-bpf-only.txt" 2 as_nobody +bpf ./hashmap
graph "$OUT/graph-root.txt" 2 timeout -k 1 3 ./hashmap

# 3. timing and counts for one load as root
for i in 1 2 3 4 5; do
  timeout -k 1 2 strace -T -e trace=bpf -o "$OUT/strace-T-$i.txt" ./hashmap > /dev/null 2>&1
done
grep -h 'insn_cnt=27' "$OUT"/strace-T-*.txt | sed 's/.*= \([0-9]*\) <\(.*\)>/fd=\1 seconds=\2/' > "$OUT/prog-load-times.txt"
timeout -s TERM 3 strace -c -f -e trace=bpf,perf_event_open,ioctl -o "$OUT/strace-c.txt" ./hashmap > /dev/null 2>&1

# 4. what the loaded program costs, seen from outside (with run-time statistics on)
sysctl -w kernel.bpf_stats_enabled=1 > /dev/null
( while :; do echo x > /dev/null; sleep 0.1; done ) &
WR=$!
./hashmap > /dev/null 2>&1 &
LP=$!
sleep 4
{ bpftool prog show name count_writes; bpftool map show; bpftool link show; bpftool btf show; } > "$OUT/show.txt" 2>&1
bpftool -j prog show name count_writes > "$OUT/prog-show.json" 2>&1
grep -E 'memlock|verified_insns|prog_id|map_ids' /proc/$LP/fdinfo/* > "$OUT/fdinfo.txt" 2>/dev/null
ls -l /proc/$LP/fd > "$OUT/loader-fds.txt" 2>&1
sysctl -w kernel.bpf_stats_enabled=0 > /dev/null

# 5. teardown when the loader is killed: who drops which reference, and when
cat > "$W/teardown.bt" <<'BT'
tracepoint:syscalls:sys_enter_kill /args.sig == 15/ { @t0 = nsecs; printf("%9s  %-15s %s\n", "0 us", comm, "kill(SIGTERM)"); }
tracepoint:syscalls:sys_enter_unlinkat /@t0 == 0 && str(args.pathname) == "/sys/fs/bpf/wc"/ { @t0 = nsecs; printf("%9s  %-15s %s\n", "0 us", comm, "unlink(/sys/fs/bpf/wc)"); }
kprobe:bpf_prog_release, kprobe:bpf_link_release, kprobe:bpf_link_free, kprobe:bpf_perf_link_release,
kprobe:bpf_prog_put_deferred, kprobe:__bpf_prog_put_rcu, kprobe:bpf_prog_free_deferred,
kprobe:bpf_map_free_deferred, kprobe:htab_map_free, kprobe:array_map_free, kprobe:bpf_map_release
/@t0/ { printf("%6llu us  %-15s %s\n", (uint64)(nsecs - @t0) / 1000, comm, func); }
kprobe:bpf_prog_put /@t0/ { $p = (struct bpf_prog *)arg0;
  printf("%6llu us  %-15s bpf_prog_put(%s) refcnt %d\n", (uint64)(nsecs - @t0) / 1000, comm, $p->aux->name, $p->aux->refcnt.counter); }
kprobe:bpf_map_put /@t0/ { $m = (struct bpf_map *)arg0;
  printf("%6llu us  %-15s bpf_map_put(%s) refcnt %d\n", (uint64)(nsecs - @t0) / 1000, comm, $m->name, $m->refcnt.counter); }
BT
bpftrace -q "$W/teardown.bt" > "$OUT/teardown-kill.txt" 2> "$W/bpftrace-kill.err" &
BP=$!
sleep 3
kill -TERM $LP; wait $LP 2>/dev/null
sleep 1
kill -INT $BP; wait $BP 2>/dev/null
bpftool prog show name count_writes > "$OUT/after-kill.txt" 2>&1; echo "prog show exit=$?" >> "$OUT/after-kill.txt"

# 6. the same teardown, held off by a pin until the pin is removed
./hashmap > /dev/null 2>&1 &
LP=$!
sleep 2
LID=$(bpftool -j link show | python3 -I -c 'import json,sys; print([l["id"] for l in json.load(sys.stdin) if l.get("type") == "perf_event"][-1])')
bpftool link pin id "$LID" /sys/fs/bpf/wc
kill -TERM $LP; wait $LP 2>/dev/null
sleep 1
{ echo "# loader gone, pin in place"; bpftool prog show name count_writes; bpftool map show name write_counts; bpftool link show id "$LID"; } > "$OUT/pinned.txt" 2>&1
bpftrace -q "$W/teardown.bt" > "$OUT/teardown-unpin.txt" 2> "$W/bpftrace-unpin.err" &
BP=$!
sleep 3
rm /sys/fs/bpf/wc
sleep 1
kill -INT $BP; wait $BP 2>/dev/null
{ echo "# pin removed"; bpftool prog show name count_writes; echo "exit=$?"; } >> "$OUT/pinned.txt" 2>&1

kill $WR 2>/dev/null
echo done > "$OUT/done.txt"
