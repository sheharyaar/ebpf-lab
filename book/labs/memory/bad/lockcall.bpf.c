/* bpf_obj_new() called while the tree's lock is held */
#include "common.h"

SEC("fentry/vfs_write")
int BPF_PROG(lockcall)
{
	u32 zero = 0;
	struct wtree *t = bpf_map_lookup_elem(&counts_tree, &zero);
	struct wnode *n;

	if (!t)
		return 0;
	bpf_spin_lock(&t->lock);
	n = bpf_obj_new(struct wnode);		/* inside the lock */
	if (n)
		bpf_rbtree_add(&t->root, &n->rb, less);
	bpf_spin_unlock(&t->lock);
	return 0;
}
