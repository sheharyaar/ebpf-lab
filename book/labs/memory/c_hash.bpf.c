/* The write counter on a HASH map, as chapter "Maps" chose it: add in place, update only to
 * insert. At fentry/vfs_write, like the two versions that follow, so the three compare. */
#include "mem.h"

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 4096);
	__type(key, u32);
	__type(value, u64);
} write_counts SEC(".maps");

SEC("fentry/vfs_write")
int BPF_PROG(count_writes)
{
	u32 tid = bpf_get_current_pid_tgid();
	u64 one = 1, *v = bpf_map_lookup_elem(&write_counts, &tid);

	if (v)
		__sync_fetch_and_add(v, 1);
	else
		bpf_map_update_elem(&write_counts, &tid, &one, BPF_NOEXIST);
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
