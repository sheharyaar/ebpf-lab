import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *

figs = {}

def tx(x, y, t, size=11, col=None, anchor='middle', mono=False, weight=None):
    return text(x, y, t, size=size, col=col, anchor=anchor, mono=mono, weight=weight)

# Figure 12.2 (the verifier map) is drawn for print further down; the screen version is in figs/pre-print/ch12.py.

# ---------- three instructions, three checkers ----------
m = 'ah-10-3'
b = []
b.append(tx(115, 12, 'instruction', size=11, col='gray'))
b.append(tx(290, 12, 'checked by', size=11, col='gray'))
b.append(tx(515, 12, 'what the kernel records about r0', size=11, col='gray'))
rows = [
    (26, 'call 0x1', 'check_helper_call()', ['r1 to r5 reset · line 10414', 'r0 = map value, maybe NULL · line 10455']),
    (96, 'if r0 == 0 goto +2', 'check_cond_jmp_op()', ['jump taken: r0 is the number 0', 'fall-through: r0 = map value · line 16167']),
]
for (y, ins, chk, eff) in rows:
    b.append(box(40, y, 150, 54, 'gray', ins, mono1=True, size1=12))
    b.append(box(205, y, 170, 54, 'teal', chk, mono1=True, size1=11))
    b.append(box(390, y, 250, 54, 'gray'))
    b.append(tx(515, y + 18, eff[0], size=11))
    b.append(tx(515, y + 36, eff[1], size=11))
    b.append(arrow(192, y + 27, 203, y + 27, m, width=1.0))
    b.append(arrow(377, y + 27, 388, y + 27, m, width=1.0))
y = 166
b.append(box(40, y, 150, 84, 'gray', 'r1 = *(u64 *)(r0 + 0)', mono1=True, size1=11))
b.append(box(205, y, 170, 84, 'teal'))
b.append(tx(290, y + 22, 'check_mem_access()', size=11, col='teal', mono=True, weight='600'))
b.append(tx(290, y + 44, 'line 6106: is r0', size=11, col='teal'))
b.append(tx(290, y + 60, 'a plain map value?', size=11, col='teal'))
b.append(box(390, y, 250, 38, 'teal', 'with the test: yes · bounds checked', size1=11))
b.append(box(390, y + 46, 250, 38, 'coral', 'without it: no · line 6322 · rejected', size1=11, sw=1.4))
b.append(arrow(192, y + 42, 203, y + 42, m, width=1.0))
b.append(arrow(377, y + 30, 388, y + 19, m, width=1.0))
b.append(arrow(377, y + 54, 388, y + 65, m, width=1.6, color=C['coral'][1]))
b.append(bar(266, 32, 'The test of r0 turns "map value, maybe NULL" into "map value".'))
figs['three'] = svg(308, 'Three of the counter\'s instructions and the checkers that see them',
                    'The call, the test of r0 and the load, each with the verifier function that checks it and what it records about r0', b, m)


save('ch12-three', figs['three'])
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

# ---------- Figure 12.4 for print: the road from a change to mainline (replaces the Mermaid sequence) ----------
m = 'ah-12-4p'
b = [markers(m).replace('</defs>', f'<marker id="{m}-g" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                                    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{GREY}"/></marker></defs>')]
cx, NX, NW = 200, 60, 280
def node(y, h, lines):
    """A step: lines are (parts, size, fill, weight), parts a list of (text, face)."""
    out = [rect(NX, y, NW, h)]
    n = len(lines)
    for i, (parts, size, fill, weight) in enumerate(lines):
        yy = y + h / 2 + (i - (n - 1) / 2) * 20
        if weight:
            out.append(t(cx, yy, parts[0][0], size=size, fam=UMONO if parts[0][1] == 'm' else SANS, weight=weight, fill=fill))
        else:
            out.append(tm(cx, yy, parts, size=size, fill=fill))
    return out
b += node(10, 54, [([('the author', 's')], 16, INK, '700'), ([('a feature or cleanup, for bpf-next', 's')], 15, GREY, None)])
# the optional CI run, before anyone reads the patch
CX0, CW0 = 430, 242
b.append(rect(CX0, 6, CW0, 86, stroke=GREY, sw=1.3, dash='6 4'))
b += [t(CX0 + CW0 / 2, 24, 'BPF CI on GitHub', size=16, weight='700'),
      tm(CX0 + CW0 / 2, 44, [('pull request against ', 's'), ('bpf-next_base', 'm')], size=15, fill=GREY),
      t(CX0 + CW0 / 2, 64, 'selftests pass or fail', size=15, fill=GREY)]
b += [line([(NX + NW, 28), (CX0 - 2, 28)], m + '-g', color=GREY, width=1.6, dash='6 4'),
      line([(CX0, 50), (NX + NW + 2, 50)], m + '-g', color=GREY, width=1.6, dash='6 4'),
      t((NX + NW + CX0) / 2, 76, 'optional', size=14.5, italic=True, fill=GREY)]
b.append(line([(cx, 64), (cx, 92)], m + '-k', width=2.2))
b += node(94, 66, [([('git send-email', 'm')], 16, INK, '700'), ([('to the bpf mailing list,', 's')], 15, GREY, None),
                   ([('subject ', 's'), ('PATCH bpf-next', 'm')], 15, GREY, None)])
b.append(line([(cx, 160), (cx, 186)], m + '-k', width=2.2))
b += node(188, 52, [([('patchwork', 's')], 16, INK, '700'), ([('queued for review', 's')], 15, GREY, None)])
b.append(line([(cx, 240), (cx, 264)], m + '-k', width=2.2))
DY, DH, DW = 316, 50, 132
b.append(f'<polygon points="{cx - DW},{DY} {cx},{DY - DH} {cx + DW},{DY} {cx},{DY + DH}" fill="#FFFFFF" stroke="{INK}" stroke-width="1.3"/>')
b += [t(cx, DY - 10, 'BPF maintainers', size=16, weight='700'), t(cx, DY + 10, 'review: changes requested?', size=15)]
# the review loop, drawn once: back to the list
b.append(line([(cx + DW, DY), (400, DY), (400, 127), (NX + NW + 2, 127)], m + '-k', width=2.2))
b.append(t(cx + DW + 10, DY - 12, 'yes', size=15.5, anchor='start', weight='700'))
b.append(line([(cx, DY + DH), (cx, DY + DH + 30)], m + '-k', width=2.2))
b.append(t(cx + 12, DY + DH + 14, 'no', size=15.5, anchor='start', weight='700'))
b += node(DY + DH + 32, 52, [([('bpf-next tree', 's')], 16, INK, '700'), ([('applied', 's')], 15, GREY, None)])
EY = DY + DH + 32 + 52
b += [t(cx, EY + 18, 'on to net-next, then mainline', size=15, weight='700')]
# legend
b += [line([(430, EY - 30), (470, EY - 30)], width=2.2), t(478, EY - 30, 'the road', size=14.5, anchor='start'),
      line([(430, EY - 6), (470, EY - 6)], color=GREY, width=1.6, dash='6 4'), t(478, EY - 6, 'optional', size=14.5, anchor='start', fill=GREY)]
figs['road'] = svg(EY + 34, 'The road from a change to mainline',
                   'Flowchart: the author may first open a pull request against bpf-next_base, where BPF CI runs the selftests. The patch goes '
                   'by git send-email to the bpf mailing list with PATCH bpf-next in its subject, waits in patchwork, and is reviewed by the BPF '
                   'maintainers; if changes are requested it goes back to the list. Otherwise it is applied to the bpf-next tree and goes on to '
                   'net-next, then mainline.', b, m)
save('ch12-road', figs['road'])
# ---------- Figure 12.2 for print: where the verifier lives in v7.2 ----------
# Three phases top to bottom; inside the walk, the dispatch to four checkers and the calls down to the line that
# printed the rejection. The path to the rejection is thick and in the accent.
BOX_FILL = '#EEF0F1'
def tmw(x, y, parts, size=15, anchor='middle', fill=INK, weight=None):
    w = f' font-weight="{weight}"' if weight else ''
    sp = ''.join(f'<tspan font-family="{UMONO if f == "m" else SANS}">{esc(s_)}</tspan>' for s_, f in parts)
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-size="{size}" fill="{fill}"{w} '
            f'xml:space="preserve">{sp}</text>')
def rectf(x, y, w, h, stroke=INK, sw=1.3, rx=5, fill='#FFFFFF'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
m = 'ah-12-2p'
b = [markers(m).replace('</defs>', f'<marker id="{m}-t" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4.6" markerHeight="4.6" '
                                    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{P2}"/></marker></defs>')]
TH = 2.8
def phase(y, title, sub, fn, fl):
    return [rectf(8, y, 664, 50), t(22, y + 16, title, size=16, anchor='start', weight='700'),
            t(22, y + 36, sub, size=14.5, anchor='start'),
            t(590, y + 25, fn, size=15, anchor='end', fam=UMONO, weight='700'), t(660, y + 25, fl, size=14.5, anchor='end', fam=UMONO, fill=GREY)]
b += [rectf(190, 8, 300, 50), tmw(340, 24, [('bpf_check()', 'm'), (' · ', 's'), ('verifier.c', 'm')], size=16, weight='700'),
      t(340, 44, 'runs once each time a program is loaded', size=14.5)]
b += [line([(510, 22), (552, 22)], color=P2, width=TH), t(560, 22, 'the path to', size=14.5, anchor='start', fill=P2, weight='700'),
      t(560, 40, 'the rejection', size=14.5, anchor='start', fill=P2, weight='700')]
b.append(line([(340, 58), (340, 73)], m + '-k', width=1.6))
b += phase(74, '1 · check the shape', 'jumps in range · no dead code · loops found', 'bpf_check_cfg()', 'cfg.c')
b.append(line([(340, 124), (340, 139)], m + '-k', width=1.6))
# phase 2, a frame around the walk
P2Y0, P2Y1 = 140, 380
b += [rectf(8, P2Y0, 664, P2Y1 - P2Y0, stroke=GREY, sw=1.2, fill=BOX_FILL),
      t(22, P2Y0 + 18, '2 · walk every path', size=16, anchor='start', weight='700'),
      tmw(660, P2Y0 + 18, [('do_check()', 'm'), (' · ', 's'), ('verifier.c', 'm')], size=15, anchor='end')]
b += [rectf(109, 176, 300, 50), t(259, 192, 'do_check_insn()', size=16, fam=UMONO, weight='700'),
      t(259, 212, 'picks a checker by kind of instruction', size=14.5)]
b += [rectf(446, 176, 214, 50), t(553, 192, 'bpf_is_state_visited()', size=15, fam=UMONO, weight='700'),
      tmw(553, 212, [('states.c', 'm'), (' · seen this state?', 's')], size=14.5)]
# the dispatch: a bus under do_check_insn() to the four checkers
CW, CY = 150, 256
xs = [22, 184, 346, 508]
names = ['check_alu_op()', 'check_load_mem()', 'check_helper_call()', 'check_cond_jmp_op()']
BUS = 241
b += [line([(xs[0] + CW / 2, BUS), (xs[3] + CW / 2, BUS)], width=1.4)]
for x, n in zip(xs, names):
    hot = n == 'check_load_mem()'
    if not hot:
        b.append(line([(x + CW / 2, BUS), (x + CW / 2, CY - 1)], m + '-k', width=1.4))
    b += [rectf(x, CY, CW, 34, stroke=P2 if hot else INK, sw=TH if hot else 1.3),
          t(x + CW / 2, CY + 17, n, size=14.5, fam=UMONO, weight='700', fill=P2 if hot else INK)]
HX = xs[1] + CW / 2
b.append(line([(HX, 226), (HX, CY - 2)], m + '-t', color=P2, width=TH))
# down to the line that printed the message
RY = 318
b += [line([(HX, CY + 34), (HX, RY - 2)], m + '-t', color=P2, width=TH),
      rectf(184, RY, 150, 34, stroke=P2, sw=TH), t(259, RY + 17, 'check_mem_access()', size=15, fam=UMONO, weight='700', fill=P2),
      line([(334, RY + 17), (362, RY + 17)], m + '-t', color=P2, width=TH),
      rectf(364, RY, 150, 34, stroke=P2, sw=TH),
      tmw(439, RY + 17, [('line 6322 ', 's'), ('verbose()', 'm')], size=15, fill=P2, weight='700'),
      line([(514, RY + 17), (534, RY + 17)], m + '-k', width=1.4),
      rectf(536, RY, 124, 34), t(598, RY + 17, 'reg_type_str()', size=15, fam=UMONO, weight='700'),
      tmw(598, RY + 46, [('log.c', 'm'), (' · words the type', 's')], size=14.5, fill=GREY)]
b.append(line([(340, P2Y1), (340, P2Y1 + 15)], m + '-k', width=1.6))
b += phase(P2Y1 + 16, '3 · rewrite for running', 'ctx field loads, helper calls, small fixes', 'bpf_do_misc_fixups() …', 'fixups.c')
H122 = P2Y1 + 16 + 50 + 8
figs['map'] = svg(H122, 'Where the verifier lives in Linux v7.2',
                  'bpf_check() in verifier.c runs once each time a program is loaded, in three phases: 1, check the shape (jumps in range, no dead '
                  'code, loops found), bpf_check_cfg() in cfg.c; 2, walk every path, do_check() in verifier.c, where do_check_insn() picks a '
                  'checker by kind of instruction (check_alu_op, check_load_mem, check_helper_call, check_cond_jmp_op) and bpf_is_state_visited() '
                  'in states.c asks whether a state was seen; the thick path runs from do_check_insn() to check_load_mem(), check_mem_access() '
                  'and verbose() at line 6322, which calls reg_type_str() in log.c to word the type; 3, rewrite for running (ctx field loads, '
                  'helper calls, small fixes), bpf_do_misc_fixups() and more in fixups.c.', b, m)
save('ch12-map', figs['map'])
print('ch12 figures ok')
