# Epilogue "Limits, traps, and where it went" (src/epilogue.html): its one drawn figure.
# Drawn to the print rules in NOTES.md "Figure rules": 680 units = 127 mm, words 14.5 units or more,
# Open Sans Condensed for words, Ubuntu Mono for code names, black and grey with one accent.
# Sources: hXDP, Brunella et al., OSDI 2020, abstract and sections 2-4 (156.25 MHz, about 15% of the FPGA,
# Sephirot's four lanes, one helper call a cycle, one memory area for all maps, 6.53 Mpps on the simple firewall);
# eHDL, Rivitti et al., ASPLOS 2023, abstract, sections 1-3 and 5.5 (a pipeline per program, a helper block per call,
# RAW and WAR hazards on map memory, 6.5-13.3% of the FPGA, 148 Mpps at 100 Gb/s with 64-byte packets, synthesis of
# "few hours"). Both PDFs fetched 13 November 2026.
import sys, os
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


def rect(x, y, w, h, stroke=INK, sw=1.3, fill='#FFFFFF', dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}"{da}/>')


def node(x, y, w, h, title, lines=(), hard=False, mono=False):
    """A step: its name in bold, then what it does in plain words. A hard part is drawn thick, in the accent."""
    out = rect(x, y, w, h, stroke=ACC if hard else INK, sw=2.6 if hard else 1.3, fill=ACCL if hard else '#FFFFFF')
    top = y + h / 2 - 9.5 * len(lines)
    out += t(x + w / 2, top, title, size=16, weight='700', fam=UMONO if mono else SANS, fill=ACC if hard else INK)
    for i, ln in enumerate(lines):
        out += t(x + w / 2, top + 20 + 18 * i, ln, size=14.5, fill=GREY)
    return out


def arrow(x1, y1, x2, y2, mid, color=INK, width=1.6):
    return (f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'marker-end="url(#{mid})"/>')


# ---------- epilogue-hw: hXDP's processor beside eHDL's pipeline ----------
# Claim: hXDP builds one processor on the FPGA that runs any XDP program, four instructions a cycle; eHDL builds a new
# circuit for each program, a pipeline with a packet in every stage; in both, helpers and maps are the hard parts.
m = 'ah-epilogue-hw'
b = []
L, R, W = 12, 352, 316                      # left panel x, right panel x, panel width
LC, RC = L + W / 2, R + W / 2
b.append(f'<line x1="340" y1="6" x2="340" y2="402" stroke="{LIGHT}" stroke-width="1.2" stroke-dasharray="5 4"/>')
b += [t(LC, 14, 'hXDP, OSDI 2020', size=16, weight='700'),
      t(LC, 34, 'one processor runs every program', size=14.5, fill=GREY, italic=True),
      t(RC, 14, 'eHDL, ASPLOS 2023', size=16, weight='700'),
      t(RC, 34, 'a new circuit for each program', size=14.5, fill=GREY, italic=True)]
# the program, unchanged in both
for cx in (LC, RC):
    b.append(node(cx - 110, 50, 220, 34, 'XDP program, as bytecode'))
    b.append(arrow(cx, 84, cx, 104, m))
b.append(node(L, 106, W, 60, 'compiler', ['drops bounds checks and zeroing,', 'packs up to 4 instructions a row']))
b.append(node(R, 106, W, 60, 'high-level synthesis', ['groups independent instructions', 'into stages; hours per program']))
for cx in (LC, RC):
    b.append(arrow(cx, 166, cx, 186, m))
# hXDP: the core and its four lanes
b.append(rect(L, 188, W, 96))
b.append(t(LC, 204, 'Sephirot, a VLIW core', size=16, weight='700'))
for i in range(4):
    x = L + 12 + i * 75
    b += [rect(x, 220, 67, 30, sw=1.1), t(x + 33.5, 235, f'lane {i + 1}', size=14.5)]
b.append(t(LC, 268, 'one row a cycle, at 156.25 MHz', size=14.5, fill=GREY))
# eHDL: the pipeline
b.append(rect(R, 188, W, 96))
b.append(t(RC, 204, 'a pipeline of stages', size=16, weight='700'))
for i, lab in enumerate(['stage 1', 'stage 2', '…', 'stage n']):
    x = R + 10 + i * 78
    if lab == '…':
        b.append(t(x + 31, 235, lab, size=16, weight='700'))
    else:
        b += [rect(x, 220, 62, 30, sw=1.1), t(x + 31, 235, lab, size=14.5)]
    if i < 3:
        b.append(arrow(x + 62 if lab != '…' else x + 46, 235, x + 78 if i != 1 else x + 94, 235, m, width=1.3))
b.append(t(RC, 268, 'a different packet in every stage', size=14.5, fill=GREY))
# the hard parts
for cx in (LC, RC):
    b.append(arrow(cx - 80, 284, cx - 80, 304, m))
    b.append(arrow(cx + 80, 284, cx + 80, 304, m))
b.append(node(L, 306, 152, 52, 'helper unit', ['one call a cycle'], hard=True))
b.append(node(L + 164, 306, 152, 52, 'maps memory', ['one area, all maps'], hard=True))
b.append(node(R, 306, 152, 52, 'helper blocks', ['one per call site'], hard=True))
b.append(node(R + 164, 306, 152, 52, 'map memory', ['hazards across stages'], hard=True))
# what each design reached
b += [t(LC, 376, 'about 15% of the FPGA', size=14.5, fill=GREY),
      t(LC, 394, '6.53 Mpps on the simple firewall', size=14.5, fill=GREY),
      t(RC, 376, '6.5 to 13.3% of the FPGA', size=14.5, fill=GREY),
      t(RC, 394, '148 Mpps: 100 Gb/s of 64-byte packets', size=14.5, fill=GREY)]
# legend
b += [rect(150, 414, 34, 18, stroke=ACC, sw=2.6, fill=ACCL),
      t(192, 423, 'where both designs did the most work: helpers and maps', size=14.5, anchor='start')]
fig = svg(440, 'hXDP and eHDL: one processor for every program, or a circuit for each',
          'Two panels. Left, hXDP (OSDI 2020): an XDP program as bytecode goes to a compiler that drops bounds checks and '
          'zeroing and packs up to four instructions a row, then runs on Sephirot, a VLIW core with four lanes that issues one '
          'row a cycle at 156.25 MHz; below it a helper unit takes one call a cycle and one memory area holds all maps; '
          'about 15 percent of the FPGA, 6.53 Mpps on the simple firewall. Right, eHDL (ASPLOS 2023): the same bytecode goes '
          'through high-level synthesis, which groups independent instructions into stages and takes hours per program, '
          'giving a pipeline of stages with a different packet in each; below it one helper block per call site and a map '
          'memory with hazards across stages; 6.5 to 13.3 percent of the FPGA, 148 Mpps at 100 Gb/s of 64-byte packets. '
          'Helpers and maps are drawn thick in the accent in both panels.', b, m)
save('epilogue-hw', fig)
