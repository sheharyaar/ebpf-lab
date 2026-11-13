/* Three socket filters for the JIT chapter (from labs/costs2-root.sh, 12 November 2026):
 * target returns 0; direct tail-calls slot 0 of jmp, a constant, which the JIT turns into
 * a patched jump; indirect tail-calls a slot computed from the packet's length, which the
 * JIT checks and jumps through at run time. Both return 1 if the tail call falls through. */
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
