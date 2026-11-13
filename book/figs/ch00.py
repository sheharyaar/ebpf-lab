import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *

# ---------------- Figure 0.1: three ways to put code in the kernel ----------------
m = 'ah-0-1'
cols = [(20, 'Kernel module', 'new code becomes kernel code', 'gray'),
        (240, 'Copy everything out', 'the kernel hands packets out', 'gray'),
        (460, 'Filter machine', 'the kernel runs a small program', 'teal')]
rows = [
    ('Runs as', [('native kernel code', 'loaded into the kernel'), ('a user-space program', 'outside the kernel'),
                 ('filter instructions', 'interpreted, once per packet')]),
    ('Can read', [('all kernel memory', 'and write it'), ('only its copies', 'nothing inside the kernel'),
                  ('one packet', 'plus 16 words of scratch')]),
    ('A bug means', [('the kernel crashes', 'the machine goes down'), ('the program crashes', 'the kernel is untouched'),
                     ('wrong packets kept', 'the kernel is untouched')]),
    ('A rejected packet costs', [('almost nothing', 'it runs at full speed'), ('a full copy', 'made, then thrown away'),
                                 ('a few instructions', 'no copy at all')]),
    ('On the next kernel', [('rebuild the module', 'it is tied to one version'), ('runs unchanged', ''),
                            ('runs unchanged', '')]),
]
b = []
for x, t1, t2, col in cols:
    b.append(text(x + 100, 18, t1, size=14, col=col, weight='600'))
    b.append(text(x + 100, 36, t2, size=11, col=col, italic=True))
y = 56
for label, cells in rows:
    watch = label == 'A bug means'
    b.append(text(20, y + 7, label, size=10.5, col='amber' if watch else 'gray', anchor='start', weight='600'))
    for (x, _, _, col), (c1, c2) in zip(cols, cells):
        b.append(box(x, y + 16, 200, 42, 'amber' if watch else col, c1, c2 or None, size1=12.5))
    y += 70
b.append(f'<rect x="20" y="{y + 2}" width="640" height="30" rx="6" fill="{C["gray"][0]}" stroke="{C["gray"][1]}" stroke-width="0.75"/>')
b.append(text(340, y + 17, 'eBPF keeps the third column and widens what the program may do: chapters 1 to 13.', size=12, col='gray'))
save('ch00-three', svg(y + 42, 'Three ways to put code in the kernel',
                       'Three columns comparing a kernel module, copying every packet to user space, and a filter machine, '
                       'row by row: how the code runs, what it can read, what a bug means, what a rejected packet costs, '
                       'and what happens on the next kernel', b, m))


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
def rect(x, y, w, h, stroke=INK, sw=1.3, rx=5, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="#FFFFFF" stroke="{stroke}" stroke-width="{sw}"{da}/>'

# ---------- Figure 0.2 for print: the BSD network tap, redrawn from the paper's Figure 1 ----------
# The packet's path through BPF is the accent, drawn thick; the rest of the path is thin and black.
m = 'ah-0-2p'
b = [markers(m).replace('</defs>', f'<marker id="{m}-t" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4.2" markerHeight="4.2" '
                                    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{P2}"/></marker></defs>')]
TH = 3.2                                # the thick accent line
COLS = [100, 270, 440]                  # the three listeners
BW = 150
b.append(t(12, 14, 'user space', size=14.5, anchor='start', italic=True, fill=GREY))
for cx, name in zip(COLS, ['network monitor', 'network monitor', 'rarpd']):
    b += [rect(cx - BW / 2, 26, BW, 36), t(cx, 44, name, size=16, weight='700')]
b.append(f'<line x1="8" y1="80" x2="672" y2="80" stroke="{GREY}" stroke-width="1" stroke-dasharray="6 4"/>')
b.append(t(12, 94, 'kernel', size=14.5, anchor='start', italic=True, fill=GREY))
for cx in COLS:
    b += [rect(cx - BW / 2, 104, BW, 34), t(cx, 121, 'buffer', size=16, weight='700'),
          rect(cx - BW / 2, 172, BW, 34, sw=1.6), t(cx, 189, 'filter', size=16, weight='700'),
          line([(cx, 104), (cx, 64)], m + '-k', width=1.5),                      # read() up to the program
          line([(cx, 172), (cx, 141)], m + '-t', color=P2, width=TH),           # accepted bytes into the buffer
          line([(cx, 238), (cx, 209)], m + '-t', color=P2, width=TH)]           # BPF runs each filter on the packet
b.append(t(COLS[2] + 14, 155, 'only accepted bytes are copied up', size=14.5, anchor='start', fill=GREY, italic=True))
b += [rect(25, 238, 490, 48, sw=1.6), t(270, 253, 'BPF: the tap', size=16, weight='700'),
      t(270, 273, 'runs every listener’s filter on the packet where it lies', size=14.5, fill=GREY)]
b += [rect(545, 172, 125, 114), t(607, 220, 'protocol', size=16, weight='700'), t(607, 240, 'stack', size=16, weight='700')]
DRV = [100, 300, 480]
for cx in DRV:
    b += [rect(cx - 70, 322, 140, 34), t(cx, 339, 'link-level driver', size=16, weight='700'),
          line([(cx, 384), (cx, 359)], m + '-k', width=1.5),                     # from the network
          line([(cx, 322), (cx, 289)], m + '-t', color=P2, width=TH)]           # each driver calls BPF first
b.append(line([(530, 322), (586, 289)], m + '-k', width=1.5))                    # then the normal path to the stack
b.append(f'<line x1="8" y1="386" x2="672" y2="386" stroke="{INK}" stroke-width="2.2"/>')
b.append(t(12, 402, 'network', size=14.5, anchor='start', italic=True, fill=GREY))
# legend
b += [line([(330, 404), (372, 404)], color=P2, width=TH), t(380, 404, 'a packet, through BPF', size=14.5, anchor='start'),
      line([(516, 404), (558, 404)], width=1.5), t(566, 404, 'the rest of the path', size=14.5, anchor='start')]
save('ch00-tap', svg(418, 'The BSD network tap',
                     'Redrawn from Figure 1 of the 1993 BSD Packet Filter paper: three link-level drivers take packets from the network '
                     'and call BPF, the tap, which runs every listener’s filter on the packet where it lies; only accepted bytes are '
                     'copied up into each listener’s buffer, read by two network monitors and rarpd in user space. One driver also '
                     'passes the packet on to the protocol stack.', b, m))

# ---------- Figure 0.3 for print: the lineage, a timeline with one row per change ----------
# Filled dot: the write counter depends on it; hollow dot: context; the 2014 rebuild in bold, in the accent.
m = 'ah-0-3p'
eras = [
    ('Classic BPF: a filter for packets, then for system calls', [
        ('1993', '—', 'The BSD Packet Filter paper (McCanne and Jacobson)', '0', 'g'),
        ('1997', '2.1.75', 'Linux Socket Filter: classic BPF on one socket', '0', 'g'),
        ('2011', '3.0', 'classic filters translated into x86-64 machine code', '7', 'g'),
        ('2012', '3.5', 'seccomp: classic BPF filters system calls', '0', 'g')]),
    ('The new machine: registers, calls, maps, hooks', [
        ('2014', '3.15', 'eBPF: the machine rebuilt inside the kernel', '1', 'a'),
        ('2014', '3.16', 'eBPF programs translated into x86-64 code', '7', 'g'),
        ('2014', '3.18', 'the bpf() system call and maps', '2, 9', 't'),
        ('2015', '4.1', 'kprobes: a program on (almost) any kernel function', '8', 'g'),
        ('2015', '4.2', 'tail calls: one program jumps to another', '7, 16', 'g'),
        ('2016', '4.4', 'bpffs: programs and maps pinned as files', '2', 'g'),
        ('2016', '4.7', 'tracepoints: fixed, named hooks', '8', 't'),
        ('2016', '4.8', 'XDP: a program in the network driver', '8', 'g')]),
    ('Types and links: one binary for many kernels', [
        ('2018', '4.16', 'bpf-to-bpf function calls', '7', 'g'),
        ('2018', '4.18', 'BTF: the kernel describes its own types', '3, 10', 't'),
        ('2019', '5.2', 'the one-million-instruction limit', '4', 'g'),
        ('2019', '5.3', 'bounded loops', '4', 'g'),
        ('2020', 'libbpf', 'CO-RE: compile once, run everywhere', '3', 't'),
        ('2020', '5.5', 'trampolines: programs on function entry and exit', '7, 8, 14', 'g'),
        ('2020', '5.7', 'LSM programs; bpf_link', '2, 8', 'g'),
        ('2020', '5.8', 'the ring buffer', '9, 15', 'g')]),
    ('Extending the kernel itself', [
        ('2021', '5.13', 'kfuncs: programs call ordinary kernel functions', '8, 13', 'g'),
        ('2024', '6.9', 'arena; BPF token', '9, 15, 21', 'g'),
        ('2024', '6.12', 'sched_ext: a CPU scheduler written in BPF', '8', 'g'),
        ('2024', 'RFC', 'RFC 9669: the instruction set becomes a standard', '1', 'g'),
        ('2025', '6.18', 'signed BPF programs', '21', 'g')]),
]
# The chapter column is not typed above: it comes from src/commits.json through numbering.py, matched by version
# (5.7 and 6.9 each join two entries), so it follows the book's order. A row with no entry keeps what is typed.
import json
BOOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BOOK)
import numbering
_NUM = numbering.get()
_BY_VERSION = {}
for _e in json.load(open(os.path.join(BOOK, 'src', 'commits.json'), encoding='utf-8')):
    _BY_VERSION.setdefault(_e['version'], []).extend(_e['chapters'])
def _chapters(version, typed):
    if version not in _BY_VERSION: return typed
    nums = []
    for _, n in _NUM.commit_chapters(_BY_VERSION[version]):
        if n not in nums: nums.append(n)
    return ', '.join(sorted(nums, key=lambda n: (1, 0) if not n.isdigit() else (0, int(n))))
eras = [(title, [(y, v, w, _chapters(v, c), k) for y, v, w, c, k in rows]) for title, rows in eras]
YX, DX, VX, CX_, RX = 58, 76, 94, 156, 672     # year (right edge), dot, version, change, chapter (right edge)
PITCH = 21
def dot(y, kind):
    if kind == 'a':
        return f'<circle cx="{DX}" cy="{y}" r="6" fill="{P2}" stroke="{P2}" stroke-width="1.2"/>'
    if kind == 't':
        return f'<circle cx="{DX}" cy="{y}" r="4.6" fill="{INK}" stroke="{INK}" stroke-width="1.2"/>'
    return f'<circle cx="{DX}" cy="{y}" r="4.6" fill="#FFFFFF" stroke="{GREY}" stroke-width="1.4"/>'
b = [t(YX, 12, 'year', size=14.5, anchor='end', italic=True, fill=GREY),
     t(VX, 12, 'kernel', size=14.5, anchor='start', italic=True, fill=GREY),
     t(CX_, 12, 'change', size=14.5, anchor='start', italic=True, fill=GREY),
     t(RX, 12, 'chapter', size=14.5, anchor='end', italic=True, fill=GREY),
     f'<line x1="8" y1="25" x2="{RX}" y2="25" stroke="{INK}" stroke-width="1.3"/>']
spine = len(b)
y, first = 32, None
for era, events in eras:
    b.append(f'<rect x="8" y="{y}" width="{RX - 8}" height="24" fill="#EEF0F1"/>')
    b.append(t(14, y + 12, era, size=15, anchor='start', weight='600', italic=True))
    y += 24 + PITCH / 2 + 3
    for year, ver, what, ch, kind in events:
        first = first or y
        acc = kind == 'a'
        fill, wt = (P2, '700') if acc else (INK, None)
        b += [t(YX, y, year, size=15, anchor='end', fam=UMONO, fill=fill, weight=wt), dot(y, kind),
              t(VX, y, ver, size=15, anchor='start', fam=UMONO, fill=fill, weight=wt),
              t(CX_, y, what, size=15, anchor='start', fill=fill, weight=wt),
              t(RX, y, ch, size=15, anchor='end', fam=UMONO, fill=fill, weight=wt)]
        if acc:
            b.append(t(CX_ + 262, y, 'the turn this book starts from', size=14.5, anchor='start', italic=True, fill=P2))
        last = y
        y += PITCH
        b.append(f'<line x1="{CX_}" y1="{y - PITCH / 2}" x2="{RX}" y2="{y - PITCH / 2}" stroke="#D3D6D9" stroke-width="0.7"/>')
    y += 4 - PITCH / 2 + 3
b.insert(spine, f'<line x1="{DX}" y1="{first}" x2="{DX}" y2="{last}" stroke="{GREY}" stroke-width="1.2"/>')
y += 14
b += [dot(y, 't').replace(f'cx="{DX}"', 'cx="20"'), t(32, y, 'the write counter depends on it', size=14.5, anchor='start'),
      dot(y, 'g').replace(f'cx="{DX}"', 'cx="250"'), t(262, y, 'context', size=14.5, anchor='start')]
save('ch00-lineage', svg(y + 14, 'Thirty-two years of BPF, one row per change',
                         'A timeline of 25 changes from the 1993 BSD Packet Filter paper to signed BPF programs in Linux 6.18, '
                         'grouped in four eras, each with its year, kernel version and the chapter that covers it; the 2014 rebuild, '
                         'eBPF in Linux 3.15, is the turn this book starts from', b, m))
print('ok')
