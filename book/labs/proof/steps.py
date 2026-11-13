#!/usr/bin/env python3
"""Check each step of the hand proof that tnum_and() is sound, case by case.

    python3 -I book/labs/proof/steps.py [BITS]

Every well-formed P and Q of BITS bits (4 unless given), every x in P and
every y in Q: one case each.  For each step of the proof the script counts
the cases in which the step's claim holds.  The last line is a tempting
claim that is false, to show what a failing step looks like.  Plain Python.
"""
import sys

N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
M = (1 << N) - 1


def sub(a, b):              # a ⊑ b: every bit set in a is set in b
    return a & ~b & M == 0


def members(v, m):          # gamma(P): x with x & ~m == v
    return [x for x in range(M + 1) if x & ~m & M == v]


tnums = [(v, m) for m in range(M + 1) for v in range(M + 1) if v & m == 0]
steps = [
    ('1', 'P.v ⊑ x and Q.v ⊑ y',
     lambda P, Q, x, y, a, b, v, m: sub(P[0], x) and sub(Q[0], y)),
    ('2', 'x ⊑ α and y ⊑ β',
     lambda P, Q, x, y, a, b, v, m: sub(x, a) and sub(y, b)),
    ('3', 'v ⊑ x & y',
     lambda P, Q, x, y, a, b, v, m: sub(v, x & y)),
    ('4', 'x & y ⊑ α & β',
     lambda P, Q, x, y, a, b, v, m: sub(x & y, a & b)),
    ('5', '(x & y) & ~m == v',
     lambda P, Q, x, y, a, b, v, m: (x & y) & ~m & M == v),
    ('6', 'v & m == 0',
     lambda P, Q, x, y, a, b, v, m: v & m == 0),
    ('no', 'x & y ⊑ v | (P.m & Q.m)',
     lambda P, Q, x, y, a, b, v, m: sub(x & y, v | (P[1] & Q[1]))),
]
held = [0] * len(steps)
cases = 0
for P in tnums:
    for Q in tnums:
        a, b = P[0] | P[1], Q[0] | Q[1]          # alpha, beta
        v = P[0] & Q[0]
        m = a & b & ~v & M                       # tnum_and(), tnum.c:92
        for x in members(*P):
            for y in members(*Q):
                cases += 1
                for i, (_, _, claim) in enumerate(steps):
                    held[i] += claim(P, Q, x, y, a, b, v, m)
print(f'{N} bits: {len(tnums)} tnums, {cases:,} cases (P, x, Q, y)')
for (k, text, _), h in zip(steps, held):
    print(f'  step {k:3} {text:26} holds in {h:,}, fails in {cases - h:,}')
