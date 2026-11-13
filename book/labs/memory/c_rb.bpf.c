/* The write counter on objects it allocates: one node per thread, from bpf_obj_new(), linked
 * into a red-black tree keyed by thread ID, under a bpf_spin_lock. The tree's root and its lock
 * live in the one value of an array map. At fentry/vfs_write: a tracepoint program may not
 * take a bpf_spin_lock, nor call bpf_obj_new() (v7.2). */
#include "mem.h"

struct wnode {
	struct bpf_rb_node rb;		/* 32 bytes the kernel uses to link the node */
	u32 tid;
	u64 count;
};

struct wtree {
	struct bpf_spin_lock lock;
	struct bpf_rb_root root __contains(wnode, rb);
	u64 nodes;			/* nodes in the tree */
	u64 nomem;			/* bpf_obj_new() returned NULL */
};

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, u32);
	__type(value, struct wtree);
} counts_tree SEC(".maps");

static bool less(struct bpf_rb_node *a, const struct bpf_rb_node *b)
{
	struct wnode *x = container_of(a, struct wnode, rb);
	struct wnode *y = container_of(b, struct wnode, rb);

	return x->tid < y->tid;
}

/* add a node for tid, made outside the lock: no call but the tree's own may run inside it */
static __always_inline void insert(struct wtree *t, u32 tid, u64 count)
{
	struct wnode *n = bpf_obj_new(struct wnode);

	if (!n) {
		__sync_fetch_and_add(&t->nomem, 1);
		return;
	}
	n->tid = tid;
	n->count = count;
	bpf_spin_lock(&t->lock);
	bpf_rbtree_add(&t->root, &n->rb, less);		/* n is no longer ours to drop */
	t->nodes++;
	bpf_spin_unlock(&t->lock);
}

SEC("fentry/vfs_write")
int BPF_PROG(count_writes)
{
	u32 zero = 0, tid = bpf_get_current_pid_tgid();
	struct wtree *t = bpf_map_lookup_elem(&counts_tree, &zero);
	struct bpf_rb_node *rb;
	struct wnode *n;

	if (!t)
		return 0;
	bpf_spin_lock(&t->lock);
	rb = bpf_rbtree_root(&t->root);
	while (rb && can_loop) {
		n = container_of(rb, struct wnode, rb);
		if (n->tid == tid) {
			n->count++;			/* through a non-owning reference */
			bpf_spin_unlock(&t->lock);
			return 0;
		}
		rb = tid < n->tid ? bpf_rbtree_left(&t->root, rb)
				  : bpf_rbtree_right(&t->root, rb);
	}
	bpf_spin_unlock(&t->lock);
	insert(t, tid, 1);			/* a thread the tree has not seen */
	return 0;
}

/* user space cannot walk the tree: this program, run with BPF_PROG_RUN, takes the nodes
 * out in order, copies tid and count into dump.out[], and frees them */
#define MAXOUT 8192
struct rec { u32 tid; u32 pad; u64 count; };
struct { struct rec out[MAXOUT]; u32 n; } dump;	/* in .bss, which user space maps */

SEC("syscall")
int drain(void *ctx)
{
	u32 zero = 0, i;
	struct wtree *t = bpf_map_lookup_elem(&counts_tree, &zero);
	struct bpf_rb_node *rb;
	struct wnode *n;

	if (!t)
		return 1;
	dump.n = 0;
	while (can_loop) {
		bpf_spin_lock(&t->lock);
		rb = bpf_rbtree_first(&t->root);
		if (!rb) {
			bpf_spin_unlock(&t->lock);
			break;
		}
		rb = bpf_rbtree_remove(&t->root, rb);	/* an owning reference again */
		t->nodes--;
		bpf_spin_unlock(&t->lock);
		if (!rb)
			continue;
		n = container_of(rb, struct wnode, rb);
		i = dump.n;
		if (i < MAXOUT) {
			dump.out[i].tid = n->tid;
			dump.out[i].count = n->count;
			dump.n = i + 1;
		}
		bpf_obj_drop(n);
	}
	return 0;
}

/* put `count` made-up threads in the tree, IDs from `first`, as if they had written once */
struct fill_args { u32 first; u32 count; };

SEC("syscall")
int fill(struct fill_args *a)
{
	u32 zero = 0, i, first = a->first, cnt = a->count;
	struct wtree *t = bpf_map_lookup_elem(&counts_tree, &zero);

	if (!t)
		return 1;
	for (i = 0; i < cnt && can_loop; i++)
		insert(t, first + i, 1);
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
