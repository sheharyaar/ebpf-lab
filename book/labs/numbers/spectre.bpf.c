// One pointer operation, loaded with and without CAP_PERFMON, to count the
// instructions the verifier adds against speculative execution. A socket filter,
// because a loader with CAP_BPF alone may load one; tracing programs need
// CAP_PERFMON to load at all, so they never get the masking.
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
} tbl SEC(".maps");

SEC("socket")
int spec(struct __sk_buff *skb)
{
	u32 key = 0, i = skb->len;
	struct slots *s = bpf_map_lookup_elem(&tbl, &key);

	if (!s || i >= 8)
		return 0;
	return s->n[i] + 1;		/* r0 += r1: map value + 0..56 */
}

char LICENSE[] SEC("license") = "GPL";
