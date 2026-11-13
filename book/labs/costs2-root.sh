#!/bin/bash
# Measurements behind the "What it costs" boxes of chapters 6, 7, 8, 9 and 12 (run 2026-11-12, kernel 7.2.15, VM).
# Build on the host (no root):  bash book/labs/costs2-root.sh build
# Then, as root in a throwaway VM:
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- 'bash /tmp/c612/costs2-root.sh'
# Output: /tmp/book-labs/costs2/*.txt
#   ch06 mask-*.txt   pointer arithmetic with and without Spectre v1 masking (loaded with and without CAP_PERFMON)
#   ch07 tail-*.txt, harden-*.txt   tail calls, constant blinding, JIT limits
#   ch08 hooks.txt    per-write cost of an empty program at a tracepoint, a kprobe and an fentry hook
#   ch09 mapread.txt  memory per map and ns per key read from user space
# Chapter 12 needs no VM: struct sizes come from the host's BTF,
#   bpftool btf dump file /sys/kernel/btf/vmlinux | grep -E "STRUCT '(bpf_verifier_env|bpf_insn_aux_data|bpf_reg_state)'"
# and the test counts from the v7.2 tree: ls tools/testing/selftests/bpf/progs/verifier_*.c | wc -l (121);
#   grep -h 'SEC("' progs/verifier_*.c | grep -v '"\.maps"\|"license"\|"\.data\|"\.bss\|"\.rodata' | wc -l (1,861)
HERE=$(cd "$(dirname "$0")" && pwd)
W=/tmp/c612
if [ "${1:-}" = build ]; then
  set -e
  mkdir -p $W && cp "$0" $W/costs2-root.sh && cp "$HERE/../program/vmlinux.h" $W/
  cd $W
  # ch06: the per-descriptor read of Figure 6.2 as a socket filter, which a CAP_BPF-only loader may load
  cat > mask.bpf.c <<'EOF'
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct slots {
	__u64 n[8];
};

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, struct slots);
} fd_counts SEC(".maps");

SEC("socket")
int count_by_len(struct __sk_buff *skb)
{
	__u32 k = 0;
	__u64 fd = skb->len;
	struct slots *s = bpf_map_lookup_elem(&fd_counts, &k);

	if (s && fd < 8)
		s->n[fd]++;
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
EOF
  # ch07: one tail call through a program array, with a constant key (direct) and a variable one (indirect)
  cat > tail.bpf.c <<'EOF'
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct {
	__uint(type, BPF_MAP_TYPE_PROG_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, __u32);
} jmp SEC(".maps");

SEC("socket")
int target(struct __sk_buff *skb)
{
	return 0;
}

SEC("socket")
int direct(struct __sk_buff *skb)
{
	bpf_tail_call(skb, &jmp, 0);
	return 1;
}

SEC("socket")
int indirect(struct __sk_buff *skb)
{
	bpf_tail_call(skb, &jmp, skb->len - 1);
	return 1;
}

char LICENSE[] SEC("license") = "GPL";
EOF
  # ch08: an empty program at three hooks on the write path
  for h in tp kp fe; do
    case $h in
      tp) sec='tracepoint/syscalls/sys_enter_write' ;;
      kp) sec='kprobe/vfs_write' ;;
      fe) sec='fentry/vfs_write' ;;
    esac
    printf '#include "vmlinux.h"\n#include <bpf/bpf_helpers.h>\n\nSEC("%s")\nint empty_%s(void *ctx)\n{\n\treturn 0;\n}\n\nchar LICENSE[] SEC("license") = "GPL";\n' "$sec" $h > hook_$h.bpf.c
  done
  # ch07: the counter without bpf_printk, for constant blinding
  sed '/bpf_printk/d; s#"../../vmlinux.h"#"vmlinux.h"#' "$HERE/../program/maps/02-hash-map/hashmap.bpf.c" > noprint.bpf.c
  for f in mask tail hook_tp hook_kp hook_fe noprint; do
    clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I. -c $f.bpf.c -o $f.bpf.o
  done
  printf 'abcdefghijklmno' > pkt15        # 15 bytes: skb->len is 1 after the Ethernet header
  gcc -O2 -Wall "$HERE/costs-mapread.c" -o mapread -lbpf
  echo "built in $W"
  exit 0
fi

set -u
ONLY=${1:-all}    # "hooks" re-runs only the chapter 8 measurement
OUT=/tmp/book-labs/costs2; mkdir -p $OUT; cd $W || exit 1
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
P=/sys/fs/bpf
{ uname -r; bpftool version | head -1; echo "nproc $(nproc)"; cat /proc/cmdline
  echo "spectre_v1: $(cat /sys/devices/system/cpu/vulnerabilities/spectre_v1)"
  echo "spectre_v2: $(cat /sys/devices/system/cpu/vulnerabilities/spectre_v2)"
  for s in bpf_jit_enable bpf_jit_harden bpf_jit_kallsyms bpf_jit_limit; do echo "$s $(cat /proc/sys/net/core/$s)"; done
} > versions.txt 2>&1; cp versions.txt $OUT/
run() { bpftool prog run pinned $1 data_in $W/pkt15 repeat ${2:-20000000} 2>&1 | grep -o 'Return value.*'; }

if [ "$ONLY" = all ]; then
# ch06: the same object loaded by full root, and by root without CAP_PERFMON and CAP_SYS_ADMIN
bpftool prog load mask.bpf.o $P/c_mask_root
capsh --drop=cap_perfmon,cap_sys_admin -- -c "grep CapEff /proc/self/status; bpftool prog load mask.bpf.o $P/c_mask_nocap" > $OUT/mask-capsh.txt 2>&1
for v in root nocap; do
  bpftool prog show pinned $P/c_mask_$v > $OUT/mask-show-$v.txt
  bpftool prog dump xlated pinned $P/c_mask_$v > $OUT/mask-xlated-$v.txt
done
for i in 1 2 3; do for v in root nocap; do echo "$v: $(run $P/c_mask_$v)"; done; done > $OUT/mask-run.txt
rm -f $P/c_mask_root $P/c_mask_nocap

# ch07: tail calls
mkdir -p $P/c_tail $P/c_tailmaps
bpftool prog loadall tail.bpf.o $P/c_tail pinmaps $P/c_tailmaps
bpftool map update pinned $P/c_tailmaps/jmp key 0 0 0 0 value pinned $P/c_tail/target
for i in 1 2 3; do for v in target direct indirect; do echo "$v: $(run $P/c_tail/$v)"; done; done > $OUT/tail-run.txt
for v in direct indirect; do bpftool prog dump jited pinned $P/c_tail/$v > $OUT/tail-jited-$v.txt; done
bpftool prog show pinned $P/c_tail/direct > $OUT/tail-show.txt; bpftool prog show pinned $P/c_tail/indirect >> $OUT/tail-show.txt
rm -rf $P/c_tail $P/c_tailmaps

# ch07: constant blinding (bpf_jit_harden=2 blinds root's programs too)
w() { local t0 t1; t0=$(date +%s%N); dd if=/dev/zero of=/dev/null bs=1 count=$1 status=none; t1=$(date +%s%N); echo $(( (t1-t0)/$1 )); }
for hd in 0 2; do
  sysctl -q -w net.core.bpf_jit_harden=$hd
  bpftool prog load noprint.bpf.o $P/c_np$hd autoattach
  bpftool prog show name count_writes > $OUT/harden-$hd-show.txt
  bpftool prog dump xlated name count_writes > $OUT/harden-$hd-xlated.txt
  sysctl -q -w kernel.bpf_stats_enabled=1
  w 1000000 > /dev/null
  bpftool prog show name count_writes > $OUT/harden-$hd-stats.txt
  sysctl -q -w kernel.bpf_stats_enabled=0
  rm -rf $P/c_np$hd; sleep 1
done
sysctl -q -w net.core.bpf_jit_harden=0
fi
w() { local t0 t1; t0=$(date +%s%N); dd if=/dev/zero of=/dev/null bs=1 count=$1 status=none; t1=$(date +%s%N); echo $(( (t1-t0)/$1 )); }

# ch08: per-write cost of an empty program at three hooks; dd does one read() and one write() per byte
w 300000 > /dev/null
hookrun() {
  echo "$1 ns per dd byte: $(w 2000000) $(w 2000000) $(w 2000000) $(w 2000000) $(w 2000000)"
  echo "$1 getppid usecs/op: $(for i in 1 2 3; do perf bench syscall basic -l 5000000 2>&1 | grep -o '[0-9.]* usecs/op' | cut -d' ' -f1; done | tr '\n' ' ')"
}
{
  hookrun none
  for h in tp kp fe; do
    bpftool prog load hook_$h.bpf.o $P/c_hook_$h autoattach || echo "autoattach failed: $h"
    w 300000 > /dev/null
    hookrun $h
    sysctl -q -w kernel.bpf_stats_enabled=1
    w 1000000 > /dev/null
    bpftool prog show name empty_$h | head -3
    sysctl -q -w kernel.bpf_stats_enabled=0
    rm -rf $P/c_hook_$h; sleep 1
  done
  hookrun none-again
} > $OUT/hooks$([ "$ONLY" = all ] || echo -2).txt 2>&1
[ "$ONLY" = all ] || exit 0

# ch09: memory per map and the cost of reading a map from user space
./mapread > $OUT/mapread.txt 2>&1

chmod -R a+r $OUT; echo done > $OUT/done.txt
