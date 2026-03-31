# Exercise: hello_world/03-tracepoint

**Difficulty:** Beginner

## Exercise Problem

Use a BTF-enabled tracepoint to trace process forks. Log the parent and child PID
with type-safe access to `struct task_struct` arguments.

## Theory

- `SEC("tp_btf/<tracepoint>")` attaches to a tracepoint with BTF (BPF Type Format)
  type information. This gives you direct, typed access to tracepoint arguments.
- Unlike raw tracepoints (`SEC("tracepoint/...")`), BTF tracepoints provide arguments
  as proper kernel structs (e.g., `struct task_struct *`) instead of raw `u64` arrays.
- The `BPF_PROG` macro declares the function with typed parameters matching the
  tracepoint signature.
- `sched_process_fork` fires whenever a process calls `fork()`. Its arguments are
  the parent and child `task_struct` pointers.
- With BTF, you can read struct fields directly (e.g., `parent->pid`) without manual
  offset calculations or `bpf_probe_read()`.

## Tasks

1. Read `parent->pid` and `child->pid` from the tracepoint arguments.
2. Use `bpf_printk()` to log both PIDs on each fork event.
3. Build: `make hello_world/03-tracepoint`
4. Load with `bpftool` and observe `trace_pipe`.
5. Trigger fork events by running commands in another terminal.

## Expected Results

- The program compiles without errors.
- When loaded, each fork produces a trace message showing parent PID and child PID.
- Running any command (which forks a new process) generates events.
