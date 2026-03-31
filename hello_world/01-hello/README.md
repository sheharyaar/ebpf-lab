# Exercise: hello_world/01-hello

**Difficulty:** Beginner

## Exercise Problem

Write your first eBPF program that prints "Hello, eBPF!" every time a new process is
executed via the `execve` syscall.

## Theory

- eBPF programs are event-driven: they attach to kernel hooks and execute when those
  events fire.
- `SEC("tracepoint/syscalls/sys_enter_execve")` attaches to the `execve` system call
  entry tracepoint.
- `bpf_printk()` is the simplest way to emit output from an eBPF program. It writes to
  the kernel trace pipe at `/sys/kernel/debug/tracing/trace_pipe`.
- Every eBPF program must declare a license (`SEC("license")`). GPL is required for
  most helper functions.

## Tasks

1. Use `bpf_printk()` inside the handler to print "Hello, eBPF!" each time `execve` fires.
2. Build the program: `make hello_world/01-hello`
3. Load and attach the program using `bpftool`:
   ```
   sudo bpftool prog load hello_world/01-hello/hello.bpf.o /sys/fs/bpf/hello
   ```
4. Observe the output:
   ```
   sudo cat /sys/kernel/debug/tracing/trace_pipe
   ```
5. Run some commands in another terminal to trigger `execve` events.
6. Clean up:
   ```
   sudo rm /sys/fs/bpf/hello
   ```

## Expected Results

- The program compiles without errors.
- When loaded and a command is executed (e.g., `ls`), the trace pipe shows
  "Hello, eBPF!" messages with the calling process info.
