/* The write counter as a count-min sketch in an arena: d rows of w counters, and beside
 * them a table of the TOPK heaviest threads, a list of nodes linked by arena pointers.
 * User space reads both through its own mapping of the arena, with no bpf() call.
 * Built twice (capstone-root.sh): c_sketch.bpf.o without the table, c_topk.bpf.o with it. */
#include "cms.h"

struct {
	__uint(type, BPF_MAP_TYPE_ARENA);
	__uint(map_flags, BPF_F_MMAPABLE);
	__uint(max_entries, 1024);		/* pages: at most 4 MiB */
} arena SEC(".maps");

#include "bpf_arena_alloc.h"

struct topnode {				/* one thread in the table of the heaviest */
	struct topnode __arena *next;
	u64 tid;
	u64 est;
};

struct sketch {
	u32 w, d;
	u64 kmin;			/* below this estimate a thread cannot enter the table */
	struct topnode __arena *top;	/* the table, a list of TOPK nodes */
	u64 c[];			/* d rows of w counters */
};

struct {
	struct sketch __arena *sk;	/* as an address user space can follow */
	u32 pages;
} g;					/* in .bss, which user space maps */

SEC("syscall")
int init(void *ctx)
{
	u64 bytes = sizeof(struct sketch) + (u64)depth * width * sizeof(u64);
	u32 i, pages = (bytes + 4095) / 4096;
	struct sketch __arena *sk;

	sk = bpf_arena_alloc_pages(&arena, NULL, pages, NUMA_NO_NODE, 0);
	if (!sk)
		return 1;
	sk->w = width;
	sk->d = depth;
#ifdef WITH_TOPK
	for (i = 0; i < TOPK && can_loop; i++) {
		struct topnode __arena *n = bpf_alloc(sizeof(*n));

		if (!n)
			return 2;
		n->next = sk->top;	/* tid 0, estimate 0: free */
		sk->top = n;
	}
#endif
	g.pages = pages;
	cast_user(sk);
	g.sk = sk;
	return 0;
}

#ifdef WITH_TOPK
/* Walk the table: refresh this thread's node, or take the node with the smallest
 * estimate if this thread's is larger. No lock: a node is claimed by compare-and-swap
 * on its tid, and an estimate may be a write or two behind. */
static __always_inline void topk_update(struct sketch __arena *sk, u32 tid, u64 est)
{
	struct topnode __arena *n, *m = NULL;
	u64 m2 = ~0ULL, old;

	if (est <= sk->kmin)
		return;
	for (n = sk->top; n && can_loop; n = n->next) {
		if (n->tid == tid) {
			n->est = est;
			return;
		}
		if (!m || n->est < m->est) {
			if (m && m->est < m2)
				m2 = m->est;
			m = n;
		} else if (n->est < m2) {
			m2 = n->est;
		}
	}
	if (!m || est <= m->est)
		return;
	old = m->tid;
	if (__sync_val_compare_and_swap(&m->tid, old, tid) != old)
		return;			/* another CPU took the node first */
	m->est = est;
	sk->kmin = est < m2 ? est : m2;
}
#endif

SEC("fentry/vfs_write")
int BPF_PROG(count_writes)
{
	struct sketch __arena *sk = g.sk;
	u32 r, w = width, tid = counted_tid();
	u64 v, est = ~0ULL;

	if (!tid || !sk)
		return 0;
	/* name the arena, or the verifier refuses the cast below:
	 * "addr_space_cast insn can only be used in a program that has an associated arena" */
	asm volatile("" : : "r"(&arena));
	cast_kern(sk);
	for (r = 0; r < CMS_D_MAX; r++) {
		if (r >= depth)
			break;
		v = __sync_fetch_and_add(&sk->c[cms_slot(tid, r, w)], 1) + 1;
		if (v < est)
			est = v;
	}
#ifdef WITH_TOPK
	topk_update(sk, tid, est);
#endif
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
