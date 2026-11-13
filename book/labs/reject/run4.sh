#!/usr/bin/env bash
cd /tmp/rej-lab
for a in "hashmap.bpf.o 4096 1" "hashmap.bpf.o 64 1" "hashmap.bpf.o 4096 3"; do echo "== $a"; ./logsize $a; done
