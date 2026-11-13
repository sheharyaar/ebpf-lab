/* the node and the tree of c_rb.bpf.c, for the programs in this folder that the verifier refuses */
#include "mem.h"

struct wnode {
	struct bpf_rb_node rb;
	u32 tid;
	u64 count;
};

struct wnode *keep_btf;		/* puts struct wnode in the object's BTF in every file */

struct wtree {
	struct bpf_spin_lock lock;
	struct bpf_rb_root root __contains(wnode, rb);
};

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, u32);
	__type(value, struct wtree);
} counts_tree SEC(".maps");

static bool less(struct bpf_rb_node *a, const struct bpf_rb_node *b)
{
	return container_of(a, struct wnode, rb)->tid < container_of(b, struct wnode, rb)->tid;
}

char LICENSE[] SEC("license") = "GPL";
