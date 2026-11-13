// Chapter 15, lab 15.1: the write counter with the map chosen in
// the chapter. An LRU hash bounds the memory and never refuses a
// new thread; the count is added in place, so an event takes no
// bucket lock once its thread has an element.
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct {
	__uint(type, BPF_MAP_TYPE_LRU_HASH);
	__uint(max_entries, 1024);
	__type(key, __u32);
	__type(value, __u64);
} write_counts SEC(".maps");

SEC("tracepoint/syscalls/sys_enter_write")
int count_writes(struct trace_event_raw_sys_enter *ctx)
{
	u32 pid = bpf_get_current_pid_tgid();
	u64 one = 1, *v = bpf_map_lookup_elem(&write_counts, &pid);

	if (v) {
		__sync_fetch_and_add(v, 1);
		return 0;
	}
	if (bpf_map_update_elem(&write_counts, &pid, &one,
				BPF_NOEXIST)) {
		v = bpf_map_lookup_elem(&write_counts, &pid);
		if (v)
			__sync_fetch_and_add(v, 1);
	}
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
