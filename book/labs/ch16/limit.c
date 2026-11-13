/* limit: load limit.bpf.o for this process only, make one getppid() call, print the runs.
 * Usage (root): limit limit.bpf.o */
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>

int main(int argc, char **argv)
{
	struct bpf_object *obj = bpf_object__open_file(argc > 1 ? argv[1] : "limit.bpf.o", NULL);
	struct bpf_map *ro, *bss;
	unsigned long long buf[2] = { 0 };
	size_t sz;
	__u32 zero = 0, *pid;

	if (!obj)
		return 1;
	ro = bpf_object__find_map_by_name(obj, "limit.rodata");
	pid = bpf_map__initial_value(ro, &sz);
	*pid = getpid();
	if (bpf_object__load(obj) ||
	    !bpf_program__attach(bpf_object__find_program_by_name(obj, "again"))) {
		fprintf(stderr, "load or attach failed\n");
		return 1;
	}
	syscall(SYS_getppid);
	bss = bpf_object__find_map_by_name(obj, "limit.bss");
	bpf_map_lookup_elem(bpf_map__fd(bss), &zero, buf);
	printf("one getppid() call: the program ran %llu times\n", buf[0]);
	return 0;
}
