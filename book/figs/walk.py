# Chapter "The verifier walks every path" (src/walk.html): figures new in the merge.
# The chapter's other figures keep their old scripts (figs/ch04.py: ch04-walk-flow, ch04-reg).
# Drawn to the print rules in NOTES.md "Figure rules": 680 units = 127 mm, words 14.5 units or more,
# Open Sans Condensed for words, Ubuntu Mono for code names, black and grey with one accent.
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import esc, svg, save

SANS = "'Open Sans Condensed', 'Open Sans', 'Myriad Pro', sans-serif"
UMONO = "'Ubuntu Mono', 'JetBrains Mono', monospace"
INK, GREY, ACC = '#1F2328', '#4A5056', '#0F6E56'


def t(x, y, s_, size=15, anchor='middle', fam=SANS, weight=None, fill=INK, italic=False):
    w = f' font-weight="{weight}"' if weight else ''
    it = ' font-style="italic"' if italic else ''
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-family="{fam}" '
            f'font-size="{size}" fill="{fill}"{w}{it}>{esc(s_)}</text>')


def rect(x, y, w, h, l1, l2=None, stroke=INK, sw=1.3, fill_text=INK, note=None):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#FFFFFF" stroke="{stroke}" stroke-width="{sw}"/>'
    if note is not None:         # an outcome: what happens, in words, and a remark under it in grey
        return (out + t(x + w / 2, y + h / 2 - 10, l1, size=16, weight='700', fill=fill_text)
                + t(x + w / 2, y + h / 2 + 12, note, size=14.5, fill=GREY, italic=True))
    if l2 is None:
        return out + t(x + w / 2, y + h / 2, l1, size=15.5, fill=fill_text)
    return (out + t(x + w / 2, y + h / 2 - 10, l1, size=16, fam=UMONO, weight='700', fill=fill_text)
            + t(x + w / 2, y + h / 2 + 11, l2, size=15, fill=GREY))


def diamond(cx, cy, hw, hh, l1, l2):
    return (f'<polygon points="{cx - hw},{cy} {cx},{cy - hh} {cx + hw},{cy} {cx},{cy + hh}" fill="#FFFFFF" '
            f'stroke="{INK}" stroke-width="1.3"/>' + t(cx, cy - 10, l1, size=15.5) + t(cx, cy + 10, l2, size=15.5))


def line(pts, mid, color=INK, width=1.8, dash=None, arrow=True):
    d = ' '.join(f'{"M" if i == 0 else "L"}{x},{y}' for i, (x, y) in enumerate(pts))
    da = f' stroke-dasharray="{dash}"' if dash else ''
    me = f' marker-end="url(#{mid})"' if arrow else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da}{me}/>'


# ---------- what the walk does at a prune point (bpf_is_state_visited(), kernel/bpf/states.c, v7.2) ----------
# Claim: at each prune point the walk asks three questions in order; two answers end the path (one accepts
# it, one refuses the program) and one saves a checkpoint. Ending a path is the accent, drawn thicker.
m = 'ah-walk-cp'
b = []
cx = 230
b.append(rect(70, 8, 320, 56, 'bpf_is_state_visited()', 'at a jump, a jump target or after a call'))
b.append(line([(cx, 64), (cx, 92)], m))
# question 1: pruning
b.append(diamond(cx, 150, 160, 56, 'does a finished state saved', 'here cover this one?'))
b.append(line([(cx + 160, 150), (452, 150)], m, color=ACC, width=3))
b.append(t(cx + 172, 136, 'yes', size=15.5, anchor='start', weight='700', fill=ACC))
b.append(rect(456, 118, 216, 64, 'path done: pruned', stroke=ACC, sw=2.6, fill_text=ACC, note='the log says “25: safe”'))
b.append(t(cx - 12, 222, 'no', size=15.5, anchor='end', weight='700'))
b.append(line([(cx, 206), (cx, 250)], m))
# question 2: a loop that never changes
b.append(diamond(cx, 306, 160, 56, 'is an earlier round of this', 'path at this slot identical?'))
b.append(line([(cx + 160, 306), (452, 306)], m, width=3))
b.append(t(cx + 172, 292, 'yes', size=15.5, anchor='start', weight='700'))
b.append(rect(456, 274, 216, 64, 'refused: infinite loop', sw=2.6, note='-EINVAL, the load ends'))
b.append(t(cx - 12, 378, 'no', size=15.5, anchor='end', weight='700'))
b.append(line([(cx, 362), (cx, 406)], m))
# question 3: save a checkpoint?
b.append(diamond(cx, 462, 160, 56, '2 jumps and 8 instructions', 'since the last save?'))
b.append(line([(cx + 160, 462), (452, 462)], m))
b.append(t(cx + 172, 448, 'yes', size=15.5, anchor='start', weight='700'))
b.append(rect(456, 436, 216, 52, 'save a checkpoint', None))
b.append(t(cx - 12, 534, 'no', size=15.5, anchor='end', weight='700'))
b.append(line([(cx, 518), (cx, 562)], m))
b.append(line([(564, 488), (564, 590), (392, 590)], m))
b.append(rect(68, 564, 324, 52, 'walk on to the next instruction', None))
# remarks beside the nodes they qualify
b.append(t(8, 228, 'cover: at least as general in', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(8, 246, 'every live register and slot', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(456, 360, 'at bpf_loop, iterator and may_goto', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(456, 378, 'slots, a state within the earlier', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(456, 396, 'round’s also ends the path', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(8, 534, 'in a loop: 20 jumps', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(8, 552, 'or 100 instructions', size=14.5, anchor='start', fill=GREY, italic=True))
fig = svg(626, 'What the walk does at a prune point',
          'Flowchart of bpf_is_state_visited in Linux v7.2. First: does a finished state saved at this instruction '
          'cover the current one? If yes the path is pruned. Second: is an earlier round of this path at this '
          'instruction identical? If yes the program is refused with infinite loop detected. Third: have two jumps '
          'and eight instructions passed since the last save? If yes a checkpoint is saved. Then the walk goes on.',
          b, m)
save('walk-checkpoint', fig)
