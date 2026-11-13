/* Refused on v7.2: push, then peek a bloom filter with the same value on the stack. Stack
 * liveness reads peek's prototype (MEM_UNINIT: write-only) where the verifier reads the bloom
 * filter's case (a read): "slot poisoned by dead code elimination". Mainline: 830e4372de5c. */
#include "../cms.h"

struct {
	__uint(type, BPF_MAP_TYPE_BLOOM_FILTER);
	__type(value, u64);
	__uint(max_entries, 1024);
} bloom SEC(".maps");

u64 seen;

SEC("fentry/vfs_write")
int BPF_PROG(bloom_seen)
{
	u64 tid = counted_tid();

	if (!tid)
		return 0;
	bpf_map_push_elem(&bloom, &tid, BPF_ANY);
	if (bpf_map_peek_elem(&bloom, &tid) == 0)
		seen++;
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
