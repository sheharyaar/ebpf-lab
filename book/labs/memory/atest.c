/* atest: run the syscall programs of alloc.bpf.o in the order given, each once with its n,
 * and print ns per operation, failures, and what the run changed in memory: this cgroup's
 * memory.current (env CG names the cgroup directory) and the active objects of the 64-byte
 * kmalloc caches in /proc/slabinfo. At the end, print the programs' stderr stream.
 * Usage: atest alloc.bpf.o PROG:N [PROG:N ...]        Needs root (run it in the VM).
 * sleep:MS in the list pauses MS milliseconds, so that grace periods and refills can pass.
 * Env HOLD=s: before reading the streams, stay loaded s seconds (for bpftool prog tracelog). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <linux/bpf.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>

struct res { unsigned long long ns, fails, n, val; void *first; };

static long long cg_bytes(void)
{
	char p[512];
	long long v = -1;
	FILE *f;

	if (!getenv("CG"))
		return -1;
	snprintf(p, sizeof(p), "%s/memory.current", getenv("CG"));
	f = fopen(p, "r");
	if (f) {
		if (fscanf(f, "%lld", &v) != 1)
			v = -1;
		fclose(f);
	}
	return v;
}

static long long slab64(void)		/* active objects in kmalloc-64 and kmalloc-cg-64 */
{
	char line[512], name[64];
	long long act, sum = 0;
	FILE *f = fopen("/proc/slabinfo", "r");

	while (f && fgets(line, sizeof(line), f))
		if (sscanf(line, "%63s %lld", name, &act) == 2 &&
		    (!strcmp(name, "kmalloc-64") || !strcmp(name, "kmalloc-cg-64")))
			sum += act;
	if (f)
		fclose(f);
	return sum;
}

int main(int argc, char **argv)
{
	struct bpf_object *obj = bpf_object__open_file(argv[1], NULL);
	struct res *r = NULL;
	struct bpf_map *m;
	char buf[4096];
	int n;

	if (!obj || bpf_object__load(obj)) {
		fprintf(stderr, "load failed\n");
		return 1;
	}
	bpf_object__for_each_map(m, obj) {
		if (strstr(bpf_map__name(m), ".bss"))
			r = bpf_map__initial_value(m, &(size_t){0});
		if (bpf_map__type(m) == BPF_MAP_TYPE_ARENA)
			printf("arena %s mapped at %p in this process\n", bpf_map__name(m),
			       bpf_map__initial_value(m, &(size_t){0}));
	}
	for (int i = 2; i < argc; i++) {
		char name[64];
		struct { unsigned int n; } a;
		LIBBPF_OPTS(bpf_test_run_opts, o, .ctx_in = &a, .ctx_size_in = sizeof(a));
		struct bpf_program *p;
		long long m0, m1, s0, s1;

		if (sscanf(argv[i], "%63[^:]:%u", name, &a.n) != 2)
			return 2;
		if (!strcmp(name, "sleep")) {		/* sleep:MS lets grace periods and refills pass */
			usleep(a.n * 1000);
			continue;
		}
		p = bpf_object__find_program_by_name(obj, name);
		if (!p)
			return 2;
		m0 = cg_bytes();
		s0 = slab64();
		int err = bpf_prog_test_run_opts(bpf_program__fd(p), &o);
		m1 = cg_bytes();
		s1 = slab64();
		printf("%-10s n=%-7u %8.1f ns each, %llu failed, ret %d err %d; memory.current %+lld B "
		       "(%+.1f B each); 64-byte slab objects %+lld; val %llu\n",
		       name, a.n, r->n ? (double)r->ns / r->n : 0, r->fails, o.retval, err,
		       m1 - m0, a.n ? (double)(m1 - m0) / a.n : 0, s1 - s0, r->val);
		fflush(stdout);
		r->ns = r->fails = r->n = 0;
	}
	if (getenv("HOLD")) {			/* stay loaded, for bpftool prog tracelog */
		printf("holding for %s s\n", getenv("HOLD"));
		fflush(stdout);
		sleep(atoi(getenv("HOLD")));
	}
	struct bpf_program *p;
	bpf_object__for_each_program(p, obj) {
		int first = 1;

		while ((n = bpf_prog_stream_read(bpf_program__fd(p), BPF_STREAM_STDERR, buf,
						 sizeof(buf) - 1, NULL)) > 0) {
			buf[n] = 0;
			if (first)
				printf("--- stderr stream of %s:\n", bpf_program__name(p));
			first = 0;
			fputs(buf, stdout);
		}
	}
	return 0;
}
