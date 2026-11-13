#!/bin/bash
# Chapter "calls" (Calling the kernel: helpers and kfuncs): what the chapter adds to book/labs/ch13-root.sh.
#   1. the counter as the kernel shows it: its four calls in the object, in the verifier log and after the rewrite
#   2. which helpers each program type may call: bpftool feature probe kernel full, counted per type
#   3. which helper calls the verifier replaces with instructions (labs/calls/inline.bpf.c)
#   4. what one call costs: ch13's bench with four more variants (labs/calls/bench.bpf.c), median of three runs
#   5. refusals: copies of the counter with one change each, every load's output in load-<name>.txt
#   6. a bpf_printk() in an XDP program, loaded as root and with CAP_PERFMON and CAP_SYS_ADMIN dropped (labs/calls/xdp_printk.bpf.c)
#   ONLY_STEP6=1 skips steps 1-5.
# Build on the host (no root; clang and bpftool):
#   bash book/labs/calls-root.sh build
# Then, as root in a throwaway VM:
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- 'bash /tmp/calls-w/calls-root.sh'
# Output: /tmp/book-labs/calls/*.txt. Pins under /sys/fs/bpf/calls_*, all removed again.
HERE=$(cd "$(dirname "$0")" && pwd)
W=/tmp/calls-w
CF="-g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I$W"

if [ "${1:-}" = build ]; then
  mkdir -p $W && cp "$0" $W/calls-root.sh && cd $W || exit 1
  cp "$HERE/../program/vmlinux.h" "$HERE"/calls/*.bpf.c $W/
  SRC="$HERE/../program/maps/02-hash-map/hashmap.bpf.c"
  : > build.txt
  mk() {  # $1 = name, rest = sed expressions applied to the counter
    local n=$1; shift
    sed -e '' "$@" "$SRC" | sed 's#"../../vmlinux.h"#"vmlinux.h"#' > $n.bpf.c
    clang $CF -c $n.bpf.c -o $n.bpf.o 2>> build.txt || echo "build failed: $n" >> build.txt
  }
  INC='/#include <bpf\/bpf_helpers.h>/a'
  A='s|^\tu64 updated_val = 1;|&\n\t'   # the counter's second line, then a new line: "$A...|" 
  mk counter
  # a helper ID past the last one
  mk badid -e "$INC static long (* const bpf_nohelper)(void) = (void *) 300;" -e "${A}bpf_nohelper();|"
  # a helper that only kprobe programs may call
  mk override -e "${A}bpf_override_return((void *)ctx, 0);|"
  # a helper that may sleep, and a kfunc that may sleep, in a program that may not
  mk sleephelp -e "${A}char buf[16];\n\tbpf_copy_from_user(buf, sizeof(buf), (const void *)ctx->args[1]);|"
  mk sleepkf -e "${A}char buf[16];\n\tbpf_copy_from_user_str(buf, sizeof(buf), (const void *)ctx->args[1], 0);|"
  mk sleepkf_s -e "${A}char buf[16];\n\tbpf_copy_from_user_str(buf, sizeof(buf), (const void *)ctx->args[1], 0);|" \
     -e 's|SEC("tracepoint/syscalls/sys_enter_write")|SEC("tp.s/syscalls/sys_enter_write")|'
  # a kfunc this kernel does not have: declared plainly, declared __weak, and __weak behind bpf_ksym_exists()
  mk missing -e "$INC extern u32 bpf_book_missing(u32 pid) __ksym;" -e "${A}pid = bpf_book_missing(pid);|"
  mk missing_weak -e "$INC extern u32 bpf_book_missing(u32 pid) __ksym __weak;" -e "${A}pid = bpf_book_missing(pid);|"
  mk missing_guard -e "$INC extern u32 bpf_book_missing(u32 pid) __ksym __weak;" \
     -e "${A}if (bpf_ksym_exists(bpf_book_missing))\n\t\tpid = bpf_book_missing(pid);|"
  llvm-objdump -dr counter.bpf.o > objdump-counter.txt
  llvm-objdump -dr missing_guard.bpf.o > objdump-missing_guard.txt
  clang $CF -c inline.bpf.c -o inline.bpf.o 2>> build.txt
  clang $CF -c xdp_printk.bpf.c -o xdp_printk.bpf.o 2>> build.txt
  for v in 0 1 2 3 4 5 6 7 8 9; do clang $CF -DVARIANT=$v -c bench.bpf.c -o bench$v.bpf.o 2>> build.txt; done
  printf '#include <stdlib.h>\n#include <unistd.h>\n#include <sys/syscall.h>\nint main(int c, char **v)\n{ long n = c > 1 ? atol(v[1]) : 1000000; for (long i = 0; i < n; i++) syscall(SYS_getppid); return 0; }\n' > trig.c
  gcc -O2 trig.c -o trig
  grep -c 'build failed' build.txt
  exit 0
fi

OUT=/tmp/book-labs/calls
mkdir -p $OUT && cd $W || exit 1
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
{ uname -r; bpftool version | head -2; clang --version | head -1; nproc; date -u; } > $OUT/versions.txt 2>&1
cp build.txt objdump-*.txt $OUT/

if [ -z "${ONLY_STEP6:-}" ]; then

# 1. the counter: the verifier log (bpftool -d asks for the log) and the program after the rewrite
bpftool -d prog load counter.bpf.o /sys/fs/bpf/calls_counter > $OUT/log-counter.txt 2>&1
bpftool prog dump xlated pinned /sys/fs/bpf/calls_counter > $OUT/xlated-counter.txt 2>&1
bpftool prog show pinned /sys/fs/bpf/calls_counter >> $OUT/xlated-counter.txt 2>&1
rm -f /sys/fs/bpf/calls_counter

# 2. which helpers each program type may call
bpftool feature probe kernel full > $OUT/probe-full.txt 2>&1
python3 -I - $OUT/probe-full.txt > $OUT/probe-counts.txt <<'EOF'
import re, sys
cur = None; n = {}
for line in open(sys.argv[1]):
    m = re.match(r'eBPF helpers supported for program type (\S+):', line)
    if m: cur = m.group(1); n[cur] = 0; continue
    if cur and line.strip().startswith('- '): n[cur] += 1
    elif cur and line.strip() == '': cur = None
for k, v in sorted(n.items(), key=lambda kv: -kv[1]): print(f'{v:4d} {k}')
EOF

# 3. which helper calls become instructions
bpftool prog load inline.bpf.o /sys/fs/bpf/calls_inl > $OUT/load-inline.txt 2>&1
bpftool prog dump xlated pinned /sys/fs/bpf/calls_inl > $OUT/xlated-inline.txt 2>&1
llvm-objdump -d inline.bpf.o > $OUT/objdump-inline.txt 2>&1
rm -f /sys/fs/bpf/calls_inl

# 4. what one call costs
sysctl -q -w kernel.bpf_stats_enabled=1
./trig 200000
: > $OUT/bench.txt
for r in 1 2 3; do
  for v in 0 1 2 3 4 5 6 7 8 9; do
    bpftool prog loadall bench$v.bpf.o /sys/fs/bpf/calls_b$v autoattach >> $OUT/bench-load.txt 2>&1
    if [ $v = 3 ]; then for k in 0 1 2 3 4 5 6 7; do bpftool map update name b_hash key $k 0 0 0 value 1 0 0 0 0 0 0 0; done; fi
    [ $r = 1 ] && bpftool prog dump xlated name bench > $OUT/xlated-bench$v.txt 2>&1
    ./trig 1000000
    bpftool -j prog show name bench | python3 -I -c "import json,sys; p=json.load(sys.stdin); p=p[0] if isinstance(p,list) else p; print('v=$v round=$r run_cnt=%d run_time_ns=%d ns_per_run=%.1f xlated=%d jited=%d' % (p['run_cnt'], p['run_time_ns'], p['run_time_ns']/p['run_cnt'], p['bytes_xlated'], p['bytes_jited']))" >> $OUT/bench.txt 2>&1
    rm -rf /sys/fs/bpf/calls_b$v; sleep 0.5
  done
done
sysctl -q -w kernel.bpf_stats_enabled=0

# 5. refusals, and two copies that load
for n in badid override sleephelp sleepkf sleepkf_s missing missing_weak missing_guard; do
  bpftool prog load $n.bpf.o /sys/fs/bpf/calls_$n > $OUT/load-$n.txt 2>&1; echo "exit=$?" >> $OUT/load-$n.txt
  if [ -e /sys/fs/bpf/calls_$n ]; then
    bpftool prog dump xlated pinned /sys/fs/bpf/calls_$n > $OUT/xlated-$n.txt 2>&1
    rm -f /sys/fs/bpf/calls_$n
  fi
done
# the same plain extern, with libbpf's debug output: where the load stops
bpftool -d prog load missing.bpf.o /sys/fs/bpf/calls_missing > $OUT/load-missing-debug.txt 2>&1; rm -f /sys/fs/bpf/calls_missing
bpftool btf dump file /sys/kernel/btf/vmlinux | grep -E "FUNC 'bpf_copy_from_user_str'|FUNC 'bpf_task_from_pid'" > $OUT/btf-ids.txt
fi

# 6. the same XDP program, loaded with every capability and without CAP_PERFMON (and CAP_SYS_ADMIN, which
#    bpf_ns_capable() in kernel/bpf/token.c accepts in place of any other)
bpftool prog load xdp_printk.bpf.o /sys/fs/bpf/calls_xdp > $OUT/load-xdp-root.txt 2>&1; echo "exit=$?" >> $OUT/load-xdp-root.txt
rm -f /sys/fs/bpf/calls_xdp
capsh --drop=cap_perfmon,cap_sys_admin -- -c 'grep CapEff /proc/self/status; bpftool prog load xdp_printk.bpf.o /sys/fs/bpf/calls_xdp' \
  > $OUT/load-xdp-noperfmon.txt 2>&1; echo "exit=$?" >> $OUT/load-xdp-noperfmon.txt
rm -f /sys/fs/bpf/calls_xdp
echo done > $OUT/done.txt
