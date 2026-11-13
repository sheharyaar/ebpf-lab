/* an arena pointer from a global, in a program that never names the arena */
#include "arena.h"

void __arena *saved;

SEC("fentry/vfs_write")
int BPF_PROG(noarena)
{
	int __arena *p = saved;

	return p ? *p : 0;
}
