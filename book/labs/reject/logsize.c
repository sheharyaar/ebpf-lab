/* logsize OBJ SIZE LEVEL: load OBJ with a caller-set log buffer of SIZE bytes at LEVEL
 * (1 = rotating, the default; 9 = 1 | BPF_LOG_FIXED); print the result, the log's length,
 * its first line and its last three lines. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <bpf/libbpf.h>
static int quiet(enum libbpf_print_level l, const char *f, va_list a) { return 0; }
int main(int argc, char **argv)
{
	size_t sz = strtoul(argv[2], NULL, 0); unsigned lvl = atoi(argv[3]);
	char *buf = calloc(1, sz); struct timespec a, b;
	libbpf_set_print(quiet);
	struct bpf_object *obj = bpf_object__open_file(argv[1], NULL);
	struct bpf_program *p;
	bpf_object__for_each_program(p, obj) { bpf_program__set_log_buf(p, buf, sz); bpf_program__set_log_level(p, lvl); }
	clock_gettime(CLOCK_MONOTONIC, &a);
	int err = bpf_object__load(obj);
	clock_gettime(CLOCK_MONOTONIC, &b);
	size_t n = strlen(buf);
	printf("size=%zu level=%u load=%d (%s) log=%zu bytes %.2f s\n", sz, lvl, err, strerror(-err), n,
	       (b.tv_sec - a.tv_sec) + (b.tv_nsec - a.tv_nsec) / 1e9);
	char *nl = strchr(buf, '\n'); printf("first: %.*s\n", nl ? (int)(nl - buf) : (int)n, buf);
	int k = 0; char *e = buf + n; while (e > buf && k < 4) { e--; if (*e == '\n') k++; }
	printf("last:\n%s\n", e);
	if (argc > 4) { FILE *f = fopen(argv[4], "w"); fwrite(buf, 1, n, f); fclose(f); }
	return 0;
}
