# Exercise: maps/01-array-counter

**Difficulty:** Beginner

## Exercise Problem

Count the number of `execve` syscalls using a BPF array map. The eBPF program
increments a counter on each event, and the userspace loader reads and prints
the count.

## Theory

- `BPF_MAP_TYPE_ARRAY` is an array indexed by integer keys (0 to max_entries-1).
  All entries are pre-allocated and zero-initialized.
- Maps are defined using the `SEC(".maps")` section with `__uint()` and `__type()`
  macros to specify map properties.
- `bpf_map_lookup_elem()` returns a pointer to the value for a given key. For
  array maps, lookups always succeed if the key is within bounds.
- To safely increment a shared counter, use `__sync_fetch_and_add()` for atomic
  operations. This is important when multiple CPUs may execute the handler
  concurrently.
- The userspace loader uses the skeleton API (`*_bpf__open_and_load`,
  `*_bpf__attach`) and `bpf_map__fd()` to access the map.

## Tasks

1. In `counter.bpf.c`: look up key 0 in `counter_map` and atomically increment
   the value.
2. In `counter.c`: implement a loop that reads the counter from the map every
   second using `bpf_map_lookup_elem()` (from `<bpf/bpf.h>`) and prints it.
3. Build: `make maps/01-array-counter`
4. Run the loader and trigger execve events in another terminal.

## Expected Results

- The program compiles and the loader runs without errors.
- The counter increases each time a new process is executed.
- Pressing Ctrl-C stops the loader cleanly.
