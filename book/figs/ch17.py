# Figures for chapter 17, redrawn for print (figure rules in NOTES.md): 680 units = 127 mm,
# words 14.5 units or more, node titles 16, black and grey with the one accent.
# The screen versions are kept in figs/pre-print/ch17.py.
# Every number below comes from book/labs/ch17-check.py, chapter 5's log (copy c) or Linux v7.2.
# Figure 17.1 (the four verdicts) is now an HTML table in src/ch17.html; figs/out/ch17-verdicts.svg is no longer used.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

# ---------- print helpers, as for Figure 4.2 (figs/ch04.py) ----------
SANS = "'Open Sans Condensed', 'Open Sans', 'Myriad Pro', sans-serif"
UMONO = "'Ubuntu Mono', 'JetBrains Mono', monospace"
INK, GREY, P2 = '#1F2328', '#4A5056', '#0F6E56'
BOX_FILL = '#EEF0F1'
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
def tm(x, y, parts, size=15, anchor='middle', fill=INK, weight=None):
    """One line in mixed faces: parts are (text, face) with face 'm' for a code name, 's' for words."""
    w = f' font-weight="{weight}"' if weight else ''
    sp = ''.join(f'<tspan font-family="{UMONO if f == "m" else SANS}">{esc(s_)}</tspan>' for s_, f in parts)
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-size="{size}" fill="{fill}"{w} '
            f'xml:space="preserve">{sp}</text>')
def rect(x, y, w, h, stroke=INK, sw=1.3, rx=5, dash=None, fill='#FFFFFF'):
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{da}/>'
def diamond(cx, cy, hw, hh, sw=1.3):
    return f'<polygon points="{cx - hw},{cy} {cx},{cy - hh} {cx + hw},{cy} {cx},{cy + hh}" fill="#FFFFFF" stroke="{INK}" stroke-width="{sw}"/>'

ACC_FILL, GREY_FILL, OFF = '#DCEFE8', '#E4E6E8', '#C9CCCF'
def cells(x0, y, cw, h, on, kind):
    """Sixteen cells for the values 0 to 15; 'on' cells filled. kind 'a' = accent (fill and heavy outline), 'g' = grey."""
    out = []
    for i in range(16):
        x = x0 + i * cw
        if i in on:
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{cw - 2:.1f}" height="{h}" rx="2" fill="{ACC_FILL if kind == "a" else GREY_FILL}" '
                       f'stroke="{P2 if kind == "a" else INK}" stroke-width="{2 if kind == "a" else 1.1}"/>')
        else:
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{cw - 2:.1f}" height="{h}" rx="2" fill="#FFFFFF" stroke="{OFF}" stroke-width="0.8"/>')
    return out

# ---------- Figure 17.2: one addition on four bits, checked by hand ----------
# Left, the inputs and the four real sums; right, rows on one axis of the sixteen four-bit values.
# The accent marks the real sums.
m = 'ah-17-2p'
b = []
GX, GW, GH = 8, 58, 32
b.append(t(GX, 14, 'every real sum x + y', size=15, anchor='start', weight='700'))
for c_, yv in enumerate((2, 6)):
    b.append(t(GX + (c_ + 1) * GW + GW / 2 - 3, 40, f'y = {yv}', fam=UMONO, fill=GREY))
for r_, xv in enumerate((1, 3)):
    yy = 54 + r_ * GH
    b.append(t(GX + GW / 2 - 4, yy + (GH - 4) / 2, f'x = {xv}', fam=UMONO, fill=GREY))
    for c_, yv in enumerate((2, 6)):
        x = GX + (c_ + 1) * GW
        b += [rect(x, yy, GW - 6, GH - 4, stroke=P2, sw=2, rx=3, fill=ACC_FILL),
              t(x + (GW - 6) / 2, yy + (GH - 4) / 2, str(xv + yv), size=16, fam=UMONO, weight='700', fill=P2)]
b += [t(GX, 140, 'x from 00x1 = {1, 3}', anchor='start', fam=UMONO), t(GX, 160, 'y from 0x10 = {2, 6}', anchor='start', fam=UMONO),
      t(GX, 188, 'as intervals:', size=14.5, anchor='start'), t(GX, 208, '[1, 3] and [2, 6]', anchor='start', fam=UMONO)]
SX, CWD, SH = 204, 29.5, 22
b.append(t(SX, 14, 'values of four bits', size=14.5, anchor='start', italic=True, fill=GREY))
for i in range(16):
    b.append(t(SX + i * CWD + (CWD - 2) / 2, 36, str(i), size=14.5, fam=UMONO, fill=GREY))
rows = [([('the real sums: 3, 5, 7, 9', 's')], {3, 5, 7, 9}, 'a'),
        ([('tnum_add(00x1, 0x10)', 'm'), (' = ', 's'), ('xxx1', 'm'), (': stands for 8 values', 's')], set(range(1, 16, 2)), 'g'),
        ([('interval addition, ', 's'), ('[1, 3] + [2, 6] = [3, 9]', 'm'), (': 7 values', 's')], set(range(3, 10)), 'g'),
        ([('the values both answers allow: the real sums again', 's')], {3, 5, 7, 9}, 'a')]
y = 58
for label, on, kind in rows:
    b.append(tm(SX, y, label, size=15, anchor='start', weight='700' if kind == 'a' else None, fill=P2 if kind == 'a' else INK))
    b += cells(SX, y + 12, CWD, SH, on, kind)
    y += 12 + SH + 22
H172 = y - 10
fig172 = svg(H172, 'Concretization and a sound abstract addition on four bits',
             'Left: x from γ(00x1) = {1, 3} and y from γ(0x10) = {2, 6}, as intervals [1, 3] and [2, 6]; every real sum x + y: 1 + 2 = 3, '
             '1 + 6 = 7, 3 + 2 = 5, 3 + 6 = 9. Right, on the sixteen values 0 to 15: the real sums 3, 5, 7, 9; tnum_add(00x1, 0x10) = xxx1, '
             'whose γ holds the 8 odd values; interval addition [1, 3] + [2, 6] = [3, 9], 7 values; the values both answers allow, the real sums again.', b, m)
save('ch17-gamma', fig172)

# ---------- Figure 17.3: one loop analysed three ways, round by round ----------
# Each strip is the sixteen values of four bits, filled where the analysis says i may be. Grey strips are rounds on the way;
# the accent (fill and heavy outline) marks where each analysis stops.
m = 'ah-17-3p'
b = []
CX = [226, 334, 442, 524, 614]          # centres of the round columns
STW = 6.25                              # one value: sixteen values = 100 units
def strip(cx, y, on, kind):
    """Sixteen narrow cells, no gaps; a stopping strip ('a') gets the accent fill and a heavy outline round it."""
    out = []
    for i in range(16):
        style = (f'fill="{ACC_FILL}" stroke="{P2}" stroke-width="1.2"' if i in on and kind == 'a' else
                 f'fill="{GREY_FILL}" stroke="{INK}" stroke-width="0.9"' if i in on else f'fill="#FFFFFF" stroke="{OFF}" stroke-width="0.7"')
        out.append(f'<rect x="{cx - 8 * STW + i * STW:.2f}" y="{y}" width="{STW:.2f}" height="20" {style}/>')
    if kind == 'a':
        out.append(f'<rect x="{cx - 8 * STW - 1.5}" y="{y - 1.5}" width="{16 * STW + 3}" height="23" fill="none" stroke="{P2}" stroke-width="2"/>')
    return out
b += [t(8, 14, 'i = 0;  loop { i = i + 1; }', size=15, anchor='start', fam=UMONO, weight='700'),
      t(672, 14, 'what is known about i where the loop begins', size=14.5, anchor='end', italic=True, fill=GREY)]
for cx, s_ in zip(CX, ('round 1', 'round 2', 'round 3', '…', 'last')):
    b.append(t(cx, 42, s_, size=14.5, fill=GREY))
ROWS = (60, 146, 232)
labels = (('join only', 'an interval analysis'), ('join and widening', 'PREVAIL, chapter 20'), ('no join', 'the Linux verifier'))
for y, (t1, t2) in zip(ROWS, labels):
    b += [t(8, y + 9, t1, size=16, anchor='start', weight='700'), t(8, y + 29, t2, size=14.5, anchor='start')]
NOTE = 58
# row 1: [0, 0], [0, 1], [0, 2], ..., [0, 15]
for cx, hi, kind in zip((CX[0], CX[1], CX[2], CX[4]), (0, 1, 2, 15), 'ggga'):
    b += strip(cx, ROWS[0], set(range(hi + 1)), kind)
    b.append(t(cx, ROWS[0] + 36, f'[0, {hi}]', fam=UMONO, weight='700' if kind == 'a' else None, fill=P2 if kind == 'a' else INK))
b.append(t(CX[3], ROWS[0] + 10, '…', size=16))
b.append(t(160, ROWS[0] + NOTE, '16 rounds on four bits; 2⁶⁴ on a 64-bit register', size=14.5, anchor='start', italic=True))
# row 2: [0, 0], then widened to [0, 15], then stable
for cx, hi, kind in zip((CX[0], CX[1]), (0, 15), 'ga'):
    b += strip(cx, ROWS[1], set(range(hi + 1)), kind)
    b.append(t(cx, ROWS[1] + 36, f'[0, {hi}]', fam=UMONO, weight='700' if kind == 'a' else None, fill=P2 if kind == 'a' else INK))
b.append(t(CX[2] - 50, ROWS[1] + 10, 'nothing changed: done', size=15, anchor='start', weight='700', fill=P2))
b.append(t(160, ROWS[1] + NOTE, '2 rounds: the upper bound moved, so it jumped to the largest number', size=14.5, anchor='start', italic=True))
# row 3: one state per round, each a single value, never merged
for cx, v in zip((CX[0], CX[1], CX[2]), (0, 1, 2)):
    b += strip(cx, ROWS[2], {v}, 'g')
    b.append(t(cx, ROWS[2] + 36, f'i = {v}', fam=UMONO))
b += [t(CX[3], ROWS[2] + 10, '…', size=16),
      t(CX[4], ROWS[2] + 10, 'i = 124,993', size=15, fam=UMONO, weight='700', fill=P2),
      t(CX[4], ROWS[2] + 32, 'at the limit', size=15, weight='700', fill=P2)]
b.append(t(160, ROWS[2] + NOTE, 'a new state each round, until the exit test or 1,000,000 instructions (chapter 5, copy c)', size=14.5, anchor='start', italic=True))
H173 = ROWS[2] + NOTE + 16
fig173 = svg(H173, 'One loop analysed three ways',
             'The loop i = 0; loop { i = i + 1; }, and what is known about i where the loop begins. Join only (an interval analysis): '
             '[0, 0], [0, 1], [0, 2], and so on to [0, 15] in the last round; 16 rounds on four bits, 2 to the 64th on a 64-bit register. '
             'Join and widening (PREVAIL, chapter 20): [0, 0], then [0, 15], then nothing changed: done; 2 rounds, because the upper bound '
             'moved and jumped to the largest number. No join (the Linux verifier): i = 0, i = 1, i = 2, and so on to i = 124,993 at the limit; '
             'a new state each round, until the exit test or 1,000,000 instructions (chapter 5, copy c).', b, m)
save('ch17-rounds', fig173)
print('ch17 figures ok')
