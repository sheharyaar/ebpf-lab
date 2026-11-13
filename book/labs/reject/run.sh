#!/usr/bin/env bash
cd /tmp/rej-lab
{ uname -r; date -u; nproc; } 
for args in "null.bpf.o 4096 1" "null.bpf.o 256 1" "null.bpf.o 256 9" "loop.bpf.o 65536 1" "loop.bpf.o 65536 9"; do
  echo "=== $args"; ./logsize $args
done
