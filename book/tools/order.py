#!/usr/bin/env python3
"""Change numbering.ORDER for a merge, safely while other agents do the same for other files.
  python3 -I tools/order.py merge NEW OLD [OLD ...]    e.g.  merge maps ch09 ch15 ch16
NEW (a file stem in src/) takes the place of the first OLD still in ORDER; the other OLDs are dropped; any PARTS key
that is now an alias of NEW (data-aliases on its <section>) is renamed to NEW's id. Idempotent: a second run, or a run
after another agent's merge, changes nothing it has already done. numbering.py is locked while it is rewritten.
  python3 -I tools/order.py move NEW --after STEM      (or --before STEM)   e.g.  move numbers --after walk
NEW, already in ORDER, is put directly after (or before) STEM, which must be in ORDER too; nothing else moves.
Idempotent, and numbering.py is locked as for merge. It refuses if either stem is missing from ORDER.
  python3 -I tools/order.py insert NEW --after STEM    (or --before STEM)   e.g.  insert memory --after maps
For a chapter that replaces no old file: NEW (a file stem in src/) goes directly after (or before) STEM. If NEW is
already in ORDER this is a move, so a second run changes nothing.
  python3 -I tools/order.py show                       the current order, with each file's id and aliases
The file changed is numbering.py in the book; ORDER_NUMBERING=path names another (a copy, for a test)."""
import fcntl, os, re, sys

BOOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUMPY = os.environ.get('ORDER_NUMBERING') or os.path.join(BOOK, 'numbering.py')

def section(stem):
    p = os.path.join(BOOK, 'src', stem + '.html')
    if not os.path.exists(p): return None, []
    m = re.search(r'<section id="([\w-]+)" class="chapter"([^>]*)>', open(p, encoding='utf-8').read())
    if not m: return None, []
    al = re.search(r'data-aliases="([^"]*)"', m.group(2))
    return m.group(1), (al.group(1).split() if al else [])

def write_order(s, m, out):
    """s with the ORDER list (matched by m) replaced by out, wrapped as merge has always written it."""
    lines, line = [], 'ORDER = ['
    for i, x in enumerate(out):
        item = repr(x) + (', ' if i < len(out) - 1 else '')
        if len(line) + len(item) > 116: lines.append(line.rstrip()); line = '         '
        line += item
    lines.append(line + ']')
    return s[:m.start()] + '\n'.join(lines) + s[m.end():]

def move(argv, insert=False):
    if len(argv) != 3 or argv[1] not in ('--after', '--before'): raise SystemExit(__doc__)
    new, where, stem = argv
    if new == stem: raise SystemExit(f'{new} cannot be moved {where[2:]} itself')
    with open(NUMPY, 'r+', encoding='utf-8') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        s = f.read()
        m = re.search(r'^ORDER = \[(.*?)\]', s, re.S | re.M)
        order = re.findall(r"'([\w-]+)'", m.group(1))
        if insert and new not in order:
            if not os.path.exists(os.path.join(BOOK, 'src', new + '.html')): raise SystemExit(f'no src/{new}.html to insert')
            order_for_check = order + [new]
        else:
            order_for_check = order
        missing = [x for x in (new, stem) if x not in order_for_check]
        if missing: raise SystemExit(f'not in ORDER: {", ".join(missing)} (nothing moved; merge puts a new file in ORDER)')
        out = [x for x in order if x != new]
        at = out.index(stem) + (1 if where == '--after' else 0)
        out[at:at] = [new]
        s2 = write_order(s, m, out) if out != order else s
        if s2 != s:
            f.seek(0); f.write(s2); f.truncate()
        print(f'ORDER: {" ".join(out)}' + ('' if s2 != s else ' (unchanged)'))

def main(argv):
    if argv[:1] == ['show']:
        order = re.search(r'^ORDER = \[(.*?)\]', open(NUMPY, encoding='utf-8').read(), re.S | re.M).group(1)
        for stem in re.findall(r"'([\w-]+)'", order):
            cid, al = section(stem)
            print(f'{stem:12} {cid or "(no file)":12} {" ".join(al)}')
        return
    if argv[:1] == ['move']: return move(argv[1:])
    if argv[:1] == ['insert']: return move(argv[1:], insert=True)
    if len(argv) < 3 or argv[0] != 'merge': raise SystemExit(__doc__)
    new, olds = argv[1], argv[2:]
    with open(NUMPY, 'r+', encoding='utf-8') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        s = f.read()
        m = re.search(r'^ORDER = \[(.*?)\]', s, re.S | re.M)
        order = re.findall(r"'([\w-]+)'", m.group(1))
        if new in order:
            out = [x for x in order if x not in olds]
        else:
            at = next((i for i, x in enumerate(order) if x in olds), None)
            if at is None: raise SystemExit(f'none of {olds} is in ORDER and {new} is not either: nothing to replace')
            out = order[:at] + [new] + [x for x in order[at + 1:] if x not in olds]
        s2 = write_order(s, m, out)
        cid, aliases = section(new)
        renamed = []
        if cid:
            pm = re.search(r'^PARTS = \{.*?^\}', s2, re.S | re.M)
            block = pm.group(0)
            for a in aliases:
                if re.search(rf"^    '{re.escape(a)}':", block, re.M) and not re.search(rf"^    '{re.escape(cid)}':", block, re.M):
                    block = re.sub(rf"^    '{re.escape(a)}':", f"    '{cid}':", block, flags=re.M); renamed.append(a)
            s2 = s2[:pm.start()] + block + s2[pm.end():]
        if s2 != s:
            f.seek(0); f.write(s2); f.truncate()
        print(f'ORDER: {" ".join(out)}' + (f'; PARTS key {", ".join(renamed)} -> {cid}' if renamed else '')
              + ('' if s2 != s else ' (unchanged)'))

if __name__ == '__main__':
    main(sys.argv[1:])
