# Chapter "struct_ops through sched_ext" (src/schedext.html): its two drawn figures.
# Drawn to the print rules in NOTES.md "Figure rules": 680 units = 127 mm, words 14.5 units or more,
# Open Sans Condensed for words, Ubuntu Mono for code names, black and grey with one accent.
# Facts: kernel/bpf/bpf_struct_ops.c and kernel/sched/ext/ext.c in v7.2; addresses, sizes and program ids
# from book/labs/schedext-root.sh step 1 (kernel 7.2.15, VM, 13 November 2026).
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


def rect(x, y, w, h, l1, l2=None, stroke=INK, sw=1.3, fill_text=INK, mono=True, size1=16):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#FFFFFF" stroke="{stroke}" stroke-width="{sw}"/>'
    fam = UMONO if mono else SANS
    if l2 is None:
        return out + t(x + w / 2, y + h / 2, l1, size=size1, fam=fam, fill=fill_text)
    return (out + t(x + w / 2, y + h / 2 - 10, l1, size=size1, fam=fam, weight='700', fill=fill_text)
            + t(x + w / 2, y + h / 2 + 11, l2, size=15, fill=GREY))


def diamond(cx, cy, hw, hh, l1, l2):
    return (f'<polygon points="{cx - hw},{cy} {cx},{cy - hh} {cx + hw},{cy} {cx},{cy + hh}" fill="#FFFFFF" '
            f'stroke="{INK}" stroke-width="1.3"/>' + t(cx, cy - 10, l1, size=15.5) + t(cx, cy + 10, l2, size=15.5))


def line(pts, mid, color=INK, width=1.8, dash=None, arrow=True):
    d = ' '.join(f'{"M" if i == 0 else "L"}{x},{y}' for i, (x, y) in enumerate(pts))
    da = f' stroke-dasharray="{dash}"' if dash else ''
    me = f' marker-end="url(#{mid})"' if arrow else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da}{me}/>'


# ---------- the struct_ops table of scx_simple and what each filled member points at ----------
# Claim: the kernel keeps its own copy of struct sched_ext_ops inside the struct_ops map; each member the
# scheduler filled points at a trampoline the kernel wrote, and the trampoline calls the program. A call
# from the scheduler core, ops.enqueue here, is an indirect call through that copy, as for a built-in table.
m = 'ah-scx-table'
b = []
XA, WA = 34, 196          # the kernel's copy of the table
XB, WB = 286, 150         # trampolines
XC, WC = 492, 182         # programs
b.append(t(XA + WA / 2, 84, 'kernel copy of sched_ext_ops', size=15.5, weight='700'))
b.append(t(XA + WA / 2, 102, 'in the struct_ops map simple_ops', size=14.5, fill=GREY))
b.append(t(XB + WB / 2, 84, 'trampolines', size=15.5, weight='700'))
b.append(t(XB + WB / 2, 102, 'one 4 KiB page', size=14.5, fill=GREY))
b.append(t(XC + WC / 2, 84, 'JIT-compiled programs', size=15.5, weight='700'))
b.append(t(XC + WC / 2, 102, 'jited size', size=14.5, fill=GREY))
rows = [('select_cpu', 'simple_select_cpu', '240 B'), ('enqueue', 'simple_enqueue', '256 B'),
        ('dequeue', None, None), ('dispatch', 'simple_dispatch', '52 B'), ('running', 'simple_running', '86 B'),
        ('stopping', 'simple_stopping', '133 B'), ('enable', 'simple_enable', '66 B'),
        ('init', 'simple_init', '122 B'), ('exit', 'simple_exit', '201 B')]
Y0, RH = 120, 34
for i, (mem, prog, size) in enumerate(rows):
    y = Y0 + i * RH
    acc = mem == 'enqueue'
    col, sw, lw = (ACC, 2.6, 3) if acc else (INK, 1.3, 1.8)
    b.append(f'<rect x="{XA}" y="{y}" width="{WA}" height="{RH - 6}" rx="4" fill="#FFFFFF" stroke="{col}" stroke-width="{sw}"/>')
    b.append(t(XA + 10, y + (RH - 6) / 2, mem, size=16, anchor='start', fam=UMONO, fill=col,
               weight='700' if acc else None))
    if prog is None:
        b.append(t(XA + WA - 10, y + (RH - 6) / 2, 'NULL', size=16, anchor='end', fam=UMONO, fill=GREY))
        b.append(t(XB, y + (RH - 6) / 2, 'no program: the kernel does without', size=14.5, anchor='start',
                   fill=GREY, italic=True))
        continue
    b.append(f'<rect x="{XB}" y="{y}" width="{WB}" height="{RH - 6}" rx="4" fill="#FFFFFF" stroke="{col}" stroke-width="{sw}"/>')
    b.append(t(XB + WB / 2, y + (RH - 6) / 2, 'bpf__…_' + mem, size=14.5, fam=UMONO, fill=col))
    b.append(f'<rect x="{XC}" y="{y}" width="{WC}" height="{RH - 6}" rx="4" fill="#FFFFFF" stroke="{col}" stroke-width="{sw}"/>')
    b.append(t(XC + 8, y + (RH - 6) / 2, prog, size=15, anchor='start', fam=UMONO, fill=col))
    b.append(t(XC + WC - 8, y + (RH - 6) / 2, size, size=14.5, anchor='end', fill=GREY))
    b.append(line([(XA + WA, y + (RH - 6) / 2), (XB - 3, y + (RH - 6) / 2)], m, color=col, width=lw))
    b.append(line([(XB + WB, y + (RH - 6) / 2), (XC - 3, y + (RH - 6) / 2)], m, color=col, width=lw))
yN = Y0 + len(rows) * RH
b.append(f'<rect x="{XA}" y="{yN}" width="{WA}" height="{RH - 6}" rx="4" fill="#FFFFFF" stroke="{INK}" stroke-width="1.3"/>')
b.append(t(XA + WA / 2, yN + (RH - 6) / 2, '28 more pointers: NULL', size=15, fill=GREY))
yD = yN + RH
b.append(f'<rect x="{XA}" y="{yD}" width="{WA}" height="{2 * RH - 6}" rx="4" fill="#FFFFFF" stroke="{INK}" stroke-width="1.3"/>')
b.append(t(XA + 10, yD + 15, 'name = "simple"', size=15.5, anchor='start', fam=UMONO))
b.append(t(XA + 10, yD + 43, 'timeout_ms = 0', size=15.5, anchor='start', fam=UMONO))
b.append(t(XB, yD + 15, 'data members are copied as they are', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(XB, yD + 43, 'timeout 0: the watchdog waits 30 s', size=14.5, anchor='start', fill=GREY, italic=True))
# the caller, above the table, and its route down the left edge into the enqueue row
b.append(rect(XA - 20, 8, 330, 50, 'sch->ops.enqueue(p, enq_flags)', 'do_enqueue_task() in kernel/sched/ext/ext.c',
              stroke=ACC, sw=2.6, fill_text=ACC))
ye = Y0 + RH + (RH - 6) / 2
b.append(line([(XA - 6, 58), (XA - 6, 70), (16, 70), (16, ye), (XA - 3, ye)], m, color=ACC, width=3))
b.append(t(372, 33, 'an indirect call, as through', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(372, 51, 'the table of a built-in class', size=14.5, anchor='start', fill=GREY, italic=True))
H = yD + 2 * RH + 4
fig = svg(H, 'The struct_ops table of scx_simple',
          'Box diagram. Left: the kernel copy of struct sched_ext_ops inside the struct_ops map simple_ops, with '
          'members select_cpu, enqueue, dequeue (NULL), dispatch, running, stopping, enable, init and exit, then 28 '
          'more NULL pointers and the data members name, set to simple, and timeout_ms, set to 0. Each filled member points at a '
          'trampoline in one 4 KiB page, and each trampoline calls its JIT-compiled program, from simple_select_cpu '
          '(240 bytes) to simple_exit (201 bytes). At the top the scheduler core calls sch->ops.enqueue, which '
          'reaches simple_enqueue through the enqueue member and its trampoline.', b, m)
save('schedext-table', fig)


# ---------- a task's path through scx_simple's callbacks and dispatch queues ----------
# Claim: a waking task meets ops.select_cpu first; if an idle CPU was found it goes straight to that CPU's
# local DSQ and ops.enqueue is skipped, otherwise ops.enqueue puts it in SHARED_DSQ and it waits until a CPU
# with nothing in its local or the global DSQ calls ops.dispatch, which moves it over. The shortcut is the accent.
m = 'ah-scx-path'
b = []
cx, LX, LW = 185, 30, 310
RX, RW = 410, 260
b.append(rect(LX, 10, LW, 52, 'try_to_wake_up()', 'a task becomes runnable'))
b.append(line([(cx, 62), (cx, 86)], m))
b.append(rect(LX, 88, LW, 52, 'ops.select_cpu()', 'simple_select_cpu: look for an idle CPU'))
b.append(line([(cx, 140), (cx, 166)], m))
b.append(diamond(cx, 222, 140, 54, 'an idle CPU', 'was found?'))
b.append(line([(cx + 140, 222), (RX - 3, 222)], m, color=ACC, width=3))
b.append(t(cx + 150, 208, 'yes', size=15.5, anchor='start', weight='700', fill=ACC))
b.append(rect(RX, 194, RW, 56, 'scx_bpf_dsq_insert()', 'into that CPU’s local DSQ', stroke=ACC, sw=2.6, fill_text=ACC))
b.append(t(530, 270, 'ops.enqueue() is skipped', size=14.5, anchor='end', fill=GREY, italic=True))
b.append(line([(540, 250), (540, 412), (LX + LW + 3, 412)], m, color=ACC, width=3))
b.append(t(cx - 12, 290, 'no', size=15.5, anchor='end', weight='700'))
b.append(line([(cx, 276), (cx, 304)], m))
b.append(rect(LX, 306, LW, 52, 'ops.enqueue()', 'simple_enqueue: into SHARED_DSQ, vtime order'))
b.append(t(LX + LW + 10, 332, 'waits there', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(line([(cx, 358), (cx, 384)], m))
b.append(rect(LX, 386, LW, 52, 'pick_task_scx()', 'a CPU looks for its next task'))
b.append(line([(cx, 438), (cx, 464)], m))
b.append(diamond(cx, 520, 140, 54, 'a task in its local', 'or the global DSQ?'))
b.append(line([(cx + 140, 520), (RX - 3, 520)], m))
b.append(t(cx + 150, 506, 'yes', size=15.5, anchor='start', weight='700'))
b.append(rect(RX, 492, RW, 56, 'ops.running()', 'the first one runs, up to 20 ms'))
b.append(t(cx - 12, 588, 'no', size=15.5, anchor='end', weight='700'))
b.append(line([(cx, 574), (cx, 602)], m))
b.append(rect(LX, 604, LW, 52, 'ops.dispatch()', 'simple_dispatch: move one from SHARED_DSQ'))
b.append(line([(LX, 630), (14, 630), (14, 520), (cx - 140 - 3, 520)], m))
b.append(t(LX, 676, 'then look again, at most 32 rounds', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(line([(540, 548), (540, 578)], m))
b.append(rect(RX, 580, RW, 56, 'ops.stopping()', 'charges the time it used to vtime'))
b.append(t(RX, 654, 'still runnable: back to ops.enqueue()', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(RX, 672, 'asleep: done until the next wake-up', size=14.5, anchor='start', fill=GREY, italic=True))
# legend
b.append(line([(30, 712), (78, 712)], m, color=ACC, width=3, arrow=False))
b.append(t(88, 712, 'the shortcut when an idle CPU was found', size=14.5, anchor='start'))
b.append(line([(380, 712), (428, 712)], m, arrow=False))
b.append(t(438, 712, 'every other way through', size=14.5, anchor='start'))
fig = svg(730, 'A task through scx_simple',
          'Flowchart. A task becomes runnable in try_to_wake_up and ops.select_cpu looks for an idle CPU. If one was '
          'found, scx_bpf_dsq_insert puts the task in that CPU local dispatch queue and ops.enqueue is skipped. '
          'Otherwise ops.enqueue puts it in SHARED_DSQ in virtual-time order, where it waits. When a CPU looks for '
          'its next task in pick_task_scx, it runs the first task of its local or the global queue, calling '
          'ops.running; if both are empty it calls ops.dispatch, which moves one task from SHARED_DSQ, and looks '
          'again, at most 32 rounds. ops.stopping charges the time used; a task still runnable goes back to '
          'ops.enqueue.', b, m)
save('schedext-path', fig)
