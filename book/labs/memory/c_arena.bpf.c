/* The write counter in an arena: the hash table of the v7.2 selftests (bpf_arena_htab.h, with
 * its page-fragment allocator bpf_arena_alloc.h), keyed by thread ID. User space reads the
 * counts through its own mapping of the arena. At fentry/vfs_write, like the other two. */
#include "mem.h"

struct {
	__uint(type, BPF_MAP_TYPE_ARENA);
	__uint(map_flags, BPF_F_MMAPABLE);
	__uint(max_entries, 1024);		/* pages: at most 4 MiB */
} arena SEC(".maps");

#include "bpf_arena_htab.h"

struct {
	void __arena *htab;		/* the table, as an address user space can follow */
	u64 nomem;			/* an insert found no memory */
} g;					/* in .bss, which user space maps */

SEC("syscall")
int init(void *ctx)
{
	struct htab __arena *h = bpf_alloc(sizeof(*h));

	if (!h)
		return 1;
	htab_init(h);			/* two pages of buckets: 1,024 list heads */
	cast_user(h);
	g.htab = h;
	return 0;
}

SEC("fentry/vfs_write")
int BPF_PROG(count_writes)
{
	struct htab __arena *h = g.htab;
	u32 tid = bpf_get_current_pid_tgid();
	hashtab_elem_t *e;

	if (!h)
		return 0;
	cast_kern(h);
	e = lookup_elem_raw(select_bucket(h, tid), htab_hash(tid), tid);
	if (e)
		__sync_fetch_and_add(&e->value, 1);
	else if (htab_update_elem(h, tid, 1))	/* no lock: two CPUs inserting into */
		__sync_fetch_and_add(&g.nomem, 1);	/* one bucket would race */
	return 0;
}

struct fill_args { u32 first; u32 count; };

SEC("syscall")
int fill(struct fill_args *a)
{
	struct htab __arena *h = g.htab;
	u32 i, first = a->first, cnt = a->count;

	if (!h)
		return 1;
	cast_kern(h);
	for (i = 0; i < cnt && can_loop; i++)
		if (htab_update_elem(h, first + i, 1))
			__sync_fetch_and_add(&g.nomem, 1);
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
