// The per-descriptor copy of the write counter (chapter "How the verifier tracks
// numbers", Figures 6.1 and 6.2): eight counters per thread, one per file
// descriptor 0 to 7. Built with -DLE8 the test becomes fd <= 8, one too many.
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct slots {
	__u64 n[8];
};

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1024);
	__type(key, __u32);
	__type(value, struct slots);
} fd_counts SEC(".maps");

SEC("tracepoint/syscalls/sys_enter_write")
int count_by_fd(struct trace_event_raw_sys_enter *ctx)
{
	u32 pid = bpf_get_current_pid_tgid();
	u64 fd = ctx->args[0];
	struct slots *s = bpf_map_lookup_elem(&fd_counts, &pid);

#ifdef LE8
	if (s && fd <= 8)
#else
	if (s && fd < 8)
#endif
		s->n[fd]++;
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
