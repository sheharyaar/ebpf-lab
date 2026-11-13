// The second lab of the chapter "How the verifier tracks numbers": the index comes
// from a map value, is tested, and is used after a helper call. The verifier
// refuses it. Load it with labs/walk/stats.c at log level 2 and find the line where
// the index loses its bound. The fix is behind -DFIXED, for numbers-root.sh; write
// your own first.
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct slots {
	__u64 n[8];
};

struct cfg {
	__u32 idx;		/* which counter to add the time to, 0 to 7 */
};

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1024);
	__type(key, __u32);
	__type(value, struct slots);
} fd_counts SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, struct cfg);
} cfg_map SEC(".maps");

SEC("tracepoint/syscalls/sys_enter_write")
int reload(struct trace_event_raw_sys_enter *ctx)
{
	u32 key = 0, pid = bpf_get_current_pid_tgid();
	struct cfg *c = bpf_map_lookup_elem(&cfg_map, &key);
	struct slots *s = bpf_map_lookup_elem(&fd_counts, &pid);
	u64 t;
#ifndef FIXED
	if (!c || !s || c->idx >= 8)
		return 0;
	t = bpf_ktime_get_ns();
	s->n[c->idx] += t;
#else
	u32 i;

	if (!c || !s)
		return 0;
	i = c->idx;		/* read the map value once */
	if (i >= 8)
		return 0;
	t = bpf_ktime_get_ns();
	s->n[i] += t;
#endif
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
