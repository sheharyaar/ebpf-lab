/* Socket filters for timing prog-array updates (pokebench.c).
 * caller tail-calls the constant slot 0, so the JIT gives it a poke descriptor and the
 * array patches its code whenever slot 0 changes; caller_var takes the slot from .bss
 * and gets the indirect form, which nothing patches. t1 and t2 are the targets. */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct {
	__uint(type, BPF_MAP_TYPE_PROG_ARRAY);
	__uint(max_entries, 4);
	__type(key, __u32);
	__type(value, __u32);
} jt SEC(".maps");

__u32 slot;

SEC("socket")
int caller(struct __sk_buff *skb)
{
	bpf_tail_call(skb, &jt, 0);
	return 0;
}

SEC("socket")
int caller_var(struct __sk_buff *skb)
{
	bpf_tail_call(skb, &jt, slot);
	return 0;
}

SEC("socket")
int t1(struct __sk_buff *skb)
{
	return 1;
}

SEC("socket")
int t2(struct __sk_buff *skb)
{
	return 2;
}

char LICENSE[] SEC("license") = "GPL";
