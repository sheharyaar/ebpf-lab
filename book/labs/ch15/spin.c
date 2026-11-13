#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <sys/syscall.h>
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec * 1e9 + t.tv_nsec; }
int main(int argc, char **argv) {
	long n = atol(argv[2]); volatile unsigned long x = 0; double t0 = now();
	if (argv[1][0] == 's') for (long i = 0; i < n; i++) syscall(SYS_getppid);
	else for (long i = 0; i < n; i++) x += i;
	printf("%s %.1f ns per iteration\n", argv[1], (now() - t0) / n);
	return 0;
}
