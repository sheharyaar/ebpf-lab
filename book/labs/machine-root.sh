#!/bin/bash
# The machine chapter (src/machine.html): the measurements behind its figures, costs box
# and "When it goes wrong" table, and the root steps of lab 1.2.
# Build on the host (no root), into /tmp/machinelab:
#   bash book/labs/machine-root.sh build
# Then, as root in a throwaway VM:
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- "bash $PWD/book/labs/machine-root.sh"
# Arguments: none = every step; or the step numbers to run, e.g. "2".
# Output: /tmp/book-labs/machine/*.txt
#   1 counter.txt   the write counter loaded but not attached: bpftool prog show, the kernel's
#                   copy of its slots (xlated.txt, xlated-opcodes.txt), its x86 code
#                   (jited-opcodes.txt) and the lengths of the x86 instructions; the JIT switch
#                   and whether the kernel holds an interpreter
#   2 cases.txt     every file in machine/cases loaded with rawload, with the kernel's log
HERE=$(cd "$(dirname "$0")" && pwd)
PROG=$(cd "$HERE/../program" && pwd)
W=/tmp/machinelab
if [ "${1:-}" = build ]; then
	set -e
	mkdir -p $W
	gcc -O2 -Wall "$HERE/machine/rawload.c" -o $W/rawload
	(cd "$PROG" && clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -I/usr/include/bpf -I. \
		-c maps/02-hash-map/hashmap.bpf.c -o $W/hashmap.bpf.o 2>/dev/null)
	llvm-objdump -dr $W/hashmap.bpf.o > $W/objdump.txt
	chmod -R a+rX $W
	echo "built in $W"
	exit 0
fi

OUT=/tmp/book-labs/machine
mkdir -p $OUT
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
P=/sys/fs/bpf
want() { [ $# -eq 0 ] || [ -z "$ARGS" ] || [[ " $ARGS " == *" $1 "* ]]; }
ARGS="$*"

if want 1; then
	rm -f $P/mc
	bpftool prog load $W/hashmap.bpf.o $P/mc
	bpftool prog show pinned $P/mc > $OUT/show.txt
	bpftool prog dump xlated pinned $P/mc > $OUT/xlated.txt
	bpftool prog dump xlated pinned $P/mc opcodes > $OUT/xlated-opcodes.txt
	bpftool prog dump jited pinned $P/mc > $OUT/jited.txt
	bpftool prog dump jited pinned $P/mc opcodes > $OUT/jited-opcodes.txt
	rm -f $P/mc
	{
	echo "## $(uname -r), $(nproc) vCPUs, $(date -u '+%Y-%m-%d %H:%M UTC')"
	cat $OUT/show.txt
	echo "## eBPF slots in the kernel's copy: $(grep -cE '^ *[0-9]+:' $OUT/xlated.txt) instructions"
	echo "## x86 instructions and their lengths"
	python3 -I - $OUT/jited-opcodes.txt <<-'PY'
		import re, sys, collections
		lines = open(sys.argv[1]).read().splitlines()
		ins = []                  # [mnemonic, bytes]; a lock prefix joins the instruction after it
		for i, l in enumerate(lines):
		    m = re.match(r'^\s*[0-9a-f]+:\s+(\S+)', l)
		    if m and i + 1 < len(lines):
		        n = len(lines[i + 1].split())
		        if ins and ins[-1][0] == 'lock':
		            ins[-1] = ['lock ' + m.group(1), ins[-1][1] + n]
		        else:
		            ins.append([m.group(1), n])
		lens = [n for _, n in ins]
		c = collections.Counter(lens)
		print('instructions', len(lens), 'bytes', sum(lens), 'mean %.2f' % (sum(lens) / len(lens)),
		      'min', min(lens), 'max', max(lens))
		print('by length:', ', '.join(f'{k} B: {c[k]}' for k in sorted(c)))
	PY
	echo "## the JIT switch"
	echo "bpf_jit_enable: $(cat /proc/sys/net/core/bpf_jit_enable)"
	echo 0 > /proc/sys/net/core/bpf_jit_enable 2>$W/err.txt; echo "write 0: exit $?, $(cat $W/err.txt)"
	dmesg | grep -i 'bpf_jit_enable is permanently' | tail -1
	echo "interpreter symbols in kallsyms: $(grep -cE ' (___bpf_prog_run|__bpf_prog_run(32|64|512))$' /proc/kallsyms)"
	} > $OUT/counter.txt 2>&1
	cat $OUT/counter.txt
fi

if want 2; then
	for f in "$HERE"/machine/cases/*.txt; do
		echo "=== $(basename $f)"
		$W/rawload "$f" 2>&1 | sed 's/^/  /'
	done > $OUT/cases.txt
	cat $OUT/cases.txt
fi
