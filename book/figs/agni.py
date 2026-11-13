# Chapter "Reading Agni: proving Linux's range analysis" (src/agni.html): its three drawn figures.
# Drawn to the print rules in NOTES.md "Figure rules": 680 units = 127 mm, words 14.5 units or more,
# Open Sans Condensed for words, Ubuntu Mono for code names, black and grey with one accent.
# Sources: agni-pipeline follows Figure 1 and Section 5 of the CAV 2023 paper (authors' copy, 30 May 2023) and
# the artifact repository github.com/bpfverif/agni (main at 9096fbd10376, pushed 19 May 2026; encodings in
# bpf-encodings/5.10); agni-operator follows verifier.c of v5.12 and v5.13 and book/labs/agni/repro.py, run
# 13 November 2026; agni-time is Table 2 of the SAS 2024 paper (preprint) and the LPC 2024 slides.
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
            f'stroke="{INK}" stroke-width="1.3"/>' + t(cx, cy - 10, l1, size=16, weight='700')
            + t(cx, cy + 11, l2, size=14.5, fill=GREY))


def note(x, y, lines, anchor='start'):
    return ''.join(t(x, y + 18 * i, ln, size=14.5, anchor=anchor, fill=GREY, italic=True)
                   for i, ln in enumerate(lines))


# ---------- agni-pipeline: from verifier.c to a verdict and a program ----------
# Claim: Agni writes no formula by hand. It compiles the verifier's own C, slices it to one instruction, turns
# the IR into one SMT formula per instruction, checks it against two specifications in turn, and looks for a
# short program only when both fail.
m = 'ah-agni-pipeline'
b = []
CX, BW, BX = 190, 340, 20
steps = [(8, 'verifier.c + a wrapper', ['clang turns them into LLVM IR'], True),
         (82, 'LLVM passes', ['inline every call, fix the opcode, drop dead code'], False),
         (156, 'LLVMToSMT', ['one SMT-LIB formula per instruction'], True)]
for y, l1, ls, mono in steps:
    b.append(rect(BX, y, BW, 58, l1, ls, mono1=mono))
for y in (66, 140):
    b.append(line([(CX, y), (CX, y + 16)], m))
b.append(note(380, 22, ['jump wrappers copy kernel code by hand,', 'one copy per range of kernel versions']))
b.append(note(380, 100, ['no loops or recursion: the calls', 'inline into one acyclic function']))
b.append(note(380, 174, ['5.10: BPF_AND 100 KB, BPF_SYNC 49 KB,', 'BPF_JLT 739 KB']))
# the three questions
D1, D2, D3 = 270, 376, 562
b.append(line([(CX, 214), (CX, D1 - 42)], m))
b.append(diamond(CX, D1, 150, 42, 'gen holds?', 'Z3; inputs: any values'))
b.append(diamond(CX, D2, 150, 42, 'sro holds?', 'inputs passed through the tail'))
b.append(line([(CX, D1 + 42), (CX, D2 - 42)], m))
b.append(t(CX - 10, D1 + 53, 'no', size=15, anchor='end', weight='700'))
b.append(rect(BX, 446, BW, 58, 'differential synthesis', ['programs of 1, 2, then 3 instructions'], mono1=False))
b.append(line([(CX, D2 + 42), (CX, 446)], m))
b.append(t(CX - 10, D2 + 55, 'no', size=15, anchor='end', weight='700'))
b.append(line([(CX, 504), (CX, D3 - 42)], m))
b.append(diamond(CX, D3, 150, 42, 'program found?', 'up to the time limit'))
# exits to the right
RX, RW = 430, 240
b.append(line([(CX + 150, D1), (RX, D1)], m, color=ACC, width=2.6))
b.append(t(CX + 160, D1 - 13, 'yes', size=15, anchor='start', weight='700', fill=ACC))
b.append(rect(RX, D1 - 29, RW, 58, 'sound', ['for every input, at 64 bits'], mono1=False, stroke=ACC, sw=2.6,
              fill_text=ACC))
b.append(line([(CX + 150, D2), (RX, D2)], m, color=ACC, width=2.6))
b.append(t(CX + 160, D2 - 13, 'yes', size=15, anchor='start', weight='700', fill=ACC))
b.append(rect(RX, D2 - 29, RW, 58, 'sound', ['the gen violation is latent'], mono1=False, stroke=ACC, sw=2.6,
              fill_text=ACC))
b.append(line([(CX + 150, D3), (RX, D3)], m))
b.append(t(CX + 160, D3 - 13, 'yes', size=15, anchor='start', weight='700'))
b.append(rect(RX, D3 - 29, RW, 58, 'a bug, shown', ['the program runs in QEMU'], mono1=False))
b.append(line([(CX, D3 + 42), (CX, 634)], m))
b.append(t(CX - 10, D3 + 55, 'no', size=15, anchor='end', weight='700'))
b.append(rect(BX, 634, BW, 46, 'inspect by hand: latent, or longer', [], mono1=False, sw=1.1))
fig = svg(688, 'From verifier.c to a verdict',
          'Flowchart. The verifier source with a wrapper per instruction is compiled by clang to LLVM IR; LLVM passes '
          'inline every call, fix the opcode and drop dead code; LLVMToSMT writes one SMT-LIB formula per instruction. '
          'Z3 checks the general specification; if it holds, the operator is sound. If not, the refined specification '
          'with inputs passed through the shared tail; if that holds, the operator is sound and the first violation is '
          'latent. If not, differential synthesis tries programs of one, two and three instructions; a program found '
          'shows the bug and is run in QEMU, otherwise the case is inspected by hand.', b, m)
save('agni-pipeline', fig)


# ---------- agni-operator: one AND, five values, a shared tail ----------
# Claim: the kernel's AND fills each output domain from several input domains, then runs a tail every operator
# shares; the refined specification passes the inputs through the same tail first. For 5.12 the claim fails in
# the two 32-bit domains.
m = 'ah-agni-operator'
b = []
DOM = ['tnum', 'u64', 's64', 'u32', 's32']
CW, CH, X0 = 54, 28, 52
def regrow(y, name, marks=None):
    out = t(X0 - 12, y + CH / 2, name, size=16, anchor='end', weight='700', fam=UMONO)
    for i, d in enumerate(DOM):
        bad = marks and d in marks
        out += (f'<rect x="{X0 + i * CW}" y="{y}" width="{CW}" height="{CH}" fill="{ACCL if bad else "#FFFFFF"}" '
                f'stroke="{ACC if bad else INK}" stroke-width="{2.4 if bad else 1.1}"/>')
        out += t(X0 + i * CW + CW / 2, y + CH / 2, d, size=15, fam=UMONO, weight='700' if bad else None,
                 fill=ACC if bad else INK)
    return out
FX, FW = 30, 300                      # the flow column
FC = FX + FW / 2
b.append(regrow(8, 'P'))
b.append(regrow(42, 'Q'))
b.append(note(350, 16, ['two registers, five values each;', 'x is in all five of P, y in all five of Q']))
b.append(line([(FC, 72), (FC, 92)], m))
b.append(rect(FX, 92, FW, 46, 'the tail, on P and on Q', [], mono1=False, stroke=GREY, sw=1.4, dash='6 4'))
b.append(note(350, 104, ['sro only; gen skips this step']))
steps = [(160, 'tnum_and()', 'tnum from the two tnums'),
         (226, 'scalar32_min_max_and()', None),
         (292, 'scalar_min_max_and()', None)]
for y, l1, _ in steps:
    b.append(rect(FX, y, FW, 46, l1, []))
for y0, y1 in ((138, 160), (206, 226), (272, 292), (338, 358)):
    b.append(line([(FC, y0), (FC, y1)], m))
b.append(note(350, 183, ['tnum from the two tnums']))
b.append(note(350, 234, ['u32 min from the new tnum; s32 from u32', 'if both s32 minima are not negative']))
b.append(t(350, 270, '5.12: returns early if both low halves are known', size=14.5, anchor='start', fill=ACC,
           weight='700'))
b.append(note(350, 304, ['u64 min from the new tnum; s64 from u64', 'if both s64 minima are not negative']))
b.append(f'<rect x="{FX}" y="358" width="{FW}" height="84" rx="5" fill="#FFFFFF" stroke="{INK}" stroke-width="1.3"/>')
for i, fn in enumerate(['__update_reg_bounds()', '__reg_deduce_bounds()', '__reg_bound_offset()']):
    b.append(t(FC, 378 + 21 * i, fn, size=16, fam=UMONO, weight='700'))
b.append(note(350, 372, ['the tail every ALU operator ends with:', 'bounds from the tnum, signed from', 'unsigned, tnum from the bounds']))
b.append(line([(FC, 442), (FC, 462)], m))
b.append(regrow(462, 'R', marks={'u32', 's32'}))
b.append(note(350, 470, ['is x & y in each of the five values of R?', '5.12: not in u32 or s32; 5.13: in all']))
fig = svg(500, 'One AND, five values, a shared tail',
          'Flowchart of the kernel\'s 64-bit AND on two registers P and Q, each with five values: tnum, u64, s64, '
          'u32, s32. For the refined specification only, each input first passes through the tail. Then tnum_and '
          'computes the tnum, scalar32_min_max_and the 32-bit bounds, from the new tnum and the inputs, and '
          'scalar_min_max_and the 64-bit bounds, again reading the new tnum; in 5.12 the 32-bit function returns early '
          'when both low halves are known. The tail, __update_reg_bounds, __reg_deduce_bounds and __reg_bound_offset, '
          'ends every ALU operator. The claim is that x AND y lies in each of the five values of the result R; in '
          '5.12 it fails for u32 and s32, in 5.13 it holds in all five.', b, m)
save('agni-operator', fig)


# ---------- agni-time: hours, weeks, then minutes ----------
# Claim: checking every operator of one kernel took hours, then weeks, and then did not finish as the shared tail
# grew; checked separately from the tail, each kernel takes minutes.
m = 'ah-agni-time'
b = []
VERS = ['4.14', '5.5', '5.9', '5.13', '5.19', '6.3', '6.4', '6.5', '6.6', '6.7', '6.8']
OLD = {'4.14': 150, '5.5': 150, '5.9': 240, '5.13': 600, '5.19': 2160, '6.3': 2160}   # minutes
NEW = {'4.14': 5, '5.5': 5, '5.9': 5, '5.13': 5, '5.19': 15, '6.3': 15, '6.4': 15, '6.5': 15, '6.6': 15,
       '6.7': 15, '6.8': 30}                                                          # upper bounds, minutes
X0, X1, Y0, Y1 = 92, 664, 330, 40
def px(i): return X0 + 22 + i * (X1 - X0 - 44) / (len(VERS) - 1)     # i may be fractional
def py(minutes): return Y0 - (math.log10(minutes) - 0) / 5 * (Y0 - Y1)      # 1 min to 100,000 min
b.append(f'<rect x="{X0}" y="{Y1}" width="{X1 - X0}" height="{Y0 - Y1}" fill="none" stroke="{GREY}" stroke-width="1"/>')
for mins, lab in [(1, '1 min'), (10, '10 min'), (60, '1 hour'), (600, '10 hours'), (10080, '1 week')]:
    y = py(mins)
    b.append(f'<line x1="{X0 - 5}" y1="{y:.1f}" x2="{X0}" y2="{y:.1f}" stroke="{GREY}" stroke-width="1"/>')
    b.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{LIGHT}" stroke-width="0.8" '
             f'stroke-dasharray="2 4"/>')
    b.append(t(X0 - 9, y, lab, size=14.5, anchor='end', fill=GREY))
for i, v in enumerate(VERS):
    b.append(t(px(i), Y0 + 18, v, size=14.5, fill=GREY))
b.append(t((X0 + X1) / 2, Y0 + 42, 'kernel version', size=15))
# old strategy: one formula per operator, tail included
pts = [(px(VERS.index(v)), py(mn)) for v, mn in OLD.items()]
b.append(line(pts, m, color=INK, width=2.2, arrow=False))
for x, y in pts:
    b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{INK}"/>')
for v in ('6.4', '6.5', '6.6', '6.7', '6.8'):
    x = px(VERS.index(v))
    b.append(line([(x, py(10080)), (x, Y1 + 30)], m, color=INK, width=1.8))
b.append(t((px(VERS.index('6.4')) + px(VERS.index('6.8'))) / 2, Y1 + 14, 'timeout after weeks: no answer',
           size=14.5, anchor='middle', fill=INK, weight='700'))
b.append(t(px(VERS.index('5.13')) - 8, py(2160) - 34, 'tail and operator', size=14.5, anchor='end', weight='700'))
b.append(t(px(VERS.index('5.13')) - 8, py(2160) - 16, 'in one formula', size=14.5, anchor='end', weight='700'))
# new strategy: operator and tail checked apart; bars at the bound, with the time below it
for v, mn in NEW.items():
    x, y = px(VERS.index(v)), py(mn)
    b.append(f'<line x1="{x - 13:.1f}" y1="{y:.1f}" x2="{x + 13:.1f}" y2="{y:.1f}" stroke="{ACC}" stroke-width="3.2"/>')
    b.append(line([(x, y + 2), (x, y + 22)], m, color=ACC, width=1.6))
b.append(t(px(1.5), py(60) + 13, 'operator and tail checked apart:', size=14.5, anchor='middle', fill=ACC,
           weight='700'))
b.append(t(px(1.5), py(60) + 31, 'under 5, 15 or 30 minutes', size=14.5, anchor='middle', fill=ACC,
           weight='700'))
fig = svg(386, 'Time to check one kernel',
          'Plot of the time to check every operator of one kernel, on a logarithmic scale from one minute to beyond a '
          'week, for kernels 4.14 to 6.8. With the tail and the operator in one formula: 2.5 hours for 4.14 and 5.5, '
          '4 hours for 5.9, 10 hours for 5.13, 36 hours for 5.19 and 6.3, and from 6.4 to 6.8 no answer before a '
          'timeout after weeks. With operator and tail checked apart: under 5 minutes up to 5.13, under 15 minutes '
          'up to 6.7, under 30 minutes for 6.8.', b, m)
save('agni-time', fig)
