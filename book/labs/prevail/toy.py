#!/usr/bin/env python3
"""A toy abstract interpreter and a toy path walk, for the PREVAIL chapter.

Both read the same few instructions, transcribed from the v7.2 verifier's
log of book/labs/prevail/pktloop.bpf.c (clang 23, -O2), with N filled in:

  once     sum_once as compiled: one length check before the loop, and a
           loop that ends on "if r3 == N"
  once-ge  the same, with that one test written "if r3 >= N"
  each     sum_each as compiled: a length check in every round

    python3 -I book/labs/prevail/toy.py once-ge 16 64 256
    python3 -I book/labs/prevail/toy.py once-ge 16 --no-narrow
    python3 -I book/labs/prevail/toy.py once-ge 16 --widen-after 0
    python3 -I book/labs/prevail/toy.py once 16
    python3 -I book/labs/prevail/toy.py each 16
    python3 -I book/labs/prevail/toy.py once-ge 16 --termination
    python3 -I book/labs/prevail/toy.py once-ge 16 -v   (each round)

The abstract interpreter keeps one interval per register, the interval
domain, and follows the schedule of PREVAIL's compute_fixpoint()
(src/crab/extrapolator.cpp): at the loop head it joins on the first round,
widens from the second, stops on the round that adds nothing and keeps
that round's value, then narrows (a meet, then narrowing) until nothing
changes.  --widen-after K widens from round K (0: never); --no-narrow keeps
the widened value, as a textbook widening does.  --termination adds a
ghost counter at the loop head and asks that it stay at most 100,000, the
limit of PREVAIL's BoundedLoopCount.

The path walk follows one path at a time with the same intervals and never
joins, as Linux's verifier does.  A branch it cannot decide is pushed and
walked later.  At a prune point (a conditional jump, or any jump's target)
a path stops when its live registers lie within those of a checkpoint
whose paths have all ended; a checkpoint is saved after at least 2 jumps
and 8 instructions, and inside a loop after 20 jumps or 100 instructions
(kernel/bpf/states.c, v7.2).  It counts instructions as the kernel's
"processed N insns" does.

Left out on purpose: the zone domain (relations such as r5 + 1 <= end),
PREVAIL's memory model (stack cells, maps, context fields), types beyond
number, context, packet pointer and packet end, helpers, signed and 32-bit
comparisons, and Linux's precision tracking.  Pointers are (region,
offset) pairs as in section 4 of the PLDI 2019 paper, and the packet's
length is a ghost variable, len, in [0, 65535].
"""
import re
import sys
import time

INF = float('inf')
U32 = 2**32 - 1
MAXPKT = 65535
LOOP_LIMIT = 100000          # PREVAIL: BoundedLoopCount::limit
ROUND_CAP = 100000           # the toy gives up after this many rounds

PROGRAMS = {'once': '''
 0: w0 = 2
 1: r2 = *(u32 *)(r1 +4)
 2: r1 = *(u32 *)(r1 +0)
 3: r3 = r1
 4: r3 += N
 5: if r3 > r2 goto pc+12
 6: w2 = 0
 7: r3 = 0
 8: r4 = r1
 9: r4 += r3
10: r4 = *(u8 *)(r4 +0)
11: w2 += w4
12: r3 += 1
13: if r3 == N goto pc+1
14: goto pc-7
15: w2 &= 1
16: w0 = 2
17: w0 -= w2
18: exit''', 'each': '''
 0: w2 = 0
 1: r3 = 0
 2: r4 = *(u32 *)(r1 +4)
 3: r1 = *(u32 *)(r1 +0)
 4: r5 = r1
 5: r5 += r3
 6: r0 = r5
 7: r0 += 1
 8: if r0 > r4 goto pc+4
 9: r5 = *(u8 *)(r5 +0)
10: w2 += w5
11: r3 += 1
12: if r3 != N goto pc-9
13: w2 &= 1
14: w0 = 2
15: w0 -= w2
16: exit'''}
PROGRAMS['once-ge'] = PROGRAMS['once'].replace('r3 == N', 'r3 >= N')

# ---------- the program ----------

R = r'([rw])(\d+)'
FORMS = [
    (R + r' = (-?\d+)$', 'movi'),
    (R + r' = [rw](\d+)$', 'mov'),
    (R + r' = \*\(u32 \*\)\(r(\d+) \+(\d+)\)$', 'ldctx'),
    (R + r' = \*\(u8 \*\)\(r(\d+) \+(\d+)\)$', 'ldpkt'),
    (R + r' ([-+&])= (-?\d+)$', 'alui'),
    (R + r' ([-+])= [rw](\d+)$', 'alu'),
    (r'if r(\d+) (>=|>|<|==|!=) (r\d+|-?\d+) goto pc([-+]\d+)$', 'jcc'),
    (r'goto pc([-+]\d+)$', 'ja'),
    (r'exit$', 'exit'),
]


def parse(name, n):
    prog = {}
    for line in PROGRAMS[name].strip().splitlines():
        pc, text = line.split(':', 1)
        pc, text = int(pc), text.strip().replace('N', str(n))
        for pat, op in FORMS:
            m = re.match(pat, text)
            if m:
                prog[pc] = (op, m.groups(), text)
                break
        else:
            raise SystemExit(f'cannot read slot {pc}: {text}')
    return prog


def target(prog, pc):
    op, g, _ = prog[pc]
    return pc + 1 + int(g[-1]) if op in ('jcc', 'ja') else None


def succs(prog, pc):
    op = prog[pc][0]
    if op == 'exit':
        return []
    if op == 'ja':
        return [target(prog, pc)]
    if op == 'jcc':
        return [target(prog, pc), pc + 1]
    return [pc + 1]


def uses_defs(ins):
    op, g, _ = ins
    if op == 'movi':
        return set(), {'r' + g[1]}
    if op in ('mov', 'ldctx', 'ldpkt'):
        return {'r' + g[2]}, {'r' + g[1]}
    if op == 'alui':
        return {'r' + g[1]}, {'r' + g[1]}
    if op == 'alu':
        return {'r' + g[1], 'r' + g[3]}, {'r' + g[1]}
    if op == 'jcc':
        u = {'r' + g[0]}
        return (u | {g[2]}) if g[2].startswith('r') else u, set()
    if op == 'exit':
        return {'r0'}, set()
    return set(), set()


def liveness(prog):
    live = {pc: set() for pc in prog}
    changed = True
    while changed:
        changed = False
        for pc in sorted(prog, reverse=True):
            out = set().union(*[live[s] for s in succs(prog, pc)])
            u, d = uses_defs(prog[pc])
            new = u | (out - d)
            if new != live[pc]:
                live[pc], changed = new, True
    return live


# ---------- intervals and abstract states ----------
# a value is (kind, lo, hi): kind 'num', 'ctx', 'pkt' (offset from the
# packet's start) or 'end' (the packet's end, offset len); a state maps
# registers to values, holds 'len', and is None when no run reaches it

def fmt(lo, hi):
    f = lambda x: '+oo' if x == INF else '-oo' if x == -INF else str(x)
    return f'[{f(lo)}, {f(hi)}]'


def show(v):
    k, lo, hi = v
    return {'num': '', 'ctx': 'ctx', 'end': 'end'}.get(k, 'pkt+') + \
        ('' if k in ('ctx', 'end') else fmt(lo, hi))


def leq(a, b):
    if a is None:
        return True
    if b is None:
        return False
    for k, v in b.items():
        w = a.get(k)
        if w is None or w[0] != v[0] or w[1] < v[1] or w[2] > v[2]:
            return False
    return True


def combine(a, b, f):
    if a is None:
        return b
    if b is None:
        return a
    out = {}
    for k in a.keys() & b.keys():
        (ka, la, ha), (kb, lb, hb) = a[k], b[k]
        if ka == kb:
            out[k] = (ka,) + f(la, ha, lb, hb)
    return out


def join(a, b):
    return combine(a, b, lambda la, ha, lb, hb: (min(la, lb), max(ha, hb)))


def widen(a, b):
    return combine(a, b, lambda la, ha, lb, hb:
                   (la if lb >= la else -INF, ha if hb <= ha else INF))


def meet(a, b):
    if a is None or b is None:
        return None
    out = dict(b)
    for k, (ka, la, ha) in a.items():
        if k in b and b[k][0] == ka:
            lo, hi = max(la, b[k][1]), min(ha, b[k][2])
            if lo > hi:
                return None
            out[k] = (ka, lo, hi)
        else:
            out[k] = a[k]
    return out


def narrow(a, b):
    if a is None or b is None:
        return None
    out = dict(a)
    for k, (ka, la, ha) in a.items():
        if k in b and b[k][0] == ka:
            out[k] = (ka, b[k][1] if la == -INF else la,
                      b[k][2] if ha == INF else ha)
    return out


NEG = {'>': '<=', '>=': '<', '<': '>=', '<=': '>', '==': '!=', '!=': '=='}


def refine(x, op, y):
    """Narrow intervals x and y so that x op y may hold; None if it cannot."""
    (xl, xh), (yl, yh) = x, y
    if op == '>':
        xl, yh = max(xl, yl + 1), min(yh, xh - 1)
    elif op == '>=':
        xl, yh = max(xl, yl), min(yh, xh)
    elif op in ('<', '<='):
        y2, x2 = refine(y, '>' if op == '<' else '>=', x) or (None, None)
        if y2 is None:
            return None
        (yl, yh), (xl, xh) = y2, x2
    elif op == '==':
        xl, xh = max(xl, yl), min(xh, yh)
        yl, yh = xl, xh
    elif op == '!=':
        if xl == xh == yl == yh:
            return None
        if yl == yh:
            xl, xh = xl + (xl == yl), xh - (xh == yl)
        if xl == xh:
            yl, yh = yl + (yl == xl), yh - (yh == xl)
    if xl > xh or yl > yh:
        return None
    return (xl, xh), (yl, yh)


def wrap(v, wide):
    k, lo, hi = v
    if not wide and k == 'num' and (lo < 0 or hi > U32):
        return ('num', 0, U32)
    return v


def step(ins, pc, s, alarms):
    """One instruction: [(next pc, state)] for each outcome it can have."""
    op, g, text = ins
    s = dict(s)

    def get(r):
        if r not in s:
            alarms.setdefault(pc, f'{r} is read before it is written')
            return ('num', -INF, INF)
        return s[r]

    if op == 'movi':
        s['r' + g[1]] = ('num', int(g[2]), int(g[2]))
    elif op == 'mov':
        s['r' + g[1]] = get('r' + g[2])
    elif op == 'ldctx':
        base = get('r' + g[2])
        if base[0] != 'ctx':
            alarms.setdefault(pc, 'context load through a non-context')
        s['r' + g[1]] = ('pkt', 0, 0) if g[3] == '0' else ('end', 0, 0)
    elif op == 'ldpkt':
        k, lo, hi = get('r' + g[2])
        off, (ll, lh) = int(g[3]), s['len'][1:]
        if k != 'pkt' or lo + off < 0 or hi + off + 1 > ll:
            alarms.setdefault(pc, f'r{g[2]} = {show((k, lo, hi))}, '
                              f'len in {fmt(ll, lh)}: may pass the end')
        s['r' + g[1]] = ('num', 0, 255)
    elif op in ('alui', 'alu'):
        k, lo, hi = get('r' + g[1])
        if op == 'alui':
            kb, lb, hb = 'num', int(g[3]), int(g[3])
        else:
            kb, lb, hb = get('r' + g[3])
        if g[2] == '&':
            v = ('num', 0, min(hi, lb) if lo >= 0 else lb)
        elif g[2] == '+' and kb == 'num':
            v = (k, lo + lb, hi + hb)
        elif g[2] == '+' and k == 'num':
            v = (kb, lb + lo, hb + hi)
        elif g[2] == '-' and k == kb == 'num':
            v = ('num', lo - hb, hi - lb)
        else:
            alarms.setdefault(pc, 'pointer arithmetic the toy refuses')
            v = ('num', -INF, INF)
        s['r' + g[1]] = wrap(v, g[0] == 'r')
    elif op == 'ja':
        return [(pc + 1 + int(g[0]), s)]
    elif op == 'exit':
        return []
    if op != 'jcc':
        return [(pc + 1, s)]
    # a conditional jump: refine the state for each outcome
    a, cmp, b = 'r' + g[0], g[1], g[2]
    out = []
    for nxt, o in ((pc + 1 + int(g[3]), cmp), (pc + 1, NEG[cmp])):
        t = dict(s)
        ka, la, ha = get(a)
        if b.startswith('r'):
            kb, lb, hb = get(b)
        else:
            kb, lb, hb = 'num', int(b), int(b)
        if ka == 'pkt' and kb == 'end':
            xy = refine((la, ha), o, t['len'][1:])
            if xy:
                t[a], t['len'] = (ka,) + xy[0], ('num',) + xy[1]
        elif ka == kb and ka in ('num', 'pkt'):
            xy = refine((la, ha), o, (lb, hb))
            if xy:
                t[a] = (ka,) + xy[0]
                if b.startswith('r'):
                    t[b] = (kb,) + xy[1]
        else:
            xy = True
        if xy:
            out.append((nxt, t))
    return out


def init():
    return {'r1': ('ctx', 0, 0), 'r10': ('stk', 512, 512),
            'len': ('num', 0, MAXPKT)}


# ---------- the abstract interpreter (one loop, as in these programs) ---

def analyse(prog, widen_after=2, do_narrow=True, termination=False,
            verbose=False):
    pcs = sorted(prog)
    back = [(pc, t) for pc in pcs for t in succs(prog, pc) if t <= pc]
    assert len({t for _, t in back}) == 1, 'the toy handles one loop'
    head, tail = back[0][1], max(pc for pc, _ in back)
    pre, alarms, count = {pc: None for pc in pcs}, {}, [0]
    edges = {}                      # (from, to) -> state on that edge

    def run(pc):
        count[0] += 1
        for nxt, t in step(prog[pc], pc, pre[pc], {}):
            edges[(pc, nxt)] = t
        return pre[pc]

    def incoming(pc, only=None):
        s = None
        for (a, b), t in edges.items():
            if b == pc and (only is None or only(a)):
                s = join(s, t)
        return s

    pre[pcs[0]] = init()
    for pc in pcs:
        if pc == head:
            break
        if pc != pcs[0]:
            pre[pc] = incoming(pc)
        if pre[pc] is not None:
            run(pc)

    def body(inv):                    # one round: the head, then the body
        edges_into_head = {k: v for k, v in edges.items() if k[1] == head}
        for k in list(edges):
            if head <= k[0] <= tail:
                del edges[k]
        edges.update({k: v for k, v in edges_into_head.items()
                      if k[0] < head})
        pre[head] = inv
        run(head)
        for pc in range(head + 1, tail + 1):
            pre[pc] = incoming(pc)
            if pre[pc] is not None:
                run(pc)
        new = incoming(head, lambda a: a < head)
        if termination:
            new['cnt'] = ('num', 0, 0)
        b = incoming(head, lambda a: a >= head)
        if b is not None and termination:
            k, lo, hi = b.get('cnt', ('num', -INF, INF))
            b = dict(b, cnt=(k, lo + 1, hi + 1))
        return join(new, b)

    entry = incoming(head)
    if termination:
        entry = dict(entry, cnt=('num', 0, 0))
    inv, up, down, k = entry, 0, 0, 0

    def note(what, s):
        if verbose:
            print(f'    {what:<16} ' + ', '.join(
                f'{r}={show(v)}' for r, v in sorted(s.items())
                if r in ('r2', 'r3', 'cnt')))
    while True:
        new = body(inv)
        up += 1
        if leq(new, inv):
            if do_narrow:
                inv = new
            note(f'up {up}: stable', inv)
            break
        k += 1
        if up >= ROUND_CAP:
            print(f'    no fixpoint after {ROUND_CAP:,} rounds; giving up')
            return None
        if widen_after == 0 or k < widen_after:
            inv = join(inv, new)
            note(f'up {up}: join', inv)
        else:
            inv = widen(inv, new)
            note(f'up {up}: widen', inv)
    k = 0
    while do_narrow:
        new = body(inv)
        down += 1
        if leq(inv, new):
            note(f'down {down}: stable', inv)
            break
        k += 1
        ref = meet(inv, new) if k == 1 else narrow(inv, new)
        done = leq(inv, ref)
        inv = ref
        note(f'down {down}: ' + ('meet' if k == 1 else 'narrow'), inv)
        if done:
            break
    body(inv)                             # the body's states, from inv
    for pc in pcs:
        if pc > tail:
            pre[pc] = incoming(pc)
            if pre[pc] is not None:
                run(pc)
    for pc in pcs:                        # the checks, on the final states
        if pre[pc] is not None:
            step(prog[pc], pc, pre[pc], alarms)
    if termination:
        hi = pre[head]['cnt'][2]
        if hi > LOOP_LIMIT:
            alarms[head] = (f'loop counter is too large: cnt in '
                            f'{fmt(*pre[head]["cnt"][1:])}')
    return dict(pre=pre, alarms=alarms, transfers=count[0], up=up,
                down=down, head=head, tail=tail)


# ---------- the path walk ----------

def walk(prog, limit=1000000):
    live = liveness(prog)
    prune = set()
    for pc in prog:
        if prog[pc][0] == 'jcc':
            prune.add(pc)
        t = target(prog, pc)
        if t is not None:
            prune.add(t)
    cps = {pc: [] for pc in prog}          # checkpoints: [state, done, L]
    open_cps, pending, alarms = [], [], {}
    n = dict(insns=0, jmps=0, saved=0, paths=0, pruned=0)
    last = dict(insns=0, jmps=0)

    def covered(cur, old, pc):
        regs = {r for r in live[pc] if r in old}
        if any(old[r][0] in ('pkt', 'end') for r in regs):
            regs.add('len')
        return all(r in cur and cur[r][0] == old[r][0]
                   and cur[r][1] >= old[r][1] and cur[r][2] <= old[r][2]
                   for r in regs)

    def end_path():
        n['paths'] += 1
        for cp in list(open_cps):
            if len(pending) <= cp[2]:
                cp[1] = True
                open_cps.remove(cp)

    pending.append((0, init()))
    while pending:
        pc, s = pending.pop()
        while True:
            n['insns'] += 1
            if n['insns'] > limit:
                return dict(n, alarms={pc: 'too many instructions'})
            if pc in prune:
                if any(done and covered(s, old, pc)
                       for old, done, _ in cps[pc]):
                    n['pruned'] += 1
                    end_path()
                    break
                looping = [cp for cp in cps[pc] if not cp[1]]
                if any(old == s for old, _, _ in looping):
                    alarms[pc] = 'infinite loop detected'
                    return dict(n, alarms=alarms)
                add = (n['jmps'] - last['jmps'] >= 2
                       and n['insns'] - last['insns'] >= 8)
                if looping and (n['jmps'] - last['jmps'] < 20
                                and n['insns'] - last['insns'] < 100):
                    add = False
                if add:
                    cp = [s, False, len(pending)]
                    cps[pc].append(cp)
                    open_cps.append(cp)
                    n['saved'] += 1
                    last.update(insns=n['insns'], jmps=n['jmps'])
            if prog[pc][0] in ('jcc', 'ja', 'exit'):   # BPF_JMP class
                n['jmps'] += 1
            outs = step(prog[pc], pc, s, alarms)
            if not outs:
                end_path()
                break
            for nxt, t in outs[:-1]:
                pending.append((nxt, t))
            pc, s = outs[-1]
    return dict(n, alarms=alarms)


# ---------- the report ----------

def report(name, n, opts):
    prog = parse(name, n)
    print(f'{name}, N={n} (slots 0-{max(prog)}; len in [0, {MAXPKT}])')
    t0 = time.perf_counter()
    a = analyse(prog, **opts)
    t1 = time.perf_counter()
    w = walk(prog)
    t2 = time.perf_counter()
    if a is None:
        return None
    h, pre = a['head'], a['pre']
    exitpc = max(prog)
    print(f'  fixpoint  {a["up"]} rounds up, {a["down"]} down, '
          f'{a["transfers"]} transfers, {1e3 * (t1 - t0):.1f} ms')
    regs = lambda s, rs: ', '.join(f'{r}={show(v)}' for r, v in
                                   sorted(s.items()) if r in rs)
    print(f'    head {h}: {regs(pre[h], ("r2", "r3", "cnt"))}')
    if pre[exitpc]:
        print(f'    exit {exitpc}: {regs(pre[exitpc], ("r0",))}')
    for pc, msg in sorted(a['alarms'].items()):
        print(f'    ALARM at {pc}: {msg}')
    print('    verdict: ' + ('rejected' if a['alarms'] else 'safe'))
    print(f'  path walk {w["insns"]} insns, {w["saved"]} checkpoints, '
          f'{w["paths"]} paths ({w["pruned"]} pruned), '
          f'{1e3 * (t2 - t1):.1f} ms')
    for pc, msg in sorted(w['alarms'].items()):
        print(f'    ALARM at {pc}: {msg}')
    print('    verdict: ' + ('rejected' if w['alarms'] else 'safe'))
    return a['transfers'], w['insns'], w['saved']


def main(argv):
    args = [x for x in argv if not x.startswith('-')]
    if not args or args[0] not in PROGRAMS:
        raise SystemExit(__doc__)
    opts = dict(do_narrow='--no-narrow' not in argv,
                termination='--termination' in argv,
                verbose='-v' in argv)
    for x in argv:
        if x.startswith('--widen-after='):
            opts['widen_after'] = int(x.split('=')[1])
    if '--widen-after' in argv:
        opts['widen_after'] = int(argv[argv.index('--widen-after') + 1])
        args.remove(argv[argv.index('--widen-after') + 1])
    name, bounds = args[0], [int(x) for x in args[1:]] or [16]
    rows = [(n, report(name, n, opts)) for n in bounds]
    if len(rows) > 1:
        print(f'{"N":>6} {"fixpoint transfers":>19} {"walk insns":>11} '
              f'{"checkpoints":>12}')
        for n, r in rows:
            if r:
                print(f'{n:>6} {r[0]:>19} {r[1]:>11} {r[2]:>12}')


if __name__ == '__main__':
    main(sys.argv[1:])
