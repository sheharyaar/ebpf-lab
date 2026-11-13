// Chapter 15: the write counter with a bpf_spin_lock in its value, at three hooks.
// Build with -DHOOK_TP (the counter's tracepoint), -DHOOK_FE (fentry on vfs_write),
// or -DHOOK_FE -DCALL_INSIDE (a helper call while the lock is held).
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct cval {
	struct bpf_spin_lock lock;
	u64 n;
};

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1024);
	__type(key, u32);
	__type(value, struct cval);
} write_counts SEC(".maps");

#ifdef HOOK_TP
SEC("tracepoint/syscalls/sys_enter_write")
#else
SEC("fentry/vfs_write")
#endif
int count_writes(void *ctx)
{
	u32 pid = bpf_get_current_pid_tgid();
	struct cval zero = {}, *v = bpf_map_lookup_elem(&write_counts, &pid);

	if (!v) {
		bpf_map_update_elem(&write_counts, &pid, &zero, BPF_NOEXIST);
		v = bpf_map_lookup_elem(&write_counts, &pid);
		if (!v)
			return 0;
	}
	bpf_spin_lock(&v->lock);
#ifdef CALL_INSIDE
	v->n += bpf_ktime_get_ns() & 1;
#endif
	v->n++;
	bpf_spin_unlock(&v->lock);
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
