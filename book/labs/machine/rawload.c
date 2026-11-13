/* rawload: hand eBPF bytes to the kernel with the bpf() system call, and print what
 * the kernel says about them. No libbpf, no object file: the bytes go in as written.
 *
 *   rawload FILE
 *
 * FILE holds one 8-byte slot per line, as hex bytes in memory order (the order
 * llvm-objdump prints them); a wide instruction takes two lines, and '#' starts a
 * comment. The program is loaded as a socket filter with the log at level 1. If the
 * load succeeds, it is run once on a 64-byte packet of zeros (BPF_PROG_TEST_RUN) and
 * its return value printed. Needs root (or CAP_BPF with unprivileged BPF allowed).
 *
 * Build: gcc -O2 -Wall rawload.c -o rawload
 */
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <linux/bpf.h>

#define MAXSLOTS 4096

static struct bpf_insn prog[MAXSLOTS];
static char log_buf[65536];

static int read_slots(const char *path)
{
	FILE *f = fopen(path, "r");
	char line[512];
	int n = 0;

	if (!f) {
		perror(path);
		exit(2);
	}
	while (fgets(line, sizeof(line), f)) {
		unsigned char b[8];
		char *p = line, *end;
		int k = 0;

		if (strchr(line, '#'))
			*strchr(line, '#') = '\0';
		while (k < 8) {
			unsigned long v = strtoul(p, &end, 16);

			if (end == p)
				break;
			b[k++] = (unsigned char)v;
			p = end;
		}
		if (k == 0)
			continue;
		if (k != 8 || n == MAXSLOTS) {
			fprintf(stderr, "%s: slot %d: want 8 bytes, got %d\n", path, n, k);
			exit(2);
		}
		memcpy(&prog[n++], b, 8);
	}
	fclose(f);
	return n;
}

int main(int argc, char **argv)
{
	union bpf_attr a;
	unsigned char pkt[64] = { 0 };
	int n, fd;

	if (argc != 2) {
		fprintf(stderr, "usage: %s FILE\n", argv[0]);
		return 2;
	}
	n = read_slots(argv[1]);

	memset(&a, 0, sizeof(a));
	a.prog_type = BPF_PROG_TYPE_SOCKET_FILTER;
	a.insns = (unsigned long)prog;
	a.insn_cnt = n;
	a.license = (unsigned long)"GPL";
	a.log_level = 1;
	a.log_buf = (unsigned long)log_buf;
	a.log_size = sizeof(log_buf);
	fd = syscall(__NR_bpf, BPF_PROG_LOAD, &a, sizeof(a));
	printf("%s: %d slots, load %s", argv[1], n, fd < 0 ? "refused" : "ok");
	if (fd < 0)
		printf(", errno %d (%s)", errno, strerror(errno));
	printf("\n%s", log_buf);
	if (fd < 0)
		return 1;

	memset(&a, 0, sizeof(a));
	a.test.prog_fd = fd;
	a.test.data_in = (unsigned long)pkt;
	a.test.data_size_in = sizeof(pkt);
	a.test.repeat = 1;
	if (syscall(__NR_bpf, BPF_PROG_TEST_RUN, &a, sizeof(a)))
		printf("test run failed: errno %d (%s)\n", errno, strerror(errno));
	else
		printf("returned %u (0x%x)\n", a.test.retval, a.test.retval);
	close(fd);
	return 0;
}
