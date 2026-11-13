/* mem: what each map layout weighs at the same size, 1,024 entries of a 4-byte key and
 * an 8-byte value (a 256 KiB ring buffer, 16 perf slots, a 1,024-page arena), as fdinfo's
 * memlock reports it and as the memory cgroup is charged for it.
 * Run as root inside a cgroup with the memory controller; pass the cgroup's directory.
 * Usage: mem /sys/fs/cgroup/c15 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>

#define N 1024
static char cg[256];

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

static long charged(void)
{
	char path[300];
	long v = -1;
	FILE *f;

	sync();
	snprintf(path, sizeof(path), "%s/memory.current", cg);
	f = fopen(path, "r");
	if (f && fscanf(f, "%ld", &v) != 1)
		v = -1;
	if (f)
		fclose(f);
	return v;
}

/* the cgroup's per-CPU charge, the "percpu" line of memory.stat */
static long percpu_charged(void)
{
	char path[300], line[256];
	long v = -1;
	FILE *f;

	snprintf(path, sizeof(path), "%s/memory.stat", cg);
	f = fopen(path, "r");
	while (f && fgets(line, sizeof(line), f))
		if (!strncmp(line, "percpu ", 7))
			v = atol(line + 7);
	if (f)
		fclose(f);
	return v;
}

static void fill(int fd, int type, int ncpu)
{
	__u64 *v = calloc(ncpu, 8);

	for (__u32 k = 0; k < N; k++)
		if (bpf_map_update_elem(fd, &k, v, BPF_ANY))
			fprintf(stderr, "fill type %d key %u failed\n", type, k);
	free(v);
}

static void one(const char *name, int type, __u32 ks, __u32 vs, __u32 max, __u32 flags, int dofill, int ncpu)
{
	LIBBPF_OPTS(bpf_map_create_opts, o, .map_flags = flags);
	long c0 = charged(), c1, c2;
	int fd = bpf_map_create(type, name, ks, vs, max, &o);
	long m1, m2 = -1;

	if (fd < 0) {
		printf("%-22s create failed: %s\n", name, strerror(-fd));
		return;
	}
	c1 = charged();
	m1 = memlock(fd);
	if (dofill) {
		fill(fd, type, ncpu);
		m2 = memlock(fd);
	}
	c2 = charged();
	printf("%-22s memlock_empty=%8ld memlock_full=%8ld per_entry_full=%7.1f memcg_create=%8ld memcg_full=%8ld\n",
	       name, m1, dofill ? m2 : m1, (double)(dofill ? m2 : m1) / max, c1 - c0, c2 - c0);
}

int main(int argc, char **argv)
{
	int ncpu = libbpf_num_possible_cpus();

	snprintf(cg, sizeof(cg), "%s", argc > 1 ? argv[1] : "/sys/fs/cgroup");
	printf("possible CPUs %d, page %ld\n", ncpu, sysconf(_SC_PAGESIZE));
	one("array", BPF_MAP_TYPE_ARRAY, 4, 8, N, 0, 0, ncpu);
	one("array_mmapable", BPF_MAP_TYPE_ARRAY, 4, 8, N, BPF_F_MMAPABLE, 0, ncpu);
	one("percpu_array", BPF_MAP_TYPE_PERCPU_ARRAY, 4, 8, N, 0, 0, ncpu);
	one("hash", BPF_MAP_TYPE_HASH, 4, 8, N, 0, 1, ncpu);
	one("hash_no_prealloc", BPF_MAP_TYPE_HASH, 4, 8, N, BPF_F_NO_PREALLOC, 1, ncpu);
	one("lru_hash", BPF_MAP_TYPE_LRU_HASH, 4, 8, N, 0, 1, ncpu);
	one("lru_hash_no_common", BPF_MAP_TYPE_LRU_HASH, 4, 8, N, BPF_F_NO_COMMON_LRU, 1, ncpu);
	one("percpu_hash", BPF_MAP_TYPE_PERCPU_HASH, 4, 8, N, 0, 1, ncpu);
	one("lru_percpu_hash", BPF_MAP_TYPE_LRU_PERCPU_HASH, 4, 8, N, 0, 1, ncpu);
	one("rhash", BPF_MAP_TYPE_RHASH, 4, 8, N, BPF_F_NO_PREALLOC, 1, ncpu);
	one("ringbuf_256k", BPF_MAP_TYPE_RINGBUF, 0, 0, 256 * 1024, 0, 0, ncpu);
	one("perf_event_array_16", BPF_MAP_TYPE_PERF_EVENT_ARRAY, 4, 4, ncpu, 0, 0, ncpu);

	/* the arena: memlock says 0 whatever is in it; the cgroup sees each page as it is touched */
	{
		LIBBPF_OPTS(bpf_map_create_opts, o, .map_flags = BPF_F_MMAPABLE);
		long c0 = charged();
		int fd = bpf_map_create(BPF_MAP_TYPE_ARENA, "arena_1024p", 0, 0, N, &o);
		char *p;

		if (fd < 0) {
			printf("arena create failed: %s\n", strerror(-fd));
			return 0;
		}
		p = mmap(NULL, (size_t)N * 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
		if (p == MAP_FAILED) {
			perror("arena mmap");
			return 0;
		}
		long c1 = charged(), m1 = memlock(fd);
		for (int i = 0; i < 256; i++)
			p[(size_t)i * 4096] = 1;
		printf("%-22s memlock_empty=%8ld memlock_256_pages=%8ld memcg_create=%8ld memcg_256_pages=%8ld\n",
		       "arena_1024p", m1, memlock(fd), c1 - c0, charged() - c0);
	}

	/* the same hash 64 times larger, so that the cgroup's page rounding is small beside it */
	one("hash_65536", BPF_MAP_TYPE_HASH, 4, 8, 64 * N, 0, 0, ncpu);
	{
		long p0 = percpu_charged();

		one("percpu_hash_65536", BPF_MAP_TYPE_PERCPU_HASH, 4, 8, 64 * N, 0, 0, ncpu);
		printf("%-22s memory.stat percpu rose by %ld\n", "percpu_hash_65536", percpu_charged() - p0);
	}
	return 0;
}
