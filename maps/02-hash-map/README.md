# Exercise: maps/02-hash-map

**Difficulty:** Intermediate

## Exercise Problem

Track the number of `write()` syscalls per PID using a BPF hash map. The userspace
loader iterates the map and prints a table of PID to write count.

## Theory

- `BPF_MAP_TYPE_HASH` is a general-purpose key-value store. Unlike array maps,
  entries are created dynamically via `bpf_map_update_elem()`.
- `bpf_map_lookup_elem()` returns NULL if the key does not exist. You must handle
  this case (e.g., initialize the entry on first access).
- `bpf_map_update_elem()` accepts flags: `BPF_ANY` (create or update),
  `BPF_NOEXIST` (create only), `BPF_EXIST` (update only).
- `max_entries` limits the number of entries. When the map is full,
  `bpf_map_update_elem()` with `BPF_NOEXIST` returns `-E2BIG`.
- From userspace, `bpf_map_get_next_key()` iterates all keys. Passing NULL as
  the current key returns the first key. When no more keys exist, it returns
  `-ENOENT`.

## Tasks

1. In `hashmap.bpf.c`: get the current PID, look up its count in `write_counts`.
   If it exists, increment it. If not, insert a new entry with count 1.
2. In `hashmap.c`: after a brief `sleep()`, iterate all map entries using
   `bpf_map_get_next_key()` and print each PID and its write count.
3. Build: `make maps/02-hash-map`
4. Run the loader and observe the per-PID write counts.

## Expected Results

- The program compiles and runs without errors.
- After a few seconds, the loader prints a table showing which PIDs called
  `write()` and how many times.
- High-write processes (like terminal emulators) show large counts.
