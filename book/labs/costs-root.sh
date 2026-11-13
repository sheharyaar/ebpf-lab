#!/bin/bash
# Measurements behind the "What it costs" boxes of chapters 1-5 (run 2026-11-12, kernel 7.2.15, VM).
# Needs the objects that ch05-root.sh leaves in /tmp/book-labs/ch05/ (run that first).
# Build on the host (no root):  bash book/labs/costs-root.sh build
# Then, as root in a throwaway VM:
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- 'bash /tmp/sw/costs-root.sh'
# Output: /tmp/book-labs/costs/*.txt (dd.txt, loglvl.txt, prog-show-*.txt, map-show-*.txt, strace-*.txt)
HERE=$(cd "$(dirname "$0")" && pwd)
if [ "${1:-}" = build ]; then
  mkdir -p /tmp/sw && cp "$0" /tmp/sw/costs-root.sh
  gcc -O2 "$HERE/costs-loglvl.c" -o /tmp/sw/loglvl -lbpf
  sed '/bpf_printk/d; s#"../../vmlinux.h"#"vmlinux.h"#' "$HERE/../program/maps/02-hash-map/hashmap.bpf.c" > /tmp/sw/noprint.bpf.c
  clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I"$HERE/../program" -c /tmp/sw/noprint.bpf.c -o /tmp/sw/noprint.bpf.o
  /tmp/sw/loglvl btf    # host: time and memory of libbpf's btf__load_vmlinux_btf() (chapter 3)
  exit 0
fi
set -u
OUT=/tmp/book-labs/costs; mkdir -p $OUT; cd $OUT
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
V=/tmp/book-labs/ch05
{ uname -r; bpftool version | head -2; nproc; } > versions.txt
w() { local t0 t1; t0=$(date +%s%N); dd if=/dev/zero of=/dev/null bs=1 count=$1 status=none; t1=$(date +%s%N); echo $(( (t1-t0)/$1 )); }
w 200000 > /dev/null
echo "no program, ns per dd iteration: $(w 1000000) $(w 1000000) $(w 1000000)" > dd.txt
# load cost without a log: time of each bpf() call
strace -T -o strace-load-hashmap.txt -e trace=bpf bpftool prog load $V/hashmap.bpf.o /sys/fs/bpf/costs_hm0 2>&1; rm -f /sys/fs/bpf/costs_hm0
strace -T -o strace-load-bounded.txt -e trace=bpf bpftool prog load $V/bounded.bpf.o /sys/fs/bpf/costs_b0 2>&1; rm -f /sys/fs/bpf/costs_b0
# per-event cost with stats on
sysctl -q -w kernel.bpf_stats_enabled=1
for o in $V/hashmap.bpf.o /tmp/sw/noprint.bpf.o; do
  n=$(basename $o .bpf.o)
  bpftool prog load $o /sys/fs/bpf/costs_$n autoattach || echo "autoattach failed for $n"
  w 200000 > /dev/null
  echo "$n attached, ns per dd iteration: $(w 1000000) $(w 1000000) $(w 1000000)" >> dd.txt
  bpftool prog show name count_writes > prog-show-$n.txt
  bpftool map show name write_counts > map-show-$n.txt
  rm -rf /sys/fs/bpf/costs_$n
  sleep 1
done
sysctl -q -w kernel.bpf_stats_enabled=0
echo "after detach, ns per dd iteration: $(w 1000000)" >> dd.txt
# log levels: size of the log and verification time
for o in hashmap bounded; do for l in 4 5 6 7; do /tmp/sw/loglvl $V/$o.bpf.o $l; done; done > loglvl.txt 2>&1
# a rejected million-instruction walk: without -d, then with -d
strace -T -o strace-loop.txt -e trace=bpf bpftool prog load $V/loop.bpf.o /sys/fs/bpf/costs_loop > /dev/null 2>&1
strace -T -o strace-loop-d.txt -e trace=bpf -e abbrev=all -s 0 bpftool -d prog load $V/loop.bpf.o /sys/fs/bpf/costs_loopd > /dev/null 2>&1
echo done > done.txt
