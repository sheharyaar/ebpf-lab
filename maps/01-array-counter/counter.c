#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <bpf/libbpf.h>
#include "counter.skel.h"

static volatile sig_atomic_t running = 1;

static void sig_handler(int sig)
{
	running = 0;
}

int main(int argc, char **argv)
{
	struct counter_bpf *skel;
	int err;

	signal(SIGINT, sig_handler);

	skel = counter_bpf__open_and_load();
	if (!skel) {
		fprintf(stderr, "Failed to open and load BPF skeleton\n");
		return 1;
	}

	err = counter_bpf__attach(skel);
	if (err) {
		fprintf(stderr, "Failed to attach BPF program\n");
		goto cleanup;
	}

	printf("Counting execve calls. Press Ctrl-C to stop.\n");

	/* TODO: periodically read counter_map index 0 and print the value */

cleanup:
	counter_bpf__destroy(skel);
	return err != 0;
}
