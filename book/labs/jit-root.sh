#!/bin/bash
# The JIT chapter (src/jit.html): the measurements behind its figures, costs box and
# "When it goes wrong" table, and the root steps of its labs.
# Build on the host (no root), into /tmp/jitlab:
#   bash book/labs/jit-root.sh build
# Then, as root in a throwaway VM:
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- "bash $PWD/book/labs/jit-root.sh"
# Arguments: none = every step; or the step numbers to run, e.g. "3 5".
# Output: /tmp/book-labs/jit/*.txt
#   1 switch.txt    the JIT switch, the build options, the interpreter's symbols
#   2 show.txt, xlated.txt, jited.txt, jited-opcodes.txt, kallsyms.txt
#                   the write counter loaded but not attached (lab 7.1)
#   3 time.txt      verification time from the log at level 4, and JIT time and passes from
#                   bpftrace (jit/jit.bt), for the counter and for generated programs (lab 7.2)
#   4 pack.txt      the executable packs in /proc/vmallocinfo and bpf_jit_current, before and
#                   while 1,000 small programs and 20 large ones are loaded
#   5 harden.txt    the counter with net.core.bpf_jit_harden at 0, 1 and 2: slots, bytes,
#                   JIT time, ns per run; harden-*-xlated.txt, harden-*-jited.txt; then
#                   generated programs of 1,000 to 100,000 instructions blinded (about a
#                   minute for the largest, nearly all of it in bpf_jit_blind_constants())
#   6 tail.txt      tail calls with a constant and a computed slot: ns per test run, the
#                   x86 of each, an empty slot (tail-jited-*.txt)
#   7 perf.txt      perf samples landing in the attached counter, and perf annotate
#   8 unpriv.txt    bpf_jit_limit reached: a classic socket filter and a seccomp filter
#                   installed by nobody; bpf_jit_kallsyms=0 and the program's symbol
HERE=$(cd "$(dirname "$0")" && pwd)
PROG=$(cd "$HERE/../program" && pwd)
W=/tmp/jitlab
if [ "${1:-}" = build ]; then
	set -e
	mkdir -p $W
	cp "$PROG/vmlinux.h" $W/
	clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I$W \
		-c "$HERE/jit/tail.bpf.c" -o $W/tail.bpf.o
	gcc -O2 -Wall "$HERE/jit/gen.c" -o $W/gen -lbpf
	gcc -O2 -Wall "$HERE/jit/unpriv.c" -o $W/unpriv
	gcc -O2 -Wall "$HERE/walk/stats.c" -o $W/stats -lbpf
	printf 'abcdefghijklmno' > $W/pkt15   # 15 bytes: skb->len is 1 after the Ethernet header
	chmod -R a+rX $W
	echo "built in $W; the counter is $PROG/maps/02-hash-map/hashmap.bpf.o (make in book/program)"
	exit 0
fi

set -u
OBJ="$PROG/maps/02-hash-map/hashmap.bpf.o"
OUT=${OUT:-/tmp/book-labs/jit}; mkdir -p "$OUT" $W; cd $W || exit 1
STEPS=${*:-1 2 3 4 5 6 7 8}
want() { case " $STEPS " in *" $1 "*) return 0 ;; esac; return 1; }
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
P=/sys/fs/bpf
{ uname -r; bpftool version | head -1; bpftrace --version; perf version; echo "nproc $(nproc)"
  echo "spectre_v2: $(cat /sys/devices/system/cpu/vulnerabilities/spectre_v2)"
  date -u; } > "$OUT/versions.txt" 2>&1

# bpftrace in the background, writing to $1, until stop_trace
start_trace() {
	bpftrace "$HERE/jit/jit.bt" > "$1" 2>&1 & BT=$!
	for _ in $(seq 60); do grep -q Attached "$1" && return; sleep 0.5; done
}
stop_trace() { kill -INT $BT; wait $BT 2>/dev/null; }
# run_time_ns / run_cnt of a program, by name
perrun() {
	bpftool prog show name "$1" | grep -o 'run_time_ns [0-9]* run_cnt [0-9]*' |
		awk '{ printf "%.1f ns a run over %d runs", $2 / $4, $4 }'
}
writes() { dd if=/dev/zero of=/dev/null bs=1 count=$1 status=none; }

if want 1; then
	{
	echo "bpf_jit_enable: $(cat /proc/sys/net/core/bpf_jit_enable)"
	zcat /proc/config.gz 2>/dev/null | grep '^CONFIG_BPF_JIT'
	for v in 0 2; do
		echo "setting $v: $( (echo $v > /proc/sys/net/core/bpf_jit_enable) 2>&1 && echo accepted)"
	done
	echo "interpreter symbols: $(grep -cE ' (___bpf_prog_run|__bpf_prog_run(32|64|512))$' /proc/kallsyms)"
	for s in bpf_jit_harden bpf_jit_kallsyms bpf_jit_limit; do
		echo "$s $(cat /proc/sys/net/core/$s)"
	done
	echo "kernel.unprivileged_bpf_disabled $(cat /proc/sys/kernel/unprivileged_bpf_disabled)"
	} > "$OUT/switch.txt" 2>&1
	cat "$OUT/switch.txt"
fi

if want 2; then
	rm -f $P/jit_c
	bpftool prog load "$OBJ" $P/jit_c
	bpftool prog show pinned $P/jit_c > "$OUT/show.txt"
	bpftool prog dump xlated pinned $P/jit_c > "$OUT/xlated.txt"
	bpftool prog dump xlated pinned $P/jit_c opcodes > "$OUT/xlated-opcodes.txt"
	bpftool prog dump jited pinned $P/jit_c > "$OUT/jited.txt"
	bpftool prog dump jited pinned $P/jit_c opcodes > "$OUT/jited-opcodes.txt"
	grep -E 'bpf_prog_[0-9a-f]+_count_writes' /proc/kallsyms > "$OUT/kallsyms.txt"
	rm -f $P/jit_c
	cat "$OUT/show.txt" "$OUT/kallsyms.txt"
fi

if want 3; then
	start_trace $W/trace3.txt
	{
	echo "## the counter, ten loads through libbpf with the log at level 4"
	for i in $(seq 10); do ./stats "$OBJ" count_writes 4 | grep -E 'load|verification time'; done
	echo "## generated programs, three loads each"
	for k in "alu 1000" "alu 10000" "alu 100000" "alu 500000" "branch 10000" "branch 100000"; do
		for i in 1 2 3; do ./gen $k; done
	done
	} > $W/time-loads.txt 2>&1
	sleep 1; stop_trace
	{ cat $W/time-loads.txt; echo "## bpftrace (jit/jit.bt), in load order"; cat $W/trace3.txt; } > "$OUT/time.txt"
	grep -v '^  pass' "$OUT/time.txt" | tail -40
fi

if want 4; then
	jitcur() { bpftrace -q -e 'BEGIN { printf("%ld", *(int64 *)kaddr("bpf_jit_current")); exit(); }' 2>/dev/null; }
	packs() { grep -E 'bpf_prog_pack|execmem' /proc/vmallocinfo; }
	{
	echo "## before"; packs; echo "bpf_jit_current $(jitcur)"
	{ sleep 8; echo; } | ./gen alu 20 1000 > $W/gen1000.txt &
	sleep 6
	echo "## 1,000 copies of alu 20 loaded"; cat $W/gen1000.txt; packs; echo "bpf_jit_current $(jitcur)"
	wait
	{ sleep 15; echo; } | ./gen alu 50000 20 > $W/gen20.txt &
	sleep 13
	echo "## 20 copies of alu 50000 loaded"; cat $W/gen20.txt; packs; echo "bpf_jit_current $(jitcur)"
	wait
	sleep 1; echo "## after"; packs; echo "bpf_jit_current $(jitcur)"
	} > "$OUT/pack.txt" 2>&1
	cat "$OUT/pack.txt"
fi

if want 5; then
	start_trace $W/trace5.txt
	for hd in 0 1 2; do
		sysctl -q -w net.core.bpf_jit_harden=$hd
		rm -rf $P/jit_h; mkdir $P/jit_h
		bpftool prog load "$OBJ" $P/jit_h/prog autoattach
		bpftool prog dump xlated name count_writes > "$OUT/harden-$hd-xlated.txt"
		bpftool prog dump jited name count_writes > "$OUT/harden-$hd-jited.txt"
		sysctl -q -w kernel.bpf_stats_enabled=1
		writes 1000000
		echo "harden $hd: $(bpftool prog show name count_writes | grep -o 'xlated [0-9]*B  jited [0-9]*B'), $(perrun count_writes)"
		sysctl -q -w kernel.bpf_stats_enabled=0
		rm -rf $P/jit_h; sleep 1
		./gen alu 100000 | sed "s/^/harden $hd: /"
	done > $W/harden-loads.txt 2>&1
	sysctl -q -w net.core.bpf_jit_harden=2      # blinding time against program size
	for n in 1000 10000 30000; do ./gen alu $n | sed "s/^/harden 2: /"; done >> $W/harden-loads.txt 2>&1
	sysctl -q -w net.core.bpf_jit_harden=0
	sleep 1; stop_trace
	{ cat $W/harden-loads.txt; echo "## bpftrace, in load order"; cat $W/trace5.txt; } > "$OUT/harden.txt"
	grep -v '^  pass' "$OUT/harden.txt"
fi

if want 6; then
	run() { bpftool prog run pinned $1 data_in $W/pkt15 repeat ${2:-20000000} 2>&1 | grep -o 'Return value.*'; }
	rm -rf $P/jit_t $P/jit_tm; mkdir -p $P/jit_t $P/jit_tm
	bpftool prog loadall tail.bpf.o $P/jit_t pinmaps $P/jit_tm
	{
	echo "## slot 0 empty"
	for v in direct indirect; do echo "$v: $(run $P/jit_t/$v)"; done
	for v in direct indirect; do bpftool prog dump jited pinned $P/jit_t/$v > "$OUT/tail-jited-$v-empty.txt"; done
	bpftool map update pinned $P/jit_tm/jmp key 0 0 0 0 value pinned $P/jit_t/target
	echo "## slot 0 holds target"
	for i in 1 2 3; do for v in target direct indirect; do echo "$v: $(run $P/jit_t/$v)"; done; done
	for v in direct indirect; do bpftool prog dump jited pinned $P/jit_t/$v > "$OUT/tail-jited-$v.txt"; done
	bpftool prog show pinned $P/jit_t/direct; bpftool prog show pinned $P/jit_t/indirect
	} > "$OUT/tail.txt" 2>&1
	rm -rf $P/jit_t $P/jit_tm
	cat "$OUT/tail.txt"
fi

if want 7; then
	rm -rf $P/jit_p; mkdir $P/jit_p
	bpftool prog load "$OBJ" $P/jit_p/prog autoattach
	SYM=$(grep -oE 'bpf_prog_[0-9a-f]+_count_writes' /proc/kallsyms | head -1)
	{
	echo "symbol $SYM"
	perf record -q -e cpu-clock -o $W/perf.data -- dd if=/dev/zero of=/dev/null bs=1 count=500000 status=none
	perf report -f -i $W/perf.data --stdio --sort sym 2>/dev/null | grep -v '^#' | grep . | head -20
	perf report -f -i $W/perf.data --stdio --sort sym 2>/dev/null | grep -E 'Samples|bpf_prog'
	echo "## perf annotate"
	perf annotate -f -i $W/perf.data --stdio -s "$SYM" 2>&1 | head -80
	} > "$OUT/perf.txt" 2>&1
	rm -rf $P/jit_p
	head -30 "$OUT/perf.txt"
fi

if want 8; then
	NB="setpriv --reuid=nobody --regid=nobody --clear-groups --inh-caps=-all"
	{
	L=$(cat /proc/sys/net/core/bpf_jit_limit)
	echo "## as nobody, bpf_jit_limit $L"; $NB ./unpriv
	sysctl -q -w net.core.bpf_jit_limit=1
	echo "## as nobody, bpf_jit_limit 1"; $NB ./unpriv
	echo "## as root, bpf_jit_limit 1"; ./unpriv
	sysctl -q -w net.core.bpf_jit_limit=$L
	echo "## bpf_jit_kallsyms 0"
	sysctl -q -w net.core.bpf_jit_kallsyms=0
	rm -f $P/jit_k; bpftool prog load "$OBJ" $P/jit_k
	echo "count_writes symbols in kallsyms: $(grep -cE 'bpf_prog_[0-9a-f]+_count_writes' /proc/kallsyms)"
	bpftool prog dump jited pinned $P/jit_k | head -3
	rm -f $P/jit_k
	sysctl -q -w net.core.bpf_jit_kallsyms=1
	rm -f $P/jit_k; bpftool prog load "$OBJ" $P/jit_k
	echo "after setting it back to 1, a new load: $(grep -cE 'bpf_prog_[0-9a-f]+_count_writes' /proc/kallsyms)"
	rm -f $P/jit_k
	} > "$OUT/unpriv.txt" 2>&1
	cat "$OUT/unpriv.txt"
fi
