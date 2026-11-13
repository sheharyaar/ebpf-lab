# Chapter 2 figures: from SEC() name to hook; who holds whom after load and attach.
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *

# ---------------- Figure 2.2: section name -> program type and hook ----------------
m = 'ah-2-2'
b = [text(40, 16, 'the SEC() string, cut at the first slash', size=11, col='gray', anchor='start', italic=True),
     text(380, 16, 'what libbpf makes of each part', size=11, col='gray', anchor='start', italic=True)]
rows = [
    ('the write counter · maps/02-hash-map', 'tracepoint', '/syscalls/sys_enter_write',
     ('BPF_PROG_TYPE_TRACEPOINT', 'table entry tracepoint+, no attach type yet'),
     ('syscalls / sys_enter_write', 'a fixed tracepoint, found by its number')),
    ('the kprobe example · hello_world/02-kprobe', 'kprobe', '/do_sys_openat2',
     ('BPF_PROG_TYPE_KPROBE', 'table entry kprobe+, no attach type yet'),
     ('do_sys_openat2', 'the entry of a kernel function, by name')),
    ('the fork tracer · hello_world/03-tracepoint', 'tp_btf', '/sched_process_fork',
     ('BPF_PROG_TYPE_TRACING', 'entry tp_btf+, attach type BPF_TRACE_RAW_TP'),
     ('sched_process_fork', 'a tracepoint with typed arguments')),
]
CW = 7.25  # mono 12 advance
for i, (lab, pre, ext, typ, hook) in enumerate(rows):
    y0 = 30 + i * 108
    b.append(text(40, y0 + 12, lab, size=11, anchor='start'))
    wp, we = len(pre) * CW + 18, len(ext) * CW + 18
    b.append(box(40, y0 + 36, wp, 32, 'teal', pre, mono1=True, size1=12))
    b.append(box(40 + wp, y0 + 36, we, 32, 'amber', ext, mono1=True, size1=12))
    b.append(box(380, y0 + 4, 260, 44, 'teal', typ[0], typ[1], mono1=True, size1=11.5))
    b.append(box(380, y0 + 56, 260, 44, 'amber', hook[0], hook[1], mono1=True, size1=11.5))
    px, ex = 40 + wp / 2, 40 + wp + we
    b.append(f'<path d="M{px},{y0 + 36} V{y0 + 26} H376" fill="none" stroke="{LINE}" stroke-width="1.3" marker-end="url(#{m})"/>')
    b.append(f'<path d="M{ex},{y0 + 52} H352 V{y0 + 78} H376" fill="none" stroke="{LINE}" stroke-width="1.3" marker-end="url(#{m})"/>')
b.append(bar(360, 36, 'Before the first slash: which program type. After it: which hook. Both come from the section name.'))
fig_sec = svg(406, 'From a SEC() name to a program type and a hook',
              'Three section names from the book\'s example programs, each split at the first slash; the prefix picks the program type and the rest names the hook', b, m)

# ---------------- Figure 2.4: who holds whom ----------------
m = 'ah-2-4'
b = [text(140, 18, 'the loader process', size=12, col='gray', weight='600'),
     text(470, 18, 'in the kernel', size=12, col='gray', weight='600')]
b.append(f'<rect x="40" y="32" width="200" height="236" rx="6" fill="{C["gray"][0]}" stroke="{C["gray"][1]}" stroke-width="0.9"/>')
fds = [(49, 'map fd · write_counts'), (99, 'map fd · …_.rodata'), (157, 'program fd'), (229, 'link fd')]
for y, t in fds:
    b.append(box(54, y, 172, 30, 'gray', t, mono1=True, size1=11))
objs = [
    (480, 44, 160, 40, 'coral', 'write_counts', 'the hash map'),
    (480, 94, 160, 40, 'coral', 'hashmap_.rodata', 'the bpf_printk string'),
    (300, 150, 140, 44, 'teal', 'count_writes', 'the program, 27 slots'),
    (300, 222, 140, 44, 'teal', 'link', 'one program on one hook'),
    (480, 222, 160, 44, 'coral', 'sys_enter_write', 'tracepoint, as a perf event'),
]
for (x, y, w, h, col, t1, t2) in objs:
    b.append(box(x, y, w, h, col, t1, t2, mono1=t1 != 'link', size1=12))
# a descriptor holds its object: dashed
for (y0, ty) in [(64, 64), (114, 114), (172, 172), (244, 244)]:
    tx2 = 478 if ty < 140 else 298
    b.append(arrow(226, y0, tx2, ty, m, dash='4 3'))
# objects hold objects: solid, thicker
b.append(arrow(370, 222, 370, 197, m, width=1.8))
b.append(arrow(440, 162, 478, 70, m, width=1.8))
b.append(arrow(440, 168, 478, 120, m, width=1.8))
b.append(arrow(440, 244, 478, 244, m, width=1.8))
b.append(text(418, 136, 'holds', size=10.5, col='gray', italic=True))
b.append(text(459, 234, 'holds', size=10.5, col='gray', italic=True))
b.append(text(380, 210, 'holds', size=10.5, col='gray', italic=True, anchor='start'))
# the pin
b.append(f'<rect x="40" y="284" width="200" height="32" rx="6" fill="#FFFFFF" stroke="{C["gray"][1]}" stroke-width="0.9" stroke-dasharray="4 3"/>')
b.append(text(140, 300, 'a pin: a file in /sys/fs/bpf', size=11.5, col='gray'))
b.append(f'<path d="M240,300 H330 V269" fill="none" stroke="{LINE}" stroke-width="1.3" stroke-dasharray="4 3" marker-end="url(#{m})"/>')
b.append(text(338, 300, 'holds whatever it names, with no process at all', size=11, col='gray', anchor='start', italic=True))
b.append(bar(330, 34, 'Each arrow is one reference. An object is freed when its last reference goes.'))
fig_objs = svg(374, 'Who holds whom after load and attach',
               'The loader process holds descriptors for two maps, the program and the link; the link holds the program and the tracepoint, the program holds both maps; a pin can hold any of them', b, m)

save('ch02-sec', fig_sec)
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

# ---------- Figure 2.3 for print: what open_and_load() and attach() ask of the kernel (replaces the Mermaid sequence) ----------
m = 'ah-2-3p'
b = [markers(m).replace('</defs>', f'<marker id="{m}-g" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                                    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{GREY}"/></marker></defs>')]
LL, KL = 96, 604                       # the loader's and the kernel's lifelines
b += [rect(LL - 66, 8, 132, 46), t(LL, 24, 'loader', size=16, weight='700'), t(LL, 43, 'through libbpf', size=14.5, fill=GREY),
      rect(KL - 66, 8, 132, 46), t(KL, 31, 'kernel', size=16, weight='700')]
END = 404
b += [f'<line x1="{LL}" y1="54" x2="{LL}" y2="{END}" stroke="{GREY}" stroke-width="1.2"/>',
      f'<line x1="{KL}" y1="54" x2="{KL}" y2="{END}" stroke="{GREY}" stroke-width="1.2"/>']
def phase(y, call, what):
    return [f'<rect x="8" y="{y - 13}" width="664" height="26" fill="#EEF0F1"/>',
            tm(16, y, [(call, 'm'), (what, 's')], size=15, anchor='start')]
def msg(n, y, parts, ask=True):
    x1, x2 = (LL, KL - 2) if ask else (KL, LL + 2)
    out = [t(16, y - 9, str(n), size=15, weight='700', anchor='start'), tm((LL + KL) / 2, y - 11, parts, size=15 if ask else 14.5, fill=INK if ask else GREY)]
    out.append(line([(x1, y), (x2, y)], m + ('-k' if ask else '-g'), color=INK if ask else GREY, width=1.8 if ask else 1.5, dash=None if ask else '6 4'))
    return out
b += phase(76, 'hashmap_bpf__open_and_load()', ': the objects are created')
b += msg(1, 116, [('BPF_MAP_CREATE', 'm'), (', twice', 's')])
b += msg(2, 150, [('two map descriptors, moved onto the numbers in the code', 's')], ask=False)
b += msg(3, 184, [('BPF_PROG_LOAD', 'm'), (', ', 's'), ('TRACEPOINT', 'm'), (', 27 slots', 's')])
b += msg(4, 218, [('the program, checked and rewritten', 's')], ask=False)
b += phase(250, 'hashmap_bpf__attach()', ': the objects are connected')
b += msg(5, 290, [('perf_event_open', 'm'), (' on the tracepoint', 's')])
b += msg(6, 324, [('perf event descriptor', 's')], ask=False)
b += msg(7, 358, [('BPF_LINK_CREATE', 'm'), (', program plus event', 's')])
b += msg(8, 392, [('link descriptor, and the program runs', 's')], ask=False)
b += [line([(204, 430), (244, 430)], width=1.8), t(252, 430, 'the loader asks', size=14.5, anchor='start'),
      line([(390, 430), (430, 430)], color=GREY, width=1.5, dash='6 4'), t(438, 430, 'the kernel answers', size=14.5, anchor='start', fill=GREY)]
fig_seq = svg(446, 'What open_and_load() and attach() ask of the kernel, in order',
              'Two lifelines, the loader through libbpf and the kernel. hashmap_bpf__open_and_load(): BPF_MAP_CREATE twice, answered with two map descriptors that libbpf moves onto the numbers already in the code; '
              'BPF_PROG_LOAD for a tracepoint program of 27 slots, answered with the program, checked and rewritten. hashmap_bpf__attach(): '
              'perf_event_open on the tracepoint, answered with a perf event descriptor; BPF_LINK_CREATE with program and event, answered with '
              'a link descriptor, and the program runs.', b, m)
save('ch02-loadseq', fig_seq)
# ---------- Figure 2.4 for print: who holds whom while the loader runs ----------
# Solid accent arrows: one kernel object holds another; dashed black arrows: the loader's descriptors and the pin.
m = 'ah-2-4p'
b = [markers(m).replace('</defs>', f'<marker id="{m}-t" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4.6" markerHeight="4.6" '
                                    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{P2}"/></marker></defs>')]
TH = 2.8
AX, AW, BX_, BW_ = 290, 180, 500, 176          # kernel objects: column A and column B
ROWS = [56, 122, 188, 254]                      # row centres: write_counts, .rodata, program, link
OH = 44
def obj(x, w, yc, name, what):
    return [rect(x, yc - OH / 2, w, OH), t(x + w / 2, yc - 9, name, size=16, fam=UMONO, weight='700'),
            t(x + w / 2, yc + 12, what, size=14.5, fill=GREY)]
b += [t(113, 14, 'the loader process', size=16, weight='700'), t(483, 14, 'in the kernel', size=16, weight='700')]
b.append(f'<rect x="8" y="28" width="210" height="254" rx="6" fill="#EEF0F1" stroke="{GREY}" stroke-width="1"/>')
for yc, lab in zip(ROWS, ['map fd · write_counts', 'map fd · …_.rodata', 'program fd', 'link fd']):
    b += [rect(20, yc - 16, 186, 32, stroke=GREY, sw=1.1), t(113, yc, lab, size=15, fam=UMONO)]
    b.append(line([(206, yc), (AX - 2, yc)], m + '-k', width=1.5, dash='6 4'))
b += obj(AX, AW, ROWS[0], 'write_counts', 'the hash map')
b += obj(AX, AW, ROWS[1], 'hashmap_.rodata', 'the bpf_printk string')
b += obj(AX, AW, ROWS[2], 'count_writes', 'the program, 27 slots')
b += obj(AX, AW, ROWS[3], 'link', 'one program on one hook')
b += obj(BX_, BW_, ROWS[3], 'sys_enter_write', 'tracepoint, as a perf event')
cx = AX + AW / 2
b += [line([(cx, ROWS[3] - OH / 2), (cx, ROWS[2] + OH / 2 + 2)], m + '-t', color=P2, width=TH),          # link holds the program
      line([(AX + AW, ROWS[3]), (BX_ - 2, ROWS[3])], m + '-t', color=P2, width=TH),                     # link holds the event
      line([(cx, ROWS[2] - OH / 2), (cx, ROWS[1] + OH / 2 + 2)], m + '-t', color=P2, width=TH),          # program holds .rodata
      line([(AX + AW, ROWS[2] - 8), (486, ROWS[2] - 8), (486, ROWS[0]), (AX + AW + 2, ROWS[0])], m + '-t', color=P2, width=TH),
      # the perf event holds the program too: bpf_perf_link_attach() takes a reference for it (syscall.c, v7.2)
      line([(BX_ + BW_ / 2, ROWS[3] - OH / 2), (BX_ + BW_ / 2, ROWS[2] + 8), (AX + AW + 2, ROWS[2] + 8)], m + '-t', color=P2, width=TH)]
# the pin
b += [rect(8, 298, 210, 34, stroke=INK, sw=1.3, dash='6 4'),
      tm(113, 315, [('a pin: a file in ', 's'), ('/sys/fs/bpf', 'm')], size=15),
      line([(218, 315), (cx, 315), (cx, ROWS[3] + OH / 2 + 2)], m + '-k', width=1.5, dash='6 4'),
      t(cx + 12, 315, 'holds whatever it names, with no process at all', size=14.5, anchor='start', italic=True, fill=GREY)]
# legend
b += [line([(20, 358), (62, 358)], color=P2, width=TH), t(70, 358, 'one kernel object holds another', size=14.5, anchor='start'),
      line([(290, 358), (332, 358)], width=1.5, dash='6 4'), t(340, 358, 'a descriptor or a pin holds an object', size=14.5, anchor='start')]
fig_objs_print = svg(374, 'Who holds whom after load and attach',
                     'The loader process holds descriptors for the two maps, write_counts and hashmap_.rodata, for the program count_writes '
                     'and for the link. In the kernel the link holds the program and the sys_enter_write tracepoint, as a perf event, '
                     'the perf event holds the program as well, and the program holds both maps. A pin, a file in /sys/fs/bpf, holds whatever it names with no process at all.', b, m)
save('ch02-objects', fig_objs_print)
print('ch02 figures ok')
