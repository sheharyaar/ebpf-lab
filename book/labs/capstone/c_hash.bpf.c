/* The write counter on a hash, as chapters "Maps" and "Memory you manage" ran it: add in
 * place, insert once, at fentry/vfs_write. Built three times (capstone-root.sh):
 *   c_hash.bpf.o   BPF_MAP_TYPE_HASH,     1,024 entries (chapter "Maps"' write_counts)
 *   c_lru.bpf.o    BPF_MAP_TYPE_LRU_HASH, 1,024 entries
 *   c_exact.bpf.o  BPF_MAP_TYPE_HASH,   262,144 entries: room for every thread */
#include "cms.h"

#ifndef MAPTYPE
#define MAPTYPE BPF_MAP_TYPE_HASH
#endif
#ifndef ENTRIES
#define ENTRIES 1024
#endif

struct {
	__uint(type, MAPTYPE);
	__uint(max_entries, ENTRIES);
	__type(key, u32);
	__type(value, u64);
} write_counts SEC(".maps");

u64 nofit;				/* inserts refused: -E2BIG from a full hash */

SEC("fentry/vfs_write")
int BPF_PROG(count_writes)
{
	u32 tid = counted_tid();
	u64 one = 1, *v;

	if (!tid)
		return 0;
	v = bpf_map_lookup_elem(&write_counts, &tid);
	if (v)
		__sync_fetch_and_add(v, 1);
	else if (bpf_map_update_elem(&write_counts, &tid, &one, BPF_NOEXIST))
		__sync_fetch_and_add(&nofit, 1);
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
