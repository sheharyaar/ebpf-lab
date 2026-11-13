#include "../../vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

/* TODO: attach a kprobe to the kernel function that handles openat2 */
SEC("kprobe/do_sys_openat2")
int BPF_KPROBE(handle_openat2)
{
	bpf_printk("[PID %u] openat2", (u32)bpf_get_current_pid_tgid());
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
