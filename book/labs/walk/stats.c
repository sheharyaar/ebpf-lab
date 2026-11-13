/* stats OBJ PROG LEVEL [LOGFILE]: load one program of OBJ, the others left out, with the
 * verifier's log at LEVEL (4 = statistics only, 6 = every state and statistics) in a
 * 512 MB buffer of our own, so that libbpf neither retries nor doubles its buffer.
 * Prints the result, the wall time of the load, verified_insns from the kernel's
 * program info, and the log's lines that are not the walk itself; the whole log goes
 * to LOGFILE if one is named. Nothing is pinned or attached; the program is freed
 * when this process exits. */
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>

static int quiet(enum libbpf_print_level l, const char *f, va_list a) { return 0; }

int main(int argc, char **argv)
{
	if (argc < 4) { fprintf(stderr, "usage: stats OBJ PROG LEVEL [LOGFILE]\n"); return 2; }
	size_t sz = 512u << 20; unsigned lvl = atoi(argv[3]);
	char *buf = calloc(1, sz); struct timespec a, b; struct bpf_program *p, *me = NULL;
	libbpf_set_print(quiet);
	struct bpf_object *obj = bpf_object__open_file(argv[1], NULL);
	if (!obj) { perror("open"); return 1; }
	bpf_object__for_each_program(p, obj) {
		int mine = !strcmp(bpf_program__name(p), argv[2]);
		bpf_program__set_autoload(p, mine);
		if (mine) { me = p; bpf_program__set_log_buf(p, buf, sz); bpf_program__set_log_level(p, lvl); }
	}
	if (!me) { fprintf(stderr, "no program %s in %s\n", argv[2], argv[1]); return 1; }
	clock_gettime(CLOCK_MONOTONIC, &a);
	int err = bpf_object__load(obj);
	clock_gettime(CLOCK_MONOTONIC, &b);
	printf("%s: load %s (%d) in %.1f ms, log %zu bytes\n", argv[2], err ? strerror(-err) : "ok", err,
	       ((b.tv_sec - a.tv_sec) * 1e9 + (b.tv_nsec - a.tv_nsec)) / 1e6, strlen(buf));
	if (!err) {
		struct bpf_prog_info info = {}; __u32 len = sizeof(info);
		if (!bpf_prog_get_info_by_fd(bpf_program__fd(me), &info, &len))
			printf("verified_insns %u (bpf_prog_info)\n", info.verified_insns);
		char path[64], line[128]; snprintf(path, sizeof(path), "/proc/self/fdinfo/%d", bpf_program__fd(me));
		FILE *fi = fopen(path, "r");
		while (fi && fgets(line, sizeof(line), fi))
			if (!strncmp(line, "verified_insns", 14) || !strncmp(line, "prog_type", 9)) printf("fdinfo %s", line);
		if (fi) fclose(fi);
	}
	/* the lines that are not the walk: anything that does not start with a slot number,
	 * "from N to M", a register dump or a source line */
	for (char *l = strtok(buf, "\n"); l; l = strtok(NULL, "\n")) {
		if ((l[0] >= '0' && l[0] <= '9') || !strncmp(l, "from ", 5) || l[0] == ';' || l[0] == ' ')
			continue;
		printf("  %s\n", l);
	}
	if (argc > 4) {      /* buf was cut up by strtok: reload is cheaper than copying 512 MB */
		FILE *f = fopen(argv[4], "w");
		bpf_object__close(obj);
		obj = bpf_object__open_file(argv[1], NULL); memset(buf, 0, sz);
		bpf_object__for_each_program(p, obj) {
			int mine = !strcmp(bpf_program__name(p), argv[2]);
			bpf_program__set_autoload(p, mine);
			if (mine) { bpf_program__set_log_buf(p, buf, sz); bpf_program__set_log_level(p, lvl); }
		}
		bpf_object__load(obj);
		fwrite(buf, 1, strlen(buf), f); fclose(f);
	}
	return 0;
}
