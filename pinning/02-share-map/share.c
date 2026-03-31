#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "writer.skel.h"
#include "reader.skel.h"

#define PIN_PATH "/sys/fs/bpf/shared_map"

static volatile sig_atomic_t running = 1;

static void sig_handler(int sig)
{
	running = 0;
}

int main(int argc, char **argv)
{
	struct writer_bpf *writer = NULL;
	struct reader_bpf *reader = NULL;
	int err = 0;

	signal(SIGINT, sig_handler);

	/*
	 * TODO:
	 * 1. Open and load the writer program.
	 * 2. Pin the writer's shared_map to PIN_PATH.
	 * 3. Open the reader program.
	 * 4. Reuse the pinned map for the reader's shared_map using
	 *    bpf_map__set_pin_path() before loading.
	 * 5. Load and attach both programs.
	 * 6. Wait in a loop, then clean up.
	 */

	writer_bpf__destroy(writer);
	reader_bpf__destroy(reader);
	return err != 0;
}
