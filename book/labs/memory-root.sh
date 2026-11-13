#!/bin/bash
# Chapter "Memory you manage": allocated objects, a red-black tree, kptrs and an arena, measured.
# Build on the host (no root):   bash book/labs/memory-root.sh build      (needs program/vmlinux.h:
#                                 run `make` in book/program first; clang 18 or later for arenas)
# Then, as root in a throwaway VM:
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- 'bash /tmp/mem-lab/memory-root.sh'
# Arguments: none = everything; "lab" = step 3's first block only (Lab "Count writes in a tree
# and in an arena"); "bad" = step 6 only (and Lab "Fix three refused programs": fix/).
# Output: /tmp/book-labs/memory/*.txt
#   versions.txt  kernel, CPUs, preemption mode, tools
#   see-rb.txt    the counter on a red-black tree: three writers, then bpftool on what it holds;
#                 verifier.txt has the verifier's log of count_writes (log level 1)
#   see-arena.txt the counter in an arena hash table; strace of the read: no bpf() call
#   bench.txt     ns per write and per run for hash, rbtree and arena: 1 and 8 writers, with
#                 0 and 1,000 other threads already counted; three rounds each
#   alloc.txt     allocation, free and lock costs inside a program, three rounds; the arena's
#                 fault reports from the programs' stderr streams
#   mem.txt       memory for 100,000 keys: tree nodes and arena elements
#   bad.txt       what the verifier says to each program in labs/memory/bad/ (logs in bad-*.txt),
#                 and whether the fixed versions in labs/memory/fix/ load; tracelog.txt has
#                 bpftool's view of an arena fault report
# memory/bpf_arena_{common,alloc,list,htab}.h are copied unchanged from the v7.2 tree
# (tools/testing/selftests/bpf/, bpf_arena_common.h from its libarena/include/).
# Recorded 13 November 2026, kernel 7.2.15-arch1-1 VM with 16 CPUs (virtme-ng 1.42 on the
# book's laptop, AMD Ryzen 7 8845HS); the chapter quotes the medians.
HERE=$(cd "$(dirname "$0")" && pwd)
W=/tmp/mem-lab
CF="-g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I. -Wno-missing-declarations"
if [ "${1:-}" = build ]; then
  set -e
  mkdir -p $W/bad $W/fix && cp "$0" $W/memory-root.sh
  cp "$HERE"/memory/*.c "$HERE"/memory/*.h $W/ && cp "$HERE"/memory/bad/* $W/bad/
  cp "$HERE"/memory/fix/* $W/fix/
  cp "$HERE/../program/vmlinux.h" $W/
  cd $W
  for o in c_hash c_rb c_arena alloc; do clang $CF -c $o.bpf.c -o $o.bpf.o; done
  for f in bad/*.bpf.c fix/*.bpf.c; do clang $CF -Ibad -c $f -o ${f%.c}.o; done
  gcc -O2 -Wall mbench.c -o mbench -lbpf -lpthread
  gcc -O2 -Wall atest.c -o atest -lbpf
  echo "built in $W"
  exit 0
fi

set -u
ONLY=${1:-all}
OUT=/tmp/book-labs/memory; mkdir -p $OUT; cd $W || exit 1
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
mountpoint -q /sys/kernel/debug || mount -t debugfs debugfs /sys/kernel/debug
{ uname -r; echo "nproc $(nproc)"; echo "preempt: $(cat /sys/kernel/debug/sched/preempt)"
  grep -m1 'model name' /proc/cpuinfo; bpftool version | head -1; clang --version | head -1
  date -u
} > $OUT/versions.txt 2>&1

if [ "$ONLY" = all ] || [ "$ONLY" = lab ]; then
if [ "$ONLY" = all ]; then
# 1. the counter on a tree: what it holds, from the counter's side and from bpftool's
{
  HOLD=4 ./mbench c_rb.bpf.o 3 1000 0 show &
  sleep 2.5
  echo "--- bpftool prog show name count_writes"; bpftool prog show name count_writes
  echo "--- bpftool map show name counts_tree"; bpftool map show name counts_tree
  echo "--- bpftool map dump name counts_tree"; bpftool map dump name counts_tree
  wait
} > $OUT/see-rb.txt 2>&1
bpftool -d prog load c_rb.bpf.o /sys/fs/bpf/m_rb > $OUT/verifier.txt 2>&1; rm -rf /sys/fs/bpf/m_rb

# 2. the counter in an arena: the same view, then the read under strace
{
  HOLD=4 ./mbench c_arena.bpf.o 3 1000 0 show &
  sleep 2.5
  echo "--- bpftool map show name arena"; bpftool map show name arena
  echo "--- the loader's mappings"; grep -E 'bpf|anon_inode' /proc/$(pgrep -n mbench)/maps
  wait
  for o in c_arena c_hash c_rb; do
    strace -f -e trace=bpf,getppid -o $OUT/strace-$o.txt ./mbench $o.bpf.o 3 1000 0 > /dev/null
    echo "--- $o: system calls between the two getppid() markers that bracket the read"
    awk '/getppid/{n++; next} n==1' $OUT/strace-$o.txt | sed 's/^[0-9]* *//' | cut -c1-60 | sort | uniq -c
  done
} > $OUT/see-arena.txt 2>&1
fi

# 3. ns per write and per run, three rounds; nw=1 with no other threads is the lab
sysctl -q -w kernel.bpf_stats_enabled=1
{
for r in 1 2 3; do for o in c_hash c_rb c_arena; do ./mbench $o.bpf.o 1 2000000 0; done; done
if [ "$ONLY" = all ]; then
for r in 1 2 3; do for o in c_hash c_rb c_arena; do
  ./mbench $o.bpf.o 1 1000000 1000
  ./mbench $o.bpf.o 8 500000 0
  ./mbench $o.bpf.o 8 500000 1000
done; done
fi
} > $OUT/bench.txt 2>&1
fi
[ "$ONLY" = lab ] && exit 0

if [ "$ONLY" = all ]; then
# 4. allocation inside a program, in a memory cgroup of its own
echo +memory > /sys/fs/cgroup/cgroup.subtree_control
mkdir -p /sys/fs/cgroup/mem11
{
for r in 1 2 3; do
  echo "--- round $r"
  bash -c "echo \$\$ > /sys/fs/cgroup/mem11/cgroup.procs; CG=/sys/fs/cgroup/mem11 exec ./atest \
    alloc.bpf.o obj_keep:100000 obj_free:100000 obj_pair:100000 obj_keep:32 obj_free:32 \
    obj_keep:32 obj_free:32 slots:100000 lock_pair:1000000 page_keep:10000 page_free:10000 \
    page_pair:10000 frag:100000 past_end:1 unalloc:1"
done
} > $OUT/alloc.txt 2>&1

# 5. memory for 100,000 keys, each structure loaded alone in a fresh cgroup
{
for o in c_rb c_arena; do
  mkdir -p /sys/fs/cgroup/mem11-$o
  bash -c "echo \$\$ > /sys/fs/cgroup/mem11-$o/cgroup.procs; CG=/sys/fs/cgroup/mem11-$o \
    exec ./mbench $o.bpf.o 1 0 100000"
done
} > $OUT/mem.txt 2>&1
fi

# 6. the verifier on the programs of labs/memory/bad
{
for f in bad/*.bpf.o; do
  b=$(basename $f .bpf.o)
  bpftool prog load $f /sys/fs/bpf/bad_$b > $OUT/bad-$b.txt 2>&1; echo "=== $b: exit $?"
  grep -v '^;\|^[0-9]*: \|^libbpf\|^-- \|^processed\|^Error\|^arg#0 reference' $OUT/bad-$b.txt | head -3
  rm -f /sys/fs/bpf/bad_$b
done
for f in fix/*.bpf.o; do
  b=$(basename $f .bpf.o)
  bpftool prog load $f /sys/fs/bpf/fix_$b > $OUT/fix-$b.txt 2>&1; echo "=== fixed $b: exit $?"
  rm -f /sys/fs/bpf/fix_$b
done
} > $OUT/bad.txt 2>&1
# what bpftool shows of an arena fault: the program's stderr stream
{
  HOLD=3 ./atest alloc.bpf.o past_end:1 &
  sleep 1.5
  echo "--- bpftool prog tracelog stderr name past_end"
  bpftool prog tracelog stderr name past_end
  wait
} > $OUT/tracelog.txt 2>&1
