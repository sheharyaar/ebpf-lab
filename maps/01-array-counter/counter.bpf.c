#include "../../vmlinux.h"
#include <bpf/bpf_helpers.h>

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, __u64);
} counter_map SEC(".maps");

/* TODO: attach to the execve syscall entry tracepoint */
SEC("")
int count_execve(struct trace_event_raw_sys_enter *ctx)
{
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
