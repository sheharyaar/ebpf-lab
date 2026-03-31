# Exercise: pinning/01-pin-map

**Difficulty:** Beginner

## Exercise Problem

Pin a BPF map to the BPF filesystem so it persists after the loader process exits.
Verify the map survives using `bpftool`.

## Theory

- BPF objects (maps and programs) are reference-counted. When all file descriptors
  to an object close, it is destroyed.
- Pinning creates a file on the BPF filesystem (`/sys/fs/bpf/`) that holds a
  reference to the object. This keeps it alive independently of any process.
- `bpf_map__pin()` pins a map to a given path. `bpf_map__unpin()` removes the pin.
- From the command line, `bpftool map show` lists all maps (including pinned ones),
  and `bpftool map dump pinned <path>` reads map contents.
- Pinning is the foundation for sharing BPF objects between programs and for
  keeping BPF programs running after the loader exits.

## Tasks

1. In `pin.bpf.c`: implement the counter logic (look up index 0 in `my_counter`
   and increment it atomically).
2. In `pin.c`: pin the map to `/sys/fs/bpf/my_counter` using `bpf_map__pin()`.
3. Build: `make pinning/01-pin-map`
4. Run the loader. It should pin the map and exit.
5. Verify persistence:
   ```
   sudo bpftool map show pinned /sys/fs/bpf/my_counter
   sudo bpftool map dump pinned /sys/fs/bpf/my_counter
   ```
6. Clean up:
   ```
   sudo rm /sys/fs/bpf/my_counter
   ```

## Expected Results

- The loader runs, pins the map, and exits.
- `bpftool map show` confirms the map exists after the loader exits.
- `bpftool map dump` shows the counter value.
- Removing the pinned path destroys the map.
