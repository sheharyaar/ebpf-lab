#!/bin/bash
# Chapter "Maps: layout, choosing, sharing": the check behind the full-hash row of its "When it goes wrong" table.
# The chapter's other numbers come from labs/ch09-root.sh, labs/costs2-root.sh (with costs-mapread.c),
# labs/ch15-root.sh and steps 2, 3 and 6 of labs/ch16-root.sh, which stay as they are.
# Run as root in a throwaway VM:
#   vng -r /boot/vmlinuz-linux --user root --rwdir /tmp -- "bash $PWD/book/labs/maps-root.sh"
# Output: /tmp/book-labs/maps/full.txt
# Recorded 12 November 2026, kernel 7.2.15 VM with 16 CPUs: keys 1 to 4 update with exit 0, key 5 prints
# "Error: update failed: Argument list too long" (-E2BIG from alloc_htab_elem()), key 2 again updates with exit 0,
# memlock 2368B, 4 keys in the dump.
set -u
OUT=/tmp/book-labs/maps; mkdir -p "$OUT"
mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf
P=/sys/fs/bpf/maps_full4
{
  uname -r; echo "possible CPUs: $(cat /sys/devices/system/cpu/possible)"
  echo "## a preallocated hash of 4 entries, filled from user space"
  rm -f $P
  bpftool map create $P type hash key 4 value 8 entries 4 name full4
  for k in 1 2 3 4 5; do
    echo "update new key $k:"; bpftool map update pinned $P key $k 0 0 0 value 1 0 0 0 0 0 0 0 2>&1; echo "exit $?"
  done
  echo "update existing key 2:"; bpftool map update pinned $P key 2 0 0 0 value 9 0 0 0 0 0 0 0 2>&1; echo "exit $?"
  bpftool map show pinned $P
  echo "keys in dump: $(bpftool map dump pinned $P | grep -c key)"
  rm -f $P
} 2>&1 | tee "$OUT/full.txt"
