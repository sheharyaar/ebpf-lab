/* Lab "Fix three refused programs", kptrstore: exchange, and drop what comes back */
#include "mem.h"

struct wcount { u32 tid; u64 count; };
struct kslot { struct wcount __kptr *p; };

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, u32);
	__type(value, struct kslot);
} stash SEC(".maps");

SEC("fentry/vfs_write")
int BPF_PROG(kptrstore)
{
	u32 zero = 0;
	struct kslot *v = bpf_map_lookup_elem(&stash, &zero);
	struct wcount *n, *old;

	if (!v)
		return 0;
	n = bpf_obj_new(struct wcount);
	if (!n)
		return 0;
	old = bpf_kptr_xchg(&v->p, n);		/* the slot owns n; we own old */
	if (old)
		bpf_obj_drop(old);		/* allowed here: no list or tree fields */
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
