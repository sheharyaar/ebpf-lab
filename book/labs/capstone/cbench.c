/* cbench: the capstone's write counters, measured the way chapter "Maps" measured its own.
 *   cbench OBJ cost NW CALLS        NW writers pinned to CPUs 1..NW make CALLS one-byte
 *                                   writes each to /dev/null, first with no program, then
 *                                   with OBJ's count_writes at fentry/vfs_write; prints ns per
 *                                   write and per run (run_time_ns / run_cnt) and what the
 *                                   structure says each writer wrote
 *   cbench OBJ churn NL LW NH HW    NH heavy threads write HW times each while NL light
 *                                   threads, 64 at a time, write LW times each; then every
 *                                   thread's count or estimate against the truth
 * OBJ is one of c_hash, c_lru, c_exact (a hash), c_sketch, c_topk (an arena), c_array,
 * c_arraytopk (.bss) or c_cms, c_cmstopk (the count-min map type of a patched kernel).
 * Env: CMS_W width (default 2719), CMS_D depth (default 5), OUT file for "tid true est"
 * lines, HOLD seconds to stay loaded after the run (for bpftool). Needs root (the VM).
 * Every program counts only this process's threads (the tgid in .rodata), so the truth
 * is known here. Reading: hashes and the map type through bpf() lookups, the arena and
 * the array through plain loads from their mappings; the getppid() calls are markers. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <math.h>
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
#include <bpf/btf.h>
#include <bpf/libbpf.h>

#define TOPK 16
enum kind { HASH, ARENA, ARRAY, CMSMAP };
static const char *kname[] = { "hash", "arena", "array", "cmsmap" };

static int devnull;
static uint32_t W = 2719, D = 5;

static double now(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec * 1e9 + t.tv_nsec;
}

/* the kernel's jhash2() over a u64 key and reciprocal_scale(), as in cms.h */
static uint32_t rol32(uint32_t w, unsigned s) { return (w << s) | (w >> ((-s) & 31)); }
static uint32_t jhash_u64(uint64_t key, uint32_t seed)
{
	uint32_t a, b, c;

	a = b = c = 0xdeadbeef + (2 << 2) + seed;
	b += (uint32_t)(key >> 32);
	a += (uint32_t)key;
	c ^= b; c -= rol32(b, 14); a ^= c; a -= rol32(c, 11);
	b ^= a; b -= rol32(a, 25); c ^= b; c -= rol32(b, 16);
	a ^= c; a -= rol32(c, 4);  b ^= a; b -= rol32(a, 14);
	c ^= b; c -= rol32(b, 24);
	return c;
}
static uint32_t slot(uint64_t key, uint32_t r)
{
	return r * W + (uint32_t)(((uint64_t)jhash_u64(key, r) * W) >> 32);
}
static uint64_t estimate(const uint64_t *c, uint64_t key)
{
	uint64_t e = UINT64_MAX;

	for (uint32_t r = 0; r < D; r++)
		if (c[slot(key, r)] < e)
			e = c[slot(key, r)];
	return e;
}

/* a global of the object's .rodata or .bss, found through its BTF */
static void *global(struct bpf_object *obj, const char *sec, const char *name)
{
	struct btf *btf = bpf_object__btf(obj);
	struct bpf_map *m;
	char *data = NULL;
	int id;

	bpf_object__for_each_map(m, obj)
		if (strstr(bpf_map__name(m), sec))
			data = bpf_map__initial_value(m, &(size_t){0});
	id = btf__find_by_name_kind(btf, sec, BTF_KIND_DATASEC);
	if (!data || id < 0)
		return NULL;
	const struct btf_type *t = btf__type_by_id(btf, id);
	const struct btf_var_secinfo *v = btf_var_secinfos(t);
	for (int i = 0; i < btf_vlen(t); i++, v++)
		if (!strcmp(btf__name_by_offset(btf, btf__type_by_id(btf, v->type)->name_off), name))
			return data + v->offset;
	return NULL;
}

static int prog_run(struct bpf_object *obj, const char *name)
{
	LIBBPF_OPTS(bpf_test_run_opts, o);
	struct bpf_program *p = bpf_object__find_program_by_name(obj, name);
	int err = bpf_prog_test_run_opts(bpf_program__fd(p), &o);

	return err ? err : (int)o.retval;
}

static void memlock(struct bpf_object *obj)	/* what each map reports, from fdinfo */
{
	struct bpf_map *m;
	char path[64], line[128];

	bpf_object__for_each_map(m, obj) {
		snprintf(path, sizeof(path), "/proc/self/fdinfo/%d", bpf_map__fd(m));
		FILE *f = fopen(path, "r");
		while (f && fgets(line, sizeof(line), f))
			if (!strncmp(line, "memlock:", 8))
				printf("  map %-12s %s", bpf_map__name(m), line);
		if (f)
			fclose(f);
	}
}

/* ---- the writers ---------------------------------------------------------------- */
struct thr { pthread_t th; uint32_t tid; long writes; int cpu; double took; };
static pthread_barrier_t go;

static void *writer(void *arg)
{
	struct thr *t = arg;

	if (t->cpu >= 0) {
		cpu_set_t s;

		CPU_ZERO(&s);
		CPU_SET(t->cpu, &s);
		sched_setaffinity(0, sizeof(s), &s);
	}
	t->tid = syscall(SYS_gettid);
	if (t->cpu >= 0)
		pthread_barrier_wait(&go);
	double t0 = now();
	for (long k = 0; k < t->writes; k++)
		write(devnull, "x", 1);
	t->took = (now() - t0) / (t->writes ? t->writes : 1);
	return NULL;
}

/* ---- reading a thread's count or estimate ---------------------------------------- */
struct reader {
	enum kind k;
	int fd;				/* hash or count-min map */
	const uint64_t *c;		/* counters: the arena's or .bss's, through mmap */
	long syscalls;
};

static int64_t read_one(struct reader *r, uint32_t tid)	/* -1: no entry */
{
	if (r->k == HASH) {
		uint64_t v;

		r->syscalls++;
		return bpf_map_lookup_elem(r->fd, &tid, &v) ? -1 : (int64_t)v;
	}
	if (r->k == CMSMAP) {
		struct { uint64_t key, count; } v = { tid, 0 };

		r->syscalls++;
		return bpf_map_lookup_elem(r->fd, NULL, &v) ? -1 : (int64_t)v.count;
	}
	return estimate(r->c, tid);
}

struct sketch_hdr { uint32_t w, d; uint64_t kmin; void *top; uint64_t c[]; };
struct topnode { struct topnode *next; uint64_t tid, est; };
struct topslot { uint64_t tid, est; };

int main(int argc, char **argv)
{
	struct bpf_object *obj;
	struct bpf_program *p;
	struct bpf_link *l;
	struct bpf_prog_info a = {}, b = {};
	uint32_t len = sizeof(a);
	struct reader rd = {};
	struct sketch_hdr *sk = NULL;
	bool cost;

	if (argc < 5 || (strcmp(argv[2], "cost") && strcmp(argv[2], "churn")) ||
	    (!strcmp(argv[2], "churn") && argc < 7)) {
		fprintf(stderr, "usage: cbench OBJ cost NW CALLS | OBJ churn NL LW NH HW\n");
		return 2;
	}
	cost = !strcmp(argv[2], "cost");
	if (getenv("CMS_W"))
		W = atoi(getenv("CMS_W"));
	if (getenv("CMS_D"))
		D = atoi(getenv("CMS_D"));
	devnull = open("/dev/null", O_WRONLY);

	obj = bpf_object__open_file(argv[1], NULL);
	if (!obj) {
		fprintf(stderr, "open failed\n");
		return 1;
	}
	*(uint32_t *)global(obj, ".rodata", "tgid") = getpid();
	if (global(obj, ".rodata", "width")) {
		*(uint32_t *)global(obj, ".rodata", "width") = W;
		*(uint32_t *)global(obj, ".rodata", "depth") = D;
	}
	if (bpf_object__find_map_by_name(obj, "cms")) {
		bpf_map__set_max_entries(bpf_object__find_map_by_name(obj, "cms"), W);
		bpf_map__set_map_extra(bpf_object__find_map_by_name(obj, "cms"), D);
	}
	int err = bpf_object__load(obj);
	if (err) {
		fprintf(stderr, "load failed: %d (%s)\n", err, strerror(-err));
		return 1;
	}
	rd.k = bpf_object__find_map_by_name(obj, "arena") ? ARENA
	     : bpf_object__find_map_by_name(obj, "cms") ? CMSMAP
	     : bpf_object__find_map_by_name(obj, "write_counts") ? HASH : ARRAY;
	if (rd.k == ARENA) {
		if (prog_run(obj, "init")) {
			fprintf(stderr, "init failed\n");
			return 1;
		}
		sk = *(struct sketch_hdr **)global(obj, ".bss", "g");
		rd.c = sk->c;
		printf("arena: sketch at %p, %u x %u counters, %u pages (%u bytes)\n", (void *)sk,
		       sk->d, sk->w, *(uint32_t *)((char *)global(obj, ".bss", "g") + 8),
		       *(uint32_t *)((char *)global(obj, ".bss", "g") + 8) * 4096);
	} else if (rd.k == ARRAY) {
		rd.c = global(obj, ".bss", "c");
	} else {
		rd.fd = bpf_map__fd(bpf_object__find_map_by_name(obj, rd.k == HASH ? "write_counts" : "cms"));
	}
	memlock(obj);

	bpf_enable_stats(BPF_STATS_RUN_TIME);
	p = bpf_object__find_program_by_name(obj, "count_writes");

	int nthr;
	struct thr *t;
	long nl = 0, lw = 0, nh, hw;
	if (cost) {
		nh = atoi(argv[3]);
		hw = atol(argv[4]);
	} else {
		nl = atol(argv[3]);
		lw = atol(argv[4]);
		nh = atoi(argv[5]);
		hw = atol(argv[6]);
	}
	nthr = nh + nl;
	t = calloc(nthr, sizeof(*t));
	double bare = 0;
	if (cost) {			/* the same writes with no program, for the bare cost */
		pthread_barrier_init(&go, NULL, nh);
		for (int i = 0; i < nh; i++) {
			t[i] = (struct thr){ .writes = hw, .cpu = i + 1 };
			pthread_create(&t[i].th, NULL, writer, &t[i]);
		}
		for (int i = 0; i < nh; i++) {
			pthread_join(t[i].th, NULL);
			bare += t[i].took / nh;
		}
	}
	bpf_prog_get_info_by_fd(bpf_program__fd(p), &a, &len);
	l = bpf_program__attach(p);
	if (!l) {
		fprintf(stderr, "attach failed\n");
		return 1;
	}
	double t0 = now(), with = 0;
	if (cost) {
		for (int i = 0; i < nh; i++) {
			t[i] = (struct thr){ .writes = hw, .cpu = i + 1 };
			pthread_create(&t[i].th, NULL, writer, &t[i]);
		}
		for (int i = 0; i < nh; i++) {
			pthread_join(t[i].th, NULL);
			with += t[i].took / nh;
		}
	} else {			/* heavy writers run while the light ones come and go */
		for (int i = 0; i < nh; i++) {
			t[i] = (struct thr){ .writes = hw, .cpu = -1 };
			pthread_create(&t[i].th, NULL, writer, &t[i]);
		}
		for (long i = 0; i < nl; i += 64) {
			long n = nl - i < 64 ? nl - i : 64;

			for (long j = 0; j < n; j++) {
				t[nh + i + j] = (struct thr){ .writes = lw, .cpu = -1 };
				pthread_create(&t[nh + i + j].th, NULL, writer, &t[nh + i + j]);
			}
			for (long j = 0; j < n; j++)
				pthread_join(t[nh + i + j].th, NULL);
		}
		for (int i = 0; i < nh; i++)
			pthread_join(t[i].th, NULL);
	}
	double took = now() - t0;
	len = sizeof(b);
	bpf_prog_get_info_by_fd(bpf_program__fd(p), &b, &len);
	if (getenv("HOLD")) {
		printf("holding for %s s\n", getenv("HOLD"));
		fflush(stdout);
		sleep(atoi(getenv("HOLD")));
	}
	bpf_link__destroy(l);

	uint64_t dc = b.run_cnt - a.run_cnt, dt = b.run_time_ns - a.run_time_ns;
	if (cost)
		printf("%-6s %s nw=%ld calls=%ld: write %.1f ns bare, %.1f with; run %.1f ns (%llu runs)\n",
		       kname[rd.k], argv[1], nh, hw, bare, with, dc ? (double)dt / dc : 0,
		       (unsigned long long)dc);
	else
		printf("%-6s %s light %ld x %ld, heavy %ld x %ld: %.1f s, run %.1f ns (%llu runs)\n",
		       kname[rd.k], argv[1], nl, lw, nh, hw, took / 1e9, dc ? (double)dt / dc : 0,
		       (unsigned long long)dc);

	/* distinct thread IDs? (raise kernel.pid_max, or IDs are reused) */
	long dup = 0;
	if (!cost) {
		char *seen = calloc(1 << 22, 1);
		for (int i = 0; i < nthr; i++)
			dup += t[i].tid < (1u << 22) && seen[t[i].tid]++;
		free(seen);
	}

	/* read every thread's count or estimate */
	syscall(SYS_getppid);			/* marker: reading starts */
	double r0 = now();
	int64_t *got = calloc(nthr, sizeof(*got));
	for (int i = 0; i < nthr; i++)
		got[i] = read_one(&rd, t[i].tid);
	double rtook = now() - r0;
	syscall(SYS_getppid);			/* marker: reading ends */

	uint64_t N = 0;
	for (int i = 0; i < nthr; i++)
		N += t[i].writes;
	printf("  read %d threads in %.0f us with %ld bpf() calls; %ld thread IDs reused\n",
	       nthr, rtook / 1e3, rd.syscalls, dup);
	if (rd.k == HASH) {
		uint64_t *nofit = global(obj, ".bss", "nofit");
		long held = 0, exact = 0, heavy_exact = 0;

		for (int i = 0; i < nthr; i++) {
			held += got[i] >= 0;
			exact += got[i] == t[i].writes;
			heavy_exact += i < nh && got[i] == t[i].writes;
		}
		printf("  entries for %ld of %d threads, %ld exact (heavy %ld of %ld exact); "
		       "inserts refused %llu\n", held, nthr, exact, heavy_exact, nh,
		       (unsigned long long)*nofit);
		for (int i = 0; i < nh && i < 4; i++)
			printf("  heavy tid %u: %ld writes, counted %lld\n", t[i].tid, t[i].writes,
			       (long long)got[i]);
	} else {
		double eps = M_E / W, bound = eps * N;
		long over = 0, under = 0;
		int64_t emax[2] = {0, 0};
		double esum[2] = {0, 0};
		long cnt[2] = {0, 0};

		for (int i = 0; i < nthr; i++) {
			int64_t e = got[i] - t[i].writes;
			int g = i < nh;		/* 1: heavy */

			under += e < 0;
			over += e > bound;
			esum[g] += e;
			cnt[g]++;
			if (e > emax[g])
				emax[g] = e;
		}
		printf("  w %u, d %u: epsilon %.5f, delta %.4f; N %llu; bound epsilon*N %.0f\n",
		       W, D, eps, exp(-(double)D), (unsigned long long)N, bound);
		if (cnt[0])
			printf("  light: mean error %.1f, max %lld\n", esum[0] / cnt[0], (long long)emax[0]);
		printf("  heavy: mean error %.1f, max %lld (%.3f%% of a heavy count)\n",
		       esum[1] / cnt[1], (long long)emax[1], hw ? 100.0 * emax[1] / hw : 0);
		printf("  below the truth: %ld; above the bound: %ld of %d (%.4f%%)\n", under, over,
		       nthr, 100.0 * over / nthr);
		if (rd.k == ARENA) {
			uint64_t sum = 0;

			for (uint32_t j = 0; j < W; j++)
				sum += sk->c[j];
			printf("  row 0 sums to %llu (every row holds N)\n", (unsigned long long)sum);
		}
		if (cost)
			for (int i = 0; i < nh; i++)
				printf("  tid %u: %ld writes, estimate %lld\n", t[i].tid, t[i].writes,
				       (long long)got[i]);
	}

	/* the table of the heaviest, if the object keeps one */
	struct { uint64_t tid, est; } top[TOPK];
	int ntop = 0;
	if (rd.k == ARENA && sk->top) {
		for (struct topnode *n = sk->top; n && ntop < TOPK; n = n->next) {
			top[ntop].tid = n->tid;
			top[ntop++].est = n->est;
		}
		printf("  table of the heaviest: a list from %p, %d nodes\n", sk->top, ntop);
	} else if (global(obj, ".bss", "top")) {
		struct topslot *s = global(obj, ".bss", "top");

		for (int i = 0; i < TOPK; i++)	/* tid 0: a slot never used */
			if (s[i].tid) {
				top[ntop].tid = s[i].tid;
				top[ntop++].est = s[i].est;
			}
	}
	for (int i = 0; i < ntop; i++)		/* largest estimate first */
		for (int j = i + 1; j < ntop; j++)
			if (top[j].est > top[i].est) {
				uint64_t x = top[i].tid, y = top[i].est;
				top[i] = top[j];
				top[j].tid = x;
				top[j].est = y;
			}
	for (int i = 0; i < ntop && i < 6 && !cost; i++) {
		long truth = -1;

		for (int j = 0; j < nthr; j++)
			if (t[j].tid == top[i].tid)
				truth = t[j].writes;
		printf("    tid %-8llu estimate %-8llu true %ld\n", (unsigned long long)top[i].tid,
		       (unsigned long long)top[i].est, truth);
	}

	if (getenv("OUT")) {
		FILE *f = fopen(getenv("OUT"), "w");

		for (int i = 0; f && i < nthr; i++)
			fprintf(f, "%u %ld %lld\n", t[i].tid, t[i].writes, (long long)got[i]);
		if (f)
			fclose(f);
	}
	return 0;
}
