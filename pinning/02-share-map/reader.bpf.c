#include "../../vmlinux.h"
#include <bpf/bpf_helpers.h>

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 256);
	__type(key, __u32);
	__type(value, __u64);
} shared_map SEC(".maps");

/* TODO: attach to the execve syscall entry tracepoint */
SEC("")
int reader_execve(struct trace_event_raw_sys_enter *ctx)
{
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
