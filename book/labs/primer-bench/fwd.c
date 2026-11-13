#include <stdio.h>
#include <stdint.h>
#include <time.h>
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1e9+t.tv_nsec;}
#define R10(x) x x x x x x x x x x
#define R100(x) R10(R10(x))
int main(void)
{
	uint64_t a = 0, one = 1, slot[8];
	uint64_t *p = slot, *q;
	double t, add, fw;

	asm volatile("" : "=r"(q) : "0"(p));   /* same address, a different register */
	for (int k = 0; k < 2; k++) {
		t = now();
		for (long i = 0; i < 20000000; i++)
			asm volatile(R100("add %1, %0\n\t") : "+r"(a) : "r"(one));
		add = (now() - t) / 2e9;
		t = now();
		for (long i = 0; i < 5000000; i++)
			asm volatile(R100("mov %0, (%1)\n\tmov (%2), %0\n\tadd $1, %0\n\t") : "+r"(a) : "r"(p), "r"(q) : "memory");
		fw = (now() - t) / 5e8;
	}
	printf("add %.3f ns; store via one register, load via another, add: %.3f ns = %.1f cycles\n", add, fw, fw / add);
	return 0;
}
