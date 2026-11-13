# Chapter "Memory you manage" (src/memory.html): its three drawn figures.
# Drawn to the print rules in NOTES.md "Figure rules": 680 units = 127 mm, words 14.5 units or more,
# Open Sans Condensed for words, Ubuntu Mono for code names, black and grey with one accent.
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import esc, svg, save

SANS = "'Open Sans Condensed', 'Open Sans', 'Myriad Pro', sans-serif"
UMONO = "'Ubuntu Mono', 'JetBrains Mono', monospace"
INK, GREY, ACC, PALE = '#1F2328', '#4A5056', '#0F6E56', '#F3F4F2'


def t(x, y, s_, size=15, anchor='middle', fam=SANS, weight=None, fill=INK, italic=False):
    w = f' font-weight="{weight}"' if weight else ''
    it = ' font-style="italic"' if italic else ''
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-family="{fam}" '
            f'font-size="{size}" fill="{fill}"{w}{it}>{esc(s_)}</text>')


def rect(x, y, w, h, l1, l2=None, stroke=INK, sw=1.3, fill_text=INK, note=None, mono=True, fill='#FFFFFF'):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    if note is not None:         # an outcome in words, with a remark under it in grey
        return (out + t(x + w / 2, y + h / 2 - 10, l1, size=16, weight='700', fill=fill_text)
                + t(x + w / 2, y + h / 2 + 12, note, size=14.5, fill=GREY, italic=True))
    if l2 is None:
        return out + t(x + w / 2, y + h / 2, l1, size=15.5, fill=fill_text, fam=UMONO if mono else SANS)
    return (out + t(x + w / 2, y + h / 2 - 10, l1, size=16, fam=UMONO if mono else SANS, weight='700', fill=fill_text)
            + t(x + w / 2, y + h / 2 + 11, l2, size=15, fill=GREY))


def diamond(cx, cy, hw, hh, l1, l2):
    return (f'<polygon points="{cx - hw},{cy} {cx},{cy - hh} {cx + hw},{cy} {cx},{cy + hh}" fill="#FFFFFF" '
            f'stroke="{INK}" stroke-width="1.3"/>' + t(cx, cy - 10, l1, size=15.5) + t(cx, cy + 10, l2, size=15.5))


def line(pts, mid, color=INK, width=1.8, dash=None, arrow=True):
    d = ' '.join(f'{"M" if i == 0 else "L"}{x},{y}' for i, (x, y) in enumerate(pts))
    da = f' stroke-dasharray="{dash}"' if dash else ''
    me = f' marker-end="url(#{mid})"' if arrow else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da}{me}/>'


# ---------- an owning reference's life (verifier.c v7.2: check_reference_leak(), ref_set_non_owning(),
# process_spin_lock() -> invalidate_non_owning_refs(); helpers.c: bpf_obj_drop(), bpf_rbtree_add/remove()) ----------
# Claim: every path from bpf_obj_new() to exit must give the object away (drop it, park it in a kptr slot, or link it
# into a tree under its lock); a linked object is reachable only as a non-owning reference until the unlock, and
# bpf_rbtree_remove() in a later run makes it owned again. The path the verifier refuses is the accent.
m = 'ah-mem-life'
b = []
cx, X0, W0 = 230, 80, 300          # main column
RX, RW = 430, 244                  # right column
HH, BH = 34, 48                    # half-height of a diamond, height of a box


def yes_right(cy, label='yes', color=INK, width=1.8):
    b.append(line([(cx + 130, cy), (RX - 4, cy)], m, color=color, width=width))
    b.append(t(cx + 140, cy - 13, label, size=15.5, anchor='start', weight='700', fill=color))


b.append(rect(X0, 6, W0, BH, 'n = bpf_obj_new(T)', 'from this CPU’s cache'))
b.append(line([(cx, 54), (cx, 68)], m))
b.append(diamond(cx, 106, 130, HH, 'did it return', 'NULL?'))
yes_right(106)
b.append(rect(RX, 86, RW, 40, 'nothing to give back', mono=False))
b.append(t(cx - 10, 150, 'no', size=15.5, anchor='end', weight='700'))
b.append(line([(cx, 140), (cx, 154)], m))
b.append(rect(X0, 158, W0, BH, 'n->tid = tid', 'owned: any field, no lock'))
b.append(line([(cx, 206), (cx, 220)], m))
b.append(diamond(cx, 258, 130, HH, 'freed in', 'this program?'))
yes_right(258)
b.append(rect(RX, 234, RW, BH, 'bpf_obj_drop(n)', 'freed after a grace period'))
b.append(t(cx - 10, 302, 'no', size=15.5, anchor='end', weight='700'))
b.append(line([(cx, 292), (cx, 306)], m))
b.append(diamond(cx, 344, 130, HH, 'parked in a', 'map value?'))
yes_right(344)
b.append(rect(RX, 320, RW, BH, 'bpf_kptr_xchg(&v->p, n)', 'the map value owns it'))
b.append(t(cx - 10, 388, 'no', size=15.5, anchor='end', weight='700'))
b.append(line([(cx, 378), (cx, 392)], m))
b.append(diamond(cx, 430, 130, HH, 'linked into', 'a tree?'))
yes_right(430, 'no', ACC, 3)
b.append(rect(RX, 403, RW, 54, 'refused at load', stroke=ACC, sw=2.6, fill_text=ACC,
              note='Unreleased reference id=…'))
b.append(t(cx - 10, 474, 'yes', size=15.5, anchor='end', weight='700'))
b.append(line([(cx, 464), (cx, 478)], m))
b.append(rect(X0, 482, W0, BH, 'bpf_rbtree_add(root, n)', 'inside bpf_spin_lock(): the tree owns it'))
b.append(line([(cx, 530), (cx, 544)], m))
b.append(rect(X0, 548, W0, BH, 'n->count++', 'non-owning: fields only'))
b.append(line([(cx, 596), (cx, 610)], m))
b.append(rect(X0, 614, W0, BH, 'bpf_spin_unlock()', 'n is no longer usable'))
b.append(line([(cx, 662), (cx, 676)], m, dash='6 4'))
b.append(rect(X0, 680, W0, BH, 'bpf_rbtree_remove(root, n)', 'a later run, locked: owned again'))
b.append(line([(X0, 704), (36, 704), (36, 258), (cx - 134, 258)], m, dash='6 4'))
# remarks beside the nodes they qualify
b.append(t(RX - 30, 12, 'verifier: R0 = ptr_or_null_T(id=5);', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(RX - 30, 30, 'id 5 stays held until it is given', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(RX - 30, 48, 'away, on every path to exit', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(RX - 30, 664, 'dashed: across runs of the', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(RX - 30, 682, 'program, later in time', size=14.5, anchor='start', fill=GREY, italic=True))
fig = svg(736, 'An owning reference from bpf_obj_new to exit',
          'Flowchart. bpf_obj_new returns n or NULL. If NULL there is nothing to give back. Otherwise the program owns '
          'n and may write any field. Before exit it must free it with bpf_obj_drop, park it in a map value with '
          'bpf_kptr_xchg, or link it into a tree with bpf_rbtree_add under the lock; if none, the load is refused with '
          'Unreleased reference. After the add, n is a non-owning reference that may write fields until '
          'bpf_spin_unlock, after which it is unusable. In a later run bpf_rbtree_remove under the lock returns it '
          'owned again, and the questions start over.', b, m)
save('memory-life', fig)


# ---------- the BPF memory allocator (kernel/bpf/memalloc.c v7.2: unit_alloc(), unit_free_rcu(),
# bpf_mem_refill(), check_free_by_rcu(), init_refill_work()) ----------
# Claim: bpf_obj_new() takes an object off this CPU's free list for the size class, with interrupts off and no
# lock; a drop puts it on a waiting list, and only after an RCU grace period may it be handed out again; irq_work
# keeps the free list between 32 and 96 objects by taking from and giving back to the kernel's slab cache.
m = 'ah-mem-alloc'
b = []
b.append(rect(10, 8, 250, 54, 'bpf_obj_new()', 'in the program, any context'))
b.append(rect(420, 8, 250, 54, 'bpf_obj_drop()', 'in the program'))
# the per-CPU cache frame
b.append(f'<rect x="10" y="96" width="660" height="240" rx="6" fill="{PALE}" stroke="{GREY}" stroke-width="1" '
         f'stroke-dasharray="5 4"/>')
b.append(t(80, 124, 'one CPU’s cache: eleven size classes', size=15, anchor='start', fill=GREY))
sizes = ['16', '32', '64', '96', '128', '192', '256', '512', '1K', '2K', '4K']
x = 320
for s_ in sizes:
    hit = s_ == '64'
    b.append(f'<rect x="{x}" y="112" width="26" height="24" rx="3" fill="#FFFFFF" '
             f'stroke="{ACC if hit else GREY}" stroke-width="{2.6 if hit else 1}"/>')
    b.append(t(x + 13, 124, s_, size=14.5, fam=UMONO, fill=ACC if hit else INK, weight='700' if hit else None))
    x += 27
b.append(t(80, 152, 'a 48-byte node and its 8-byte header take the 64-byte class (accent)', size=14.5,
           anchor='start', fill=GREY, italic=True))
b.append(rect(30, 174, 250, 60, 'free list', 'kept between 32 and 96', stroke=ACC, sw=2.6))
b.append(rect(400, 174, 250, 60, 'waiting list', 'dropped, maybe still in use'))
b.append(line([(55, 170), (55, 66)], m, color=ACC, width=3))
b.append(t(66, 80, 'one off the list, interrupts off', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(line([(640, 62), (640, 170)], m))
b.append(line([(396, 204), (284, 204)], m))
b.append(t(340, 190, 'after a grace period', size=14.5, fill=GREY, italic=True))
b.append(rect(30, 262, 620, 54, 'irq_work on the same CPU', 'below 32: allocate a batch; above 96: give some back', mono=False))
b.append(line([(110, 238), (110, 258)], m))
b.append(line([(200, 258), (200, 238)], m))
b.append(rect(30, 366, 620, 54, 'kmalloc-cg-64', 'the kernel’s slab cache for 64-byte objects'))
b.append(line([(250, 320), (250, 362)], m))
b.append(line([(430, 362), (430, 320)], m))
b.append(t(262, 341, 'kmalloc_node()', size=14.5, anchor='start', fam=UMONO, fill=GREY))
b.append(t(442, 341, 'kfree()', size=14.5, anchor='start', fam=UMONO, fill=GREY))
fig = svg(430, 'Where bpf_obj_new gets its memory',
          'Box diagram of the BPF memory allocator. Each CPU has a cache with eleven size classes from 16 bytes to '
          '4 KiB; the counter\'s 48-byte nodes use the 64-byte class. bpf_obj_new takes one object off the free list '
          'with interrupts off. bpf_obj_drop puts it on a waiting list, which joins the free list after an RCU grace '
          'period. irq_work on the same CPU keeps the free list between 32 and 96 objects, allocating batches from '
          'the kmalloc-cg-64 slab cache and giving objects back to it.', b, m)
save('memory-alloc', fig)


# ---------- one arena page seen three ways (kernel/bpf/arena.c v7.2, header comment; arena_alloc_pages();
# fixups.c: addr_space_cast becomes a 32-bit mov; x86 JIT: r12 = kern_vm_start) ----------
# Claim: a page of the arena has one 32-bit offset. User space reaches it at the upper half of its mapping's
# address plus that offset, the program keeps only the offset, and the JIT adds kern_vm_start; so a pointer that
# the program stores (in user form) can be followed by user space as it is.
m = 'ah-mem-arena'
b = []
# user space band
b.append(t(40, 16, 'user space: the loader’s mapping of the arena (1,024 pages, 4 MiB)', size=15, anchor='start',
           weight='700'))
b.append(f'<rect x="40" y="32" width="630" height="40" rx="4" fill="#FFFFFF" stroke="{INK}" stroke-width="1.3"/>')
b.append(f'<rect x="40" y="32" width="64" height="40" rx="4" fill="{PALE}" stroke="{ACC}" stroke-width="2.6"/>')
b.append(t(72, 52, 'page 0', size=14.5, fill=ACC, weight='700'))
b.append(t(390, 52, '0x7f5cac7d3000 … 0x7f5cacbd3000', size=15, fam=UMONO))
b.append(t(40, 92, 'the table: 0x7f5cac7d3fe8', size=15, anchor='start', fam=UMONO))
# program band: the register, the two casts
b.append(f'<rect x="40" y="150" width="290" height="44" rx="4" fill="#FFFFFF" stroke="{INK}" stroke-width="1.3"/>')
b.append(t(185, 172, '0x00000000ac7d3fe8', size=16, fam=UMONO, weight='700'))
b.append(t(350, 140, 'the program: a register of type arena', size=15, anchor='start', weight='700'))
b.append(t(350, 164, 'solid: cast to the kernel’s space,', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(350, 182, 'keep the low 32 bits; dashed: cast', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(350, 200, 'back, add the mapping’s upper 32 bits', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(line([(120, 102), (120, 146)], m))
b.append(line([(210, 146), (210, 102)], m, dash='6 4'))
# kernel band
b.append(t(40, 234, 'the kernel: 4 GiB + 64 KiB of addresses, set aside when the map was created', size=15,
           anchor='start', weight='700'))
b.append(t(40, 254, 'each load or store: [kern_vm_start + 0xac7d3fe8 + off], kern_vm_start in r12', size=14.5,
           anchor='start', fam=UMONO, fill=GREY))
b.append(f'<rect x="40" y="270" width="630" height="40" rx="4" fill="#FFFFFF" stroke="{INK}" stroke-width="1.3"/>')
b.append(f'<rect x="440" y="270" width="64" height="40" rx="4" fill="{PALE}" stroke="{ACC}" stroke-width="2.6"/>')
b.append(t(472, 290, 'page 0', size=14.5, fill=ACC, weight='700'))
b.append(t(50, 290, 'kern_vm_start', size=15, anchor='start', fam=UMONO))
# the page itself, and who put it there
b.append(rect(240, 350, 280, 50, 'one 4 KiB page', 'the same memory on both sides', mono=False, stroke=ACC, sw=2.6))
b.append(line([(40, 52), (20, 52), (20, 375), (236, 375)], m, color=ACC, width=2))
b.append(line([(472, 310), (472, 346)], m, color=ACC, width=2))
b.append(t(30, 336, 'mapped in by a user fault', size=14.5, anchor='start', fill=GREY, italic=True))
b.append(t(484, 330, 'or by bpf_arena_alloc_pages()', size=14.5, anchor='start', fill=GREY, italic=True))
fig = svg(410, 'One arena page seen three ways',
          'Three bands. User space maps the arena of 1,024 pages at 0x7f5cac7d3000 and finds the hash table at '
          '0x7f5cac7d3fe8 on page 0. The program holds the same pointer as a register of type arena whose value is '
          'the low 32 bits, 0xac7d3fe8; a cast to the kernel space keeps the low 32 bits and a cast back adds the '
          'mapping\'s upper 32 bits. The kernel set aside 4 GiB plus 64 KiB of addresses from kern_vm_start; each '
          'load or store in the program goes to kern_vm_start plus the offset, with kern_vm_start held in register '
          'r12. Both mappings point at the same 4 KiB page, which a user-space fault or bpf_arena_alloc_pages put '
          'there.', b, m)
save('memory-arena', fig)
