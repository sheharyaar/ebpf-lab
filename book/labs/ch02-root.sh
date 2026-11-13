#!/bin/bash
# Chapter 2 lab: the steps that need root. Records what the lab solution quotes.
# On the host:        sudo bash book/labs/ch02-root.sh
# In a throwaway VM:  vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- "bash $PWD/book/labs/ch02-root.sh"
# Output: /tmp/book-labs/ch02/*.txt. Builds in /tmp/ch02; one pin under /sys/fs/bpf, removed again.
set -u
OUT=/tmp/book-labs/ch02; W=/tmp/ch02
PROG=$(cd "$(dirname "$0")/../program" && pwd)
mkdir -p "$OUT" "$W"
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
mountpoint -q /sys/kernel/tracing || mount -t tracefs tracefs /sys/kernel/tracing
{ uname -r; bpftool version | head -2; strace -V | head -1; } > "$OUT/versions.txt" 2>&1

# 1. a copy of the loader in /tmp (the program folder is only read)
if [ ! -x "$W/hashmap" ]; then
  ( cd "$PROG" && clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I. \
      -c maps/02-hash-map/hashmap.bpf.c -o "$W/hashmap.bpf.o" 2>/dev/null &&
    bpftool gen skeleton "$W/hashmap.bpf.o" > "$W/hashmap.skel.h" &&
    cp maps/02-hash-map/hashmap.c "$W/" &&
    cd "$W" && gcc -g -O2 -Wall -I. hashmap.c -o hashmap -lbpf -lelf -lz ) > "$OUT/build.txt" 2>&1
fi
cd "$W" || exit 1

# 2. trace the loader while it loads and attaches (its read loop never ends; stdout goes nowhere)
strace -f -o "$OUT/strace-full.txt" -e trace=bpf,perf_event_open ./hashmap > /dev/null 2>&1 &
SPID=$!
sleep 3
LPID=$(pgrep -n -x hashmap)
ls -l /proc/"$LPID"/fd 2>&1 | grep -v ' -> /dev/' > "$OUT/loader-fds.txt"
cat /sys/kernel/tracing/events/syscalls/sys_enter_write/id > "$OUT/tracepoint-id.txt" 2>&1
bpftool prog show name count_writes > "$OUT/prog-show.txt" 2>&1
bpftool link show > "$OUT/link-show.txt" 2>&1
bpftool map show > "$OUT/map-show.txt" 2>&1

# 3. pin the link, stop the loader, watch the program keep running, then unpin
PROG_ID=$(bpftool -j prog show name count_writes | python3 -I -c 'import json,sys; d=json.load(sys.stdin); d=d[0] if isinstance(d,list) else d; print(d["id"])')
LINK_ID=$(bpftool -j link show | python3 -I -c "import json,sys; print(next(l['id'] for l in json.load(sys.stdin) if l.get('prog_id')==$PROG_ID))")
echo "prog $PROG_ID link $LINK_ID" > "$OUT/ids.txt"
bpftool link pin id "$LINK_ID" /sys/fs/bpf/wc >> "$OUT/ids.txt" 2>&1
pkill -TERM -x hashmap; wait "$SPID"
sleep 1
bpftool prog show name count_writes > "$OUT/prog-after-exit.txt" 2>&1
bpftool map dump name write_counts 2>&1 | grep -c '"key"' > "$OUT/map-keys-after-exit-1.txt"
sleep 3
bpftool map dump name write_counts 2>&1 | grep -c '"key"' > "$OUT/map-keys-after-exit-2.txt"
bpftool map dump name write_counts 2>&1 | tail -5 > "$OUT/map-tail-after-exit.txt"
rm -f /sys/fs/bpf/wc
sleep 1
bpftool prog show name count_writes > "$OUT/prog-after-unpin.txt" 2>&1
echo "exit=$?" >> "$OUT/prog-after-unpin.txt"

# 4. the lines the solution quotes (the read loop's calls left out)
grep -v -E 'GET_NEXT_KEY|MAP_LOOKUP_ELEM|^[0-9]+ +---|\+\+\+' "$OUT/strace-full.txt" | cut -c1-170 > "$OUT/strace-load-attach.txt"
grep -cE 'MAP_GET_NEXT_KEY' "$OUT/strace-full.txt" > "$OUT/strace-loop-count.txt"
rm -f "$OUT/strace-full.txt"
chmod -R a+r "$OUT"
echo "ch02 done: $OUT"
