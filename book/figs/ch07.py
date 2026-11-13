# Figures for chapter 7, "The JIT: bytecode becomes x86" (spec §5.3: 680 wide, palette tokens).
# Run from dossier/:  python3 -I figs/ch07.py   ->  figs/out/ch07-*.svg
# Every instruction and byte below is from the learner's write counter loaded on kernel 7.2.15
# (bpftool prog dump xlated / jited opcodes, in a virtme-ng VM, 12 November 2026).
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

def code(x, y, t, col=None, size=11, weight=None, anchor='start'):
    return tx(x, y, t, size=size, anchor=anchor, mono=True, col=col, weight=weight)

def panel(x, y, w, h, col, sw=0.8):
    l, d, _ = C[col]
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{l}" stroke="{d}" stroke-width="{sw}"/>'

# ---------------- Figure 7.3: four of the counter's instructions, translated ----------------
m = 'ah-7-3'
b = []
L, M, R = 40, 232, 452          # left edges of the three columns
LW, MW, RW = 168, 196, 188
heads = [(L, LW, 'the object', 'llvm-objdump, from clang'), (M, MW, 'after the rewrites', 'bpftool prog dump xlated'),
         (R, RW, 'x86', 'bpftool prog dump jited')]
for x, w, t1, t2 in heads:
    b.append(tx(x + w / 2, 16, t1, size=13, weight='600', col='teal'))
    b.append(tx(x + w / 2, 32, t2, size=10, mono=True))

rows = [  # (slot label, height, left lines, middle lines, right lines)
    ('slot 4', 28, [('r2 = r10', None)], [('r2 = r10', None)],
     [('movq %rbp, %rsi', None), ('48 89 ee', 'gray')]),
    ('slot 5', 28, [('r2 += -0x4', None)], [('r2 += -4', None)],
     [('addq $-4, %rsi', None), ('48 83 c6 fc', 'gray')]),
    ('slot 6', 40, [('r1 = 0x0 ll', None), ('relocation: write_counts', 'gray')], [('r1 = map[id:2]', None)],
     [('movabsq $…, %rdi', None), ('the map\'s address', 'gray')]),
    ('slot 8', 72, [('call 0x1', None)],
     [('call __htab_map_lookup_elem', None), ('if r0 == 0x0 goto pc+1', 'amber'), ('r0 += 56', 'amber')],
     [('callq …', None), ('testq %rax, %rax', 'amber'), ('je …', 'amber'), ('addq $56, %rax', 'amber')]),
]
y = 46
for slot, h, left, mid, right in rows:
    b.append(panel(L, y, LW, h, 'gray', 0.6))
    b.append(panel(M, y, MW, h, 'teal', 0.6))
    b.append(panel(R, y, RW, h, 'teal', 0.6))
    b.append(tx(L + LW - 6, y + 11, slot, size=9.5, anchor='end', col='gray', italic=True))
    for col_x, lines, step in [(L + 10, left, 16), (M + 10, mid, 16), (R + 10, right, 16)]:
        n = len(lines)
        top = y + h / 2 - (n - 1) * step / 2
        if col_x == R + 10 and n == 2 and lines[1][0][:2] in ('48', 'e8'):   # mnemonic and its bytes side by side
            b.append(code(col_x, y + h / 2, lines[0][0]))
            b.append(code(R + RW - 8, y + h / 2, lines[1][0], col='gray', size=10, anchor='end'))
            continue
        for i, (t, c) in enumerate(lines):
            b.append(code(col_x, top + i * step, t, col=c, size=10 if c == 'gray' else 11,
                          weight='600' if c == 'amber' else None))
    b.append(arrow(L + LW + 2, y + h / 2, M - 4, y + h / 2, m))
    b.append(arrow(M + MW + 2, y + h / 2, R - 4, y + h / 2, m))
    y += h + 8
b.append(tx(M + 10, y + 6, 'amber: added by the kernel', size=11, col='amber', italic=True, anchor='start'))
b.append(tx(640, y + 6, 'r0=rax  r1=rdi  r2=rsi  r10=rbp', size=10, mono=True, anchor='end'))
yb = y + 22
b.append(f'<rect x="40" y="{yb}" width="600" height="46" rx="6" fill="{C["gray"][0]}" stroke="{C["gray"][1]}" stroke-width="0.75"/>')
b.append(tx(340, yb + 15, '27 slots, 216 bytes  →  29 slots, 232 bytes  →  152 bytes of x86', size=12, col='gray', mono=True))
b.append(tx(340, yb + 32, 'Each bytecode register is one x86 register, so most instructions become one x86 instruction.', size=12, col='gray'))
fig3 = svg(yb + 56, 'Three instructions of the write counter, from bytecode to x86',
           'Three columns: the compiled bytecode, the bytecode after the kernel rewrites the map lookup, and the x86 the JIT wrote, row by row', b, m)

# ---------------- Figure 7.4: a tail call on x86 ----------------
m = 'ah-7-4'
b = []
# program A
b.append(panel(40, 40, 200, 156, 'teal'))
b.append(tx(140, 56, 'program A', size=13, weight='600', col='teal'))
b.append(code(52, 82, '…', col='teal'))
b.append(f'<rect x="48" y="94" width="184" height="44" rx="4" fill="#FFFFFF" stroke="{C["teal"][1]}" stroke-width="1.4"/>')
b.append(code(56, 108, 'bpf_tail_call(ctx,', col='teal', weight='600'))
b.append(code(56, 126, '  &progs, 2)', col='teal', weight='600'))
b.append(f'<rect x="48" y="160" width="184" height="26" rx="4" fill="#FFFFFF" stroke="{C["gray"][1]}" stroke-width="0.8"/>')
b.append(tx(140, 173, 'A\'s next instruction', size=11, col='gray'))
# the program array
b.append(tx(560, 16, 'progs: a program array', size=11, col='coral', weight='600'))
for i, t in enumerate(['–', 'C', 'B', '–']):
    x = 480 + i * 40
    b.append(f'<rect x="{x}" y="26" width="38" height="28" rx="4" fill="{C["coral"][0]}" stroke="{C["coral"][1]}" stroke-width="{1.6 if i == 2 else 0.8}"/>')
    b.append(tx(x + 19, 34, str(i), size=9, col='coral'))
    b.append(tx(x + 19, 46, t, size=11, mono=True, col='coral', weight='600'))
# the three checks
checks = ['is 2 below max_entries?', 'fewer than 33 tail calls?', 'does slot 2 hold a program?']
for i, t in enumerate(checks):
    y = 70 + i * 52
    b.append(panel(282, y, 176, 32, 'amber'))
    b.append(tx(370, y + 16, t, size=11, col='amber', weight='600'))
    b.append(f'<path d="M282,{y + 16} H262 V173 H236" fill="none" stroke="{LINE}" stroke-width="1.1" marker-end="url(#{m})"/>' if i == 0 else
             f'<path d="M282,{y + 16} H262" fill="none" stroke="{LINE}" stroke-width="1.1"/>')
    if i < 2:
        b.append(arrow(370, y + 33, 370, y + 50, m))
        b.append(tx(380, y + 42, 'yes', size=10, anchor='start'))
b.append(tx(258, 120, 'no', size=10, anchor='end'))
b.append(arrow(240, 108, 280, 86, m, width=2.4, color=C['teal'][1]))
# after the last check: count + 1, unwind, jump
b.append(arrow(370, 207, 370, 222, m))
b.append(tx(380, 214, 'yes', size=10, anchor='start'))
b.append(tx(370, 234, 'count + 1, free A\'s registers', size=11, col='teal'))
b.append(f'<path d="M458,234 H500 V200" fill="none" stroke="{C["teal"][1]}" stroke-width="2.4" marker-end="url(#{m})"/>')
# program B
b.append(panel(480, 70, 160, 126, 'teal'))
b.append(tx(560, 86, 'program B', size=13, weight='600', col='teal'))
for i, t in enumerate(['endbr64', '5-byte nop, 3-byte nop', 'push %rbp', 'mov %rsp, %rbp']):
    b.append(code(492, 104 + i * 14, t, col='gray', size=10))
b.append(f'<path d="M600,98 h6 v52 h-6" fill="none" stroke="{C["gray"][1]}" stroke-width="0.9"/>')
b.append(tx(612, 124, 'skipped', size=10, anchor='start', col='gray', italic=True))
b.append(code(492, 166, 'endbr64', col='teal', weight='600'))
b.append(code(492, 182, 'B\'s own code', col='teal'))
b.append(tx(636, 166, '← lands here', size=10, anchor='end', col='teal', italic=True))
b.append(bar(256, 34, 'A never gets control back: B runs in A\'s stack frame. After 33 jumps the next one falls through.'))
fig4 = svg(300, 'A tail call on x86',
           'Program A calls bpf_tail_call; three checks decide between falling through to A\'s next instruction and jumping into program B past its first instructions', b, m)

save('ch07-translate', fig3)
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

# ---------- Figure 7.4 for print: a tail call on x86, as a flowchart ----------
# The checks are diamonds; the route of a tail call that is taken is thick, in the accent; a failed check is a thin black exit.
m = 'ah-7-4p'
b = [markers(m).replace('</defs>', f'<marker id="{m}-t" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4.6" markerHeight="4.6" '
                                    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{P2}"/></marker></defs>')]
TH = 2.8
DX, DW, DH = 160, 130, 27              # the checks: centre x, half-width, half-height
b += [rect(30, 8, 260, 58), t(DX, 25, 'program A', size=16, weight='700'),
      t(DX, 47, 'bpf_tail_call(ctx, &progs, 2)', size=15, fam=UMONO, weight='700')]
checks = [(114, [('is 2 below ', 's'), ('max_entries', 'm'), ('?', 's')]),
          (190, [('fewer than 33 tail calls?', 's')]),
          (266, [('does slot 2 hold a program?', 's')])]
b.append(line([(DX, 66), (DX, 114 - DH - 2)], m + '-t', color=P2, width=TH))
for i, (yc, parts) in enumerate(checks):
    b.append(f'<polygon points="{DX - DW},{yc} {DX},{yc - DH} {DX + DW},{yc} {DX},{yc + DH}" fill="#FFFFFF" stroke="{INK}" stroke-width="1.3"/>')
    b.append(tm(DX, yc, parts, size=15))
    nxt = checks[i + 1][0] - DH - 2 if i < 2 else 344
    b += [line([(DX, yc + DH), (DX, nxt)], m + '-t', color=P2, width=TH), t(DX + 10, yc + DH + 11, 'yes', size=15, anchor='start', weight='700', fill=P2)]
    b += [line([(DX + DW, yc), (318, yc)], width=1.5), t(DX + DW + 6, yc - 12, 'no', size=15, anchor='start', weight='700')]
b += [line([(318, 114), (318, 266)], width=1.5), line([(318, 190), (344, 190)], m + '-k', width=1.5),
      rect(346, 170, 130, 40), t(411, 190, "A's next instruction", size=15)]
# the program array
b.append(tm(560, 16, [('progs', 'm'), (': a program array', 's')], size=15))
for i, nm in enumerate(['–', 'C', 'B', '–']):
    x = 470 + i * 48
    hot = i == 2
    b += [t(x + 22, 40, str(i), size=14.5, fam=UMONO, fill=GREY),
          f'<rect x="{x}" y="52" width="44" height="32" rx="4" fill="#FFFFFF" stroke="{P2 if hot else INK}" stroke-width="{2.4 if hot else 1.2}"/>',
          t(x + 22, 68, nm, size=16, fam=UMONO, weight='700', fill=P2 if hot else INK)]
# the last step and the jump
b += [rect(30, 344, 260, 44, sw=1.6), t(DX, 366, "count + 1, free A's registers", size=15)]
b += [line([(290, 366), (398, 366)], m + '-t', color=P2, width=TH), t(344, 354, 'jump', size=15, weight='700', fill=P2)]
# program B
b += [rect(400, 234, 276, 172), t(538, 252, 'program B', size=16, weight='700')]
for k, (s_, fam) in enumerate([('endbr64', UMONO), ('5-byte nop, 3-byte nop', SANS), ('push %rbp', UMONO), ('mov %rsp, %rbp', UMONO)]):
    b.append(t(416, 276 + k * 19, s_, size=14.5 if fam == SANS else 15, anchor='start', fam=fam, fill=GREY))
b += [f'<path d="M590,268 h7 v65 h-7" fill="none" stroke="{GREY}" stroke-width="1.2"/>', t(605, 300, 'skipped', size=14.5, anchor='start', italic=True, fill=GREY),
      t(416, 366, 'endbr64', size=15, anchor='start', fam=UMONO, weight='700', fill=P2), t(486, 366, 'lands here', size=14.5, anchor='start', italic=True, fill=P2),
      t(416, 388, "B's own code", size=15, anchor='start')]
# legend
b += [line([(30, 424), (72, 424)], color=P2, width=TH), t(80, 424, 'the tail call taken', size=14.5, anchor='start'),
      line([(230, 424), (272, 424)], width=1.5), t(280, 424, 'a check fails', size=14.5, anchor='start')]
fig74p = svg(440, 'A tail call on x86',
             'Program A calls bpf_tail_call(ctx, &progs, 2). Three checks follow: is 2 below max_entries, fewer than 33 tail calls, '
             'does slot 2 hold a program; a no to any goes on at A\'s next instruction. With three yeses the count goes up by one, '
             'A\'s registers are freed and the code jumps into program B, slot 2 of the program array progs, past B\'s endbr64, '
             'nops, push %rbp and mov %rsp, %rbp, landing on a second endbr64 before B\'s own code.', b, m)
save('ch07-tailcall', fig74p)
print('ch07 figures ok')
