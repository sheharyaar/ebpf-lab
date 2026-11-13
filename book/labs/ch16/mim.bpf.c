/* What a lookup through a map-in-map costs, by chapter 13's method: 64 of the same
 * operation per getppid() call, unrolled, timed with run_time_ns, less the baseline.
 * VARIANT 0 the key only; 1 a hash; 2 array of maps, then the inner hash;
 * 3 hash of maps, then the inner hash; 4 an array; 5 array of maps, then the inner array. */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#define N 64

struct inner_hash {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 8);
	__type(key, u32);
	__type(value, u64);
} in_h SEC(".maps");

struct inner_arr {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 8);
	__type(key, u32);
	__type(value, u64);
} in_a SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY_OF_MAPS);
	__uint(max_entries, 4);
	__type(key, u32);
	__array(values, struct inner_hash);
} out_ah SEC(".maps") = { .values = { [0] = &in_h } };

struct {
	__uint(type, BPF_MAP_TYPE_HASH_OF_MAPS);
	__uint(max_entries, 4);
	__type(key, u32);
	__array(values, struct inner_hash);
} out_hh SEC(".maps") = { .values = { [0] = &in_h } };

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY_OF_MAPS);
	__uint(max_entries, 4);
	__type(key, u32);
	__array(values, struct inner_arr);
} out_aa SEC(".maps") = { .values = { [0] = &in_a } };

u64 sink;

SEC("tracepoint/syscalls/sys_enter_getppid")
int bench(void *ctx)
{
	u32 pid = bpf_get_current_pid_tgid() >> 32;
	u32 key = pid & 7, zero = pid & 0;
	u64 sum = 0;
	void *in;
	u64 *v;

#pragma unroll
	for (int i = 0; i < N; i++) {
#if VARIANT == 1
		v = bpf_map_lookup_elem(&in_h, &key); if (v) sum += *v;
#elif VARIANT == 2
		in = bpf_map_lookup_elem(&out_ah, &zero);
		if (in) { v = bpf_map_lookup_elem(in, &key); if (v) sum += *v; }
#elif VARIANT == 3
		in = bpf_map_lookup_elem(&out_hh, &zero);
		if (in) { v = bpf_map_lookup_elem(in, &key); if (v) sum += *v; }
#elif VARIANT == 4
		v = bpf_map_lookup_elem(&in_a, &key); if (v) sum += *v;
#elif VARIANT == 5
		in = bpf_map_lookup_elem(&out_aa, &zero);
		if (in) { v = bpf_map_lookup_elem(in, &key); if (v) sum += *v; }
#endif
	}
	sink = sum;
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
