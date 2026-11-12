#!/usr/bin/env bash
# Root steps for the labs of chapter 4 (walk both paths) and chapter 5 (break it three ways).
# Loads the write counter and eight changed copies, and saves what the kernel says about each.
#
#   sudo bash dossier/labs/ch05-root.sh        (from the playground root, or anywhere)
#
# The playground is only read. Copies, objects and logs go to /tmp/dossier-labs/ch05/.
# Every load either fails (nothing is pinned) or is unpinned at once; nothing is attached.
set -u
REPO=$(cd "$(dirname "$0")/../.." && pwd)
SRC="$REPO/maps/02-hash-map/hashmap.bpf.c"
OUT=/tmp/dossier-labs/ch05
mkdir -p "$OUT"
[ -r "$SRC" ] || { echo "cannot read $SRC" >&2; exit 1; }

# Write the copies: the original (include path fixed) and one file per change.
python3 -I - "$SRC" "$OUT" <<'EOF'
import sys
src, out = sys.argv[1], sys.argv[2]
s = open(src).read().replace('"../../vmlinux.h"', '"vmlinux.h"')
inc = '__atomic_fetch_add(&updated_val, *curr_val, __ATOMIC_SEQ_CST);'
assert inc in s and 'if (curr_val) {' in s, 'the program differs from the one the chapters were written against'
V = {
    'hashmap':  s,
    # chapter 5, the three logs in the figure
    'null':     s.replace('if (curr_val) {', '{'),
    'past':     s.replace(inc, '__atomic_fetch_add(&updated_val, *(curr_val + 1), __ATOMIC_SEQ_CST);'),
    'loop':     s.replace(inc, inc + '\n\t\tfor (u64 i = 0; i < *curr_val; i++)\n\t\t\tbpf_printk("tick %llu", i);'),
    'bounded':  s.replace(inc, inc + '\n\t\tfor (u64 i = 0; i < *curr_val && i < 16; i++)\n\t\t\tbpf_printk("tick %llu", i);'),
    # chapter 5, the lab
    'key':      s.replace('bpf_map_lookup_elem(&write_counts, &pid)', 'bpf_map_lookup_elem(&write_counts, (void *)(long)pid)'),
    'redirect': s.replace('u64 updated_val = 1;', 'u64 updated_val = 1;\n\tbpf_redirect(0, 0);'),
    'var':      s.replace(inc, '__atomic_fetch_add(&updated_val, *(curr_val + (pid & 1)), __ATOMIC_SEQ_CST);'),
}
for k, v in V.items():
    open(f'{out}/{k}.bpf.c', 'w').write(v)
EOF

{ uname -r; bpftool version | head -1; clang --version | head -1; date -u; } > "$OUT/versions.txt"
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf

for v in hashmap null past loop bounded key redirect var; do
    clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I"$REPO" \
          -c "$OUT/$v.bpf.c" -o "$OUT/$v.bpf.o" 2> "$OUT/$v.clang.txt" || { echo "$v: compile failed" >&2; continue; }
    pin=/sys/fs/bpf/dossier_ch05_$v
    if [ "$v" = hashmap ] || [ "$v" = bounded ]; then
        # accepted programs: ask for every step (levels 1, 2 and 4)
        bpftool -d prog load "$OUT/$v.bpf.o" "$pin" > "$OUT/$v.log" 2>&1
    else
        # rejected programs: the log libbpf prints after a failed load (level 1)
        bpftool prog load "$OUT/$v.bpf.o" "$pin" > "$OUT/$v.log" 2>&1
    fi
    echo "exit status $?" >> "$OUT/$v.log"
    rm -f "$pin"
done
chown -R "${SUDO_UID:-0}:${SUDO_GID:-0}" "$OUT"

# One line per load: the reason, or the statistics of an accepted load.
for v in hashmap null past loop bounded key redirect var; do
    printf '%-9s ' "$v"
    grep -E 'invalid|cannot use|too large|type=|outside|^processed' "$OUT/$v.log" | grep -v '^libbpf' | head -2 | paste -sd'|'
done | tee "$OUT/summary.txt"
