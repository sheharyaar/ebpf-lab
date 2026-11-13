/* splitload: load split.bpf.o (or split_var.bpf.o) and attach count_writes.
 * Usage (root): splitload OBJ hold        attach, print "ready", wait for a line on stdin
 *               splitload OBJ link        attach, pin the link at /sys/fs/bpf/c16_link, exit
 *               splitload OBJ link+maps   the same, and pin write_counts and jmp_table
 *                                          under /sys/fs/bpf/c16_maps/ */
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <bpf/libbpf.h>

int main(int argc, char **argv)
{
	struct bpf_object *obj;
	struct bpf_link *link;
	char line[16];

	if (argc < 3)
		return 2;
	obj = bpf_object__open_file(argv[1], NULL);
	if (!obj || bpf_object__load(obj)) {
		fprintf(stderr, "load failed\n");
		return 1;
	}
	link = bpf_program__attach(bpf_object__find_program_by_name(obj, "count_writes"));
	if (!link) {
		fprintf(stderr, "attach failed\n");
		return 1;
	}
	if (!strcmp(argv[2], "hold")) {
		printf("ready\n");
		fflush(stdout);
		fgets(line, sizeof(line), stdin);
		return 0;
	}
	if (bpf_link__pin(link, "/sys/fs/bpf/c16_link"))
		return 1;
	if (!strcmp(argv[2], "link+maps")) {
		mkdir("/sys/fs/bpf/c16_maps", 0700);
		bpf_map__pin(bpf_object__find_map_by_name(obj, "write_counts"), "/sys/fs/bpf/c16_maps/write_counts");
		bpf_map__pin(bpf_object__find_map_by_name(obj, "jmp_table"), "/sys/fs/bpf/c16_maps/jmp_table");
	}
	printf("pinned; loader exits\n");
	return 0;
}
