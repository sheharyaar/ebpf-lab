// One loop written five ways, for the walk chapter: hash the first N bytes that each
// write() writes (64-bit FNV-1a) into a per-CPU scratch value. Only loaded, never
// attached. Build with -DN=256 or -DN=4096 (at most MAXB).
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

#ifndef N
#define N 256
#endif
#define MAXB 4096
#define FNV_OFFSET 0xcbf29ce484222325ULL
#define FNV_PRIME 0x100000001b3ULL

struct scratch {
	u64 h;
	unsigned char b[MAXB];
};

struct {
	__uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
	__uint(max_entries, 1);
	__type(key, u32);
	__type(value, struct scratch);
} buf SEC(".maps");

static __always_inline u64 step(u64 h, unsigned char c)
{
	return (h ^ c) * FNV_PRIME;
}

static __always_inline struct scratch *fill(struct trace_event_raw_sys_enter *ctx)
{
	u32 k = 0;
	struct scratch *s = bpf_map_lookup_elem(&buf, &k);

	if (s)
		bpf_probe_read_user(s->b, N, (void *)ctx->args[1]);
	return s;
}

/* 1. a plain bounded loop: the walk goes round once per byte */
SEC("tracepoint/syscalls/sys_enter_write")
int plain(struct trace_event_raw_sys_enter *ctx)
{
	struct scratch *s = fill(ctx);
	u64 h = FNV_OFFSET;

	if (!s)
		return 0;
#pragma clang loop unroll(disable)
	for (int i = 0; i < N; i++)
		h = step(h, s->b[i]);
	s->h = h;
	return 0;
}

/* 2. bpf_loop(): the body is a callback, walked until its state stops changing */
struct lctx {
	struct scratch *s;
	u64 h;
};

static long one_byte(u64 i, void *data)
{
	struct lctx *c = data;

	if (i >= MAXB)
		return 1;
	c->h = step(c->h, c->s->b[i]);
	return 0;
}

SEC("tracepoint/syscalls/sys_enter_write")
int helper(struct trace_event_raw_sys_enter *ctx)
{
	struct lctx c = { .s = fill(ctx), .h = FNV_OFFSET };

	if (!c.s)
		return 0;
	bpf_loop(N, one_byte, &c, 0);
	c.s->h = c.h;
	return 0;
}

/* 3. an open-coded iterator: bpf_for() calls bpf_iter_num_new/next/destroy */
SEC("tracepoint/syscalls/sys_enter_write")
int iter(struct trace_event_raw_sys_enter *ctx)
{
	struct scratch *s = fill(ctx);
	u64 h = FNV_OFFSET;
	int i;

	if (!s)
		return 0;
	bpf_for(i, 0, N)
		h = step(h, s->b[i]);
	s->h = h;
	return 0;
}

/* 4. may_goto: the plain loop with a may_goto instruction in its test */
#define can_loop                                        \
	({ __label__ l_break, l_continue;               \
	bool ret = true;                                \
	asm volatile goto("may_goto %l[l_break]"        \
		      :::: l_break);                    \
	goto l_continue;                                \
	l_break: ret = false;                           \
	l_continue:;                                    \
	ret;                                            \
	})

SEC("tracepoint/syscalls/sys_enter_write")
int maygoto(struct trace_event_raw_sys_enter *ctx)
{
	struct scratch *s = fill(ctx);
	u64 h = FNV_OFFSET;

	if (!s)
		return 0;
#pragma clang loop unroll(disable)
	for (int i = 0; i < N && can_loop; i++)
		h = step(h, s->b[i]);
	s->h = h;
	return 0;
}

/* 5. may_goto with the counter kept in map memory, which the walk does not track: the
 * counter comes back as an unknown number in [0, N) every round, as bpf_for's does */
SEC("tracepoint/syscalls/sys_enter_write")
int maygoto_mem(struct trace_event_raw_sys_enter *ctx)
{
	struct scratch *s = fill(ctx);
	volatile u32 *ip;
	u64 h = FNV_OFFSET;

	if (!s)
		return 0;
	ip = (volatile u32 *)&s->h;     /* low half of h, used as the counter's home */
	*ip = 0;
	while (can_loop) {
		u32 i = *ip;

		if (i >= N)
			break;
		h = step(h, s->b[i]);
		*ip = i + 1;
	}
	s->h = h;
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
