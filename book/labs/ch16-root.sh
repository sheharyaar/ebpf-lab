#!/bin/bash
# Chapter 16: sharing maps between programs, map-in-map, program arrays and tail calls.
# Run as root in a throwaway VM (it pins under /sys/fs/bpf and attaches to tracepoints):
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- "bash $PWD/book/labs/ch16-root.sh"
# Builds in /tmp/c16 (the program folder is only read). Output: /tmp/book-labs/ch16/*.txt
#   versions.txt  kernel, CPUs, tool versions
#   share.txt     step 1: the counter and a second program from another object share write_counts
#                 through a pin; what keeps the map alive; libbpf refusing a mismatched pin
#   mem.txt       step 2: memlock of a prog array and of maps of maps; the inner-map template check
#   mim.txt       step 3: ns per run for 64 lookups, plain and through a map of maps (3 rounds)
#   split.txt     step 4: the counter split by a tail call: ns per run, run counts, and the
#                 prog array emptied when its last user reference goes (jited dumps in jit-*.txt,
#                 program addresses in kallsyms-*.txt)
#   owner.txt     step 5: a socket filter refused by the tracepoint programs' prog array
#   poke.txt      step 6: microseconds per prog-array update with 0, 1, 8 and 32 direct callers,
#                 and per swap of an inner map against a plain array write
#   limit.txt     step 7: how many times a program that tail-calls itself runs
# The chapter's two-CPU times for step 6 came from the same VM started with two CPUs:
#   vng -r /boot/vmlinuz-linux --cpus 2 --user root --rwdir /tmp -- "OUT=/tmp/book-labs/ch16-2cpu bash $PWD/book/labs/ch16-root.sh 6"
# Arguments: none = every step; or the step numbers to run, e.g. "4 6". OUT=dir overrides the output folder.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
PROG=$HERE/../program
W=/tmp/c16; OUT=${OUT:-/tmp/book-labs/ch16}
CF="-g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I."
STEPS=${*:-"1 2 3 4 5 6 7"}
want() { case " $STEPS " in *" $1 "*) return 0;; esac; return 1; }
mkdir -p $W $OUT; cd $W || exit 1
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
{ uname -r; echo "nproc $(nproc)"; grep -m1 'model name' /proc/cpuinfo
  bpftool version | head -1; clang --version | head -1; } > $OUT/versions.txt 2>&1

# ---- build (no root needed for this part) ----
cp "$HERE"/ch16/* $W/; cp "$PROG/vmlinux.h" $W/
sed -e 's#"../../vmlinux.h"#"vmlinux.h"#' -e '/__type(value, __u64);/a\	__uint(pinning, LIBBPF_PIN_BY_NAME);' \
    "$PROG/maps/02-hash-map/hashmap.bpf.c" > counter_pin.bpf.c
sed -e 's#"../../vmlinux.h"#"vmlinux.h"#' -e '/bpf_printk/d' \
    "$PROG/maps/02-hash-map/hashmap.bpf.c" > wc_noprintk.bpf.c
{ for o in counter_pin wc_noprintk forget split poke limit; do clang $CF -c $o.bpf.c -o $o.bpf.o; done
  clang $CF -DBIG -c forget.bpf.c -o forget_big.bpf.o
  clang $CF -DSLOT_VAR -c split.bpf.c -o split_var.bpf.o
  for v in 0 1 2 3 4 5; do clang $CF -DVARIANT=$v -c mim.bpf.c -o mim$v.bpf.o; done
  gcc -O2 -Wall pokebench.c -o pokebench -lbpf
  gcc -O2 -Wall limit.c -o limit -lbpf
  gcc -O2 -Wall splitload.c -o splitload -lbpf
  printf '#include <fcntl.h>\n#include <stdlib.h>\n#include <unistd.h>\nint main(int c,char**v){long n=atol(v[1]);int fd=open("/dev/null",O_WRONLY);for(long i=0;i<n;i++)write(fd,"x",1);return 0;}\n' > wloop.c
  gcc -O2 wloop.c -o wloop
  printf '#include <stdlib.h>\n#include <unistd.h>\n#include <sys/syscall.h>\nint main(int c,char**v){long n=atol(v[1]);for(long i=0;i<n;i++)syscall(SYS_getppid);return 0;}\n' > trig.c
  gcc -O2 trig.c -o trig
} > $OUT/build.txt 2>&1
# run_time_ns / run_cnt of a program, by name
stat() { bpftool -j prog show name "$1" 2>/dev/null | python3 -I -c "import json,sys
try: p=json.load(sys.stdin)
except ValueError: print('no such program'); sys.exit()
p=p[0] if isinstance(p,list) else p
c=p.get('run_cnt',0); t=p.get('run_time_ns',0); print('run_cnt %d run_time_ns %d ns_per_run %.1f' % (c, t, t/c if c else 0))"; }
# the sum of a map's values
msum() { bpftool -j map dump "$@" 2>/dev/null | python3 -I -c "import json,sys
try: d=json.load(sys.stdin)
except ValueError: print('(no such map)'); sys.exit()
t=0
for e in d:
    v=e.get('formatted',e)['value']; t+= v if isinstance(v,int) else int.from_bytes(bytes(int(x,16) for x in v),'little')
print(t)"; }
# fell_through, the first variable in the .bss map of the split counter that is loaded
bssval() { local id=$(bpftool -j map show | python3 -I -c "import json,sys; print([m['id'] for m in json.load(sys.stdin) if m.get('name','').endswith('.bss')][-1])")
  bpftool -j map dump id $id | python3 -I -c "import json,sys; v=json.load(sys.stdin)[0]['formatted']['value']['.bss']; print([x['fell_through'] for x in v if 'fell_through' in x][0])"; }
memlock() { bpftool -j map show "$@" | python3 -I -c "import json,sys; print(json.load(sys.stdin).get('bytes_memlock'))"; }

# ---- 1. one map, two programs, two objects, two processes ----
if want 1; then
{
  rm -rf /sys/fs/bpf/write_counts /sys/fs/bpf/c16_counter /sys/fs/bpf/c16_forget
  echo "## the counter, its map pinned by name"
  bpftool -d prog loadall counter_pin.bpf.o /sys/fs/bpf/c16_counter autoattach 2>&1 | grep -i 'pinned map\|pin' | head -3
  echo "## the second object, loaded by a second bpftool process"
  bpftool -d prog loadall forget.bpf.o /sys/fs/bpf/c16_forget autoattach 2>&1 | grep -i 'pinned map' | head -3
  bpftool prog show name count_writes; bpftool prog show name forget_thread
  bpftool map show name write_counts
  ls -l /sys/fs/bpf/write_counts
  for i in $(seq 20); do ./wloop 10; done
  echo "entries after 20 short-lived writers, with forget_thread: $(bpftool -j map dump pinned /sys/fs/bpf/write_counts | python3 -I -c 'import json,sys; print(len(json.load(sys.stdin)))')"
  rm -rf /sys/fs/bpf/c16_forget
  for i in $(seq 20); do ./wloop 10; done
  echo "entries after 20 more, forget_thread unloaded: $(bpftool -j map dump pinned /sys/fs/bpf/write_counts | python3 -I -c 'import json,sys; print(len(json.load(sys.stdin)))')"
  echo "## a third object asks for 2,048 entries"
  bpftool -d prog loadall forget_big.bpf.o /sys/fs/bpf/c16_big autoattach 2>&1 | grep -i 'reuse\|mismatch\|Error' | head -4
  echo "## what keeps the map alive"
  MID=$(bpftool -j map show name write_counts | python3 -I -c "import json,sys; print(json.load(sys.stdin)['id'])")
  rm -rf /sys/fs/bpf/c16_counter; sleep 1
  echo "programs unloaded, pin kept: $(bpftool map show id $MID 2>&1 | head -1)"
  rm -f /sys/fs/bpf/write_counts; sleep 1
  echo "pin removed: $(bpftool map show id $MID 2>&1 | head -1)"
} > $OUT/share.txt 2>&1
fi

# ---- 2. memory, and the inner-map template ----
if want 2; then
{
  D=/sys/fs/bpf/c16_mem; rm -rf $D; mkdir -p $D
  bpftool map create $D/arr type array key 4 value 4 entries 1024 name arr4
  bpftool map create $D/pa type prog_array key 4 value 4 entries 1024 name pa
  bpftool map create $D/pa2 type prog_array key 4 value 4 entries 2 name pa2
  bpftool map create $D/ih type hash key 4 value 8 entries 1024 name ih
  bpftool map create $D/ia type array key 4 value 8 entries 8 name ia
  bpftool map create $D/aom type array_of_maps key 4 value 4 entries 1024 name aom inner_map pinned $D/ih
  bpftool map create $D/hom type hash_of_maps key 4 value 4 entries 1024 name hom inner_map pinned $D/ih
  for m in arr pa pa2 ih ia aom hom; do echo "memlock $m $(memlock pinned $D/$m)"; done
  echo "## the template check: outer maps whose template is a hash of 4-byte keys and 8-byte values"
  bpftool map create $D/h64 type hash key 4 value 8 entries 64 name h64
  bpftool map create $D/h16 type hash key 4 value 16 entries 1024 name h16
  bpftool map create $D/lru type lru_hash key 4 value 8 entries 1024 name lru
  echo "hash, 64 entries:";        bpftool map update pinned $D/aom key 1 0 0 0 value pinned $D/h64 && echo ok
  echo "hash, 16-byte values:";    bpftool map update pinned $D/aom key 2 0 0 0 value pinned $D/h16 && echo ok
  echo "LRU hash, same sizes:";    bpftool map update pinned $D/aom key 3 0 0 0 value pinned $D/lru && echo ok
  echo "## an array as the template: entries must match unless BPF_F_INNER_MAP (0x1000)"
  bpftool map create $D/a16 type array key 4 value 8 entries 16 name a16
  bpftool map create $D/aoa type array_of_maps key 4 value 4 entries 4 name aoa inner_map pinned $D/ia
  echo "array, 16 entries for 8:"; bpftool map update pinned $D/aoa key 0 0 0 0 value pinned $D/a16 && echo ok
  bpftool map create $D/iaf type array key 4 value 8 entries 8 name iaf flags 0x1000
  bpftool map create $D/a16f type array key 4 value 8 entries 16 name a16f flags 0x1000
  bpftool map create $D/aof type array_of_maps key 4 value 4 entries 4 name aof inner_map pinned $D/iaf
  echo "array, 16 for 8, BPF_F_INNER_MAP:"; bpftool map update pinned $D/aof key 0 0 0 0 value pinned $D/a16f && echo ok
  echo "## templates that are refused at creation"
  echo "a prog array as template:"; bpftool map create $D/x1 type array_of_maps key 4 value 4 entries 4 name x1 inner_map pinned $D/pa
  echo "a map of maps as template:"; bpftool map create $D/x2 type array_of_maps key 4 value 4 entries 4 name x2 inner_map pinned $D/aom
  rm -rf $D
} > $OUT/mem.txt 2>&1
fi

# ---- 3. a lookup through a map of maps ----
if want 3; then
{
  sysctl -q -w kernel.bpf_stats_enabled=1
  ./trig 200000
  for r in 1 2 3; do
    for v in 0 1 2 3 4 5; do
      bpftool prog loadall mim$v.bpf.o /sys/fs/bpf/c16_m$v autoattach > /dev/null 2>&1 || echo "load failed v=$v"
      for k in 0 1 2 3 4 5 6 7; do bpftool map update name in_h key $k 0 0 0 value 1 0 0 0 0 0 0 0; done
      [ $r = 1 ] && bpftool prog dump xlated name bench > $OUT/xlated-mim$v.txt 2>&1
      ./trig 1000000
      echo "v=$v round=$r $(stat bench)"
      rm -rf /sys/fs/bpf/c16_m$v; sleep 0.5
    done
  done
  sysctl -q -w kernel.bpf_stats_enabled=0
} > $OUT/mim.txt 2>&1
fi

# ---- 4. the counter split in two by a tail call ----
if want 4; then
{
  sysctl -q -w kernel.bpf_stats_enabled=1
  for r in 1 2 3; do
    # the whole counter without bpf_printk, for comparison
    rm -rf /sys/fs/bpf/c16_w; bpftool prog loadall wc_noprintk.bpf.o /sys/fs/bpf/c16_w autoattach > /dev/null 2>&1
    [ $r = 1 ] && bpftool prog dump jited name count_writes > $OUT/jit-wc_noprintk.txt 2>&1
    taskset -c 1 ./wloop 2000000
    echo "wc_noprintk round=$r count_writes: $(stat count_writes)"
    echo "wc_noprintk round=$r map total $(msum name write_counts)"
    rm -rf /sys/fs/bpf/c16_w; sleep 0.5
    for o in split split_var; do
      coproc L { ./splitload $o.bpf.o hold; }
      read -r ready <&${L[0]}
      [ $r = 1 ] && bpftool prog dump jited name count_writes > $OUT/jit-$o.txt 2>&1
      [ $r = 1 ] && bpftool prog dump xlated name count_writes > $OUT/xlated-$o.txt 2>&1
      [ $r = 1 ] && grep -E 'bpf_prog_[0-9a-f]+_count_(update|writes)' /proc/kallsyms > $OUT/kallsyms-$o.txt
      taskset -c 1 ./wloop 2000000
      echo "$o round=$r count_writes: $(stat count_writes)"
      echo "$o round=$r count_update: $(stat count_update)"
      echo "$o round=$r map total $(msum name write_counts), fell_through $(bssval)"
      echo >&${L[1]}; wait $L_PID 2>/dev/null; sleep 0.5
    done
  done
  echo "## the link pinned, the maps not: the loader exits and the prog array loses its last user reference"
  rm -rf /sys/fs/bpf/c16_link /sys/fs/bpf/c16_maps
  ./splitload split.bpf.o link; sleep 1
  echo "jmp_table: $(bpftool map dump name jmp_table 2>&1 | tr '\n' ' ')"
  bpftool prog dump jited name count_writes > $OUT/jit-split-emptied.txt 2>&1
  taskset -c 1 ./wloop 100000
  echo "after 100000 writes: map total $(msum name write_counts), fell_through $(bssval)"
  echo "count_writes: $(stat count_writes); count_update: $(stat count_update)"
  rm -f /sys/fs/bpf/c16_link; sleep 1
  echo "## the link and the maps pinned"
  ./splitload split.bpf.o link+maps; sleep 1
  echo "jmp_table: $(bpftool map dump pinned /sys/fs/bpf/c16_maps/jmp_table 2>&1 | tr '\n' ' ')"
  taskset -c 1 ./wloop 100000
  echo "after 100000 writes: map total $(msum pinned /sys/fs/bpf/c16_maps/write_counts), fell_through $(bssval)"
  echo "jmp_table memlock $(memlock pinned /sys/fs/bpf/c16_maps/jmp_table)"
  sysctl -q -w kernel.bpf_stats_enabled=0
} > $OUT/split.txt 2>&1
fi

# ---- 5. the owner check (uses the pinned split counter of step 4) ----
if want 5; then
{
  [ -e /sys/fs/bpf/c16_maps/jmp_table ] || ./splitload split.bpf.o link+maps
  rm -rf /sys/fs/bpf/c16_sock /sys/fs/bpf/c16_sock2 /sys/fs/bpf/c16_tp
  bpftool prog loadall poke.bpf.o /sys/fs/bpf/c16_sock
  echo "## a socket filter into the tracepoint programs' array, slot 1"
  bpftool map update pinned /sys/fs/bpf/c16_maps/jmp_table key 1 0 0 0 value pinned /sys/fs/bpf/c16_sock/t1 && echo ok
  echo "## a socket filter that names the same array at load"
  bpftool -d prog loadall poke.bpf.o /sys/fs/bpf/c16_sock2 map name jt pinned /sys/fs/bpf/c16_maps/jmp_table 2>&1 | grep -v '^libbpf: \(elf\|sec\|map .*: found\|prog .*: found\|CO-RE\|loading\|license\|kernel\)' | tail -8
  echo "## a second tracepoint program into slot 1: same type, accepted"
  bpftool prog loadall wc_noprintk.bpf.o /sys/fs/bpf/c16_tp > /dev/null 2>&1
  bpftool map update pinned /sys/fs/bpf/c16_maps/jmp_table key 1 0 0 0 value pinned /sys/fs/bpf/c16_tp/count_writes && echo ok
  bpftool map dump pinned /sys/fs/bpf/c16_maps/jmp_table
  rm -rf /sys/fs/bpf/c16_link /sys/fs/bpf/c16_maps /sys/fs/bpf/c16_sock /sys/fs/bpf/c16_sock2 /sys/fs/bpf/c16_tp
} > $OUT/owner.txt 2>&1
fi

# ---- 6. what an update of a prog-array slot costs ----
if want 6; then
  for r in 1 2 3; do echo "## round $r"; ./pokebench poke.bpf.o; done > $OUT/poke.txt 2>&1
fi

# ---- 7. the tail-call limit ----
if want 7; then
  ./limit limit.bpf.o > $OUT/limit.txt 2>&1
fi
echo "done: $OUT"
