#!/usr/bin/env bash
cd /tmp/rej-lab
./logsize null.bpf.o 4096 1 full.txt >/dev/null; ./logsize null.bpf.o 256 1 ring.txt >/dev/null; ./logsize null.bpf.o 256 9 fixed.txt >/dev/null
