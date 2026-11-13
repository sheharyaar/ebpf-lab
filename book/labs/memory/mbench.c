/* mbench: the write counter three ways (c_hash, c_rb, c_arena .bpf.o), measured the way the
 * chapter "Maps" measured its counters. Loads OBJ, puts PREFILL made-up threads in it (IDs from
 * 0x80000000, above any real one), runs NW writer threads pinned to CPUs 1..NW, CALLS one-byte
 * writes each to /dev/null, first with no program and then with the counter attached at
 * fentry/vfs_write, and prints ns per write (wall clock), ns per run (run_time_ns / run_cnt) and
 * each writer's count read back the way the structure allows: lookups for the hash, a drain
 * program for the tree, plain loads through the arena's mapping for the arena.
 * Usage: mbench OBJ NW CALLS PREFILL [show]       Needs root (run it in the VM).
 * CALLS 0: only load, prefill and print what the prefill added to memory.current of the
 * cgroup named by env CG and to the 64-byte kmalloc caches. Env HOLD=s: after the measured
 * run, stay loaded and attached for s seconds, for bpftool.
 * Between the two getppid() calls around "reading" the program makes no other system call
 * of its own except, for the hash, bpf() lookups and, for the tree, one BPF_PROG_RUN. */
#define _GNU_SOURCE
#include <fcntl.h>
#include <pthread.h>
#include <sched.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <linux/bpf.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>

/* the arena hash table as user space sees it: the layout of bpf_arena_htab.h, whose pointers
 * the program stored as user addresses */
struct anode { struct anode *next, **pprev; };
struct aelem { int hash, key, value; struct anode hash_node; };
struct ahtab { struct anode **buckets; int n_buckets; };

enum kind { HASH, TREE, ARENA };
static long calls;
static int nw, devnull;
static pthread_barrier_t go;
static double took[64];
static uint32_t tids[64];

static double now(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec * 1e9 + t.tv_nsec;
}

static void *writer(void *arg)
{
	long i = (long)arg;
	cpu_set_t s;

	CPU_ZERO(&s);
	CPU_SET(i + 1, &s);
	sched_setaffinity(0, sizeof(s), &s);
	tids[i] = syscall(SYS_gettid);
	pthread_barrier_wait(&go);
	double t0 = now();
	for (long k = 0; k < calls; k++)
		write(devnull, "x", 1);
	took[i] = (now() - t0) / calls;
	return NULL;
}

static double run_writers(void)
{
	pthread_t th[64];
	double w = 0;

	pthread_barrier_init(&go, NULL, nw);
	for (long i = 0; i < nw; i++)
		pthread_create(&th[i], NULL, writer, (void *)i);
	for (int i = 0; i < nw; i++)
		pthread_join(th[i], NULL);
	pthread_barrier_destroy(&go);
	for (int i = 0; i < nw; i++)
		w += took[i];
	return w / nw;
}

static long long cg_bytes(void)		/* memory.current of the cgroup in env CG */
{
	char path[512];
	long long v = -1;
	FILE *f;

	if (!getenv("CG"))
		return -1;
	snprintf(path, sizeof(path), "%s/memory.current", getenv("CG"));
	f = fopen(path, "r");
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

static int prog_run(struct bpf_object *obj, const char *name, void *ctx, int sz)
{
	LIBBPF_OPTS(bpf_test_run_opts, o, .ctx_in = ctx, .ctx_size_in = sz);
	struct bpf_program *p = bpf_object__find_program_by_name(obj, name);
	int err = bpf_prog_test_run_opts(bpf_program__fd(p), &o);

	return err ? err : (int)o.retval;
}

static void *bss(struct bpf_object *obj)
{
	struct bpf_map *m;

	bpf_object__for_each_map(m, obj)
		if (strstr(bpf_map__name(m), ".bss"))
			return bpf_map__initial_value(m, &(size_t){0});
	return NULL;
}

int main(int argc, char **argv)
{
	struct { uint32_t first, count; } fa = { 0x80000000u, 0 };
	struct bpf_object *obj;
	struct bpf_program *p;
	struct bpf_link *l;
	struct bpf_prog_info a = {}, b = {};
	uint32_t len = sizeof(a);
	enum kind k;
	long keys = 0, got[64] = {0};
	bool show = argc > 5 && !strcmp(argv[5], "show");

	if (argc < 5) {
		fprintf(stderr, "usage: mbench OBJ NW CALLS PREFILL [show]\n");
		return 2;
	}
	nw = atoi(argv[2]);
	calls = atol(argv[3]);
	fa.count = atoi(argv[4]);
	devnull = open("/dev/null", O_WRONLY);
	obj = bpf_object__open_file(argv[1], NULL);
	if (!obj || bpf_object__load(obj)) {
		fprintf(stderr, "load failed\n");
		return 1;
	}
	k = bpf_object__find_map_by_name(obj, "arena") ? ARENA
	  : bpf_object__find_map_by_name(obj, "counts_tree") ? TREE : HASH;
	if (k == ARENA && prog_run(obj, "init", NULL, 0)) {
		fprintf(stderr, "init failed\n");
		return 1;
	}
	long long m0 = cg_bytes(), s0 = slab64();
	if (fa.count && k == HASH) {
		int fd = bpf_map__fd(bpf_object__find_map_by_name(obj, "write_counts"));
		uint64_t one = 1;

		for (uint32_t i = 0; i < fa.count; i++) {
			uint32_t key = fa.first + i;
			bpf_map_update_elem(fd, &key, &one, BPF_NOEXIST);
		}
	} else if (fa.count && prog_run(obj, "fill", &fa, sizeof(fa))) {
		fprintf(stderr, "fill failed\n");
		return 1;
	}
	if (calls == 0) {			/* memory only: what PREFILL keys cost */
		long long m1 = cg_bytes(), s1 = slab64();

		printf("%-7s %u keys: memory.current %+lld B (%.1f B a key); 64-byte slab objects %+lld\n",
		       k == HASH ? "hash" : k == TREE ? "rbtree" : "arena", fa.count, m1 - m0,
		       fa.count ? (double)(m1 - m0) / fa.count : 0, s1 - s0);
		return 0;
	}
	bpf_enable_stats(BPF_STATS_RUN_TIME);
	p = bpf_object__find_program_by_name(obj, "count_writes");
	double none = run_writers();
	bpf_prog_get_info_by_fd(bpf_program__fd(p), &a, &len);
	l = bpf_program__attach(p);
	if (!l) {
		fprintf(stderr, "attach failed\n");
		return 1;
	}
	double with = run_writers();
	len = sizeof(b);
	bpf_prog_get_info_by_fd(bpf_program__fd(p), &b, &len);
	if (getenv("HOLD")) {			/* stay loaded and attached, for bpftool */
		printf("holding for %s s\n", getenv("HOLD"));
		fflush(stdout);
		sleep(atoi(getenv("HOLD")));
	}
	bpf_link__destroy(l);

	syscall(SYS_getppid);			/* marker: reading starts */
	if (k == HASH) {
		int fd = bpf_map__fd(bpf_object__find_map_by_name(obj, "write_counts"));
		uint32_t key, next, *prev = NULL;
		uint64_t v;

		while (bpf_map_get_next_key(fd, prev, &next) == 0) {
			keys++;
			key = next;
			prev = &key;
		}
		for (int i = 0; i < nw; i++)
			if (bpf_map_lookup_elem(fd, &tids[i], &v) == 0)
				got[i] = v;
	} else if (k == TREE) {
		struct rec { uint32_t tid, pad; uint64_t count; } *out;
		char *base = bss(obj);

		prog_run(obj, "drain", NULL, 0);
		out = (void *)base;			/* dump.out[8192], then dump.n */
		keys = *(uint32_t *)(base + 8192 * sizeof(*out));
		for (long j = 0; j < keys; j++)
			for (int i = 0; i < nw; i++)
				if (out[j].tid == tids[i])
					got[i] = out[j].count;
	} else {
		struct ahtab *h = *(struct ahtab **)bss(obj);	/* g.htab */

		for (int bkt = 0; h && bkt < h->n_buckets; bkt++)
			for (struct anode *n = h->buckets[bkt]; n; n = n->next) {
				struct aelem *e = (void *)((char *)n - __builtin_offsetof(struct aelem, hash_node));

				keys++;
				for (int i = 0; i < nw; i++)
					if ((uint32_t)e->key == tids[i])
						got[i] = e->value;
			}
		if (show && h)
			printf("arena: htab at %p, buckets at %p, %d buckets\n", (void *)h,
			       (void *)h->buckets, h->n_buckets);
	}
	syscall(SYS_getppid);			/* marker: reading ends */

	long sum = 0;
	for (int i = 0; i < nw; i++)
		sum += got[i];
	uint64_t dc = b.run_cnt - a.run_cnt, dt = b.run_time_ns - a.run_time_ns;
	printf("%-7s nw=%d calls=%ld prefill=%u: write %.1f ns bare, %.1f with; run %.1f ns "
	       "(%llu runs); keys %ld; writers counted %ld of %ld\n",
	       k == HASH ? "hash" : k == TREE ? "rbtree" : "arena", nw, calls, fa.count,
	       none, with, dc ? (double)dt / dc : 0, (unsigned long long)dc, keys, sum, nw * calls);
	if (show)
		for (int i = 0; i < nw; i++)
			printf("  tid %u: %ld writes counted\n", tids[i], got[i]);
	return 0;
}
