/* topk_array.h: the table of the heaviest threads where pointers cannot go, in .bss:
 * TOPK slots found by index. Used by c_array.bpf.c and c_cms.bpf.c. */
#pragma once

struct { u64 tid, est; } top[TOPK];	/* .bss: user space reads it through mmap */
u64 kmin;

static __always_inline void topk_update(u32 tid, u64 est)
{
	u64 m2 = ~0ULL, old;
	int i, m = -1;

	if (est <= kmin)
		return;
	for (i = 0; i < TOPK; i++) {
		if (top[i].tid == tid) {
			top[i].est = est;
			return;
		}
		if (m < 0 || top[i].est < top[m].est) {
			if (m >= 0 && top[m].est < m2)
				m2 = top[m].est;
			m = i;
		} else if (top[i].est < m2) {
			m2 = top[i].est;
		}
	}
	if (m < 0 || est <= top[m].est)
		return;
	old = top[m].tid;
	if (__sync_val_compare_and_swap(&top[m].tid, old, tid) != old)
		return;
	top[m].est = est;
	kmin = est < m2 ? est : m2;
}
