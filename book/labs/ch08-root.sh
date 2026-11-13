#!/bin/bash
# Chapter 8 lab: count the hooks on this kernel. Needs root for tracefs and debugfs.
# On the host:        sudo bash book/labs/ch08-root.sh
# In a throwaway VM:  vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- "bash $PWD/book/labs/ch08-root.sh"
# Output: /tmp/book-labs/ch08/counts.txt. Reads only; attaches nothing.
set -u
OUT=/tmp/book-labs/ch08; mkdir -p "$OUT"
T=/sys/kernel/tracing
mountpoint -q $T || mount -t tracefs tracefs $T
mountpoint -q /sys/kernel/debug || mount -t debugfs debugfs /sys/kernel/debug
mountpoint -q /sys/kernel/security || mount -t securityfs securityfs /sys/kernel/security
{
  echo "kernel:                         $(uname -r)"
  echo "modules loaded:                 $(tail -n +2 /proc/modules | wc -l)"
  echo "tracepoints (available_events): $(wc -l < $T/available_events)"
  echo "  of them sys_enter_*:          $(grep -c '^syscalls:sys_enter_' $T/available_events)"
  echo "functions ftrace can hook:      $(wc -l < $T/available_filter_functions)"
  echo "functions in vmlinux BTF:       $(bpftool btf dump file /sys/kernel/btf/vmlinux 2>/dev/null | grep -c "^\[[0-9]*\] FUNC '")"
  echo "kprobe blacklist entries:       $(wc -l < /sys/kernel/debug/kprobes/blacklist)"
  echo "active LSMs:                    $(cat /sys/kernel/security/lsm)"
  echo "--- your two hooks"
  grep -x 'syscalls:sys_enter_write' $T/available_events
  grep -w '^do_sys_openat2' $T/available_filter_functions
  grep -w '^vfs_write' $T/available_filter_functions
  echo "--- the write tracepoint's record format"
  sed -n '1,20p' $T/events/syscalls/sys_enter_write/format
} > "$OUT/counts.txt" 2>&1

# the answer to question 8.2: ten failing write() calls, counted at three hooks (needs bpftrace)
W=/tmp/ch08; mkdir -p $W; cd $W
printf '%s\n' '#include <fcntl.h>' '#include <unistd.h>' 'int main(void)' '{' \
  '	int fd = open("/etc/hostname", O_RDONLY);' '	for (int i = 0; i < 10; i++)' \
  '		write(fd, "x", 1);	/* fails: the file is open read-only */' '	return 0;' '}' > rowrite.c
gcc -O2 -o rowrite rowrite.c
cat > hooks.bt <<'BT'
tracepoint:syscalls:sys_enter_write /comm == "rowrite"/ { @tracepoint_sys_enter_write = count(); }
fentry:vmlinux:vfs_write /comm == "rowrite"/ { @fentry_vfs_write = count(); }
fexit:vmlinux:vfs_write /comm == "rowrite"/ { @fexit_vfs_write_returned[retval] = count(); }
fentry:vmlinux:security_file_permission /comm == "rowrite" && args.mask == 2/ { @fentry_security_file_permission_write = count(); }
BT
bpftrace hooks.bt > "$OUT/bpftrace-rowrite.txt" 2>&1 &
BTP=$!; sleep 6; ./rowrite; sleep 1; kill -INT $BTP; wait $BTP
chmod -R a+r "$OUT"; echo "ch08 done: $OUT"
