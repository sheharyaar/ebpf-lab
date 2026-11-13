/* latency of a dependent register add, a store-then-load through memory, and a pointer chase */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

static double now(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec * 1e9 + t.tv_nsec;
}

#define REP100(x) x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x

static double add_chain(long n)
{
	uint64_t a = 0, one = 1;
	double t = now();

	for (long i = 0; i < n; i++)
		asm volatile(REP100("add %1, %0\n\t") : "+r"(a) : "r"(one));
	return (now() - t) / (n * 100.0);
}

static double spill_chain(long n, uint64_t *slot)
{
	uint64_t a = 0;
	double t = now();

	for (long i = 0; i < n; i++)
		asm volatile(REP100("mov %0, (%1)\n\tmov (%1), %0\n\tadd $1, %0\n\t") : "+r"(a) : "r"(slot) : "memory");
	return (now() - t) / (n * 100.0);
}

static double spill_rsp(long n)
{
	uint64_t a = 0;
	double t = now();

	for (long i = 0; i < n; i++)
		asm volatile(REP100("mov %0, -64(%%rsp)\n\tmov -64(%%rsp), %0\n\tadd $1, %0\n\t") : "+r"(a) : : "memory");
	return (now() - t) / (n * 100.0);
}

static double chase(size_t bytes, long n)
{
	size_t lines = bytes / 64, *perm = malloc(lines * sizeof(size_t));
	char *buf = aligned_alloc(4096, bytes);
	void **p;

	for (size_t i = 0; i < lines; i++)
		perm[i] = i;
	for (size_t i = lines - 1; i > 0; i--) {
		size_t j = rand() % (i + 1), t = perm[i];

		perm[i] = perm[j];
		perm[j] = t;
	}
	for (size_t i = 0; i < lines; i++)
		*(void **)(buf + perm[i] * 64) = buf + perm[(i + 1) % lines] * 64;
	p = (void **)(buf + perm[0] * 64);
	for (long i = 0; i < 2 * (long)lines; i++)
		p = *p;
	double t = now();

	for (long i = 0; i < n; i++)
		p = *p;
	t = (now() - t) / n;
	if (!p)
		puts("");
	free(perm);
	free(buf);
	return t;
}

int main(void)
{
	uint64_t slot;
	double add = add_chain(20000000), sp, sr;

	add = add_chain(20000000);
	sp = spill_chain(5000000, &slot);
	sr = spill_rsp(5000000);
	printf("add r,r          %.3f ns  (1 cycle by definition)\n", add);
	printf("store+load+add   %.3f ns  %.1f cycles (pointer in a register)\n", sp, sp / add);
	printf("store+load+add   %.3f ns  %.1f cycles (rsp-relative)\n", sr, sr / add);
	size_t sz[] = { 16 << 10, 192 << 10, 512 << 10, 6 << 20, 12 << 20, 256 << 20 };
	for (int i = 0; i < 6; i++) {
		double c = chase(sz[i], 20000000);

		printf("chase %8zu KiB  %.2f ns  %.0f cycles\n", sz[i] >> 10, c, c / add);
	}
	return 0;
}
