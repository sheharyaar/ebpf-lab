/* Lab "Fix three refused programs", unlocked: write the node while it is still ours */
#include "common.h"

SEC("fentry/vfs_write")
int BPF_PROG(unlocked)
{
	u32 zero = 0;
	struct wtree *t = bpf_map_lookup_elem(&counts_tree, &zero);
	struct wnode *n;

	if (!t)
		return 0;
	n = bpf_obj_new(struct wnode);
	if (!n)
		return 0;
	n->count = 1;				/* owning reference: no lock needed */
	bpf_spin_lock(&t->lock);
	bpf_rbtree_add(&t->root, &n->rb, less);
	bpf_spin_unlock(&t->lock);
	return 0;
}
