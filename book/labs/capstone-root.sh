#!/bin/bash
# Chapter "Capstone: a new data structure, twice": the write counter as a count-min sketch,
# in an arena on a stock kernel (Part A) and as a map type of its own in a patched kernel
# (Part B), measured against a hash and an LRU hash by the method of chapter "Maps".
#
# Build on the host (no root):  bash book/labs/capstone-root.sh build
#   (needs book/program/vmlinux.h: run `make` in book/program first; clang 18 or later)
# Part A, as root in a throwaway VM of the stock kernel:
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- 'bash /tmp/cap-lab/capstone-root.sh stock'
# Part B, in a VM of the patched kernel (the series in labs/capstone/patches applied to v7.2,
# built with test_progs and bench; see Lab "Add the map type to the kernel"):
#   vng -r ~/kernels/linux-capstone/arch/x86/boot/bzImage --user root --rwdir /tmp -- \
#       'bash /tmp/cap-lab/capstone-root.sh patched ~/kernels/linux-capstone'
# "lab" instead of "stock" runs Lab A's measurements only; "stockb" runs Part B's tools on the
# stock kernel (vng -r /boot/vmlinuz-linux ... 'bash /tmp/cap-lab/capstone-root.sh stockb ~/kernels/linux-capstone').
# The patched kernel was built twice: with the selftests' config fragments as they are (lockdep on:
# selftest.txt) and with lock debugging off for the measurements (Lab "Add the map type to the kernel").
# Output: /tmp/book-labs/capstone/*.txt
#   versions-*.txt  kernel, CPUs, tools
#   cost-*.txt      ns per write and per run, 1 writer (3 rounds) and 8 writers (3 rounds)
#   churn-*.txt     100,000 light threads writing 3 times and 4 heavy threads writing
#                   100,000 times: what each structure holds, error against the truth;
#                   churn-*.dat has "tid true estimate" for every thread (the plot)
#   see.txt         bpftool and /proc/PID/maps on the arena sketch while it runs; strace of
#                   the read (no bpf() call for the arena, one per thread for the others)
#   bad-*.txt       the map type on the stock kernel, and the two refused programs in bad/
#   bench.txt, selftest.txt, probe.txt   Part B: the benchmark, the selftests, libbpf's probe
#   stockb.txt      Part B's tools on the stock kernel ("stockb"), and the bloom filter peek
#                   that v7.2's stack liveness refuses (bad/bloompeek*.bpf.c)
# Recorded 13 November 2026 on the book's laptop (AMD Ryzen 7 8845HS, 16 CPUs), virtme-ng
# 1.42 VMs with 16 CPUs: stock kernel 7.2.15-arch1-1; patched kernel 7.2.0 built from the
# v7.2 tag with the series. The chapter quotes the medians.
# memory/mem.h, memory/bpf_arena_{common,alloc}.h are chapter "Memory you manage"'s copies.
HERE=$(cd "$(dirname "$0")" && pwd)
W=/tmp/cap-lab
CF="-g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I. -Wno-missing-declarations"
if [ "${1:-}" = build ]; then
  set -e
  mkdir -p $W/bad && cp "$0" $W/capstone-root.sh
  cp "$HERE"/capstone/*.c "$HERE"/capstone/*.h $W/ && cp "$HERE"/capstone/bad/*.c $W/bad/
  cp "$HERE"/memory/mem.h "$HERE"/memory/bpf_arena_common.h "$HERE"/memory/bpf_arena_alloc.h $W/
  cp "$HERE/../program/vmlinux.h" $W/
  cd $W
  b() { o=$1; src=$2; shift 2; clang $CF "$@" -c $src.bpf.c -o $o.bpf.o; }
  b c_hash c_hash; b c_lru c_hash -DMAPTYPE=BPF_MAP_TYPE_LRU_HASH; b c_exact c_hash -DENTRIES=262144
  b c_sketch c_sketch; b c_topk c_sketch -DWITH_TOPK
  b c_array c_array; b c_arraytopk c_array -DWITH_TOPK
  b c_cms c_cms; b c_cmstopk c_cms -DWITH_TOPK
  for f in bad/*.bpf.c; do clang $CF -c $f -o ${f%.c}.o; done
  gcc -O2 -Wall cbench.c -o cbench -lbpf -lpthread -lm
  echo "built in $W"
  exit 0
fi

set -u
MODE=${1:-stock}
OUT=/tmp/book-labs/capstone; mkdir -p $OUT; cd $W || exit 1
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
sysctl -qw kernel.pid_max=4194304	# 100,000 threads, each with an ID of its own
TAG=$([ "$MODE" = patched ] && echo patched || echo stock)
{ uname -a; echo "nproc $(nproc)"; grep -m1 'model name' /proc/cpuinfo
  bpftool version | head -1; clang --version | head -1; date -u
  echo "spec_rstack_overflow: $(cat /sys/devices/system/cpu/vulnerabilities/spec_rstack_overflow)"
} > $OUT/versions-$TAG.txt 2>&1

cost() {	# cost OBJ...: 1 writer x 3 rounds, then 8 writers x 3 rounds
  for o in "$@"; do
    for r in 1 2 3; do ./cbench $o.bpf.o cost 1 2000000 | grep -E '^[a-z]'; done
    for r in 1 2 3; do ./cbench $o.bpf.o cost 8 1000000 | grep -E '^[a-z]'; done
  done
}
churn() {	# churn OBJ [DAT]: the workload a hash cannot hold
  echo "=== $1 ${CMS_W:+CMS_W=$CMS_W}"
  OUT_DAT=${2:-}
  if [ -n "$OUT_DAT" ]; then OUT=$OUT/$OUT_DAT ./cbench $1.bpf.o churn 100000 3 4 100000
  else ./cbench $1.bpf.o churn 100000 3 4 100000; fi
}

if [ "$MODE" = stock ] || [ "$MODE" = lab ]; then
  cost c_hash c_lru c_sketch c_topk c_array c_arraytopk > $OUT/cost-stock.txt 2>&1
  { churn c_hash; churn c_lru; churn c_exact
    churn c_sketch churn-sketch.dat; churn c_topk; churn c_array
    CMS_W=272 churn c_sketch churn-w272.dat
    CMS_W=68 churn c_sketch churn-w68.dat
  } > $OUT/churn-stock.txt 2>&1
fi

if [ "$MODE" = stock ]; then
  # what the running sketch looks like from outside, and what reading it costs
  {
    HOLD=4 ./cbench c_topk.bpf.o churn 20000 3 4 100000 > hold.txt 2>&1 &
    sleep 3
    echo "--- bpftool map show (abridged by the chapter)"; bpftool map show
    echo "--- bpftool prog show name count_writes"; bpftool prog show name count_writes
    echo "--- /proc/PID/maps"; grep bpf-map /proc/$(pgrep -n cbench)/maps
    wait; cat hold.txt
    for o in c_topk c_hash; do
      strace -f -e trace=bpf,getppid -o s.txt ./cbench $o.bpf.o churn 2000 3 4 20000 > /dev/null
      echo "--- $o: bpf() calls between the two getppid() markers of the read"
      awk '/getppid/{n++; next} n==1' s.txt | grep -o 'BPF_[A-Z_]*' | sort | uniq -c
    done
  } > $OUT/see.txt 2>&1
  # failures
  { echo "--- the map type on a stock kernel"; ./cbench c_cms.bpf.o cost 1 1000
    for p in fetchor arenakey; do
      echo "--- bad/$p"; bpftool prog load bad/$p.bpf.o /sys/fs/bpf/bad_$p 2>&1 | tail -6
    done
  } > $OUT/bad-stock.txt 2>&1
fi

if [ "$MODE" = stockb ]; then	# Part B's tools on the stock kernel: what they say without the series
  K=${2:-$HOME/kernels/linux-capstone}/tools/testing/selftests/bpf
  { echo "--- the patched tree's bpftool: feature probe"; $K/tools/sbin/bpftool feature probe kernel | grep -E 'count_min|bloom_filter'
    echo "--- test_progs -t count_min_map"; (cd $K && ./test_progs -t count_min_map 2>&1 | grep -E '^#|Summary|FAIL:' | head -20)
    for p in bloompeek bloompeek2; do
      echo "--- bad/$p: a bloom filter peek of a stack value"
      bpftool prog load bad/$p.bpf.o /sys/fs/bpf/$p 2>&1 | grep -E 'poisoned|^Error'
    done
  } > $OUT/stockb.txt 2>&1
fi

if [ "$MODE" = patched ]; then
  K=${2:-$HOME/kernels/linux-capstone}/tools/testing/selftests/bpf
  cost c_hash c_lru c_sketch c_topk c_array c_cms c_cmstopk > $OUT/cost-patched.txt 2>&1
  { churn c_cms churn-cms.dat; churn c_cmstopk; churn c_sketch
  } > $OUT/churn-patched.txt 2>&1
  { HOLD=3 ./cbench c_cms.bpf.o cost 1 100000 > /dev/null 2>&1 &
    sleep 1.5; BT=$K/tools/sbin/bpftool		# built from the patched tree
    echo "--- the host's bpftool: map show name cms"; bpftool map show name cms
    echo "--- the patched tree's bpftool: map show name cms"; $BT map show name cms; wait
    echo "--- the patched tree's bpftool: feature probe"; $BT feature probe kernel | grep -E 'count_min|bloom_filter'
    echo "--- the patched tree's bpftool: map help"; $BT map help 2>&1 | grep -E 'rhash|count_min'
  } > $OUT/probe.txt 2>&1
  (cd $K && ./test_progs -t count_min_map,verifier_bloom_peek,bloom_filter_map) > $OUT/selftest.txt 2>&1
  { cd $K
    for p in 1 8; do
      for b in count-min-push count-min-peek count-min-hash count-min-lru; do
        echo "--- $b -p $p --cms_nr_keys 100000"
        ./bench -w2 -d6 -a -p $p --cms_nr_keys 100000 $b 2>&1 | grep Summary
      done
      for b in bloom-update bloom-lookup; do
        echo "--- $b -p $p --nr_hash_funcs 5 --value_size 8 --nr_entries 100000"
        ./bench -w2 -d6 -a -p $p --nr_hash_funcs 5 --value_size 8 --nr_entries 100000 $b 2>&1 | grep Summary
      done
    done
  } > $OUT/bench.txt 2>&1
fi
echo "done: $OUT"
