#include "../../vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

/* TODO: attach to the scheduler fork tracepoint using BTF-typed tracepoint */
SEC("")
int BPF_PROG(handle_fork, struct task_struct *parent, struct task_struct *child)
{
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
