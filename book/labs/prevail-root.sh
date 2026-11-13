#!/usr/bin/env bash
# Root steps for the PREVAIL chapter (src/prevail.html): Linux's walk of one packet loop,
# measured at four loop bounds, to set beside the toy abstract interpreter of labs/prevail/.
#
#   as root in a throwaway VM (no sudo on the host):
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- bash book/labs/prevail-root.sh
#
# book/ is only read. Objects and logs go to /tmp/book-labs/prevail/.
# Every load is freed when its loader exits; nothing is pinned or attached.
set -u
BOOK=$(cd "$(dirname "$0")/.." && pwd)
LAB="$BOOK/labs/prevail"
OUT=/tmp/book-labs/prevail
mkdir -p "$OUT"
CFLAGS="-g -O2 -target bpf -I/usr/include/bpf"

{ uname -r; bpftool version | head -1; clang --version | head -1; echo "cpus $(nproc)"; date -u; } \
    > "$OUT/versions.txt"
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf

# the loader of the walk chapter: one program of an object, log level 4, statistics only
cc -O2 -Wall "$BOOK/labs/walk/stats.c" -lbpf -o "$OUT/stats"
S="$OUT/stats"

# 1. the two loops at four bounds, three loads each, statistics only
for n in 16 64 256 1024; do
    clang $CFLAGS -DN=$n -c "$LAB/pktloop.bpf.c" -o "$OUT/pktloop$n.bpf.o"
done
{
for n in 16 64 256 1024; do
    for p in sum_once sum_each; do
        for i in 1 2 3; do "$S" "$OUT/pktloop$n.bpf.o" "$p" 4 | sed "s/^/N=$n /"; done
    done
done
} > "$OUT/pktloop.txt" 2>&1

# 2. the bytecode the toy transcribes, and one full log of each loop at N=16 (level 2)
llvm-objdump -d --no-show-raw-insn "$OUT/pktloop16.bpf.o" > "$OUT/pktloop16.dis" 2>&1 || true
for p in sum_once sum_each; do
    "$S" "$OUT/pktloop16.bpf.o" "$p" 2 "$OUT/$p-16-level2.log" > /dev/null
done

chown -R "${SUDO_UID:-0}:${SUDO_GID:-0}" "$OUT" 2>/dev/null
cat "$OUT/versions.txt"
grep -h 'load\|processed' "$OUT/pktloop.txt"
