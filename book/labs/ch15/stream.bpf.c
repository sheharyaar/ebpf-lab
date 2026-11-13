// Chapter 15: one 16-byte event per getppid() call, sent through a ring buffer
// or through a perf buffer.
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct {
	__uint(type, BPF_MAP_TYPE_RINGBUF);
	__uint(max_entries, 256 * 1024);
} rb SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
	__uint(key_size, sizeof(u32));
	__uint(value_size, sizeof(u32));
} pb SEC(".maps");

struct ev {
	u32 tid;
	u32 cpu;
	u64 ts;
};

const volatile u64 rb_flags = 0;   /* 0, or BPF_RB_NO_WAKEUP */
u64 rb_dropped;

SEC("tracepoint/syscalls/sys_enter_getppid")
int s_rb(void *ctx)
{
	struct ev *e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);

	if (!e) {
		__sync_fetch_and_add(&rb_dropped, 1);
		return 0;
	}
	e->tid = bpf_get_current_pid_tgid();
	e->cpu = bpf_get_smp_processor_id();
	e->ts = bpf_ktime_get_ns();
	bpf_ringbuf_submit(e, rb_flags);
	return 0;
}

SEC("tracepoint/syscalls/sys_enter_getppid")
int s_pb(void *ctx)
{
	struct ev e = {
		.tid = bpf_get_current_pid_tgid(),
		.cpu = bpf_get_smp_processor_id(),
		.ts = bpf_ktime_get_ns(),
	};

	bpf_perf_event_output(ctx, &pb, BPF_F_CURRENT_CPU, &e, sizeof(e));
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
