/* The write counter split in two programs joined by a tail call.
 * count_writes is attached to the write tracepoint and only jumps; count_update
 * does the counting of hashmap.bpf.c, without its bpf_printk() line.
 * Built twice: as is, the slot is the constant 0 and the JIT writes a direct jump;
 * with -DSLOT_VAR the slot comes from a global in .bss, which the verifier cannot
 * know, so the JIT writes the indirect form with its run-time checks. */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1024);
	__type(key, __u32);
	__type(value, __u64);
} write_counts SEC(".maps");

int count_update(struct trace_event_raw_sys_enter *ctx);

struct {
	__uint(type, BPF_MAP_TYPE_PROG_ARRAY);
	__uint(max_entries, 2);
	__type(key, __u32);
	__array(values, int (struct trace_event_raw_sys_enter *));
} jmp_table SEC(".maps") = {
	.values = { [0] = (void *)&count_update },
};

__u32 slot;		/* .bss: zero, but not a constant to the verifier */
__u64 fell_through;	/* counts runs whose tail call found no program */

SEC("tracepoint/syscalls/sys_enter_write")
int count_writes(struct trace_event_raw_sys_enter *ctx)
{
#ifdef SLOT_VAR
	bpf_tail_call(ctx, &jmp_table, slot);
#else
	bpf_tail_call(ctx, &jmp_table, 0);
#endif
	__sync_fetch_and_add(&fell_through, 1);
	return 0;
}

SEC("tracepoint")
int count_update(struct trace_event_raw_sys_enter *ctx)
{
	u32 pid = bpf_get_current_pid_tgid();
	u64 updated_val = 1;
	u64 *curr_val = bpf_map_lookup_elem(&write_counts, &pid);

	if (curr_val)
		__atomic_fetch_add(&updated_val, *curr_val, __ATOMIC_SEQ_CST);
	bpf_map_update_elem(&write_counts, &pid, &updated_val, BPF_ANY);
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
