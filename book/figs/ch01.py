import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *

figs = {}

# ---------------- Figure 1.1: two machines ----------------
m = 'ah-1-1'
rows = [
    (('A and X', 'two registers, 32 bits', True, 'gray'), ('r0 … r9', 'ten registers, 64 bits', True, 'teal')),
    (('a hidden frame pointer', 'the program cannot see it', False, 'gray'), ('r10', 'read-only frame pointer to the stack', True, 'teal')),
    (('scratch memory', 'a few words to park values in', False, 'gray'), ('stack', 'reached through r10; the key lives here', False, 'teal')),
    (('reads one packet', 'its only input', False, 'gray'), ('reads what r1 points at', 'the hook decides what that is', False, 'teal')),
    (('returns bytes to keep', '0 drops the packet', False, 'gray'), ('returns a value in r0', 'its meaning depends on the hook', False, 'teal')),
    (('no calls', 'the program is on its own', False, 'gray'), ('call', 'into helper functions in the kernel', True, 'coral')),
    (('no memory between packets', 'every run starts empty', False, 'gray'), ('maps', 'tables that outlive a run', True, 'coral')),
]
b = [text(165, 22, 'Classic BPF · 1993', size=14, col='gray', weight='600'),
     text(515, 22, 'eBPF · 2014', size=14, col='teal', weight='600')]
y0, step, h = 44, 54, 44
for i, (L, R) in enumerate(rows):
    y = y0 + i * step
    b.append(box(40, y, 250, h, L[3], L[0], L[1], mono1=L[2]))
    b.append(box(390, y, 250, h, R[3], R[0], R[1], mono1=R[2]))
    b.append(arrow(298, y + h / 2, 382, y + h / 2, m))
yb = y0 + len(rows) * step + 4
b.append(f'<rect x="40" y="{yb}" width="600" height="46" rx="6" fill="{C["gray"][0]}" stroke="{C["gray"][1]}" stroke-width="0.75"/>')
b.append(text(340, yb + 15, 'Both are a small machine inside the kernel that returns one value.', size=12, col='gray'))
b.append(text(340, yb + 32, 'The 2014 machine added width, a stack, calls into the kernel, and maps.', size=12, col='gray'))
figs['machines'] = svg(yb + 56, 'Classic BPF and eBPF side by side',
                       'Two columns comparing the 1993 classic BPF machine with the 2014 eBPF machine, row by row', b, m)

# ---------------- Figure 1.2: eight bytes ----------------
m = 'ah-1-2'
X0, BW = 40, 75   # one byte = 75 units
b = []
b.append(text(X0, 12, '1993 · classic BPF', size=11, col='gray', anchor='start', mono=True))
for (s, n, lab) in [(0, 2, 'op · 16 bits'), (2, 1, 'jt · 8'), (3, 1, 'jf · 8'), (4, 4, 'k · 32 bits')]:
    b.append(box(X0 + s * BW, 22, n * BW, 30, 'gray', lab, size1=11))
b.append(text(X0, 74, '2014 · eBPF, the same eight bytes cut differently', size=11, col='teal', anchor='start', mono=True))
fields = [(0, 1, 'teal', 'opcode', '8 bits'), (1, 1, 'amber', 'src · dst', '4 + 4 bits'),
          (2, 2, 'gray', 'offset', '16 bits, signed'), (4, 4, 'coral', 'immediate', '32 bits, signed')]
for (s, n, col, t1, t2) in fields:
    if col == 'amber':
        b.append(box(X0 + s * BW, 84, n * BW, 44, col))
        b.append(f'<line x1="{X0 + 1.5*BW}" y1="88" x2="{X0 + 1.5*BW}" y2="124" stroke="{C["amber"][1]}" stroke-width="0.8" stroke-dasharray="3 2"/>')
        for k, lab in [(0, 'src'), (1, 'dst')]:
            cx = X0 + (1.25 + 0.5 * k) * BW
            b.append(text(cx, 98, lab, size=12, col='amber', weight='600'))
            b.append(text(cx, 115, '4 bits', size=10, col='amber'))
    else:
        b.append(box(X0 + s * BW, 84, n * BW, 44, col, t1, t2, size1=12))
colof = ['teal', 'amber', 'gray', 'gray', 'coral', 'coral', 'coral', 'coral']

def byterow(y, label, hexes, notes, reads):
    out = [text(X0, y - 10, label, size=11, anchor='start', mono=True)]
    for i, hx in enumerate(hexes):
        out.append(box(X0 + i * BW, y, BW, 30, colof[i], hx, mono1=True, size1=13))
    for (s, n, t) in notes:
        for j, line in enumerate(t.split('\n')):
            out.append(text(X0 + (s + n / 2) * BW, y + 44 + j * 14, line, size=11))
    out.append(text(640, y - 10, reads, size=12, anchor='end', mono=True, weight='600', col='teal'))
    return out

b += byterow(176, 'slot 4 of the counter', ['bf', 'a2', '00', '00', '00', '00', '00', '00'],
             [(0, 1, 'move'), (1, 1, 'src r10\ndst r2'), (2, 2, 'unused'), (4, 4, 'unused')], 'reads as   r2 = r10')
b += byterow(272, 'slot 8 of the counter', ['85', '00', '00', '00', '01', '00', '00', '00'],
             [(0, 1, 'call'), (1, 1, 'unused'), (2, 2, 'unused'), (4, 4, '01 00 00 00 = 1, little-endian: helper 1')], 'reads as   call 1')
b.append(bar(338, 34, 'Every instruction has these five fields. The opcode says which of them it uses.'))
figs['encoding'] = svg(382, 'One eBPF instruction, field by field',
                       'An eight-byte instruction split into opcode, registers, offset and immediate, with two instructions from the learner\'s program decoded', b, m)

# ---------------- Figure 1.3: one helper call (step widget) ----------------
m = 'ah-1-3'
b = []
RW, GAP, RX = 50, 5, 40
def rx(i): return RX + i * (RW + GAP)
def rc(i): return rx(i) + RW / 2
RY, RH = 40, 40
for i in range(11):
    b.append(text(rc(i), 26, f'r{i}', size=11, mono=True, weight='600'))
# register contents per step
cells = {
    0: [('1,2', 'gray', '–'), ('3+', 'amber', 'value?')],
    1: [('1,2', 'coral', 'map'), ('3+', 'gray', '×')],
    2: [('1,2', 'teal', '&key'), ('3+', 'gray', '×')],
    3: [('1,2', 'gray', '–'), ('3+', 'gray', '×')],
    4: [('1,2', 'gray', '–'), ('3+', 'gray', '×')],
    5: [('1,2', 'gray', '–'), ('3+', 'gray', '×')],
    6: [(None, 'gray', '–')], 7: [(None, 'gray', '–')], 8: [(None, 'gray', '–')], 9: [(None, 'gray', '–')],
    10: [(None, 'teal', 'frame')],
}
for i, lst in cells.items():
    for (stp, col, t) in lst:
        b.append(box(rx(i), RY, RW, RH, col, t, mono1=True, size1=12, step=stp))
# brackets under the register row
def bracket(i0, i1, y, label, col, stp):
    x1, x2 = rx(i0), rx(i1) + RW
    d = C[col][1]
    return (f'<g data-step="{stp}"><path d="M{x1},{y} v6 H{x2} v-6" fill="none" stroke="{d}" stroke-width="1"/>'
            + text((x1 + x2) / 2, y + 18, label, size=11, col=col) + '</g>')
b.append(bracket(1, 5, RY + RH + 6, 'arguments go in r1 to r5', 'teal', '1'))
b.append(bracket(1, 5, RY + RH + 6, 'unreadable after the call', 'gray', '3+'))
b.append(bracket(6, 10, RY + RH + 6, 'r6 to r10 are kept across the call', 'gray', '3+'))
# helper box
HY = 128
b.append(box(205, HY, 270, 52, 'coral', 'bpf_map_lookup_elem', 'helper 1, runs in the kernel', mono1=True, size1=12, step='2+', sw=1.6))
b.append(arrow(rc(1), RY + RH + 2, 300, HY - 4, m, width=2.4, color=C['coral'][1], step='2'))
b.append(arrow(rc(2), RY + RH + 2, 330, HY - 4, m, width=2.4, color=C['coral'][1], step='2'))
b.append(f'<path d="M205,{HY + 26} H{rc(0)} V{RY + RH + 4}" fill="none" stroke="{C["amber"][1]}" stroke-width="2.4" marker-end="url(#{m})" data-step="3"/>')
b.append(text(130, HY + 38, 'the answer, in r0', size=11, col='amber', step='3'))
# the code line for each step
codes = [('1', 'slots 4 to 7:   r2 = r10 − 4   ·   r1 = the map'), ('2', 'slot 8:   call 1'),
         ('3', 'after slot 8:   r0 = pointer to the value, or 0'), ('4', 'slot 9:   if r0 == 0 goto +2')]
for stp, t in codes:
    b.append(text(340, 206, t, size=13, mono=True, weight='600', col='teal', step=stp))
b.append(text(340, 228, 'the program tests r0 before it reads through it; the kernel refuses a program that skips this test', size=11, step='4', italic=True))
b.append('<g data-step="4">' + bar(244, 30, 'Five registers in, one out. Whatever the program keeps across a call lives in r6 to r10.') + '</g>')
figs['helpercall'] = svg(284, 'One helper call, register by register',
                         'Eleven registers before and after the call to helper 1, with the helper box between them', b, m)


save('ch01-machines', figs['machines'])
save('ch01-helpercall', figs['helpercall'])
for i, f in enumerate(frames(figs['helpercall'], 'ah-1-3', (1, 3, 4), crop={1: 240, 3: 240}), 1):
    save(f'ch01-helpercall-twin{i}', f)
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

# ---------- Figure 1.4 for print: registers against moments, one grid (replaces the three frames) ----------
m = 'ah-1-4p'
b = [markers(m)]
LX, C0, CWD = 8, 150, 176              # label column from x=8; three moment columns of 176 from x=150
def ccx(j): return C0 + j * CWD + CWD / 2
heads = [('slots 4 to 7, before the call', []),
         ('after slot 8, the call', [('bpf_map_lookup_elem', 'm', INK), ('helper 1, runs in the kernel', 's', GREY)]),
         ('slot 9, the test', [('if r0 == 0 goto +2', 'm', INK)])]
for j, (h1, more) in enumerate(heads):
    b.append(t(ccx(j), 16, h1, size=16, weight='700'))
    for k, (s_, f, col) in enumerate(more):
        b.append(t(ccx(j), 37 + k * 19, s_, size=15 if f == 'm' else 14.5, fam=UMONO if f == 'm' else SANS, fill=col))
HB = 82                                 # the rule under the heads
b.append(f'<line x1="{LX}" y1="{HB}" x2="676" y2="{HB}" stroke="{INK}" stroke-width="1.3"/>')
for j in (1, 2):
    b.append(f'<line x1="{C0 + j * CWD}" y1="6" x2="{C0 + j * CWD}" y2="{HB - 6}" stroke="#C9CCCF" stroke-width="1"/>')
X5, DASH4 = '×  ×  ×  ×  ×', '–  –  –  –'
rows = [  # register label, what it is, height, cells (each a list of lines: parts, size, fill)
    ('r0', 'the answer', 60,
     [[([('–', 'm')], 15, GREY)],
      [([('value?', 'm')], 16, P2), ([('pointer to the value, or 0', 's')], 14.5, P2)],
      [([('value?', 'm')], 16, P2), ([('tested here, before the', 's')], 14.5, P2), ([('program reads through it', 's')], 14.5, P2)]]),
    ('r1 to r5', 'the arguments', 74,
     [[([('r1', 'm'), (' = the map', 's')], 15, INK), ([('r2 = &key = r10 − 4', 'm')], 15, INK), ([('r3', 'm'), (' to ', 's'), ('r5', 'm'), (': –', 's')], 15, GREY)],
      [([(X5, 'm')], 15, INK), ([('unreadable after the call', 's')], 14.5, GREY)],
      [([(X5, 'm')], 15, INK)]]),
    ('r6 to r9', '', 56,
     [[([(DASH4, 'm')], 15, GREY)],
      [([(DASH4, 'm')], 15, GREY), ([('kept across the call', 's')], 14.5, GREY)],
      [([(DASH4, 'm')], 15, GREY)]]),
    ('r10', 'frame pointer', 56,
     [[([('frame', 'm')], 15, INK)],
      [([('frame', 'm')], 15, INK), ([('kept across the call', 's')], 14.5, GREY)],
      [([('frame', 'm')], 15, INK)]]),
]
y = HB
for i, (reg, what, h, cells_) in enumerate(rows):
    acc = reg == 'r0'
    b.append(t(LX + 4, y + h / 2 - (9 if what else 0), reg, size=16, anchor='start', fam=UMONO, weight='700', fill=P2 if acc else INK))
    if what:
        b.append(t(LX + 4, y + h / 2 + 11, what, size=14.5, anchor='start', fill=P2 if acc else GREY))
    for j, lines in enumerate(cells_):
        n = len(lines)
        for k, (parts, size, fill) in enumerate(lines):
            b.append(tm(ccx(j), y + h / 2 + (k - (n - 1) / 2) * 19, parts, size=size, fill=fill))
    for j in (1, 2):
        b.append(f'<line x1="{C0 + j * CWD}" y1="{y + 6}" x2="{C0 + j * CWD}" y2="{y + h - 6}" stroke="#C9CCCF" stroke-width="1"/>')
    y += h
    b.append(f'<line x1="{LX}" y1="{y}" x2="676" y2="{y}" stroke="{INK if i == len(rows) - 1 else "#C9CCCF"}" stroke-width="{1.3 if i == len(rows) - 1 else 1}"/>')
b.append(t(676, y + 18, 'the kernel refuses a program that skips this test', size=14.5, anchor='end', italic=True, fill=P2))
fig_call_print = svg(y + 32, 'One helper call, register by register, at three moments',
                     'A grid of the registers r0, r1 to r5, r6 to r9 and r10 against three moments. Before the call, at slots 4 to 7, '
                     'r1 holds the map and r2 the key\'s address, r10 minus 4. After the call to bpf_map_lookup_elem at slot 8, r0 holds a '
                     'pointer to the value or 0, r1 to r5 cannot be read, and r6 to r10 are kept. At slot 9 the program tests r0.', b, m)
save('ch01-helpercall-print', fig_call_print)
# ---------- Figure 1.2 for print: eight bytes, two ways to cut them, and two slots of the counter ----------
# The bytes an instruction uses are in bold, in the accent, with a heavier outline; unused bytes are grey.
m = 'ah-1-2p'
b = []
X0, BW = 20, 80                       # one byte = 80 units, from x=20 to 660
def bx(i): return X0 + i * BW
b.append(t(X0, 12, '1993 · classic BPF', size=14.5, anchor='start', italic=True, fill=GREY))
for s_, n, lab in [(0, 2, 'op · 16 bits'), (2, 1, 'jt · 8'), (3, 1, 'jf · 8'), (4, 4, 'k · 32 bits')]:
    b += [rect(bx(s_), 24, n * BW - 4, 34, stroke=GREY, sw=1.1), t(bx(s_) + (n * BW - 4) / 2, 41, lab, size=15, fill=GREY)]
b.append(t(X0, 80, '2014 · eBPF, the same eight bytes cut differently', size=14.5, anchor='start', italic=True, fill=INK))
for s_, n, t1, t2 in [(0, 1, 'opcode', '8 bits'), (2, 2, 'offset', '16 bits, signed'), (4, 4, 'immediate', '32 bits, signed')]:
    cx = bx(s_) + (n * BW - 4) / 2
    b += [rect(bx(s_), 92, n * BW - 4, 48), t(cx, 107, t1, size=16, weight='700'), t(cx, 126, t2, size=14.5, fill=GREY)]
b.append(rect(bx(1), 92, BW - 4, 48))
b.append(f'<line x1="{bx(1) + 38}" y1="96" x2="{bx(1) + 38}" y2="136" stroke="{GREY}" stroke-width="1" stroke-dasharray="3 2"/>')
for k, lab in enumerate(['src', 'dst']):
    cx = bx(1) + 19 + 38 * k
    b += [t(cx, 107, lab, size=16, weight='700'), t(cx, 126, '4 bits', size=14.5, fill=GREY)]
FIELDS = [(0, 1), (1, 1), (2, 2), (4, 4)]   # opcode, registers, offset, immediate
def byterow(y, label, reads, hexes, used, notes):
    out = [t(X0, y - 14, label, size=14.5, anchor='start', italic=True, fill=GREY),
           f'<text x="660" y="{y - 14}" text-anchor="end" dominant-baseline="central" font-size="15" fill="{INK}" xml:space="preserve">'
           f'<tspan font-family="{SANS}" font-style="italic" fill="{GREY}">reads as  </tspan><tspan font-family="{UMONO}" font-weight="700">{esc(reads)}</tspan></text>']
    for i, hx in enumerate(hexes):
        u = any(s_ <= i < s_ + n for (s_, n) in [FIELDS[f] for f in used])
        out += [rect(bx(i), y, BW - 4, 34, stroke=P2 if u else GREY, sw=2 if u else 1),
                t(bx(i) + (BW - 4) / 2, y + 17, hx, size=16, fam=UMONO, weight='700' if u else None, fill=P2 if u else GREY)]
    for f, lines in notes:
        s_, n = FIELDS[f]
        for j, ln in enumerate(lines):
            out.append(t(bx(s_) + (n * BW - 4) / 2, y + 50 + j * 18, ln, size=14.5, fill=INK if f in used else GREY))
    return out
b += byterow(178, 'slot 4 of the counter', 'r2 = r10', ['bf', 'a2', '00', '00', '00', '00', '00', '00'], (0, 1),
             [(0, ['move']), (1, ['src r10', 'dst r2']), (2, ['unused']), (3, ['unused'])])
b += byterow(296, 'slot 8 of the counter', 'call 1', ['85', '00', '00', '00', '01', '00', '00', '00'], (0, 3),
             [(0, ['call']), (1, ['unused']), (2, ['unused']), (3, ['01 00 00 00 = 1, little-endian: helper 1'])])
fig_enc_print = svg(366, 'One eBPF instruction, field by field',
                    'Eight bytes cut two ways: the 1993 layout, op 16 bits, jt 8, jf 8, k 32 bits; the 2014 layout, opcode 8 bits, '
                    'src and dst 4 bits each, offset 16 bits signed, immediate 32 bits signed. Slot 4 of the counter, bf a2 then six zero '
                    'bytes, reads as r2 = r10: a move, src r10, dst r2, offset and immediate unused. Slot 8, 85 00 00 00 01 00 00 00, '
                    'reads as call 1: the immediate 01 00 00 00 is 1, little-endian, helper 1.', b, m)
save('ch01-encoding', fig_enc_print)
print('ch01 figures ok')
