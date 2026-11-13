// Chapter 15: what one count costs, ten ways. Every program runs at the getppid
// tracepoint and counts one event into its own map. `mode` picks the key:
// 0 = the thread ID (each writer its own key; for arrays tid & 1023, adjacent slots),
// 1 = key 0 for every writer (one shared value),
// 2 = for arrays, (tid * 8) & 1023, so that each writer's slot sits in its own 64-byte line.
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

#define MAP(name, t, flags)                                              \
	struct {                                                         \
		__uint(type, t);                                         \
		__uint(max_entries, 1024);                               \
		__uint(map_flags, flags);                                \
		__type(key, u32);                                        \
		__type(value, u64);                                      \
	} name SEC(".maps")

MAP(m_hash_upd, BPF_MAP_TYPE_HASH, 0);
MAP(m_hash_atomic, BPF_MAP_TYPE_HASH, 0);
MAP(m_hash_plain, BPF_MAP_TYPE_HASH, 0);
MAP(m_pchash, BPF_MAP_TYPE_PERCPU_HASH, 0);
MAP(m_lru, BPF_MAP_TYPE_LRU_HASH, 0);
MAP(m_np_upd, BPF_MAP_TYPE_HASH, BPF_F_NO_PREALLOC);
MAP(m_arr_atomic, BPF_MAP_TYPE_ARRAY, 0);
MAP(m_arr_plain, BPF_MAP_TYPE_ARRAY, 0);
MAP(m_pcarr, BPF_MAP_TYPE_PERCPU_ARRAY, 0);

const volatile int mode = 0;

static __always_inline u32 hkey(void)
{
	u32 tid = bpf_get_current_pid_tgid();

	return mode == 1 ? 0 : tid;
}

static __always_inline u32 akey(void)
{
	u32 tid = bpf_get_current_pid_tgid();

	if (mode == 1)
		return 0;
	return mode == 2 ? (tid * 8) & 1023 : tid & 1023;
}

/* the baseline: the key and nothing else */
SEC("tracepoint/syscalls/sys_enter_getppid")
int t_empty(void *ctx)
{
	volatile u32 k = hkey();

	return 0;
}

/* the write counter's way, without bpf_printk: lookup, add on the stack, update */
SEC("tracepoint/syscalls/sys_enter_getppid")
int t_hash_upd(void *ctx)
{
	u32 k = hkey();
	u64 one = 1, *v = bpf_map_lookup_elem(&m_hash_upd, &k);

	if (v)
		__atomic_fetch_add(&one, *v, __ATOMIC_SEQ_CST);
	bpf_map_update_elem(&m_hash_upd, &k, &one, BPF_ANY);
	return 0;
}

/* the same counter on a hash made without preallocation */
SEC("tracepoint/syscalls/sys_enter_getppid")
int t_np_upd(void *ctx)
{
	u32 k = hkey();
	u64 one = 1, *v = bpf_map_lookup_elem(&m_np_upd, &k);

	if (v)
		__atomic_fetch_add(&one, *v, __ATOMIC_SEQ_CST);
	bpf_map_update_elem(&m_np_upd, &k, &one, BPF_ANY);
	return 0;
}

#define INPLACE(fn, map, op)                                             \
	SEC("tracepoint/syscalls/sys_enter_getppid")                    \
	int fn(void *ctx)                                                \
	{                                                                \
		u32 k = hkey();                                          \
		u64 one = 1, *v = bpf_map_lookup_elem(&map, &k);         \
                                                                         \
		if (!v && bpf_map_update_elem(&map, &k, &one, BPF_NOEXIST)) \
			v = bpf_map_lookup_elem(&map, &k);               \
		if (v)                                                   \
			op;                                              \
		return 0;                                                \
	}

/* add in place, through the pointer the lookup returned */
INPLACE(t_hash_atomic, m_hash_atomic, __sync_fetch_and_add(v, 1))
INPLACE(t_hash_plain, m_hash_plain, *v += 1)
INPLACE(t_pchash, m_pchash, *v += 1)
INPLACE(t_lru, m_lru, __sync_fetch_and_add(v, 1))

#define ARR(fn, map, op)                                                 \
	SEC("tracepoint/syscalls/sys_enter_getppid")                    \
	int fn(void *ctx)                                                \
	{                                                                \
		u32 k = akey();                                          \
		u64 *v = bpf_map_lookup_elem(&map, &k);                  \
                                                                         \
		if (v)                                                   \
			op;                                              \
		return 0;                                                \
	}

ARR(t_arr_atomic, m_arr_atomic, __sync_fetch_and_add(v, 1))
ARR(t_arr_plain, m_arr_plain, *v += 1)
ARR(t_pcarr, m_pcarr, *v += 1)

char LICENSE[] SEC("license") = "GPL";
