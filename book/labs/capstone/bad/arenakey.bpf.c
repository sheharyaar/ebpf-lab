/* Refused: a key that lives in the arena, handed to a map helper. A helper takes memory
 * on the stack, in a map value, a packet and a few more, and arena memory is none of
 * them; copy the key to the stack first. */
#include "../cms.h"
#include "bpf_arena_common.h"

struct {
	__uint(type, BPF_MAP_TYPE_ARENA);
	__uint(map_flags, BPF_F_MMAPABLE);
	__uint(max_entries, 1);
} arena SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1024);
	__type(key, u32);
	__type(value, u64);
} write_counts SEC(".maps");

u32 __arena *keys;			/* thread IDs that a program wrote to the arena */

SEC("fentry/vfs_write")
int BPF_PROG(count_listed)
{
	u32 __arena *k = keys;
	u64 one = 1;

	asm volatile("" : : "r"(&arena));
	if (!k)
		return 0;
	bpf_map_update_elem(&write_counts, (const void *)k, &one, BPF_ANY);
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
