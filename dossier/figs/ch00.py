import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *

# ---------------- Figure 0.1: three ways to put code in the kernel ----------------
m = 'ah-0-1'
cols = [(20, 'Kernel module', 'your code becomes kernel code', 'gray'),
        (240, 'Copy everything out', 'the kernel hands packets to you', 'gray'),
        (460, 'Filter machine', 'the kernel runs your small program', 'teal')]
rows = [
    ('Runs as', [('native kernel code', 'loaded into the kernel'), ('a user-space program', 'outside the kernel'),
                 ('filter instructions', 'interpreted, once per packet')]),
    ('Can read', [('all kernel memory', 'and write it'), ('only its copies', 'nothing inside the kernel'),
                  ('one packet', 'plus 16 words of scratch')]),
    ('A bug means', [('the kernel crashes', 'the machine goes down'), ('your program crashes', 'the kernel is untouched'),
                     ('wrong packets kept', 'the kernel is untouched')]),
    ('A rejected packet costs', [('almost nothing', 'it runs at full speed'), ('a full copy', 'made, then thrown away'),
                                 ('a few instructions', 'no copy at all')]),
    ('On the next kernel', [('rebuild the module', 'it is tied to one version'), ('runs unchanged', ''),
                            ('runs unchanged', '')]),
]
b = []
for x, t1, t2, col in cols:
    b.append(text(x + 100, 18, t1, size=14, col=col, weight='600'))
    b.append(text(x + 100, 36, t2, size=11, col=col, italic=True))
y = 56
for label, cells in rows:
    watch = label == 'A bug means'
    b.append(text(20, y + 7, label, size=10.5, col='amber' if watch else 'gray', anchor='start', weight='600'))
    for (x, _, _, col), (c1, c2) in zip(cols, cells):
        b.append(box(x, y + 16, 200, 42, 'amber' if watch else col, c1, c2 or None, size1=12.5))
    y += 70
b.append(f'<rect x="20" y="{y + 2}" width="640" height="30" rx="6" fill="{C["gray"][0]}" stroke="{C["gray"][1]}" stroke-width="0.75"/>')
b.append(text(340, y + 17, 'eBPF keeps the third column and widens what the program may do: chapters 1 to 9.', size=12, col='gray'))
save('ch00-three', svg(y + 42, 'Three ways to put code in the kernel',
                       'Three columns comparing a kernel module, copying every packet to user space, and a filter machine, '
                       'row by row: how the code runs, what it can read, what a bug means, what a rejected packet costs, '
                       'and what happens on the next kernel', b, m))

# ---------------- Figure 0.2: the BSD network tap, redrawn from the paper's Figure 1 ----------------
m = 'ah-0-2'
T = C['teal'][1]
b = []
apps = [(60, 'network monitor'), (230, 'network monitor'), (400, 'rarpd')]
b.append(text(20, 16, 'user space', size=10.5, col='gray', anchor='start', italic=True))
for x, name in apps:
    b.append(box(x, 26, 140, 32, 'gray', name, size1=12))
b.append(f'<line x1="20" y1="76" x2="660" y2="76" stroke="{LINE}" stroke-width="0.8" stroke-dasharray="5 4"/>')
b.append(text(20, 90, 'kernel', size=10.5, col='gray', anchor='start', italic=True))
for x, _ in apps:
    b.append(box(x, 100, 140, 30, 'gray', 'buffer', size1=12))
    b.append(box(x, 158, 140, 30, 'teal', 'filter', size1=12))
    b.append(arrow(x + 70, 98, x + 70, 62, m))                       # read() up to the program
    b.append(arrow(x + 70, 156, x + 70, 134, m, width=2.4, color=T))  # accepted bytes into the buffer
    b.append(arrow(x + 70, 214, x + 70, 192, m, width=2.4, color=T))  # BPF hands the packet to each filter
b.append(box(60, 216, 480, 34, 'coral', 'BPF: the tap', 'runs every listener’s filter on the packet where it lies', size1=12.5))
b.append(box(560, 158, 100, 92, 'gray', 'protocol', 'stack', size1=12))
drivers = [60, 260, 460]
for x in drivers:
    b.append(box(x, 288, 140, 30, 'gray', 'link-level driver', size1=12))
    b.append(arrow(x + 70, 352, x + 70, 322, m))
for x in (130, 330, 500):
    b.append(arrow(x, 286, x, 254, m, width=2.4, color=T))           # each driver calls BPF first
b.append(arrow(590, 286, 610, 254, m))                               # then the normal path to the stack
b.append(f'<line x1="20" y1="356" x2="660" y2="356" stroke="{LINE}" stroke-width="2"/>')
b.append(text(340, 370, 'network', size=11, col='gray', italic=True))
b.append(text(560, 132, 'only accepted bytes', size=10.5, col='amber', anchor='start'))
b.append(text(560, 146, 'are copied up', size=10.5, col='amber', anchor='start'))
b.append(f'<line x1="556" y1="140" x2="478" y2="145" stroke="{C["amber"][1]}" stroke-width="0.9" stroke-dasharray="3 3"/>')
save('ch00-tap', svg(382, 'The BSD network tap',
                     'Redrawn from Figure 1 of the 1993 BSD Packet Filter paper: link-level drivers call BPF, which runs each '
                     'listening program’s filter on the packet and copies only accepted bytes into that program’s buffer', b, m))

# ---------------- Figure 0.3: the lineage, one row per change ----------------
m = 'ah-0-3'
eras = [
    ('Classic BPF: a filter for packets, then for system calls', [
        ('1993', '—', 'The BSD Packet Filter paper (McCanne and Jacobson)', '0', 'g'),
        ('1997', '2.1.75', 'Linux Socket Filter: classic BPF on one socket', '0', 'g'),
        ('2011', '3.0', 'classic filters translated into x86-64 machine code', '7', 'g'),
        ('2012', '3.5', 'seccomp: classic BPF filters system calls', '0', 'g')]),
    ('The new machine: registers, calls, maps, hooks', [
        ('2014', '3.15', 'eBPF: the machine rebuilt inside the kernel', '1', 'a'),
        ('2014', '3.16', 'eBPF programs translated into x86-64 code', '7', 'g'),
        ('2014', '3.18', 'the bpf() system call and maps', '2, 9', 't'),
        ('2015', '4.1', 'kprobes: a program on (almost) any kernel function', '8', 'g'),
        ('2015', '4.2', 'tail calls: one program jumps to another', '7', 'g'),
        ('2016', '4.4', 'bpffs: programs and maps pinned as files', '2', 'g'),
        ('2016', '4.7', 'tracepoints: fixed, named hooks', '8', 't'),
        ('2016', '4.8', 'XDP: a program in the network driver', '8', 'g')]),
    ('Types and links: one binary for many kernels', [
        ('2018', '4.16', 'bpf-to-bpf function calls', '7', 'g'),
        ('2018', '4.18', 'BTF: the kernel describes its own types', '3', 't'),
        ('2019', '5.2', 'the one-million-instruction limit', '4', 'g'),
        ('2019', '5.3', 'bounded loops', '4', 'g'),
        ('2020', 'libbpf', 'CO-RE: compile once, run everywhere', '3', 't'),
        ('2020', '5.5', 'trampolines: programs on function entry and exit', '7, 8', 'g'),
        ('2020', '5.7', 'LSM programs; bpf_link', '2, 8', 'g'),
        ('2020', '5.8', 'the ring buffer', '9', 'g')]),
    ('Extending the kernel itself', [
        ('2021', '5.13', 'kfuncs: programs call ordinary kernel functions', '8', 'g'),
        ('2024', '6.9', 'arena; BPF token', '9, 11', 'g'),
        ('2024', '6.12', 'sched_ext: a CPU scheduler written in BPF', '8', 'g'),
        ('2024', 'RFC', 'RFC 9669: the instruction set becomes a standard', '1', 'g'),
        ('2025', '6.18', 'signed BPF programs', '11', 'g')]),
]
DOT = {'g': (C['gray'][0], C['gray'][1]), 't': (C['teal'][1], C['teal'][2]), 'a': (C['amber'][1], C['amber'][2])}
b = [text(56, 14, 'year', size=10, col='gray', anchor='end', italic=True),
     text(92, 14, 'kernel', size=10, col='gray', anchor='start', italic=True),
     text(150, 14, 'change', size=10, col='gray', anchor='start', italic=True),
     text(664, 14, 'chapter', size=10, col='gray', anchor='end', italic=True)]
y, top = 34, 34
for era, events in eras:
    b.append(f'<rect x="16" y="{y - 2}" width="648" height="20" fill="{C["gray"][0]}"/>')
    b.append(text(24, y + 8, era, size=11, col='gray', anchor='start', weight='600', italic=True))
    y += 30
    for year, ver, what, ch, kind in events:
        fill, stroke = DOT[kind]
        b.append(text(56, y, year, size=11, anchor='end', mono=True))
        b.append(f'<circle cx="74" cy="{y}" r="4.2" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
        b.append(text(92, y, ver, size=11, anchor='start', mono=True, col='teal' if kind != 'g' else None))
        b.append(text(150, y, what, size=11.5, anchor='start', col='amber' if kind == 'a' else None,
                      weight='600' if kind != 'g' else None))
        b.append(text(664, y, ch, size=11, anchor='end', mono=True, col='gray'))
        b.append(f'<line x1="150" y1="{y + 10}" x2="664" y2="{y + 10}" stroke="#D6D2C8" stroke-width="0.5"/>')
        y += 21
    y += 8
b.insert(0, f'<line x1="74" y1="{top + 26}" x2="74" y2="{y - 34}" stroke="#BDB7AA" stroke-width="1"/>')
b.append(f'<circle cx="30" cy="{y + 6}" r="4.2" fill="{C["teal"][1]}" stroke="{C["teal"][2]}"/>')
b.append(text(40, y + 6, 'your write counter depends on it', size=10.5, col='teal', anchor='start'))
b.append(f'<circle cx="270" cy="{y + 6}" r="4.2" fill="{C["amber"][1]}" stroke="{C["amber"][2]}"/>')
b.append(text(280, y + 6, 'the turn this book starts from', size=10.5, col='amber', anchor='start'))
b.append(f'<circle cx="490" cy="{y + 6}" r="4.2" fill="{C["gray"][0]}" stroke="{C["gray"][1]}"/>')
b.append(text(500, y + 6, 'context', size=10.5, col='gray', anchor='start'))
save('ch00-lineage', svg(y + 20, 'Thirty-two years of BPF, one row per change',
                         'A list of 25 changes from the 1993 BSD Packet Filter paper to signed BPF programs in Linux 6.18, '
                         'grouped in four eras, each with its year, kernel version and the chapter that covers it', b, m))
print('ok')
