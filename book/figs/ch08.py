import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *

# ---------------- Figure 8.1: one write() past the hooks (step widget) ----------------
m = 'ah-8-1'
b = []
PY, PH = 84, 40            # the path row
path = [  # x, w, title, detail, mono
    (8, 104, 'write()', 'a process', True),
    (130, 112, 'syscall entry', 'into the kernel', False),
    (260, 112, 'vfs_write()', 'every write', True),
    (390, 162, 'security_file_', 'permission()', True),
    (570, 102, "the file's", 'write()', False),
]
for (x, w, t1, t2, mono) in path:
    if x == 390:
        b.append(box(x, PY, w, PH, 'gray'))
        b.append(text(x + w / 2, PY + 13, t1, size=11, mono=True, weight='600', col='gray'))
        b.append(text(x + w / 2, PY + 28, t2, size=11, mono=True, weight='600', col='gray'))
    else:
        b.append(box(x, PY, w, PH, 'gray', t1, t2, mono1=mono, size1=12))
for i in range(len(path) - 1):
    x1 = path[i][0] + path[i][1]
    b.append(arrow(x1 + 1, PY + PH / 2, path[i + 1][0] - 2, PY + PH / 2, m, width=2.2, color=C['teal'][1]))

def hook(cx, y, w, col, t1, t2, stp, up=True):
    x = cx - w / 2
    out = [box(x, y, w, 32, col, t1, t2, mono1=True, size1=11, step=stp)]
    y1, y2 = (y + 32, PY) if up else (PY + PH, y)
    out.append(f'<line x1="{cx}" y1="{y1}" x2="{cx}" y2="{y2}" stroke="{C[col][1]}" stroke-width="1.6" data-step="{stp}"/>')
    return out

HY = 30
b += hook(186, HY, 140, 'teal', 'sys_enter_write', 'tracepoint: the counter', '1+')
b += hook(316, HY, 112, 'amber', 'kprobe · fentry', 'function entry', '2+')
b += hook(471, HY, 150, 'coral', 'LSM program', 'may refuse the write', '3+')
LY = 142
b += hook(186, LY, 140, 'gray', 'sys_exit_write', 'tracepoint', '4', up=False)
b += hook(316, LY, 112, 'amber', 'fexit', 'sees the result', '4', up=False)
steps = [('1', '1 · write() enters the kernel; the tracepoint fires and the counter runs'),
         ('2', '2 · vfs_write() begins; a program at its entry runs before its body'),
         ('3', '3 · the permission check; an LSM program may answer with an error, and the write ends'),
         ('4', '4 · on the way back out, fexit sees what vfs_write() returned')]
for stp, t in steps:
    b.append(text(340, 12, t, size=12, col='teal' if stp == '1' else None, weight='600', step=stp))
figs = {}
figs['path'] = svg(184, 'One write() call passing the hooks on its way through the kernel',
                   'A write system call as a row of five kernel stages, with the hooks where a BPF program can run above and below them', b, m)

# ---------------- Figure 8.2: a fixed hook or any function ----------------
m = 'ah-8-2'
b = []
LX, LW = 8, 112
cols = [('tracepoint', 'teal'), ('kprobe', 'gray'), ('fentry · fexit', 'gray')]
CX0, CW, CG = 128, 176, 8
def cx(i): return CX0 + i * (CW + CG)
for i, (t, col) in enumerate(cols):
    b.append(text(cx(i) + CW / 2, 16, t, size=14, mono=True, weight='600', col=col))
rows = [
    ('who placed it', ['kernel developers,', 'in the source'], ['whoever attaches it,', 'by function name'], ['whoever attaches it,', 'by function name']),
    ('how many here', ['2,079 named events', '367 of them syscall entries'], ['almost any instruction;', '751 blacklisted'], ['59,017 function entries', 'that ftrace can patch']),
    ('how it is reached', ['a call compiled in,', 'idle until attached'], ['at the entry, a call from', "ftrace's slot; else int3"], ['a no-op rewritten into a', 'call to a trampoline']),
    ('what r1 points at', ['the event record:', 'named fields'], ['the saved CPU registers', '(struct pt_regs)'], ['the arguments, typed', 'by BTF; fexit adds the result']),
    ('after an upgrade', ['names and fields', 'rarely change'], ['renamed: fails to attach', 'inlined: misses those calls'], ['renamed: fails at load', 'inlined: misses those calls']),
]
RY0, RH, RG = 32, 42, 8
for r, (lab, *cells) in enumerate(rows):
    y = RY0 + r * (RH + RG)
    last = r == len(rows) - 1
    b.append(text(LX, y + RH / 2, lab, size=11, anchor='start', col='amber' if last else None, weight='600' if last else None))
    for i, (l1, l2) in enumerate(cells):
        col = 'amber' if last else ('teal' if i == 0 else 'gray')
        b.append(box(cx(i), y, CW, RH, col))
        b.append(text(cx(i) + CW / 2, y + 14, l1, size=11, col=col))
        b.append(text(cx(i) + CW / 2, y + 29, l2, size=11, col=col))
yb = RY0 + len(rows) * (RH + RG) + 2
b.append(bar(yb, 30, 'A tracepoint is kept on purpose; the other two attach wherever the code happens to be today.'))
figs['three'] = svg(yb + 40, 'Tracepoint, kprobe and fentry compared',
                    'Three columns comparing tracepoints, kprobes and fentry programs: who placed the hook, how many there are, how it is reached, what the program sees, and what an upgrade does', b, m)

# ---------------- Figure 8.4: what a new hook takes (cache_ext) ----------------
m = 'ah-8-4'
b = []
# left: the policy programs
b.append(box(8, 40, 170, 150, 'teal'))
b.append(text(93, 58, 'the policy', size=13, weight='600', col='teal'))
for k, t in enumerate(['policy_init', 'evict_folios', 'folio_added', 'folio_accessed', 'folio_removed']):
    b.append(text(93, 82 + k * 22, t, size=11, mono=True, col='teal'))
b.append(text(93, 204, 'five BPF programs', size=11, col='teal'))
# middle: the struct_ops table
b.append(box(250, 40, 180, 150, 'coral'))
b.append(text(340, 58, 'struct_ops table', size=13, weight='600', col='coral'))
b.append(text(340, 76, 'struct cachebpf_ops', size=11, mono=True, col='coral'))
for k in range(5):
    b.append(f'<rect x="275" y="{88 + k * 19}" width="130" height="15" rx="3" fill="#FFFFFF" stroke="{C["coral"][1]}" stroke-width="0.7"/>')
    b.append(text(340, 95.5 + k * 19, 'function pointer', size=10, col='coral'))
b.append(text(340, 204, 'filled in when the policy loads', size=11, col='coral'))
for k in range(5):
    b.append(arrow(178, 82 + k * 22, 272, 95.5 + k * 19, m, width=1.6, color=C['teal'][1]))
# right: the page cache calling the table
b.append(box(502, 40, 170, 150, 'gray'))
b.append(text(587, 58, 'the page cache', size=13, weight='600', col='gray'))
for k, t in enumerate(['set up a cgroup', 'needs room', 'a page comes in', 'a page is read', 'a page leaves']):
    b.append(text(587, 82 + k * 22, t, size=11, col='gray'))
b.append(text(587, 204, '210 lines of call sites', size=11, col='gray'))
for k in range(5):
    b.append(arrow(500, 82 + k * 22, 408, 95.5 + k * 19, m, width=1.2))
# below: kfuncs and the verifier
b.append(box(8, 232, 330, 52, 'coral', 'kfuncs: list_create, list_add, list_move, …', 'the eviction-list API the programs call · 750 lines'))
b.append(arrow(28, 190, 28, 230, m, width=1.6, color=C['teal'][1]))
b.append(box(352, 232, 320, 52, 'gray', 'the verifier and registration', 'which kfuncs, which callbacks · 80 + 580 lines'))
b.append(text(340, 22, 'A program set fills the table; the subsystem calls through it.', size=12, weight='600'))
b.append(bar(298, 30, 'About 2,000 lines on Linux 6.6.8. Only 290 touch the page cache and the verifier.'))
figs['newhook'] = svg(338, 'What cache_ext added to the kernel to make a new hook',
                      'The cache_ext design: five policy programs fill a struct_ops table that the page cache calls at five events; the programs call kfuncs; the verifier is taught both', b, m)

save('ch08-path', figs['path'])
for i, f in enumerate(frames(figs['path'], 'ah-8-1', (1, 2, 3, 4), crop={1: 130, 2: 130, 3: 130}), 1):
    save(f'ch08-path-twin{i}', f)
save('ch08-three', figs['three'])

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

# ---------- Figure 8.1 for print: the write() path drawn once, every hook where it fires (replaces the four frames) ----------
m = 'ah-8-1p'
b = [markers(m)]
PY, PH = 112, 56                       # the row of stages the call passes on its way in
stages = [  # x, w, first line, its face, second line, its face
    (8, 92, 'write()', 'm', 'a process', 's'),
    (126, 116, 'syscall entry', 's', 'into the kernel', 's'),
    (268, 110, 'vfs_write()', 'm', 'every write', 's'),
    (404, 140, 'security_file_', 'm', 'permission()', 'm'),
    (570, 102, "the file's", 's', 'write()', 'm'),
]
for x, w, l1, f1, l2, f2 in stages:
    b.append(rect(x, PY, w, PH))
    if f2 == 'm' and f1 == 'm':        # a name too long for one line, broken in two
        b += [t(x + w / 2, PY + PH / 2 - 9, l1, size=16, fam=UMONO, weight='700'),
              t(x + w / 2, PY + PH / 2 + 10, l2, size=16, fam=UMONO, weight='700')]
    else:
        b += [t(x + w / 2, PY + PH / 2 - 9, l1, size=16, fam=UMONO if f1 == 'm' else SANS, weight='700'),
              t(x + w / 2, PY + PH / 2 + 11, l2, size=15, fam=UMONO if f2 == 'm' else SANS, fill=GREY)]
for (x, w, *_), (x2, *_) in zip(stages, stages[1:]):
    b.append(line([(x + w, PY + PH / 2), (x2 - 2, PY + PH / 2)], m + '-k', width=2.2))
b.append(t(8, 92, 'on the way in', size=14.5, anchor='start', italic=True, fill=GREY))
# the way back out: from the file's write() under the row and back to the process
RY = 234
b.append(line([(621, PY + PH), (621, RY), (54, RY), (54, PY + PH + 2)], m + '-k', width=2.2))
b.append(t(66, RY + 16, 'on the way back out', size=14.5, anchor='start', italic=True, fill=GREY))

def hook(ax, ay, tx_, ty, w, name, what, up=True):
    """A hook: a two-line tag (name in mono, then what it does) joined by a line to the point where it fires."""
    y1 = ty + 46 if up else ty
    return [f'<line x1="{ax}" y1="{y1}" x2="{ax}" y2="{ay}" stroke="{GREY}" stroke-width="1.3"/>',
            f'<circle cx="{ax}" cy="{ay}" r="3.2" fill="{INK}"/>',
            rect(tx_ - w / 2, ty, w, 46, stroke=GREY, sw=1.1, rx=8),
            t(tx_, ty + 14, name, size=15, fam=UMONO, weight='700'),
            tm(tx_, ty + 33, what, size=14.5, fill=GREY) if isinstance(what, list) else t(tx_, ty + 33, what, size=14.5, fill=GREY)]
HY = 30
b += hook(184, PY, 176, HY, 140, 'sys_enter_write', 'tracepoint: the counter')
b += hook(323, PY, 323, HY, 132, 'kprobe · fentry', 'function entry')
b += hook(474, PY, 474, HY, 136, 'LSM program', 'may refuse the write')
LY = 262
b += hook(184, RY, 184, LY, 128, 'sys_exit_write', 'tracepoint', up=False)
b += hook(323, RY, 354, LY, 192, 'fexit', [('sees what ', 's'), ('vfs_write()', 'm'), (' returned', 's')], up=False)
# a refusal: the call goes no further than the permission check
b += [line([(474, PY + PH), (474, 206)], color=P2, width=2.2, dash='6 4'),
      f'<line x1="458" y1="207" x2="490" y2="207" stroke="{P2}" stroke-width="3"/>',
      t(452, 200, 'refused: the write ends here', size=14.5, anchor='end', fill=P2, weight='700')]
# legend
b += [line([(474, 280), (514, 280)], width=2.2), t(522, 280, 'the call', size=14.5, anchor='start'),
      line([(474, 302), (514, 302)], color=P2, width=2.2, dash='6 4'), t(522, 302, 'refused by the LSM program', size=14.5, anchor='start', fill=P2)]
figs['pathprint'] = svg(318, 'One write() call and every hook it passes',
                        'The write system call as a row of five stages, write(), syscall entry, vfs_write(), security_file_permission() and the '
                        "file's write(), returning under the row to the process. Above the row: the sys_enter_write tracepoint at syscall entry, "
                        'a kprobe or fentry program at the entry of vfs_write(), an LSM program at the permission check, which may '
                        'refuse the write and end it there. Below the return line: fexit as vfs_write() returns and the sys_exit_write tracepoint.', b, m)
save('ch08-path-print', figs['pathprint'])
# ---------- Figure 8.4 for print: what cache_ext added to make a new hook ----------
# One row per page-cache event: the page cache calls through a slot of the struct_ops table (thin, black),
# which a policy program fills when the policy loads (thick, in the accent).
m = 'ah-8-4p'
b = [markers(m).replace('</defs>', f'<marker id="{m}-t" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4.6" markerHeight="4.6" '
                                    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{P2}"/></marker></defs>')]
TH = 2.8
EV_R, TB0, TB1, PG0 = 196, 270, 420, 496       # events end at EV_R; table from TB0 to TB1; programs from PG0
RY = [70, 100, 130, 160, 190]                    # row centres
b += [t(110, 16, 'the page cache', size=16, weight='700'), t(110, 36, 'five events', size=14.5, fill=GREY),
      t((TB0 + TB1) / 2, 16, 'struct_ops table', size=16, weight='700'),
      t((TB0 + TB1) / 2, 36, 'struct cachebpf_ops', size=14.5, fam=UMONO, fill=GREY),
      t(578, 16, 'the policy', size=16, weight='700'), t(578, 36, 'five BPF programs', size=14.5, fill=GREY)]
b.append(f'<rect x="{TB0 - 6}" y="{RY[0] - 19}" width="{TB1 - TB0 + 12}" height="{RY[-1] - RY[0] + 38}" rx="6" fill="#FFFFFF" stroke="{P2}" stroke-width="2.2"/>')
events = ['set up a cgroup', 'needs room', 'a page comes in', 'a page is read', 'a page leaves']
progs = ['policy_init', 'evict_folios', 'folio_added', 'folio_accessed', 'folio_removed']
for yc, ev, pg in zip(RY, events, progs):
    b += [t(EV_R, yc, ev, size=15, anchor='end'),
          line([(EV_R + 8, yc), (TB0 - 2, yc)], m + '-k', width=1.5),
          rect(TB0, yc - 12, TB1 - TB0, 24, stroke=GREY, sw=1, rx=3), t((TB0 + TB1) / 2, yc, 'function pointer', size=14.5),
          line([(PG0 - 8, yc), (TB1 + 2, yc)], m + '-t', color=P2, width=TH),
          t(PG0, yc, pg, size=15, anchor='start', fam=UMONO)]
b += [t(110, 228, '210 lines of call sites', size=14.5, fill=GREY),
      t((TB0 + TB1) / 2, 228, 'filled in when the policy loads', size=14.5, fill=P2)]
# the programs call kfuncs; the verifier is taught both
b += [line([(578, 202), (578, 256)], m + '-k', width=1.5), t(588, 230, 'the programs call', size=14.5, anchor='start', italic=True, fill=GREY)]
b += [rect(346, 258, 330, 54), tm(511, 276, [('kfuncs: ', 's'), ('list_create, list_add, list_move, …', 'm')], size=15).replace('<text ', '<text font-weight="700" '),
      t(511, 297, 'the eviction-list API the programs call · 750 lines', size=14.5, fill=GREY)]
b += [rect(8, 258, 324, 54), t(170, 276, 'the verifier and registration', size=16, weight='700'),
      t(170, 297, 'which kfuncs, which callbacks · 80 + 580 lines', size=14.5, fill=GREY)]
# legend
b += [line([(8, 336), (50, 336)], width=1.5), t(58, 336, 'the page cache calls through the table', size=14.5, anchor='start'),
      line([(300, 336), (342, 336)], color=P2, width=TH), t(350, 336, 'a program fills a slot when the policy loads', size=14.5, anchor='start')]
figs['newhook_print'] = svg(352, 'What cache_ext added to the kernel to make a new hook',
                            'Five rows. The page cache calls through a function pointer in the struct_ops table, struct cachebpf_ops, when it '
                            'sets up a cgroup, needs room, a page comes in, a page is read and a page leaves; the pointers are filled when the '
                            'policy loads by its five BPF programs, policy_init, evict_folios, folio_added, folio_accessed and folio_removed. '
                            'The call sites are 210 lines. The programs call kfuncs, list_create, list_add, list_move and more, the '
                            'eviction-list API, 750 lines; the verifier and registration, which kfuncs and which callbacks, take 80 + 580 lines.', b, m)
save('ch08-newhook', figs['newhook_print'])
print('ch08 figures ok')
