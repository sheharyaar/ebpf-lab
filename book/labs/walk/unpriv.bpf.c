// Socket filters for the walk chapter's unprivileged loads (no maps, so that a loader
// without capabilities can load them once kernel.unprivileged_bpf_disabled is 0).
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

/* a bounded loop: accepted for CAP_BPF, refused at the shape check without it */
SEC("socket")
int ubackedge(struct __sk_buff *skb)
{
	u32 n = skb->len, h = 0;

#pragma clang loop unroll(disable)
	for (int i = 0; i < 16; i++)
		h = h * 31 + (n >> i);
	return h & 1;
}

/* no loop, twelve tests of the packet length (eleven branches once clang is done), each
 * path ending in a copy whose size is the sum of the tests taken, so that no path can
 * stand in for another */
#define B(k) if (n & (1u << k)) x += 2 * k + 3;
SEC("socket")
int upaths(struct __sk_buff *skb)
{
	u32 n = skb->len, x = 0;
	char arr[176];

	B(0) B(1) B(2) B(3) B(4) B(5) B(6) B(7) B(8) B(9) B(10) B(11)
	return bpf_skb_load_bytes(skb, 0, arr, x + 1);
}

char LICENSE[] SEC("license") = "GPL";
