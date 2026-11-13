#!/usr/bin/env python3
"""Five ways a Z3 query about a verifier operation goes wrong, each run.

    $PY -I book/labs/proof/pitfalls.py wf       # a missing assumption
    $PY -I book/labs/proof/pitfalls.py signed   # < against ULT
    $PY -I book/labs/proof/pitfalls.py widths   # ints, 32 and 64 bits
    $PY -I book/labs/proof/pitfalls.py timeout  # Linux 5.12's tnum_mul
    $PY -I book/labs/proof/pitfalls.py sat      # sat read as proved

The unfaithful encodings of C (32-bit halves, sign, an invariant left out,
code that runs later) are flags of cve.py.

Run from the repository root; PY is book/.venv/bin/python (Z3 5.4.1).
"""
import sys, time
from z3 import (BitVec, BitVecs, BitVecVal, Solver, ULE, If, Z3Exception,
                Extract, sat, simplify)


def tnum_and(pv, pm, qv, qm):              # kernel/bpf/tnum.c:92
    return pv & qv, (pv | pm) & (qv | qm) & ~(pv & qv)


def show(s, names):
    md = s.model()
    return ', '.join(f'{n}={md.eval(e, model_completion=True).as_long():#x}'
                     for n, e in names)


def wf():
    n = 8
    pv, pm, qv, qm, x, y = BitVecs('pv pm qv qm x y', n)
    rv, rm = tnum_and(pv, pm, qv, qm)
    z = x & y
    member = lambda x, v, m: x & ~m == v              # CGO 2022, Eq. 9
    masked = lambda x, v, m: x & ~m == v & ~m         # reads the same, is not
    for name, mem, wellformed in (('Eq. 9, no wellformed', member, False),
                                  ('masked, no wellformed', masked, False),
                                  ('masked, wellformed', masked, True)):
        s = Solver()
        if wellformed:
            s.add(pv & pm == 0, qv & qm == 0)
        s.add(mem(x, pv, pm), mem(y, qv, qm), (z & ~rm) != rv)
        r = s.check()
        print(f'{name:22} {r}', end='')
        print('  ' + show(s, [('pv', pv), ('pm', pm), ('qv', qv), ('qm', qm),
                              ('x', x), ('y', y)]) if r == sat else '')


def signed():
    x, y = BitVecs('x y', 32)
    for name, le in (('x & y <= x', lambda a, b: a <= b),
                     ('ULE(x & y, x)', ULE)):
        s = Solver()
        s.add(le(x & y, x) == False)                  # look for a violation
        r = s.check()
        print(f'{name:14} {r}', end='')
        if r == sat:
            md = s.model()
            k = [md.eval(e).as_long() for e in (x, y, x & y)]
            print(f'  x={k[0]:#010x} y={k[1]:#010x} x&y={k[2]:#010x}', end='')
        print()


def widths():
    x = BitVec('x', 32)
    print('x == 0x100000002 on 32 bits becomes', simplify(x == 0x100000002))
    try:
        BitVec('w', 32) & BitVec('r', 64)
    except Z3Exception as e:
        print('32-bit & 64-bit:', e.value.decode()[:58], '...')
    r = BitVec('r', 64)
    print('Extract(31, 0, r) has width', Extract(31, 0, r).size())


def mul_v512(pv, pm, qv, qm, n):           # kernel/bpf/tnum.c in Linux 5.12
    def hma(acc, value, mask):             # while (mask): one round per bit
        for i in range(n):
            bit = Extract(i, i, mask) == 1
            sv, sm = acc[0] + 0, acc[1] + (value << i)  # tnum_add(acc, (0, v))
            mu = ((sm + sv) ^ sv) | acc[1] | (value << i)
            acc = (If(bit, sv & ~mu, acc[0]), If(bit, mu, acc[1]))
        return acc
    acc = hma((pv * qv, BitVecVal(0, n)), pm, qm | qv)
    return hma(acc, qm, pv)


def timeout():
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    for n in (8, 16):
        pv, pm, qv, qm, x, y = BitVecs('pv pm qv qm x y', n)
        rv, rm = mul_v512(pv, pm, qv, qm, n)
        s = Solver()
        s.set(timeout=limit * 1000)        # milliseconds
        s.add(pv & pm == 0, qv & qm == 0, x & ~pm == pv, y & ~qm == qv)
        s.add((x * y) & ~rm != rv)
        t = time.perf_counter()
        r = s.check()
        print(f'tnum_mul of 5.12, {n} bits: {r} after'
              f' {time.perf_counter() - t:.1f} s', end='')
        print(f' ({s.reason_unknown()})' if str(r) == 'unknown' else '')


def sat_as_proof():
    pv, pm, qv, qm, x, y = BitVecs('pv pm qv qm x y', 64)
    rv, rm = tnum_and(pv, pm, qv, qm)
    s = Solver()
    s.add(pv & pm == 0, qv & qm == 0, x & ~pm == pv, y & ~qm == qv)
    s.add((x & y) & ~rm == rv)             # the claim itself, not negated
    print('claim asserted as it stands:', s.check(), ' one example:',
          show(s, [('x', x), ('y', y)]))


{'wf': wf, 'signed': signed, 'widths': widths, 'timeout': timeout,
 'sat': sat_as_proof}[sys.argv[1]]()
