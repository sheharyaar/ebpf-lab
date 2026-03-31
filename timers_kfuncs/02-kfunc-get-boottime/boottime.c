#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "boottime.skel.h"

static volatile sig_atomic_t running = 1;

static void sig_handler(int sig)
{
	running = 0;
}

int main(int argc, char **argv)
{
	struct boottime_bpf *skel;
	int err;

	signal(SIGINT, sig_handler);

	skel = boottime_bpf__open_and_load();
	if (!skel) {
		fprintf(stderr, "Failed to open and load BPF skeleton\n");
		return 1;
	}

	err = boottime_bpf__attach(skel);
	if (err) {
		fprintf(stderr, "Failed to attach BPF program\n");
		goto cleanup;
	}

	printf("Looking up task info via kfunc on execve. Press Ctrl-C to stop.\n");

	/*
	 * TODO: periodically read info_map index 0 and print the
	 * stored task_info (pid, tgid, comm).
	 */

cleanup:
	boottime_bpf__destroy(skel);
	return err != 0;
}
