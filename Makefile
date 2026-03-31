CLANG    := clang
BPFTOOL  := bpftool
CC       := gcc
ARCH     := $(shell uname -m | sed 's/x86_64/x86/' | sed 's/aarch64/arm64/')

BPF_CFLAGS := -g -O2 -target bpf -D__TARGET_ARCH_$(ARCH) \
              -I/usr/include/bpf -I. -Wall -Werror \
              -Wno-missing-declarations

BPF_CFLAGS_STRICT := -g -O2 -target bpf -D__TARGET_ARCH_$(ARCH) \
                     -I/usr/include/bpf -I. -Wall -Wextra -Werror

CFLAGS  := -g -O2 -Wall -I.
CFLAGS_STRICT := -g -O2 -Wall -Wextra -Werror -I.
LDFLAGS := -lbpf -lelf -lz

EXERCISES := hello_world/01-hello \
             hello_world/02-kprobe \
             hello_world/03-tracepoint \
             maps/01-array-counter \
             maps/02-hash-map \
             maps/03-ringbuf \
             pinning/01-pin-map \
             pinning/02-share-map \
             timers_kfuncs/01-timer-basic \
             timers_kfuncs/02-kfunc-get-boottime

.PHONY: all clean $(EXERCISES)

all: $(EXERCISES)

# --- vmlinux.h ---

vmlinux.h: /sys/kernel/btf/vmlinux
	$(BPFTOOL) btf dump file $< format c > $@

# --- Generic rules ---

%.bpf.o: %.bpf.c vmlinux.h
	$(CLANG) $(BPF_CFLAGS) -c $< -o $@

%.skel.h: %.bpf.o
	$(BPFTOOL) gen skeleton $< > $@

# --- hello_world ---

hello_world/01-hello: hello_world/01-hello/hello.bpf.o

hello_world/02-kprobe: hello_world/02-kprobe/kprobe.bpf.o

hello_world/03-tracepoint: hello_world/03-tracepoint/tracepoint.bpf.o

# --- maps ---

maps/01-array-counter: maps/01-array-counter/counter
maps/01-array-counter/counter: maps/01-array-counter/counter.c \
                                maps/01-array-counter/counter.skel.h
	$(CC) $(CFLAGS) -I maps/01-array-counter $< -o $@ $(LDFLAGS)

maps/02-hash-map: maps/02-hash-map/hashmap
maps/02-hash-map/hashmap: maps/02-hash-map/hashmap.c \
                           maps/02-hash-map/hashmap.skel.h
	$(CC) $(CFLAGS) -I maps/02-hash-map $< -o $@ $(LDFLAGS)

maps/03-ringbuf: maps/03-ringbuf/ringbuf
maps/03-ringbuf/ringbuf: maps/03-ringbuf/ringbuf.c \
                          maps/03-ringbuf/ringbuf.skel.h
	$(CC) $(CFLAGS) -I maps/03-ringbuf $< -o $@ $(LDFLAGS)

# --- pinning ---

pinning/01-pin-map: pinning/01-pin-map/pin
pinning/01-pin-map/pin: pinning/01-pin-map/pin.c \
                         pinning/01-pin-map/pin.skel.h
	$(CC) $(CFLAGS) -I pinning/01-pin-map $< -o $@ $(LDFLAGS)

pinning/02-share-map: pinning/02-share-map/share
pinning/02-share-map/share: pinning/02-share-map/share.c \
                             pinning/02-share-map/writer.skel.h \
                             pinning/02-share-map/reader.skel.h
	$(CC) $(CFLAGS) -I pinning/02-share-map $< -o $@ $(LDFLAGS)

# --- timers_kfuncs ---

timers_kfuncs/01-timer-basic: timers_kfuncs/01-timer-basic/timer
timers_kfuncs/01-timer-basic/timer: timers_kfuncs/01-timer-basic/timer.c \
                                     timers_kfuncs/01-timer-basic/timer.skel.h
	$(CC) $(CFLAGS) -I timers_kfuncs/01-timer-basic $< -o $@ $(LDFLAGS)

timers_kfuncs/02-kfunc-get-boottime: timers_kfuncs/02-kfunc-get-boottime/boottime
timers_kfuncs/02-kfunc-get-boottime/boottime: timers_kfuncs/02-kfunc-get-boottime/boottime.c \
                                                timers_kfuncs/02-kfunc-get-boottime/boottime.skel.h
	$(CC) $(CFLAGS) -I timers_kfuncs/02-kfunc-get-boottime $< -o $@ $(LDFLAGS)

# --- test (strict warnings) ---

TEST_EXERCISES := $(addprefix test/,$(EXERCISES))
.PHONY: $(TEST_EXERCISES)

test/hello_world/01-hello: vmlinux.h
	$(CLANG) $(BPF_CFLAGS_STRICT) -c hello_world/01-hello/hello.bpf.c -o hello_world/01-hello/hello.bpf.o

test/hello_world/02-kprobe: vmlinux.h
	$(CLANG) $(BPF_CFLAGS_STRICT) -c hello_world/02-kprobe/kprobe.bpf.c -o hello_world/02-kprobe/kprobe.bpf.o

test/hello_world/03-tracepoint: vmlinux.h
	$(CLANG) $(BPF_CFLAGS_STRICT) -c hello_world/03-tracepoint/tracepoint.bpf.c -o hello_world/03-tracepoint/tracepoint.bpf.o

test/maps/01-array-counter: vmlinux.h
	$(CLANG) $(BPF_CFLAGS_STRICT) -c maps/01-array-counter/counter.bpf.c -o maps/01-array-counter/counter.bpf.o
	$(BPFTOOL) gen skeleton maps/01-array-counter/counter.bpf.o > maps/01-array-counter/counter.skel.h
	$(CC) $(CFLAGS_STRICT) -I maps/01-array-counter maps/01-array-counter/counter.c -o maps/01-array-counter/counter $(LDFLAGS)

test/maps/02-hash-map: vmlinux.h
	$(CLANG) $(BPF_CFLAGS_STRICT) -c maps/02-hash-map/hashmap.bpf.c -o maps/02-hash-map/hashmap.bpf.o
	$(BPFTOOL) gen skeleton maps/02-hash-map/hashmap.bpf.o > maps/02-hash-map/hashmap.skel.h
	$(CC) $(CFLAGS_STRICT) -I maps/02-hash-map maps/02-hash-map/hashmap.c -o maps/02-hash-map/hashmap $(LDFLAGS)

test/maps/03-ringbuf: vmlinux.h
	$(CLANG) $(BPF_CFLAGS_STRICT) -c maps/03-ringbuf/ringbuf.bpf.c -o maps/03-ringbuf/ringbuf.bpf.o
	$(BPFTOOL) gen skeleton maps/03-ringbuf/ringbuf.bpf.o > maps/03-ringbuf/ringbuf.skel.h
	$(CC) $(CFLAGS_STRICT) -I maps/03-ringbuf maps/03-ringbuf/ringbuf.c -o maps/03-ringbuf/ringbuf $(LDFLAGS)

test/pinning/01-pin-map: vmlinux.h
	$(CLANG) $(BPF_CFLAGS_STRICT) -c pinning/01-pin-map/pin.bpf.c -o pinning/01-pin-map/pin.bpf.o
	$(BPFTOOL) gen skeleton pinning/01-pin-map/pin.bpf.o > pinning/01-pin-map/pin.skel.h
	$(CC) $(CFLAGS_STRICT) -I pinning/01-pin-map pinning/01-pin-map/pin.c -o pinning/01-pin-map/pin $(LDFLAGS)

test/pinning/02-share-map: vmlinux.h
	$(CLANG) $(BPF_CFLAGS_STRICT) -c pinning/02-share-map/writer.bpf.c -o pinning/02-share-map/writer.bpf.o
	$(BPFTOOL) gen skeleton pinning/02-share-map/writer.bpf.o > pinning/02-share-map/writer.skel.h
	$(CLANG) $(BPF_CFLAGS_STRICT) -c pinning/02-share-map/reader.bpf.c -o pinning/02-share-map/reader.bpf.o
	$(BPFTOOL) gen skeleton pinning/02-share-map/reader.bpf.o > pinning/02-share-map/reader.skel.h
	$(CC) $(CFLAGS_STRICT) -I pinning/02-share-map pinning/02-share-map/share.c -o pinning/02-share-map/share $(LDFLAGS)

test/timers_kfuncs/01-timer-basic: vmlinux.h
	$(CLANG) $(BPF_CFLAGS_STRICT) -c timers_kfuncs/01-timer-basic/timer.bpf.c -o timers_kfuncs/01-timer-basic/timer.bpf.o
	$(BPFTOOL) gen skeleton timers_kfuncs/01-timer-basic/timer.bpf.o > timers_kfuncs/01-timer-basic/timer.skel.h
	$(CC) $(CFLAGS_STRICT) -I timers_kfuncs/01-timer-basic timers_kfuncs/01-timer-basic/timer.c -o timers_kfuncs/01-timer-basic/timer $(LDFLAGS)

test/timers_kfuncs/02-kfunc-get-boottime: vmlinux.h
	$(CLANG) $(BPF_CFLAGS_STRICT) -c timers_kfuncs/02-kfunc-get-boottime/boottime.bpf.c -o timers_kfuncs/02-kfunc-get-boottime/boottime.bpf.o
	$(BPFTOOL) gen skeleton timers_kfuncs/02-kfunc-get-boottime/boottime.bpf.o > timers_kfuncs/02-kfunc-get-boottime/boottime.skel.h
	$(CC) $(CFLAGS_STRICT) -I timers_kfuncs/02-kfunc-get-boottime timers_kfuncs/02-kfunc-get-boottime/boottime.c -o timers_kfuncs/02-kfunc-get-boottime/boottime $(LDFLAGS)

# --- clean ---

clean:
	find . -name '*.bpf.o' -o -name '*.skel.h' | xargs -r rm -f
	rm -f maps/01-array-counter/counter \
	      maps/02-hash-map/hashmap \
	      maps/03-ringbuf/ringbuf \
	      pinning/01-pin-map/pin \
	      pinning/02-share-map/share \
	      timers_kfuncs/01-timer-basic/timer \
	      timers_kfuncs/02-kfunc-get-boottime/boottime
	rm -f vmlinux.h
