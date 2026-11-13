/* loglvl OBJ LEVEL: load every program in OBJ at a log level, report log size and time.
 * loglvl btf: time btf__load_vmlinux_btf() and report RSS growth. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <bpf/libbpf.h>
#include <bpf/btf.h>
static long rss_kb(void) { long v = 0; char l[256]; FILE *f = fopen("/proc/self/status", "r");
	while (f && fgets(l, sizeof l, f)) if (!strncmp(l, "VmRSS:", 6)) v = atol(l + 6); if (f) fclose(f); return v; }
static long us(struct timespec a, struct timespec b) { return (b.tv_sec - a.tv_sec) * 1000000L + (b.tv_nsec - a.tv_nsec) / 1000; }
int main(int argc, char **argv)
{
	struct timespec a, b;
	if (argc == 2 && !strcmp(argv[1], "btf")) {
		long r0 = rss_kb();
		clock_gettime(CLOCK_MONOTONIC, &a);
		struct btf *btf = btf__load_vmlinux_btf();
		clock_gettime(CLOCK_MONOTONIC, &b);
		printf("btf__load_vmlinux_btf: %ld us, types=%u, rss +%ld KB\n", us(a, b), btf ? btf__type_cnt(btf) : 0, rss_kb() - r0);
		return 0;
	}
	size_t sz = 64u << 20;
	char *buf = calloc(1, sz);
	struct bpf_object *obj = bpf_object__open_file(argv[1], NULL);
	struct bpf_program *p;
	if (!obj) return 1;
	bpf_object__for_each_program(p, obj) { bpf_program__set_log_level(p, atoi(argv[2])); bpf_program__set_log_buf(p, buf, sz); }
	clock_gettime(CLOCK_MONOTONIC, &a);
	int err = bpf_object__load(obj);
	clock_gettime(CLOCK_MONOTONIC, &b);
	char *vt = strstr(buf, "verification time");
	char line[64] = "-"; if (vt) sscanf(vt, "%63[^\n]", line);
	printf("%s level=%s err=%d log_bytes=%zu load_wall_us=%ld | %s\n", strrchr(argv[1], '/') + 1, argv[2], err, strlen(buf), us(a, b), line);
	return 0;
}
