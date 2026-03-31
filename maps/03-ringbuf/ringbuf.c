#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <bpf/libbpf.h>
#include "ringbuf.skel.h"
#include "ringbuf.h"

static volatile sig_atomic_t running = 1;

static void sig_handler(int sig)
{
	running = 0;
}

static int handle_event(void *ctx, void *data, size_t data_sz)
{
	struct event *e = data;

	printf("pid=%-6d comm=%s\n", e->pid, e->comm);
	return 0;
}

int main(int argc, char **argv)
{
	struct ringbuf_bpf *skel;
	struct ring_buffer *rb = NULL;
	int err;

	signal(SIGINT, sig_handler);

	skel = ringbuf_bpf__open_and_load();
	if (!skel) {
		fprintf(stderr, "Failed to open and load BPF skeleton\n");
		return 1;
	}

	err = ringbuf_bpf__attach(skel);
	if (err) {
		fprintf(stderr, "Failed to attach BPF program\n");
		goto cleanup;
	}

	rb = ring_buffer__new(bpf_map__fd(skel->maps.events),
			      handle_event, NULL, NULL);
	if (!rb) {
		fprintf(stderr, "Failed to create ring buffer\n");
		err = 1;
		goto cleanup;
	}

	printf("Listening for exec events. Press Ctrl-C to stop.\n");

	/*
	 * TODO: poll the ring buffer in a loop using ring_buffer__poll()
	 * while running is true.
	 */

cleanup:
	ring_buffer__free(rb);
	ringbuf_bpf__destroy(skel);
	return err != 0;
}
