/* unpriv: what an ordinary user's classic filters do when the JIT will not take them.
 * Attaches a one-instruction classic filter to a socket (SO_ATTACH_FILTER) and installs
 * a one-instruction seccomp filter, and prints each result. Neither needs a capability;
 * the kernel turns both into eBPF and hands them to the JIT. Run it as nobody, once
 * with the default net.core.bpf_jit_limit and once with the limit set to 1. */
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <linux/filter.h>
#include <linux/seccomp.h>

int main(void)
{
	struct sock_filter accept = BPF_STMT(BPF_RET | BPF_K, 0xffffffff);
	struct sock_filter allow = BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW);
	struct sock_fprog sp = { .len = 1, .filter = &accept };
	struct sock_fprog fp = { .len = 1, .filter = &allow };
	int s = socket(AF_INET, SOCK_DGRAM, 0);
	int r = setsockopt(s, SOL_SOCKET, SO_ATTACH_FILTER, &sp, sizeof(sp));

	printf("SO_ATTACH_FILTER: %s", r ? "failed" : "ok");
	if (r)
		printf(", errno %d (%s)", errno, strerror(errno));
	printf("\n");
	prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
	r = prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &fp);
	printf("seccomp filter: %s", r ? "failed" : "ok");
	if (r)
		printf(", errno %d (%s)", errno, strerror(errno));
	printf("\n");
	return 0;
}
