# Exercise: maps/03-ringbuf

**Difficulty:** Intermediate

## Exercise Problem

Emit an event to userspace every time a process calls `exec`. Use a ring buffer
map to stream events containing the PID and command name.

## Theory

- `BPF_MAP_TYPE_RINGBUF` is a high-performance, single-producer multi-consumer
  buffer for streaming data from kernel to userspace.
- The workflow in the BPF program:
  1. `bpf_ringbuf_reserve()` — reserve space for an event in the ring buffer.
  2. Fill in the event data.
  3. `bpf_ringbuf_submit()` — submit the event to userspace.
  If reservation fails (buffer full), `bpf_ringbuf_reserve()` returns NULL.
- `bpf_get_current_comm()` fills a buffer with the current task's command name.
- From userspace, `ring_buffer__new()` creates a consumer and
  `ring_buffer__poll()` blocks until events are available.
- Ring buffers replace the older `BPF_MAP_TYPE_PERF_EVENT_ARRAY` for most use
  cases. They have better performance and simpler semantics.
- A shared header (`ringbuf.h`) defines the event struct used by both the BPF
  program and the userspace loader.

## Tasks

1. In `ringbuf.bpf.c`: reserve space in the ring buffer, fill in `pid`
   (from `bpf_get_current_pid_tgid()`) and `comm` (from
   `bpf_get_current_comm()`), then submit the event.
2. In `ringbuf.c`: implement the poll loop using `ring_buffer__poll()`.
3. Build: `make maps/03-ringbuf`
4. Run the loader and execute commands in another terminal.

## Expected Results

- The program compiles and runs without errors.
- Each time a process calls exec, the loader prints the PID and command name.
- Pressing Ctrl-C stops the loader cleanly.
