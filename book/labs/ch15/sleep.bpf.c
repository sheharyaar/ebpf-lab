// Chapter 15: a sleepable uprobe program (loaded, never attached) that sends one event,
// through a perf buffer (-DPERF) or through a ring buffer.
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct {
	__uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
	__uint(key_size, sizeof(u32));
	__uint(value_size, sizeof(u32));
} pb SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_RINGBUF);
	__uint(max_entries, 4096);
} rb SEC(".maps");

SEC("uprobe.s")
int ev_sleepable(void *ctx)
{
	u64 t = bpf_ktime_get_ns();

#ifdef PERF
	bpf_perf_event_output(ctx, &pb, BPF_F_CURRENT_CPU, &t, sizeof(t));
#else
	bpf_ringbuf_output(&rb, &t, sizeof(t), 0);
#endif
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
