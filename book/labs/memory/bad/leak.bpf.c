/* an object allocated and never dropped, linked or stashed */
#include "common.h"

SEC("fentry/vfs_write")
int BPF_PROG(leak)
{
	struct wnode *n = bpf_obj_new(struct wnode);

	if (!n)
		return 0;
	n->tid = bpf_get_current_pid_tgid();
	return 0;			/* n is still ours */
}
