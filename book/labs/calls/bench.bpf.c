// What one call costs: 64 of the same operation per getppid() event, against variant 0, which does none.
// Variants 0-5 are those of book/labs/ch13-root.sh; 6-9 add helpers the verifier writes inline (6, 8, 9)
// and one it calls (7). Built once per variant with -DVARIANT=n by book/labs/calls-root.sh.
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#define N 64

struct { __uint(type, BPF_MAP_TYPE_ARRAY); __uint(max_entries, 8);
	 __type(key, u32); __type(value, u64); } b_arr SEC(".maps");
struct { __uint(type, BPF_MAP_TYPE_ARRAY); __uint(max_entries, 8); __uint(map_flags, BPF_F_INNER_MAP);
	 __type(key, u32); __type(value, u64); } b_arrcall SEC(".maps");
struct { __uint(type, BPF_MAP_TYPE_HASH); __uint(max_entries, 8);
	 __type(key, u32); __type(value, u64); } b_hash SEC(".maps");
u64 sink;

SEC("tracepoint/syscalls/sys_enter_getppid")
int bench(void *ctx)
{
	u32 pid = bpf_get_current_pid_tgid() >> 32;
	u32 key = pid & 7;
	u64 sum = 0;
#pragma unroll
	for (int i = 0; i < N; i++) {
#if VARIANT == 1	/* array lookup, inlined by array_map_gen_lookup() */
		u64 *v = bpf_map_lookup_elem(&b_arr, &key); if (v) sum += *v;
#elif VARIANT == 2	/* the same array lookup through a call (BPF_F_INNER_MAP) */
		u64 *v = bpf_map_lookup_elem(&b_arrcall, &key); if (v) sum += *v;
#elif VARIANT == 3	/* hash lookup */
		u64 *v = bpf_map_lookup_elem(&b_hash, &key); if (v) sum += *v;
#elif VARIANT == 4	/* a helper call */
		sum += bpf_get_current_pid_tgid();
#elif VARIANT == 5	/* a kfunc acquire and release */
		struct task_struct *t = bpf_task_from_pid(pid);
		if (t) { sum += t->pid; bpf_task_release(t); }
#elif VARIANT == 6	/* inlined: three instructions */
		sum += bpf_get_smp_processor_id();
#elif VARIANT == 7	/* a helper call that reads the clock */
		sum += bpf_ktime_get_ns();
#elif VARIANT == 8	/* inlined: a 64-bit load of jiffies */
		sum += bpf_jiffies64();
#elif VARIANT == 9	/* inlined: three instructions */
		sum += bpf_get_current_task();
#endif
	}
	sink = sum;
	return 0;
}
char LICENSE[] SEC("license") = "GPL";
