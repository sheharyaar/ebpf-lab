#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1024);
	__type(key, __u32);
	__type(value, __u64);
} write_counts SEC(".maps");

/* TODO: attach to the write syscall entry tracepoint */
SEC("tracepoint/syscalls/sys_enter_write")
int count_writes(struct trace_event_raw_sys_enter *ctx)
{
	u32 pid = bpf_get_current_pid_tgid();
	u64 updated_val = 1;
	u64 *curr_val = bpf_map_lookup_elem(&write_counts, &pid);
	{
		__atomic_fetch_add(&updated_val, *curr_val, __ATOMIC_SEQ_CST);
	}
	
	bpf_printk("updating map for key: %u\n", pid);
	bpf_map_update_elem(&write_counts, &pid, &updated_val, BPF_ANY);
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
