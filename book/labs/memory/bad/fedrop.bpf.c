/* the same drop at fentry, where the counter now runs */
#include "common.h"

SEC("fentry/vfs_write")
int BPF_PROG(fedrop)
{
	struct wnode *n = bpf_obj_new(struct wnode);

	if (n)
		bpf_obj_drop(n);
	return 0;
}
