# Chapter "Reading PREVAIL: a verifier built on abstract interpretation" (src/prevail.html): its four drawn figures.
# Drawn to the print rules in NOTES.md "Figure rules": 680 units = 127 mm, words 14.5 units or more,
# Open Sans Condensed for words, Ubuntu Mono for code names, black and grey with one accent.
# Sources: prevail-curve is book/labs/prevail-root.sh run on kernel 7.2.15 in a VM (13 November 2026) and
# book/labs/prevail/toy.py; prevail-cfg and prevail-rounds are toy.py's run of once-ge at N=16 (and of once and
# --no-narrow); prevail-zone follows Table 3 of the PLDI 2019 paper, applied to slots 5 to 9 of sum_each.
import math, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import esc, svg, save

SANS = "'Open Sans Condensed', 'Open Sans', 'Myriad Pro', sans-serif"
UMONO = "'Ubuntu Mono', 'JetBrains Mono', monospace"
INK, GREY, LIGHT, ACC, ACCL = '#1F2328', '#4A5056', '#B8BCC0', '#0F6E56', '#E1F5EE'


def t(x, y, s_, size=15, anchor='middle', fam=SANS, weight=None, fill=INK, italic=False):
    w = f' font-weight="{weight}"' if weight else ''
    it = ' font-style="italic"' if italic else ''
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-family="{fam}" '
            f'font-size="{size}" fill="{fill}"{w}{it}>{esc(s_)}</text>')


def rect(x, y, w, h, l1, lines=(), stroke=INK, sw=1.3, mono1=True, fill='#FFFFFF', fill_text=INK, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ''
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="{stroke}" '
           f'stroke-width="{sw}"{da}/>')
    top = y + h / 2 - 9.5 * len(lines)
    out += t(x + w / 2, top, l1, size=16, fam=UMONO if mono1 else SANS, weight='700', fill=fill_text)
    for i, ln in enumerate(lines):
        out += t(x + w / 2, top + 21 + 19 * i, ln, size=15, fill=GREY)
    return out


def line(pts, mid, color=INK, width=1.8, dash=None, arrow=True):
    d = ' '.join(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}' for i, (x, y) in enumerate(pts))
    da = f' stroke-dasharray="{dash}"' if dash else ''
    me = f' marker-end="url(#{mid})"' if arrow else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da}{me}/>'


def diamond(cx, cy, hw, hh, l1, l2):
    return (f'<polygon points="{cx - hw},{cy} {cx},{cy - hh} {cx + hw},{cy} {cx},{cy + hh}" fill="#FFFFFF" '
            f'stroke="{INK}" stroke-width="1.3"/>' + t(cx, cy - 10, l1, size=16, weight='700', fam=UMONO)
            + t(cx, cy + 11, l2, size=14.5, fill=GREY))


def note(x, y, lines, anchor='start', fill=GREY, weight=None):
    return ''.join(t(x, y + 18 * i, ln, size=14.5, anchor=anchor, fill=fill, italic=weight is None,
                     weight=weight) for i, ln in enumerate(lines))


# ---------- prevail-curve: instructions walked against the loop bound ----------
# Claim: Linux's walk of the packet loop grows in step with the loop bound (7N + 12 and 10N + 8 instructions,
# measured in the VM, and counted the same by the toy walk), while the toy fixpoint does the same 47 or 53
# transfers at every bound.
m = 'ah-prevail-curve'
b = []
NS = [16, 64, 256, 1024]
ONCE = [124, 460, 1804, 7180]
EACH = [168, 654, 2568, 10254]
X0, X1, Y0, Y1 = 110, 520, 318, 26
def px(n): return X0 + 30 + (math.log2(n) - 4) / 6 * (X1 - X0 - 60)
def py(v): return Y0 - (math.log10(v) - 1) / 4 * (Y0 - Y1)          # 10 to 100,000
b.append(f'<rect x="{X0}" y="{Y1}" width="{X1 - X0}" height="{Y0 - Y1}" fill="none" stroke="{GREY}" stroke-width="1"/>')
for v, lab in [(10, '10'), (100, '100'), (1000, '1,000'), (10000, '10,000'), (100000, '100,000')]:
    y = py(v)
    b.append(f'<line x1="{X0 - 5}" y1="{y:.1f}" x2="{X0}" y2="{y:.1f}" stroke="{GREY}" stroke-width="1"/>')
    b.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{LIGHT}" stroke-width="0.8" '
             f'stroke-dasharray="2 4"/>')
    b.append(t(X0 - 9, y, lab, size=14.5, anchor='end', fill=GREY))
for n in NS:
    b.append(f'<line x1="{px(n):.1f}" y1="{Y0}" x2="{px(n):.1f}" y2="{Y0 + 5}" stroke="{GREY}" stroke-width="1"/>')
    b.append(t(px(n), Y0 + 18, f'{n:,}', size=14.5, fill=GREY))
b.append(t((X0 + X1) / 2, Y0 + 42, 'loop bound N (bytes read)', size=15))
b.append(t(24, (Y0 + Y1) / 2, 'instructions', size=15, anchor='middle') .replace(
    '<text ', f'<text transform="rotate(-90 24 {(Y0 + Y1) / 2})" '))
def series(vals, dash, col, width, dot):
    pts = [(px(n), py(v)) for n, v in zip(NS, vals)]
    out = line(pts, m, color=col, width=width, dash=dash, arrow=False)
    for x, y in pts:
        out += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{col if dot else "#FFFFFF"}" '
                f'stroke="{col}" stroke-width="1.8"/>')
    return out
b.append(series(EACH, '7 4', INK, 2.0, False))
b.append(series(ONCE, None, INK, 2.2, True))
b.append(series([53] * 4, '7 4', ACC, 2.0, False))
b.append(series([47] * 4, None, ACC, 2.6, True))
# values at the ends
b.append(t(px(1024) + 10, py(10254) - 9, '10,254', size=14.5, anchor='start'))
b.append(t(px(1024) + 10, py(7180) + 9, '7,180', size=14.5, anchor='start'))
b.append(t(px(16) - 10, py(168) - 9, '168', size=14.5, anchor='end'))
b.append(t(px(16) - 10, py(124) + 9, '124', size=14.5, anchor='end'))
b.append(t(px(1024) + 10, py(53) - 9, '53', size=14.5, anchor='start', fill=ACC))
b.append(t(px(1024) + 10, py(47) + 9, '47', size=14.5, anchor='start', fill=ACC))
# legend, inside the figure
LX = 540
def key(y, dash, col, width, dot, lab1, lab2):
    out = line([(LX, y), (LX + 34, y)], m, color=col, width=width, dash=dash, arrow=False)
    out += (f'<circle cx="{LX + 17}" cy="{y}" r="4.5" fill="{col if dot else "#FFFFFF"}" stroke="{col}" '
            f'stroke-width="1.8"/>')
    out += t(LX + 42, y - 9, lab1, size=14.5, anchor='start', fill=col, weight='700')
    out += t(LX + 42, y + 9, lab2, size=14.5, anchor='start', fill=GREY)
    return out
b.append(t(LX, 40, 'Linux v7.2 walk', size=15, anchor='start', weight='700'))
b.append(t(LX, 58, '(the toy walk: same)', size=14.5, anchor='start', fill=GREY))
b.append(key(88, None, INK, 2.2, True, 'sum_once', '7N + 12'))
b.append(key(130, '7 4', INK, 2.0, False, 'sum_each', '10N + 8'))
b.append(t(LX, 182, 'toy fixpoint', size=15, anchor='start', weight='700', fill=ACC))
b.append(t(LX, 200, '(transfers)', size=14.5, anchor='start', fill=GREY))
b.append(key(230, None, ACC, 2.6, True, 'once', '47'))
b.append(key(272, '7 4', ACC, 2.0, False, 'each', '53'))
fig = svg(372, 'Instructions walked against the loop bound',
          'Log-log plot. For loop bounds 16, 64, 256 and 1,024, Linux v7.2 processed 124, 460, 1,804 and 7,180 '
          'instructions for sum_once and 168, 654, 2,568 and 10,254 for sum_each, growing in step with the bound; '
          'the toy walk counts the same. The toy fixpoint evaluates 47 instructions for sum_once and 53 for sum_each '
          'at every bound, a flat line.', b, m)
save('prevail-curve', fig)


# ---------- prevail-cfg: one state per node ----------
# Claim: the abstract interpreter keeps one state per point of the graph; after the fixpoint the state at the loop
# head holds every round at once, and the read is checked against it once.
m = 'ah-prevail-cfg'
b = []
FX, FW = 40, 300
FC = FX + FW / 2
b.append(rect(FX, 8, FW, 58, 'slots 0 to 4', ['r1 = data, r2 = end, r3 = data + 16'], mono1=False))
b.append(line([(FC, 66), (FC, 84)], m))
D1 = 126
b.append(diamond(FC, D1, 140, 42, 'r3 > r2 ?', 'slot 5: past the end?'))
b.append(line([(FC + 140, D1), (FC + 178, D1)], m))
b.append(t(FC + 148, D1 - 13, 'yes', size=15, anchor='start', weight='700'))
b.append(rect(FC + 178, D1 - 26, 112, 52, 'slot 18', ['exit, r0 = 2'], mono1=False))
b.append(line([(FC, D1 + 42), (FC, 214)], m))
b.append(t(FC - 10, D1 + 54, 'no', size=15, anchor='end', weight='700'))
b.append(rect(FX, 214, FW, 52, 'slots 6 and 7', ['w2 = 0, r3 = 0'], mono1=False))
b.append(line([(FC, 266), (FC, 296)], m))
b.append(rect(FX, 296, FW, 96, 'slots 8 to 12, loop head at 8', ['r4 = r1 + r3', 'read 1 byte at r4 (slot 10)',
                                                                  'w2 += byte, r3 += 1'],
              mono1=False, stroke=ACC, sw=2.6, fill_text=ACC))
b.append(line([(FC, 392), (FC, 416)], m))
D2 = 458
b.append(diamond(FC, D2, 140, 42, 'r3 >= 16 ?', 'slot 13: loop done?'))
b.append(line([(FC, D2 + 42), (FC, 534)], m))
b.append(t(FC - 10, D2 + 54, 'yes', size=15, anchor='end', weight='700'))
b.append(rect(FX, 534, FW, 52, 'slots 15 to 18', ['return 2 - (w2 & 1)'], mono1=False))
# the back edge, on the left
b.append(line([(FC - 140, D2), (14, D2), (14, 344), (FX, 344)], m))
b.append(t(FC - 150, D2 - 13, 'no', size=15, anchor='end', weight='700'))
# the states, as notes beside the edges they qualify
NX = 362
b.append(note(NX, 184, ['len in [16, 65535]']))
b.append(note(NX, 272, ['r3 in [0, 0]  (entry)']))
b.append(note(NX, 314, ['at the head, after the fixpoint:', 'r3 in [0, 15]', 'w2 in [0, 4294967295]']))
b.append(t(NX, 374, 'read: r4 = pkt + [0, 15], 15 + 1 <= 16 <= len', size=14.5, anchor='start', fill=ACC,
           weight='700'))
b.append(note(NX, D2 - 9, ['slot 14, back to 8:', 'r3 in [1, 15]']))
b.append(note(NX, 512, ['r3 in [16, 16]']))
b.append(note(NX, 560, ['r0 in [1, 2]']))
fig = svg(596, 'One state per node',
          'Flowchart of sum_once at N = 16 with the interval state the toy fixpoint keeps at each point. Slots 0 to 4 '
          'load data and end and compute data plus 16; slot 5 tests whether that is past the end, and exits if so; '
          'otherwise the packet length is at least 16. Slots 6 and 7 set w2 and r3 to 0. The loop body, slots 8 to '
          '12 with the loop head at 8, reads one byte at r1 plus r3; at the head r3 is in [0, 15] after the fixpoint, '
          'so the read at offset 0 to 15 fits a packet of at least 16 bytes. Slot 13 tests r3 >= 16; if not, slot 14 '
          'jumps back to 8 with r3 in [1, 15]; if so, r3 is 16 and slots 15 to 18 return 1 or 2.', b, m)
save('prevail-cfg', fig)


# ---------- prevail-rounds: join, widen, narrow on a number line ----------
# Claim: at the loop head, the interval for r3 grows by join, jumps to infinity by widening, and comes back to
# [0, 15] only when the loop's exit test can cut it; Linux's walk instead holds one value per round.
m = 'ah-prevail-rounds'
b = []
LX0, LX1 = 300, 640                  # the number line: 0 .. 20, then +oo
U = (LX1 - 30 - LX0) / 20
def nx(v): return LX0 + v * U
ROWS = [('entry, from slot 7', (0, 0), 'solid'),
        ('round 1: join', (0, 1), 'solid'),
        ('round 2: widen', (0, None), 'solid'),
        ('round 3: kept, r3 >= 16', (0, 15), 'acc'),
        ('round 3, --no-narrow', (0, None), 'grey'),
        ('round 3, r3 == 16 (as compiled)', (0, None), 'grey'),
        ('Linux: one state a round', 'dots', 'solid')]
RY0, RH = 50, 44
# the access limit
b.append(f'<line x1="{nx(15.5):.1f}" y1="{RY0 - 24}" x2="{nx(15.5):.1f}" y2="{RY0 + RH * len(ROWS) - 18}" '
         f'stroke="{ACC}" stroke-width="1.6" stroke-dasharray="5 4"/>')
b.append(t(nx(15.5) - 6, RY0 - 32, 'the read at slot 10 needs r3 <= 15', size=14.5, anchor='end', fill=ACC,
           weight='700'))
for i, (lab, iv, style) in enumerate(ROWS):
    y = RY0 + i * RH
    b.append(t(LX0 - 16, y, lab, size=15, anchor='end', fill=INK if style != 'grey' else GREY))
    b.append(f'<line x1="{LX0}" y1="{y}" x2="{LX1}" y2="{y}" stroke="{LIGHT}" stroke-width="1"/>')
    for v in range(0, 21, 5):
        b.append(f'<line x1="{nx(v):.1f}" y1="{y - 4}" x2="{nx(v):.1f}" y2="{y + 4}" stroke="{LIGHT}" stroke-width="1"/>')
    if iv == 'dots':
        for v in range(16):
            b.append(f'<circle cx="{nx(v):.1f}" cy="{y}" r="4" fill="{INK}"/>')
        continue
    lo, hi = iv
    col = ACC if style == 'acc' else GREY if style == 'grey' else INK
    x1 = nx(hi) if hi is not None else LX1
    if lo == hi:
        b.append(f'<circle cx="{nx(lo):.1f}" cy="{y}" r="5" fill="{col}"/>')
    else:
        da = ' stroke-dasharray="7 4"' if style == 'grey' else ''
        b.append(f'<line x1="{nx(lo):.1f}" y1="{y}" x2="{x1:.1f}" y2="{y}" stroke="{col}" stroke-width="7"{da}/>')
        if hi is None:
            b.append(f'<path d="M{LX1 - 2},{y - 9} L{LX1 + 12},{y} L{LX1 - 2},{y + 9} z" fill="{col}"/>')
# axis labels below
ya = RY0 + RH * (len(ROWS) - 1) + 30
for v in range(0, 21, 5):
    b.append(t(nx(v), ya, str(v), size=14.5, fill=GREY))
b.append(t(LX1 + 6, ya, '+oo', size=14.5, fill=GREY))
b.append(t((LX0 + LX1) / 2, ya + 24, 'r3 at the loop head (slot 8), N = 16', size=15))
fig = svg(ya + 40, 'r3 at the loop head, round by round',
          'Seven number lines from 0 to 20 with an arrow to infinity. Entry: r3 is 0. Round 1, join: 0 to 1. Round 2, '
          'widen: 0 to infinity. Round 3 with the test r3 >= 16: kept at 0 to 15, inside the limit of 15 that the '
          'read at slot 10 needs. Round 3 with --no-narrow, and round 3 with the compiled test r3 == 16: still 0 to '
          'infinity, past the limit. Linux: sixteen separate points, 0 to 15, one state for each round.', b, m)
save('prevail-rounds', fig)


# ---------- prevail-zone: one packet check as difference constraints ----------
# Claim: a difference constraint keeps the fact that the read at slot 9 of sum_each needs, r5 + 1 <= end, by
# adding up the constraints on a path through the graph; the interval domain, which has no edges, cannot.
m = 'ah-prevail-zone'
b = []
def node(x, y, l1, l2):
    return (f'<ellipse cx="{x}" cy="{y}" rx="70" ry="30" fill="#FFFFFF" stroke="{INK}" stroke-width="1.4"/>'
            + t(x, y - 8, l1, size=16, fam=UMONO, weight='700') + t(x, y + 12, l2, size=14.5, fill=GREY))
N3, N5, N0, NL = (110, 60), (110, 210), (420, 210), (420, 360)
b.append(node(*N3, 'r3', 'the round, i'))
b.append(node(*N5, 'r5.off', 'byte to read'))
b.append(node(*N0, 'r0.off', 'r5 + 1'))
b.append(node(*NL, 'len', 'packet end'))
b.append(line([(N3[0], N3[1] + 30), (N5[0], N5[1] - 30)], m, arrow=False, width=2))
b.append(t(N3[0] + 12, 135, 'r5.off - r3 = 0', size=14.5, anchor='start', fam=UMONO))
b.append(t(N3[0] + 12, 154, 'slot 5: r5 = data + r3', size=14.5, anchor='start', fill=GREY))
b.append(line([(N5[0] + 70, N5[1]), (N0[0] - 70, N0[1])], m, arrow=False, width=2))
b.append(t((N5[0] + N0[0]) / 2, N5[1] - 14, 'r0.off - r5.off = 1', size=14.5, fam=UMONO))
b.append(t((N5[0] + N0[0]) / 2, N5[1] + 16, 'slots 6 and 7', size=14.5, fill=GREY))
b.append(line([(N0[0], N0[1] + 30), (NL[0], NL[1] - 30)], m, arrow=False, width=2))
b.append(t(NL[0] + 12, 276, 'r0.off - len <= 0', size=14.5, anchor='start', fam=UMONO))
b.append(t(NL[0] + 12, 295, 'slot 8, not taken', size=14.5, anchor='start', fill=GREY))
# the derived constraint
b.append(line([(N5[0] + 20, N5[1] + 29), (NL[0] - 70, NL[1])], m, color=ACC, width=2.6, dash='8 5', arrow=False))
b.append(t(24, 318, 'r5.off - len <= -1', size=16, anchor='start', fam=UMONO, fill=ACC, weight='700'))
b.append(t(24, 338, 'the sum along the path: the read', size=14.5, anchor='start', fill=ACC))
b.append(t(24, 356, 'at slot 9 fits, in every round', size=14.5, anchor='start', fill=ACC))
# what intervals keep instead
b.append(f'<rect x="20" y="412" width="640" height="62" rx="5" fill="#FFFFFF" stroke="{GREY}" stroke-width="1.1" '
         f'stroke-dasharray="6 4"/>')
b.append(t(36, 432, 'intervals alone, after widening:', size=15, anchor='start', weight='700'))
b.append(t(36, 454, 'r3 in [0, +oo], r5.off in [0, +oo], len in [1, 65535]: no edge, so no bound on r5.off - len',
           size=14.5, anchor='start', fill=GREY))
b.append(t(660, 60, 'solid: a fact the instruction adds', size=14.5, anchor='end', fill=GREY))
b.append(t(660, 80, 'dashed: derived by closure', size=14.5, anchor='end', fill=ACC))
fig = svg(486, 'One packet check as difference constraints',
          'Constraint graph of four variables: r3, the offset of r5, the offset of r0, and the packet length len. '
          'Slot 5 gives r5.off minus r3 equals 0; slots 6 and 7 give r0.off minus r5.off equals 1; slot 8, not taken, '
          'gives r0.off minus len at most 0. Adding the constraints along the path from r5.off to len gives r5.off '
          'minus len at most minus 1, drawn dashed: the read at slot 9 fits in every round. Below, the interval '
          'domain after widening keeps r3 and r5.off in 0 to infinity and len in 1 to 65535, with no relation, so it '
          'cannot bound r5.off minus len.', b, m)
save('prevail-zone', fig)
