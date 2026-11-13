/* mapread: what it costs user space to read a 1,024-entry map, and what the maps weigh.
 * Needs CAP_BPF (run as root in the VM). Prints memlock per map and ns per key per method. */
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/mman.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>

#define N 1024
#define ROUNDS 200

static volatile __u64 sink;

static double now(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec * 1e9 + t.tv_nsec;
}

static long memlock(int fd)
{
	char path[64], line[128];
	long v = -1;
	FILE *f;

	snprintf(path, sizeof(path), "/proc/self/fdinfo/%d", fd);
	f = fopen(path, "r");
	while (f && fgets(line, sizeof(line), f))
		if (!strncmp(line, "memlock:", 8))
			v = atol(line + 8);
	if (f)
		fclose(f);
	return v;
}

int main(void)
{
	LIBBPF_OPTS(bpf_map_create_opts, mm, .map_flags = BPF_F_MMAPABLE);
	LIBBPF_OPTS(bpf_map_create_opts, np, .map_flags = BPF_F_NO_PREALLOC);
	LIBBPF_OPTS(bpf_map_batch_opts, bo);
	int ncpu = libbpf_num_possible_cpus();
	int h = bpf_map_create(BPF_MAP_TYPE_HASH, "rd_hash", 4, 8, N, NULL);
	int hn = bpf_map_create(BPF_MAP_TYPE_HASH, "rd_hash_np", 4, 8, N, &np);
	int pc = bpf_map_create(BPF_MAP_TYPE_PERCPU_HASH, "rd_pcpu", 4, 8, N, NULL);
	int a = bpf_map_create(BPF_MAP_TYPE_ARRAY, "rd_array", 4, 8, N, NULL);
	int am = bpf_map_create(BPF_MAP_TYPE_ARRAY, "rd_array_mm", 4, 8, N, &mm);
	__u32 key, next, keys[N], out;
	__u64 val, vals[N], *pcv = calloc(ncpu, 8), *m;
	double t0, t1;
	int r, n, err, calls;

	if (h < 0 || hn < 0 || pc < 0 || a < 0 || am < 0) {
		perror("bpf_map_create");
		return 1;
	}
	printf("possible CPUs %d\n", ncpu);
	printf("memlock, 1024 x (4 B key, 8 B value): hash %ld, hash no_prealloc (empty) %ld, percpu_hash %ld, array %ld, array mmapable %ld\n",
	       memlock(h), memlock(hn), memlock(pc), memlock(a), memlock(am));
	for (key = 1; key <= N; key++) {
		val = key;
		bpf_map_update_elem(h, &key, &val, BPF_ANY);
		bpf_map_update_elem(hn, &key, &val, BPF_ANY);
		bpf_map_update_elem(pc, &key, pcv, BPF_ANY);
		bpf_map_update_elem(a, &(__u32){ key - 1 }, &val, BPF_ANY);
	}
	printf("memlock after filling: hash no_prealloc %ld\n", memlock(hn));

	/* 1. the fixed loader's walk: get_next_key, then lookup, two bpf() calls per key */
	t0 = now();
	for (r = 0; r < ROUNDS; r++) {
		__u32 *prev = NULL;

		n = 0;
		while (bpf_map_get_next_key(h, prev, &next) == 0) {
			bpf_map_lookup_elem(h, &next, &val);
			sink += val;
			key = next;
			prev = &key;
			n++;
		}
		if (n != N) {
			fprintf(stderr, "walk saw %d keys\n", n);
			return 1;
		}
	}
	t1 = now();
	printf("hash: get_next_key + lookup_elem      %6.0f ns per key\n", (t1 - t0) / ROUNDS / N);

	/* 2. keys known in advance: one bpf() call per key */
	t0 = now();
	for (r = 0; r < ROUNDS; r++)
		for (key = 1; key <= N; key++) {
			bpf_map_lookup_elem(h, &key, &val);
			sink += val;
		}
	t1 = now();
	printf("hash: lookup_elem, keys known        %6.0f ns per key\n", (t1 - t0) / ROUNDS / N);

	/* 3. batch: as many keys and values as fit in one bpf() call */
	t0 = now();
	for (r = 0; r < ROUNDS; r++) {
		void *in = NULL;
		__u32 cnt;

		n = 0;
		calls = 0;
		do {
			cnt = N - n;
			err = bpf_map_lookup_batch(h, in, &out, keys + n, vals + n, &cnt, &bo);
			n += cnt;
			in = &out;
			calls++;
		} while (!err && n < N);
		if (n != N || (err && err != -ENOENT)) {
			fprintf(stderr, "batch read %d keys, err %d\n", n, err);
			return 1;
		}
		sink += vals[0];
	}
	t1 = now();
	printf("hash: lookup_batch                   %6.1f ns per key (%d bpf() calls per round)\n",
	       (t1 - t0) / ROUNDS / N, calls);

	/* 4. per-CPU hash: one bpf() call copies one value per possible CPU */
	t0 = now();
	for (r = 0; r < ROUNDS; r++)
		for (key = 1; key <= N; key++) {
			bpf_map_lookup_elem(pc, &key, pcv);
			sink += pcv[0];
		}
	t1 = now();
	printf("percpu_hash: lookup_elem, keys known %6.0f ns per key (%d values copied)\n",
	       (t1 - t0) / ROUNDS / N, ncpu);

	/* 5. array: one bpf() call per index, then the same array through mmap() */
	t0 = now();
	for (r = 0; r < ROUNDS; r++)
		for (key = 0; key < N; key++) {
			bpf_map_lookup_elem(a, &key, &val);
			sink += val;
		}
	t1 = now();
	printf("array: lookup_elem                   %6.0f ns per key\n", (t1 - t0) / ROUNDS / N);

	m = mmap(NULL, N * 8, PROT_READ | PROT_WRITE, MAP_SHARED, am, 0);
	if (m == MAP_FAILED) {
		perror("mmap");
		return 1;
	}
	t0 = now();
	for (r = 0; r < ROUNDS * 100; r++)
		for (key = 0; key < N; key++)
			sink += ((volatile __u64 *)m)[key];
	t1 = now();
	printf("array mmapable: load through mmap()  %6.2f ns per key, no bpf() call\n",
	       (t1 - t0) / (ROUNDS * 100) / N);
	return 0;
}
