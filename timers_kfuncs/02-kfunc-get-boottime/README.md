# Exercise: timers_kfuncs/02-kfunc-get-boottime

**Difficulty:** Intermediate

## Exercise Problem

Use kfuncs (`bpf_task_from_pid` and `bpf_task_release`) to look up a task by PID
from within an eBPF program. Store task information in a map and read it from
userspace.

## Theory

- KFuncs (kernel functions) are a newer mechanism for extending eBPF capabilities.
  Unlike BPF helpers (which have a fixed ABI), kfuncs are regular kernel functions
  exposed to BPF programs.
- To call a kfunc, declare it as an `extern` with the `__ksym` attribute:
  ```c
  extern struct task_struct *bpf_task_from_pid(s32 pid) __ksym;
  extern void bpf_task_release(struct task_struct *p) __ksym;
  ```
- The verifier resolves `__ksym` symbols at load time by looking up the function
  in the kernel's BTF information.
- `bpf_task_from_pid()` is an **acquire** kfunc: it returns a reference-counted
  pointer to a `struct task_struct`. You **must** release it with
  `bpf_task_release()` before the program exits, or the verifier will reject it.
- This acquire/release pattern is a key difference from BPF helpers. KFuncs can
  have richer semantics: returning kernel objects, enforcing ownership rules, etc.
- Available kfuncs depend on the kernel version. Use
  `bpftool btf dump file /sys/kernel/btf/vmlinux | grep "FUNC 'bpf_"` to list them.

## Tasks

1. In `boottime.bpf.c`: get the current PID using `bpf_get_current_pid_tgid()`,
   call `bpf_task_from_pid()` to look up the task, read fields from the returned
   `struct task_struct *` (pid, tgid, comm), store them in `info_map`, and release
   the task with `bpf_task_release()`.
2. In `boottime.c`: read `info_map` index 0 periodically and print the task info.
3. Build: `make timers_kfuncs/02-kfunc-get-boottime`
4. Run the loader and execute commands to trigger execve events.
5. Explore available kfuncs on your kernel:
   ```
   sudo bpftool btf dump file /sys/kernel/btf/vmlinux | grep "FUNC 'bpf_"
   ```

## Expected Results

- The program compiles and loads without errors.
- Each execve looks up the calling task and stores its info.
- The loader prints the PID, TGID, and command name of the last exec'd process.
- Forgetting `bpf_task_release()` causes a verifier error (try it!).
