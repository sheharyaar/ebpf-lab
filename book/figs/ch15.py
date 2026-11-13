import sys, os, math, re
sys.path.insert(0, os.path.dirname(__file__))
from common import svg, save, esc, MONO

# Print rules for the O'Reilly edition (NOTES.md "Figure rules"): set at the 127 mm text width, so on the
# 680-unit canvas every label is 14.5 units or more (7.5 pt), in Open Sans Condensed for words and Ubuntu Mono
# for code names, and the drawing is black and grey with the book's one accent, told apart in greyscale by
# fill darkness, outline and marker shape. (The screen version, at 13.5 units in the serif, is in figs/pre-print/ch15.py.)
SANS = "'Open Sans Condensed', 'Open Sans', 'Myriad Pro', sans-serif"
UMONO = "'Ubuntu Mono', 'JetBrains Mono', monospace"
INK, GREY_D, GREY_M, GREY_L, WHITE = '#1F2328', '#4A5056', '#9EA3A8', '#E4E6E8', '#FFFFFF'
ACC, ACC_D = '#0F6E56', '#0F6E56'          # the one accent, as in every figure of the book
FS = 14.5                                  # smallest label

figs = {}

CODE = re.compile(r'(max_entries|‑E2BIG|\bHASH\b|memlock)')   # code names inside a line of words
def t(x, y, s, size=FS, fill=INK, anchor='middle', mono=False, weight=None, italic=False):
    f = f' font-family="{UMONO}"' if mono else f' font-family="{SANS}"'
    w = f' font-weight="{weight}"' if weight else ''
    it = ' font-style="italic"' if italic else ''
    body = esc(s)
    if not mono and CODE.search(s):
        body = ''.join(f'<tspan font-family="{UMONO}">{esc(p)}</tspan>' if i % 2 else esc(p) for i, p in enumerate(CODE.split(s)))
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-size="{size}" '
            f'fill="{fill}"{f}{w}{it} xml:space="preserve">{body}</text>')

def r(x, y, w, h, fill, stroke=GREY_D, sw=0.9, rx=4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'

def line(x1, y1, x2, y2, stroke=GREY_D, sw=1, dash=None, mid=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    m = f' marker-end="url(#{mid})"' if mid else ''
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}{m}/>'

def summary(y, s):
    return r(20, y, 640, 28, GREY_L, GREY_D, 0.75, 6) + t(340, y + 14, s)

# ---------------- Figure 15.1: what each layout weighs at the counter's size ----------------
# Numbers: /tmp/book-labs/ch15/mem.txt (labs/ch15-root.sh step 1), kernel 7.2.15, 16 possible CPUs.
m = 'ah-15-1'
b = []
X0, S = 272, 1.45            # bar origin, units per byte
rows = [('ARRAY', 8.3, None, 'made'),
        ('ARRAY, MMAPABLE', 12.0, None, 'made'),
        ('LRU_HASH', 80.9, None, 'made'),
        ('HASH (the counter)', 82.0, None, 'made'),
        ('HASH, NO_PREALLOC', 16.9, 88.9, 'grows'),
        ('PERCPU_ARRAY', 136.3, None, 'cpu'),
        ('PERCPU_HASH', 208.9, None, 'cpu')]
b.append(t(8, 14, 'bytes per entry: memlock ÷ 1,024 entries, 16 possible CPUs', size=15, weight='700', anchor='start'))
top, step, bh = 40, 30, 18
for v in range(0, 201, 50):
    x = X0 + v * S
    b.append(line(x, top - 8, x, top + len(rows) * step - 6, GREY_M, 0.6, '2 3'))
    b.append(t(x, top + len(rows) * step + 6, f'{v}', mono=True, fill=GREY_D))
for k, (lab, v, v2, kind) in enumerate(rows):
    y = top + k * step
    b.append(t(X0 - 10, y + bh / 2, lab, mono=True, anchor='end'))
    fill = {'made': GREY_L, 'grows': GREY_L, 'cpu': ACC}[kind]
    b.append(r(X0, y, max(3, v * S), bh, fill, INK if kind == 'cpu' else GREY_D, 0.9, 2))
    if v2:
        b.append(r(X0 + v * S, y, (v2 - v) * S, bh, WHITE, INK, 1.1, 2, '4 3'))
        b.append(t(X0 + v2 * S + 8, y + bh / 2, f'{v:.1f} → {v2:.1f}', mono=True, weight='600', anchor='start'))
    else:
        b.append(t(X0 + v * S + 8, y + bh / 2, f'{v:.1f}', mono=True, weight='600',
                   fill=ACC_D if kind == 'cpu' else INK, anchor='start'))
# legend
ly = top + len(rows) * step + 30
for x, kind, lab in ((20, 'made', 'made at creation'), (230, 'grows', 'grows as keys arrive'), (470, 'cpu', 'a value per CPU')):
    if kind == 'grows':
        b.append(r(x, ly - 8, 26, 16, WHITE, INK, 1.1, 2, '4 3'))
    else:
        b.append(r(x, ly - 8, 26, 16, GREY_L if kind == 'made' else ACC, INK if kind == 'cpu' else GREY_D, 0.9, 2))
    b.append(t(x + 34, ly, lab, anchor='start'))
# maps that hold no entries
y0 = ly + 34
b.append(t(8, y0, 'maps without entries', size=15, weight='700', anchor='start'))
other = [('RINGBUF, 256 KiB', 'memlock 275,776 B; one buffer for all CPUs'),
         ('PERF_EVENT_ARRAY', 'memlock 432 B; 266,240 B a CPU not counted there'),
         ('ARENA, 1,024 pages', 'memlock 0 B; 256 pages touched charged 1.1–1.3 MB')]
for k, (t1, t2) in enumerate(other):
    y = y0 + 24 + k * 22
    b.append(t(X0 - 10, y, t1, mono=True, anchor='end'))
    b.append(t(X0, y, t2, anchor='start'))
yb = y0 + 24 + 3 * 22 + 2
b.append(summary(yb, 'A layout pays for its entries when created, unless it allocates as keys arrive.'))
figs['mem'] = svg(yb + 34, 'Bytes per entry for seven map layouts at 1,024 entries, and three maps that hold no entries',
                  'Horizontal bars of bytes per entry: array 8.3, mmapable array 12, LRU hash 80.9, hash 82, hash without preallocation 16.9 empty to 88.9 full, per-CPU array 136, per-CPU hash 209; below, the ring buffer, perf event array and arena with their reported memory', b, m)

# ---------------- Figure 15.2: ns per run, one writer and eight, own keys and one shared key ----------------
# Medians of rounds 1-4 from /tmp/book-labs/ch15/upd.txt (labs/ch15-root.sh step 2), kernel 7.2.15.
# (way of counting, map type, one writer, eight writers own keys, eight writers one key, share lost on one key)
UPD = [('lookup, copy, update', 'HASH, the counter', 139.0, 1284.1, 3987.3, '66 %'),
       ('the same, made as needed', 'HASH, NO_PREALLOC', 181.7, 1659.9, 5819.6, '70 %'),
       ('lookup, plain add', 'HASH', 78.0, 535.0, 657.2, '0.5 %'),
       ('lookup, atomic add', 'HASH', 79.0, 533.2, 713.9, '0'),
       ('lookup, atomic add', 'LRU_HASH', 77.7, 566.1, 666.7, '0'),
       ('lookup, plain add', 'PERCPU_HASH', 77.2, 559.5, 591.5, '0'),
       ('atomic add at an index', 'ARRAY', 49.5, 410.8, 443.6, '0'),
       ('plain add at an index', 'PERCPU_ARRAY', 53.8, 323.8, 406.1, '0'),
       ('the key only', 'no map: the floor', 47.5, 310.9, 354.7, '')]
m = 'ah-15-2'
b = []
X0, X1 = 278, 590
lo, hi = math.log10(30), math.log10(8000)
def X(v): return X0 + (math.log10(v) - lo) / (hi - lo) * (X1 - X0)
top, step = 46, 40
b.append(t(X0 - 12, 14, 'way of counting', weight='600', anchor='end'))
b.append(t((X0 + X1) / 2, 14, 'ns per run, log scale', weight='600'))
b.append(t(640, 14, 'lost', weight='600'))
for v, lab in ((50, '50'), (100, '100'), (200, '200'), (500, '500'), (1000, '1k'), (2000, '2k'), (5000, '5k')):
    x = X(v)
    b.append(line(x, top - 16, x, top + len(UPD) * step - 18, GREY_M, 0.6, '2 3'))
    b.append(t(x, top + len(UPD) * step - 4, lab, mono=True, fill=GREY_D))

def circle(x, y): return f'<circle cx="{x}" cy="{y}" r="6" fill="{WHITE}" stroke="{INK}" stroke-width="1.5"/>'
def diamond(x, y): return (f'<rect x="{x - 5}" y="{y - 5}" width="10" height="10" fill="{GREY_M}" stroke="{INK}" '
                           f'stroke-width="1.2" transform="rotate(45 {x} {y})"/>')
def square(x, y): return f'<rect x="{x - 6}" y="{y - 6}" width="12" height="12" fill="{ACC}" stroke="{INK}" stroke-width="1.2"/>'

for k, (t1, t2, one, own, shared, lost) in enumerate(UPD):
    y = top + k * step
    b.append(t(X0 - 12, y - 8, t1, anchor='end'))
    b.append(t(X0 - 12, y + 9, t2, mono=True, fill=GREY_D, anchor='end'))
    xs = [X(one), X(own), X(shared)]
    b.append(line(min(xs), y, max(xs), y, GREY_D, 1))
    b += [circle(X(one), y), diamond(X(own), y), square(X(shared), y)]
    if lost:
        b.append(t(640, y, lost, mono=True, weight='600', fill=ACC_D if lost != '0' else GREY_D))
ly = top + len(UPD) * step + 22
for x, f, lab in ((30, circle, 'one writer'), (232, diamond, 'eight, own keys'), (452, square, 'eight, one key')):
    b.append(f(x, ly))
    b.append(t(x + 14, ly, lab, anchor='start'))
b.append(summary(ly + 20, 'On one key the counter’s update loses counts; an atomic or per-CPU add does not.'))
figs['update'] = svg(ly + 54, 'Nanoseconds per run for eight ways of counting, with one writer, eight writers on their own keys, and eight on one key',
                     'Dot plot on a logarithmic axis: for each way of counting, a white circle for one writer, a grey diamond for eight writers with their own keys and an accent square for eight writers sharing one key, with the share of counts lost on the shared key at the right', b, m)

# ---------------- Figure 15.5: choosing a map, four questions in order ----------------
m = 'ah-15-5'
b = []
QX, QW = 4, 232              # question column
YX, NX, CW = 246, 464, 212   # yes and no columns
H, G, Y0 = 66, 12, 30
b.append(t(QX + QW / 2, 12, 'ask in order', size=15, weight='700'))
b.append(t(YX + CW / 2, 12, 'yes', size=15, weight='700'))
b.append(t(NX + CW / 2, 12, 'no', size=15, weight='700'))
rows = [(('Must user space see every', 'event, in order, soon?'),
         ('RINGBUF', 'one buffer for all CPUs;', 'stop here'),
         ('a map with keys', 'go on to the next', 'question')),
        (('Are the keys small integers', 'known in advance?'),
         ('ARRAY', 'every entry exists; the', 'lookup is inlined'),
         ('HASH', 'made in advance, up to', 'max_entries')),
        (('Can the set of keys outgrow', 'max_entries: threads, flows?'),
         ('LRU_HASH', 'evicts the least recently', 'used entry to make room'),
         ('keep the type', 'a full HASH refuses a', 'new key with ‑E2BIG')),
        (('Do several CPUs write one', 'key at the same moment?'),
         ('PERCPU_ form', 'memory × CPUs, and the', 'reader adds the copies'),
         ('one value, added in place', '__sync_fetch_and_add()', 'through the lookup’s pointer'))]
counter = {(0, 'no'), (1, 'no'), (2, 'yes'), (3, 'no')}
for k, (q, yes, no) in enumerate(rows):
    y = Y0 + k * (H + G)
    b.append(r(QX, y, QW, H, GREY_L, GREY_D, 0.9, 5))
    b.append(t(QX + 10, y + H / 2 - 9, q[0], anchor='start'))
    b.append(t(QX + 10, y + H / 2 + 9, q[1], anchor='start'))
    for x, cell, tag in ((YX, yes, 'yes'), (NX, no, 'no')):
        hot = (k, tag) in counter
        b.append(r(x, y, CW, H, WHITE, ACC_D if hot else GREY_D, 2.4 if hot else 0.9, 5))
        mono = cell[0].replace('_', '').isupper() or cell[0].startswith('PERCPU')
        b.append(t(x + 10, y + 15, cell[0], weight='600', mono=mono, fill=ACC_D if hot else INK, anchor='start'))
        b.append(t(x + 10, y + 34, cell[1], anchor='start', mono=cell[1].startswith('__')))
        b.append(t(x + 10, y + 51, cell[2], anchor='start'))
    if k < len(rows) - 1:
        b.append(line(QX + QW / 2, y + H, QX + QW / 2, y + H + G - 1, GREY_D, 1.2, None, m))
yb = Y0 + len(rows) * (H + G) + 2
b.append(t(8, yb + 6, 'Thick accent outlines mark the write counter’s answers.', anchor='start', fill=ACC_D, weight='600'))
b.append(summary(yb + 22, 'Then check the contexts table: a sleepable program cannot use a perf buffer.'))
figs['choose'] = svg(yb + 56, 'Choosing a map in four questions asked in order',
                     'Four rows, each a question with a yes cell and a no cell: ring buffer or a map with keys; array or hash; LRU hash or keep the type; per-CPU form or one value added in place. The write counter’s cells have thick accent outlines', b, m)

for k in ('mem', 'update', 'choose'):
    save(f'ch15-{k}', figs[k])
print('ch15 figures ok')
