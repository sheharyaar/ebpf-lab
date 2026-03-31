#include "../../vmlinux.h"
#include <bpf/bpf_helpers.h>

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1024);
	__type(key, __u32);
	__type(value, __u64);
} write_counts SEC(".maps");

/* TODO: attach to the write syscall entry tracepoint */
SEC("")
int count_writes(struct trace_event_raw_sys_enter *ctx)
{
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
