# Chapter 3 figures: where vmlinux.h comes from; one CO-RE relocation, followed (step widget + twins).
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *

def box2(x, y, w, h, col, t1, t2, mono1=False, mono2=False, step=None, size1=12.5, sw=0.9, dash=None):
    """A box with a title and a detail line; either line may be monospace."""
    l, d, xx = C[col]
    st = f' data-step="{step}"' if step else ''
    da = f' stroke-dasharray="{dash}"' if dash else ''
    f1 = f' font-family="{MONO}"' if mono1 else ''
    f2 = f' font-family="{MONO}"' if mono2 else ''
    cx = x + w / 2
    return (f'<g{st}><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{l}" stroke="{d}" stroke-width="{sw}"{da}/>'
            f'<text x="{cx}" y="{y + h/2 - 9}" text-anchor="middle" dominant-baseline="central" font-size="{size1}" font-weight="600" fill="{xx}"{f1}>{esc(t1)}</text>'
            f'<text x="{cx}" y="{y + h/2 + 10}" text-anchor="middle" dominant-baseline="central" font-size="11" fill="{d}"{f2}>{esc(t2)}</text></g>')

# ---------------- Figure 3.1: where vmlinux.h comes from ----------------
m = 'ah-3-1'
b = []
b.append(text(40, 16, 'the kernel build: once per kernel', size=11, col='gray', anchor='start', italic=True))
row1 = [(40, 100, 'gray', 'kernel source', 'and its config', False),
        (170, 110, 'gray', 'DWARF', 'compiler debug info', False),
        (310, 120, 'coral', 'BTF', 'pahole converts it', False),
        (460, 180, 'coral', '/sys/kernel/btf/vmlinux', '6.5 MB on your machine', True)]
for (x, w, col, t1, t2, mo) in row1:
    b.append(box2(x, 28, w, 50, col, t1, t2, mono1=mo, size1=11 if mo else 12.5))
for x1, x2 in [(140, 168), (280, 308), (430, 458)]:
    b.append(arrow(x1, 53, x2, 53, m))
b.append(text(40, 110, 'your build machine: once per header', size=11, col='gray', anchor='start', italic=True))
row2 = [(460, 180, 'bpftool btf dump', 'file … format c', True),
        (310, 120, 'vmlinux.h', '161,305 lines', True),
        (170, 110, 'clang', 'notes each read', False),
        (40, 100, 'your .bpf.o', 'code + records', True)]
for (x, w, t1, t2, mo) in row2:
    b.append(box2(x, 122, w, 50, 'teal', t1, t2, mono1=mo, size1=12 if mo else 12.5))
b.append(arrow(550, 80, 550, 120, m))
for x1, x2 in [(458, 432), (308, 282), (168, 142)]:
    b.append(arrow(x1, 147, x2, 147, m))
b.append(text(196, 204, 'the machine that loads it: at every start', size=11, col='gray', anchor='start', italic=True))
b.append(box2(460, 216, 180, 50, 'coral', '/sys/kernel/btf/vmlinux', "that machine's kernel", mono1=True, size1=11))
b.append(box2(170, 216, 262, 50, 'teal', 'libbpf, at load', "answers each record from that kernel's types", size1=12.5, sw=1.6))
b.append(f'<path d="M90,174 V241 H166" fill="none" stroke="{LINE}" stroke-width="1.3" marker-end="url(#{m})"/>')
b.append(arrow(458, 241, 434, 241, m))
b.append(bar(286, 36, "The kernel's types are read twice: once to write the header, once by libbpf when the program loads."))
fig_hdr = svg(332, 'Where vmlinux.h comes from, and where the kernel types are read again',
              'The kernel build turns debug info into BTF exposed in sysfs; bpftool dumps it as vmlinux.h; clang compiles the program with records; libbpf reads the target kernel BTF again at load', b, m)

# ---------------- Figure 3.3: one relocation (step widget) ----------------
m = 'ah-3-3'
b = []
b.append(text(115, 14, 'your object, compiled in March', size=11.5, col='gray', weight='600'))
b.append(text(340, 14, 'libbpf, at load', size=11.5, col='gray', weight='600', step='2+'))
b.append(text(565, 14, "your kernel's types, today", size=11.5, col='gray', weight='600', step='2+'))
b.append(box2(20, 28, 190, 52, 'teal', 'slot 2, as compiled', 'w4 = *(u32 *)(r1 + 0xad0)', mono2=True))
b.append(box2(20, 92, 190, 52, 'amber', 'a record for slot 2', 'task_struct.pid: offset?', mono2=True))
b.append(box2(250, 92, 180, 52, 'gray', 'libbpf', 'matches by name', step='2+'))
b.append(box2(470, 28, 190, 52, 'coral', 'struct task_struct', '6144 bytes, 269 fields', mono1=True, step='2+', size1=12))
b.append(box2(470, 92, 190, 52, 'coral', 'field 95: pid', 'at byte 2872 = 0xb38', step='2,3'))
b.append(box2(470, 92, 190, 52, 'coral', 'no field named pid', 'say, after a rename', step='4', dash='4 3'))
b.append(arrow(212, 118, 247, 118, m, step='2+'))
b.append(arrow(432, 118, 467, 118, m, step='2+'))
b.append(text(115, 156, '0xad0 = 2768: field 97 in the March header', size=10.5, col='gray', step='2+', italic=True))
b.append(arrow(340, 146, 340, 168, m, width=2.4, color=C['teal'][1], step='3'))
b.append(box2(20, 172, 640, 44, 'teal', 'slot 2, as loaded', 'w4 = *(u32 *)(r1 + 0xb38)', mono2=True, step='3', sw=1.6))
b.append(arrow(340, 146, 340, 168, m, width=2.4, color=C['coral'][1], step='4'))
b.append(box2(20, 172, 640, 44, 'coral', 'slot 2 becomes a call to helper 195896080, "bad relo"', 'the load fails: failed to resolve CO-RE relocation …', mono2=True, step='4', sw=1.6))
steps = [('1', 'clang wrote the March offset into slot 2, and a record that asks for it again at load'),
         ('2', 'libbpf looks up task_struct, then pid, by name in the running kernel\'s types'),
         ('3', 'it writes the new offset into slot 2; the kernel receives a plain load'),
         ('4', 'on a kernel with no field of that name, the load fails instead of reading the wrong bytes')]
for stp, t in steps:
    b.append(text(340, 232, t, size=11.5, italic=True, step=stp))
fig_relo = svg(244, 'One CO-RE relocation in the fork tracer, followed from compile to load',
               'Slot 2 of the fork tracer carries the March offset of task_struct.pid; libbpf finds pid by name in the running kernel and patches the offset, or fails the load if no such field exists', b, m)

save('ch03-header', fig_hdr)
save('ch03-relo', fig_relo)
for i, f in enumerate(frames(fig_relo, m, (3, 4)), 1):
    save(f'ch03-relo-twin{i}', f)
print('ch03 figures ok')
