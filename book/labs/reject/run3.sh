#!/usr/bin/env bash
bpftool feature probe kernel > /tmp/rej-lab/probe.txt 2>&1
grep -n 'helpers supported for program type tracepoint' /tmp/rej-lab/probe.txt
awk '/helpers supported for program type tracepoint:/{f=1;next} /helpers supported/{f=0} f' /tmp/rej-lab/probe.txt | grep -c 'bpf_'
awk '/helpers supported for program type tracepoint:/{f=1;next} /helpers supported/{f=0} f' /tmp/rej-lab/probe.txt | grep -E 'bpf_redirect$|bpf_map_lookup_elem$'
awk '/helpers supported for program type xdp:/{f=1;next} /helpers supported/{f=0} f' /tmp/rej-lab/probe.txt | grep -E 'bpf_redirect$'
