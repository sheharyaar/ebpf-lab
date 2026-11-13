/* a helper asked to write into arena memory */
#include "arena.h"

char __arena comm[16];

SEC("fentry/vfs_write")
int BPF_PROG(arenahelper)
{
	char __arena *p = comm;

	bpf_get_current_comm((void *)p, 16);	/* wants stack or map memory */
	return 0;
}
