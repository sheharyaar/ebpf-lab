// Chapter 15: an update that runs while the same bucket's lock is held on this CPU.
// Replacing an element whose value holds a bpf_timer calls bpf_obj_cancel_fields()
// under the bucket lock (htab_map_update_elem() -> check_and_cancel_fields()), and an
// fentry program there updates the same map, then a second map.
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct val {
	struct bpf_timer t;
	u64 payload;
};

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1);
	__type(key, u32);
	__type(value, struct val);
} htab SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1);
	__type(key, u32);
	__type(value, u64);
} other SEC(".maps");

int same_err = 1, other_err = 1, runs;

SEC("fentry/bpf_obj_cancel_fields")
int nested(void *ctx)
{
	u32 key = 0;
	u64 one = 1;
	struct val v = { .payload = 1 };

	runs++;
	same_err = bpf_map_update_elem(&htab, &key, &v, BPF_ANY);
	other_err = bpf_map_update_elem(&other, &key, &one, BPF_ANY);
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
