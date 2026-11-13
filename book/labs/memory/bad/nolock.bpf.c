/* a node added to the tree without the tree's lock */
#include "common.h"

SEC("fentry/vfs_write")
int BPF_PROG(nolock)
{
	u32 zero = 0;
	struct wtree *t = bpf_map_lookup_elem(&counts_tree, &zero);
	struct wnode *n;

	if (!t)
		return 0;
	n = bpf_obj_new(struct wnode);
	if (!n)
		return 0;
	bpf_rbtree_add(&t->root, &n->rb, less);	/* no bpf_spin_lock(&t->lock) */
	return 0;
}
