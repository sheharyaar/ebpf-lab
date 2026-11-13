# Chapter "One proof by hand, one bug by solver" (src/proof.html): its three drawn figures.
# Drawn to the print rules in NOTES.md "Figure rules": 680 units = 127 mm, words 14.5 units or more,
# Open Sans Condensed for words, Ubuntu Mono for code names, black and grey with one accent.
# Numbers in proof-time: measured on the host (AMD Ryzen 7 8845HS, Python 3.14.10, z3-solver 5.4.1),
# 13 November 2026, with book/labs/ch17-check.py, book/labs/proof/prove.py and pitfalls.py.
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


def cell(x, y, w, h, fill='#FFFFFF', stroke=INK, sw=1.2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def rect(x, y, w, h, l1, lines=(), stroke=INK, sw=1.3, mono1=True, fill_text=INK):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#FFFFFF" stroke="{stroke}" stroke-width="{sw}"/>'
    out += t(x + w / 2, y + 20, l1, size=16, fam=UMONO if mono1 else SANS, weight='700', fill=fill_text)
    for i, ln in enumerate(lines):
        out += t(x + w / 2, y + 44 + 19 * i, ln, size=15, fill=GREY)
    return out


def line(pts, mid, color=INK, width=1.8, dash=None, arrow=True):
    d = ' '.join(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}' for i, (x, y) in enumerate(pts))
    da = f' stroke-dasharray="{dash}"' if dash else ''
    me = f' marker-end="url(#{mid})"' if arrow else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da}{me}/>'


# ---------- proof-member: what (v, m) stands for ----------
# Claim: x is in the tnum (v, m) when x with its unknown bits cleared equals v; for 1x0x four of the
# sixteen four-bit values pass the test.
m = 'ah-proof-member'
b = []
cw, ch, x0 = 40, 34, 150
rows = [('the tnum', '1x0x', True), ('value v', '1000', False), ('mask m', '0101', False)]
for r, (label, bits, big) in enumerate(rows):
    y = 14 + r * (ch + 8)
    b.append(t(x0 - 14, y + ch / 2, label, size=15.5, anchor='end'))
    for i, c in enumerate(bits):
        unknown = big and c == 'x'
        b.append(cell(x0 + i * cw, y, cw, ch, fill=ACCL if unknown else '#FFFFFF', stroke=ACC if unknown else INK,
                      sw=2 if unknown else 1.2))
        b.append(t(x0 + i * cw + cw / 2, y + ch / 2, c, size=18 if big else 16, fam=UMONO, weight='700' if big else None,
                   fill=ACC if unknown else INK))
b.append(t(x0 + 2 * cw, 14 + 3 * (ch + 8) + 6, 'bit 3 on the left, bit 0 on the right', size=14.5, fill=GREY, italic=True))
# the test, worked twice
tx = 345
b.append(t(tx, 24, 'the test: x & ~m == v', size=16, anchor='start', fam=UMONO, weight='700'))
b.append(t(tx, 58, 'x = 1101:  1101 & 1010 = 1000', size=15.5, anchor='start', fam=UMONO))
b.append(t(tx + 248, 58, 'in', size=15.5, anchor='start', weight='700', fill=ACC))
b.append(t(tx, 86, 'x = 0101:  0101 & 1010 = 0000', size=15.5, anchor='start', fam=UMONO))
b.append(t(tx + 248, 86, 'not in', size=15.5, anchor='start', weight='700'))
b.append(t(tx, 116, '~m = 1010 keeps the known bits 3 and 1', size=14.5, anchor='start', fill=GREY, italic=True))
# the sixteen values
sy, sw_, sx = 200, 39, 28
b.append(t(340, 176, 'the sixteen four-bit values; the four in 1x0x are filled', size=15, fill=GREY))
for k in range(16):
    inn = (k & 0b1010) == 0b1000
    b.append(cell(sx + k * sw_, sy, sw_, 40, fill=ACCL if inn else '#FFFFFF', stroke=ACC if inn else LIGHT,
                  sw=2.4 if inn else 1))
    b.append(t(sx + k * sw_ + sw_ / 2, sy + 20, str(k), size=16, weight='700' if inn else None, fill=ACC if inn else GREY))
    b.append(t(sx + k * sw_ + sw_ / 2, sy + 56, f'{k:04b}', size=14.5, fam=UMONO, fill=INK if inn else GREY))
fig = svg(284, 'What a tnum stands for',
          'The tnum 1x0x is the pair value 1000, mask 0101. A four-bit x belongs to it when x AND NOT m equals v: '
          '1101 passes, 0101 does not. Of the sixteen values 0 to 15, the members are 8, 9, 12 and 13.', b, m)
save('proof-member', fig)


# ---------- proof-query: what Z3 is asked ----------
# Claim: the assumptions and the negated claim go to the solver together; unsat proves the claim at that
# width, sat comes with a model that breaks it, unknown proves nothing.
m = 'ah-proof-query'
b = []
b.append(rect(14, 10, 318, 104, 'assumptions', ['P and Q are well-formed: v & m == 0', 'x is in P and y is in Q: x & ~m == v'],
              mono1=False))
b.append(rect(348, 10, 318, 104, 'the claim, turned round', ['R = tnum_and(P, Q)', '(x & y) & ~R.m != R.v'], mono1=False))
b.append(line([(173, 114), (173, 140), (300, 140), (300, 160)], m))
b.append(line([(507, 114), (507, 140), (380, 140), (380, 160)], m))
cx, cy, hw, hh = 340, 232, 190, 66
b.append(f'<polygon points="{cx - hw},{cy} {cx},{cy - hh} {cx + hw},{cy} {cx},{cy + hh}" fill="#FFFFFF" stroke="{INK}" '
         f'stroke-width="1.3"/>')
b.append(t(cx, cy - 22, 's.check()', size=16, fam=UMONO, weight='700'))
b.append(t(cx, cy + 2, 'can all of them hold at once', size=15.5))
b.append(t(cx, cy + 22, 'for some n-bit values?', size=15.5))
# no: unsat, down
b.append(line([(cx, cy + hh), (cx, 346)], m, color=ACC, width=3))
b.append(t(cx - 12, cy + hh + 18, 'no', size=15.5, anchor='end', weight='700', fill=ACC))
b.append(rect(190, 348, 300, 70, 'unsat', ['the claim holds for every input of n bits'], stroke=ACC, sw=2.6, fill_text=ACC))
# yes: sat, right
b.append(line([(cx + hw, cy), (cx + hw, 312), (604, 312), (604, 346)], m))
b.append(t(cx + hw + 10, cy - 14, 'yes', size=15.5, anchor='start', weight='700'))
b.append(rect(530, 348, 140, 70, 'sat', ['s.model() breaks it'], stroke=INK, sw=1.3))
# the third answer, as a remark
b.append(t(14, 300, 'a third answer, unknown: a timeout', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(14, 318, 'or a resource limit stopped the', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(14, 336, 'search, and nothing is proved', size=14.5, anchor='start', fill=GREY, italic=True))
fig = svg(430, 'What the solver is asked',
          'Flowchart. Two boxes, the assumptions (P and Q well-formed, x in P, y in Q) and the claim turned round '
          '(x AND y is not in R), both feed s.check(): can all of them hold at once for some n-bit values? No: unsat, '
          'the claim holds for every input of n bits. Yes: sat, and s.model() gives values that break it. A third answer, '
          'unknown, means a timeout or limit stopped the search.', b, m)
save('proof-query', fig)


# ---------- proof-time: time against width ----------
# Claim: the exhaustive check grows about sixteenfold per bit and needs 16 minutes at 8 bits, while Z3 proves
# tnum_add() at 64 bits in under a second; the old multiplication is out of reach for both.
m = 'ah-proof-time'
b = []
X0, X1, Y0, Y1 = 96, 600, 330, 30          # plot box: x from 4 to 64 bits (log2), y from 1e-3 to 1e5 s (log10)
def px(bits): return X0 + (math.log2(bits) - 2) / 4 * (X1 - X0)
def py(sec): return Y0 - (math.log10(sec) + 3) / 8 * (Y0 - Y1)
b.append(f'<rect x="{X0}" y="{Y1}" width="{X1 - X0}" height="{Y0 - Y1}" fill="none" stroke="{GREY}" stroke-width="1"/>')
for e, lab in [(-3, '1 ms'), (-1, '0.1 s'), (1, '10 s'), (3, '1,000 s'), (5, '100,000 s')]:
    y = py(10 ** e)
    b.append(f'<line x1="{X0 - 5}" y1="{y:.1f}" x2="{X0}" y2="{y:.1f}" stroke="{GREY}" stroke-width="1"/>')
    b.append(t(X0 - 9, y, lab, size=14.5, anchor='end', fill=GREY))
for bits in (4, 8, 16, 32, 64):
    x = px(bits)
    b.append(f'<line x1="{x:.1f}" y1="{Y0}" x2="{x:.1f}" y2="{Y0 + 5}" stroke="{GREY}" stroke-width="1"/>')
    b.append(t(x, Y0 + 18, str(bits), size=14.5, fill=GREY))
b.append(t((X0 + X1) / 2, Y0 + 40, 'width of the bit-vectors, in bits', size=15))
day = py(86400)
b.append(f'<line x1="{X0}" y1="{day:.1f}" x2="{X1}" y2="{day:.1f}" stroke="{LIGHT}" stroke-width="1.2" stroke-dasharray="2 4"/>')
b.append(t(X1 - 6, day - 11, 'one day', size=14.5, anchor='end', fill=GREY, italic=True))
# the exhaustive check of tnum_and(), measured, then sixteenfold a bit
chk = [(4, 0.02), (5, 0.23), (6, 3.79), (7, 59.72), (8, 987.12)]
b.append(line([(px(k), py(s_)) for k, s_ in chk], m, color=ACC, width=2.6, arrow=False))
for k, s_ in chk:
    b.append(f'<circle cx="{px(k):.1f}" cy="{py(s_):.1f}" r="4.5" fill="{ACC}"/>')
b.append(line([(px(8), py(987.12)), (px(9.4), py(987.12 * 16 ** 1.4))], m, color=ACC, width=2.2, dash='5 4', arrow=False))
b.append(t(X0 + 10, py(3e4), 'checker, tnum_and:', size=14.5, anchor='start', fill=ACC, weight='700'))
b.append(t(X0 + 10, py(3e4) + 18, '16 min at 8 bits,', size=14.5, anchor='start', fill=ACC, weight='700'))
b.append(t(X0 + 10, py(3e4) + 36, '×16 for each bit more', size=14.5, anchor='start', fill=ACC))
# Z3 on tnum_add(), median of five runs
add = [(8, 0.012), (16, 0.062), (32, 0.131), (64, 0.771)]
b.append(line([(px(k), py(s_)) for k, s_ in add], m, color=INK, width=2.2, arrow=False))
for k, s_ in add:
    b.append(f'<rect x="{px(k) - 4.5:.1f}" y="{py(s_) - 4.5:.1f}" width="9" height="9" fill="{INK}"/>')
b.append(t(px(64) - 8, py(0.771) - 18, 'Z3, tnum_add: 0.77 s', size=14.5, anchor='end', weight='700'))
# Z3 on tnum_and()
andz = [(8, 0.002), (16, 0.003), (32, 0.003), (64, 0.006)]
b.append(line([(px(k), py(s_)) for k, s_ in andz], m, color=GREY, width=1.8, dash='3 3', arrow=False))
for k, s_ in andz:
    b.append(f'<circle cx="{px(k):.1f}" cy="{py(s_):.1f}" r="4" fill="#FFFFFF" stroke="{GREY}" stroke-width="1.6"/>')
b.append(t(px(64) - 8, py(0.006) - 16, 'Z3, tnum_and: 6 ms', size=14.5, anchor='end', fill=GREY))
# Z3 on the multiplication of Linux 5.12
b.append(f'<path d="M{px(8):.1f},{py(13.2) - 6:.1f} l6,6 l-6,6 l-6,-6 z" fill="{INK}"/>')
b.append(t(px(8) + 12, py(13.2) - 8, 'Z3, tnum_mul', size=14.5, anchor='start'))
b.append(t(px(8) + 12, py(13.2) + 10, 'of 5.12: 13 s', size=14.5, anchor='start'))
b.append(f'<path d="M{px(16):.1f},{py(60) - 6:.1f} l6,6 l-6,6 l-6,-6 z" fill="#FFFFFF" stroke="{INK}" stroke-width="1.4"/>')
b.append(line([(px(16), py(60) - 8), (px(16), py(86400) + 8)], m, color=INK, width=1.4))
b.append(t(px(16) + 10, py(60) + 2, 'at 16 bits: no answer in 60 s,', size=14.5, anchor='start', italic=True, fill=GREY))
b.append(t(px(16) + 10, py(60) + 20, 'none in 24 hours (CGO 2022)', size=14.5, anchor='start', italic=True, fill=GREY))
fig = svg(384, 'Time against width',
          'Log-log plot of seconds against bit width from 4 to 64. The exhaustive checker on tnum_and rises from 0.02 s at '
          '4 bits to 987 s at 8 bits, sixteenfold per bit. Z3 proves tnum_add in 0.012 s at 8 bits up to 0.77 s at 64, and '
          'tnum_and in 2 to 6 ms. Z3 proves the multiplication of Linux 5.12 in 13 s at 8 bits and gives no answer within '
          '60 s at 16 bits; the CGO 2022 paper reports none within 24 hours.', b, m)
save('proof-time', fig)
