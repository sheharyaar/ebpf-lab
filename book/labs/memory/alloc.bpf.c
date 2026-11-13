/* alloc: what allocating costs, timed inside the program with bpf_ktime_get_ns(). Each program
 * is a syscall program run once with BPF_PROG_RUN (by atest.c), and does its work n times.
 *   obj_pair   bpf_obj_new() and bpf_obj_drop() of a 48-byte node, n times
 *   obj_keep   n nodes allocated and kept, each stashed as a kptr in a slot of `stash`
 *   obj_free   the n nodes taken back out of their slots with bpf_kptr_xchg() and dropped
 *   slots      the loop of obj_keep with no allocation (lookup and kptr exchange only)
 *   lock_pair  bpf_spin_lock() and bpf_spin_unlock() on a map value, n times, uncontended
 *   page_pair  bpf_arena_alloc_pages() and bpf_arena_free_pages() of one page, n times
 *   page_keep  n arena pages allocated one at a time and kept; page_free gives them back
 *   frag       n 32-byte objects from the selftests' page-fragment allocator, in the arena
 *   past_end   a load from 1 GiB into the arena, past its size
 *   unalloc    a store to page 40000 of the arena, which nobody allocated */
#include "mem.h"

struct wnode {
	struct bpf_rb_node rb;
	u32 tid;
	u64 count;
};

struct kslot { struct wnode __kptr *p; };

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 100000);
	__type(key, u32);
	__type(value, struct kslot);
} stash SEC(".maps");

struct lkval { struct bpf_spin_lock l; u64 x; };

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, u32);
	__type(value, struct lkval);
} lk SEC(".maps");

struct {
	__uint(type, BPF_MAP_TYPE_ARENA);
	__uint(map_flags, BPF_F_MMAPABLE);
	__uint(max_entries, 65536);		/* pages: 256 MiB of address space */
} arena SEC(".maps");

#include "bpf_arena_alloc.h"

struct { u64 ns, fails, n, val; void __arena *first; } r;	/* results, in .bss */
struct args { u32 n; };

SEC("syscall")
int obj_pair(struct args *a)
{
	u32 n = a->n, i;
	u64 t0 = bpf_ktime_get_ns(), fails = 0;

	for (i = 0; i < n && can_loop; i++) {
		struct wnode *p = bpf_obj_new(struct wnode);

		if (!p) {
			fails++;
			continue;
		}
		bpf_obj_drop(p);
	}
	r.ns = bpf_ktime_get_ns() - t0;
	r.fails = fails;
	r.n = n;
	return 0;
}

static __always_inline int stash_loop(u32 n, bool alloc)
{
	u64 t0 = bpf_ktime_get_ns(), fails = 0;
	u32 i;

	for (i = 0; i < n && can_loop; i++) {
		struct kslot *v = bpf_map_lookup_elem(&stash, &i);
		struct wnode *p = NULL, *old;

		if (!v)
			break;
		if (alloc) {
			p = bpf_obj_new(struct wnode);
			if (!p) {
				fails++;
				continue;
			}
			p->tid = i;
		}
		old = bpf_kptr_xchg(&v->p, p);	/* the slot owns p; we own what was there */
		if (old)
			bpf_obj_drop(old);
	}
	r.ns = bpf_ktime_get_ns() - t0;
	r.fails = fails;
	r.n = n;
	return 0;
}

SEC("syscall")
int obj_keep(struct args *a) { return stash_loop(a->n, true); }

SEC("syscall")
int obj_free(struct args *a) { return stash_loop(a->n, false); }

SEC("syscall")
int slots(struct args *a)
{
	u64 t0 = bpf_ktime_get_ns();
	u32 i, n = a->n;

	for (i = 0; i < n && can_loop; i++) {
		struct kslot *v = bpf_map_lookup_elem(&stash, &i);
		struct wnode *old;

		if (!v)
			break;
		old = bpf_kptr_xchg(&v->p, NULL);
		if (old)
			bpf_obj_drop(old);
	}
	r.ns = bpf_ktime_get_ns() - t0;
	r.n = n;
	return 0;
}

SEC("syscall")
int lock_pair(struct args *a)
{
	u32 zero = 0, i, n = a->n;
	struct lkval *v = bpf_map_lookup_elem(&lk, &zero);
	u64 t0 = bpf_ktime_get_ns();

	if (!v)
		return 1;
	for (i = 0; i < n && can_loop; i++) {
		bpf_spin_lock(&v->l);
		v->x++;
		bpf_spin_unlock(&v->l);
	}
	r.ns = bpf_ktime_get_ns() - t0;
	r.n = n;
	return 0;
}

SEC("syscall")
int page_pair(struct args *a)
{
	u32 i, n = a->n;
	u64 t0 = bpf_ktime_get_ns(), fails = 0;

	for (i = 0; i < n && can_loop; i++) {
		void __arena *p = bpf_arena_alloc_pages(&arena, NULL, 1, NUMA_NO_NODE, 0);

		if (!p) {
			fails++;
			continue;
		}
		bpf_arena_free_pages(&arena, p, 1);
	}
	r.ns = bpf_ktime_get_ns() - t0;
	r.fails = fails;
	r.n = n;
	return 0;
}

SEC("syscall")
int page_keep(struct args *a)
{
	u32 i, n = a->n;
	u64 t0 = bpf_ktime_get_ns(), fails = 0;

	for (i = 0; i < n && can_loop; i++) {
		void __arena *p = bpf_arena_alloc_pages(&arena, NULL, 1, NUMA_NO_NODE, 0);

		if (!p) {
			fails++;
			continue;
		}
		if (!i)
			r.first = p;
		*(volatile int __arena *)p = 1;		/* touch it */
	}
	r.ns = bpf_ktime_get_ns() - t0;
	r.fails = fails;
	r.n = n;
	return 0;
}

SEC("syscall")
int page_free(struct args *a)
{
	char __arena *p = r.first;
	u32 i, n = a->n;
	u64 t0 = bpf_ktime_get_ns();

	for (i = 0; i < n && can_loop; i++)
		bpf_arena_free_pages(&arena, p + (u64)i * __PAGE_SIZE, 1);
	r.ns = bpf_ktime_get_ns() - t0;
	r.n = n;
	return 0;
}

SEC("syscall")
int frag(struct args *a)
{
	u32 i, n = a->n;
	u64 t0 = bpf_ktime_get_ns(), fails = 0;

	for (i = 0; i < n && can_loop; i++) {
		u64 __arena *p = bpf_alloc(32);

		if (!p) {
			fails++;
			continue;
		}
		*p = i;
	}
	r.ns = bpf_ktime_get_ns() - t0;
	r.fails = fails;
	r.n = n;
	return 0;
}

SEC("syscall")
int past_end(struct args *a)
{
	char __arena *base = arena_base(&arena);	/* names the arena: see bad/noarena */

	/* 1 GiB in: past the arena's 256 MiB, still inside the 4 GiB the kernel set aside */
	r.val = *(volatile int __arena *)(base + (1ull << 30));	/* reads 0, and is reported */
	return 0;
}

SEC("syscall")
int unalloc(struct args *a)
{
	char __arena *base = arena_base(&arena);

	/* page 40000: nobody allocated it (libbpf keeps the arena globals in the last pages) */
	*(volatile int __arena *)(base + 40000ull * __PAGE_SIZE) = 7;	/* skipped, and reported */
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
