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
    ('gray', '; if (curr_val) { @ past.bpf.c:18', 'the C line, from the object\'s BTF'),
    ('teal', '9: (15) if r0 == 0x0 goto pc+2 ; R0=map_value(…,vs=8)', 'an instruction, then what it changed'),
    ('gray', '; __atomic_fetch_add(…, *(curr_val + 1), …); @ past.bpf.c:19', 'the next C line'),
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

save('ch05-rules', figs['rules'])
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

# ---------- Figure 5.2 for print: log (b), its parts, read from the bottom up ----------
# Grey: the C lines and the statistics; black: the walk, the stopping instruction in bold; the reason in bold, in the accent, with a bar.
m = 'ah-5-2p'
b = [markers(m)]
rows = [
    ('c', '; if (curr_val) { @ past.bpf.c:18', 'the C line, from the object\'s BTF'),
    ('w', '9: (15) if r0 == 0x0 goto pc+2 ; R0=map_value(…,vs=8)', 'an instruction, then what it changed'),
    ('c', '; __atomic_fetch_add(…, *(curr_val + 1), …); @ past.bpf.c:19', 'the next C line'),
    ('s', '10: (79) r1 = *(u64 *)(r0 +8)', 'where the walk stopped'),
    ('r', 'invalid access to map value, value_size=8 off=8 size=8', 'the reason: which rule failed,'),
    ('r', 'R0 min value is outside of the allowed memory range', 'and for which register'),
    ('c', 'processed 10 insns (limit 1000000) … total_states 1 …', 'statistics, printed even on rejection'),
]
LX, RH, Y0 = 46, 30, 8
for i, (k, ln, lab) in enumerate(rows):
    yc = Y0 + i * RH + RH / 2
    fill = {'c': GREY, 'w': INK, 's': INK, 'r': P2}[k]
    wt = '700' if k in 'sr' else None
    b.append(t(LX, yc, ln, size=14.5, anchor='start', fam=UMONO, fill=fill, weight=wt).replace('<text ', '<text xml:space="preserve" '))
    b.append(t(676, yc, lab, size=14.5, anchor='end', italic=True, fill=fill, weight='600' if k == 'r' else None))
    if i:
        b.append(f'<line x1="{LX}" y1="{Y0 + i * RH}" x2="676" y2="{Y0 + i * RH}" stroke="#D3D6D9" stroke-width="0.8"/>')
# the reason: a heavy bar beside its two lines
b.append(f'<line x1="{LX - 7}" y1="{Y0 + 4 * RH + 4}" x2="{LX - 7}" y2="{Y0 + 6 * RH - 4}" stroke="{P2}" stroke-width="3.5"/>')
# read upward
top, bot = Y0 + 6, Y0 + 7 * RH - 6
b.append(line([(26, bot), (26, top)], m + '-k', width=2))
b.append(f'<text x="12" y="{(top + bot) / 2}" font-family="{SANS}" font-size="14.5" font-style="italic" fill="{INK}" text-anchor="middle" '
         f'dominant-baseline="central" transform="rotate(-90 12 {(top + bot) / 2})">read from the bottom up</text>')
figs['parts_print'] = svg(Y0 + 7 * RH + 8, 'The parts of one rejection log',
                          'Log (b), seven lines, each named at the right, read from the bottom up: the statistics line, printed even on '
                          'rejection; the reason in two lines, which rule failed and for which register; the instruction where the walk '
                          'stopped, slot 10; the next C line; slot 9, an instruction, then what it changed; the C line, from the object\'s BTF.', b, m)
save('ch05-parts', figs['parts_print'])
print('ch05 figures ok')
