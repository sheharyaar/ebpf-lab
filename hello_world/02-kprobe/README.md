# Exercise: hello_world/02-kprobe

**Difficulty:** Beginner

## Exercise Problem

Attach an eBPF program to the kernel function `do_sys_openat2` using a kprobe.
Log the PID of each process that opens a file.

## Theory

- Kprobes let you attach eBPF programs to almost any kernel function, not just
  predefined tracepoints.
- `SEC("kprobe/<function>")` specifies which kernel function to probe.
- The `BPF_KPROBE` macro simplifies accessing function arguments through the
  `struct pt_regs` context. Without it, you would use `PT_REGS_PARM1(ctx)`, etc.
- `bpf_get_current_pid_tgid()` returns the current task's PID and TGID packed
  into a `u64`. The lower 32 bits are the kernel PID (thread ID), the upper 32
  bits are the TGID (userspace PID).
- Kprobes are **not part** of the **kernel's stable ABI**. Function signatures and names
  can change between kernel versions. This is a key trade-off vs tracepoints.

## Tasks

1. Use `bpf_get_current_pid_tgid()` to obtain the PID of the calling process. The returned value contains both `pid` and `tgid` of the process, so check the function definition comments to see the format of the returned value.
2. Use `bpf_printk()` to log the PID each time `do_sys_openat2` is called.
3. Build: `make hello_world/02-kprobe`
4. Load with `bpftool` and observe output in `trace_pipe`.
5. Compare the attach behavior with the tracepoint from exercise 01.

## Expected Results

- The program compiles without errors.
- When loaded, every file open operation produces a trace line with the PID.
- Opening files in another terminal (e.g., `cat /etc/hostname`) generates events.
