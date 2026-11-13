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
b.append(bar(y + 4, 32, 'Proved for every path before the program runs once. Whether it counts the right thing is not checked.'))
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
figs['walk'] = svg(212, 'The kernel walking both paths of the write counter',
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

# ---------- Figure 4.2 for print: one flowchart, two paths (replaces the three-frame twins) ----------
# Drawn for the 127 mm text column: 680 units = 127 mm, so 14.2 units = 7.5 pt; labels here are 14.5-16.
SANS = "'Open Sans Condensed', 'Open Sans', 'Myriad Pro', sans-serif"
UMONO = "'Ubuntu Mono', 'JetBrains Mono', monospace"
INK, GREY, P2 = '#1F2328', '#4A5056', '#0F6E56'
def t(x, y, s_, size=15, anchor='middle', fam=SANS, weight=None, fill=INK, italic=False):
    w = f' font-weight="{weight}"' if weight else ''
    it = ' font-style="italic"' if italic else ''
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-family="{fam}" '
            f'font-size="{size}" fill="{fill}"{w}{it}>{esc(s_)}</text>')
def node(y, h, l1, l2, x=200, w=280):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#FFFFFF" stroke="{INK}" stroke-width="1.3"/>'
            + t(x + w / 2, y + h / 2 - 9, l1, size=16, fam=UMONO, weight='700') + t(x + w / 2, y + h / 2 + 11, l2, size=15, fill=GREY))
def line(pts, mid, color=INK, width=1.8, dash=None, arrow=True):
    d = ' '.join(f'{"M" if i == 0 else "L"}{x},{y}' for i, (x, y) in enumerate(pts))
    da = f' stroke-dasharray="{dash}"' if dash else ''
    me = f' marker-end="url(#{mid})"' if arrow else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da}{me}/>'
def saved(x, y):   # a "state saved" tag joined by a short line to the node whose left edge is at x
    return (f'<line x1="{x - 18}" y1="{y}" x2="{x}" y2="{y}" stroke="{GREY}" stroke-width="1.2"/>'
            f'<rect x="{x - 122}" y="{y - 12}" width="104" height="24" rx="12" fill="#FFFFFF" stroke="{GREY}" stroke-width="1"/>'
            + t(x - 70, y, 'state saved', size=14.5, fill=GREY))
m2 = 'ah-4-2f'
mk = (f'<marker id="{m2}-2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
      f'<path d="M0,0 L10,5 L0,10 z" fill="{P2}"/></marker>')
b = [mk.replace('<marker', '<defs><marker').replace('</marker>', '</marker></defs>')]
cx = 340
# legend
b += [line([(500, 18), (548, 18)], m2, arrow=False, width=2.2), t(556, 18, 'path 1', anchor='start', weight='600'),
      line([(500, 42), (548, 42)], m2, color=P2, dash='7 5', arrow=False, width=2.2), t(556, 42, 'path 2', anchor='start', weight='600', fill=P2)]
# nodes
b.append(node(10, 54, 'slots 0–8', 'put the key on the stack, look it up'))
b.append(f'<polygon points="220,146 {cx},104 460,146 {cx},188" fill="#FFFFFF" stroke="{INK}" stroke-width="1.3"/>')
b += [t(cx, 135, 'slot 9', size=16, fam=UMONO, weight='700'), t(cx, 157, 'r0 == 0 ?', size=16, fam=UMONO)]
b.append(node(224, 54, 'slots 10–11', 'read the count, add one'))
b.append(node(312, 54, 'slots 12–24', 'print, update the map'))
b.append(node(400, 54, 'slot 25', 'set the return value to 0'))
b.append(node(488, 48, 'slot 26', 'exit'))
# path 1: the main column
b += [line([(cx, 64), (cx, 102)], m2, width=2.2), line([(cx, 188), (cx, 222)], m2, width=2.2), line([(cx, 278), (cx, 310)], m2, width=2.2),
      line([(328, 366), (328, 398)], m2, width=2.2), line([(cx, 454), (cx, 486)], m2, width=2.2)]
b += [t(cx - 12, 84, 'r0 = map value or NULL', size=15, anchor='end', italic=True, fill=GREY),
      t(cx + 12, 204, 'no', size=15.5, anchor='start', weight='700'),
      t(cx - 12, 204, 'r0 = map value', size=15, anchor='end', italic=True, fill=GREY)]
# path 2: the jump to slot 12, then on to slot 25, where it stops
b += [line([(460, 146), (560, 146), (560, 339), (482, 339)], m2 + '-2', color=P2, dash='7 5', width=2.2),
      line([(352, 366), (352, 398)], m2 + '-2', color=P2, dash='7 5', width=2.2),
      t(470, 132, 'yes', size=15.5, anchor='start', weight='700', fill=P2),
      t(572, 214, 'jump to slot 12', size=15, anchor='start', fill=P2), t(572, 234, 'r0 = 0', size=15, anchor='start', italic=True, fill=P2)]
# saved states and where each path ends
b += [saved(220, 146), saved(200, 427)]
b += [f'<line x1="492" y1="414" x2="492" y2="440" stroke="{P2}" stroke-width="3"/>',
      t(502, 418, 'path 2 stops here:', size=15, anchor='start', weight='600', fill=P2),
      t(502, 438, 'same state as the saved one', size=15, anchor='start', fill=P2),
      t(502, 458, '12 instructions walked', size=15, anchor='start', fill=P2)]
b += [t(492, 504, 'path 1 ends: 24 instructions', size=15, anchor='start', weight='600'),
      t(492, 524, '36 walked in all', size=15, anchor='start', fill=GREY)]
figs['walkflow'] = svg(542, 'The verifier walks the write counter: two paths, one cut short',
                       'Flowchart of the counter: slots 0 to 8, then the test at slot 9. Path 1 falls through to slots 10 and 11, '
                       'then 12 to 24, 25 and the exit at 26, 24 instructions, saving states at slots 9 and 25. Path 2 jumps to slot 12 '
                       'and stops at slot 25, where its state matches the saved one, after 12 instructions.', b, m2)
save('ch04-walk-flow', figs['walkflow'])
# ---------- Figure 4.3 for print: three entries of the kernel's record, the first taken apart ----------
# The part the test at slot 9 removes, _or_null, is the accent, in bold with a heavier bracket.
m = 'ah-4-3p'
b = []
EX, CWM = 20, 8.0                       # entries in Ubuntu Mono 16: 8 units a character
def entry(y, toks):
    """toks: (text, style) with style None, 'b' for bold or 'a' for the accent; returns the x span of each token."""
    sp, x, spans = [], EX, []
    for s_, st in toks:
        fill = P2 if st == 'a' else INK
        wt = ' font-weight="700"' if st else ''
        sp.append(f'<tspan fill="{fill}"{wt}>{esc(s_)}</tspan>')
        spans.append((x, x + len(s_) * CWM)); x += len(s_) * CWM
    return (f'<text x="{EX}" y="{y}" dominant-baseline="central" font-family="{UMONO}" font-size="16" fill="{INK}" '
            f'xml:space="preserve">{"".join(sp)}</text>'), spans, x
def label(y, s_): return t(EX, y, s_, size=14.5, anchor='start', italic=True, fill=GREY)
b.append(label(12, 'after slot 8, the call to the map lookup, the kernel writes down:'))
txt, spans, _ = entry(38, [('R0=', None), ('map_value', 'b'), ('_or_null', 'a'), ('(', None), ('id=1', 'b'), (',', None),
                           ('map=write_counts', 'b'), (',', None), ('ks=4,vs=8', 'b'), (')', None)])
b.append(txt)
parts = [(1, 68, ['what r0 points at:', 'a value inside a map']), (2, 204, ['maybe NULL: no read', 'through r0 until a test']),
         (4, 340, ['shared by every copy', 'of this pointer']), (6, 476, ['which map the', 'value lives in']),
         (8, 612, ['key 4 bytes, value 8:', 'reads stay inside vs'])]
for k, cx, lines in parts:
    x0, x1 = spans[k]
    acc = k == 2
    col, sw = (P2, 2.2) if acc else (INK, 1.2)
    b.append(f'<path d="M{x0 + 1},50 v5 H{x1 - 1} v-5" fill="none" stroke="{col}" stroke-width="{sw}"/>')
    b.append(line([((x0 + x1) / 2, 55), (cx, 80)], None, color=col, width=sw, arrow=False))
    for j, ln in enumerate(lines):
        b.append(t(cx, 92 + j * 18, ln, size=14.5, fill=P2 if acc else INK, weight='700' if acc and j == 0 else None))
b.append(label(146, 'after slot 9, on the path where the test failed (r0 is not 0):'))
txt, spans, xe = entry(172, [('R0=', None), ('map_value', 'b'), ('(id=1,map=write_counts,ks=4,vs=8)', None)])
b += [txt, t(xe + 24, 172, '_or_null is gone', size=15, anchor='start', weight='700', fill=P2)]
b.append(label(206, 'at slot 12, the key read back as a number:'))
txt, spans, xe = entry(232, [('R3=', None), ('scalar', 'b'), ('(smin=0,smax=umax=0xffffffff,…)', None)])
b += [txt, t(xe + 24, 232, 'a plain number, with bounds', size=15, anchor='start', fill=GREY, italic=True)]
fig_reg_print = svg(250, "One register's state at one instruction, part by part",
                    'Three entries from the verifier log. After slot 8: R0=map_value_or_null(id=1,map=write_counts,ks=4,vs=8), taken apart: '
                    'map_value, what r0 points at, a value inside a map; _or_null, maybe NULL, no read through r0 until a test; id=1, shared '
                    'by every copy of this pointer; map=write_counts, which map the value lives in; ks=4,vs=8, key 4 bytes, value 8, reads '
                    'stay inside vs. After slot 9, on the path where the test failed: the same entry with _or_null gone. At slot 12: '
                    'R3=scalar(smin=0,smax=umax=0xffffffff,…), a plain number, with bounds.', b, m)
save('ch04-reg', fig_reg_print)
print('ch04 figures ok')
