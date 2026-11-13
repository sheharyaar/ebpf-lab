# Figures for chapter 11, redrawn for print (figure rules in NOTES.md): 680 units = 127 mm,
# words 14.5 units or more, node titles 16, black and grey with the one accent.
# The screen versions are kept in figs/pre-print/ch11.py.
# Figure 11.2 (the steps of BPF_PROG_LOAD) is now an HTML table in src/ch11.html; figs/out/ch11-path.svg is no longer used.
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

# ---------- Figure 11.4: the teardown after SIGTERM, a timeline in three execution contexts ----------
# Time runs down the left (not to scale); columns are the contexts. What runs is a solid box; the two waits are
# dashed boxes in the accent; arrows hand the work to the next context.
m = 'ah-11-4p'
b = [markers(m)]
TX = 8
LANES = {'loader': (64, 236, 'the exiting loader'), 'rcu': (308, 160, 'RCU callback'), 'kw': (476, 196, 'kworkers')}
b.append(t(TX, 16, 'time', size=15, anchor='start', weight='700'))
for x, w, lab in LANES.values():
    b += [t(x + w / 2, 16, lab, size=15, weight='700'),
          f'<line x1="{x + w / 2}" y1="28" x2="{x + w / 2}" y2="__BOTTOM__" stroke="#C9CCCF" stroke-width="1" stroke-dasharray="2 4"/>']
def ev(lane, y, lines, wait=False, tl=None, tsize=15):
    """An event (solid box) or a wait (dashed accent box). lines: lists of (text, face) parts; the first line is the title."""
    x, w, _ = LANES[lane]
    h = 18 * len(lines) + 10
    out = [rect(x, y, w, h, stroke=P2 if wait else INK, sw=2 if wait else 1.2, dash='6 4' if wait else None)]
    for k, parts in enumerate(lines):
        out.append(tm(x + 8, y + 14 + 18 * k, parts, size=tsize if k == 0 else 14.5, anchor='start',
                      weight='700' if k == 0 else None, fill=P2 if wait and k == 0 else INK))
    if tl:
        out.append(t(TX, y + 14, tl, size=14.5, anchor='start', fam=UMONO, fill=GREY))
    return out, y + h
M, S = 'm', 's'
y = 30
o, y1 = ev('loader', y, [[('kill(SIGTERM)', M)], [('files close as the process exits', S)]], tl='0'); b += o; y = y1 + 10
o, y1 = ev('loader', y, [[('link fd: ', S), ('bpf_link_release()', M)], [('bpf_perf_link_release()', M), (': detach', S)]], tl='0.6 ms'); b += o; y = y1 + 10
o, y1 = ev('loader', y, [[('waits ≈ 25 ms', S)], [('perf_event_detach_bpf_prog()', M)], [('in ', S), ('synchronize_rcu_tasks_trace()', M)]], wait=True); b += o; y = y1 + 10
o, y1 = ev('loader', y, [[('program: 3 → 2, the perf event’s', S)], [('then 2 → 1, the link’s own', S)]], tl='25.7 ms'); b += o; y = y1 + 10
YP = y
o, y1 = ev('loader', y, [[('prog fd: 1 → 0, ID freed', S)], [('bpf_prog_put_deferred()', M), (':', S)], [('call_rcu()', M)]], tl='25.7 ms'); b += o
YPE = y1; y = y1 + 10
o, y1 = ev('loader', y, [[('map fds: ', S), ('bpf_map_release()', M)], [('write_counts', M), (' 2 → 1, ', S), ('.rodata', M), (' 2 → 1', S)]], tl='25.7 ms'); b += o
YME = y1; y = y1 + 20
# the grace period, from call_rcu() to the callback
o, yg = ev('rcu', YP, [[('RCU grace period', S)], [('≈ 9 ms: every CPU', S)], [('that might still run', S)], [('count_writes', M), (' has', S)],
                       [('passed a quiescent state', S)]], wait=True); b += o
b.append(line([(300, YP + 14), (306, YP + 14)], m + '-k', width=1.5))
y = max(y, yg + 20)
YR = y
o, yr1 = ev('rcu', y, [[('__bpf_prog_put_rcu()', M)], [('then ', S), ('bpf_prog_free()', M)]], tl='34.5 ms', tsize=14.5); b += o
o, yk1 = ev('kw', y, [[('bpf_prog_free_deferred()', M)], [('used_maps', M), (': 1 → 0 and 1 → 0', S)]]); b += o
b += [line([(388, yg), (388, YR - 2)], m + '-k', width=1.5), line([(468, YR + 14), (474, YR + 14)], m + '-k', width=1.5)]
y = yk1 + 12
o, yk2 = ev('kw', y, [[('bpf_map_free_deferred()', M)], [('htab_map_free()', M), (',', S)], [('array_map_free()', M)]], tl='34.6 ms'); b += o
b.append(line([(574, yk1), (574, y - 2)], m + '-k', width=1.5))
H114 = yk2 + 46
# legend, in the loader's column below its last event
LY = yk2 + 26
b += [rect(64, LY - 10, 36, 20, sw=1.2), t(110, LY, 'runs in this column', size=14.5, anchor='start'),
      rect(268, LY - 10, 36, 20, stroke=P2, sw=2, dash='6 4'), t(314, LY, 'a wait', size=14.5, anchor='start', fill=P2, weight='700'),
      line([(400, LY), (436, LY)], m + '-k', width=1.5), t(446, LY, 'hands on to another column', size=14.5, anchor='start')]
fig114 = svg(H114, 'What the kernel did when the write counter’s loader was killed',
             'A timeline in three columns: the exiting loader, the RCU callback and the kworkers. In the exiting loader: kill(SIGTERM) at 0; at 0.6 ms the link fd is released and '
             'bpf_perf_link_release() detaches; perf_event_detach_bpf_prog() waits about 25 ms in synchronize_rcu_tasks_trace(); at '
             '25.7 ms the program goes 3 to 2 (the perf event) and 2 to 1 (the link), the prog fd 1 to 0 with the ID freed and '
             'bpf_prog_put_deferred() calling call_rcu(), and the map fds are released (write_counts 2 to 1, .rodata 2 to 1). An RCU grace '
             'period of about 9 ms follows. At 34.5 ms the RCU callback runs __bpf_prog_put_rcu() then bpf_prog_free(), and a kworker '
             'runs bpf_prog_free_deferred(), used_maps 1 to 0 and 1 to 0; at 34.6 ms a kworker runs bpf_map_free_deferred(): '
             'htab_map_free(), array_map_free().', b, m)
fig114 = fig114.replace('__BOTTOM__', str(yk2))
save('ch11-teardown', fig114)
print('ch11 figures ok')
