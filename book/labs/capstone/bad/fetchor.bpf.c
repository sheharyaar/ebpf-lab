/* Refused: an atomic OR that returns the old value, on arena memory. The x86 JIT of v7.2
 * cannot emit fetch-and/or/xor on the arena (bpf_jit_supports_insn()), and the verifier
 * asks it first (atomic_ptr_type_ok()). A plain __sync_fetch_and_add is accepted. */
#include "../cms.h"
#include "bpf_arena_common.h"

struct {
	__uint(type, BPF_MAP_TYPE_ARENA);
	__uint(map_flags, BPF_F_MMAPABLE);
	__uint(max_entries, 1);
} arena SEC(".maps");

u64 __arena *flags;			/* set by a syscall program, not shown */

SEC("fentry/vfs_write")
int BPF_PROG(mark)
{
	u64 __arena *f = flags;

	asm volatile("" : : "r"(&arena));
	if (!f)
		return 0;
	if (__sync_fetch_and_or(f, 1) & 1)	/* was it marked already? */
		return 0;
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
