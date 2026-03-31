#include "../../vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 256);
	__type(key, __u32);
	__type(value, __u64);
} shared_map SEC(".maps");

/* TODO: attach a kprobe to the kernel function that handles openat2 */
SEC("")
int BPF_KPROBE(writer_openat2)
{
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
