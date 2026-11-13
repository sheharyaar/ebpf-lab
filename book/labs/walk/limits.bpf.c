// Small programs that run into the walk's limits, for the walk chapter's "when it goes
// wrong" table. Each is loaded alone with labs/walk/stats.c; none is ever attached.
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

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

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, u32);
	__type(value, u64);
} flag SEC(".maps");

static __always_inline struct scratch *scratch(void)
{
	u32 k = 0;

	return bpf_map_lookup_elem(&buf, &k);
}

/* the plain loop of loops.bpf.c, run for ROUNDS rounds over the 4 KB buffer */
#define HASH_ROUNDS(name, ROUNDS)                                       \
SEC("tracepoint/syscalls/sys_enter_write")                              \
int name(struct trace_event_raw_sys_enter *ctx)                                                     \
{                                                                       \
	struct scratch *s = scratch();                                  \
	u64 h = FNV_OFFSET;                                             \
	if (!s)                                                         \
		return 0;                                               \
	_Pragma("clang loop unroll(disable)")                           \
	for (u32 i = 0; i < ROUNDS; i++)                                \
		h = (h ^ s->b[i & (MAXB - 1)]) * FNV_PRIME;             \
	s->h = h;                                                       \
	return 0;                                                       \
}
HASH_ROUNDS(slow, 90000)        /* passes, slowly */
HASH_ROUNDS(budget, 1000000)    /* walks past the instruction budget */

/* a branch whose outcome the walk cannot know, in every round of a loop */
SEC("tracepoint/syscalls/sys_enter_write")
int branches(struct trace_event_raw_sys_enter *ctx)
{
	u64 n = 0;

#pragma clang loop unroll(disable)
	for (int i = 0; i < 10000; i++)
		if (bpf_get_prandom_u32() & 1)
			n += bpf_ktime_get_ns();
	return n & 1;
}

/* wait until user space sets a flag: the state at the loop head never changes */
SEC("tracepoint/syscalls/sys_enter_write")
int spin(struct trace_event_raw_sys_enter *ctx)
{
	u32 k = 0;
	u64 *f = bpf_map_lookup_elem(&flag, &k);

	if (!f)
		return 0;
	while (*(volatile u64 *)f == 0)
		;
	return 0;
}

/* sixteen nested static functions: the walk needs 17 frames */
#define CHAIN(n, next) \
	static __noinline int f##n(int x) { return next(x + 1) ^ n; }
static __noinline int f16(int x) { return x * 3; }
CHAIN(15, f16) CHAIN(14, f15) CHAIN(13, f14) CHAIN(12, f13) CHAIN(11, f12)
CHAIN(10, f11) CHAIN(9, f10) CHAIN(8, f9) CHAIN(7, f8) CHAIN(6, f7) CHAIN(5, f6)
CHAIN(4, f5) CHAIN(3, f4) CHAIN(2, f3) CHAIN(1, f2)

SEC("tracepoint/syscalls/sys_enter_write")
int deep(struct trace_event_raw_sys_enter *ctx)
{
	return f1(bpf_get_prandom_u32()) & 1;
}

/* the same chain as global functions, each verified once on its own */
#define GCHAIN(n, next) \
	__noinline int g##n(int x) { return next(x + 1) ^ n; }
__noinline int g16(int x) { return x * 3; }
GCHAIN(15, g16) GCHAIN(14, g15) GCHAIN(13, g14) GCHAIN(12, g13) GCHAIN(11, g12)
GCHAIN(10, g11) GCHAIN(9, g10) GCHAIN(8, g9) GCHAIN(7, g8) GCHAIN(6, g7) GCHAIN(5, g6)
GCHAIN(4, g5) GCHAIN(3, g4) GCHAIN(2, g3) GCHAIN(1, g2)

SEC("tracepoint/syscalls/sys_enter_write")
int deepglobal(struct trace_event_raw_sys_enter *ctx)
{
	return g1(bpf_get_prandom_u32()) & 1;
}

/* one function with a 32-round loop, called from four places, static or global */
static __noinline u64 mix_static(u64 h)
{
#pragma clang loop unroll(disable)
	for (int i = 0; i < 32; i++)
		h = (h ^ i) * FNV_PRIME;
	return h;
}

__noinline u64 mix_global(u64 h)
{
#pragma clang loop unroll(disable)
	for (int i = 0; i < 32; i++)
		h = (h ^ i) * FNV_PRIME;
	return h;
}

SEC("tracepoint/syscalls/sys_enter_write")
int four_static(struct trace_event_raw_sys_enter *ctx)
{
	u64 h = bpf_get_prandom_u32();

	h = mix_static(h); h = mix_static(h + 1);
	h = mix_static(h + 2); h = mix_static(h + 3);
	return h & 1;
}

SEC("tracepoint/syscalls/sys_enter_write")
int four_global(struct trace_event_raw_sys_enter *ctx)
{
	u64 h = bpf_get_prandom_u32();

	h = mix_global(h); h = mix_global(h + 1);
	h = mix_global(h + 2); h = mix_global(h + 3);
	return h & 1;
}

/* three nested functions with a 200-byte key on the stack each */
struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1);
	__uint(key_size, 200);
	__uint(value_size, 8);
} big SEC(".maps");

#define FRAME200(name, next)                                            \
	static __noinline int name(int x)                               \
	{                                                               \
		char a[200];                                            \
		__builtin_memset(a, x, sizeof(a));                      \
		return (bpf_map_lookup_elem(&big, a) != 0) + next(x + 1); \
	}
static __noinline int s_end(int x) { return x + 1; }
FRAME200(s3, s_end) FRAME200(s2, s3) FRAME200(s1, s2)

SEC("socket")
int stack_socket(struct __sk_buff *skb)
{
	return s1(skb->len) & 1;
}

SEC("tracepoint/syscalls/sys_enter_write")
int stack_tp(struct trace_event_raw_sys_enter *ctx)
{
	return s1(bpf_get_prandom_u32()) & 1;
}

char LICENSE[] SEC("license") = "GPL";
