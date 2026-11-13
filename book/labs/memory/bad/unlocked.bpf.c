/* a node written after the lock that made the reference valid was dropped */
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
	bpf_spin_lock(&t->lock);
	bpf_rbtree_add(&t->root, &n->rb, less);
	bpf_spin_unlock(&t->lock);
	n->count = 1;				/* the tree owns n, and the lock is gone */
	return 0;
}
