#!/bin/bash
# Chapter 2 lab: the steps that need root. Records what the lab solution only predicts.
# Run once, from anywhere:  sudo bash dossier/labs/ch02-root.sh
# Output: /tmp/dossier-labs/ch02/*.txt   Touches nothing outside /tmp and one pin under /sys/fs/bpf (removed again).
set -u
OUT=/tmp/dossier-labs/ch02; W=/tmp/ch02
PLAY=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p "$OUT" "$W"
{ uname -r; bpftool version | head -2; strace -V | head -1; } > "$OUT/versions.txt" 2>&1

# 1. build a copy of the loader in /tmp (the playground is only read)
if [ ! -x "$W/hashmap" ]; then
  ( cd "$PLAY" && clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I. \
      -c maps/02-hash-map/hashmap.bpf.c -o "$W/hashmap.bpf.o" 2>/dev/null &&
    bpftool gen skeleton "$W/hashmap.bpf.o" > "$W/hashmap.skel.h" &&
    cp maps/02-hash-map/hashmap.c "$W/" &&
    cd "$W" && gcc -g -O2 -Wall -I. hashmap.c -o hashmap -lbpf -lelf -lz ) > "$OUT/build.txt" 2>&1
fi
cd "$W" || exit 1

# 2. trace the loader while it loads and attaches
strace -f -o "$OUT/strace-full.txt" -e trace=bpf,perf_event_open ./hashmap > "$OUT/loader-stdout.txt" 2>&1 &
sleep 3
LPID=$(pgrep -n -x hashmap)
ls -l /proc/"$LPID"/fd > "$OUT/loader-fds.txt" 2>&1
cat /sys/kernel/tracing/events/syscalls/sys_enter_write/id > "$OUT/tracepoint-id.txt" 2>&1
bpftool prog show name count_writes > "$OUT/prog-show.txt" 2>&1
bpftool link show > "$OUT/link-show.txt" 2>&1
bpftool map show > "$OUT/map-show.txt" 2>&1

# 3. pin the link, stop the loader, watch the program keep running
PROG_ID=$(bpftool -j prog show name count_writes | python3 -I -c 'import json,sys; d=json.load(sys.stdin); d=d[0] if isinstance(d,list) else d; print(d["id"])')
LINK_ID=$(bpftool -j link show | python3 -I -c "import json,sys; print(next(l['id'] for l in json.load(sys.stdin) if l.get('prog_id')==$PROG_ID))")
echo "prog $PROG_ID link $LINK_ID" > "$OUT/ids.txt"
bpftool link pin id "$LINK_ID" /sys/fs/bpf/dossier_ch02_wc >> "$OUT/ids.txt" 2>&1
pkill -TERM -x hashmap; wait
sleep 1
bpftool prog show name count_writes > "$OUT/prog-after-exit.txt" 2>&1
bpftool map dump name write_counts 2>&1 | tail -3 > "$OUT/map-after-exit-1.txt"
sleep 3
bpftool map dump name write_counts 2>&1 | tail -3 > "$OUT/map-after-exit-2.txt"
rm -f /sys/fs/bpf/dossier_ch02_wc
sleep 1
bpftool prog show name count_writes > "$OUT/prog-after-unpin.txt" 2>&1

# 4. the lines the solution quotes
grep -E 'write_counts|rodata|insn_cnt=27|LINK_CREATE|perf_event_open' "$OUT/strace-full.txt" | cut -c1-140 > "$OUT/strace-grep.txt"
grep -c 'bpf(BPF_PROG_LOAD' "$OUT/strace-full.txt" > "$OUT/strace-prog-load-count.txt"
head -c 1500 "$OUT/loader-stdout.txt" > "$OUT/loader-stdout-head.txt"
chmod -R a+r "$OUT"
echo "ch02 done: $OUT"
