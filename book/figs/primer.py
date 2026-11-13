# Figures for the primer: registers and instructions (hand SVG, 680 wide, palette from common.C).
# Teal: registers; coral: memory; amber: what a call destroys or what to count; grey: context.
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *

figs = {}


def dots(x, y, n):  # n memory accesses, drawn right to left from x
    return ''.join(f'<circle cx="{x - k * 9}" cy="{y}" r="3.2" fill="{C["coral"][1]}"/>' for k in range(n))


# ---------------- Figure P.1: a = (b + c) * d on three machines ----------------
m = 'ah-P-1'
b = []
cols = [
    (12, 'Stack machine', 'WebAssembly, from clang --target=wasm32',
     ('coral', 'b, c, d in locals 0, 1, 2', 'the operand stack is memory too'),
     [('local.get 1', 'stack: c', 2), ('local.get 0', 'stack: c b', 2), ('i64.add', 'stack: b+c', 3),
      ('local.get 2', 'stack: b+c d', 2), ('i64.mul', 'stack: a', 3)],
     'a is left on top of the stack', '5 instructions · 12 accesses'),
    (240, 'Accumulator machine', 'classic BPF, the 1993 machine',
     ('coral', 'b, c, d in scratch M[1]–M[3]', 'only A and X are registers'),
     [('ld M[1]', 'A = b', 1), ('ldx M[2]', 'X = c', 1), ('add x', 'A = b+c', 0),
      ('ldx M[3]', 'X = d', 1), ('mul x', 'A = a', 0)],
     'a is left in A', '5 instructions · 3 accesses'),
    (468, 'Register machine', 'eBPF, from clang -target bpf',
     ('teal', 'b, c, d in r1, r2, r3', 'ten registers to hold values'),
     [('r0 = r2', 'r0 = c', 0), ('r0 += r1', 'r0 = b+c', 0), ('r0 *= r3', 'r0 = a', 0)],
     'a is left in r0', '3 instructions · 0 accesses'),
]
W = 200
for (x0, title, sub, start, rows, left, total) in cols:
    cx = x0 + W / 2
    b.append(text(cx, 14, title, size=13, weight='600'))
    b.append(text(cx, 31, sub, size=10.5, col='gray', italic=True))
    col, t1, t2 = start
    b.append(box(x0, 42, W, 38, col))
    b.append(text(cx, 55, t1, size=11, col=col, weight='600'))
    b.append(text(cx, 70, t2, size=10.5, col=col))
    for k, (ins, note, n) in enumerate(rows):
        y = 92 + k * 26
        b.append(f'<rect x="{x0}" y="{y}" width="{W}" height="22" rx="4" fill="#FFFFFF" stroke="{C["gray"][1]}" stroke-width="0.6"/>')
        b.append(text(x0 + 8, y + 11, ins, size=11, mono=True, anchor='start', col='teal' if x0 == 468 else None))
        b.append(text(x0 + 92, y + 11, note, size=10.5, anchor='start', col='gray'))
        b.append(dots(x0 + 190, y + 11, n))
    b.append(text(cx, 232, left, size=10.5, col='gray', italic=True))
    b.append(box(x0, 246, W, 26, 'amber', total, size1=11.5))
# the same line on two hardware ISAs, under the eBPF rows
b.append(f'<rect x="468" y="170" width="{W}" height="48" rx="4" fill="none" stroke="{C["gray"][1]}" stroke-width="0.6" stroke-dasharray="3 3"/>')
b.append(text(476, 181, 'the same line on hardware:', size=10.5, anchor='start', col='gray', italic=True))
b.append(text(476, 196, 'x86-64', size=10.5, anchor='start', col='gray'))
b.append(text(530, 196, 'leaq; imulq', size=10.5, mono=True, anchor='start', col='gray'))
b.append(text(476, 210, 'RISC-V', size=10.5, anchor='start', col='gray'))
b.append(text(530, 210, 'add; mul', size=10.5, mono=True, anchor='start', col='gray'))
# legend for the dots
b.append(dots(52, 292, 1))
b.append(text(60, 292, 'one read or write of memory, counted with the operand stack in memory and A, X, r0–r3 in processor registers',
              size=10.5, anchor='start', col='gray'))
b.append(bar(306, 28, 'The more values a machine can name in registers, the fewer trips it makes to memory: 12, then 3, then 0.'))
figs['machines'] = svg(342, 'a = (b + c) * d on a stack machine, an accumulator machine and a register machine',
                       'Three columns of instructions for the same expression, with memory accesses marked as coral dots: 12, 3 and 0', b, m)

# ---------------- Figure P.3: registers across a call, and the stack below r10 ----------------
m = 'ah-P-3'
b = []
regs = [('r0', 'rax', 'return value'), ('r1', 'rdi', 'argument 1'), ('r2', 'rsi', 'argument 2'), ('r3', 'rdx', 'argument 3'),
        ('r4', 'rcx', 'argument 4'), ('r5', 'r8', 'argument 5'), ('r6', 'rbx', 'long-lived values'), ('r7', 'r13', ''),
        ('r8', 'r14', ''), ('r9', 'r15', ''), ('r10', 'rbp', 'frame pointer')]
Y0, STEP, H = 40, 25, 21
b.append(text(48, 16, 'eBPF', size=12, weight='600'))
b.append(text(150, 16, 'role', size=12, weight='600'))
b.append(text(232, 16, 'x86-64', size=12, weight='600'))
b.append(text(343, 16, 'after a call', size=12, weight='600'))
for k, (e, x, role) in enumerate(regs):
    y = Y0 + k * STEP
    col = 'amber' if k <= 5 else ('teal' if k <= 9 else 'gray')
    b.append(box(18, y, 60, H, col, e, mono1=True, size1=11.5))
    if role: b.append(text(92, y + H / 2, role, size=10.5, anchor='start'))
    b.append(box(202, y, 60, H, col, x, mono1=True, size1=11.5))
# grouped verdicts: caller-saved, callee-saved, frame pointer
groups = [(0, 5, 'amber', ['caller-saved', 'a call may overwrite', 'all six; r0 comes back', 'holding the result']),
          (6, 9, 'teal', ['callee-saved', 'a call hands them', 'back unchanged']),
          (10, 10, 'gray', ['never written'])]
for (a, z, col, lines) in groups:
    y1, y2 = Y0 + a * STEP, Y0 + z * STEP + H
    b.append(box(276, y1, 136, y2 - y1, col))
    mid = (y1 + y2) / 2 - (len(lines) - 1) * 7.5
    for i, t in enumerate(lines):
        b.append(text(344, mid + i * 15, t, size=11 if i == 0 else 10.5, col=col, weight='600' if i == 0 else None))
b.append(text(18, 326, 'x86-64 registers with no eBPF partner: r9 (sixth argument), r10, r11, r12, rsp',
              size=10.5, anchor='start', col='gray'))
# the stack below r10
SX, SW = 470, 190
b.append(text(SX + SW / 2, 16, 'the stack: 512 bytes below r10', size=12, weight='600'))
b.append(text(SX - 6, 40, 'r10 →', size=11, mono=True, anchor='end', col='teal'))
b.append(f'<line x1="{SX}" y1="40" x2="{SX + SW}" y2="40" stroke="{C["teal"][1]}" stroke-width="1.6"/>')
slots = [('r10 − 8', 'a local variable'), ('r10 − 16', 'a spilled register'), ('r10 − 24', 'free')]
for k, (off, what) in enumerate(slots):
    y = 42 + k * 30
    b.append(box(SX, y, SW, 26, 'coral'))
    b.append(text(SX + 10, y + 13, off, size=11, mono=True, anchor='start', col='coral'))
    b.append(text(SX + SW - 10, y + 13, what, size=10.5, anchor='end', col='coral'))
b.append(f'<rect x="{SX}" y="132" width="{SW}" height="56" rx="6" fill="{C["coral"][0]}" stroke="{C["coral"][1]}" stroke-width="0.9" stroke-dasharray="4 3"/>')
b.append(text(SX + SW / 2, 160, '… 60 more 8-byte slots …', size=10.5, col='coral'))
b.append(box(SX, 192, SW, 26, 'coral'))
b.append(text(SX + 10, 205, 'r10 − 512', size=11, mono=True, anchor='start', col='coral'))
b.append(text(SX + SW - 10, 205, 'the last slot', size=10.5, anchor='end', col='coral'))
b.append(arrow(SX + SW + 8, 50, SX + SW + 8, 214, m, color=C['gray'][1]))
b.append(text(SX + SW + 4, 228, 'lower addresses', size=10, anchor='end', col='gray', italic=True))
b.append(text(SX, 252, 'spill:', size=10.5, anchor='start', col='amber', weight='600'))
b.append(text(SX + 36, 252, '*(u64 *)(r10 - 16) = r1', size=10.5, mono=True, anchor='start'))
b.append(text(SX, 272, 'fill:', size=10.5, anchor='start', col='amber', weight='600'))
b.append(text(SX + 36, 272, 'r1 = *(u64 *)(r10 - 16)', size=10.5, mono=True, anchor='start'))
b.append(text(SX, 296, 'r10 is read-only, so each slot keeps', size=10.5, anchor='start', col='gray'))
b.append(text(SX, 311, 'one name for the whole function', size=10.5, anchor='start', col='gray'))
b.append(bar(338, 28, 'A call may destroy r0 to r5; r6 to r9 and r10 come back unchanged.'))
figs['regs'] = svg(374, 'eBPF registers beside their x86-64 partners, what a call does to each, and the stack below r10',
                   'Eleven eBPF registers with x86-64 partners grouped as caller-saved, callee-saved and frame pointer; on the right the 512-byte stack', b, m)

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
def rect(x, y, w, h, stroke=INK, sw=1.3, rx=5, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="#FFFFFF" stroke="{stroke}" stroke-width="{sw}"{da}/>'
def pdots(x, y, n):  # n memory accesses, in the accent, drawn right to left from x
    return ''.join(f'<circle cx="{x - k * 11}" cy="{y}" r="4" fill="{P2}"/>' for k in range(n))

# ---------- Figure P.1 for print: a = (b + c) * d on three machines ----------
# The accent marks memory: one dot per read or write.
m = 'ah-P-1p'
b = []
PW = 212
for (x0, title, sub, start, rows, left, total) in zip((8, 234, 460), *zip(*[c[1:] for c in cols])):
    cxp = x0 + PW / 2
    b += [t(cxp, 14, title, size=16, weight='700'), t(cxp, 34, sub, size=14.5, italic=True, fill=GREY)]
    _, s1, s2 = start
    b += [rect(x0, 48, PW, 46), t(cxp, 62, s1, size=15, weight='700'), t(cxp, 81, s2, size=14.5, fill=GREY)]
    for k, (ins, note, n) in enumerate(rows):
        y = 104 + k * 31
        b += [rect(x0, y, PW, 26, stroke=GREY, sw=1, rx=4), t(x0 + 10, y + 13, ins, size=15, anchor='start', fam=UMONO),
              t(x0 + 100, y + 13, note, size=14.5, anchor='start', fill=GREY), pdots(x0 + PW - 12, y + 13, n)]
    b += [t(cxp, 278, left, size=14.5, italic=True, fill=GREY),
          rect(x0, 292, PW, 30, sw=1.8), t(cxp, 307, total, size=15, weight='700')]
# the same line on two hardware ISAs, under the eBPF rows
b += [rect(460, 198, PW, 62, stroke=GREY, sw=1, rx=4, dash='4 3'),
      t(470, 213, 'the same line on hardware:', size=14.5, anchor='start', italic=True, fill=GREY),
      t(470, 231, 'x86-64', size=14.5, anchor='start', fill=GREY), t(530, 231, 'leaq; imulq', size=15, anchor='start', fam=UMONO, fill=GREY),
      t(470, 249, 'RISC-V', size=14.5, anchor='start', fill=GREY), t(530, 249, 'add; mul', size=15, anchor='start', fam=UMONO, fill=GREY)]
# legend for the dots
b += [pdots(16, 344, 1), t(28, 344, 'one read or write of memory, counted with the operand stack in memory and A, X, r0–r3 in processor registers',
                               size=14.5, anchor='start')]
figs['machines_print'] = svg(360, 'a = (b + c) * d on a stack machine, an accumulator machine and a register machine',
                             'Three columns for the same expression. Stack machine, WebAssembly from clang --target=wasm32, b, c, d in locals '
                             '0, 1, 2: local.get 1, local.get 0, i64.add, local.get 2, i64.mul, leaving a on top of the stack; 5 instructions, '
                             '12 memory accesses. Accumulator machine, classic BPF, b, c, d in scratch M[1] to M[3]: ld M[1], ldx M[2], add x, '
                             'ldx M[3], mul x, leaving a in A; 5 instructions, 3 accesses. Register machine, eBPF from clang -target bpf, b, c, d '
                             'in r1, r2, r3: r0 = r2, r0 += r1, r0 *= r3, leaving a in r0; 3 instructions, 0 accesses; on hardware the same line '
                             'is leaq; imulq on x86-64 and add; mul on RISC-V.', b, m)
save('primer-machines', figs['machines_print'])

# ---------- Figure P.3 for print: registers across a call, and the stack below r10 ----------
# The accent marks the registers a call may overwrite, with a heavy bracket.
m = 'ah-P-3p'
b = [markers(m)]
RY0, RP = 44, 25                       # first row centre, row pitch
b += [t(12, 14, 'eBPF', size=15, anchor='start', weight='700'), t(60, 14, 'role', size=15, anchor='start', weight='700'),
      t(170, 14, 'x86-64', size=15, anchor='start', weight='700'), t(236, 14, 'after a call', size=15, anchor='start', weight='700'),
      f'<line x1="8" y1="28" x2="396" y2="28" stroke="{INK}" stroke-width="1.3"/>']
for k, (e, x, role) in enumerate(regs):
    y = RY0 + k * RP
    acc = k <= 5
    b += [t(12, y, e, size=15, anchor='start', fam=UMONO, weight='700', fill=P2 if acc else INK),
          t(60, y, role, size=14.5, anchor='start', fill=GREY) if role else '',
          t(170, y, x, size=15, anchor='start', fam=UMONO, fill=P2 if acc else INK)]
for k in (6, 10):
    yb = RY0 + k * RP - RP / 2
    b.append(f'<line x1="8" y1="{yb}" x2="396" y2="{yb}" stroke="#C9CCCF" stroke-width="1"/>')
b.append(f'<line x1="8" y1="{RY0 + 10.5 * RP}" x2="396" y2="{RY0 + 10.5 * RP}" stroke="{INK}" stroke-width="1.3"/>')
pgroups = [(0, 5, P2, 3, ['caller-saved', 'a call may overwrite', 'all six; r0 comes back', 'holding the result']),
           (6, 9, INK, 1.3, ['callee-saved', 'a call hands them', 'back unchanged']),
           (10, 10, GREY, 1.3, ['never written'])]
for (a_, z, col, sw, lines) in pgroups:
    y1, y2 = RY0 + a_ * RP - 9, RY0 + z * RP + 9
    b.append(f'<path d="M222,{y1} h6 V{y2} h-6" fill="none" stroke="{col}" stroke-width="{sw}"/>')
    mid = (y1 + y2) / 2 - (len(lines) - 1) * 9
    for i, s_ in enumerate(lines):
        b.append(t(238, mid + i * 18, s_, size=15 if i == 0 else 14.5, anchor='start', weight='700' if i == 0 else None,
                   fill=col if i == 0 else (P2 if col == P2 else GREY)))
b.append(t(8, 328, 'x86-64 registers with no eBPF partner: r9 (sixth argument), r10, r11, r12, rsp', size=14.5, anchor='start', fill=GREY))
# the stack below r10
SX3, SW3 = 452, 186
b.append(t(SX3 + SW3 / 2, 14, 'the stack: 512 bytes below r10', size=15, weight='700'))
b += [t(SX3 - 8, 40, 'r10', size=15, anchor='end', fam=UMONO, weight='700'),
      f'<line x1="{SX3}" y1="40" x2="{SX3 + SW3}" y2="40" stroke="{INK}" stroke-width="2.4"/>']
for k, (off, what) in enumerate([('r10 − 8', 'a local variable'), ('r10 − 16', 'a spilled register'), ('r10 − 24', 'free')]):
    y = 42 + k * 30
    b += [rect(SX3, y, SW3, 28, rx=3), t(SX3 + 8, y + 14, off, size=15, anchor='start', fam=UMONO),
          t(SX3 + SW3 - 8, y + 14, what, size=14.5, anchor='end', fill=GREY)]
b += [rect(SX3, 134, SW3, 52, rx=3, stroke=GREY, sw=1, dash='4 3'), t(SX3 + SW3 / 2, 160, '… 60 more 8-byte slots …', size=14.5, fill=GREY),
      rect(SX3, 190, SW3, 28, rx=3), t(SX3 + 8, 204, 'r10 − 512', size=15, anchor='start', fam=UMONO),
      t(SX3 + SW3 - 8, 204, 'the last slot', size=14.5, anchor='end', fill=GREY)]
b += [line([(SX3 + SW3 + 18, 46), (SX3 + SW3 + 18, 214)], m + '-k', width=1.5),
      t(676, 234, 'lower addresses', size=14.5, anchor='end', italic=True, fill=GREY)]
b += [t(SX3 - 30, 262, 'spill:', size=15, anchor='start', weight='700'), t(SX3 + 14, 262, '*(u64 *)(r10 - 16) = r1', size=15, anchor='start', fam=UMONO),
      t(SX3 - 30, 284, 'fill:', size=15, anchor='start', weight='700'), t(SX3 + 14, 284, 'r1 = *(u64 *)(r10 - 16)', size=15, anchor='start', fam=UMONO),
      t(SX3 - 30, 312, 'r10 is read-only, so each slot keeps', size=14.5, anchor='start', fill=GREY),
      t(SX3 - 30, 330, 'one name for the whole function', size=14.5, anchor='start', fill=GREY)]
figs['regs_print'] = svg(344, 'eBPF registers beside their x86-64 partners, what a call does to each, and the stack below r10',
                         'Left: r0 return value, rax; r1 to r5 arguments 1 to 5, rdi, rsi, rdx, rcx, r8: caller-saved, a call may overwrite '
                         'all six, r0 comes back holding the result. r6 to r9, long-lived values, rbx, r13, r14, r15: callee-saved, a call '
                         'hands them back unchanged. r10, frame pointer, rbp: never written. x86-64 registers with no eBPF partner: r9, r10, '
                         'r11, r12, rsp. Right: the 512-byte stack below r10, r10 − 8 a local variable, r10 − 16 a spilled register, '
                         'r10 − 24 free, 60 more 8-byte slots, r10 − 512 the last slot, toward lower addresses; a spill '
                         '*(u64 *)(r10 - 16) = r1 and a fill r1 = *(u64 *)(r10 - 16).', b, m)
save('primer-regs', figs['regs_print'])
print('primer figures ok')
