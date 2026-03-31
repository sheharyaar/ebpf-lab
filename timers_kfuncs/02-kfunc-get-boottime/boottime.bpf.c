#include "../../vmlinux.h"
#include <bpf/bpf_helpers.h>

extern struct task_struct *bpf_task_from_pid(s32 pid) __ksym;
extern void bpf_task_release(struct task_struct *p) __ksym;

struct task_info {
	__u32 pid;
	__u32 tgid;
	char comm[16];
};

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, struct task_info);
} info_map SEC(".maps");

/* TODO: attach to the execve syscall entry tracepoint */
SEC("")
int lookup_task(struct trace_event_raw_sys_enter *ctx)
{
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
