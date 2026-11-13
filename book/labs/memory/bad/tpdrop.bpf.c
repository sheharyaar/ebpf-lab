/* a node allocated and dropped at the counter's original hook, the write tracepoint */
#include "common.h"

SEC("tracepoint/syscalls/sys_enter_write")
int tpdrop(void *ctx)
{
	struct wnode *n = bpf_obj_new(struct wnode);	/* allowed here */

	if (n)
		bpf_obj_drop(n);			/* refused: n holds a bpf_rb_node */
	return 0;
}
