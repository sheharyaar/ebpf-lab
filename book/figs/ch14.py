# Figures for chapter 14, redrawn for print (figure rules in NOTES.md): 680 units = 127 mm,
# words 14.5 units or more, node titles 16, black and grey with the one accent.
# The screen versions are kept in figs/pre-print/ch14.py.
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

GREY_FILL = '#E4E6E8'

# ---------- Figure 14.1: three paths from write() to the program's first instruction ----------
# Frames from the stacks in /tmp/book-labs/ch14/stack-{tp,kp,fe}.txt (labs/ch14-root.sh, step 8), glue from v7.2 source.
# Each column is read top to bottom. Code that attaching wrote or redirected has a heavy outline in the accent;
# the program is the grey box.
m = 'ah-14-1p'
b = [markers(m)]
CW, GAP, X0 = 216, 10, 6
cols = [X0, X0 + CW + GAP, X0 + 2 * (CW + GAP)]
heads = [('tracepoint', 'syscalls/sys_enter_write', '+127 ns per write'),
         ('kprobe at the entry', 'kprobe/vfs_write', '+114 ns per write'),
         ('fentry', 'fentry/vfs_write', '+57 ns per write')]
for x, (t1, t2, t3) in zip(cols, heads):
    cx = x + CW / 2
    b += [t(cx, 14, t1, size=16, weight='700'), t(cx, 32, t2, size=14.5, fam=UMONO, fill=GREY), t(cx, 50, t3, size=15, weight='700')]
YS = 64
b += [rect(X0, YS, 3 * CW + 2 * GAP, 30, sw=1.2),
      tm(340, YS + 15, [('entry_SYSCALL_64', 'm'), (' → ', 's'), ('do_syscall_64()', 'm'), (': the ', 's'), ('write()', 'm'), (' call enters the kernel', 's')], size=14.5)]
# each step: (kind, title parts, detail lines); kind 'a' = written or redirected by attaching, 'p' = the program
M, S_ = 'm', 's'
paths = [
    [('', [('syscall_trace_enter()', M)], [[('inlined; tests a work flag that', S_)], [('attaching set on every thread', S_)]]),
     ('a', [('trace_syscall_enter()', M)], [[('a static key, now a jump, then a', S_)], [('static call aimed at the probe', S_)]]),
     ('', [('perf_syscall_enter()', M)], [[('is write’s bit set in the bitmap?', S_)], [('yes: number 1', S_)]]),
     ('', [('perf_call_bpf_enter()', M)], [[('builds the record on its own stack:', S_)], [('a regs pointer, the number, arguments', S_)]]),
     ('', [('trace_call_bpf_faultable()', M)], [[('recursion check for this program;', S_)], [('preemptible, migration off', S_)]]),
     ('p', [('count_writes', M)], [[('r1 = rdi = the record', S_)]])],
    [('', [('ksys_write()', M), (' → ', S_), ('vfs_write()', M)], [[('four bytes of no-op, then', S_)], [('the five-byte ftrace slot', S_)]]),
     ('a', [('vfs_write+4', M), (': call', S_)], [[('the slot was a no-op; now it calls', S_)], [('an ftrace trampoline for kprobes', S_)]]),
     ('a', [('ftrace trampoline', S_)], [[('saves every register as a', S_)], [('struct pt_regs', M), (' on the stack', S_)]]),
     ('', [('kprobe_ftrace_handler()', M)], [[('preemption off; finds the kprobe', S_)], [('by address, marks it running', S_)]]),
     ('', [('trace_call_bpf()', M)], [[('via ', S_), ('kprobe_perf_func()', M), ('; one', S_)], [('bpf_prog_active', M), (' counter per CPU', S_)]]),
     ('p', [('count_writes', M)], [[('r1 = rdi = the saved ', S_), ('pt_regs', M)]])],
    [('', [('ksys_write()', M), (' → ', S_), ('vfs_write()', M)], [[('four bytes of no-op, then', S_)], [('the five-byte ftrace slot', S_)]]),
     ('a', [('vfs_write+4', M), (': call', S_)], [[('the slot now calls the BPF', S_)], [('trampoline directly', S_)]]),
     ('a', [('bpf_trampoline_6442594783', M)], [[('132 bytes the JIT wrote: stores', S_)], [('rdi, rsi, rdx, rcx on its stack', S_)]]),
     ('', [('__bpf_prog_enter_recur()', M)], [[('recursion check for this program;', S_)], [('preemptible, migration off', S_)]]),
     ('p', [('count_writes', M)], [[('r1 = rdi = rbp − 0x20,', S_)], [('the four saved arguments', S_)]]),
     ('', [('__bpf_prog_exit_recur()', M)], [[('then the trampoline returns', S_)], [('and ', S_), ('vfs_write+9', M), (' runs', S_)]])],
]
Y0, G = YS + 30 + 14, 14
ends = []
for x, rows in zip(cols, paths):
    cx = x + CW / 2
    b.append(line([(cx, YS + 30), (cx, Y0 - 1)], m + '-k', width=1.5))
    y = Y0
    for k, (kind, title, lines) in enumerate(rows):
        h = 27 + 18 * len(lines)
        b.append(rect(x, y, CW, h, stroke=P2 if kind == 'a' else INK, sw=2.6 if kind == 'a' else 1.2, fill=GREY_FILL if kind == 'p' else '#FFFFFF'))
        b.append(tm(x + 9, y + 14, title, size=15, anchor='start', weight='700', fill=P2 if kind == 'a' else INK))
        for j, parts in enumerate(lines):
            b.append(tm(x + 9, y + 33 + 18 * j, parts, size=14.5, anchor='start'))
        y += h
        if k < len(rows) - 1:
            b.append(line([(cx, y), (cx, y + G - 1)], m + '-k', width=1.5))
            y += G
    ends.append(y)
LY = max(ends) + 22
b += [rect(X0, LY - 10, 36, 20, stroke=P2, sw=2.6), t(X0 + 46, LY, 'written or redirected by attaching', size=14.5, anchor='start', fill=P2, weight='700'),
      rect(300, LY - 10, 36, 20, sw=1.2, fill=GREY_FILL), t(346, LY, 'the program', size=14.5, anchor='start'),
      line([(450, LY), (486, LY)], m + '-k', width=1.5), t(496, LY, 'runs next', size=14.5, anchor='start')]
H141 = LY + 16
fig141 = svg(H141, 'Three paths from the write() system call to the first instruction of the write counter',
             'Three columns after entry_SYSCALL_64 and do_syscall_64(). Tracepoint (syscalls/sys_enter_write, +127 ns per write): '
             'syscall_trace_enter(), trace_syscall_enter() (a static key, now a jump, then a static call aimed at the probe), '
             'perf_syscall_enter(), perf_call_bpf_enter(), trace_call_bpf_faultable(), count_writes with r1 the record. '
             'Kprobe at the entry (kprobe/vfs_write, +114 ns): ksys_write() and vfs_write(), the call at vfs_write+4 to an ftrace '
             'trampoline for kprobes, which saves struct pt_regs, kprobe_ftrace_handler(), trace_call_bpf(), count_writes with r1 the saved '
             'pt_regs. Fentry (fentry/vfs_write, +57 ns): ksys_write() and vfs_write(), the call at vfs_write+4 to the BPF trampoline '
             'bpf_trampoline_6442594783, 132 bytes, __bpf_prog_enter_recur(), count_writes with r1 = rbp - 0x20, __bpf_prog_exit_recur().', b, m)
save('ch14-paths', fig141)
print('ch14 figures ok')
