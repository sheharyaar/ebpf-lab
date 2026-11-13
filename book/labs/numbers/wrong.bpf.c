// Small copies of the per-descriptor counter, most of them refused for one reason
// about numbers, for the "when it goes wrong" table of the chapter "How the
// verifier tracks numbers" (the second lab's program is reload.bpf.c). Each is
// loaded alone with labs/walk/stats.c; none is attached.
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

/* 1. a signed index: fd < 8 says nothing about fd >= 0 */
SEC("tracepoint/syscalls/sys_enter_write")
int neg_index(struct trace_event_raw_sys_enter *ctx)
{
	int fd = ctx->args[0];
	LOOKUP();

	if (s && fd < 8)
		s->n[fd]++;
	return 0;
}

/* 2. a 32-bit index with no test at all */
SEC("tracepoint/syscalls/sys_enter_write")
int no_check(struct trace_event_raw_sys_enter *ctx)
{
	u32 fd = ctx->args[0];
	LOOKUP();

	if (s)
		s->n[fd]++;
	return 0;
}

/* 3. one slot too many: fd <= 8 */
SEC("tracepoint/syscalls/sys_enter_write")
int past_end(struct trace_event_raw_sys_enter *ctx)
{
	u64 fd = ctx->args[0];
	LOOKUP();

	if (s && fd <= 8)
		s->n[fd]++;
	return 0;
}

/* 4. a 64-bit index with no test: the pointer arithmetic itself is refused */
SEC("tracepoint/syscalls/sys_enter_write")
int ptr_unbounded(struct trace_event_raw_sys_enter *ctx)
{
	u64 fd = ctx->args[0];
	LOOKUP();

	if (s)
		s->n[fd]++;
	return 0;
}

/* 5. the test is made by a function whose parameter is 32 bits wide, on a copy */
static __always_inline int valid_fd(u32 fd)
{
	return fd < 8;
}

SEC("tracepoint/syscalls/sys_enter_write")
int copy32(struct trace_event_raw_sys_enter *ctx)
{
	u64 fd = ctx->args[0];
	LOOKUP();

	if (s && valid_fd(fd))
		s->n[fd]++;
	return 0;
}

/* 6. a variable offset into the stack, untested */
SEC("tracepoint/syscalls/sys_enter_write")
int stack_var(struct trace_event_raw_sys_enter *ctx)
{
	u64 buf[8] = {};
	u32 fd = ctx->args[0];

	buf[ctx->args[1] & 7] = 1;
	return buf[fd];
}

/* 7. a packet read with no test against data_end */
SEC("tc")
int pkt_nocheck(struct __sk_buff *skb)
{
	unsigned char *data = (void *)(long)skb->data;

	return data[0];
}

/* 7, fixed */
SEC("tc")
int pkt_check(struct __sk_buff *skb)
{
	unsigned char *data = (void *)(long)skb->data;
	unsigned char *end = (void *)(long)skb->data_end;

	if (data + 1 > end)
		return 0;
	return data[0];
}

char LICENSE[] SEC("license") = "GPL";
