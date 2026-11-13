// What precision costs: two programs that differ only in what they do with k.
// K tests each add a different constant to k on one side, so every path through
// them leaves k a known number, and many paths leave different numbers.
// "matters" uses k as an index, so the verifier marks it precise and must tell the
// paths apart; "never" only stores k, so it stays imprecise and the paths merge.
// Build with -DK=8, 12, 16, ... and load each alone with labs/walk/stats.c.
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

#ifndef K
#define K 16
#endif

struct slots {
	__u64 n[8];
};

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, struct slots);
} tbl SEC(".maps");

/* one test: a real branch (the empty asm cannot be hoisted out of it) */
#define T(b)						\
	if (K > b && (x & (1ULL << b))) {		\
		k += b + 1;				\
		barrier();				\
	}

#define TESTS							\
	T(0) T(1) T(2) T(3) T(4) T(5) T(6) T(7)		\
	T(8) T(9) T(10) T(11) T(12) T(13) T(14) T(15)		\
	T(16) T(17) T(18) T(19) T(20) T(21) T(22) T(23)

SEC("tracepoint/syscalls/sys_enter_write")
int matters(struct trace_event_raw_sys_enter *ctx)
{
	u64 x = ctx->args[2], k = 0;
	u32 key = 0;
	struct slots *s = bpf_map_lookup_elem(&tbl, &key);

	if (!s)
		return 0;
	TESTS
	s->n[k & 7] += 1;		/* k decides the address */
	return 0;
}

SEC("tracepoint/syscalls/sys_enter_write")
int never(struct trace_event_raw_sys_enter *ctx)
{
	u64 x = ctx->args[2], k = 0;
	u32 key = 0;
	struct slots *s = bpf_map_lookup_elem(&tbl, &key);

	if (!s)
		return 0;
	TESTS
	s->n[0] += k;			/* k is only data */
	return 0;
}

/* the fix: the same sum computed without branches, so that k is one unknown
 * number on one path instead of a different constant on each of many */
#define F(b)	if (K > b) k += ((x >> b) & 1) * (b + 1);
#define FLAT							\
	F(0) F(1) F(2) F(3) F(4) F(5) F(6) F(7)		\
	F(8) F(9) F(10) F(11) F(12) F(13) F(14) F(15)		\
	F(16) F(17) F(18) F(19) F(20) F(21) F(22) F(23)

SEC("tracepoint/syscalls/sys_enter_write")
int matters_flat(struct trace_event_raw_sys_enter *ctx)
{
	u64 x = ctx->args[2], k = 0;
	u32 key = 0;
	struct slots *s = bpf_map_lookup_elem(&tbl, &key);

	if (!s)
		return 0;
	FLAT
	s->n[k & 7] += 1;
	return 0;
}

/* the other fix: the index comes from the input, which is the same unknown number
 * on every path, and k goes back to being data */
SEC("tracepoint/syscalls/sys_enter_write")
int from_input(struct trace_event_raw_sys_enter *ctx)
{
	u64 x = ctx->args[2], k = 0;
	u32 key = 0;
	struct slots *s = bpf_map_lookup_elem(&tbl, &key);

	if (!s)
		return 0;
	TESTS
	s->n[x & 7] += k;
	return 0;
}

/* the same two as socket filters, which a loader without CAP_BPF may load: without
 * CAP_BPF every scalar is precise from the start (__mark_reg_unknown) */
SEC("socket")
int matters_sk(struct __sk_buff *skb)
{
	u64 x = skb->len, k = 0;
	u32 key = 0;
	struct slots *s = bpf_map_lookup_elem(&tbl, &key);

	if (!s)
		return 0;
	TESTS
	s->n[k & 7] += 1;
	return 0;
}

SEC("socket")
int never_sk(struct __sk_buff *skb)
{
	u64 x = skb->len, k = 0;
	u32 key = 0;
	struct slots *s = bpf_map_lookup_elem(&tbl, &key);

	if (!s)
		return 0;
	TESTS
	s->n[0] += k;
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
