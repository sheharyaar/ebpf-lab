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
        (460, 180, 'coral', '/sys/kernel/btf/vmlinux', '6.5 MB on kernel 7.2', True)]
for (x, w, col, t1, t2, mo) in row1:
    b.append(box2(x, 28, w, 50, col, t1, t2, mono1=mo, size1=11 if mo else 12.5))
for x1, x2 in [(140, 168), (280, 308), (430, 458)]:
    b.append(arrow(x1, 53, x2, 53, m))
b.append(text(40, 110, 'the build machine: once per header', size=11, col='gray', anchor='start', italic=True))
row2 = [(460, 180, 'bpftool btf dump', 'file … format c', True),
        (310, 120, 'vmlinux.h', '166,183 lines', True),
        (170, 110, 'clang', 'notes each read', False),
        (40, 100, 'the .bpf.o', 'code + records', True)]
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
b.append(text(115, 14, 'the object, built on kernel 7.2', size=11.5, col='gray', weight='600'))
b.append(text(340, 14, 'libbpf, at load', size=11.5, col='gray', weight='600', step='2+'))
b.append(text(565, 14, "an Ubuntu 20.04 kernel, 5.4", size=11.5, col='gray', weight='600', step='2,3'))
b.append(text(565, 14, "a kernel without that field", size=11.5, col='gray', weight='600', step='4'))
b.append(box2(20, 28, 190, 52, 'teal', 'slot 2, as compiled', 'w4 = *(u32 *)(r1 + 0xb38)', mono2=True))
b.append(box2(20, 92, 190, 52, 'amber', 'a record for slot 2', 'task_struct.pid: offset?', mono2=True))
b.append(box2(250, 92, 180, 52, 'gray', 'libbpf', 'matches by name', step='2+'))
b.append(box2(470, 28, 190, 52, 'coral', 'struct task_struct', '9280 bytes, 213 fields', mono1=True, step='2,3', size1=12))
b.append(box2(470, 28, 190, 52, 'coral', 'struct task_struct', 'found by name', mono1=True, step='4', size1=12))
b.append(box2(470, 92, 190, 52, 'coral', 'field 65: pid', 'at byte 2264 = 0x8d8', step='2,3'))
b.append(box2(470, 92, 190, 52, 'coral', 'no field named pid', 'say, after a rename', step='4', dash='4 3'))
b.append(arrow(212, 118, 247, 118, m, step='2+'))
b.append(arrow(432, 118, 467, 118, m, step='2+'))
b.append(text(115, 156, '0xb38 = 2872: field 95 in the 7.2 header', size=10.5, col='gray', step='2+', italic=True))
b.append(arrow(340, 146, 340, 168, m, width=2.4, color=C['teal'][1], step='3'))
b.append(box2(20, 172, 640, 44, 'teal', 'slot 2, as loaded on that kernel', 'w4 = *(u32 *)(r1 + 0x8d8)', mono2=True, step='3', sw=1.6))
b.append(arrow(340, 146, 340, 168, m, width=2.4, color=C['coral'][1], step='4'))
b.append(box2(20, 172, 640, 44, 'coral', 'slot 2 becomes a call to helper 195896080, "bad relo"', 'the load fails: failed to resolve CO-RE relocation …', mono2=True, step='4', sw=1.6))
steps = [('1', 'clang wrote the 7.2 kernel\'s offset into slot 2, and a record that asks for it again at load'),
         ('2', 'on another kernel, libbpf looks up task_struct, then pid, by name in that kernel\'s types'),
         ('3', 'it writes that kernel\'s offset into slot 2; the kernel receives a plain load'),
         ('4', 'on a kernel with no field of that name, the load fails instead of reading the wrong bytes')]
for stp, t in steps:
    b.append(text(340, 232, t, size=11.5, italic=True, step=stp))
fig_relo = svg(244, 'One CO-RE relocation in the fork tracer, followed from compile to load on another kernel',
               'Slot 2 of the fork tracer carries the 7.2 offset of task_struct.pid; on a 5.4 kernel libbpf finds pid by name and patches the offset, or fails the load if no such field exists', b, m)

save('ch03-relo', fig_relo)
for i, f in enumerate(frames(fig_relo, m, (3, 4)), 1):
    save(f'ch03-relo-twin{i}', f)
# ---------- print helpers, as for Figure 4.2 (figs/ch04.py): 680 units = 127 mm, words 14.5 or more, node titles 16 ----------
SANS = "'Open Sans Condensed', 'Open Sans', 'Myriad Pro', sans-serif"
UMONO = "'Ubuntu Mono', 'JetBrains Mono', monospace"
INK, GREY, P2 = '#1F2328', '#4A5056', '#0F6E56'
def t(x, y, s_, size=15, anchor='middle', fam=SANS, weight=None, fill=INK, italic=False):
    w = f' font-weight="{weight}"' if weight else ''
    it = ' font-style="italic"' if italic else ''
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-family="{fam}" '
            f'font-size="{size}" fill="{fill}"{w}{it}>{esc(s_)}</text>')
def line(pts, mid=None, color=INK, width=1.8, dash=None):
    d = ' '.join(f'{"M" if i == 0 else "L"}{x},{y}' for i, (x, y) in enumerate(pts))
    da = f' stroke-dasharray="{dash}"' if dash else ''
    me = f' marker-end="url(#{mid})"' if mid else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da}{me}/>'
def markers(mid):
    return '<defs>' + ''.join(f'<marker id="{mid}-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                              f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
                              for k, c in (('k', INK), ('a', P2))) + '</defs>'
def tm(x, y, parts, size=15, anchor='middle', fill=INK):
    """One line in mixed faces: parts are (text, face) with face 'm' for a code name, 's' for words."""
    sp = ''.join(f'<tspan font-family="{UMONO if f == "m" else SANS}">{esc(s_)}</tspan>' for s_, f in parts)
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-size="{size}" fill="{fill}" xml:space="preserve">{sp}</text>'
def rect(x, y, w, h, stroke=INK, sw=1.3, rx=5, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="#FFFFFF" stroke="{stroke}" stroke-width="{sw}"{da}/>'

# ---------- Figure 3.3 for print: one flowchart, two target kernels (replaces the two frames) ----------
m = 'ah-3-3p'
b = [markers(m)]
cx, NX, NW = 170, 20, 300              # the main column
def node(y, h, lines):
    """A step: lines are (text or [(text, face), ...], size, face, weight, fill)."""
    out = [rect(NX, y, NW, h)]
    n = len(lines)
    for i, (s_, size, face, weight, fill) in enumerate(lines):
        yy = y + h / 2 + (i - (n - 1) / 2) * 20
        out.append(tm(cx, yy, s_, size=size, fill=fill) if isinstance(s_, list) else
                   t(cx, yy, s_, size=size, fam=UMONO if face == 'm' else SANS, weight=weight, fill=fill))
    return out
b += node(10, 58, [('slot 2, as compiled', 16, 's', '700', INK), ('w4 = *(u32 *)(r1 + 0xb38)', 15, 'm', None, INK)])
b += [t(336, 29, '0xb38 = 2872:', size=14.5, anchor='start', italic=True, fill=GREY),
      t(336, 49, 'field 95 in the 7.2 header', size=14.5, anchor='start', italic=True, fill=GREY)]
b.append(line([(cx, 68), (cx, 116)], m + '-k', width=2.2))
b += [t(cx + 12, 83, 'clang adds a record for slot 2:', size=14.5, anchor='start', italic=True, fill=GREY),
      t(cx + 12, 102, 'task_struct.pid: offset?', size=14.5, anchor='start', fam=UMONO, fill=GREY)]
b += node(118, 58, [('libbpf, at load, on another kernel', 16, 's', '700', INK),
                    ([('looks up ', 's'), ('struct task_struct', 'm'), (' by name', 's')], 15, 's', None, GREY)])
b.append(line([(cx, 176), (cx, 200)], m + '-k', width=2.2))
DY, DH, DW = 264, 62, 152              # the decision: centre y, half height, half width
b.append(f'<polygon points="{cx - DW},{DY} {cx},{DY - DH} {cx + DW},{DY} {cx},{DY + DH}" fill="#FFFFFF" stroke="{INK}" stroke-width="1.3"/>')
b += [t(cx, DY - 20, "does the target kernel's", size=15), t(cx, DY, 'struct task_struct', size=15, fam=UMONO, weight='700'),
      tm(cx, DY + 20, [('have a field named ', 's'), ('pid', 'm'), ('?', 's')], size=15)]
# yes: Ubuntu 20.04's 5.4 kernel, where pid has moved
b.append(line([(cx, DY + DH), (cx, 392)], m + '-k', width=2.2))
b += [t(cx - 12, DY + DH + 16, 'yes', size=15.5, anchor='end', weight='700'),
      t(cx + 12, 348, "Ubuntu 20.04's 5.4 kernel:", size=14.5, anchor='start', fill=GREY, weight='700'),
      tm(cx + 12, 367, [('task_struct', 'm'), (': 9280 bytes, 213 fields', 's')], size=14.5, anchor='start', fill=GREY),
      tm(cx + 12, 386, [('pid', 'm'), (': field 65, at byte 2264 = 0x8d8', 's')], size=14.5, anchor='start', fill=GREY)]
b += node(394, 58, [('slot 2, as loaded on that kernel', 16, 's', '700', INK), ('w4 = *(u32 *)(r1 + 0x8d8)', 15, 'm', None, INK)])
b.append(t(cx, 470, 'the kernel receives a plain load', size=15, weight='700'))
# no: a kernel without that field
RX, RW = 400, 272
b.append(line([(cx + DW, DY), (RX - 2, DY)], m + '-a', color=P2, width=2.2, dash='7 5'))
b += [t(cx + DW + 10, DY - 13, 'no', size=15.5, anchor='start', weight='700', fill=P2),
      t(RX, 195, 'a kernel without that field,', size=14.5, anchor='start', italic=True, fill=P2),
      t(RX, 213, 'say, after a rename', size=14.5, anchor='start', italic=True, fill=P2)]
b.append(rect(RX, DY - 30, RW, 60, stroke=P2, sw=1.6, dash='7 5'))
b += [t(RX + RW / 2, DY - 10, 'slot 2 becomes a call to', size=16, weight='700', fill=P2),
      t(RX + RW / 2, DY + 11, 'helper 195896080, "bad relo"', size=15, fam=UMONO, fill=P2)]
b += [line([(RX + RW / 2, DY + 30), (RX + RW / 2, DY + 60)], color=P2, width=2.2, dash='7 5'),
      f'<line x1="{RX + RW / 2 - 18}" y1="{DY + 61}" x2="{RX + RW / 2 + 18}" y2="{DY + 61}" stroke="{P2}" stroke-width="3"/>',
      t(RX + RW / 2, DY + 80, 'the load fails here:', size=15, weight='700', fill=P2),
      t(RX + RW / 2, DY + 99, 'failed to resolve CO-RE relocation …', size=14.5, fam=UMONO, fill=P2)]
# legend
b += [line([(400, 428), (440, 428)], width=2.2), t(448, 428, "on Ubuntu 20.04's 5.4 kernel", size=14.5, anchor='start'),
      line([(400, 452), (440, 452)], color=P2, width=2.2, dash='7 5'), t(448, 452, 'on a kernel without that field', size=14.5, anchor='start', fill=P2)]
fig_relo_print = svg(484, 'One CO-RE relocation in the fork tracer, from compile to load on two other kernels',
                     'Flowchart: slot 2 as compiled on 7.2 holds offset 0xb38 and a record asking for task_struct.pid. At load libbpf '
                     "looks up struct task_struct by name in the target kernel's BTF and asks whether it has a field named pid. Yes, on "
                     "Ubuntu 20.04's 5.4 kernel: slot 2 is rewritten with 0x8d8 and the kernel receives a plain load. No: slot 2 becomes a "
                     'call to helper 195896080 and the load fails.', b, m)
save('ch03-relo-print', fig_relo_print)
# ---------- Figure 3.1 for print: where vmlinux.h comes from, and the two reads of the kernel's types ----------
# Rows run left to right, one per place and time, top to bottom; the two reads of the kernel's types are thick, in the accent.
m = 'ah-3-1p'
b = [markers(m).replace('</defs>', f'<marker id="{m}-t" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4.6" markerHeight="4.6" '
                                    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{P2}"/></marker></defs>')]
TH = 2.8
NH = 52
def nd(x, w, y, l1, l2, m1=False, m2=False, sw=1.3):
    return [rect(x, y, w, NH, sw=sw),
            t(x + w / 2, y + NH / 2 - 10, l1, size=15 if m1 else 16, fam=UMONO if m1 else SANS, weight='700'),
            t(x + w / 2, y + NH / 2 + 11, l2, size=14.5, fam=UMONO if m2 else SANS, fill=GREY)]
def band(y, s_): return t(24, y, s_, size=14.5, anchor='start', italic=True, fill=GREY)
# the kernel build
R1 = 28
b.append(band(14, 'the kernel build: once per kernel'))
b += nd(24, 124, R1, 'kernel source', 'and its config') + nd(176, 124, R1, 'DWARF', 'compiler debug info')
b += nd(328, 124, R1, 'BTF', 'pahole converts it') + nd(480, 190, R1, '/sys/kernel/btf/vmlinux', '6.5 MB on kernel 7.2', m1=True)
for x1, x2 in [(148, 174), (300, 326), (452, 478)]:
    b.append(line([(x1, R1 + NH / 2), (x2, R1 + NH / 2)], m + '-k', width=1.5))
# the build machine
R2 = 130
b.append(band(116, 'the build machine: once per header'))
b += nd(30, 170, R2, 'bpftool btf dump', 'file … format c', m1=True, m2=True) + nd(228, 120, R2, 'vmlinux.h', '166,183 lines', m1=True)
b += nd(376, 120, R2, 'clang', 'notes each read') + nd(524, 146, R2, 'the .bpf.o', 'code + records')
for x1, x2 in [(200, 226), (348, 374), (496, 522)]:
    b.append(line([(x1, R2 + NH / 2), (x2, R2 + NH / 2)], m + '-k', width=1.5))
b.append(line([(575, R1 + NH), (575, 98), (10, 98), (10, R2 + NH / 2), (28, R2 + NH / 2)], m + '-t', color=P2, width=TH))   # read 1
# the machine that loads it
R3 = 232
b.append(band(218, 'the machine that loads it: at every start'))
b += nd(24, 190, R3, '/sys/kernel/btf/vmlinux', "that machine's kernel", m1=True)
b += nd(372, 298, R3, 'libbpf, at load', "answers each record from that kernel's types", sw=1.8)
b.append(line([(597, R2 + NH), (597, R3 - 2)], m + '-k', width=1.5))
b.append(line([(214, R3 + NH / 2), (370, R3 + NH / 2)], m + '-t', color=P2, width=TH))                                    # read 2
# legend
b += [line([(24, 312), (66, 312)], color=P2, width=TH), t(74, 312, "a read of the kernel's types", size=14.5, anchor='start'),
      line([(250, 312), (292, 312)], width=1.5), t(300, 312, 'feeds the next step', size=14.5, anchor='start')]
fig_hdr_print = svg(328, 'Where vmlinux.h comes from, and where the kernel types are read again',
                    "Three rows. The kernel build, once per kernel: kernel source and its config, DWARF, BTF made by pahole, published as "
                    "/sys/kernel/btf/vmlinux, 6.5 MB on kernel 7.2. The build machine, once per header: bpftool btf dump reads that file "
                    "and writes vmlinux.h, 166,183 lines; clang notes each read in the .bpf.o, code plus records. The machine that loads it, "
                    "at every start: libbpf reads that machine's /sys/kernel/btf/vmlinux and answers each record from that kernel's types.", b, m)
save('ch03-header', fig_hdr_print)
print('ch03 figures ok')
