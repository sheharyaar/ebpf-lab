#!/usr/bin/env bash
cd /tmp/rej-lab
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
strace -f -e trace=bpf -e abbrev=none -s 0 -o /tmp/rej-lab/strace.txt bpftool prog load null.bpf.o /sys/fs/bpf/rej_null >/dev/null 2>&1
grep -o 'BPF_PROG_LOAD.*' /tmp/rej-lab/strace.txt | grep -o 'log_level=[0-9]*\|log_size=[0-9]*\|= -1 E[A-Z]*' | paste -sd' '
bpftool version | head -1
