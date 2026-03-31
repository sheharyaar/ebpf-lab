#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "timer.skel.h"

static volatile sig_atomic_t running = 1;

static void sig_handler(int sig)
{
	running = 0;
}

int main(int argc, char **argv)
{
	struct timer_bpf *skel;
	int err;

	signal(SIGINT, sig_handler);

	skel = timer_bpf__open_and_load();
	if (!skel) {
		fprintf(stderr, "Failed to open and load BPF skeleton\n");
		return 1;
	}

	err = timer_bpf__attach(skel);
	if (err) {
		fprintf(stderr, "Failed to attach BPF program\n");
		goto cleanup;
	}

	printf("Timer armed on nanosleep. Press Ctrl-C to stop.\n");

	/*
	 * TODO: periodically read timer_map index 0 and print fire_count
	 * to verify the timer callback has executed.
	 */

cleanup:
	timer_bpf__destroy(skel);
	return err != 0;
}
