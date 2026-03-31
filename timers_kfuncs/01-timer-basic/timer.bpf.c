#include "../../vmlinux.h"
#include <bpf/bpf_helpers.h>

struct timer_val {
	struct bpf_timer timer;
	__u64 fire_count;
};

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, struct timer_val);
} timer_map SEC(".maps");

static int __attribute__((used))
timer_callback(void *map, __u32 *key, struct timer_val *val)
{
	return 0;
}

/* TODO: attach to the nanosleep syscall entry tracepoint */
SEC("")
int arm_timer(struct trace_event_raw_sys_enter *ctx)
{
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
