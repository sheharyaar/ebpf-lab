/* cms.h: what every version of the capstone's counter shares on the BPF side.
 * The hash is the kernel's jhash2() over the 8-byte key (the thread ID widened to
 * a u64), seeded with the row number, and a row's slot is picked with the kernel's
 * reciprocal_scale(): the same functions the count-min map type of Part B uses
 * with BPF_F_ZERO_SEED, so all the sketches put a thread in the same counters.
 * mem.h (from labs/memory) supplies vmlinux.h, the libbpf headers and can_loop. */
#pragma once
#include "mem.h"

#define CMS_W_MAX	2719		/* e / 0.001: epsilon = 0.001 */
#define CMS_D_MAX	5		/* ceil(ln(1 / 0.01)): delta = e^-5 = 0.0067 */
#define TOPK		16		/* threads kept in the table of the heaviest */

const volatile u32 tgid = 0;		/* count only this process; 0: everyone */
const volatile u32 width = CMS_W_MAX;	/* counters a row (the arena version may
					 * take any width; the array, at most W_MAX) */
const volatile u32 depth = CMS_D_MAX;	/* rows, 1 .. CMS_D_MAX */

static __always_inline u32 rol32(u32 w, unsigned int s)
{
	return (w << s) | (w >> ((-s) & 31));
}

/* jhash2(k, 2, seed) of include/linux/jhash.h, for k = {low, high} of a u64 */
static __always_inline u32 jhash_u64(u64 key, u32 seed)
{
	u32 a, b, c;

	a = b = c = 0xdeadbeef + (2 << 2) + seed;
	b += (u32)(key >> 32);
	a += (u32)key;
	c ^= b; c -= rol32(b, 14);
	a ^= c; a -= rol32(c, 11);
	b ^= a; b -= rol32(a, 25);
	c ^= b; c -= rol32(b, 16);
	a ^= c; a -= rol32(c, 4);
	b ^= a; b -= rol32(a, 14);
	c ^= b; c -= rol32(b, 24);
	return c;
}

/* the counter for key in row r: reciprocal_scale(h, w) = h * w / 2^32 */
static __always_inline u32 cms_slot(u64 key, u32 r, u32 w)
{
	return r * w + (u32)(((u64)jhash_u64(key, r) * w) >> 32);
}

/* returns the thread ID to count, or 0 to skip this write */
static __always_inline u32 counted_tid(void)
{
	u64 id = bpf_get_current_pid_tgid();

	if (tgid && (u32)(id >> 32) != tgid)
		return 0;
	return (u32)id;
}

/* the count-min map type of Part B; not in a stock kernel's vmlinux.h */
#ifndef BPF_MAP_TYPE_COUNT_MIN
#define BPF_MAP_TYPE_COUNT_MIN 36
#endif

struct cms_value {			/* a count-min map's value: key, then count */
	u64 key;
	u64 count;
};
