# Exercise: timers_kfuncs/01-timer-basic

**Difficulty:** Intermediate

## Exercise Problem

Arm a BPF timer when a `nanosleep` syscall occurs. The timer callback increments a
counter. The userspace loader reads the counter to verify the timer fired.

## Theory

- `struct bpf_timer` must live inside a BPF map value. It cannot be a standalone
  variable or stack variable.
- Timer lifecycle:
  1. `bpf_timer_init()` — initialize the timer with a map and clock type
     (e.g., `CLOCK_MONOTONIC`).
  2. `bpf_timer_set_callback()` — set the function to call when the timer fires.
  3. `bpf_timer_start()` — start the timer with a delay in nanoseconds and flags.
- The callback signature is:
  `static int callback(void *map, key_type *key, value_type *val)`
- Timers are one-shot by default. To create a periodic timer, call
  `bpf_timer_start()` again from inside the callback.
- The timer callback runs in a softirq context. It has access to the map entry
  it belongs to but has limited helper access.
- `BPF_F_TIMER_ABS` flag makes the timeout absolute; without it, the timeout
  is relative.

## Tasks

1. In `arm_timer()`: look up key 0 in `timer_map`, initialize the timer with
   `bpf_timer_init()`, set the callback, and start it with a 1-second delay.
2. In `timer_callback()`: increment `fire_count` and optionally restart the
   timer for periodic execution.
3. In `timer.c`: read `fire_count` from `timer_map` periodically and print it.
4. Build: `make timers_kfuncs/01-timer-basic`
5. Run the loader, trigger a nanosleep (e.g., `sleep 1` in another terminal),
   and observe the counter incrementing.

## Expected Results

- The program compiles and loads without errors.
- After triggering a nanosleep, the timer fires and `fire_count` increases.
- If made periodic, the counter keeps incrementing at the configured interval.
