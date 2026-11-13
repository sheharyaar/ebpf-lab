/* gen KIND N [COPIES]: build a socket filter of about N instructions in memory, load it
 * COPIES times (default 1) with the verifier's log at level 4, and print for the first
 * copy the slots after the kernel's rewrites, the bytes of x86, and the verification
 * time from the log's statistics line. The program does nothing useful; it exists so
 * that the JIT has a known number of instructions to translate.
 *   KIND alu     r0 = 0, then N times r0 += K (K a 32-bit constant), then exit
 *   KIND branch  r0 = 0, then N/2 times { if r0 == K goto +1; r0 += K }, then exit
 * With COPIES > 1 the copies stay loaded until the process gets a newline on stdin,
 * so that a script can look at the memory they take. Needs CAP_BPF (root in the VM). */
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <linux/bpf.h>
#include <bpf/bpf.h>

static struct bpf_insn ins(__u8 code, __u8 dst, __u8 src, __s16 off, __s32 imm)
{
	struct bpf_insn i = { .code = code, .dst_reg = dst, .src_reg = src,
			      .off = off, .imm = imm };
	return i;
}

int main(int argc, char **argv)
{
	if (argc < 3) {
		fprintf(stderr, "usage: gen alu|branch N [COPIES]\n");
		return 2;
	}
	int branch = !strcmp(argv[1], "branch");
	long n = atol(argv[2]), copies = argc > 3 ? atol(argv[3]) : 1, len = 0;
	struct bpf_insn *p = calloc(n + 4, sizeof(*p));
	size_t logsz = 1 << 20;
	char *log = calloc(1, logsz);

	p[len++] = ins(BPF_ALU64 | BPF_MOV | BPF_K, BPF_REG_0, 0, 0, 0);
	for (long i = 0; len < n + 1; i++) {
		__s32 k = (__s32)((i * 2654435761u) & 0x7fffffff);

		if (branch)
			p[len++] = ins(BPF_JMP | BPF_JEQ | BPF_K, BPF_REG_0, 0, 1, k);
		p[len++] = ins(BPF_ALU64 | BPF_ADD | BPF_K, BPF_REG_0, 0, 0, k);
	}
	p[len++] = ins(BPF_JMP | BPF_EXIT, 0, 0, 0, 0);

	int *fds = calloc(copies, sizeof(int));
	for (long c = 0; c < copies; c++) {
		LIBBPF_OPTS(bpf_prog_load_opts, o, .log_level = c ? 0 : 4,
			    .log_buf = c ? NULL : log, .log_size = c ? 0 : logsz);
		fds[c] = bpf_prog_load(BPF_PROG_TYPE_SOCKET_FILTER, "gen", "GPL",
				       p, len, &o);
		if (fds[c] < 0) {
			printf("%s %ld: copy %ld failed: %s (%d)\n", argv[1], n, c,
			       strerror(errno), errno);
			return 1;
		}
	}
	struct bpf_prog_info info = {};
	__u32 il = sizeof(info);
	bpf_prog_get_info_by_fd(fds[0], &info, &il);
	char *t = strstr(log, "verification time");
	long us = t ? atol(t + strlen("verification time")) : -1;
	printf("%s %ld: %ld slots in, %u slots xlated, %u bytes jited, verified in %ld us, id %u\n",
	       argv[1], n, len, info.xlated_prog_len / 8, info.jited_prog_len, us, info.id);
	if (copies > 1) {
		printf("%ld copies loaded; newline to free them\n", copies);
		fflush(stdout);
		getchar();
	}
	return 0;
}
