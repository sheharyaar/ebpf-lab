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
	__u32 t=0;
	while(running) {
		printf("t=%u\n", t);
		uint32_t prev_key = 0;
		uint32_t key = 0;
		uint64_t val = 0;

		while(bpf_map__get_next_key(skel->maps.write_counts, &prev_key, &key, sizeof(__u32)) == 0) {
			if (bpf_map__lookup_elem(skel->maps.write_counts, 
				&key, sizeof(__u32),
				&val, sizeof(__u64), 0) == 0) {
				printf("%u\t%lu\n", key, val);
			}
		}

		t++;
		sleep(10);
	}

cleanup:
	hashmap_bpf__destroy(skel);
	return err != 0;
}
