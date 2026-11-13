// SPDX-License-Identifier: GPL-2.0
/* tcp_mini: the smallest TCP congestion control written as struct_ops.
 * Every callback hands the work to the kernel's own Reno code through kfuncs
 * that net/ipv4/bpf_tcp_ca.c offers to tcp_congestion_ops programs.
 * Built with -DNO_SSTHRESH it leaves out a callback the kernel requires.
 * Build: clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I. -c tcp_mini.bpf.c
 */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

extern __u32 tcp_reno_ssthresh(struct sock *sk) __ksym;
extern void tcp_reno_cong_avoid(struct sock *sk, __u32 ack, __u32 acked) __ksym;
extern __u32 tcp_reno_undo_cwnd(struct sock *sk) __ksym;

char _license[] SEC("license") = "GPL";

#ifndef NO_SSTHRESH
SEC("struct_ops")
__u32 BPF_PROG(mini_ssthresh, struct sock *sk)
{
	return tcp_reno_ssthresh(sk);
}
#endif

SEC("struct_ops")
void BPF_PROG(mini_cong_avoid, struct sock *sk, __u32 ack, __u32 acked)
{
	tcp_reno_cong_avoid(sk, ack, acked);
}

SEC("struct_ops")
__u32 BPF_PROG(mini_undo_cwnd, struct sock *sk)
{
	return tcp_reno_undo_cwnd(sk);
}

SEC(".struct_ops.link")
struct tcp_congestion_ops mini = {
#ifndef NO_SSTHRESH
	.ssthresh	= (void *)mini_ssthresh,
#endif
	.cong_avoid	= (void *)mini_cong_avoid,
	.undo_cwnd	= (void *)mini_undo_cwnd,
	.name		= "bpf_mini",
};
