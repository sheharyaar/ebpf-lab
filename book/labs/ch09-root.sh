#!/bin/bash
# Chapter 9 figures and lab: the steps that need root.
# On the host:        sudo bash book/labs/ch09-root.sh
# In a throwaway VM:  vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- "bash $PWD/book/labs/ch09-root.sh"
# Output: /tmp/book-labs/ch09/*.txt. Builds in /tmp/ch09; the program folder is only read.
set -u
OUT=/tmp/book-labs/ch09; W=/tmp/ch09
PROG=$(cd "$(dirname "$0")/../program" && pwd)
mkdir -p "$OUT" "$W"
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
mountpoint -q /sys/kernel/tracing || mount -t tracefs tracefs /sys/kernel/tracing
{ uname -r; bpftool version | head -1; echo "possible CPUs: $(cat /sys/devices/system/cpu/possible)"; } > "$OUT/versions.txt" 2>&1

# 1. copies of the loader: as written, and with the iteration fixed
if [ ! -x "$W/hashmap" ] || [ ! -x "$W/hashmap-fixed" ]; then
  ( cd "$PROG" && clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I. \
      -c maps/02-hash-map/hashmap.bpf.c -o "$W/hashmap.bpf.o" 2>/dev/null &&
    bpftool gen skeleton "$W/hashmap.bpf.o" > "$W/hashmap.skel.h" &&
    cp maps/02-hash-map/hashmap.c "$W/" &&
    cd "$W" && gcc -g -O2 -Wall -I. hashmap.c -o hashmap -lbpf -lelf -lz &&
    python3 -I - "$W/hashmap.c" "$W/hashmap-fixed.c" <<'PY'
import sys
s = open(sys.argv[1]).read()
s = s.replace("uint32_t prev_key = 0;", "uint32_t prev_key = 0;\n\t\tuint32_t *prev = NULL;\t/* NULL asks for the first key */")
s = s.replace("get_next_key(skel->maps.write_counts, &prev_key, &key", "get_next_key(skel->maps.write_counts, prev, &key")
s = s.replace("\t\t\t\tprintf(\"%u\\t%lu\\n\", key, val);\n\t\t\t}\n",
              "\t\t\t\tprintf(\"%u\\t%lu\\n\", key, val);\n\t\t\t}\n\t\t\tprev_key = key;\t/* the next call starts after this key */\n\t\t\tprev = &prev_key;\n")
assert s.count("prev = &prev_key") == 1, "patch did not apply"
open(sys.argv[2], "w").write(s)
PY
    gcc -g -O2 -Wall -I. hashmap-fixed.c -o hashmap-fixed -lbpf -lelf -lz &&
    diff -u hashmap.c hashmap-fixed.c > "$OUT/fix.diff" ) > "$OUT/build.txt" 2>&1
fi
cd "$W" || exit 1

# a steady writer, so that the map has keys
( while :; do echo x > /dev/null; sleep 0.1; done ) &
WR=$!

# 2. the loader as written: the first 12 lines, and Ctrl-C ignored
./hashmap 2>&1 | head -n 12 > "$OUT/loader-as-written.txt"
./hashmap > /dev/null 2>&1 &
LP=$!
sleep 13
kill -INT $LP; sleep 2
{ echo "after SIGINT:"; ps -o pid=,stat=,etime=,args= -p $LP; } > "$OUT/loader-sigint.txt" 2>&1

# 3. the map and the program, seen from outside while that loader runs
bpftool map show name write_counts > "$OUT/map-show.txt" 2>&1
bpftool map dump name write_counts 2>&1 | head -n 12 > "$OUT/map-dump.txt"
bpftool prog show name count_writes > "$OUT/prog-show.txt" 2>&1
bpftool prog dump xlated name count_writes > "$OUT/xlated.txt" 2>&1
bpftool prog dump xlated name count_writes opcodes 2>&1 | head -n 40 > "$OUT/xlated-opcodes.txt"
kill -TERM $LP; wait $LP 2>/dev/null

# 4. the fixed loader: two rounds, then Ctrl-C (SIGINT) ends it
timeout -s INT 23 ./hashmap-fixed > "$OUT/loader-fixed.txt" 2>&1
echo "exit=$?" >> "$OUT/loader-fixed.txt"

kill $WR 2>/dev/null
chmod -R a+r "$OUT"; echo "ch09 done: $OUT"
