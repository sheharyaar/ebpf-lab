import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import svg, save, esc

# Drawn for the 127 mm text column (680 units = 127 mm): words at 14.5 units or more, node titles 16,
# Open Sans Condensed for words and Ubuntu Mono for code names, black and grey with one accent that
# also differs by line weight or style (NOTES.md "Figure rules"; pattern of Figure 4.2 in ch04.py).
SANS = "'Open Sans Condensed', 'Open Sans', 'Myriad Pro', sans-serif"
UMONO = "'Ubuntu Mono', 'JetBrains Mono', monospace"
INK, GREY, GREY_L, WHITE = '#1F2328', '#4A5056', '#E4E6E8', '#FFFFFF'
ACC = '#0F6E56'   # the book's one accent, as in Figure 4-2

figs = {}


def t(x, y, s_, size=15, anchor='middle', fam=SANS, weight=None, fill=INK, italic=False):
    w = f' font-weight="{weight}"' if weight else ''
    it = ' font-style="italic"' if italic else ''
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-family="{fam}" '
            f'font-size="{size}" fill="{fill}"{w}{it}>{esc(s_)}</text>')


def box(x, y, w, h, fill=WHITE, stroke=INK, sw=1.3, dash=None, rx=5):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'


def node(x, y, w, h, l1, l2, stroke=INK, sw=1.3):
    return (box(x, y, w, h, stroke=stroke, sw=sw) + t(x + w / 2, y + h / 2 - 10, l1, size=16, fam=UMONO, weight='700')
            + t(x + w / 2, y + h / 2 + 11, l2, size=15, fill=GREY))


def path(pts, mid, color=INK, width=1.6, dash=None, arrow=True):
    d = ' '.join(f'{"M" if i == 0 else "L"}{x},{y}' for i, (x, y) in enumerate(pts))
    da = f' stroke-dasharray="{dash}"' if dash else ''
    me = f' marker-end="url(#{mid})"' if arrow else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da}{me}/>'


def diamond(cx, cy, hw, hh, l1, l2, stroke=INK, sw=1.3):
    return (f'<polygon points="{cx - hw},{cy} {cx},{cy - hh} {cx + hw},{cy} {cx},{cy + hh}" fill="{WHITE}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>' + t(cx, cy - 10, l1, size=15) + t(cx, cy + 10, l2, size=15))


def marker(mid, color):
    return (f'<defs><marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker></defs>')


# ---------------- Figure 16.3: a map of maps, its template, and a swap ----------------
# Facts: bpf_map_meta_alloc(), bpf_map_meta_equal(), bpf_map_fd_get_ptr(), bpf_map_fd_put_ptr() in
# kernel/bpf/map_in_map.c; mark_ptr_not_null_reg() in verifier.c gives lookup 1's result the template.
m = 'ah-16-3'
b = [marker(m + 'a', ACC)]
# legend
b += [path([(420, 16), (462, 16)], m, width=1.8, arrow=False), t(470, 16, 'a lookup follows', anchor='start'),
      path([(420, 40), (462, 40)], m + 'a', color=ACC, width=2.4, dash='7 5', arrow=False),
      t(470, 40, 'user space swaps slot 0', anchor='start', fill=ACC, weight='600')]
# the program
b.append(node(10, 92, 160, 62, 'count_writes', 'two lookups'))
# the outer map: four slots
OX, OW, SY, SH = 240, 150, 92, 34
b.append(t(OX + OW / 2, 64, 'outer map', size=15, weight='600'))
b.append(t(OX + OW / 2, 80, 'ARRAY_OF_MAPS', size=15, fam=UMONO, fill=GREY))
cells = [('0', 'points to A'), ('1', 'empty'), ('2', 'empty'), ('3', 'empty')]
for k, (n, c) in enumerate(cells):
    y = SY + k * SH
    b.append(box(OX, y, OW, SH, fill=WHITE if k else GREY_L, rx=0, sw=1.1))
    b.append(t(OX + 16, y + SH / 2, n, fam=UMONO, size=15, fill=GREY))
    b.append(t(OX + 34, y + SH / 2, c, anchor='start', size=15, fill=INK if k == 0 else GREY))
# inner maps
IX, IW = 480, 190
b.append(node(IX, 92, IW, 62, 'HASH  A', 'the counts so far'))
b.append(node(IX, 196, IW, 62, 'HASH  B', 'empty, ready'))
# lookups
b.append(path([(170, 109), (OX - 2, 109)], m, width=1.8))
b.append(t((170 + OX) / 2, 96, 'lookup 1', size=15, weight='600'))
b.append(path([(OX + OW, 109), (IX - 2, 109)], m, width=1.8))
b.append(t((OX + OW + IX) / 2, 96, 'lookup 2', size=15, weight='600'))
# the swap
b.append(path([(OX + OW, 116), (440, 116), (440, 227), (IX - 2, 227)], m + 'a', color=ACC, width=2.4, dash='7 5'))
b.append(t(452, 175, 'one update:', size=15, anchor='start', fill=ACC, weight='600'))
b.append(t(530, 175, 'slot 0 = B', size=15.5, anchor='start', fill=ACC, fam=UMONO, weight='700'))
b.append(t(IX + IW / 2, 276, 'A is freed after an RCU grace', size=15, fill=GREY))
b.append(t(IX + IW / 2, 295, 'period if nothing else holds it', size=15, fill=GREY))
# the template
TY = 330
b.append(path([(OX + OW / 2, SY + 4 * SH), (OX + OW / 2, TY - 2)], m, color=GREY, width=1.3, dash='3 3', arrow=False))
b.append(t(OX + OW / 2 + 8, (SY + 4 * SH + TY) / 2, 'kept by the outer map', size=15, anchor='start', fill=GREY, italic=True))
b.append(box(10, TY, 660, 64, fill=GREY_L, stroke=GREY, sw=1.1))
b.append(t(24, TY + 20, 'inner-map template, copied at creation from the map given as inner_map_fd', size=15, anchor='start', weight='600'))
b.append(t(24, TY + 44, 'HASH · key 4 B · value 8 B · flags 0 · BTF fields', size=15.5, anchor='start', fam=UMONO))
b.append(t(10, TY + 88, 'At load, the verifier checks lookup 2 against the template, since any matching map may be in the slot.', size=15, anchor='start'))
b.append(t(10, TY + 110, 'At update, a map of another type, key size, value size or flags is refused with ‑EINVAL;', size=15, anchor='start'))
b.append(t(10, TY + 130, 'an array inside must also match max_entries unless the template has BPF_F_INNER_MAP.', size=15, anchor='start'))
figs['mim'] = svg(TY + 146, 'A map of maps: two lookups, a template checked at load and at update, and a swap of a whole inner map',
                  'The program looks up slot 0 of an array of maps, which holds a pointer to hash A, and then looks up a key in A. '
                  'User space replaces slot 0 with hash B in one update, and A is freed after a grace period. Below, the template the outer map '
                  'keeps: hash, 4-byte key, 8-byte value, flags 0, BTF fields, against which loads and updates are checked.', b, m)

# ---------------- Figure 16.5: one update of a prog-array slot ----------------
# Facts: bpf_fd_array_map_update_elem(), prog_fd_array_get_ptr(), prog_array_map_poke_run() in arraymap.c;
# bpf_prog_map_compatible() in core.c; bpf_arch_poke_desc_update() and __bpf_arch_text_poke() in
# arch/x86/net/bpf_jit_comp.c; smp_text_poke_single() in arch/x86/kernel/alternative.c.
# Times: /tmp/book-labs/ch16/poke.txt (labs/ch16-root.sh step 6), kernel 7.2.15, 16 virtual CPUs.
T_PLAIN = '0.8 to 3.7 µs'
T_SITE = '0.05 to 1.1 ms a site'
T_RCU = '5 to 7 ms a site, both patches included'
m = 'ah-16-5'
b = [marker(m + 'a', ACC)]
CX, NW = 190, 300
NX = CX - NW / 2
RX = 400                      # right column: where a path ends
b.append(node(NX, 8, NW, 56, 'bpf_map_update_elem()', 'user space puts a program in slot k'))
b.append(path([(CX, 64), (CX, 88)], m))
b.append(diamond(CX, 130, 150, 42, '', ''))
b += [t(CX, 112, 'type, JIT, sleepable,', size=15), t(CX, 130, 'expected_attach_type', size=14, fam=UMONO),
      t(CX, 148, 'as the owner’s?', size=15)]
b.append(path([(CX + 150, 130), (RX - 2, 130)], m))
b.append(t(CX + 160, 118, 'no', size=15.5, anchor='start', weight='700'))
b.append(t(RX + 8, 120, 'stops here: ‑EINVAL,', size=15, anchor='start', weight='600'))
b.append(t(RX + 8, 140, 'the slot is unchanged', size=15, anchor='start'))
b.append(path([(CX, 172), (CX, 198)], m))
b.append(t(CX - 10, 185, 'yes', size=15.5, anchor='end', weight='700'))
b.append(node(NX, 200, NW, 56, 'xchg(&ptrs[k], prog)', 'the slot holds the new program'))
b.append(path([(CX, 256), (CX, 280)], m))
b.append(diamond(CX, 322, 150, 42, 'does a direct tail call', 'name this map and slot k?'))
b.append(path([(CX + 150, 322), (RX - 2, 322)], m))
b.append(t(CX + 160, 310, 'no', size=15.5, anchor='start', weight='700'))
b.append(t(RX + 8, 312, 'done: ' + T_PLAIN, size=15, anchor='start', weight='600'))
b.append(t(RX + 8, 332, 'in all, as for any array', size=15, anchor='start'))
b.append(path([(CX, 364), (CX, 390)], m + "a", color=ACC, width=2.4))
b.append(t(CX - 10, 377, 'yes', size=15.5, anchor='end', weight='700'))
b.append(node(NX, 392, NW, 56, 'bpf_arch_poke_desc_update()', 'rewrite 5 bytes at each such site', stroke=ACC, sw=2.6))
b.append(t(RX + 8, 400, 'for each site: an int3, then three', size=15, anchor='start', fill=ACC))
b.append(t(RX + 8, 420, 'rounds of interrupts to every CPU;', size=15, anchor='start', fill=ACC))
b.append(t(RX + 8, 440, T_SITE + ' here', size=15, anchor='start', fill=ACC, weight='600'))
b.append(path([(CX, 448), (CX, 472)], m + "a", color=ACC, width=2.4))
b.append(diamond(CX, 514, 150, 42, 'was the slot', 'emptied?'))
b.append(path([(CX + 150, 514), (RX - 2, 514)], m + "a", color=ACC, width=2.4))
b.append(t(CX + 160, 502, 'yes', size=15.5, anchor='start', weight='700'))
b.append(node(RX, 486, 270, 56, 'synchronize_rcu()', 'between its two patches', stroke=ACC, sw=2.6))
b.append(t(RX + 135, 556, T_RCU, size=15, fill=ACC, weight='600'))
b.append(path([(CX, 556), (CX, 590)], m))
b.append(t(CX - 10, 573, 'no', size=15.5, anchor='end', weight='700'))
b.append(path([(RX + 135, 566), (RX + 135, 614), (CX + 90, 614)], m))
b.append(box(CX - 90, 592, 180, 44))
b.append(t(CX, 614, 'done', size=16, weight='700'))
b.append(t(10, 662, 'Thick accent outlines: work done once for every program whose direct tail call names the slot.', size=15, anchor='start', fill=ACC))
figs['update'] = svg(678, 'What one update of a program-array slot does',
                     'Flowchart: user space writes a program into slot k; if its type, JIT, sleepable flag or expected_attach_type differ from the owner’s, the update stops with EINVAL. '
                     'Otherwise the slot is exchanged; if no direct tail call names the slot, the update is done in a few microseconds. If one does, '
                     'the kernel rewrites five bytes at each such call site, with interrupts to every CPU, and when the slot was emptied it also waits '
                     'for an RCU grace period at each site.', b, m)

for k in ('mim', 'update'):
    save(f'ch16-{k}', figs[k])
print('ch16 figures ok')
