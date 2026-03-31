#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "hashmap.skel.h"

static volatile sig_atomic_t running = 1;

static void sig_handler(int sig)
{
	running = 0;
}

int main(int argc, char **argv)
{
	struct hashmap_bpf *skel;
	int err;

	signal(SIGINT, sig_handler);

	skel = hashmap_bpf__open_and_load();
	if (!skel) {
		fprintf(stderr, "Failed to open and load BPF skeleton\n");
		return 1;
	}

	err = hashmap_bpf__attach(skel);
	if (err) {
		fprintf(stderr, "Failed to attach BPF program\n");
		goto cleanup;
	}

	printf("Tracking per-PID write() counts. Press Ctrl-C to stop.\n");

	/*
	 * TODO: wait for a period, then iterate all entries in write_counts
	 * using bpf_map_get_next_key() and bpf_map_lookup_elem().
	 * Print a table of PID -> count.
	 */

cleanup:
	hashmap_bpf__destroy(skel);
	return err != 0;
}
