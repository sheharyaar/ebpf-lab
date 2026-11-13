/* Lab "Fix three refused programs", leak: the node goes into the tree, under its lock */
#include "common.h"

SEC("fentry/vfs_write")
int BPF_PROG(leak)
{
	u32 zero = 0;
	struct wtree *t = bpf_map_lookup_elem(&counts_tree, &zero);
	struct wnode *n;

	if (!t)
		return 0;
	n = bpf_obj_new(struct wnode);
	if (!n)
		return 0;
	n->tid = bpf_get_current_pid_tgid();
	bpf_spin_lock(&t->lock);
	bpf_rbtree_add(&t->root, &n->rb, less);	/* the tree owns n now */
	bpf_spin_unlock(&t->lock);
	return 0;
}
