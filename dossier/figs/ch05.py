# Chapter 5 figures: the parts of one log; from reason line to rule to the lost proof.
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *

figs = {}

def mono(x, y, t, size=10.5, col='gray', weight=None):
    w = f' font-weight="{weight}"' if weight else ''
    return (f'<text x="{x}" y="{y}" dominant-baseline="central" font-size="{size}" font-family="{MONO}" '
            f'fill="{C[col][2]}"{w}>{esc(t)}</text>')

# ---------- Figure 5.2: one log, its parts, read from the bottom up ----------
m = 'ah-5-2'
b = []
rows = [
    ('gray', '; if (curr_val) { @ past.bpf.c:18', 'your C line, from the object\'s BTF'),
    ('teal', '9: (15) if r0 == 0x0 goto pc+2 ; R0=map_value(…,vs=8)', 'an instruction, then what it changed'),
    ('gray', '; __atomic_fetch_add(…, *(curr_val + 1), …); @ past.bpf.c:19', 'your C line'),
    ('amber', '10: (79) r1 = *(u64 *)(r0 +8)', 'where the walk stopped'),
    ('coral', 'invalid access to map value, value_size=8 off=8 size=8', 'the reason: which rule failed,'),
    ('coral', 'R0 min value is outside of the allowed memory range', 'and for which register'),
    ('gray', 'processed 10 insns (limit 1000000) … total_states 1 …', 'statistics, printed even on rejection'),
]
y0, rh = 18, 30
for i, (col, line, lab) in enumerate(rows):
    y = y0 + i * rh
    l, d, xx = C[col]
    b.append(f'<rect x="44" y="{y}" width="596" height="{rh - 4}" rx="3" fill="{l}" stroke="{d}" stroke-width="0.7"/>')
    b.append(mono(54, y + (rh - 4) / 2, line, col=col, weight='600' if col in ('amber', 'coral') else None))
    b.append(tx(632, y + (rh - 4) / 2, lab, size=10.5, col=col, anchor='end', italic=True))
# read-upward arrow on the left
top, bot = y0 + 4, y0 + 7 * rh - 8
b.append(arrow(28, bot, 28, top, m, width=2.2, color=C['amber'][1]))
b.append(f'<text x="14" y="{(top + bot) / 2}" font-size="11" fill="{C["amber"][1]}" text-anchor="middle" '
         f'transform="rotate(-90 14 {(top + bot) / 2})" dominant-baseline="central">read from the bottom up</text>')
yb = y0 + 7 * rh + 8
b.append(bar(yb, 30, 'Skip the statistics, read the reason, then climb the walk to the line where the proof went missing.'))
figs['parts'] = svg(yb + 40, 'The parts of one rejection log',
                    'A seven-line rejection log split into C source lines, walked instructions, the stopping instruction, the reason and the statistics line', b, m)

# ---------- Figure 5.3: from reason line to rule to the lost proof ----------
m = 'ah-5-3'
b = []
cols = [(20, 220, 'coral', 'the reason line says'), (250, 190, 'teal', 'the rule behind it'),
        (460, 200, 'amber', 'where the proof was lost')]
for x, w, col, h in cols:
    b.append(tx(x + w / 2, 14, h, size=12, col=col, weight='600'))
rows = [
    (['R0 invalid mem access', "'map_value_or_null'"],
     ['a pointer that may be NULL', 'is read only after a test', 'on the same path'],
     ['slots 9 to 10: the lookup\'s', 'result is read with no test', 'of r0 in between']),
    (['invalid access to map value,', 'value_size=8 off=8 size=8'],
     ['every access through a map', 'value stays inside the', 'value\'s size'],
     ['curr_val + 1: offset 8 of', 'an 8-byte value, on every', 'path through that line']),
    (['BPF program is too large.', 'Processed 1000001 insn'],
     ['the walk must reach every', 'exit within one million', 'instructions'],
     ['the loop test: its bound is', 'read from the map, so the', 'walk never sees a last round']),
]
y = 28
H = 66
for left, mid, right in rows:
    for (x, w, col, _), lines in zip(cols, (left, mid, right)):
        b.append(box(x, y, w, H, col, sw=1.2 if col == 'coral' else 0.9))
        n = len(lines)
        for j, t in enumerate(lines):
            ty = y + H / 2 + (j - (n - 1) / 2) * 16
            if col == 'coral':
                b.append(mono(x + 10, ty, t, size=10.5, col='coral', weight='600'))
            else:
                b.append(tx(x + w / 2, ty, t, size=11, col=col))
    b.append(arrow(242, y + H / 2, 248, y + H / 2, m, width=1.0))
    b.append(arrow(442, y + H / 2, 458, y + H / 2, m, width=1.0))
    y += H + 10
b.append(bar(y + 2, 30, 'The log says where the walk stopped. The fix goes where the proof was lost.'))
figs['rules'] = svg(y + 42, 'From reason line to rule to the lost proof',
                    'Three rejection messages from the learner\'s program, each mapped to the rule it enforces and to the place where the program lost the proof', b, m)

save('ch05-parts', figs['parts'])
save('ch05-rules', figs['rules'])
print('ch05 figures ok')
