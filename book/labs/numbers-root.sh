#!/usr/bin/env bash
# Root steps for the chapter "How the verifier tracks numbers" (src/numbers.html): the
# counter and its per-descriptor copy at log level 2 (the first lab), the programs of the
# "when it goes wrong" table and of the second lab, what precision costs, and the
# instructions added against speculative execution with and without CAP_PERFMON.
#
#   as root in a throwaway VM (no sudo on the host), from the repository's top directory:
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- bash book/labs/numbers-root.sh
#
# book/ is only read. Copies, objects and logs go to /tmp/book-labs/numbers/.
# Every load is freed when its loader exits; pins are removed at once; nothing is attached.
set -u
BOOK=$(cd "$(dirname "$0")/.." && pwd)
REPO="$BOOK/program"
LAB="$BOOK/labs/numbers"
OUT=/tmp/book-labs/numbers
rm -rf "$OUT"; mkdir -p "$OUT"
CFLAGS="-g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I$REPO -Wno-missing-declarations"
# CAP_BPF and CAP_NET_ADMIN kept; CAP_PERFMON and CAP_SYS_ADMIN (which implies it) dropped
NOPERFMON="setpriv --inh-caps=-all --bounding-set=-perfmon,-sys_admin"

{ uname -r; bpftool version | head -1; clang --version | head -1; echo "cpus $(nproc)"; date -u
  echo "cmdline: $(cat /proc/cmdline)"
  grep -H . /sys/devices/system/cpu/vulnerabilities/spectre_v1 2>/dev/null
  echo "capabilities without CAP_PERFMON:"; $NOPERFMON grep Cap /proc/self/status
} > "$OUT/versions.txt" 2>&1
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf

sed 's|"../../vmlinux.h"|"vmlinux.h"|' "$REPO/maps/02-hash-map/hashmap.bpf.c" > "$OUT/counter.bpf.c"
clang $CFLAGS -c "$OUT/counter.bpf.c" -o "$OUT/counter.bpf.o"
clang $CFLAGS -c "$LAB/fdcount.bpf.c" -o "$OUT/fdcount.bpf.o"
clang $CFLAGS -DLE8 -c "$LAB/fdcount.bpf.c" -o "$OUT/fdcount8.bpf.o"
for f in wrong show spectre reload; do clang $CFLAGS -c "$LAB/$f.bpf.c" -o "$OUT/$f.bpf.o"; done
clang $CFLAGS -DFIXED -c "$LAB/reload.bpf.c" -o "$OUT/reload-fixed.bpf.o"
for k in 4 8 12 16 20 24; do clang $CFLAGS -DK=$k -c "$LAB/precise.bpf.c" -o "$OUT/precise$k.bpf.o"; done
cc -O2 -Wall "$BOOK/labs/walk/stats.c" -lbpf -o "$OUT/stats"
S="$OUT/stats"

# 1. what you see: the counter and the per-descriptor copy at level 2 (and statistics)
{
"$S" "$OUT/counter.bpf.o" count_writes 6 "$OUT/counter.log"
"$S" "$OUT/fdcount.bpf.o" count_by_fd 6 "$OUT/fdcount.log"
"$S" "$OUT/fdcount8.bpf.o" count_by_fd 6 "$OUT/fdcount8.log"
for p in narrow32 linked spill both64 both32; do "$S" "$OUT/show.bpf.o" $p 6 "$OUT/$p.log"; done
} > "$OUT/see.txt" 2>&1

# the first lab as the book prints it: bpftool -d asks for levels 1, 2 and 4
{
for p in counter fdcount; do
    bpftool -d prog load "$OUT/$p.bpf.o" /sys/fs/bpf/book_numbers_$p 2> "$OUT/lab1-$p.log"
    echo "$p: load exit $?"
    rm -f /sys/fs/bpf/book_numbers_$p
done
} > "$OUT/lab1.txt" 2>&1

# 2. when it goes wrong: each refused copy alone, level 2 with statistics
{
for p in neg_index no_check past_end ptr_unbounded copy32 stack_var pkt_nocheck pkt_check; do
    "$S" "$OUT/wrong.bpf.o" $p 6 "$OUT/wrong-$p.log"
    echo
done
} > "$OUT/wrong.txt" 2>&1

# the second lab: the index read again from the map value after a call, and the fix
{
"$S" "$OUT/reload.bpf.o" reload 6 "$OUT/reload.log"
"$S" "$OUT/reload-fixed.bpf.o" reload 6 "$OUT/reload-fixed.log"
} > "$OUT/lab2.txt" 2>&1

# 3. what precision costs: "matters", "never", the branch-free "matters_flat" and
#    "from_input" at K tests, statistics only, three loads each; then one level-2 log
#    of the first two at K = 8 for the mark_precise lines
{
for k in 4 8 12 16 20 24; do
    for p in matters never matters_flat from_input; do
        for i in 1 2 3; do "$S" "$OUT/precise$k.bpf.o" $p 4 | sed "s/^/K=$k $p /"; done
    done
done
for p in matters never; do "$S" "$OUT/precise8.bpf.o" $p 6 "$OUT/precise8-$p.log" > /dev/null; done
} > "$OUT/precise.txt" 2>&1

# 3b. the same as socket filters, as root and as the user nobody (no CAP_BPF: every
#     scalar precise); sets kernel.unprivileged_bpf_disabled to 0, which only a throwaway
#     VM should do
NOBODY="setpriv --reuid=65534 --regid=65534 --clear-groups --inh-caps=-all"
{
echo "unprivileged_bpf_disabled was $(cat /proc/sys/kernel/unprivileged_bpf_disabled)"
echo 0 > /proc/sys/kernel/unprivileged_bpf_disabled
for k in 4 8 12 16; do
    for p in matters_sk never_sk; do
        for who in root nobody; do
            pre=""; [ "$who" = nobody ] && pre="$NOBODY"
            for i in 1 2 3; do $pre "$S" "$OUT/precise$k.bpf.o" $p 4 | sed "s/^/K=$k $p $who /"; done
        done
    done
done
# with CAP_BPF but without CAP_PERFMON: precision tracking on, Spectre masking on
$NOPERFMON "$S" "$OUT/precise8.bpf.o" matters_sk 4 | sed "s/^/K=8 matters_sk noperfmon /"
$NOPERFMON "$S" "$OUT/precise8.bpf.o" matters_sk 6 "$OUT/precise8-matters_sk-noperfmon.log" > /dev/null
} > "$OUT/precise-unpriv.txt" 2>&1

# 4. speculative execution: one socket filter, as root and without CAP_PERFMON
head -c 18 /dev/zero > "$OUT/pkt18"
{
for who in root noperfmon; do
    pre=""; [ "$who" = noperfmon ] && pre="$NOPERFMON"
    echo "== $who: statistics"
    $pre "$S" "$OUT/spectre.bpf.o" spec 4
    $pre "$S" "$OUT/spectre.bpf.o" spec 6 "$OUT/spectre-$who.log" > /dev/null
    $pre bpftool prog load "$OUT/spectre.bpf.o" /sys/fs/bpf/book_numbers_spec
    echo "== $who: xlated"
    bpftool prog dump xlated pinned /sys/fs/bpf/book_numbers_spec > "$OUT/spectre-$who.xlated"
    cat "$OUT/spectre-$who.xlated"
    echo "instructions: $(grep -cE '^ *[0-9]+:' "$OUT/spectre-$who.xlated")"
    bpftool prog show pinned /sys/fs/bpf/book_numbers_spec
    echo "== $who: test runs, 20 million each"
    for i in 1 2 3; do
        bpftool prog run pinned /sys/fs/bpf/book_numbers_spec data_in "$OUT/pkt18" repeat 20000000
    done
    rm -f /sys/fs/bpf/book_numbers_spec
done
} > "$OUT/spectre.txt" 2>&1

chown -R "${SUDO_UID:-0}:${SUDO_GID:-0}" "$OUT" 2>/dev/null
cat "$OUT/versions.txt"
grep -h 'load ' "$OUT/see.txt" "$OUT/wrong.txt" "$OUT/lab2.txt" | head -20
