#!/bin/bash
# Chapter 13: helpers and kfuncs from the inside. The steps that need root.
# On the host:        sudo bash book/labs/ch13-root.sh
# In a throwaway VM:  vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- "bash $PWD/book/labs/ch13-root.sh"
# Output: /tmp/book-labs/ch13/*.txt. Builds in /tmp/ch13; the program folder is only read.
# Pins under /sys/fs/bpf/ch13_*, all removed again. ONLY_STEP3=1 skips steps 0-2 (the timing runs).
set -u
OUT=/tmp/book-labs/ch13; W=/tmp/ch13
PROG=$(cd "$(dirname "$0")/../program" && pwd)
mkdir -p "$OUT" "$W"
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
{ uname -r; bpftool version | head -2; clang --version | head -1; nproc; } > "$OUT/versions.txt" 2>&1
CF="-g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I$PROG"
cd "$W" || exit 1

if [ -z "${ONLY_STEP3:-}" ]; then
# 0. the write counter and its loader, as in chapter 11
( cd "$PROG" && clang $CF -c maps/02-hash-map/hashmap.bpf.c -o "$W/hashmap.bpf.o" 2>/dev/null &&
  bpftool gen skeleton "$W/hashmap.bpf.o" > "$W/hashmap.skel.h" && cp maps/02-hash-map/hashmap.c "$W/" &&
  cd "$W" && gcc -g -O2 -Wall -I. hashmap.c -o hashmap -lbpf -lelf -lz ) > "$OUT/build.txt" 2>&1

# 1. call 0x1 and call 0xe: in the object, after the verifier, and the addresses they became
llvm-objdump -d hashmap.bpf.o | grep -E 'call' > "$OUT/objdump-calls.txt"
./hashmap > /dev/null 2>&1 &
LP=$!
sleep 2
bpftool prog dump xlated name count_writes > "$OUT/xlated-counter.txt" 2>&1
bpftool prog dump xlated name count_writes opcodes > "$OUT/xlated-counter-opcodes.txt" 2>&1
grep -w -E '__bpf_call_base|bpf_get_current_pid_tgid|bpf_map_lookup_elem|__htab_map_lookup_elem|htab_map_lookup_elem|htab_map_update_elem|bpf_map_update_elem|bpf_trace_printk|array_map_lookup_elem|bpf_task_from_pid|bpf_task_release' /proc/kallsyms > "$OUT/kallsyms.txt"
kill -TERM $LP; wait $LP 2>/dev/null
# the verifier's view of the call (bpftool -d asks for a log at level 1+2+4)
bpftool -d prog load hashmap.bpf.o /sys/fs/bpf/ch13_hm > "$OUT/verifier-log-counter.txt" 2>&1; rm -f /sys/fs/bpf/ch13_hm

# 2. what one call costs: 64 of the same operation per event, five ways, against a baseline
cat > bench.bpf.c <<'EOF'
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#define N 64
struct { __uint(type, BPF_MAP_TYPE_ARRAY); __uint(max_entries, 8); __type(key, u32); __type(value, u64); } b_arr SEC(".maps");
struct { __uint(type, BPF_MAP_TYPE_ARRAY); __uint(max_entries, 8); __uint(map_flags, BPF_F_INNER_MAP);
         __type(key, u32); __type(value, u64); } b_arrcall SEC(".maps");
struct { __uint(type, BPF_MAP_TYPE_HASH); __uint(max_entries, 8); __type(key, u32); __type(value, u64); } b_hash SEC(".maps");
extern struct task_struct *bpf_task_from_pid(s32 pid) __ksym;
extern void bpf_task_release(struct task_struct *p) __ksym;
u64 sink;
SEC("tracepoint/syscalls/sys_enter_getppid")
int bench(void *ctx)
{
	u32 pid = bpf_get_current_pid_tgid() >> 32;
	u32 key = pid & 7;
	u64 sum = 0;
#pragma unroll
	for (int i = 0; i < N; i++) {
#if VARIANT == 1
		u64 *v = bpf_map_lookup_elem(&b_arr, &key); if (v) sum += *v;
#elif VARIANT == 2
		u64 *v = bpf_map_lookup_elem(&b_arrcall, &key); if (v) sum += *v;
#elif VARIANT == 3
		u64 *v = bpf_map_lookup_elem(&b_hash, &key); if (v) sum += *v;
#elif VARIANT == 4
		sum += bpf_get_current_pid_tgid();
#elif VARIANT == 5
		struct task_struct *t = bpf_task_from_pid(pid);
		if (t) { sum += t->pid; bpf_task_release(t); }
#endif
	}
	sink = sum;
	return 0;
}
char LICENSE[] SEC("license") = "GPL";
EOF
cat > trig.c <<'EOF'
#include <stdlib.h>
#include <unistd.h>
#include <sys/syscall.h>
int main(int argc, char **argv) { long n = argc > 1 ? atol(argv[1]) : 1000000; for (long i = 0; i < n; i++) syscall(SYS_getppid); return 0; }
EOF
gcc -O2 trig.c -o trig
for v in 0 1 2 3 4 5; do clang $CF -I"$W" -DVARIANT=$v -c bench.bpf.c -o bench$v.bpf.o 2>> "$OUT/build.txt"; done
sysctl -q -w kernel.bpf_stats_enabled=1
./trig 200000
: > "$OUT/bench.txt"
for r in 1 2 3; do
  for v in 0 1 2 3 4 5; do
    bpftool prog loadall bench$v.bpf.o /sys/fs/bpf/ch13_b$v autoattach >> "$OUT/bench-load.txt" 2>&1
    if [ $v = 3 ]; then for k in 0 1 2 3 4 5 6 7; do bpftool map update name b_hash key $k 0 0 0 value 1 0 0 0 0 0 0 0; done; fi
    [ $r = 1 ] && bpftool prog dump xlated name bench > "$OUT/xlated-bench$v.txt" 2>&1
    ./trig 1000000
    bpftool -j prog show name bench | python3 -I -c "import json,sys; p=json.load(sys.stdin); p=p[0] if isinstance(p,list) else p; print('v=$v round=$r run_cnt=%d run_time_ns=%d ns_per_run=%.1f xlated=%d jited=%d' % (p['run_cnt'], p['run_time_ns'], p['run_time_ns']/p['run_cnt'], p['bytes_xlated'], p['bytes_jited']))" >> "$OUT/bench.txt" 2>&1
    rm -rf /sys/fs/bpf/ch13_b$v; sleep 0.5
  done
done
sysctl -q -w kernel.bpf_stats_enabled=0
fi

# 3. kfuncs in the counter, and four refusals (the lab and the questions)
mk() {  # $1 = name, rest = sed expressions applied to the counter
  local n=$1; shift
  sed "$@" "$PROG/maps/02-hash-map/hashmap.bpf.c" | sed 's#"../../vmlinux.h"#"vmlinux.h"#' > "$n.bpf.c"
  clang $CF -c "$n.bpf.c" -o "$n.bpf.o" >> "$OUT/build.txt" 2>&1 || echo "build failed: $n" >> "$OUT/build.txt"
}
KDECL='/#include <bpf\/bpf_helpers.h>/a extern struct task_struct *bpf_task_from_pid(s32 pid) __ksym;\nextern void bpf_task_release(struct task_struct *p) __ksym;'
# the lab solution: key by process, found through the task
mk kfunc_ok -e "$KDECL" \
  -e 's|^\tu32 pid = bpf_get_current_pid_tgid();|\tstruct task_struct *t = bpf_task_from_pid((u32)bpf_get_current_pid_tgid());\n\tif (!t)\n\t\treturn 0;\n\tu32 pid = t->tgid;\n\tbpf_task_release(t);|'
mk kfunc_norelease -e "$KDECL" \
  -e 's|^\tu32 pid = bpf_get_current_pid_tgid();|\tstruct task_struct *t = bpf_task_from_pid((u32)bpf_get_current_pid_tgid());\n\tif (!t)\n\t\treturn 0;\n\tu32 pid = t->tgid;|'
mk kfunc_nonull -e "$KDECL" \
  -e 's|^\tu32 pid = bpf_get_current_pid_tgid();|\tstruct task_struct *t = bpf_task_from_pid((u32)bpf_get_current_pid_tgid());\n\tu32 pid = t->tgid;\n\tbpf_task_release(t);|'
mk kfunc_socket -e "$KDECL" -e 's|SEC("tracepoint/syscalls/sys_enter_write")|SEC("socket")|' \
  -e 's|^\tu32 pid = bpf_get_current_pid_tgid();|\tstruct task_struct *t = bpf_task_from_pid(1);\n\tif (!t)\n\t\treturn 0;\n\tu32 pid = t->tgid;\n\tbpf_task_release(t);|'
mk helper_byvalue -e 's|bpf_map_lookup_elem(&write_counts, &pid)|bpf_map_lookup_elem(\&write_counts, (void *)(long)pid)|'
mk helper_license -e 's|"GPL"|"Proprietary"|'
# the lab's common wrong turn: release first, read after
mk kfunc_useafter -e "$KDECL" \
  -e 's|^\tu32 pid = bpf_get_current_pid_tgid();|\tstruct task_struct *t = bpf_task_from_pid((u32)bpf_get_current_pid_tgid());\n\tif (!t)\n\t\treturn 0;\n\tbpf_task_release(t);\n\tu32 pid = t->tgid;|'
# question 13.1: the counter with an array map, as rewritten by the verifier
mk counter_array -e 's|BPF_MAP_TYPE_HASH|BPF_MAP_TYPE_ARRAY|'
llvm-objdump -dr kfunc_ok.bpf.o > "$OUT/objdump-kfunc_ok.txt" 2>&1
for n in kfunc_ok kfunc_norelease kfunc_nonull kfunc_socket helper_byvalue helper_license kfunc_useafter counter_array; do
  bpftool prog load $n.bpf.o /sys/fs/bpf/ch13_$n > "$OUT/load-$n.txt" 2>&1; echo "exit=$?" >> "$OUT/load-$n.txt"
  [ $n = kfunc_ok ] && bpftool prog dump xlated pinned /sys/fs/bpf/ch13_$n > "$OUT/xlated-kfunc_ok.txt" 2>&1
  [ $n = kfunc_ok ] && bpftool prog show pinned /sys/fs/bpf/ch13_$n >> "$OUT/xlated-kfunc_ok.txt" 2>&1
  [ $n = counter_array ] && bpftool prog dump xlated pinned /sys/fs/bpf/ch13_$n > "$OUT/xlated-counter_array.txt" 2>&1
  rm -f /sys/fs/bpf/ch13_$n
done
# the kfunc's BTF ID, which libbpf wrote into the call's immediate
bpftool btf dump file /sys/kernel/btf/vmlinux | grep -E "FUNC 'bpf_task_from_pid'|FUNC 'bpf_task_release'" > "$OUT/btf-ids.txt"
grep -c "DECL_TAG 'bpf_kfunc'" <(bpftool btf dump file /sys/kernel/btf/vmlinux) > "$OUT/kfunc-count.txt"
echo done > "$OUT/done.txt"
