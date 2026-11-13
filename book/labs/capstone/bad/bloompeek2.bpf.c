/* Refused on v7.2: a peek of a bloom filter with a value on the stack (see bloompeek.bpf.c). */
#include "../cms.h"

struct {
	__uint(type, BPF_MAP_TYPE_BLOOM_FILTER);
	__type(value, u64);
	__uint(max_entries, 1024);
} bloom SEC(".maps");

u64 seen;

SEC("fentry/vfs_write")
int BPF_PROG(bloom_test)
{
	u64 tid = counted_tid();

	if (!tid)
		return 0;
	if (bpf_map_peek_elem(&bloom, &tid) == 0)
		seen++;
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
