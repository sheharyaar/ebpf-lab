# Chapter 4 figures: the promise, the walk (step widget), one register's state.
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *

figs = {}

# ---------- Figure 4.1: the promise, as an absence list ----------
m = 'ah-4-1'
b = []
b.append(tx(40, 14, 'A program the kernel has loaded never …', size=12, col='coral', anchor='start', weight='600'))
b.append(tx(420, 14, 'how the kernel made sure, at load time', size=12, col='teal', anchor='start', weight='600'))
rows = [
    ('jumps outside itself, or keeps code', 'that no path can reach', 'gray', 'the shape check, before the walk', 'one look at every jump'),
    ('reads a register it never wrote', None, 'teal', 'the walk: every register has a type,', 'and "never written" is one of them'),
    ('reads through a pointer that may be NULL', None, 'teal', 'the walk: the pointer stays "maybe NULL"', 'until a test on that path removes it'),
    ('reads or writes outside the memory', 'it was given', 'teal', 'the walk: every pointer carries the size', 'of what it points at'),
    ('calls a helper its program type does not', 'allow, or with the wrong arguments', 'teal', 'the walk: each call is checked against', 'the helper\'s list of argument types'),
    ('runs without end', None, 'teal', 'the walk must reach every exit within', 'one million instructions'),
]
y = 30
for (l1, l2, col, r1, r2) in rows:
    b.append(box(40, y, 330, 44, 'gray'))
    b.append(tx(56, y + 22 if not l2 else y + 14, l1, size=12, anchor='start', col='gray'))
    if l2: b.append(tx(56, y + 30, l2, size=12, anchor='start', col='gray'))
    b.append(box(400, y, 240, 44, col))
    b.append(tx(414, y + 14, r1, size=11, anchor='start', col=col))
    b.append(tx(414, y + 30, r2, size=11, anchor='start', col=col))
    b.append(arrow(372, y + 22, 398, y + 22, m, width=1.0))
    y += 52
b.append(bar(y + 4, 32, 'Proved for every path before the program runs once. Whether it counts what you meant is not checked.'))
figs['promise'] = svg(y + 46, 'What a loaded program never does, and how the kernel made sure',
                      'Six things a loaded eBPF program never does, each paired with the load-time check that rules it out', b, m)

# ---------- Figure 4.2: the walk over the learner's program (step widget, three frames) ----------
m = 'ah-4-2'
b = []
T = C['teal'][1]
# frame labels
for k, lab in [(1, '1 · the first path, as far as the branch'), (2, '2 · the first path, on to the exit'),
               (3, '3 · back for the second path')]:
    b.append(tx(20, 12, lab, size=12, anchor='start', weight='600', col='teal', step=str(k)))
# program blocks
b.append(box(20, 44, 150, 50, 'gray', 'slots 0 to 8', 'key on the stack · look up', mono1=True, size1=12))
b.append(box(196, 47, 104, 44, 'gray', 'slot 9', 'is r0 == 0 ?', mono1=True, size1=12))
b.append(box(334, 24, 120, 40, 'gray', 'slots 10, 11', 'read count · add', mono1=True, size1=11))
b.append(box(488, 44, 172, 50, 'gray', 'slots 12 to 26', 'print · update · exit', mono1=True, size1=12))
# plain connectors
b.append(arrow(172, 69, 194, 69, m, width=1.0))
b.append(arrow(302, 60, 332, 46, m, width=1.0))
b.append(arrow(456, 44, 486, 56, m, width=1.0))
b.append(f'<path d="M248,93 V124 H520 V96" fill="none" stroke="{LINE}" stroke-width="1" marker-end="url(#{m})"/>')
b.append(tx(310, 36, 'r0 ≠ 0', size=10, mono=True))
b.append(tx(384, 134, 'r0 == 0: jump to slot 12', size=10, mono=True))
# thick teal overlays per frame
b.append(f'<path d="M24,100 H166" stroke="{T}" stroke-width="3.2" fill="none" data-step="1,2"/>')
b.append(arrow(172, 69, 194, 69, m, width=2.4, color=T, step='1,2'))
b.append(arrow(302, 60, 332, 46, m, width=2.4, color=T, step='2'))
b.append(arrow(456, 44, 486, 56, m, width=2.4, color=T, step='2'))
b.append(f'<path d="M492,100 H656" stroke="{T}" stroke-width="3.2" fill="none" data-step="2"/>')
b.append(f'<path d="M248,93 V124 H520 V96" fill="none" stroke="{T}" stroke-width="2.4" marker-end="url(#{m})" data-step="3"/>')
b.append(f'<path d="M524,100 H600" stroke="{T}" stroke-width="3.2" fill="none" data-step="3"/>')
# saved states (amber tags)
A = C['amber']
def tag(x, y, t, step):
    return (f'<g data-step="{step}"><rect x="{x}" y="{y}" width="58" height="18" rx="4" fill="{A[0]}" stroke="{A[1]}" stroke-width="1"/>'
            + tx(x + 29, y + 9, t, size=10, col='amber', mono=True) + '</g>')
b.append(tag(219, 26, 'saved', '1+'))
b.append(tag(590, 24, 'saved 25', '2+'))
b.append(f'<g data-step="3"><rect x="602" y="92" width="74" height="18" rx="4" fill="{A[0]}" stroke="{A[1]}" stroke-width="1.4"/>'
         + tx(639, 101, '25: safe', size=10, col='amber', mono=True, weight='600') + '</g>')
# status row
SY = 150
heads = ['r0 here', 'paths waiting', 'saved states', 'instructions walked']
xs = [20, 190, 360, 520]
ws = [160, 160, 150, 140]
for x, w, h in zip(xs, ws, heads):
    b.append(box(x, SY, w, 52, 'gray'))
    b.append(tx(x + w / 2, SY + 13, h, size=10, col='gray'))
vals = {
    1: ['maybe NULL', 'slot 12, r0 = 0', 'at slot 9', '9'],
    2: ['a map value', 'slot 12, r0 = 0', 'at slots 9, 25', '24'],
    3: ['0, never read', 'none', 'at slots 9, 25', '36'],
}
for k, vs in vals.items():
    for i, (x, w, v) in enumerate(zip(xs, ws, vs)):
        col = 'amber' if i == 0 else 'teal'
        b.append(tx(x + w / 2, SY + 34, v, size=12, col=col, mono=(i == 3 or 'slot' in v), weight='600', step=str(k)))
figs['walk'] = svg(212, 'The kernel walking both paths of your write counter',
                   'Program blocks for slots 0 to 26 with the path being walked drawn thick, the saved states, and a status row', b, m)

# ---------- Figure 4.3: one register's state, part by part ----------
m = 'ah-4-3'
b = []
b.append(tx(20, 14, 'after slot 8, the call to the map lookup, the kernel writes down:', size=11, anchor='start', col='gray'))
toks = [('R0=', 'gray'), ('map_value', 'teal'), ('_or_null', 'amber'), ('(', 'gray'), ('id=1', 'teal'), (',', 'gray'),
        ('map=write_counts', 'teal'), (',', 'gray'), ('ks=4,vs=8', 'teal'), (')', 'gray')]
CW = 8.4  # mono advance at 14px
x = 40
pos = {}
for t, col in toks:
    w = len(t) * CW
    if col != 'gray':
        l, d, xx = C[col]
        b.append(f'<rect x="{x - 1}" y="30" width="{w + 2}" height="24" rx="3" fill="{l}" stroke="{d}" stroke-width="0.8"/>')
    b.append(f'<text x="{x}" y="42" dominant-baseline="central" font-size="14" font-family="{MONO}" fill="{C[col][2]}">{esc(t)}</text>')
    pos[t] = (x, x + w)
    x += w
callouts = [
    ('map_value', 'teal', 92, ['what r0 points at:', 'a value inside a map']),
    ('_or_null', 'amber', 222, ['maybe NULL: no read', 'through r0 until a test']),
    ('id=1', 'teal', 352, ['shared by every copy', 'of this pointer']),
    ('map=write_counts', 'teal', 482, ['which map the', 'value lives in']),
    ('ks=4,vs=8', 'teal', 612, ['key 4 bytes, value 8:', 'reads stay inside vs']),
]
for t, col, cx, lines in callouts:
    x0, x1 = pos[t]
    mid = (x0 + x1) / 2
    b.append(f'<path d="M{mid},55 V68 H{cx} V84" fill="none" stroke="{C[col][1]}" stroke-width="1"/>')
    b.append(box(cx - 62, 86, 124, 44, col))
    b.append(tx(cx, 100, lines[0], size=10.5, col=col))
    b.append(tx(cx, 116, lines[1], size=10.5, col=col))
# second line: after the test
b.append(tx(20, 152, 'after slot 9, on the path where the test failed (r0 is not 0):', size=11, anchor='start', col='gray'))
x = 40
for t, col in [('R0=', 'gray'), ('map_value', 'teal'), ('(id=1,map=write_counts,ks=4,vs=8)', 'gray')]:
    w = len(t) * CW
    if col != 'gray':
        l, d, xx = C[col]
        b.append(f'<rect x="{x - 1}" y="164" width="{w + 2}" height="24" rx="3" fill="{l}" stroke="{d}" stroke-width="0.8"/>')
    b.append(f'<text x="{x}" y="176" dominant-baseline="central" font-size="14" font-family="{MONO}" fill="{C[col][2]}">{esc(t)}</text>')
    x += w
b.append(tx(500, 176, '_or_null is gone', size=11, col='amber', anchor='start', weight='600'))
# third line: a scalar
b.append(tx(20, 208, 'at slot 12, the key read back as a number:', size=11, anchor='start', col='gray'))
x = 40
for t, col in [('R3=', 'gray'), ('scalar', 'teal'), ('(smin=0,smax=umax=0xffffffff,…)', 'gray')]:
    w = len(t) * CW
    if col != 'gray':
        l, d, xx = C[col]
        b.append(f'<rect x="{x - 1}" y="220" width="{w + 2}" height="24" rx="3" fill="{l}" stroke="{d}" stroke-width="0.8"/>')
    b.append(f'<text x="{x}" y="232" dominant-baseline="central" font-size="14" font-family="{MONO}" fill="{C[col][2]}">{esc(t)}</text>')
    x += w
b.append(tx(395, 232, 'a plain number, with bounds', size=11, col='teal', anchor='start'))
b.append(bar(258, 30, 'One register, one instruction: a type, which object, its sizes, and an id that links its copies.'))
figs['reg'] = svg(298, 'One register\'s state at one instruction, part by part',
                  'The kernel record of r0 after the map lookup, split into type, maybe-NULL flag, id, map and sizes', b, m)

save('ch04-promise', figs['promise'])
save('ch04-walk', figs['walk'])
for i, f in enumerate(frames(figs['walk'], m := 'ah-4-2', (1, 2, 3)), 1):
    save(f'ch04-walk-twin{i}', f)
save('ch04-reg', figs['reg'])
print('ch04 figures ok')
