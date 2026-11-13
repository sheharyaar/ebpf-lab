// A bpf_printk() left in an XDP program. XDP needs CAP_BPF and CAP_NET_ADMIN to load, and bpf_trace_printk()
// sits behind CAP_PERFMON in bpf_base_func_proto() (kernel/bpf/helpers.c, line 2192): book/labs/calls-root.sh,
// step 6, loads it once as root and once with CAP_PERFMON and CAP_SYS_ADMIN dropped (CAP_SYS_ADMIN stands in for it).
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

SEC("xdp")
int xdp_pass(struct xdp_md *ctx)
{
	bpf_printk("packet on ifindex %u", ctx->ingress_ifindex);
	return XDP_PASS;
}
char LICENSE[] SEC("license") = "GPL";
