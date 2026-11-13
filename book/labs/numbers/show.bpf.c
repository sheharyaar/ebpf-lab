// Programs the verifier accepts, for the chapter "How the verifier tracks
// numbers": a 32-bit test, a test made on a copy of the index, a test on an
// index kept on the stack, and two tests whose both sides use the value. Each is loaded alone with labs/walk/stats.c at log
// level 2; none is attached.
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

#define LOOKUP()							\
	u32 pid = bpf_get_current_pid_tgid();				\
	struct slots *s = bpf_map_lookup_elem(&fd_counts, &pid)

/* the test on a 32-bit index compiles to a 32-bit jump */
SEC("tracepoint/syscalls/sys_enter_write")
int narrow32(struct trace_event_raw_sys_enter *ctx)
{
	u32 fd = ctx->args[0];
	LOOKUP();

	if (s && fd < 8)
		s->n[fd]++;
	return 0;
}

/* the test is made on a copy; the empty asm keeps the copy in its own register */
SEC("tracepoint/syscalls/sys_enter_write")
int linked(struct trace_event_raw_sys_enter *ctx)
{
	u64 fd = ctx->args[0], copy = fd;
	LOOKUP();

	barrier_var(copy);
	if (s && copy < 8)
		s->n[fd]++;
	return 0;
}

/* the index lives on the stack (volatile), so the test and the index are two
 * separate loads from the same stack slot */
SEC("tracepoint/syscalls/sys_enter_write")
int spill(struct trace_event_raw_sys_enter *ctx)
{
	volatile u64 fd = ctx->args[0];
	LOOKUP();

	if (s && fd < 8)
		s->n[fd]++;
	return 0;
}

/* both sides of a 64-bit test use the value, so the log prints both states */
SEC("tracepoint/syscalls/sys_enter_write")
int both64(struct trace_event_raw_sys_enter *ctx)
{
	u64 fd = ctx->args[0];
	LOOKUP();

	if (!s)
		return 0;
	if (fd < 8)
		s->n[fd]++;
	else
		s->n[0] += fd;
	return 0;
}

/* the same with a 32-bit index, and so a 32-bit test */
SEC("tracepoint/syscalls/sys_enter_write")
int both32(struct trace_event_raw_sys_enter *ctx)
{
	u32 fd = ctx->args[0];
	LOOKUP();

	if (!s)
		return 0;
	if (fd < 8)
		s->n[fd]++;
	else
		s->n[0] += fd;
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
