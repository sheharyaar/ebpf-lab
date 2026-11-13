#include <bpf/libbpf.h>
#include <stdio.h>

int main(void)
{
	struct bpf_object *o = bpf_object__open_file("/tmp/c14/hooks14.bpf.o", NULL);
	struct bpf_link *l;

	bpf_object__load(o);
	l = bpf_program__attach(bpf_object__find_program_by_name(o, "e_kpbad"));
	printf("attach returned %s\\n", l ? "a link" : "NULL");
	return 0;
}
