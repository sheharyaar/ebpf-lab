# Figures for chapter 13, redrawn for print (figure rules in NOTES.md): 680 units = 127 mm,
# words 14.5 units or more, node titles 16, black and grey with the one accent.
# The screen versions are kept in figs/pre-print/ch13.py.
# Figure 13.2 (two helper calls, stage by stage) is now an HTML table in src/ch13.html; figs/out/ch13-path.svg is no longer used.
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

ACC_FILL, GREY_FILL = '#DCEFE8', '#E4E6E8'

# ---------- Figure 13.3: nanoseconds per operation, a bar chart ----------
# The accent marks the lookup with no call (accent fill, heavy outline, bold label).
m = 'ah-13-3p'
b = []
X0, S = 316, 7.0                # bar origin, units per nanosecond
data = [([('array lookup, inlined', 's')], [('7 instructions, no call', 's')], 0.50),
        ([('bpf_get_current_pid_tgid()', 'm')], [('a helper: one direct call', 's')], 4.148),
        ([('array lookup through a call', 's')], [('BPF_F_INNER_MAP', 'm'), (': ', 's'), ('array_map_lookup_elem()', 'm')], 4.89),
        ([('hash lookup, 8 keys stored', 's')], [('call ', 's'), ('__htab_map_lookup_elem()', 'm')], 13.92),
        ([('kfunc pair', 's')], [('bpf_task_from_pid()', 'm'), (' + ', 's'), ('bpf_task_release()', 'm')], 39.73)]
TOP, STEP, BH = 10, 48, 24
YAX = TOP + len(data) * STEP
for v in range(0, 41, 10):
    x = X0 + v * S
    b += [f'<line x1="{x}" y1="{TOP - 2}" x2="{x}" y2="{YAX}" stroke="#C9CCCF" stroke-width="1" stroke-dasharray="2 4"/>',
          t(x, YAX + 14, str(v), size=14.5, fam=UMONO, fill=GREY)]
b += [line([(X0, YAX), (X0 + 40 * S, YAX)], color=GREY, width=1), t(X0 + 20 * S, YAX + 36, 'nanoseconds per operation', size=14.5, fill=GREY)]
for k, (l1, l2, v) in enumerate(data):
    y = TOP + k * STEP + 6
    hot = k == 0
    b += [tm(X0 - 12, y + 3, l1, size=15, anchor='end', weight='700', fill=P2 if hot else INK),
          tm(X0 - 12, y + 22, l2, size=14.5, anchor='end', fill=GREY)]
    w = max(3.5, v * S)
    b += [f'<rect x="{X0}" y="{y}" width="{w:.1f}" height="{BH}" rx="2" fill="{ACC_FILL if hot else GREY_FILL}" '
          f'stroke="{P2 if hot else INK}" stroke-width="{2.4 if hot else 1.1}"/>',
          t(X0 + w + 8, y + BH / 2, f'{v:.1f} ns', size=15, anchor='start', fam=UMONO, weight='700', fill=P2 if hot else INK)]
H133 = YAX + 50
fig133 = svg(H133, 'Nanoseconds per operation for inlined and called lookups, a helper and a kfunc pair',
             'Horizontal bars, nanoseconds per operation: array lookup inlined (7 instructions, no call) 0.5; bpf_get_current_pid_tgid(), a helper, '
             'one direct call, 4.1; array lookup through a call (BPF_F_INNER_MAP: array_map_lookup_elem()) 4.9; hash lookup with 8 keys stored '
             '(call __htab_map_lookup_elem()) 13.9; kfunc pair bpf_task_from_pid() + bpf_task_release() 39.7.', b, m)
save('ch13-cost', fig133)

# ---------- Figure 13.4: a kfunc, registered at build and boot, checked at load ----------
# Two columns of steps, each read top to bottom. The verifier's check, which looks the BTF ID up in the registered set,
# is the accent: a heavy outline and a dashed line from the set.
m = 'ah-13-4p'
b = [markers(m)]
LX0, LX1, RX0, RX1 = 8, 296, 352, 672
def col_box(x0, x1, y, rows, accent=False, tag=None):
    """rows: lists of (text, face) parts, or (parts, 'b') for a bold line; returns the box and its bottom."""
    h = 18 * len(rows) + 14
    out = [rect(x0, y, x1 - x0, h, stroke=P2 if accent else INK, sw=2.6 if accent else 1.3)]
    for k, r in enumerate(rows):
        parts, bold = (r[0], True) if isinstance(r, tuple) else (r, False)
        indent = 16 if parts and parts[0][0].startswith('  ') else 0
        parts = [(parts[0][0].lstrip(), parts[0][1])] + parts[1:] if indent else parts
        out.append(tm(x0 + 9 + indent, y + 16 + 18 * k, parts, size=14.5, anchor='start', weight='700' if bold else None,
                      fill=P2 if accent and bold else INK))
    if tag:
        out.append(t(x1 - 9, y + 16 + 18, tag, size=14.5, anchor='end', fam=UMONO, fill=GREY))
    return out, y + h
M, S_ = 'm', 's'
b += [t((LX0 + LX1) / 2, 14, 'when the kernel is built and boots', size=16, weight='700'),
      t((RX0 + RX1) / 2, 14, 'when the counter calls a kfunc', size=16, weight='700')]
y = 32
o, yb = col_box(LX0, LX1, y, [([('__bpf_kfunc struct task_struct *', M)], 'b'), ([('bpf_task_from_pid(s32 pid)', M)], 'b')], tag='helpers.c'); b += o
b.append(line([((LX0 + LX1) / 2, yb), ((LX0 + LX1) / 2, yb + 17)], m + '-k', width=1.5)); y = yb + 18
o, yb = col_box(LX0, LX1, y, [[('BTF_KFUNCS_START(generic_btf_ids)', M)], [('BTF_ID_FLAGS(func, bpf_task_from_pid,', M)],
                              ([('  KF_ACQUIRE | KF_RET_NULL)', M)], 'b'),
                              [('.BTF_ids', M), (' holds 0 until', S_)], [('resolve_btfids', M), (' writes the BTF ID,', S_)],
                              [('82636, as the kernel is linked', S_)]]); b += o
b.append(line([((LX0 + LX1) / 2, yb), ((LX0 + LX1) / 2, yb + 17)], m + '-k', width=1.5)); y = yb + 18
YREG = y
o, yb = col_box(LX0, LX1, y, [([('kfunc_init()', M), (', a late_initcall:', S_)], 'b'), [('register_btf_kfunc_id_set(', M)],
                              [('  BPF_PROG_TYPE_TRACING,', M)], [('  &generic_kfunc_set)', M)],
                              [('the TRACING hook also holds', S_)], [('tracepoint programs; five more', S_)], [('types get the set', S_)]]); b += o
YL = yb
y = 32
o, yb = col_box(RX0, RX1, y, [[('clang: extern … ', S_), ('bpf_task_from_pid()', M), (' __ksym', M)],
                              ([('call -0x1  R_BPF_64_32 bpf_task_from_pid', M)], 'b')]); b += o
b.append(line([((RX0 + RX1) / 2, yb), ((RX0 + RX1) / 2, yb + 17)], m + '-k', width=1.5)); y = yb + 18
o, yb = col_box(RX0, RX1, y, [[('libbpf, from ', S_), ('/sys/kernel/btf/vmlinux', M), (':', S_)],
                              ([('src_reg 2 (kfunc call), imm 82636', M)], 'b')]); b += o
b.append(line([((RX0 + RX1) / 2, yb), ((RX0 + RX1) / 2, yb + 17)], m + '-k', width=1.5)); y = yb + 18
YCHK = y
o, yb = col_box(RX0, RX1, y, [([('check_kfunc_call()', M), (': in a set for this hook?', S_)], 'b'),
                              [('then arguments against the BTF prototype:', S_)],
                              [('R0=trusted_ptr_or_null_task_struct(id=2)', M)],
                              [('KF_RET_NULL', M), (': test r0 before any use;', S_)],
                              [('KF_ACQUIRE', M), (': release refs=2 before exit', S_)]], accent=True); b += o
b.append(line([((RX0 + RX1) / 2, yb), ((RX0 + RX1) / 2, yb + 17)], m + '-k', width=1.5)); y = yb + 18
o, yb = col_box(RX0, RX1, y, [[('kallsyms_lookup_name()', M), (', then the rewrite:', S_)],
                              ([('call bpf_task_from_pid#279936', M)], 'b')]); b += o
YR = yb
# the check looks the ID up in the registered set
b.append(line([(LX1, YREG + 30), (324, YREG + 30), (324, YCHK + 16), (RX0 - 2, YCHK + 16)], m + '-a', color=P2, width=2, dash='6 4'))
YLEG = max(YL, YR) + 24
b += [line([(LX0, YLEG), (LX0 + 40, YLEG)], m + '-k', width=1.5), t(LX0 + 48, YLEG, 'the next step', size=14.5, anchor='start'),
      line([(170, YLEG), (210, YLEG)], color=P2, width=2, dash='6 4'),
      t(218, YLEG, 'the check looks the BTF ID up in the sets registered for the hook', size=14.5, anchor='start', fill=P2)]
H134 = YLEG + 14
fig134 = svg(H134, 'A kfunc registered when the kernel boots and checked when a program that calls it is loaded',
             'Left, when the kernel is built and boots: __bpf_kfunc struct task_struct *bpf_task_from_pid(s32 pid) in helpers.c; '
             'BTF_KFUNCS_START(generic_btf_ids) and BTF_ID_FLAGS(func, bpf_task_from_pid, KF_ACQUIRE | KF_RET_NULL), whose .BTF_ids entry holds 0 '
             'until resolve_btfids writes the BTF ID, 82636, as the kernel is linked; kfunc_init(), a late_initcall, calls '
             'register_btf_kfunc_id_set(BPF_PROG_TYPE_TRACING, &generic_kfunc_set); the TRACING hook also holds tracepoint programs and five '
             'more types get the set. Right, when the counter calls a kfunc: clang emits call -0x1 with R_BPF_64_32 bpf_task_from_pid for '
             'an extern __ksym; libbpf writes src_reg 2 and imm 82636 from /sys/kernel/btf/vmlinux; check_kfunc_call() looks the ID up in '
             'the set for this hook, checks the arguments against the BTF prototype, R0=trusted_ptr_or_null_task_struct(id=2), KF_RET_NULL '
             'means r0 must be tested before use and KF_ACQUIRE that refs=2 must be released before exit; kallsyms_lookup_name() and the '
             'rewrite give call bpf_task_from_pid#279936.', b, m)
save('ch13-kfunc', fig134)
print('ch13 figures ok')
