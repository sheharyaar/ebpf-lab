import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *

figs = {}

def tx(x, y, t, size=11, col=None, anchor='middle', mono=False, weight=None):
    return text(x, y, t, size=size, col=col, anchor=anchor, mono=mono, weight=weight)

# ---------- verifier map, v7.2 ----------
m = 'ah-10-2'
b = []
b.append(box(190, 8, 300, 44, 'gray', 'bpf_check()  ·  verifier.c', 'runs once each time a program is loaded', mono1=True, size1=12))
b.append(arrow(340, 54, 340, 70, m))
# phase 1
b.append(box(40, 72, 600, 44, 'gray'))
b.append(tx(60, 87, '1 · check the shape', size=12, col='gray', anchor='start', weight='600'))
b.append(tx(60, 104, 'jumps in range · no dead code · loops found', size=11, col='gray', anchor='start'))
b.append(tx(452, 94, 'bpf_check_cfg()', size=12, col='gray', anchor='middle', mono=True, weight='600'))
b.append(tx(620, 94, 'cfg.c', size=11, col='gray', anchor='end', mono=True))
b.append(arrow(340, 118, 340, 132, m))
# phase 2 container
b.append(f'<rect x="40" y="134" width="600" height="212" rx="6" fill="{C["teal"][0]}" stroke="{C["teal"][1]}" stroke-width="1"/>')
b.append(tx(60, 150, '2 · walk every path', size=12, col='teal', anchor='start', weight='600'))
b.append(tx(620, 150, 'do_check()  ·  verifier.c', size=11, col='teal', anchor='end', mono=True))
b.append(box(150, 164, 280, 40, 'teal', 'do_check_insn()', 'picks a checker by kind of instruction', mono1=True, size1=12))
b.append(box(450, 164, 176, 40, 'gray', 'bpf_is_state_visited()', 'states.c · seen this state?', mono1=True, size1=10))
names = ['check_alu_op', 'check_load_mem', 'check_helper_call', 'check_cond_jmp_op']
xs = [52, 196, 340, 484]
for x, n in zip(xs, names):
    col = 'amber' if n == 'check_load_mem' else 'teal'
    b.append(box(x, 232, 136, 34, col, n + '()', mono1=True, size1=11))
    b.append(arrow(290, 206, x + 68, 230, m, width=1.0))
b.append(box(150, 296, 144, 34, 'amber', 'check_mem_access()', mono1=True, size1=11, sw=1.4))
b.append(arrow(264, 268, 222, 294, m, width=2.2, color=C['amber'][1]))
b.append(box(320, 296, 150, 34, 'amber', 'line 6322  verbose()', mono1=True, size1=11, sw=1.4))
b.append(arrow(296, 313, 318, 313, m, width=2.2, color=C['amber'][1]))
b.append(box(496, 296, 130, 34, 'gray', 'reg_type_str()', mono1=True, size1=11))
b.append(tx(561, 338, 'log.c · words the type', size=10, col='gray'))
b.append(arrow(472, 313, 494, 313, m, width=1.0))
b.append(arrow(340, 348, 340, 362, m))
# phase 3
b.append(box(40, 364, 600, 44, 'gray'))
b.append(tx(60, 379, '3 · rewrite for running', size=12, col='gray', anchor='start', weight='600'))
b.append(tx(60, 396, 'context reads, helper calls, small fixes', size=11, col='gray', anchor='start'))
b.append(tx(452, 386, 'bpf_do_misc_fixups() …', size=12, col='gray', mono=True, weight='600'))
b.append(tx(620, 386, 'fixups.c', size=11, col='gray', anchor='end', mono=True))
b.append(bar(420, 32, 'Your rejection is one verbose() call inside the walk, in the checker for loads.'))
figs['map'] = svg(462, 'Where the verifier lives in Linux v7.2',
                  'The three phases of bpf_check with the file each lives in, and the path from do_check_insn down to the line that printed the rejection', b, m)

# ---------- three instructions, three checkers ----------
m = 'ah-10-3'
b = []
b.append(tx(115, 12, 'your instruction', size=11, col='gray'))
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
b.append(tx(290, y + 60, 'exactly a map value?', size=11, col='teal'))
b.append(box(390, y, 250, 38, 'teal', 'with your test: yes · bounds checked', size1=11))
b.append(box(390, y + 46, 250, 38, 'coral', 'without it: no · line 6322 · rejected', size1=11, sw=1.4))
b.append(arrow(192, y + 42, 203, y + 42, m, width=1.0))
b.append(arrow(377, y + 30, 388, y + 19, m, width=1.0))
b.append(arrow(377, y + 54, 388, y + 65, m, width=1.6, color=C['coral'][1]))
b.append(bar(266, 32, 'Your test of r0 is what turns "map value, maybe NULL" into "map value".'))
figs['three'] = svg(308, 'Three of your instructions and the checkers that see them',
                    'The call, the test of r0 and the load, each with the verifier function that checks it and what it records about r0', b, m)


save('ch10-map', figs['map'])
save('ch10-three', figs['three'])
print('ch10 figures ok')
