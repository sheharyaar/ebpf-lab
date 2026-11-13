/* The tail-call limit: a program that counts its runs and tail-calls itself through
 * slot 0 of its own program array. One getppid() call, then read runs. */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

int again(void *ctx);

struct {
	__uint(type, BPF_MAP_TYPE_PROG_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__array(values, int (void *));
} self SEC(".maps") = { .values = { [0] = (void *)&again } };

__u64 runs;
const volatile __u32 target_pid = 0;

SEC("tracepoint/syscalls/sys_enter_getppid")
int again(void *ctx)
{
	if ((bpf_get_current_pid_tgid() >> 32) != target_pid)
		return 0;
	__sync_fetch_and_add(&runs, 1);
	bpf_tail_call(ctx, &self, 0);
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
