#!/bin/bash
# Chapter "hooks" (Hooks, and what attaching writes into the kernel): every per-event cost in the chapter's
# "What it costs" box, measured in one VM session (2026-11-12, to settle the 0.36 us a run of the old
# load-and-attach chapter against the 155 ns of the JIT chapter, and the dd figures of the old hooks chapter
# against the write() figures of the old attach-internals chapter).
#   1. the write counter's own cost per run, with and without bpf_printk, two ways:
#      dd    as the old chapters did: dd copies 1,000,000 bytes one at a time (one read() and one write() a byte)
#            with the counter attached and kernel.bpf_stats_enabled=1; run_time_ns / run_cnt from bpftool,
#            ns per dd byte from date
#      bench as the attach-internals chapter did: bench14 times one-byte write() calls to /dev/null on CPU 1,
#            median of 7 x 1M with stats off, then 100,000 writes with stats on for run_time_ns / run_cnt
#   2. one empty program at a time at each hook on the write path (bench14 event): ns per write, run_time_ns,
#      the line in kprobes/list and the bytes at vfs_write+4 and +9
#   3. getppid() with nothing attached and with the counter at the write tracepoint, which sets the
#      system-call work flag on every thread (syscall_regfunc(), kernel/tracepoint.c)
# Build on the host (no root; run `make` in book/program first):
#   bash book/labs/ch14-root.sh build && bash book/labs/hooks-root.sh build
# Then, as root in a throwaway VM:
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- 'bash /tmp/hkc/hooks-root.sh'
# Output: /tmp/book-labs/hooks/versions.txt, perrun.txt, bench-*.txt, event.txt, ppid.txt
HERE=$(cd "$(dirname "$0")" && pwd)
W=/tmp/hkc
if [ "${1:-}" = build ]; then
  set -e
  [ -x /tmp/c14/bench14 ] || { echo "run: bash $HERE/ch14-root.sh build"; exit 1; }
  mkdir -p $W && cp "$0" $W/hooks-root.sh
  cp "$HERE/../program/vmlinux.h" $W/
  SRC="$HERE/../program/maps/02-hash-map/hashmap.bpf.c"
  sed 's#"../../vmlinux.h"#"vmlinux.h"#' "$SRC" > $W/printk.bpf.c
  sed '/bpf_printk/d; s#"../../vmlinux.h"#"vmlinux.h"#' "$SRC" > $W/noprint.bpf.c
  for f in printk noprint; do
    clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I$W -c $W/$f.bpf.c -o $W/$f.bpf.o
  done
  cp /tmp/c14/bench14 /tmp/c14/hooks14.bpf.o $W/
  cat > $W/ppid.c <<'EOF'
// ppid: ns per getppid() system call, median of 7 x 1M
#include <stdio.h>
#include <stdlib.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
static long long now(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec * 1000000000LL + t.tv_nsec;
}
static int cmp(const void *a, const void *b)
{
	double x = *(const double *)a, y = *(const double *)b;
	return x < y ? -1 : x > y;
}
int main(void)
{
	double v[7];
	for (int r = -1; r < 7; r++) {
		long long t0 = now();
		for (int i = 0; i < 1000000; i++)
			syscall(SYS_getppid);
		if (r >= 0)
			v[r] = (now() - t0) / 1e6;
	}
	qsort(v, 7, sizeof(v[0]), cmp);
	printf("median %.0f ns/getppid  [min %.0f max %.0f]\n", v[3], v[0], v[6]);
	return 0;
}
EOF
  gcc -O2 -Wall $W/ppid.c -o $W/ppid
  echo "built in $W"
  exit 0
fi

set -u
OUT=/tmp/book-labs/hooks; mkdir -p $OUT /tmp/book-labs/ch14; cd $W || exit 1
# bench14 calls /tmp/c14/kcore.py to print the bytes at vfs_write; it is there after ch14-root.sh build
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
mountpoint -q /sys/kernel/tracing || mount -t tracefs tracefs /sys/kernel/tracing
mountpoint -q /sys/kernel/debug || mount -t debugfs debugfs /sys/kernel/debug
{ uname -r; echo "nproc $(nproc)"; echo "bpf_jit_harden $(cat /proc/sys/net/core/bpf_jit_harden)"
  echo "preempt: $(cat /sys/kernel/debug/sched/preempt)"; grep -m1 'model name' /proc/cpuinfo; date -Is
} > $OUT/versions.txt 2>&1

# 3. getppid first, with nothing attached, then with the counter at the write tracepoint
taskset -c 1 ./ppid > /dev/null
echo "nothing attached: $(taskset -c 1 ./ppid)" > $OUT/ppid.txt
bpftool prog load noprint.bpf.o /sys/fs/bpf/hk_pp autoattach
echo "counter at sys_enter_write: $(taskset -c 1 ./ppid)" >> $OUT/ppid.txt
rm -f /sys/fs/bpf/hk_pp; sleep 1
echo "after detach: $(taskset -c 1 ./ppid)" >> $OUT/ppid.txt

# 1. the counter, two ways, three rounds
w() { local t0 t1; t0=$(date +%s%N); taskset -c 1 dd if=/dev/zero of=/dev/null bs=1 count=$1 status=none
      t1=$(date +%s%N); echo $(( (t1-t0)/$1 )); }
: > $OUT/perrun.txt
w 200000 > /dev/null
echo "no program: ns per dd byte $(w 1000000) $(w 1000000) $(w 1000000)" >> $OUT/perrun.txt
for round in 1 2 3; do
  for o in printk noprint; do
    bpftool prog load $o.bpf.o /sys/fs/bpf/hk_$o autoattach || { echo "load failed: $o" >> $OUT/perrun.txt; continue; }
    w 200000 > /dev/null
    sysctl -q -w kernel.bpf_stats_enabled=1
    t=$(w 1000000)
    s=$(bpftool prog show name count_writes | grep -o 'run_time_ns [0-9]* run_cnt [0-9]*')
    sysctl -q -w kernel.bpf_stats_enabled=0
    echo "round $round $o dd: $t ns per dd byte; $s" >> $OUT/perrun.txt
    rm -f /sys/fs/bpf/hk_$o; sleep 1
    taskset -c 1 ./bench14 $o.bpf.o event count_writes > $OUT/bench-$o-$round.txt 2>&1
  done
done

# 2. one empty program at a time at each hook
taskset -c 1 ./bench14 hooks14.bpf.o event e_tp e_rawtp e_kp e_kpoff e_fentry e_fexit > $OUT/event.txt 2>&1
chmod -R a+r $OUT; echo done > $OUT/done.txt
