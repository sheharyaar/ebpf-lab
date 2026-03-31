#include "../../vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include "ringbuf.h"

struct {
	__uint(type, BPF_MAP_TYPE_RINGBUF);
	__uint(max_entries, 256 * 1024);
} events SEC(".maps");

/* TODO: attach to the scheduler exec tracepoint using BTF-typed tracepoint */
SEC("")
int BPF_PROG(handle_exec, struct task_struct *p, pid_t old_pid,
	     struct linux_binprm *bprm)
{
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
