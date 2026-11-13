/* stream: events from stream.bpf.o to user space through a ring buffer or a perf buffer.
 * Usage: stream stream.bpf.o MODE NTHREADS CALLS PACE_NS
 *   MODE rb    ring buffer, a wake-up when the reader has caught up (the default)
 *        rbnw  ring buffer, BPF_RB_NO_WAKEUP; the reader looks every 10 ms
 *        pb    perf buffer, 64 pages per CPU, a wake-up after every event (libbpf's default)
 *        pb64  perf buffer, a wake-up after every 64 events
 * Writers are pinned to CPUs 1..N; each makes CALLS getppid() calls, PACE_NS apart
 * (busy-waiting). The reader is pinned to CPU 15 and counts events, the polls that
 * returned something, and its own context switches. Needs root (run in the VM). */
#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>

static long calls, pace;
static volatile int finished;
static unsigned long long got, lost;

static double now(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec * 1e9 + t.tv_nsec;
}

static void pin(int cpu)
{
	cpu_set_t s;

	CPU_ZERO(&s);
	CPU_SET(cpu, &s);
	sched_setaffinity(0, sizeof(s), &s);
}

static void *writer(void *arg)
{
	pin((long)arg);
	for (long i = 0; i < calls; i++) {
		double t = now();

		syscall(SYS_getppid);
		while (pace && now() - t < pace)
			;
	}
	__sync_fetch_and_add(&finished, 1);
	return NULL;
}

static int on_rb(void *ctx, void *data, size_t len) { got++; return 0; }
static void on_pb(void *ctx, int cpu, void *data, __u32 len) { got++; }
static void on_lost(void *ctx, int cpu, __u64 n) { lost += n; }

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

static void mapped(const char *what, unsigned long *bytes, int *n)
{
	char line[512];
	FILE *f = fopen("/proc/self/maps", "r");

	*bytes = 0;
	*n = 0;
	while (f && fgets(line, sizeof(line), f)) {
		unsigned long a, b;

		if (strstr(line, what) && sscanf(line, "%lx-%lx", &a, &b) == 2) {
			*bytes += b - a;
			(*n)++;
		}
	}
	if (f)
		fclose(f);
}

int main(int argc, char **argv)
{
	const char *mode = argv[2];
	int n = atoi(argv[3]), isrb = !strncmp(mode, "rb", 2), nw = !strcmp(mode, "rbnw");
	struct bpf_object *obj = bpf_object__open_file(argv[1], NULL);
	struct ring_buffer *rb = NULL;
	struct perf_buffer *pb = NULL;
	struct bpf_map *m;
	struct bpf_program *p;
	struct bpf_link *l;
	struct bpf_prog_info a = {}, b = {};
	struct rusage r0, r1;
	__u32 len = sizeof(a);
	unsigned long long polls = 0, dropped = 0;
	pthread_t th[64];
	double t0, t1;

	calls = atol(argv[4]);
	pace = atol(argv[5]);
	if (!obj)
		return 1;
	bpf_object__for_each_map(m, obj)
		if (strstr(bpf_map__name(m), ".rodata") && nw)
			*(__u64 *)bpf_map__initial_value(m, &(size_t){0}) = BPF_RB_NO_WAKEUP;
	bpf_program__set_autoload(bpf_object__find_program_by_name(obj, isrb ? "s_pb" : "s_rb"), false);
	if (bpf_object__load(obj) || bpf_enable_stats(BPF_STATS_RUN_TIME) < 0) {
		fprintf(stderr, "load or stats failed\n");
		return 1;
	}
	pin(15);
	if (isrb) {
		rb = ring_buffer__new(bpf_map__fd(bpf_object__find_map_by_name(obj, "rb")), on_rb, NULL, NULL);
	} else {
		LIBBPF_OPTS(perf_buffer_opts, po, .sample_period = strcmp(mode, "pb64") ? 1 : 64);
		pb = perf_buffer__new(bpf_map__fd(bpf_object__find_map_by_name(obj, "pb")), 64, on_pb, on_lost, NULL, &po);
	}
	if (!rb && !pb) {
		fprintf(stderr, "buffer setup failed\n");
		return 1;
	}
	p = bpf_object__find_program_by_name(obj, isrb ? "s_rb" : "s_pb");
	l = bpf_program__attach(p);
	bpf_prog_get_info_by_fd(bpf_program__fd(p), &a, &len);
	getrusage(RUSAGE_THREAD, &r0);
	t0 = now();
	for (long t = 0; t < n; t++)
		pthread_create(&th[t], NULL, writer, (void *)(t + 1));
	for (;;) {
		int done = finished == n, k;

		if (nw) {
			usleep(10000);
			k = ring_buffer__consume(rb);
		} else {
			k = rb ? ring_buffer__poll(rb, 100) : perf_buffer__poll(pb, 100);
		}
		if (k > 0)
			polls++;
		if (done && k <= 0)
			break;
	}
	t1 = now();
	getrusage(RUSAGE_THREAD, &r1);
	for (int t = 0; t < n; t++)
		pthread_join(th[t], NULL);
	len = sizeof(b);
	bpf_prog_get_info_by_fd(bpf_program__fd(p), &b, &len);
	if (isrb) {
		bpf_object__for_each_map(m, obj)
			if (strstr(bpf_map__name(m), ".bss"))
				bpf_map_lookup_elem(bpf_map__fd(m), &(__u32){0}, &dropped);
		lost = dropped;
	}
	{
		unsigned long rbb, pbb;
		int rbn, pbn;
		int fd = bpf_map__fd(bpf_object__find_map_by_name(obj, isrb ? "rb" : "pb"));

		mapped("bpf-map", &rbb, &rbn);
		mapped("perf_event", &pbb, &pbn);
		printf("%-4s threads=%d pace_ns=%ld events=%llu got=%llu lost=%llu polls_with_data=%llu "
		       "reader_vol_switches=%ld reader_invol=%ld ns_per_event_prog=%.1f wall_ms=%.0f "
		       "map_memlock=%ld mapped_bpf=%lu(%d) mapped_perf=%lu(%d)\n",
		       mode, n, pace, (unsigned long long)(b.run_cnt - a.run_cnt), got, lost, polls,
		       r1.ru_nvcsw - r0.ru_nvcsw, r1.ru_nivcsw - r0.ru_nivcsw,
		       (double)(b.run_time_ns - a.run_time_ns) / (b.run_cnt - a.run_cnt), (t1 - t0) / 1e6,
		       memlock(fd), rbb, rbn, pbb, pbn);
	}
	bpf_link__destroy(l);
	return 0;
}
