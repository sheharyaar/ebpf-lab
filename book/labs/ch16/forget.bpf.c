/* A second program that shares the write counter's map from another object and
 * another process: when a thread exits, it deletes the thread's count.
 * The map definition matches hashmap.bpf.c and asks libbpf to pin it by name, so
 * whichever object loads first creates /sys/fs/bpf/write_counts and the other reuses it.
 * With -DBIG the definition asks for 2,048 entries, and libbpf refuses to reuse the pin. */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

#ifdef BIG
#define ENTRIES 2048
#else
#define ENTRIES 1024
#endif

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, ENTRIES);
	__type(key, __u32);
	__type(value, __u64);
	__uint(pinning, LIBBPF_PIN_BY_NAME);
} write_counts SEC(".maps");

SEC("tracepoint/sched/sched_process_exit")
int forget_thread(void *ctx)
{
	u32 pid = bpf_get_current_pid_tgid();

	bpf_map_delete_elem(&write_counts, &pid);
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
