/* a kernel pointer stored into the arena, loaded back and followed */
#include "arena.h"

struct ent { struct task_struct *task; };
struct ent __arena slot;
int pid;

SEC("fentry/vfs_write")
int BPF_PROG(arenakptr)
{
	slot.task = bpf_get_current_task_btf();	/* the store is accepted */
	asm volatile("" ::: "memory");		/* load it back from the arena */
	pid = slot.task->pid;			/* what comes back is a number */
	return 0;
}
