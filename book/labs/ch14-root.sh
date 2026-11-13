#!/bin/bash
# Chapter 14: what the kernel runs on each event, measured on the write path.
# Build on the host (no root):  bash book/labs/ch14-root.sh build      (run `make` in book/program first)
# Then, as root in a throwaway VM:
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- 'bash /tmp/c14/ch14-root.sh'
# Output: /tmp/book-labs/ch14/*.txt
#   event.txt      ns per 1-byte write() to /dev/null with one empty program attached at each hook,
#                  plus the probe lists and the bytes at vfs_write's entry while it is attached
#   event-int3.txt the same for the kprobe at vfs_write+0x9 with kprobe optimization turned off
#   attach.txt     attach and detach times for each hook, 21 rounds
#   tramp-*.bin    the trampolines the JIT wrote for fentry and fexit (disassemble on the host:
#                  objdump -D -b binary -m i386:x86-64 tramp-e_fentry.bin)
#   graph-*.txt    function_graph traces: one fentry attach, one kprobe attach, one write() under the counter
#   misses.txt     the write counter's recursion_misses with two writers on one CPU and on two
#   eilseq.txt     a kprobe in the middle of an instruction
#   stack-*.txt    the kernel stack under the counter's map update at four hooks (step 8)
#   misses-modes.txt  empty programs and the counter, two writers on one CPU, preempt=full and lazy (step 9)
#   graph-deep-*.txt  every function under one fentry attach and one kprobe arm (step 10)
#   lab-misses.txt the run behind lab 14.1: the counter as a tracepoint, kprobe and fentry program (step 11)
# Arguments after the VM command line: none = everything; "part2" = steps 8-11; "lab" = step 11 only.
HERE=$(cd "$(dirname "$0")" && pwd)
W=/tmp/c14
if [ "${1:-}" = build ]; then
  set -e
  mkdir -p $W && cp "$0" $W/ch14-root.sh && cp "$HERE/../program/vmlinux.h" $W/
  cp "$HERE/../program/maps/02-hash-map/hashmap.bpf.o" $W/
  cd $W
  # an empty program at each hook on the write path; e_kpbad points inside the 7-byte `sub` at vfs_write+0x9
  cat > hooks14.bpf.c <<'EOF'
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

SEC("tracepoint/syscalls/sys_enter_write")
int e_tp(void *ctx) { return 0; }

SEC("raw_tp/sys_enter")
int e_rawtp(void *ctx) { return 0; }

SEC("kprobe/vfs_write")
int e_kp(void *ctx) { return 0; }

SEC("kprobe/vfs_write+0x9")
int e_kpoff(void *ctx) { return 0; }

SEC("kprobe/vfs_write+0xc")
int e_kpbad(void *ctx) { return 0; }

SEC("fentry/vfs_write")
int e_fentry(void *ctx) { return 0; }

SEC("fexit/vfs_write")
int e_fexit(void *ctx) { return 0; }

char LICENSE[] SEC("license") = "GPL";
EOF
  # the write counter's body at three more hooks, for the stacks of step 8
  for v in "kp:kprobe/vfs_write" "kpoff:kprobe/vfs_write+0x9" "fe:fentry/vfs_write"; do
    sed -e "s#SEC(\"tracepoint/syscalls/sys_enter_write\")#SEC(\"${v#*:}\")#" \
        -e 's#struct trace_event_raw_sys_enter \*ctx#void *ctx#' -e 's#"../../vmlinux.h"#"vmlinux.h"#' \
        "$HERE/../program/maps/02-hash-map/hashmap.bpf.c" > wc_${v%%:*}.bpf.c
    clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I. -c wc_${v%%:*}.bpf.c -o wc_${v%%:*}.bpf.o
  done
  # question 14.1: the same argument read through two contexts
  cat > ctxoff.bpf.c <<'EOF'
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

__u64 seen;

SEC("kprobe/vfs_write")
int BPF_KPROBE(kp_count, struct file *file, const char *buf, size_t count)
{
	seen = count;
	return 0;
}

SEC("fentry/vfs_write")
int BPF_PROG(fe_count, struct file *file, const char *buf, size_t count)
{
	seen = count;
	return 0;
}

char LICENSE[] SEC("license") = "GPL";
EOF
  cat > bench14.c <<'EOF'
// bench14: one empty program at a time on the write path.
//   bench14 OBJ event PROG...   ns per 1-byte write() to /dev/null with each PROG attached (median of 7 x 1M)
//   bench14 OBJ attach PROG...  attach and detach times, 21 rounds each
//   bench14 OBJ once PROG       attach once, hold one second, detach (for tracing the attach)
//   bench14 OBJ misses PROG...  recursion_misses with two writers on CPU 3, 2,000,000 writes each
#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define REPS 7
#define N 1000000

static long long now(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec * 1000000000LL + t.tv_nsec;
}

static double per_write(int fd, long n)
{
	char c = 'x';
	long long t0 = now();

	for (long i = 0; i < n; i++)
		if (write(fd, &c, 1) != 1)
			exit(1);
	return (double)(now() - t0) / n;
}

static int cmp(const void *a, const void *b)
{
	double x = *(const double *)a, y = *(const double *)b;

	return x < y ? -1 : x > y;
}

static double median(double *v, int n)
{
	qsort(v, n, sizeof(*v), cmp);
	return v[n / 2];
}

static void sh(const char *cmd)
{
	fflush(stdout);
	if (system(cmd) < 0)
		perror("system");
}

static void baseline(int fd, const char *label)
{
	double v[REPS];

	per_write(fd, 200000);
	for (int i = 0; i < REPS; i++)
		v[i] = per_write(fd, N);
	printf("%-10s median %.0f ns/write  [", label, median(v, REPS));
	for (int i = 0; i < REPS; i++)
		printf(" %.0f", v[i]);
	printf(" ]\n");
}

static void event(int fd, struct bpf_program *p)
{
	const char *name = bpf_program__name(p);
	struct bpf_prog_info info = {};
	__u32 len = sizeof(info);
	char cmd[256];
	struct bpf_link *l;

	l = bpf_program__attach(p);
	if (!l) {
		printf("== %s: attach failed\n", name);
		return;
	}
	usleep(500000);	/* the kprobe optimizer waits 5 jiffies, then for an RCU tasks grace period */
	printf("== %s  (%s)\n", name, bpf_program__section_name(p));
	sh("grep -h vfs_write /sys/kernel/debug/kprobes/list /sys/kernel/tracing/enabled_functions");
	sh("python3 /tmp/c14/kcore.py vfs_write 16");
	if (!strncmp(name, "e_kpoff", 7))
		sh("python3 /tmp/c14/kcore.py vfs_write+0x9 8");
	if (!strncmp(name, "e_fe", 4)) {
		snprintf(cmd, sizeof(cmd), "python3 /tmp/c14/kcore.py 'bpf_trampoline_#' 512 /tmp/book-labs/ch14/tramp-%s.bin", name);
		sh(cmd);
	}
	baseline(fd, name);
	sh("sysctl -q -w kernel.bpf_stats_enabled=1");
	per_write(fd, 100000);
	sh("sysctl -q -w kernel.bpf_stats_enabled=0");
	bpf_prog_get_info_by_fd(bpf_program__fd(p), &info, &len);
	printf("   after 100000 writes with stats on: run_cnt %llu run_time_ns %llu recursion_misses %llu\n",
	       (unsigned long long)info.run_cnt, (unsigned long long)info.run_time_ns,
	       (unsigned long long)info.recursion_misses);
	bpf_link__destroy(l);
	usleep(300000);
}

static void misses(struct bpf_program *p)
{
	struct bpf_prog_info info = {};
	__u32 len = sizeof(info);
	struct bpf_link *l = bpf_program__attach(p);

	if (!l)
		return;
	usleep(300000);
	sh("taskset -c 3 /tmp/c14/wloop 2000000 & taskset -c 3 /tmp/c14/wloop 2000000 & wait");
	bpf_prog_get_info_by_fd(bpf_program__fd(p), &info, &len);
	printf("%-10s recursion_misses %8llu of 4000000 writes (%.2f%%)\n", bpf_program__name(p),
	       (unsigned long long)info.recursion_misses, info.recursion_misses / 40000.0);
	bpf_link__destroy(l);
	usleep(300000);
}

static void attach(struct bpf_program *p)
{
	double a[21], d[21];

	for (int r = 0; r < 21; r++) {
		long long t0 = now(), t1, t2;
		struct bpf_link *l = bpf_program__attach(p);

		t1 = now();
		if (!l) {
			printf("%-10s attach failed\n", bpf_program__name(p));
			return;
		}
		bpf_link__destroy(l);
		t2 = now();
		a[r] = (t1 - t0) / 1e3;
		d[r] = (t2 - t1) / 1e3;
		usleep(50000);
	}
	double am = median(a, 21), dm = median(d, 21);	/* sorts a and d */

	printf("%-10s attach median %8.1f us (min %8.1f, max %8.1f)   detach median %8.1f us (min %8.1f, max %8.1f)\n",
	       bpf_program__name(p), am, a[0], a[20], dm, d[0], d[20]);
}

int main(int argc, char **argv)
{
	struct bpf_object *obj;
	struct bpf_program *p;
	int fd = open("/dev/null", O_WRONLY);

	if (argc < 4)
		return 2;
	obj = bpf_object__open_file(argv[1], NULL);
	if (!obj || bpf_object__load(obj))
		return 1;
	if (!strcmp(argv[2], "event")) {
		printf("== nothing attached\n");
		sh("python3 /tmp/c14/kcore.py vfs_write 16; python3 /tmp/c14/kcore.py vfs_write+0x9 8");
		baseline(fd, "none");
	}
	for (int i = 3; i < argc; i++) {
		p = bpf_object__find_program_by_name(obj, argv[i]);
		if (!p)
			continue;
		if (!strcmp(argv[2], "event")) {
			event(fd, p);
		} else if (!strcmp(argv[2], "misses")) {
			misses(p);
		} else if (!strcmp(argv[2], "once")) {
			struct bpf_link *l = bpf_program__attach(p);

			sleep(1);
			bpf_link__destroy(l);
		} else {
			attach(p);
		}
	}
	if (!strcmp(argv[2], "event"))
		baseline(fd, "none");
	bpf_object__close(obj);
	return 0;
}
EOF
  # a writer for the miss experiment and the function_graph trace
  cat > wloop.c <<'EOF'
#include <fcntl.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv)
{
	long n = argc > 1 ? atol(argv[1]) : 1;
	int fd = open("/dev/null", O_WRONLY);

	for (long i = 0; i < n; i++)
		if (write(fd, "x", 1) != 1)
			return 1;
	return 0;
}
EOF
  # libbpf's view of a kprobe that starts inside an instruction
  cat > bad.c <<'EOF'
#include <bpf/libbpf.h>
#include <stdio.h>

int main(void)
{
	struct bpf_object *o = bpf_object__open_file("/tmp/c14/hooks14.bpf.o", NULL);
	struct bpf_link *l;

	bpf_object__load(o);
	l = bpf_program__attach(bpf_object__find_program_by_name(o, "e_kpbad"));
	printf("attach returned %s\n", l ? "a link" : "NULL");
	return 0;
}
EOF
  # read live kernel text through /proc/kcore: kcore.py NAME[+OFF] NBYTES [RAWFILE]; NAME ending in '#' matches any digits
  cat > kcore.py <<'EOF'
import os, struct, sys
spec, n = sys.argv[1], int(sys.argv[2])
name, _, off = spec.partition('+')
off = int(off, 0) if off else 0
addr = None
for line in open('/proc/kallsyms'):
    a, t, s = line.split()[:3]
    if s == name or (name.endswith('#') and s.startswith(name[:-1]) and s[len(name) - 1:].isdigit()):
        addr, name = int(a, 16), s
        break
if addr is None:
    sys.exit('no symbol ' + spec)
addr += off
fd = os.open('/proc/kcore', os.O_RDONLY)
hdr = os.pread(fd, 64, 0)
phoff, = struct.unpack_from('<Q', hdr, 0x20)
phentsize, phnum = struct.unpack_from('<HH', hdr, 0x36)
for i in range(phnum):
    p_type, _, p_off, p_vaddr, _, _, p_memsz, _ = struct.unpack_from('<IIQQQQQQ', os.pread(fd, phentsize, phoff + i * phentsize))
    if p_type == 1 and p_vaddr <= addr < p_vaddr + p_memsz:
        b = os.pread(fd, n, p_off + addr - p_vaddr)
        break
else:
    sys.exit('address not in kcore')
if len(sys.argv) > 3:
    open(sys.argv[3], 'wb').write(b)
    print('%s+0x%x: %d bytes at 0x%x -> %s' % (name, off, n, addr, sys.argv[3]))
else:
    print('%s+0x%x: %s' % (name, off, b.hex(' ')))
EOF
  # sum the values of the counter's map from `bpftool -j map dump`
  cat > msum.py <<'EOF'
import json, sys
t = 0
for e in json.load(sys.stdin):
    v = e.get('formatted', e)['value']
    t += v if isinstance(v, int) else int.from_bytes(bytes(int(x, 16) for x in v), 'little')
print(t)
EOF
  clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I. -c hooks14.bpf.c -o hooks14.bpf.o
  clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I. -c ctxoff.bpf.c -o ctxoff.bpf.o
  gcc -O2 -Wall bench14.c -o bench14 -lbpf
  gcc -O2 -Wall wloop.c -o wloop
  gcc -O2 -Wall bad.c -o bad -lbpf
  llvm-objdump -d --no-show-raw-insn ctxoff.bpf.o > ctxoff.txt
  echo "built in $W"
  exit 0
fi

set -u
ONLY=${1:-all}    # "part2" runs steps 8-11, "lab" only step 11
OUT=/tmp/book-labs/ch14; mkdir -p $OUT; cd $W || exit 1
T=/sys/kernel/tracing
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
mountpoint -q $T || mount -t tracefs tracefs $T
mountpoint -q /sys/kernel/debug || mount -t debugfs debugfs /sys/kernel/debug
{ uname -r; echo "nproc $(nproc)"; echo "preempt: $(cat /sys/kernel/debug/sched/preempt)"
  echo "kprobes-optimization $(cat /proc/sys/debug/kprobes-optimization)"
  grep -m1 'model name' /proc/cpuinfo
} > $OUT/versions.txt 2>&1

if [ "$ONLY" = all ]; then
# 1. per-write cost, and what each hook looks like while it is attached
taskset -c 1 ./bench14 hooks14.bpf.o event e_tp e_rawtp e_kp e_kpoff e_fentry e_fexit > $OUT/event.txt 2>&1
# 2. the same kprobe at vfs_write+0x9, left as a breakpoint
sysctl -q -w debug.kprobes-optimization=0
taskset -c 1 ./bench14 hooks14.bpf.o event e_kpoff > $OUT/event-int3.txt 2>&1
sysctl -q -w debug.kprobes-optimization=1
# 3. attach and detach times
taskset -c 1 ./bench14 hooks14.bpf.o attach e_tp e_rawtp e_kp e_kpoff e_fentry e_fexit > $OUT/attach.txt 2>&1

# 4. one fentry attach and one kprobe attach, traced: the trampoline build and the text patching
echo 0 > $T/tracing_on; echo nop > $T/current_tracer; : > $T/set_ftrace_filter
for f in bpf_tracing_prog_attach bpf_trampoline_link_prog bpf_trampoline_update arch_bpf_trampoline_size \
         bpf_tramp_image_alloc bpf_prog_pack_alloc arch_prepare_bpf_trampoline bpf_arch_text_copy text_poke_copy \
         register_ftrace_direct update_ftrace_direct_add register_ftrace_function ftrace_startup ftrace_shutdown \
         ftrace_modify_all_code ftrace_replace_code arch_ftrace_update_trampoline \
         smp_text_poke_batch_finish smp_text_poke_sync_each_cpu synchronize_rcu_tasks_rude \
         perf_kprobe_init create_local_trace_kprobe register_kprobe arm_kprobe perf_event_attach_bpf_prog \
         bpf_perf_link_attach bpf_link_settle; do
  echo $f >> $T/set_ftrace_filter 2>/dev/null
done
cat $T/set_ftrace_filter > $OUT/graph-attach-filter.txt
echo 1 > $T/options/funcgraph-retval 2>/dev/null
echo function_graph > $T/current_tracer; : > $T/trace; echo 1 > $T/tracing_on
taskset -c 1 ./bench14 hooks14.bpf.o once e_fentry
echo 0 > $T/tracing_on; cat $T/trace > $OUT/graph-attach-fentry.txt
: > $T/trace; echo 1 > $T/tracing_on
taskset -c 1 ./bench14 hooks14.bpf.o once e_kp
echo 0 > $T/tracing_on; cat $T/trace > $OUT/graph-attach-kprobe.txt
echo nop > $T/current_tracer; : > $T/set_ftrace_filter; echo 0 > $T/options/funcgraph-retval 2>/dev/null

# 5. one write() under the write counter, from the syscall work to the program
bpftool prog load hashmap.bpf.o /sys/fs/bpf/wc autoattach
echo trace_syscall_enter > $T/set_graph_function 2>/dev/null || echo perf_syscall_enter > $T/set_graph_function
echo 8 > $T/max_graph_depth
echo function_graph > $T/current_tracer; : > $T/trace
bash -c "echo \$BASHPID > $T/set_ftrace_pid; echo 1 > $T/tracing_on; exec ./wloop 1"
echo 0 > $T/tracing_on
cat $T/trace > $OUT/graph-write.txt
echo nop > $T/current_tracer; : > $T/set_graph_function; echo 0 > $T/max_graph_depth; : > $T/set_ftrace_pid
rm -f /sys/fs/bpf/wc; sleep 1

# 6. recursion misses: the counter runs preemptible, and its recursion counter is per CPU
{
  bpftool prog load hashmap.bpf.o /sys/fs/bpf/wc autoattach
  echo "--- two writers on CPU 3, 3,000,000 writes each"
  taskset -c 3 ./wloop 3000000 & taskset -c 3 ./wloop 3000000 & wait
  bpftool prog show name count_writes | head -2
  echo "map total: $(bpftool -j map dump name write_counts | python3 /tmp/c14/msum.py)"
  rm -f /sys/fs/bpf/wc; sleep 1
  bpftool prog load hashmap.bpf.o /sys/fs/bpf/wc autoattach
  echo "--- two writers on CPUs 2 and 3, 3,000,000 writes each"
  taskset -c 2 ./wloop 3000000 & taskset -c 3 ./wloop 3000000 & wait
  bpftool prog show name count_writes | head -2
  echo "map total: $(bpftool -j map dump name write_counts | python3 /tmp/c14/msum.py)"
  rm -f /sys/fs/bpf/wc
} > $OUT/misses.txt 2>&1

# 7. a kprobe that does not start on an instruction boundary
./bad > $OUT/eilseq.txt 2>&1
fi

if [ "$ONLY" != lab ]; then
# 8. the kernel stack under the counter's map update, with the counter at four hooks
cat > /tmp/c14/stack.bt <<'BT'
fentry:vmlinux:htab_map_update_elem /comm == "wloop"/ { @[kstack] = count(); }
BT
for v in tp kp kpoff-int3 fe; do
  case $v in tp) o=hashmap.bpf.o ;; kpoff-int3) o=wc_kpoff.bpf.o; sysctl -q -w debug.kprobes-optimization=0 ;; *) o=wc_$v.bpf.o ;; esac
  bpftool prog load $o /sys/fs/bpf/wc autoattach
  bpftrace -q /tmp/c14/stack.bt > $OUT/stack-$v.txt 2>&1 &
  BTP=$!; sleep 5; taskset -c 1 ./wloop 1000; sleep 1; kill -INT $BTP; wait $BTP
  rm -f /sys/fs/bpf/wc; sysctl -q -w debug.kprobes-optimization=1; sleep 1
done

# 9. the empty programs and the counter with two writers on one CPU, in each preemption mode
#    (this kernel offers "full" and "lazy"; writing "voluntary" fails and leaves the mode as it was)
for mode in full lazy; do
  echo $mode > /sys/kernel/debug/sched/preempt
  { echo "--- preempt: $(cat /sys/kernel/debug/sched/preempt)"
    taskset -c 1 ./bench14 hooks14.bpf.o misses e_tp e_rawtp e_kp e_kpoff e_fentry
    bpftool prog load hashmap.bpf.o /sys/fs/bpf/wc autoattach
    taskset -c 3 ./wloop 2000000 & taskset -c 3 ./wloop 2000000 & wait
    echo "count_writes $(bpftool prog show name count_writes | grep -o 'recursion_misses [0-9]*') of 4000000 writes"
    rm -f /sys/fs/bpf/wc; sleep 1
  } >> $OUT/misses-modes.txt 2>&1
done
echo full > /sys/kernel/debug/sched/preempt

# 10. where the time of an fentry attach and a kprobe attach goes, every function two levels down
for v in fentry:bpf_trampoline_update kp:arm_kprobe; do
  echo ${v#*:} > $T/set_graph_function; echo 3 > $T/max_graph_depth
  echo function_graph > $T/current_tracer; : > $T/trace; echo 1 > $T/tracing_on
  taskset -c 1 ./bench14 hooks14.bpf.o once e_${v%%:*}
  echo 0 > $T/tracing_on; cat $T/trace > $OUT/graph-deep-${v%%:*}.txt
  echo nop > $T/current_tracer; : > $T/set_graph_function; echo 0 > $T/max_graph_depth
done
fi

# 11. lab 14.1: the write counter at three hooks, two writers on CPU 3, then on CPUs 2 and 3
{
for o in hashmap wc_kp wc_fe; do
  for cpus in "3 3" "2 3"; do
    set -- $cpus
    bpftool prog load $o.bpf.o /sys/fs/bpf/wc autoattach
    taskset -c $1 ./wloop 3000000 & taskset -c $2 ./wloop 3000000 & wait
    echo "$o on CPUs $1,$2: $(bpftool prog show name count_writes | head -1 | grep -o 'recursion_misses [0-9]*' || echo 'recursion_misses 0'), map total $(bpftool -j map dump name write_counts | python3 /tmp/c14/msum.py)"
    rm -f /sys/fs/bpf/wc; sleep 1
  done
done
} > $OUT/lab-misses.txt 2>&1

chmod -R a+r $OUT; echo done > $OUT/done.txt
