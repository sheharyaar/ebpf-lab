#!/usr/bin/env python3
"""CVE-2021-3490: the verifier's 32-bit bounds for AND, OR and XOR, asked of Z3.

    $PY -I book/labs/proof/cve.py             # and, or, xor; 3 kernels
    $PY -I book/labs/proof/cve.py and         # one operation
    $PY -I book/labs/proof/cve.py and --small # a small counterexample
    $PY -I book/labs/proof/cve.py --example   # the fixing commit's case
    $PY -I book/labs/proof/cve.py and --zext  # pitfalls: unfaithful
    $PY -I book/labs/proof/cve.py and --usign #   encodings, and a
    $PY -I book/labs/proof/cve.py and --unsynced  # missing invariant
    $PY -I book/labs/proof/cve.py and --known --no64  # stopped too soon

The property: for every pair of registers the verifier could describe, and
every pair of values inside those descriptions, the low 32 bits of the
result lie inside the 32-bit bounds the kernel computes.  Z3 is given the
negation; sat is a counterexample, unsat a proof at this width.

Kernels:  5.10  scalar32_min_max_{and,or,xor}(), kernel/bpf/verifier.c of
                v5.10 (lines 5871, 5942, 6012): the bug, from 5.7 (5.10
                for XOR) until 5.13-rc4
          5.13  the same functions after commit 049c4e13714e (May 2021)
          7.2   verifier.c of v7.2 (lines 14161, 14205, 14249), where the
                32-bit range is one circular range, struct cnum32
The tnum operations are the same in all three (kernel/bpf/tnum.c).

Run from the repository root; PY is book/.venv/bin/python (Z3 5.4.1).
"""
import sys, time
from z3 import (BitVec, BitVecVal, Extract, ZeroExt, If, And, Or, Not,
                ULE, ULT, UGT, LShR, Solver, Optimize, sat, simplify)

U32_MAX = BitVecVal(0xffffffff, 32)
S32_MIN = BitVecVal(0x80000000, 32)        # -2^31 as 32 bits
S32_MAX = BitVecVal(0x7fffffff, 32)
ZEXT = '--zext' in sys.argv                # pitfall: compare all 64 bits
USIGN = '--usign' in sys.argv              # pitfall: s32 bounds tested unsigned
SYNCED = '--unsynced' not in sys.argv      # pitfall: drop the invariants
SMALL = '--small' in sys.argv              # smallest x, y; tight bounds
NO64 = '--no64' in sys.argv                # pitfall: stop before scalar_<op>()
KNOWN = '--known' in sys.argv              # only registers known in all 64 bits


def lo32(e):
    return Extract(31, 0, e)


def umin(a, b): return If(ULT(a, b), a, b)
def umax(a, b): return If(UGT(a, b), a, b)
def smin(a, b): return If(a < b, a, b)     # < on bit-vectors is signed
def smax(a, b): return If(a > b, a, b)


TNUM = {                                   # kernel/bpf/tnum.c:92, 102, 111
    'and': lambda av, am, bv, bm: (av & bv,
                                   (av | am) & (bv | bm) & ~(av & bv)),
    'or':  lambda av, am, bv, bm: (av | bv, (am | bm) & ~(av | bv)),
    'xor': lambda av, am, bv, bm: ((av ^ bv) & ~(am | bm), am | bm),
}
CONC = {'and': lambda x, y: x & y, 'or': lambda x, y: x | y,
        'xor': lambda x, y: x ^ y}


# ------------------------------------------------ 5.10 and 5.13: four bounds
class Reg4:
    def __init__(self, name):
        self.v, self.m = BitVec(name + '.v', 64), BitVec(name + '.m', 64)
        self.b = [BitVec(f'{name}.{k}', 32)
                  for k in ('s32_min', 's32_max', 'u32_min', 'u32_max')]

    def holds(self, x):                    # x is in the tnum and the bounds
        s_lo, s_hi, u_lo, u_hi = self.b
        w = lo32(x)
        return And(self.v & self.m == 0, x & ~self.m == self.v,
                   s_lo <= w, w <= s_hi, ULE(u_lo, w), ULE(w, u_hi),
                   tidy(self.b, lo32(self.v), lo32(self.m)) if SYNCED
                   else True)


def tidy(b, v32, m32):
    """Two rules the verifier's tidy-up after every arithmetic step leaves
    true (v5.10 verifier.c:6434-6436).  __reg32_deduce_bounds() (:1165): if
    either range stays on one side of the sign boundary, the signed and
    unsigned 32-bit ranges are the same.  __reg_bound_offset() (:1240): the
    low half of the tnum lies inside tnum_range(u32_min, u32_max)."""
    s_lo, s_hi, u_lo, u_hi = b
    one_side = Or(s_lo >= 0, s_hi < 0, u_hi >= 0, u_lo < 0)  # signed tests
    chi = u_lo ^ u_hi                      # tnum_range(), tnum.c: the bits
    for k in (1, 2, 4, 8, 16):             # from the highest one that
        chi = chi | LShR(chi, k)           # differs downwards are unknown
    return And(If(one_side, And(s_lo == u_lo, s_hi == u_hi), True),
               m32 & ~chi == 0, v32 & ~chi == u_lo & ~chi)


def bounds_v510(op, d_b, s_b, v32, m32, src_known, fixed):
    """scalar32_min_max_<op>() of v5.10; with fixed, after 049c4e13714e.
    v32, m32 are tnum_subreg(dst->var_off), which already holds the result."""
    d_smin, d_smax, d_umin, d_umax = d_b
    s_smin, s_smax, s_umin, s_umax = s_b
    if op == 'and':                        # verifier.c:5889-5903
        lo, hi = v32, umin(d_umax, s_umax)
    elif op == 'or':                       # verifier.c:5960-5974
        lo, hi = umax(d_umin, s_umin), v32 | m32
    else:                                  # verifier.c:6027-6039
        lo, hi = v32, v32 | m32
    neg = Or(d_smin < 0, s_smin < 0)       # "Lose signed bounds"
    new = [If(neg, S32_MIN, lo), If(neg, S32_MAX, hi), lo, hi]
    both = And(src_known, m32 == 0)        # src_known && dst_known
    kept = [v32] * 4 if fixed else list(d_b)  # mark known : return
    return [If(both, k, n) for k, n in zip(kept, new)]


def after_64bit(b, rv, rm, s_m):
    """scalar_<op>() runs next (v5.10 verifier.c:5907, 5977, 6042): if
    both whole registers are known, __mark_reg_known() resets the 32-bit
    bounds too (:1014).  Only then was the comment's assumption true."""
    whole = And(s_m == 0, rm == 0)
    return [If(whole, lo32(rv), e) for e in b]


def update_reg32_bounds(b, v32, m32):      # __update_reg32_bounds(), :1130
    s_lo, s_hi, u_lo, u_hi = b
    return [smax(s_lo, v32 | (m32 & S32_MIN)),
            smin(s_hi, v32 | (m32 & S32_MAX)),
            umax(u_lo, v32), umin(u_hi, v32 | m32)]


def inside4(b, z):
    s_lo, s_hi, u_lo, u_hi = b
    if ZEXT:                               # wrong: the 64-bit result itself
        w, s_lo, s_hi = z, ZeroExt(32, s_lo), ZeroExt(32, s_hi)
        u_lo, u_hi = ZeroExt(32, u_lo), ZeroExt(32, u_hi)
    else:
        w = lo32(z)
    if USIGN:                              # wrong: signed bounds, unsigned test
        return And(ULE(s_lo, w), ULE(w, s_hi), ULE(u_lo, w), ULE(w, u_hi))
    return And(s_lo <= w, w <= s_hi, ULE(u_lo, w), ULE(w, u_hi))


# ------------------------------------------------ 7.2: one circular range
class RegC:
    def __init__(self, name):
        self.v, self.m = BitVec(name + '.v', 64), BitVec(name + '.m', 64)
        self.base = BitVec(name + '.base', 32)
        self.size = BitVec(name + '.size', 32)

    def holds(self, x):
        return And(self.v & self.m == 0, x & ~self.m == self.v,
                   ULE(lo32(x) - self.base, self.size))


def c_umin(base, size):                    # cnum32_umin(), cnum_defs.h:48
    return If(UGT(size, U32_MAX - base), BitVecVal(0, 32), base)


def c_umax(base, size):                    # cnum32_umax(), cnum_defs.h:54
    return If(UGT(size, U32_MAX - base), U32_MAX, base + size)


def range_v72(op, d, s, v32, m32, src_known):
    """scalar32_min_max_<op>() of v7.2; returns cnum32_from_urange(lo, hi)."""
    if op == 'and':
        lo, hi = v32, umin(c_umax(d.base, d.size), c_umax(s.base, s.size))
    elif op == 'or':
        lo = umax(c_umin(d.base, d.size), c_umin(s.base, s.size))
        hi = v32 | m32
    else:
        lo, hi = v32, v32 | m32
    known = And(src_known, m32 == 0)       # then __mark_reg32_known()
    return If(known, v32, lo), If(known, BitVecVal(0, 32), hi - lo)


# ------------------------------------------------ the queries
def query(op, kernel):
    x, y = BitVec('x', 64), BitVec('y', 64)
    if kernel == '7.2':
        d, s = RegC('dst'), RegC('src')
    else:
        d, s = Reg4('dst'), Reg4('src')
    rv, rm = TNUM[op](d.v, d.m, s.v, s.m)  # dst->var_off = tnum_<op>(...)
    v32, m32 = lo32(rv), lo32(rm)
    src_known = lo32(s.m) == 0             # tnum_subreg_is_const(src)
    z = CONC[op](x, y)
    so = Optimize() if SMALL else Solver()
    so.add(d.holds(x), s.holds(y))
    if KNOWN:
        so.add(d.m == 0, s.m == 0)
    if kernel == '7.2':
        base, size = range_v72(op, d, s, v32, m32, src_known)
        so.add(Not(ULE(lo32(z) - base, size)))
        out = [base, size]
    else:
        out = bounds_v510(op, d.b, s.b, v32, m32, src_known,
                          kernel == '5.13')
        out = out if NO64 else after_64bit(out, rv, rm, s.m)
        so.add(Not(inside4(out, z)))
    if SMALL:                              # easy numbers, not a weaker claim
        if kernel != '7.2':
            for r in (d, s):               # bounds as tight as the tnum allows
                so.add(And([a == b for a, b in zip(r.b, update_reg32_bounds(
                    r.b, lo32(r.v), lo32(r.m)))]))
        so.minimize(x), so.minimize(y), so.minimize(d.m), so.minimize(s.m)
    t = time.perf_counter()
    ans = so.check()
    print(f'{op:3} {kernel:4} {ans} in {time.perf_counter() - t:.2f} s')
    if ans == sat:
        md = so.model()
        def h(e, w=16):
            k = md.eval(e, model_completion=True).as_long()
            return f'{k:#0{w + 2}x}'
        print(f'      dst var_off=({h(d.v)}; {h(d.m)})  x={h(x)}')
        print(f'      src var_off=({h(s.v)}; {h(s.m)})  y={h(y)}')
        if kernel != '7.2':
            print('      dst 32-bit bounds before: s32 [%s, %s] u32 [%s, %s]'
                  % tuple(h(e, 8) for e in d.b))
            print('      computed by the kernel:   s32 [%s, %s] u32 [%s, %s]'
                  % tuple(h(e, 8) for e in out))
            print('      after __update_reg32_bounds: s32 [%s, %s] u32 [%s, %s]'
                  % tuple(h(e, 8) for e in update_reg32_bounds(out, v32, m32)))
        print(f'      the real result, low 32 bits: {h(lo32(z), 8)}')


def example():
    """The fixing commit's case: R2 = (0x1; 0xffffffff00000000), all four
    32-bit bounds 1; R3 = 0x100000002, all four 2; then r2 &= r3."""
    c = lambda k: BitVecVal(k, 32)
    v32, m32, known = c(1 & 2), c(0), True  # low half of tnum_and(): 0, known
    for fixed, name in ((False, '5.10'), (True, '5.13')):
        b = bounds_v510('and', [c(1)] * 4, [c(2)] * 4, v32, m32, known, fixed)
        a = update_reg32_bounds(b, v32, m32)
        f = lambda bs: ', '.join(str(simplify(e).as_signed_long()) for e in bs)
        print(f'{name}: s32_min, s32_max, u32_min, u32_max = {f(b)}')
        print(f'      after __update_reg32_bounds(): {f(a)}')

    class R:                               # R2 and R3 as circular ranges
        def __init__(self, k): self.base, self.size = c(k), c(0)
    base, size = (simplify(e).as_long() for e in
                  range_v72('and', R(1), R(2), v32, m32, known))
    print(f'7.2:  r32 = cnum32 {{base {base}, size {size}}}: the value {base}')


if '--example' in sys.argv:
    example()
else:
    ops = [a for a in sys.argv[1:] if a in TNUM] or ['and', 'or', 'xor']
    for op in ops:
        for kernel in ('5.10', '5.13', '7.2'):
            query(op, kernel)
