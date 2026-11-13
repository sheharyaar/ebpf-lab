# Chapter "Capstone: a new data structure, twice" (src/capstone.html): its three drawn figures.
# Drawn to the print rules in NOTES.md "Figure rules": 680 units = 127 mm, words 14.5 units or more,
# Open Sans Condensed for words, Ubuntu Mono for code names, black and grey with one accent.
# Numbers from book/labs/capstone-root.sh, kernel 7.2.15 VM, 13 November 2026 (churn-sketch.dat,
# churn-w272.dat, churn-w68.dat, see.txt); the counters of capstone-rows are rebuilt from
# churn-sketch.dat with the program's hash (cms.h), which reproduces all 100,004 estimates.
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from common import esc, svg, save

SANS = "'Open Sans Condensed', 'Open Sans', 'Myriad Pro', sans-serif"
UMONO = "'Ubuntu Mono', 'JetBrains Mono', monospace"
INK, GREY, ACC, PALE, RULE = '#1F2328', '#4A5056', '#0F6E56', '#F3F4F2', '#867F71'


def t(x, y, s_, size=15, anchor='middle', fam=SANS, weight=None, fill=INK, italic=False):
    w = f' font-weight="{weight}"' if weight else ''
    it = ' font-style="italic"' if italic else ''
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-family="{fam}" '
            f'font-size="{size}" fill="{fill}"{w}{it}>{esc(s_)}</text>')


def line(pts, mid, color=INK, width=1.8, dash=None, arrow=True):
    d = ' '.join(f'{"M" if i == 0 else "L"}{x},{y}' for i, (x, y) in enumerate(pts))
    da = f' stroke-dasharray="{dash}"' if dash else ''
    me = f' marker-end="url(#{mid})"' if arrow else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da}{me}/>'


def rect(x, y, w, h, fill='#FFFFFF', stroke=INK, sw=1.3, dash=None, rx=3):
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}"{da}/>')


# ---------- the sketch: five rows, one light thread and one heavy thread ----------
# Claim: every thread adds to one counter in each of the five rows; its estimate is the smallest of
# the five, which other threads' counts can only raise. Light thread 300652 (3 writes) reads 93;
# heavy thread 300647 (100,000 writes) reads 100,090.
W = 2719
light = [(743, 117), (1232, 138), (266, 111), (2053, 93), (544, 123)]
heavy = [(494, 100102), (1816, 100156), (1345, 100123), (1363, 100090), (2461, 100117)]
m = 'ah-cap-rows'
b = []
X0, X1 = 118, 668
def xs(slot): return X0 + slot / (W - 1) * (X1 - X0)
b.append(rect(14, 6, 20, 16, fill=PALE, stroke=ACC, sw=2.6))
b.append(t(42, 14, 'thread 300652: 3 writes', size=15, anchor='start', fill=ACC, weight='700'))
b.append(rect(250, 6, 20, 16, stroke=GREY, sw=1.6, dash='4 3'))
b.append(t(278, 14, 'thread 300647: 100,000 writes', size=15, anchor='start', fill=GREY))
b.append(t(488, 14, 'a write adds 1 at both marks', size=14.5, anchor='start', fill=GREY, italic=True))
y0 = 64
for r in range(5):
    y = y0 + r * 58
    b.append(t(14, y + 9, f'row {r}', size=15.5, anchor='start', weight='700'))
    b.append(t(14, y + 29, f'seed {r}', size=14.5, anchor='start', fam=UMONO, fill=GREY))
    b.append(rect(X0, y, X1 - X0, 22, fill=PALE, stroke=RULE, sw=1, rx=2))
    hs, hv = heavy[r]
    ls, lv = light[r]
    hx, lx = xs(hs), xs(ls)
    b.append(rect(hx - 6, y - 3, 12, 28, stroke=GREY, sw=1.6, dash='4 3', rx=1))
    b.append(t(hx, y + 38, f'{hv:,}', size=14.5, fill=GREY, fam=UMONO))
    mn = lv == min(v for _, v in light)
    b.append(rect(lx - 6, y - 3, 12, 28, fill=ACC if mn else PALE, stroke=ACC, sw=2.6, rx=1))
    b.append(t(lx, y - 13, f'{lv}' + ('  smallest' if mn else ''), size=15 if mn else 14.5, fill=ACC,
               weight='700' if mn else None, fam=UMONO if not mn else SANS, anchor='middle'))
yb = y0 + 5 * 58 + 6
b.append(t(X0, yb, 'counter 0', size=14.5, anchor='start', fill=GREY))
b.append(t(X1, yb, 'counter 2,718', size=14.5, anchor='end', fill=GREY))
b.append(t(14, yb + 30, 'estimate for 300652: min(117, 138, 111, 93, 123) = 93, against 3 written',
           size=15.5, anchor='start', fill=ACC, weight='700'))
b.append(t(14, yb + 54, 'estimate for 300647: 100,090, against 100,000 written; every row sums to 700,000',
           size=15.5, anchor='start'))
fig = svg(yb + 70, 'A count-min sketch with five rows of 2,719 counters, one update and one query',
          'Five horizontal bars, rows 0 to 4, each standing for 2,719 counters and hashed with its own seed. '
          'Thread 300652, which wrote 3 times, has one counter in each row, holding 117, 138, 111, 93 and 123; '
          'the smallest, 93 in row 3, is its estimate. Thread 300647, which wrote 100,000 times, has counters '
          'holding 100,102, 100,156, 100,123, 100,090 and 100,117; its estimate is 100,090. Every row sums to '
          '700,000, the writes of all threads.', b, m)
save('capstone-rows', fig)


# ---------- the arena: the sketch, its table, and the pointers user space follows ----------
# Claim: the sketch and the table of the heaviest live in one arena; .bss holds the address of the
# sketch, the sketch's header holds the address of the table's first node, each node the next: all
# addresses in the loader's own mapping, followed with plain loads (see.txt).
m = 'ah-cap-arena'
b = []
b.append(t(14, 16, 'the loader’s mapping of the arena: 4 MiB at 0x7fdbcae5e000 (1,024 pages, 28 in use)',
           size=15.5, anchor='start', weight='700'))
# sketch pages 0..26
b.append(rect(14, 40, 470, 120))
b.append(rect(14, 40, 110, 120, fill=PALE, stroke=INK))
b.append(t(69, 60, 'header', size=15.5, weight='700'))
for i, s_ in enumerate(['w = 2719', 'd = 5', 'kmin', 'top']):
    b.append(t(24, 86 + i * 20, s_, size=14.5, anchor='start', fam=UMONO))
b.append(t(304, 62, 'c[5][2719]: the counters', size=15.5, weight='700'))
b.append(t(304, 84, '108,760 bytes, 8 a counter', size=14.5, fill=GREY))
for r in range(5):
    b.append(rect(140, 100 + r * 11, 330, 8, fill=PALE, stroke=RULE, sw=0.8, rx=1))
b.append(t(249, 176, 'pages 0 to 26: 110,592 bytes from bpf_arena_alloc_pages() in init', size=14.5, fill=GREY))
# node page 27
b.append(rect(500, 40, 166, 120))
b.append(t(583, 58, 'page 27', size=15.5, weight='700'))
b.append(t(583, 176, 'from bpf_alloc()', size=14.5, fill=GREY))
for i in range(4):
    y = 74 + i * 20
    b.append(rect(516, y, 134, 16, fill=PALE if i else '#FFFFFF', stroke=ACC, sw=2.0 if i == 0 else 1.2, rx=2))
    b.append(t(583, y + 8, 'next · tid · est' if i < 3 else '… 16 nodes', size=14, fam=UMONO if i < 3 else SANS))
for i in range(3):
    b.append(line([(652, 82 + i * 20), (660, 82 + i * 20), (660, 92 + i * 20), (652, 92 + i * 20)], m,
                  color=ACC, width=1.4))
# top -> first node
b.append(line([(66, 148), (66, 200), (494, 200), (494, 82), (514, 82)], m, color=ACC, width=2.2))
b.append(t(280, 214, 'top = 0x7fdbcae79e78, the first node', size=14.5, fill=ACC, fam=UMONO))
# .bss
b.append(rect(14, 252, 230, 44, fill=PALE))
b.append(t(129, 266, '.bss: one page, mmap()ed', size=15, weight='700'))
b.append(t(129, 285, 'g.sk = 0x7fdbcae5e000', size=14.5, fam=UMONO))
b.append(line([(30, 252), (30, 162)], m, width=2.0))
b.append(t(262, 262, 'the program stores each pointer as an address of this mapping;', size=14.5,
           anchor='start', fill=GREY, italic=True))
b.append(t(262, 282, 'the loader reads all of it with loads, and no bpf() call', size=14.5, anchor='start',
           fill=GREY, italic=True))
fig = svg(304, 'The sketch and the table of the heaviest in one arena, as the loader sees them',
          'The loader maps the arena, 4 MiB at 0x7fdbcae5e000, of which 28 pages are in use. Pages 0 to 26, '
          '110,592 bytes from bpf_arena_alloc_pages, hold the sketch: a header with w = 2719, d = 5, kmin and '
          'top, then five rows of 2,719 eight-byte counters, 108,760 bytes. Page 27, from bpf_alloc, holds the '
          'sixteen nodes of the table, each with next, tid and est, linked by next. The header\'s top holds '
          '0x7fdbcae79e78, the first node. The program\'s .bss, one page mapped by the loader, holds g.sk = '
          '0x7fdbcae5e000. Every pointer is an address in the loader\'s mapping, so it reads everything with '
          'loads and no bpf() call.', b, m)
save('capstone-arena', fig)


# ---------- accuracy against the bound ----------
# Claim: at each width every one of the 100,004 errors stayed under e*N/w, and the typical error was
# about a seventh of it; narrowing the sketch tenfold multiplies the error tenfold.
m = 'ah-cap-acc'
b = []
rows = [(2719, 33, 90, 144, 700), (272, 903, 1041, 1176, 6996), (68, 4104, 4287, 4614, 27982)]
LX0, LX1 = 170, 640
lo, hi = math.log10(10), math.log10(100000)
def lx(v): return LX0 + (math.log10(v) - lo) / (hi - lo) * (LX1 - LX0)
for v in [10, 100, 1000, 10000, 100000]:
    x = lx(v)
    b.append(f'<line x1="{x}" y1="34" x2="{x}" y2="236" stroke="#D9D6CF" stroke-width="1"/>')
    b.append(t(x, 252, f'{v:,}', size=14.5, fill=GREY))
b.append(t(LX0 + (LX1 - LX0) / 2, 274, 'estimate minus true count, over all 100,004 threads (log scale)',
           size=15, fill=INK))
b.append(t(14, 16, 'width w', size=15, anchor='start', weight='700'))
b.append(t(LX0, 16, 'bar: smallest to largest error · dot: median · accent: bound e × 700,000 / w', size=14.5,
           anchor='start', fill=GREY, italic=True))
for i, (w, mn, md, mx, bd) in enumerate(rows):
    y = 64 + i * 66
    b.append(t(14, y, f'{w:,}', size=16, anchor='start', weight='700', fam=UMONO))
    b.append(t(14, y + 20, f'{w * 5 * 8:,} bytes', size=14.5, anchor='start', fill=GREY))
    b.append(f'<line x1="{lx(mn)}" y1="{y}" x2="{lx(mx)}" y2="{y}" stroke="{INK}" stroke-width="7" '
             f'stroke-linecap="butt"/>')
    b.append(f'<circle cx="{lx(md)}" cy="{y}" r="6" fill="#FFFFFF" stroke="{INK}" stroke-width="2"/>')
    b.append(f'<line x1="{lx(bd)}" y1="{y - 16}" x2="{lx(bd)}" y2="{y + 16}" stroke="{ACC}" stroke-width="3.2"/>')
    b.append(t(lx(md), y + 22, f'median {md:,}, largest {mx:,}', size=14.5, fill=INK))
    b.append(t(lx(bd) - 6, y - 22, f'bound {bd:,}', size=14.5, fill=ACC, weight='700', anchor='end'))
fig = svg(284, 'Errors of the arena sketch at three widths against the bound',
          'Three rows on a logarithmic scale of the error from 10 to 100,000, one for each width. Width 2,719 '
          '(108,760 bytes): errors from 33 to 144, median 90, bound 700. Width 272 (10,880 bytes): errors from '
          '903 to 1,176, median 1,041, bound 6,996. Width 68 (2,720 bytes): errors from 4,104 to 4,614, median '
          '4,287, bound 27,982. No error reaches its bound.', b, m)
save('capstone-accuracy', fig)
