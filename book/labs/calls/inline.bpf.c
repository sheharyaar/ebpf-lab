// Which helper calls the verifier replaces with instructions. One tracepoint program calls eight helpers;
// `bpftool prog dump xlated` after the load shows which calls are left (book/labs/calls-root.sh, step 3).
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct { __uint(type, BPF_MAP_TYPE_ARRAY); __uint(max_entries, 4);
	 __type(key, u32); __type(value, u64); } arr SEC(".maps");
u64 sink;

SEC("tracepoint/syscalls/sys_enter_getppid")
int inl(void *ctx)
{
	u32 key = 1;
	u64 sum = 0, *v;

	sum += bpf_get_smp_processor_id();		/* 8 */
	sum += (u64)bpf_get_current_task();		/* 35 */
	sum += bpf_jiffies64();				/* 118 */
	v = bpf_map_lookup_elem(&arr, &key);		/* 1 */
	if (v)
		sum += *v;
	sum += bpf_ktime_get_ns();			/* 5 */
	sum += bpf_get_prandom_u32();			/* 7 */
	sum += bpf_get_current_pid_tgid();		/* 14 */
	sum += bpf_get_numa_node_id();			/* 42 */
	sink = sum;
	return 0;
}
char LICENSE[] SEC("license") = "GPL";
