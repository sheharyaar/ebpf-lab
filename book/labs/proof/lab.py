#!/usr/bin/env python3
"""Lab: check a tnum operation on small widths, then prove it at 64 bits.

    python3 -I book/labs/proof/lab.py check [BITS]  # every case, 4 bits
    $PY -I book/labs/proof/lab.py prove [BITS]      # Z3, 64 bits

Write the operation once, in op() below, using only & | ^ ~ + and -.  The
same code then runs on Python integers, cut to BITS bits at the end, and on
Z3 bit-vectors.  (Cutting at the end is right for these six operators
because the low bits of their results depend only on the low bits of their
inputs; a comparison, a division or a right shift would break that.)
As shipped, op() is tnum_and(); replace it with the operation you chose.

Run from the repository root; PY is book/.venv/bin/python (Z3 5.4.1).
"""
import sys, time


def op(pv, pm, qv, qm):                # kernel/bpf/tnum.c:92, Linux v7.2
    alpha = pv | pm
    beta = qv | qm
    v = pv & qv
    return v, alpha & beta & ~v


def concrete(x, y):                    # what the instruction does to numbers
    return x & y


def trits(v, m, n):
    return ''.join('x' if m >> i & 1 else str(v >> i & 1)
                   for i in reversed(range(n)))


def check(n):
    M = (1 << n) - 1
    tn = [(v, m) for m in range(M + 1) for v in range(M + 1) if v & m == 0]
    gamma = {t: [x for x in range(M + 1) if x & ~t[1] & M == t[0]] for t in tn}
    t0, cases, bad = time.perf_counter(), 0, []
    for P in tn:
        for Q in tn:
            rv, rm = (k & M for k in op(*P, *Q))
            for x in gamma[P]:
                for y in gamma[Q]:
                    cases += 1
                    z = concrete(x, y) & M
                    if z & ~rm & M != rv:
                        bad.append((P, Q, x, y, z, rv, rm))
    print(f'check, {n} bits: {cases:,} cases, {len(bad):,} counterexamples,'
          f' {time.perf_counter() - t0:.2f} s')
    if bad:
        P, Q, x, y, z, rv, rm = bad[0]
        print(f'  first: P {trits(*P, n)} x {x:0{n}b}, Q {trits(*Q, n)}'
              f' y {y:0{n}b}: z {z:0{n}b} is not in R {trits(rv, rm, n)}')


def prove(n):
    from z3 import BitVecs, Solver, sat
    pv, pm, qv, qm, x, y = BitVecs('pv pm qv qm x y', n)
    rv, rm = op(pv, pm, qv, qm)
    z = concrete(x, y)
    s = Solver()
    s.add(pv & pm == 0, qv & qm == 0)
    s.add(x & ~pm == pv, y & ~qm == qv)
    s.add(z & ~rm != rv)
    t0 = time.perf_counter()
    r = s.check()
    print(f'prove, {n} bits: {r} in {time.perf_counter() - t0:.3f} s')
    if r == sat:
        md = s.model()
        k = lambda e: md.eval(e, model_completion=True).as_long()
        print(f'  P {trits(k(pv), k(pm), n)}  x {k(x):0{n}b}')
        print(f'  Q {trits(k(qv), k(qm), n)}  y {k(y):0{n}b}')
        print(f'  R {trits(k(rv), k(rm), n)}  z {k(z):0{n}b}')


mode = sys.argv[1] if len(sys.argv) > 1 else 'check'
bits = int(sys.argv[2]) if len(sys.argv) > 2 else (4 if mode == 'check' else 64)
{'check': check, 'prove': prove}[mode](bits)
