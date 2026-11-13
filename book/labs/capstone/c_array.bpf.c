/* The same count-min sketch in .bss, which libbpf creates as a one-element array map with
 * BPF_F_MMAPABLE: user space reads it through mmap too, but nothing in it can point at
 * anything, so the table of the heaviest is a fixed array (topk_array.h). Built twice:
 * c_array.bpf.o without the table, c_arraytopk.bpf.o with it. */
#include "cms.h"
#include "topk_array.h"

#define NC (CMS_D_MAX * CMS_W_MAX)
u64 c[NC];				/* d rows of width counters, width <= CMS_W_MAX */

SEC("fentry/vfs_write")
int BPF_PROG(count_writes)
{
	u32 r, j, w = width, tid = counted_tid();
	u64 v, est = ~0ULL;

	if (!tid)
		return 0;
	for (r = 0; r < CMS_D_MAX; r++) {
		if (r >= depth)
			break;
		j = cms_slot(tid, r, w);
		if (j >= NC)		/* the verifier wants the index bounded */
			return 0;
		v = __sync_fetch_and_add(&c[j], 1) + 1;
		if (v < est)
			est = v;
	}
#ifdef WITH_TOPK
	topk_update(tid, est);
#endif
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
