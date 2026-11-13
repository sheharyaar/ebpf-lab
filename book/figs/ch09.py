# Figures for chapter 9, redrawn for print (figure rules in NOTES.md): 680 units = 127 mm,
# words 14.5 units or more, node titles 16, black and grey with the one accent.
# The screen versions are kept in figs/pre-print/ch09.py.
# Figure 9.4 (three ways into one map) is now an HTML table in src/ch09.html; figs/out/ch09-share.svg is no longer used.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

# ---------- print helpers, as for Figure 4.2 (figs/ch04.py) ----------
SANS = "'Open Sans Condensed', 'Open Sans', 'Myriad Pro', sans-serif"
UMONO = "'Ubuntu Mono', 'JetBrains Mono', monospace"
INK, GREY, P2 = '#1F2328', '#4A5056', '#0F6E56'
ACC_FILL, GREY_FILL, BOX_FILL = '#DCEFE8', '#E4E6E8', '#EEF0F1'
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

# ---------- Figure 9.2: the write_counts map in kernel memory, a box diagram ----------
# The accent marks one thing: where a value sits in its element (thick outline and a measured line, so it reads in grey).
m = 'ah-9-2p'
b = [markers(m)]
# struct bpf_htab, with struct bpf_map inside
b += [rect(8, 8, 240, 228, stroke=GREY, sw=1.2, fill=BOX_FILL),
      tm(128, 26, [('struct bpf_htab', 'm'), (' · 896 B', 's')], size=16, weight='700'),
      rect(20, 42, 216, 132), t(128, 60, 'struct bpf_map', size=16, fam=UMONO, weight='700')]
fields = [[('type', 'm'), ('  hash', 's')],
          [('key', 'm'), (' 4 B · ', 's'), ('value', 'm'), (' 8 B', 's')],
          [('max_entries', 'm'), ('  1024', 's')],
          [('id', 'm'), ('  7 · two counts', 's')],
          [('ops', 'm')]]
for k, parts in enumerate(fields):
    b.append(tm(32, 82 + k * 19, parts, anchor='start'))
b += [tm(32, 194, [('hashrnd', 'm'), ('  a random seed', 's')], anchor='start'),
      tm(32, 214, [('buckets', 'm'), (' · ', 's'), ('elems', 'm'), (' · ', 's'), ('freelist', 'm')], anchor='start')]
# the ops pointer, out to the table of functions
OY = 82 + 4 * 19
b += [f'<circle cx="62" cy="{OY}" r="3" fill="{INK}"/>',
      line([(62, OY), (266, OY), (266, 293), (288, 293)], m + '-k', width=1.5)]
# the buckets
BX, BW, BH, BP = 290, 150, 24, 28
b.append(tm(BX + BW / 2, 26, [('buckets', 'm'), (' · 1024 × 16 B', 's')], size=16, weight='700'))
for k, lab in enumerate(['0', '1', '2', '…', 'k', '…', '1023']):
    y = 42 + k * BP
    b += [rect(BX, y, BW, BH, sw=1.1, rx=3), t(BX + 10, y + BH / 2, lab, anchor='start', fam=UMONO),
          t(BX + BW - 8, y + BH / 2, 'head · lock', size=14.5, anchor='end', fill=GREY)]
YK = 42 + 4 * BP + BH / 2
b += [t(580, YK - 30, 'bucket k: a list of elements', size=14.5, fill=GREY),
      line([(BX + BW + 2, YK), (470, YK)], m + '-k', width=1.5),
      rect(472, YK - 14, 86, 28), t(515, YK, 'element'),
      line([(558, YK), (586, YK)], m + '-k', width=1.5),
      rect(588, YK - 14, 84, 28), t(630, YK, 'element')]
# the ops table
b += [rect(290, 252, 382, 82), t(481, 270, 'htab_map_ops', size=16, fam=UMONO, weight='700'),
      t(304, 294, '.map_lookup_elem', anchor='start', fam=UMONO), t(486, 294, '.map_update_elem', anchor='start', fam=UMONO),
      t(304, 318, '.map_get_next_key', anchor='start', fam=UMONO),
      tm(486, 318, [('.map_gen_lookup', 'm'), ('  … 16 more', 's')], anchor='start')]
# the element pool, and one element byte by byte
b.append(tm(8, 362, [('preallocated: 1024 + 16 elements × 64 B, one drawn byte by byte', 's')], size=16, anchor='start', weight='700'))
EX, SC, EY, EH = 8, 664 / 64, 376, 36
x = EX
for n, lab in [(16, 'list'), (24, 'lru / pptr'), (4, 'hash'), (4, ''), (8, 'key'), (8, 'value')]:
    w = n * SC
    if lab == 'value':
        b += [rect(x, EY, w, EH, stroke=P2, sw=2.6, rx=2, fill=ACC_FILL),
              t(x + w / 2, EY + EH / 2, lab, fam=UMONO, weight='700', fill=P2)]
    else:
        b.append(rect(x, EY, w, EH, sw=1.1, rx=2, fill=GREY_FILL if not lab else '#FFFFFF'))
        if lab:
            b.append(t(x + w / 2, EY + EH / 2, lab, fam=UMONO))
    b.append(t(x + w / 2, EY + EH + 14, str(n), size=14.5, fill=GREY))
    x += w
# the measured offset: from the start of the element to the start of the value
VX = EX + 56 * SC
DY = EY + EH + 38
b += [line([(EX, EY + EH + 2), (EX, DY + 8)], color=GREY, width=1.1),
      line([(VX, EY + EH + 2), (VX, DY + 8)], color=P2, width=2),
      line([(EX + 2, DY), (EX + 196, DY)], color=P2, width=2) .replace('/>', f' marker-start="url(#{m}-a)"/>'),
      t((EX + VX) / 2, DY, 'value = element + 56', size=15, fam=UMONO, weight='700', fill=P2),
      line([(VX - 196, DY), (VX - 2, DY)], m + '-a', color=P2, width=2)]
b.append(t(340, DY + 36, '896 + 1024 × 16 + 1040 × 64 + 16 × 8 = 83,968 bytes, set aside before the first write', size=14.5))
H92 = DY + 52
fig92 = svg(H92, 'The hash map the loader created, in kernel memory',
            'The struct bpf_htab object, 896 bytes, holding struct bpf_map (type hash, key 4 B, value 8 B, max_entries 1024, id 7 and two counts, '
            'and an ops pointer to htab_map_ops with .map_lookup_elem, .map_update_elem, .map_get_next_key, .map_gen_lookup and 16 more), '
            'a random seed hashrnd and the buckets, elems and freelist pointers; 1024 buckets of 16 bytes, each a list head and a lock, '
            'bucket k holding a list of two elements; 1024 + 16 preallocated elements of 64 bytes, one drawn byte by byte: list 16, '
            'lru / pptr 24, hash 4 and 4 of rounding, key 8, value 8, so the value is at element + 56. '
            '896 + 1024 × 16 + 1040 × 64 + 16 × 8 = 83,968 bytes, set aside before the first write.', b, m)
save('ch09-object', fig92)
print('ch09 figures ok')
