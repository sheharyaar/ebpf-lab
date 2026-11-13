/* the tree counter's lookup at its original hook, the write tracepoint */
#include "common.h"

SEC("tracepoint/syscalls/sys_enter_write")
int tptree(void *ctx)
{
	u32 zero = 0;
	struct wtree *t = bpf_map_lookup_elem(&counts_tree, &zero);
	struct bpf_rb_node *rb;

	if (!t)
		return 0;
	bpf_spin_lock(&t->lock);
	rb = bpf_rbtree_root(&t->root);
	if (rb)
		container_of(rb, struct wnode, rb)->count++;
	bpf_spin_unlock(&t->lock);
	return 0;
}
