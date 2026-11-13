# The book's spine program (your write counter) and the two hook examples,
# copied verbatim from the playground's `solutions` branch (commit 0314b86) on 2026-11-12.
# Run from this folder:  make        -> vmlinux.h, the object, the skeleton and the loader
CLANG   ?= clang
BPFTOOL ?= bpftool
ARCH    := $(shell uname -m | sed 's/x86_64/x86/;s/aarch64/arm64/')
BPF_CFLAGS := -g -O2 -target bpf -D__TARGET_ARCH_$(ARCH) -I/usr/include/bpf -I.
HM := maps/02-hash-map

all: $(HM)/hashmap hello_world/02-kprobe/kprobe.bpf.o hello_world/03-tracepoint/tracepoint.bpf.o

vmlinux.h:
	$(BPFTOOL) btf dump file /sys/kernel/btf/vmlinux format c > $@

%.bpf.o: %.bpf.c vmlinux.h
	$(CLANG) $(BPF_CFLAGS) -c $< -o $@

$(HM)/hashmap.skel.h: $(HM)/hashmap.bpf.o
	$(BPFTOOL) gen skeleton $< > $@

$(HM)/hashmap: $(HM)/hashmap.c $(HM)/hashmap.skel.h
	$(CC) -g -O2 -Wall -I$(HM) $< -o $@ -lbpf -lelf -lz

clean:
	rm -f vmlinux.h */*/*.o $(HM)/hashmap.skel.h $(HM)/hashmap

.PHONY: all clean
