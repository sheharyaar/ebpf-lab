# Chapter 2 figures: from SEC() name to hook; who holds whom after load and attach.
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *

# ---------------- Figure 2.2: section name -> program type and hook ----------------
m = 'ah-2-2'
b = [text(40, 16, 'your SEC() string, cut at the first slash', size=11, col='gray', anchor='start', italic=True),
     text(380, 16, 'what libbpf makes of each part', size=11, col='gray', anchor='start', italic=True)]
rows = [
    ('your write counter · maps/02-hash-map', 'tracepoint', '/syscalls/sys_enter_write',
     ('BPF_PROG_TYPE_TRACEPOINT', 'table entry tracepoint+, no attach type yet'),
     ('syscalls / sys_enter_write', 'a fixed tracepoint, found by its number')),
    ('your kprobe exercise · hello_world/02-kprobe', 'kprobe', '/do_sys_openat2',
     ('BPF_PROG_TYPE_KPROBE', 'table entry kprobe+, no attach type yet'),
     ('do_sys_openat2', 'the entry of a kernel function, by name')),
    ('your fork tracer · hello_world/03-tracepoint', 'tp_btf', '/sched_process_fork',
     ('BPF_PROG_TYPE_TRACING', 'entry tp_btf+, attach type BPF_TRACE_RAW_TP'),
     ('sched_process_fork', 'a tracepoint with typed arguments')),
]
CW = 7.25  # mono 12 advance
for i, (lab, pre, ext, typ, hook) in enumerate(rows):
    y0 = 30 + i * 108
    b.append(text(40, y0 + 12, lab, size=11, anchor='start'))
    wp, we = len(pre) * CW + 18, len(ext) * CW + 18
    b.append(box(40, y0 + 36, wp, 32, 'teal', pre, mono1=True, size1=12))
    b.append(box(40 + wp, y0 + 36, we, 32, 'amber', ext, mono1=True, size1=12))
    b.append(box(380, y0 + 4, 260, 44, 'teal', typ[0], typ[1], mono1=True, size1=11.5))
    b.append(box(380, y0 + 56, 260, 44, 'amber', hook[0], hook[1], mono1=True, size1=11.5))
    px, ex = 40 + wp / 2, 40 + wp + we
    b.append(f'<path d="M{px},{y0 + 36} V{y0 + 26} H376" fill="none" stroke="{LINE}" stroke-width="1.3" marker-end="url(#{m})"/>')
    b.append(f'<path d="M{ex},{y0 + 52} H352 V{y0 + 78} H376" fill="none" stroke="{LINE}" stroke-width="1.3" marker-end="url(#{m})"/>')
b.append(bar(360, 36, 'Before the first slash: which program type. After it: which hook. Both come from the section name.'))
fig_sec = svg(406, 'From a SEC() name to a program type and a hook',
              'Three section names from the learner\'s exercises, each split at the first slash; the prefix picks the program type and the rest names the hook', b, m)

# ---------------- Figure 2.4: who holds whom ----------------
m = 'ah-2-4'
b = [text(140, 18, 'your loader process', size=12, col='gray', weight='600'),
     text(470, 18, 'in the kernel', size=12, col='gray', weight='600')]
b.append(f'<rect x="40" y="32" width="200" height="236" rx="6" fill="{C["gray"][0]}" stroke="{C["gray"][1]}" stroke-width="0.9"/>')
fds = [(49, 'map fd · write_counts'), (99, 'map fd · …_.rodata'), (157, 'program fd'), (229, 'link fd')]
for y, t in fds:
    b.append(box(54, y, 172, 30, 'gray', t, mono1=True, size1=11))
objs = [
    (480, 44, 160, 40, 'coral', 'write_counts', 'the hash map'),
    (480, 94, 160, 40, 'coral', 'hashmap_.rodata', 'the bpf_printk string'),
    (300, 150, 140, 44, 'teal', 'count_writes', 'the program, 27 slots'),
    (300, 222, 140, 44, 'teal', 'link', 'one program on one hook'),
    (480, 222, 160, 44, 'coral', 'sys_enter_write', 'tracepoint, as a perf event'),
]
for (x, y, w, h, col, t1, t2) in objs:
    b.append(box(x, y, w, h, col, t1, t2, mono1=t1 != 'link', size1=12))
# a descriptor holds its object: dashed
for (y0, ty) in [(64, 64), (114, 114), (172, 172), (244, 244)]:
    tx2 = 478 if ty < 140 else 298
    b.append(arrow(226, y0, tx2, ty, m, dash='4 3'))
# objects hold objects: solid, thicker
b.append(arrow(370, 222, 370, 197, m, width=1.8))
b.append(arrow(440, 162, 478, 70, m, width=1.8))
b.append(arrow(440, 168, 478, 120, m, width=1.8))
b.append(arrow(440, 244, 478, 244, m, width=1.8))
b.append(text(418, 136, 'holds', size=10.5, col='gray', italic=True))
b.append(text(459, 234, 'holds', size=10.5, col='gray', italic=True))
b.append(text(380, 210, 'holds', size=10.5, col='gray', italic=True, anchor='start'))
# the pin
b.append(f'<rect x="40" y="284" width="200" height="32" rx="6" fill="#FFFFFF" stroke="{C["gray"][1]}" stroke-width="0.9" stroke-dasharray="4 3"/>')
b.append(text(140, 300, 'a pin: a file in /sys/fs/bpf', size=11.5, col='gray'))
b.append(f'<path d="M240,300 H330 V269" fill="none" stroke="{LINE}" stroke-width="1.3" stroke-dasharray="4 3" marker-end="url(#{m})"/>')
b.append(text(338, 300, 'holds whatever it names, with no process at all', size=11, col='gray', anchor='start', italic=True))
b.append(bar(330, 34, 'Each arrow is one reference. An object is freed when its last reference goes.'))
fig_objs = svg(374, 'Who holds whom after load and attach',
               'The loader process holds descriptors for two maps, the program and the link; the link holds the program and the tracepoint, the program holds both maps; a pin can hold any of them', b, m)

save('ch02-sec', fig_sec)
save('ch02-objects', fig_objs)
print('ch02 figures ok')
