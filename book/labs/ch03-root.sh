#!/bin/bash
# Chapter 3: an optional root step. The lab itself needs no root; this loads the fork tracer for real
# and records libbpf's patch lines and the instructions the kernel received.
# On the host:        sudo bash book/labs/ch03-root.sh
# In a throwaway VM:  vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- "bash $PWD/book/labs/ch03-root.sh"
# Output: /tmp/book-labs/ch03/*.txt. One pin under /sys/fs/bpf, removed again.
set -u
OUT=/tmp/book-labs/ch03; W=/tmp/ch03
PROG=$(cd "$(dirname "$0")/../program" && pwd)
mkdir -p "$OUT" "$W"
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
( cd "$PROG" && clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I. \
    -c hello_world/03-tracepoint/tracepoint.bpf.c -o "$W/tracepoint-root.bpf.o" ) > "$OUT/build.txt" 2>&1
PIN=/sys/fs/bpf/book_ch03_tp
rm -f "$PIN"
bpftool -d prog load "$W/tracepoint-root.bpf.o" "$PIN" > "$OUT/load-debug.txt" 2>&1
grep -E 'relo #[0-9]+: (patched|matching)' "$OUT/load-debug.txt" > "$OUT/patched.txt"
bpftool prog dump xlated pinned "$PIN" > "$OUT/xlated.txt" 2>&1
rm -f "$PIN"
chmod -R a+r "$OUT"
echo "ch03 done: $OUT"
