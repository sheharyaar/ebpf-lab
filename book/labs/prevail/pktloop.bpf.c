// One loop over the first N bytes of a packet, for the PREVAIL chapter: an
// XDP program that adds up bytes. sum_once checks the packet's length once,
// before the loop; sum_each checks it in every round, against the byte it is
// about to read. Only loaded, never attached. Build with -DN=16, 64 or 256.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

#ifndef N
#define N 16
#endif

SEC("xdp")
int sum_once(struct xdp_md *ctx)
{
	unsigned char *data = (void *)(long)ctx->data;
	unsigned char *end = (void *)(long)ctx->data_end;
	unsigned int sum = 0;

	if (data + N > end)
		return XDP_PASS;
#pragma clang loop unroll(disable)
	for (int i = 0; i < N; i++)
		sum += data[i];
	return sum & 1 ? XDP_DROP : XDP_PASS;
}

SEC("xdp")
int sum_each(struct xdp_md *ctx)
{
	unsigned char *data = (void *)(long)ctx->data;
	unsigned char *end = (void *)(long)ctx->data_end;
	unsigned int sum = 0;

#pragma clang loop unroll(disable)
	for (int i = 0; i < N; i++) {
		if (data + i + 1 > end)
			break;
		sum += data[i];
	}
	return sum & 1 ? XDP_DROP : XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
