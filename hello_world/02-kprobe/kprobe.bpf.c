#include "../../vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

/* TODO: attach a kprobe to the kernel function that handles openat2 */
SEC("")
int BPF_KPROBE(handle_openat2)
{
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
