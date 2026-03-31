#include <stdio.h>
#include <stdlib.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "pin.skel.h"

#define PIN_PATH "/sys/fs/bpf/my_counter"

int main(int argc, char **argv)
{
	struct pin_bpf *skel;
	int err;

	skel = pin_bpf__open_and_load();
	if (!skel) {
		fprintf(stderr, "Failed to open and load BPF skeleton\n");
		return 1;
	}

	err = pin_bpf__attach(skel);
	if (err) {
		fprintf(stderr, "Failed to attach BPF program\n");
		goto cleanup;
	}

	/*
	 * TODO: pin the my_counter map to PIN_PATH using
	 * bpf_map__pin(skel->maps.my_counter, PIN_PATH).
	 * Print a success message and exit.
	 * The map should persist after this process exits.
	 */

cleanup:
	pin_bpf__destroy(skel);
	return err != 0;
}
