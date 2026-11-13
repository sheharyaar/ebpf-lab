#!/usr/bin/env bash
cd /tmp/rej-lab
for i in 1 2 3; do for lv in 1 9; do ./logsize loop.bpf.o 65536 $lv | head -1; done; done
