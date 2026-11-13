# Figures for chapter 6, "How the verifier tracks numbers" (spec §5.3: 680 wide, palette tokens).
# Run from dossier/:  python3 -I figs/ch06.py   ->  figs/out/ch06-*.svg
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

def cells(x0, y, w, h, n, on, col, lab=None, mono=True, size=11):
    """A strip of n cells; cells whose index is in `on` are filled with the colour."""
    out = []
    l, d, xx = C[col]
    for i in range(n):
        filled = i in on
        out.append(f'<rect x="{x0 + i * w}" y="{y}" width="{w - 2}" height="{h}" rx="3" '
                   f'fill="{l if filled else "#FFFFFF"}" stroke="{d if filled else "#C9C6BC"}" stroke-width="{0.9 if filled else 0.6}"/>')
        if lab is not None and filled:
            out.append(tx(x0 + i * w + (w - 2) / 2, y + h / 2, lab(i), size=size, col=col, mono=mono))
    return out

# ---------------- Figure 6.1: two descriptions of one number ----------------
m = 'ah-6-1'
b = []
X0, W, H = 210, 26, 22          # sixteen cells of 26 units from x=210 to 626
for i in range(16):
    b.append(tx(X0 + i * W + 12, 16, str(i), size=10, mono=True))
b.append(tx(40, 16, 'value of r6  →', size=10, anchor='start', italic=True))

def group(y, title, rng, tn, tlabel, rlabel):
    out = [tx(40, y, title, size=12, anchor='start', mono=True, weight='600', col='teal')]
    rows = [('range', rlabel, rng, 'teal'), ('tnum', tlabel, tn, 'purple'),
            ('both allow', '', sorted(set(rng) & set(tn)), 'amber')]
    for k, (name, detail, on, col) in enumerate(rows):
        yy = y + 14 + k * (H + 6)
        out.append(tx(40, yy + H / 2 - (6 if detail else 0), name, size=12, anchor='start', col=col, weight='600'))
        if detail:
            out.append(tx(40, yy + H / 2 + 8, detail, size=10, anchor='start', mono=True, col=col))
        out += cells(X0, yy, W, H, 16, set(on), col)
    return out

b += group(42, 'after  if r6 > 7  (fd < 8)', range(0, 8), range(0, 8), '0xxx · (0x0; 0x7)', '[0, 7]')
b += group(156, 'after  if r6 > 8  (fd <= 8)', range(0, 9), range(0, 16), 'xxxx · (0x0; 0xf)', '[0, 8]')
# callout for the cells only the tnum allows
b.append(f'<path d="M{X0 + 9 * W},{252} v6 H{X0 + 16 * W - 2} v-6" fill="none" stroke="{C["purple"][1]}" stroke-width="1"/>')
b.append(tx(X0 + 12.5 * W, 268, 'the tnum alone also allows 9 to 15', size=11, col='purple'))
b.append(bar(282, 30, 'The kernel keeps both descriptions and trusts only the values both allow.'))
fig1 = svg(322, 'A range and a tnum describing the same register',
           'Two groups of sixteen cells: after the test fd < 8 the range and the tnum agree on 0 to 7; after fd <= 8 the range says 0 to 8 and the tnum 0 to 15', b, m)

# ---------------- Figure 6.2: one test narrows a range (step widget) ----------------
m = 'ah-6-2'
b = []
CX, CW, CH = 150, 24, 22        # sixteen cells from x=150 to 534, then a break, then the rest
FAR0, FAR1 = 556, 640
def axis(step):
    out = [f'<g data-step="{step}">']
    for i in range(16):
        out.append(tx(CX + i * CW + 11, 44, str(i), size=10, mono=True))
    out.append(tx(546, 44, '…', size=11))
    out.append(tx((FAR0 + FAR1) / 2, 44, '16 … 2⁶⁴−1', size=10, mono=True))
    return out + ['</g>']

def row(y, step, label, on, col, far=False, detail=None):
    l, d, xx = C[col]
    out = [f'<g data-step="{step}">', tx(40, y + CH / 2 - (6 if detail else 0), label, size=11, anchor='start', col=col, weight='600')]
    if detail:
        out.append(tx(40, y + CH / 2 + 8, detail, size=10, anchor='start', col=col, mono=True))
    out += cells(CX, y, CW, CH, 16, set(on), col)
    out.append(f'<path d="M538,{y + 4} l6,-6 M542,{y + CH + 2} l6,-6" stroke="#9A978E" stroke-width="1"/>')
    out.append(f'<rect x="{FAR0}" y="{y}" width="{FAR1 - FAR0}" height="{CH}" rx="3" fill="{l if far else "#FFFFFF"}" '
               f'stroke="{d if far else "#C9C6BC"}" stroke-width="{0.9 if far else 0.6}"/>')
    return out + ['</g>']

codes = {1: ('slot 3:   r6 = *(u64 *)(r6 + 16)', 'the descriptor fd'),
         2: ('slot 10:  if r6 > 0x7 goto pc+5', 'the walk splits in two'),
         3: ('slot 10, fall-through side', 'the test proved r6 ≤ 7'),
         4: ('slots 11 to 13:  r6 <<= 3;  r0 += r6;  read', 'the address')}
for k, (c, note) in codes.items():
    b.append(tx(40, 18, c, size=12, anchor='start', mono=True, weight='600', col='teal', step=str(k)))
    b.append(tx(640, 18, note, size=11, anchor='end', italic=True, step=str(k)))
b += axis('1,2,3')
b += row(56, '1', 'r6', range(16), 'teal', far=True, detail='any value')
b += row(56, '2', 'jumps away', range(8, 16), 'gray', far=True, detail='r6 > 7: to exit')
b += row(88, '2', 'falls through', range(0, 8), 'teal', detail='r6 ≤ 7')
b += row(56, '3', 'range', range(0, 8), 'teal', detail='[0, 7]')
b += row(88, '3', 'tnum', range(0, 8), 'purple', detail='…0000xxx')
logs = {1: '3: (79) r6 = *(u64 *)(r6 +16)    ; R6=scalar()',
        2: '10: (25) if r6 > 0x7 goto pc+5',
        3: 'R6=scalar(smin=smin32=0,smax=umax=smax32=umax32=7,var_off=(0x0; 0x7))',
        4: 'R0=map_value(…,vs=64,smin=smin32=0,smax=umax=smax32=umax32=56,var_off=(0x0; 0x38))'}
for k, t in logs.items():
    b.append(tx(40, 134, t, size=10.5, anchor='start', mono=True, col='gray', step=str(k)))
# step 4: the 64-byte value as eight counters, and the reads the range allows
V0, VW = 150, 48
g = ['<g data-step="4">', tx(40, 66, 'the value', size=11, anchor='start', col='teal', weight='600'),
     tx(40, 80, '64 bytes', size=10, anchor='start', col='teal', mono=True)]
for i in range(8):
    # plain rect and text: frames() cannot cut a step group that contains a nested <g>
    g.append(f'<rect x="{V0 + i * VW}" y="56" width="{VW - 2}" height="30" rx="6" fill="{C["teal"][0]}" stroke="{C["teal"][1]}" stroke-width="0.9"/>')
    g.append(tx(V0 + i * VW + (VW - 2) / 2, 71, f'n[{i}]', size=11, mono=True, col='teal', weight='600'))
    g.append(tx(V0 + i * VW, 96, str(i * 8), size=10, mono=True))
g.append(tx(V0 + 8 * VW - 2, 96, '64', size=10, mono=True, weight='600'))
ad = C['amber'][1]
g.append(f'<path d="M{V0},{106} v6 H{V0 + 7 * VW} v-6" fill="none" stroke="{ad}" stroke-width="1.4"/>')
g.append(f'<path d="M{V0 + 7 * VW},{112} H{V0 + 8 * VW - 2}" stroke="{ad}" stroke-width="2.4" marker-end="url(#{m})"/>')
g.append(tx(V0 + 3.5 * VW, 121, 'offsets 0 to 56 the range allows', size=10.5, col='amber'))
g.append(tx(560, 116, '56 + 8 = 64: inside', size=11, col='amber', weight='600', anchor='start'))
g.append('</g>')
b += g
fig2 = svg(148, 'One test narrows the range of r6',
           'Four frames: r6 holds any value, the test splits the walk, the fall-through side knows 0 to 7, and the reads stay inside the 64-byte value', b, m)

# ---------------- Figure 6.3: sound, and how precise ----------------
m = 'ah-6-3'
b = []
X0, W, H = 230, 48, 24
b.append(tx(40, 18, 'r1 holds 1 or 3: tnum 00x1.   Then  r1 += 1.', size=12, anchor='start', mono=True, weight='600', col='teal'))
for i in range(8):
    b.append(tx(X0 + i * W + (W - 2) / 2, 44, str(i), size=11, mono=True))
rows3 = [('real results', '1+1 and 3+1', {2, 4}, 'amber', None),
         ('tnum_add() says', '0xx0', {0, 2, 4, 6}, 'purple', 'sound: holds both real results; imprecise: 0 and 6 never happen'),
         ('a buggy answer', '0010', {2}, 'coral', 'unsound: misses 4, so a check passes that should fail')]
for k, (name, detail, on, col, note) in enumerate(rows3):
    y = 56 + k * 52
    b.append(tx(40, y + H / 2 - 6, name, size=12, anchor='start', col=col, weight='600'))
    b.append(tx(40, y + H / 2 + 8, detail, size=10, anchor='start', col=col, mono=True))
    b += cells(X0, y, W, H, 8, on, col)
    if note:
        b.append(tx(X0, y + H + 12, note, size=11, anchor='start', col=col, italic=True))
b.append(bar(206, 30, 'Too wide costs a safe program its load. Too narrow lets an unsafe one in.'))
fig3 = svg(246, 'Sound and precise, on one addition',
           'Three rows of eight cells: the real results 2 and 4, the tnum answer 0, 2, 4, 6, and an unsound answer that misses 4', b, m)

# ---------------- Figure 6.4: one arc, two readings (v7.2 circular range) ----------------
m = 'ah-6-4'
b = []
cx, cy, r = 175, 150, 92
def pt(k, rr):
    a = math.radians(-90 + k * 22.5)
    return cx + rr * math.cos(a), cy + rr * math.sin(a)
b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#C9C6BC" stroke-width="1.2"/>')
arc = {14, 15, 0, 1, 2}
# the arc itself, clockwise from 14 to 2
x1, y1 = pt(14, r); x2, y2 = pt(2, r)
b.append(f'<path d="M{x1:.1f},{y1:.1f} A{r},{r} 0 0 1 {x2:.1f},{y2:.1f}" fill="none" stroke="{C["amber"][1]}" stroke-width="5" stroke-linecap="round"/>')
for k in range(16):
    px, py = pt(k, r)
    on = k in arc
    b.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{4.5 if on else 3}" fill="{C["amber"][1] if on else "#FFFFFF"}" stroke="{C["amber"][1] if on else "#9A978E"}" stroke-width="1"/>')
    ox, oy = pt(k, r + 18)
    b.append(tx(round(ox, 1), round(oy, 1), str(k), size=11, mono=True, col='teal' if on else None, weight='600' if on else None))
    ix, iy = pt(k, r - 20)
    s = k if k < 8 else k - 16
    b.append(tx(round(ix, 1), round(iy, 1), str(s).replace('-', '−'), size=10, mono=True, col='purple' if on else None))
b.append(tx(cx, cy - 8, 'outside: unsigned', size=10, col='teal'))
b.append(tx(cx, cy + 8, 'inside: signed', size=10, col='purple'))
R0 = 340
b.append(tx(R0, 36, 'One arc: first value 14, then 4 more', size=12, anchor='start', weight='600', col='amber'))
b.append(tx(R0, 54, 'holds 14, 15, 0, 1, 2', size=11, anchor='start', mono=True, col='amber'))
b.append(tx(R0, 90, 'read as signed', size=12, anchor='start', weight='600', col='purple'))
b.append(tx(R0, 108, '−2 to 2: five values, exact', size=11, anchor='start', col='purple'))
b.append(tx(R0, 144, 'read as unsigned, with a min and a max', size=12, anchor='start', weight='600', col='teal'))
b.append(tx(R0, 162, '0 to 15: the arc crosses 15 → 0,', size=11, anchor='start', col='teal'))
b.append(tx(R0, 178, 'so a pair of bounds must take everything', size=11, anchor='start', col='teal'))
b.append(tx(R0, 214, 'v7.1 kept both pairs and reconciled them;', size=11, anchor='start', italic=True))
b.append(tx(R0, 230, 'v7.2 keeps the arc and reads both off it.', size=11, anchor='start', italic=True))
fig4 = svg(268, 'A circular range on four bits',
           'A circle of sixteen values with an arc from 14 to 2: signed it is minus 2 to 2, unsigned bounds would have to cover 0 to 15', b, m)

save('ch06-narrow', fig2)
for i, f in enumerate(frames(fig2, 'ah-6-2', (1, 2, 3, 4)), 1):
    save(f'ch06-narrow-twin{i}', f)
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

# ---------- Figure 6.2 for print: one shared axis, one row per step (replaces the four frames) ----------
m = 'ah-6-2p'
b = [markers(m)]
LX, SX, SW_, SH = 8, 128, 29, 26       # label column from x=8; sixteen cells of 29 from x=128; cell height
FX0, FX1 = 610, 676                    # the cell for 16 … 2^64-1, after a break
ACC_FILL, GREY_FILL = '#DCEFE8', '#E4E6E8'
def cell(x, y, w, kind):
    if kind == 'a':                    # values the fall-through path keeps: accent, heavier line
        return f'<rect x="{x}" y="{y}" width="{w}" height="{SH}" rx="3" fill="{ACC_FILL}" stroke="{P2}" stroke-width="1.6"/>'
    if kind == 'g':                    # values on a path that leaves, or before the test
        return f'<rect x="{x}" y="{y}" width="{w}" height="{SH}" rx="3" fill="{GREY_FILL}" stroke="{GREY}" stroke-width="1"/>'
    return f'<rect x="{x}" y="{y}" width="{w}" height="{SH}" rx="3" fill="#FFFFFF" stroke="#C9CCCF" stroke-width="0.8"/>'
def strip(y, label, detail, on, kind, far=False, inner=None, upto=16, accent=False):
    out = [t(LX, y + SH / 2 - 9, label, size=15, anchor='start', weight='700', fill=P2 if accent else INK),
           t(LX, y + SH / 2 + 10, detail, size=14.5, anchor='start', fam=UMONO, fill=P2 if accent else GREY)]
    for i in range(upto):
        out.append(cell(SX + i * SW_, y, SW_ - 2, kind if i in on else None))
        if inner and i in on:
            out.append(t(SX + i * SW_ + (SW_ - 2) / 2, y + SH / 2, inner(i), size=14.5, fam=UMONO, fill=P2))
    if upto == 16:
        out.append(f'<path d="M593,{y + SH - 4} l7,-8 M601,{y + SH - 4} l7,-8" stroke="{GREY}" stroke-width="1"/>')
        out.append(cell(FX0, y, FX1 - FX0, kind if far else None))
    return out
def head(y, code, note):
    return [t(LX, y, code, size=16, anchor='start', fam=UMONO, weight='700'), t(676, y, note, size=14.5, anchor='end', italic=True, fill=GREY)]
def log(y, s_):
    return [t(LX, y, s_, size=14.5, anchor='start', fam=UMONO, fill=GREY).replace('<text ', '<text xml:space="preserve" ')]
# the shared axis: the values r6 can hold
b.append(t(LX, 14, 'values of r6', size=14.5, anchor='start', italic=True, fill=GREY))
for i in range(16):
    b.append(t(SX + i * SW_ + (SW_ - 2) / 2, 14, str(i), size=14.5, fam=UMONO))
b.append(t((FX0 + FX1) / 2, 14, '16 … 2⁶⁴−1', size=14.5, fam=UMONO))
def rule(y): return f'<line x1="{LX}" y1="{y}" x2="676" y2="{y}" stroke="#C9CCCF" stroke-width="1"/>'
b.append(f'<line x1="{LX}" y1="28" x2="676" y2="28" stroke="{INK}" stroke-width="1.3"/>')
# slot 3: the descriptor, any value
b += head(44, 'slot 3:  r6 = *(u64 *)(r6 + 16)', 'the descriptor fd')
b += strip(62, 'r6', 'any value', range(16), 'g', far=True)
b += log(104, '3: (79) r6 = *(u64 *)(r6 +16)    ; R6=scalar()')
b.append(rule(120))
# slot 10: the walk splits in two
b += head(136, 'slot 10:  if r6 > 0x7 goto pc+5', 'the walk splits in two')
b += strip(154, 'jumps away', 'r6 > 7: to exit', range(8, 16), 'g', far=True)
b += strip(192, 'falls through', 'r6 ≤ 7', range(8), 'a', accent=True)
b += log(234, '10: (25) if r6 > 0x7 goto pc+5')
b.append(rule(250))
# slot 10, the fall-through side: range and tnum
b += head(266, 'slot 10, fall-through side', 'the test proved r6 ≤ 7')
b += strip(284, 'range', '[0, 7]', range(8), 'a', accent=True)
b += strip(322, 'tnum', '…0000xxx', range(8), 'a', accent=True)
b += log(364, 'R6=scalar(smin=smin32=0,smax=umax=smax32=umax32=7,var_off=(0x0; 0x7))')
b.append(rule(380))
# slots 11 to 13: shift, add, read; the offsets land inside the 64-byte value
b += head(396, 'slots 11 to 13:  r6 <<= 3;  r0 += r6;  read', 'the address')
b += strip(414, 'r6 after the shift', '0 to 56', range(8), 'a', inner=lambda i: str(8 * i), upto=8, accent=True)
b.append(t(SX + 8 * SW_ + 12, 414 + SH / 2, 'offsets 0 to 56 the range allows', size=14.5, anchor='start', fill=P2))
VY = 452
b += [t(LX, VY + SH / 2 - 9, 'the value', size=15, anchor='start', weight='700'),
      t(LX, VY + SH / 2 + 10, '64 bytes', size=14.5, anchor='start', fam=UMONO, fill=GREY)]
for i in range(8):
    b.append(f'<rect x="{SX + i * SW_}" y="{VY}" width="{SW_ - 2}" height="{SH}" rx="3" fill="#FFFFFF" stroke="{INK}" stroke-width="1.2"/>')
b += [t(SX + 4 * SW_ - 1, VY + SH + 14, 'n[0] … n[7]', size=14.5, fam=UMONO),
      f'<line x1="{SX + 8 * SW_ - 1}" y1="{VY - 6}" x2="{SX + 8 * SW_ - 1}" y2="{VY + SH + 6}" stroke="{INK}" stroke-width="2.4"/>',
      t(SX + 8 * SW_ - 1, VY + SH + 16, '64', size=14.5, fam=UMONO, weight='700'),
      t(SX + 8 * SW_ + 12, VY + SH / 2, '56 + 8 = 64: inside', size=15, anchor='start', weight='700', fill=P2)]
b += log(VY + SH + 36, 'R0=map_value(…,vs=64,smin=smin32=0,smax=umax=smax32=umax32=56,var_off=(0x0; 0x38))')
H62 = VY + SH + 52
fig2p = svg(H62, 'One test narrows the range of r6, on one axis',
            'Rows on one axis of the values 0 to 15 and beyond: after slot 3 r6 may hold any value; slot 10 splits the walk, with 8 and up '
            'jumping to the exit and 0 to 7 falling through; on the fall-through side the range is 0 to 7 and the tnum ends in three unknown '
            'bits; after the shift the offsets 0 to 56 stay inside the 64-byte value, since 56 + 8 = 64.', b, m)
save('ch06-narrow-print', fig2p)
# ---------- shared by Figures 6.1, 6.3 and 6.4 for print ----------
def hd(x, y, parts, size=16, anchor='start'):
    """A heading in mixed faces, bold: parts are (text, face) with face 'm' for code."""
    sp = ''.join(f'<tspan font-family="{UMONO if f == "m" else SANS}">{esc(s_)}</tspan>' for s_, f in parts)
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-size="{size}" font-weight="700" '
            f'fill="{INK}" xml:space="preserve">{sp}</text>')
def cellk(x, y, w, h, kind):
    if kind == 'a':                    # what the figure is about: accent, heavier line
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{ACC_FILL}" stroke="{P2}" stroke-width="1.8"/>'
    if kind == 'g':
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{GREY_FILL}" stroke="{GREY}" stroke-width="1"/>'
    if kind == 'm':                    # a value that should be there and is not
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#FFFFFF" stroke="{P2}" stroke-width="1.8" stroke-dasharray="4 3"/>'
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#FFFFFF" stroke="#C9CCCF" stroke-width="0.8"/>'

# ---------- Figure 6.1 for print: two descriptions of one number, on one axis ----------
m = 'ah-6-1p'
b = []
SX1, SW1, SH1 = 150, 32, 26            # sixteen cells of 32 from x=150 to 662
def row61(y, label, detail, on, kind, accent=False):
    out = [t(LX, y + SH1 / 2 - (9 if detail else 0), label, size=15, anchor='start', weight='700', fill=P2 if accent else INK)]
    if detail:
        out.append(t(LX, y + SH1 / 2 + 10, detail, size=14.5, anchor='start', fam=UMONO, fill=GREY))
    out += [cellk(SX1 + i * SW1, y, SW1 - 3, SH1, kind if i in on else None) for i in range(16)]
    return out
b.append(t(LX, 14, 'values of r6', size=14.5, anchor='start', italic=True, fill=GREY))
for i in range(16):
    b.append(t(SX1 + i * SW1 + (SW1 - 3) / 2, 14, str(i), size=14.5, fam=UMONO))
b.append(f'<line x1="{LX}" y1="28" x2="676" y2="28" stroke="{INK}" stroke-width="1.3"/>')
def group61(y, test, src, rng, tn, rlab, tlab):
    out = [hd(LX, y, [('after  ', 's'), (test, 'm'), ('   (', 's'), (src, 'm'), (')', 's')])]
    out += row61(y + 22, 'range', rlab, set(rng), 'g')
    out += row61(y + 62, 'tnum', tlab, set(tn), 'g')
    out += row61(y + 102, 'both allow', None, set(rng) & set(tn), 'a', accent=True)
    return out
b += group61(46, 'if r6 > 7', 'fd < 8', range(0, 8), range(0, 8), '[0, 7]', '0xxx · (0x0; 0x7)')
b.append(f'<line x1="{LX}" y1="186" x2="676" y2="186" stroke="#C9CCCF" stroke-width="1"/>')
b += group61(204, 'if r6 > 8', 'fd <= 8', range(0, 9), range(0, 16), '[0, 8]', 'xxxx · (0x0; 0xf)')
bx0, bx1 = SX1 + 9 * SW1, SX1 + 16 * SW1 - 3
b.append(f'<path d="M{bx0},{338} v6 H{bx1} v-6" fill="none" stroke="{INK}" stroke-width="1.2"/>')
b.append(t((bx0 + bx1) / 2, 358, 'the tnum alone also allows 9 to 15', size=14.5))
fig61p = svg(372, 'A range and a tnum describing the same register',
             'Two groups of rows on the values 0 to 15. After if r6 > 7 (fd < 8): the range [0, 7] and the tnum 0xxx, (0x0; 0x7), '
             'both allow 0 to 7. After if r6 > 8 (fd <= 8): the range [0, 8] allows 0 to 8, the tnum xxxx, (0x0; 0xf), allows 0 to 15, '
             'and both allow 0 to 8; the tnum alone also allows 9 to 15.', b, m)
save('ch06-twodesc', fig61p)

# ---------- Figure 6.3 for print: one addition, three answers ----------
# The real results are the accent wherever they appear: filled where an answer holds them, dashed where it misses one.
m = 'ah-6-3p'
b = []
SX3, SW3, SH3 = 176, 58, 28            # eight cells of 58 from x=176 to 640
b.append(hd(LX, 14, [('r1', 'm'), (' holds 1 or 3: tnum ', 's'), ('00x1', 'm'), ('.   Then  ', 's'), ('r1 += 1', 'm'), ('.', 's')]))
for i in range(8):
    b.append(t(SX3 + i * SW3 + (SW3 - 4) / 2, 44, str(i), size=14.5, fam=UMONO))
b.append(f'<line x1="{LX}" y1="58" x2="676" y2="58" stroke="{INK}" stroke-width="1.3"/>')
def row63(y, label, detail, kinds, note=None):
    out = [hd(LX, y + SH3 / 2 - 9, label, size=15),
           t(LX, y + SH3 / 2 + 11, detail, size=14.5, anchor='start', fam=UMONO, fill=GREY)]
    out += [cellk(SX3 + i * SW3, y, SW3 - 4, SH3, kinds.get(i)) for i in range(8)]
    if note:
        out.append(t(SX3, y + SH3 + 16, note, size=14.5, anchor='start', italic=True))
    return out
b += row63(70, [('real results', 's')], '1+1 and 3+1', {2: 'a', 4: 'a'})
b += row63(126, [('tnum_add()', 'm'), (' says', 's')], '0xx0', {0: 'g', 2: 'a', 4: 'a', 6: 'g'},
           'sound: holds both real results; imprecise: 0 and 6 never happen')
b += row63(200, [('a buggy answer', 's')], '0010', {2: 'a', 4: 'm'},
           'unsound: misses 4, so a check passes that should fail')
LY = 278
b.append(f'<line x1="{LX}" y1="{LY - 16}" x2="676" y2="{LY - 16}" stroke="#C9CCCF" stroke-width="1"/>')
for x, kind, s_ in [(LX, 'a', 'a real result'), (186, 'g', 'a value that never happens'), (420, 'm', 'a real result left out')]:
    b += [cellk(x, LY - 10, 26, 20, kind), t(x + 34, LY, s_, size=14.5, anchor='start')]
fig63p = svg(LY + 18, 'Sound and precise, on one addition',
             'r1 holds 1 or 3, tnum 00x1, then r1 += 1. Three rows on the values 0 to 7: the real results, 1+1 and 3+1, are 2 and 4; '
             'tnum_add() says 0xx0, which allows 0, 2, 4 and 6: sound, it holds both real results, but imprecise, 0 and 6 never happen; '
             'a buggy answer, 0010, allows only 2: unsound, it misses 4, so a check passes that should fail.', b, m)
save('ch06-sound', fig63p)

# ---------- Figure 6.4 for print: one arc, two readings ----------
m = 'ah-6-4p'
b = []
ccx, ccy, cr = 168, 150, 96
def cpt(k, rr):
    a = math.radians(-90 + k * 22.5)
    return ccx + rr * math.cos(a), ccy + rr * math.sin(a)
ARC = {14, 15, 0, 1, 2}
b.append(f'<circle cx="{ccx}" cy="{ccy}" r="{cr}" fill="none" stroke="#9AA0A6" stroke-width="1.3"/>')
x1, y1 = cpt(14, cr); x2, y2 = cpt(2, cr)
b.append(f'<path d="M{x1:.1f},{y1:.1f} A{cr},{cr} 0 0 1 {x2:.1f},{y2:.1f}" fill="none" stroke="{P2}" stroke-width="6" stroke-linecap="round"/>')
for k in range(16):
    on = k in ARC
    px, py = cpt(k, cr)
    b.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{5.5 if on else 3.5}" fill="{P2 if on else "#FFFFFF"}" '
             f'stroke="{P2 if on else GREY}" stroke-width="1.2"/>')
    ox, oy = cpt(k, cr + 21)
    b.append(t(round(ox, 1), round(oy, 1), str(k), size=14.5, fam=UMONO, weight='700' if on else None, fill=P2 if on else INK))
    ix, iy = cpt(k, cr - 23)
    sv = k if k < 8 else k - 16
    b.append(t(round(ix, 1), round(iy, 1), str(sv).replace('-', '−'), size=14.5, fam=UMONO, weight='700' if on else None,
               fill=P2 if on else GREY))
b += [t(ccx, ccy - 10, 'outside: unsigned', size=14.5, italic=True), t(ccx, ccy + 10, 'inside: signed', size=14.5, italic=True, fill=GREY)]
R0 = 330
b += [t(R0, 36, 'One arc: first value 14, then 4 more', size=15, anchor='start', weight='700', fill=P2),
      t(R0, 56, 'holds 14, 15, 0, 1, 2', size=14.5, anchor='start', fam=UMONO),
      t(R0, 92, 'read as signed', size=15, anchor='start', weight='700'),
      t(R0, 112, '−2 to 2: five values, exact', size=14.5, anchor='start'),
      t(R0, 148, 'read as unsigned, with a min and a max', size=15, anchor='start', weight='700'),
      t(R0, 168, '0 to 15: the arc crosses 15 → 0,', size=14.5, anchor='start'),
      t(R0, 186, 'so a pair of bounds must take everything', size=14.5, anchor='start'),
      t(R0, 222, 'v7.1 kept both pairs and reconciled them;', size=14.5, anchor='start', italic=True, fill=GREY),
      t(R0, 240, 'v7.2 keeps the arc and reads both off it.', size=14.5, anchor='start', italic=True, fill=GREY)]
fig64p = svg(282, 'A circular range on four bits',
             'A circle of sixteen values, unsigned 0 to 15 outside and signed −8 to 7 inside, with a thick arc from 14 to 2 holding '
             '14, 15, 0, 1 and 2: read as signed it is −2 to 2, five values, exact; read as unsigned with a min and a max it must be '
             '0 to 15, since the arc crosses 15 to 0. v7.1 kept both pairs and reconciled them; v7.2 keeps the arc and reads both off it.', b, m)
save('ch06-circle', fig64p)
print('ch06 figures ok')
