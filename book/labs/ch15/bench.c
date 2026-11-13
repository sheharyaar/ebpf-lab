/* bench: what each counting program in upd.bpf.o adds to a getppid() call, with N writers
 * pinned to CPUs 1..N, each making CALLS calls. Needs root (run in the VM).
 * Usage: bench upd.bpf.o MODE NTHREADS CALLS ROUNDS [prog ...]
 * Prints, per program and round: wall-clock ns per call averaged over the writers ("none"
 * is the same loop with no program attached), ns per run from run_time_ns/run_cnt (bpf_stats
 * is switched on unless NOSTATS is set), the recursion misses, and the change in the map's
 * total (all CPUs added up) against the calls made. */
#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>

struct run { const char *prog, *map; int percpu; };
static const struct run all[] = {
	{ "none", NULL, 0 },             { "t_empty", NULL, 0 },          { "t_hash_upd", "m_hash_upd", 0 },
	{ "t_np_upd", "m_np_upd", 0 },   { "t_hash_atomic", "m_hash_atomic", 0 },
	{ "t_hash_plain", "m_hash_plain", 0 }, { "t_pchash", "m_pchash", 1 },
	{ "t_lru", "m_lru", 0 },         { "t_arr_atomic", "m_arr_atomic", 0 },
	{ "t_arr_plain", "m_arr_plain", 0 }, { "t_pcarr", "m_pcarr", 1 },
};

static long calls;
static pthread_barrier_t go;
static double took[64];

static double now(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec * 1e9 + t.tv_nsec;
}

static void *writer(void *arg)
{
	cpu_set_t s;

	CPU_ZERO(&s);
	CPU_SET((long)arg, &s);
	sched_setaffinity(0, sizeof(s), &s);
	pthread_barrier_wait(&go);
	double t0 = now();
	for (long i = 0; i < calls; i++)
		syscall(SYS_getppid);
	took[(long)arg - 1] = (now() - t0) / calls;
	return NULL;
}

static unsigned long long total(struct bpf_map *m, int percpu, int ncpu)
{
	int fd = bpf_map__fd(m);
	__u32 k, next, *prev = NULL;
	__u64 v[256];
	unsigned long long t = 0;

	while (bpf_map_get_next_key(fd, prev, &next) == 0) {
		if (bpf_map_lookup_elem(fd, &next, v) == 0)
			for (int c = 0; c < (percpu ? ncpu : 1); c++)
				t += v[c];
		k = next;
		prev = &k;
	}
	return t;
}

int main(int argc, char **argv)
{
	int mode = atoi(argv[2]), n = atoi(argv[3]), rounds = atoi(argv[5]);
	int ncpu = libbpf_num_possible_cpus();
	struct bpf_object *obj = bpf_object__open_file(argv[1], NULL);
	struct bpf_map *rodata;
	pthread_t th[64];

	calls = atol(argv[4]);
	if (!obj)
		return 1;
	bpf_object__for_each_map(rodata, obj)
		if (strstr(bpf_map__name(rodata), ".rodata"))
			memcpy(bpf_map__initial_value(rodata, &(size_t){0}), &mode, sizeof(mode));
	if (bpf_object__load(obj)) {
		fprintf(stderr, "load failed\n");
		return 1;
	}
	if (!getenv("NOSTATS") && bpf_enable_stats(BPF_STATS_RUN_TIME) < 0) {
		perror("bpf_enable_stats");
		return 1;
	}
	for (int r = 0; r < rounds; r++)
		for (size_t i = 0; i < sizeof(all) / sizeof(all[0]); i++) {
			const struct run *x = &all[i];
			struct bpf_program *p;
			struct bpf_prog_info a = {}, b = {};
			__u32 len = sizeof(a);
			unsigned long long t0 = 0, t1 = 0;
			struct bpf_link *l = NULL;
			int want = argc <= 6;
			double wall = 0;

			for (int j = 6; j < argc; j++)
				want |= !strcmp(argv[j], x->prog);
			if (!want)
				continue;
			p = bpf_object__find_program_by_name(obj, strcmp(x->prog, "none") ? x->prog : "t_empty");
			if (x->map)
				t0 = total(bpf_object__find_map_by_name(obj, x->map), x->percpu, ncpu);
			bpf_prog_get_info_by_fd(bpf_program__fd(p), &a, &len);
			if (strcmp(x->prog, "none"))
				l = bpf_program__attach(p);
			if (strcmp(x->prog, "none") && !l) {
				fprintf(stderr, "attach %s failed\n", x->prog);
				return 1;
			}
			pthread_barrier_init(&go, NULL, n);
			for (long t = 0; t < n; t++)
				pthread_create(&th[t], NULL, writer, (void *)(t + 1));
			for (int t = 0; t < n; t++)
				pthread_join(th[t], NULL);
			bpf_link__destroy(l);
			for (int t = 0; t < n; t++)
				wall += took[t] / n;
			len = sizeof(b);
			bpf_prog_get_info_by_fd(bpf_program__fd(p), &b, &len);
			if (x->map)
				t1 = total(bpf_object__find_map_by_name(obj, x->map), x->percpu, ncpu);
			unsigned long long runs = b.run_cnt - a.run_cnt, misses = b.recursion_misses - a.recursion_misses;
			unsigned long long made = (unsigned long long)n * calls;
			printf("mode=%d threads=%d round=%d %-14s ns_per_call=%7.1f run_ns=%7.1f misses=%llu counted=%llu lost=%lld\n",
			       mode, n, r, x->prog, wall, runs ? (double)(b.run_time_ns - a.run_time_ns) / runs : 0.0,
			       strcmp(x->prog, "none") ? misses : 0ULL, t1 - t0,
			       x->map ? (long long)(made - misses - (t1 - t0)) : 0LL);
			fflush(stdout);
		}
	return 0;
}
