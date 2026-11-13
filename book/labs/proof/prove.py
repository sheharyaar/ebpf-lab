#!/usr/bin/env python3
"""Ask Z3 whether a tnum operation is sound at one width.

    $PY -I book/labs/proof/prove.py OP [BITS]

OP is and, add or and-broken; BITS is 64 unless given.  unsat means
no counterexample exists at that width; sat prints one.

Run from the repository root; PY is book/.venv/bin/python (Z3 5.4.1).
"""
import sys, time
from z3 import BitVecs, Solver, sat

def tnum_and(pv, pm, qv, qm):         # kernel/bpf/tnum.c:92, Linux v7.2
    alpha = pv | pm
    beta = qv | qm
    v = pv & qv
    return v, alpha & beta & ~v

def tnum_and_broken(pv, pm, qv, qm):  # alpha forgets P's unknown bits
    alpha = pv
    beta = qv | qm
    v = pv & qv
    return v, alpha & beta & ~v

def tnum_add(pv, pm, qv, qm):         # kernel/bpf/tnum.c:63, Linux v7.2
    sm, sv = pm + qm, pv + qv
    mu = ((sm + sv) ^ sv) | pm | qm
    return sv & ~mu, mu

OPS = {'and': (tnum_and, lambda x, y: x & y),
       'and-broken': (tnum_and_broken, lambda x, y: x & y),
       'add': (tnum_add, lambda x, y: x + y)}

def trits(v, m, n):                   # a tnum written bit by bit: 0, 1, x
    return ''.join('x' if m >> i & 1 else str(v >> i & 1)
                   for i in reversed(range(n)))

name = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 64
op, concrete = OPS[name]
pv, pm, qv, qm, x, y = BitVecs('pv pm qv qm x y', n)
rv, rm = op(pv, pm, qv, qm)
z = concrete(x, y)
s = Solver()
s.add(pv & pm == 0, qv & qm == 0)     # P and Q are well-formed
s.add(x & ~pm == pv, y & ~qm == qv)   # x is in P and y is in Q
s.add(z & ~rm != rv)                  # ... and z = x op y is not in R
t = time.perf_counter()
answer = s.check()
dt = time.perf_counter() - t
mb = s.statistics().get_key_value('max memory')
print(f'{name}, {n} bits: {answer} in {dt:.3f} s, Z3 at most {mb:.1f} MB')
if answer == sat:                     # the model is a counterexample
    md = s.model()
    val = lambda e: md.eval(e, model_completion=True).as_long()
    print('  P', trits(val(pv), val(pm), n), '  x', f'{val(x):0{n}b}')
    print('  Q', trits(val(qv), val(qm), n), '  y', f'{val(y):0{n}b}')
    print('  R', trits(val(rv), val(rm), n), '  z', f'{val(z):0{n}b}')
