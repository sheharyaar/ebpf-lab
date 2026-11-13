#!/usr/bin/env bash
# Root steps for the walk chapter (src/walk.html, "The verifier walks every path"): the counter
# loaded with the verifier's statistics, one loop written five ways (its second lab) and the small
# programs of the "when it goes wrong" table.
#
#   as root in a throwaway VM (no sudo on the host):
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- bash book/labs/walk-root.sh
#
# book/ is only read. Copies, objects and logs go to /tmp/book-labs/walk/.
# Every load is freed when its loader exits; the one pin is removed at once; nothing is attached.
set -u
BOOK=$(cd "$(dirname "$0")/.." && pwd)
REPO="$BOOK/program"
LAB="$BOOK/labs/walk"
OUT=/tmp/book-labs/walk
mkdir -p "$OUT"
CFLAGS="-g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I$REPO -Wno-missing-declarations"

{ uname -r; bpftool version | head -1; clang --version | head -1; echo "cpus $(nproc)"; date -u; } > "$OUT/versions.txt"
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf

# the write counter as the book prints it, with its include fixed for a copy outside book/program
sed 's|"../../vmlinux.h"|"vmlinux.h"|' "$REPO/maps/02-hash-map/hashmap.bpf.c" > "$OUT/counter.bpf.c"
clang $CFLAGS -c "$OUT/counter.bpf.c" -o "$OUT/counter.bpf.o"
for n in 256 4096; do clang $CFLAGS -DN=$n -c "$LAB/loops.bpf.c" -o "$OUT/loops$n.bpf.o"; done
clang $CFLAGS -c "$LAB/limits.bpf.c" -o "$OUT/limits.bpf.o"
cc -O2 -Wall "$LAB/stats.c" -lbpf -o "$OUT/stats"
S="$OUT/stats"

# 1. the counter: statistics only (level 4), five times; then every state (2 | 4 = 6), once, logged
{
for i in 1 2 3 4 5; do "$S" "$OUT/counter.bpf.o" count_writes 4; done
"$S" "$OUT/counter.bpf.o" count_writes 6 "$OUT/counter-level6.log"
# bpftool's view of the same program once it is loaded
bpftool prog load "$OUT/counter.bpf.o" /sys/fs/bpf/book_walk_counter
bpftool prog show pinned /sys/fs/bpf/book_walk_counter
rm -f /sys/fs/bpf/book_walk_counter
} > "$OUT/counter.txt" 2>&1

# 2. the second lab: one loop five ways, at 256 and 4,096 bytes, three loads each, statistics only
{
for n in 256 4096; do
    for p in plain helper iter maygoto maygoto_mem; do
        for i in 1 2 3; do "$S" "$OUT/loops$n.bpf.o" "$p" 4 | sed "s/^/N=$n /"; done
    done
done
} > "$OUT/loops.txt" 2>&1

# 3. the limits, one program at a time, statistics only
{
for p in slow budget branches spin deep deepglobal four_static four_global stack_socket stack_tp; do
    "$S" "$OUT/limits.bpf.o" "$p" 4
done
} > "$OUT/limits.txt" 2>&1

# 4. without CAP_BPF: a loop, and two loads at once with and without capabilities
#    (sets kernel.unprivileged_bpf_disabled to 0, which only a throwaway VM should do)
clang $CFLAGS -c "$LAB/unpriv.bpf.c" -o "$OUT/unpriv.bpf.o"
NOBODY="setpriv --reuid=65534 --regid=65534 --clear-groups --inh-caps=-all"
{
echo "unprivileged_bpf_disabled was $(cat /proc/sys/kernel/unprivileged_bpf_disabled)"
echo 0 > /proc/sys/kernel/unprivileged_bpf_disabled
echo "== root"; "$S" "$OUT/unpriv.bpf.o" ubackedge 4
echo "== nobody"; $NOBODY "$S" "$OUT/unpriv.bpf.o" ubackedge 4
for who in root nobody; do
    pre=""; [ "$who" = nobody ] && pre="$NOBODY"
    echo "== $who, one load"; $pre "$S" "$OUT/unpriv.bpf.o" upaths 4
    echo "== $who, two at once"
    t0=$(date +%s%N)
    $pre "$S" "$OUT/unpriv.bpf.o" upaths 4 > "$OUT/u1.txt" &
    $pre "$S" "$OUT/unpriv.bpf.o" upaths 4 > "$OUT/u2.txt"
    wait; t1=$(date +%s%N)
    cat "$OUT/u1.txt" "$OUT/u2.txt"; echo "both done in $(( (t1 - t0) / 1000000 )) ms"
done
} > "$OUT/unpriv.txt" 2>&1

chown -R "${SUDO_UID:-0}:${SUDO_GID:-0}" "$OUT" 2>/dev/null
cat "$OUT/versions.txt"
grep -h 'load\|verified\|processed\|verification time\|stack depth\|insns processed' "$OUT/counter.txt" | head -20
