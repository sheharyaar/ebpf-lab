/* The write counter on the count-min map type of Part B (BPF_MAP_TYPE_COUNT_MIN, a patched
 * kernel only). push adds the value's count to its key; it cannot return the estimate, so
 * the table of the heaviest costs a peek. Built twice: c_cms.bpf.o, c_cmstopk.bpf.o. */
#include "cms.h"
#include "topk_array.h"

struct {
	__uint(type, BPF_MAP_TYPE_COUNT_MIN);
	__type(value, struct cms_value);
	__uint(max_entries, CMS_W_MAX);		/* the width; the loader may change it */
	__uint(map_extra, CMS_D_MAX);		/* the depth */
	__uint(map_flags, BPF_F_ZERO_SEED);	/* the hashes of cms.h */
} cms SEC(".maps");

SEC("fentry/vfs_write")
int BPF_PROG(count_writes)
{
	struct cms_value v = { .count = 1 };
	u32 tid = counted_tid();

	if (!tid)
		return 0;
	v.key = tid;
	bpf_map_push_elem(&cms, &v, BPF_ANY);
#ifdef WITH_TOPK
	topk_update(tid, bpf_map_peek_elem(&cms, &v));
#endif
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
