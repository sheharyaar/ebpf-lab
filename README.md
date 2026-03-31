# eBPF Playground

A hands-on playground for learning eBPF concepts using libbpf/CO-RE. Each exercise
provides skeleton code with an accompanying README — read the theory, then implement
the logic yourself.

## Prerequisites

- Linux kernel with BTF support (`/sys/kernel/btf/vmlinux`)
- clang
- bpftool
- libbpf, libelf, zlib (development headers)

## Usage

```sh
# Build a specific exercise (skeleton build, relaxed warnings)
make <exercise>

# Test your implementation (strict warnings, all errors enabled)
make test/<exercise>

# Build everything
make all

# Clean all build artifacts
make clean
```

## Exercises

| # | Exercise | Level | Concepts |
|---|----------|-------|----------|
| 1 | `hello_world/01-hello` | Beginner | `bpf_printk`, tracepoint, minimal eBPF program |
| 2 | `hello_world/02-kprobe` | Beginner | kprobe program type, `BPF_KPROBE` macro, `bpf_get_current_pid_tgid` |
| 3 | `hello_world/03-tracepoint` | Beginner | BTF-typed tracepoint (`tp_btf`), typed `task_struct` args, `BPF_PROG` macro |
| 4 | `maps/01-array-counter` | Beginner | `BPF_MAP_TYPE_ARRAY`, `__sync_fetch_and_add`, skeleton loader |
| 5 | `maps/02-hash-map` | Intermediate | `BPF_MAP_TYPE_HASH`, `bpf_map_lookup_elem`, `bpf_map_update_elem`, map iteration |
| 6 | `maps/03-ringbuf` | Intermediate | `BPF_MAP_TYPE_RINGBUF`, `bpf_ringbuf_reserve`/`submit`, `ring_buffer__poll` |
| 7 | `pinning/01-pin-map` | Beginner | `bpf_map__pin`, BPF filesystem, `bpftool map` |
| 8 | `pinning/02-share-map` | Intermediate | Sharing pinned maps, `bpf_map__set_pin_path`, multi-program loader |
| 9 | `timers_kfuncs/01-timer-basic` | Intermediate | `struct bpf_timer`, `bpf_timer_init`/`set_callback`/`start` |
| 10 | `timers_kfuncs/02-kfunc-get-boottime` | Intermediate | KFuncs, `__ksym`, `bpf_task_from_pid`, acquire/release semantics |
