# Figures for chapter 10, redrawn for print (figure rules in NOTES.md): 680 units = 127 mm,
# words 14.5 units or more, node titles 16, black and grey with the one accent.
# The screen versions are kept in figs/pre-print/ch10.py.
# Figure 10.4 (the object's sections and the BTF of write_counts) is now an HTML table in src/ch10.html;
# figs/out/ch10-object.svg is no longer used.
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

# ---------- Figure 10.1: the write counter through clang, as a flowchart ----------
# Steps top to bottom; the two checks that stop a build are diamonds with a "yes" exit to the right;
# the passes the BPF target adds are notes in the accent, joined by dashed lines to where each runs.
m = 'ah-10-1p'
b = [markers(m)]
X0, X1 = 8, 372                 # the flow column
FX = (X0 + X1) / 2
IX0, IX1 = 22, 358              # steps inside the back end
RX = 394                        # the notes on the right
def step(y0, h, title, sub, x0=X0, x1=X1, tfam=SANS):
    cx = (x0 + x1) / 2
    out = [rect(x0, y0, x1 - x0, h)]
    out.append(tm(cx, y0 + 15, title, size=16, weight='700') if isinstance(title, list) else t(cx, y0 + 15, title, size=16, weight='700', fam=tfam))
    out.append(tm(cx, y0 + h - 14, sub, size=14.5) if isinstance(sub, list) else t(cx, y0 + h - 14, sub, size=14.5))
    return out
def down(y0, y1, x=FX):
    return line([(x, y0), (x, y1 - 1)], m + '-k', width=1.6)
def note(y, name, lines, to):
    """A pass of the BPF target: its name in the accent, what it does below, a dashed line to where it runs."""
    out = [t(RX, y, name, size=15, anchor='start', fam=UMONO, weight='700', fill=P2)]
    for k, s_ in enumerate(lines):
        out.append(t(RX, y + 18 * (k + 1), s_, size=14.5, anchor='start'))
    pts = [(RX - 6, y), to] if abs(to[1] - y) < 8 or to[0] >= X1 - 20 else [(RX - 6, y), (RX - 12, y), (RX - 12, to[1]), to]
    out += [line(pts, color=P2, width=1.6, dash='5 4'), f'<circle cx="{to[0]}" cy="{to[1]}" r="3" fill="{P2}"/>']
    return out

# the source, a terminal
b += [rect(X0, 8, X1 - X0, 32, rx=16),
      tm(FX, 24, [('hashmap.bpf.c', 'm'), (' + ', 's'), ('vmlinux.h', 'm'), (' + ', 's'), ('bpf_helpers.h', 'm')], size=15, weight='700'),
      t(RX, 24, 'your C, and the headers it includes', size=14.5, anchor='start', fill=GREY)]
b.append(down(40, 56))
b += step(56, 46, 'Front end · clang', [('parses the C, expands ', 's'), ('SEC()', 'm'), (' and ', 's'), ('__uint()', 'm'), (', writes LLVM IR', 's')])
b += [down(102, 126), t(FX - 10, 114, 'IR', size=14.5, anchor='end', fam=UMONO, fill=GREY)]
b += step(126, 46, [('Middle · LLVM at ', 's'), ('-O2', 'm')], 'general passes: locals into registers, dead code removed')
b.append(down(172, 190))
# the back end, a grey frame around its steps
FY0 = 190
b += [rect(X0, FY0, X1 - X0, 0, stroke=GREY, sw=1.2, fill=BOX_FILL)]          # height set below
b.append(tm(FX, FY0 + 17, [('BPF back end · ', 's'), ('llvm/lib/Target/BPF', 'm')], size=16, weight='700'))
y = FY0 + 34
b += step(y, 46, 'instruction selection', [('IR operations become BPF instructions (', 's'), ('BPFInstrInfo.td', 'm'), (')', 's')], IX0, IX1)
S1 = y; y += 46
b.append(down(y, y + 14)); y += 14
b += step(y, 46, 'register allocation', 'values go to r0–r9; r10 stays the frame pointer', IX0, IX1); y += 46
b.append(down(y, y + 14)); y += 14
b += step(y, 46, 'frame layout', 'stack slots below r10, at most 512 bytes', IX0, IX1); y += 46
b.append(down(y, y + 14)); y += 14
DW, DH = 118, 24
D1 = y + DH
b += [diamond(FX, D1, DW, DH), t(FX, D1, 'stack reaches 512 bytes?', size=15)]
y = D1 + DH
b += [down(y, y + 18), t(FX + 10, y + 9, 'no', size=15, anchor='start', weight='700')]; y += 18
D2 = y + DH
b += [diamond(FX, D2, DW, DH), t(FX, D2, "XADD's return value used?", size=15)]
y = D2 + DH
b += [down(y, y + 18), t(FX + 10, y + 9, 'no', size=15, anchor='start', weight='700')]; y += 18
b += step(y, 46, 'object writer', [('bytes, relocations, and ', 's'), ('BTFDebug', 'm'), (': ', 's'), ('.BTF', 'm'), (', ', 's'), ('.BTF.ext', 'm')], IX0, IX1)
y += 46
FY1 = y + 10
b[b.index(rect(X0, FY0, X1 - X0, 0, stroke=GREY, sw=1.2, fill=BOX_FILL))] = rect(X0, FY0, X1 - X0, FY1 - FY0, stroke=GREY, sw=1.2, fill=BOX_FILL)
b.append(down(y, FY1 + 16)); y = FY1 + 16
b += [rect(X0, y, X1 - X0, 32, rx=16),
      tm(FX, y + 16, [('hashmap.bpf.o', 'm'), (': an ELF object with code, maps, license, BTF', 's')], size=15, weight='700')]
H101 = y + 32 + 8
# the two checks: where the build stops
for yc, lines in [(D1, [('stops the build:', True), ('"Looks like the BPF stack limit is exceeded"', False), ('BPFRegisterInfo.cpp', 'm')]),
                  (D2, [([('stops the build on ', 's'), ('-mcpu=v1', 'm'), (' and ', 's'), ('v2', 'm'), (':', 's')], True), ('"Invalid usage of the XADD return value"', False), ('BPFMIPreEmitChecking', 'm')])]:
    b += [line([(FX + DW, yc), (RX - 8, yc)], m + '-k', width=1.6), t(FX + DW + 8, yc - 11, 'yes', size=15, anchor='start', weight='700')]
    for k, (s_, kind) in enumerate(lines):
        yy = yc + (k - 1) * 18
        if isinstance(s_, list):
            b.append(tm(RX, yy, s_, size=14.5, anchor='start', weight='700'))
            continue
        b.append(t(RX, yy, s_, size=15 if kind == 'm' else 14.5, anchor='start', fam=UMONO if kind == 'm' else SANS,
                   weight='700' if kind is True else None, fill=GREY if kind == 'm' else INK))
# the passes the BPF target adds, beside where each runs
b += note(78, 'BPFAbstractMemberAccess', ['pipeline start: a CO-RE field read', 'becomes a named, patchable constant'], (FX + 2, 114))
b += note(146, 'BPFAdjustOpt · BPFIRPeephole', ['steer general passes toward code', "the kernel's checker can follow"], (X1, 149))
b += note(212, 'BPFCheckAndAdjustIR', ['last IR fix-ups before selection'], (X1, FY0 + 17))
b += note(262, 'BPFMISimplifyPatchable', ['folds the CO-RE constant into', 'the instruction that uses it'], (IX1, S1 + 23))
# legend
LY = H101 - 58
b += [line([(RX, LY), (RX + 40, LY)], m + '-k', width=1.6), t(RX + 48, LY, 'the build, top to bottom', size=14.5, anchor='start'),
      line([(RX, LY + 24), (RX + 40, LY + 24)], color=P2, width=1.6, dash='5 4'),
      t(RX + 48, LY + 24, 'where a pass of the BPF target runs', size=14.5, anchor='start', fill=P2)]
fig101 = svg(H101, 'The write counter through clang: front end, middle, BPF back end',
             'A flowchart. hashmap.bpf.c with vmlinux.h and bpf_helpers.h goes through the front end (clang parses the C, expands SEC() and '
             '__uint() and writes LLVM IR), the middle (LLVM at -O2: locals into registers, dead code removed) and the BPF back end in '
             'llvm/lib/Target/BPF: instruction selection, register allocation, frame layout, a check for a stack reaching 512 bytes, a check '
             'for a used XADD return value, and the object writer, ending in hashmap.bpf.o. A yes at either check stops the build. '
             'Beside the stages, joined by dashed lines: BPFAbstractMemberAccess at the pipeline start, BPFAdjustOpt and BPFIRPeephole in '
             'the middle, BPFCheckAndAdjustIR before selection and BPFMISimplifyPatchable after it.', b, m)
save('ch10-pipeline', fig101)
print('ch10 figures ok')
