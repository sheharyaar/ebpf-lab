# Exercise: pinning/02-share-map

**Difficulty:** Intermediate

## Exercise Problem

Two independent BPF programs share a single hash map via pinning. A writer program
records data on a kprobe, and a reader program accesses the same data on a tracepoint.

## Theory

- Two BPF programs can share the same map by pinning. The first program creates and
  pins the map; the second program opens the pinned map and reuses it.
- `bpf_map__set_pin_path()` tells libbpf to pin (or reuse a pinned) map at a given
  path. Call this before `*_bpf__load()`.
- Both BPF programs must define the map with identical type, key size, value size,
  and max entries. The map definitions must match exactly.
- The loader orchestrates the order: load writer first (creates + pins the map),
  then load reader (reuses the pinned map).
- This pattern is common in production for decoupling data producers from consumers.

## Tasks

1. In `writer.bpf.c`: on each `openat2` call, get the PID and increment its count
   in `shared_map`.
2. In `reader.bpf.c`: on each `execve`, look up the current PID in `shared_map`
   and log the count with `bpf_printk()`.
3. In `share.c`: implement the loader logic:
   - Load the writer and pin its `shared_map`.
   - Set the pin path on the reader's `shared_map` before loading.
   - Attach both programs and wait.
4. Build: `make pinning/02-share-map`
5. Run the loader, observe trace_pipe, and trigger events.
6. Clean up: remove the pinned map from `/sys/fs/bpf/`.

## Expected Results

- Both programs compile and load without errors.
- The writer records per-PID open counts in the shared map.
- The reader can access the same data when exec events fire.
- `bpftool map dump pinned /sys/fs/bpf/shared_map` shows entries from the writer.
