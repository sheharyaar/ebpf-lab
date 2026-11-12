import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *

figs = {}

# ---------------- Figure 1.1: two machines ----------------
m = 'ah-1-1'
rows = [
    (('A and X', 'two registers, 32 bits', True, 'gray'), ('r0 … r9', 'ten registers, 64 bits', True, 'teal')),
    (('a hidden frame pointer', 'the program cannot see it', False, 'gray'), ('r10', 'read-only frame pointer to the stack', True, 'teal')),
    (('scratch memory', 'a few words to park values in', False, 'gray'), ('stack', 'reached through r10; your key lives here', False, 'teal')),
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

b += byterow(176, 'your slot 4', ['bf', 'a2', '00', '00', '00', '00', '00', '00'],
             [(0, 1, 'move'), (1, 1, 'src r10\ndst r2'), (2, 2, 'unused'), (4, 4, 'unused')], 'reads as   r2 = r10')
b += byterow(272, 'your slot 8', ['85', '00', '00', '00', '01', '00', '00', '00'],
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
save('ch01-encoding', figs['encoding'])
save('ch01-helpercall', figs['helpercall'])
for i, f in enumerate(frames(figs['helpercall'], 'ah-1-3', (1, 3, 4), crop={1: 240, 3: 240}), 1):
    save(f'ch01-helpercall-twin{i}', f)
print('ch01 figures ok')
