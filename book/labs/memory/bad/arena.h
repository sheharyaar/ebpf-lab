/* an arena for the programs in this folder that the verifier refuses */
#include "mem.h"

struct {
	__uint(type, BPF_MAP_TYPE_ARENA);
	__uint(map_flags, BPF_F_MMAPABLE);
	__uint(max_entries, 16);
} arena SEC(".maps");

#include "bpf_arena_alloc.h"

char LICENSE[] SEC("license") = "GPL";
