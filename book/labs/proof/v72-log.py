#!/usr/bin/env python3
"""What the running kernel's verifier computes for the fixing commit's case.

    vng -r /boot/vmlinuz-linux --user root -- \
        python3 -I book/labs/proof/v72-log.py

Loads, as root in a throwaway VM, an eight-instruction socket filter that builds
the register state of commit 049c4e13714e's message (R2 with var_off
(0x1; 0xffffffff00000000), R3 = 0x100000002), runs r2 &= r3, and returns 0.
It reads no memory.  The script prints the verifier's log at level 2 for the
AND and the instruction before it.  No compiler, no libbpf: raw instructions
through bpf(2) with ctypes.
"""
import ctypes, os, struct

BPF_PROG_LOAD, SOCKET_FILTER, NR_BPF = 5, 1, 321   # linux/bpf.h, x86-64


def insn(code, dst=0, src=0, off=0, imm=0):         # struct bpf_insn
    return struct.pack('<BBhi', code, dst | src << 4, off, imm)


prog = b''.join([
    insn(0x85, imm=7),           # call bpf_get_prandom_u32: r0 = 32 random bits
    insn(0x67, 0, imm=32),       # r0 <<= 32     low half known 0, high unknown
    insn(0x47, 0, imm=1),        # r0 |= 1       low half known 1
    insn(0xbf, 2, 0),            # r2 = r0
    insn(0x18, 3, imm=2),        # r3 = 0x100000002 (two slots)
    insn(0x00, imm=1),
    insn(0x5f, 2, 3),            # r2 &= r3
    insn(0xb7, 0, imm=0),        # r0 = 0
    insn(0x95),                  # exit
])
code = ctypes.create_string_buffer(prog, len(prog))
lic = ctypes.create_string_buffer(b'GPL')
log = ctypes.create_string_buffer(1 << 16)
attr = ctypes.create_string_buffer(struct.pack(
    '<IIQQIIQ', SOCKET_FILTER, len(prog) // 8, ctypes.addressof(code),
    ctypes.addressof(lic), 2, len(log), ctypes.addressof(log)), 128)
libc = ctypes.CDLL(None, use_errno=True)
fd = libc.syscall(NR_BPF, BPF_PROG_LOAD, attr, 128)
err = ctypes.get_errno()
print(f'kernel {os.uname().release}: load', 'ok' if fd >= 0 else
      f'failed: {os.strerror(err)}')
for line in log.value.decode().splitlines():
    if line.startswith(('2:', '6:')) or 'processed' in line:
        print(line)
