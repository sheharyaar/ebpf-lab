/* pokebench: what one update of a prog-array slot costs from user space, when no program,
 * one, eight or 32 programs hold a direct tail call to that slot.
 * Every caller is a fresh load of poke.bpf.o whose map "jt" is replaced, through
 * bpf_map__reuse_fd(), by the array of the first load, so all of them track one array.
 * Usage (root): pokebench poke.bpf.o */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>

static const char *path;

static double now(void)
{
	struct timespec ts;

	clock_gettime(CLOCK_MONOTONIC, &ts);
	return ts.tv_sec * 1e9 + ts.tv_nsec;
}

static int cmp(const void *a, const void *b)
{
	double x = *(const double *)a, y = *(const double *)b;

	return x < y ? -1 : x > y;
}

static void report(const char *what, int callers, double *d, int n)
{
	double sum = 0;

	for (int i = 0; i < n; i++)
		sum += d[i];
	qsort(d, n, sizeof(*d), cmp);
	printf("%-34s callers=%-2d n=%-4d median_us=%.2f p90_us=%.2f mean_us=%.2f\n",
	       what, callers, n, d[n / 2] / 1e3, d[n * 9 / 10] / 1e3, sum / n / 1e3);
}

static struct bpf_object *load(int jtfd)
{
	struct bpf_object *obj = bpf_object__open_file(path, NULL);

	if (!obj) {
		perror("open");
		exit(1);
	}
	if (jtfd >= 0) {
		bpf_map__reuse_fd(bpf_object__find_map_by_name(obj, "jt"), jtfd);
		bpf_program__set_autoload(bpf_object__find_program_by_name(obj, "caller_var"), false);
		bpf_program__set_autoload(bpf_object__find_program_by_name(obj, "t1"), false);
		bpf_program__set_autoload(bpf_object__find_program_by_name(obj, "t2"), false);
	}
	if (bpf_object__load(obj)) {
		fprintf(stderr, "load failed\n");
		exit(1);
	}
	return obj;
}

static int fd_of(struct bpf_object *obj, const char *name)
{
	return bpf_program__fd(bpf_object__find_program_by_name(obj, name));
}

static int retval(int prog)
{
	char pkt[64] = { 0 };
	LIBBPF_OPTS(bpf_test_run_opts, o, .data_in = pkt, .data_size_in = sizeof(pkt), .repeat = 1);

	if (bpf_prog_test_run_opts(prog, &o))
		return -1;
	return o.retval;
}

/* replace a filled slot again and again, alternating two programs */
static void replace(const char *what, int callers, int map, __u32 key, int a, int b, int n)
{
	double *d = calloc(n, sizeof(*d));

	bpf_map_update_elem(map, &key, &a, BPF_ANY);
	for (int i = 0; i < n; i++) {
		int v = i & 1 ? a : b;
		double t0 = now();

		if (bpf_map_update_elem(map, &key, &v, BPF_ANY))
			perror("update");
		d[i] = now() - t0;
	}
	report(what, callers, d, n);
	free(d);
}

/* fill an empty slot, then empty it again */
static void fill_empty(const char *what, int callers, int map, __u32 key, int a, int n)
{
	double *ins = calloc(n, sizeof(double)), *del = calloc(n, sizeof(double));
	char l[80];

	bpf_map_delete_elem(map, &key);
	for (int i = 0; i < n; i++) {
		double t0 = now();

		bpf_map_update_elem(map, &key, &a, BPF_ANY);
		ins[i] = now() - t0;
		t0 = now();
		bpf_map_delete_elem(map, &key);
		del[i] = now() - t0;
	}
	snprintf(l, sizeof(l), "%s fill", what);
	report(l, callers, ins, n);
	snprintf(l, sizeof(l), "%s empty", what);
	report(l, callers, del, n);
	free(ins);
	free(del);
}

/* swapping a whole inner map in an array of maps, against writing a value of a plain array */
static void swap_inner(void)
{
	int tmpl = bpf_map_create(BPF_MAP_TYPE_HASH, "tmpl", 4, 8, 1024, NULL);
	LIBBPF_OPTS(bpf_map_create_opts, o, .inner_map_fd = tmpl);
	int outer = bpf_map_create(BPF_MAP_TYPE_ARRAY_OF_MAPS, "outer", 4, 4, 4, &o);
	int a = bpf_map_create(BPF_MAP_TYPE_HASH, "in_a", 4, 8, 1024, NULL);
	int b = bpf_map_create(BPF_MAP_TYPE_HASH, "in_b", 4, 8, 1024, NULL);
	int arr = bpf_map_create(BPF_MAP_TYPE_ARRAY, "plain", 4, 8, 4, NULL);
	double *d = calloc(2000, sizeof(*d));
	__u32 zero = 0;

	replace("array of maps: swap inner map", 0, outer, 0, a, b, 2000);
	for (int i = 0; i < 2000; i++) {
		__u64 v = i;
		double t0 = now();

		bpf_map_update_elem(arr, &zero, &v, BPF_ANY);
		d[i] = now() - t0;
	}
	report("plain array: write a value", 0, d, 2000);
	free(d);
}

int main(int argc, char **argv)
{
	struct bpf_object *first, *more[64];
	int jt, t1, t2, caller, cvar, nmore = 0, callers = 1;
	__u32 zero = 0;

	path = argc > 1 ? argv[1] : "poke.bpf.o";
	swap_inner();
	first = load(-1);
	jt = bpf_map__fd(bpf_object__find_map_by_name(first, "jt"));
	t1 = fd_of(first, "t1");
	t2 = fd_of(first, "t2");
	caller = fd_of(first, "caller");
	cvar = fd_of(first, "caller_var");

	/* a prog array that no program names: the plain cost of an fd-array update */
	int spare = bpf_map_create(BPF_MAP_TYPE_PROG_ARRAY, "jt_spare", 4, 4, 4, NULL);
	replace("unused array: replace", 0, spare, 0, t1, t2, 2000);
	fill_empty("unused array:", 0, spare, 0, t1, 200);
	/* slot 1 of the tracked array: the poke list is walked, nothing matches */
	__u32 one = 1;
	replace("tracked array, other slot: replace", 0, jt, one, t1, t2, 2000);

	/* check that the slot change reaches both kinds of caller */
	bpf_map_update_elem(jt, &zero, &t1, BPF_ANY);
	printf("check: slot 0 = t1: caller returns %d, caller_var returns %d\n", retval(caller), retval(cvar));
	bpf_map_update_elem(jt, &zero, &t2, BPF_ANY);
	printf("check: slot 0 = t2: caller returns %d, caller_var returns %d\n", retval(caller), retval(cvar));
	bpf_map_delete_elem(jt, &zero);
	printf("check: slot 0 empty: caller returns %d, caller_var returns %d\n", retval(caller), retval(cvar));

	int steps[] = { 1, 8, 32 };
	for (int s = 0; s < 3; s++) {
		while (callers < steps[s]) {
			more[nmore++] = load(jt);
			callers++;
		}
		replace("direct slot: replace", callers, jt, zero, t1, t2, 400);
		fill_empty("direct slot:", callers, jt, zero, t1, 20);
	}
	bpf_map_update_elem(jt, &zero, &t2, BPF_ANY);
	printf("check: after the runs, slot 0 = t2: caller returns %d, last caller returns %d\n",
	       retval(caller), retval(fd_of(more[nmore - 1], "caller")));
	return 0;
}
