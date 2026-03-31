#include "../../vmlinux.h"
#include <bpf/bpf_helpers.h>

/* TODO: attach to the execve syscall entry tracepoint */
SEC("")
int handle_execve(struct trace_event_raw_sys_enter *ctx)
{
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
