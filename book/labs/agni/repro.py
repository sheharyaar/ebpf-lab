#!/usr/bin/env python3
"""Agni's verdict on BPF_AND, re-derived by hand with Z3.

    $PY -I book/labs/agni/repro.py 5.12            # refined spec (sro)
    $PY -I book/labs/agni/repro.py 5.13
    $PY -I book/labs/agni/repro.py 5.13 --gen      # general spec (gen)
    $PY -I book/labs/agni/repro.py 6.9 --modular   # no tail (SAS 2024)
    $PY -I book/labs/agni/repro.py 6.10 --modular
    $PY -I book/labs/agni/repro.py 5.12 --synth    # build a program
    $PY -I book/labs/agni/repro.py 5.12 --size     # size of the query
Add --small to keep every number below 2^34 (16 below for 32-bit bounds),
and --timeout=MS to give each query a time limit in milliseconds.

The operator is the verifier's 64-bit AND of two scalar registers, as
adjust_scalar_min_max_vals() runs it: the taint check on the source,
tnum_and(), scalar32_min_max_and(), scalar_min_max_and(), then the
shared tail __update_reg_bounds(), __reg_deduce_bounds() and
__reg_bound_offset() (kernel/bpf/verifier.c, tnum.c).  A register is
the five abstract values Agni checks: the tnum, u64, s64, u32, s32.

Kernels:  5.12  verifier.c of v5.12: scalar32_min_max_and() returns
                early when both low halves are known (CVE-2021-3490)
          5.13  after commit 049c4e13714e: it marks the low half known
          6.9   the two AND functions as in 5.13 (only with --modular)
          6.10  after commit 1f586614f3ff: signed bounds are copied from
                unsigned ones only when they do not cross the sign
                boundary (only with --modular)
The shared tail is the same in v5.12 and v5.13; 6.9 and 6.10 have a
larger reg_bounds_sync(), which this script does not encode.

Specifications, from Agni (CAV 2023, Equations 2 and 4):
  gen      x in each input's five values -> x & y in each output's
  sro      the same, with each input first passed through the tail
  modular  gen, for the operator with its tail removed (SAS 2024, Eq. 3)
One query per domain: Z3 looks for x, y and inputs that put x & y
outside that domain of the output; unsat is a proof at 64 bits.

Run from the repository root; PY is book/.venv/bin/python (Z3 5.4.1).
"""
import sys, time
from z3 import (BitVec, BitVecVal, Extract, ZeroExt, If, And, Or, Not,
                ULE, ULT, UGT, Solver, sat, unsat)

KERNELS = ('5.12', '5.13', '6.9', '6.10')
DOMAINS = ('u64', 's64', 'tnum', 'u32', 's32')
U64_MAX = BitVecVal(2**64 - 1, 64)
S64_MIN = BitVecVal(2**63, 64)
S64_MAX = BitVecVal(2**63 - 1, 64)
U32_MAX = BitVecVal(2**32 - 1, 32)
S32_MIN = BitVecVal(2**31, 32)
S32_MAX = BitVecVal(2**31 - 1, 32)
LO32 = BitVecVal(2**32 - 1, 64)
FIELDS = ('v', 'm', 'smin', 'smax', 'umin', 'umax',
          's32min', 's32max', 'u32min', 'u32max')


def lo(e): return Extract(31, 0, e)
def umin(a, b): return If(ULT(a, b), a, b)
def umax(a, b): return If(UGT(a, b), a, b)
def smin(a, b): return If(a < b, a, b)       # < on bit-vectors is signed
def smax(a, b): return If(a > b, a, b)


class Reg:
    """struct bpf_reg_state, the fields value tracking uses."""
    def __init__(self, name=None, **kw):
        for f in FIELDS:
            w = 32 if f.startswith(('s32', 'u32')) else 64
            setattr(self, f, kw[f] if f in kw else BitVec(f'{name}.{f}', w))

    def but(self, **kw):                      # a copy with some fields set
        return Reg(**{f: kw.get(f, getattr(self, f)) for f in FIELDS})


def select(c, a, b):                          # if (c) a else b, per field
    return Reg(**{f: If(c, getattr(a, f), getattr(b, f)) for f in FIELDS})


def unknown():                                # __mark_reg_unknown()
    return Reg(v=BitVecVal(0, 64), m=U64_MAX, smin=S64_MIN, smax=S64_MAX,
               umin=BitVecVal(0, 64), umax=U64_MAX, s32min=S32_MIN,
               s32max=S32_MAX, u32min=BitVecVal(0, 32), u32max=U32_MAX)


def known(imm):                               # ___mark_reg_known()
    return Reg(v=imm, m=BitVecVal(0, 64), smin=imm, smax=imm, umin=imm,
               umax=imm, s32min=lo(imm), s32max=lo(imm), u32min=lo(imm),
               u32max=lo(imm))


# ---- kernel/bpf/tnum.c, v5.13 ----------------------------------------
def tnum_and(av, am, bv, bm):                 # line 86
    alpha, beta, v = av | am, bv | bm, av & bv
    return v, alpha & beta & ~v


def tnum_or(av, am, bv, bm):                  # line 96
    v = av | bv
    return v, (am | bm) & ~v


def tnum_intersect(av, am, bv, bm):           # line 141
    v, mu = av | bv, am & bm
    return v & ~mu, mu


def fls64(x):                                 # 1 + index of the top 1 bit
    r = BitVecVal(0, 64)
    for i in range(64):
        r = If(Extract(i, i, x) == 1, BitVecVal(i + 1, 64), r)
    return r


def tnum_range(lo_, hi_):                     # line 21
    bits = fls64(lo_ ^ hi_)
    delta = (BitVecVal(1, 64) << bits) - 1
    return (If(UGT(bits, 63), BitVecVal(0, 64), lo_ & ~delta),
            If(UGT(bits, 63), U64_MAX, delta))


def clear_subreg(v, m):                       # tnum_clear_subreg()
    return v & ~LO32, m & ~LO32


# ---- the shared tail, verifier.c of v5.12 and v5.13 -------------------
def update_reg32_bounds(r):                   # v5.13 line 1225
    v32, m32 = lo(r.v), lo(r.m)
    return r.but(s32min=smax(r.s32min, v32 | (m32 & S32_MIN)),
                 s32max=smin(r.s32max, v32 | (m32 & S32_MAX)),
                 u32min=umax(r.u32min, v32),
                 u32max=umin(r.u32max, v32 | m32))


def update_reg64_bounds(r):                   # line 1240
    return r.but(smin=smax(r.smin, r.v | (r.m & S64_MIN)),
                 smax=smin(r.smax, r.v | (r.m & S64_MAX)),
                 umin=umax(r.umin, r.v),
                 umax=umin(r.umax, r.v | r.m))


def update_reg_bounds(r):                     # line 1253
    return update_reg64_bounds(update_reg32_bounds(r))


def deduce(lo_s, hi_s, lo_u, hi_u, zero):     # __reg{32,64}_deduce_bounds
    same = Or(lo_s >= zero, hi_s < zero)      # cannot cross the sign
    a, b = umax(lo_s, lo_u), umin(hi_s, hi_u)
    pos = hi_u >= zero                        # (s)umax >= 0
    neg = lo_u < zero                         # (s)umin < 0
    m = umin(hi_s, hi_u)
    return (If(same, a, If(pos, lo_u, If(neg, a, lo_s))),
            If(same, b, If(pos, m, If(neg, hi_u, hi_s))),
            If(same, a, If(pos, lo_u, If(neg, a, lo_u))),
            If(same, b, If(pos, m, hi_u)))


def reg_deduce_bounds(r):                     # lines 1260, 1294, 1328
    s0, s1, u0, u1 = deduce(r.s32min, r.s32max, r.u32min, r.u32max,
                            BitVecVal(0, 32))
    r = r.but(s32min=s0, s32max=s1, u32min=u0, u32max=u1)
    s0, s1, u0, u1 = deduce(r.smin, r.smax, r.umin, r.umax,
                            BitVecVal(0, 64))
    return r.but(smin=s0, smax=s1, umin=u0, umax=u1)


def reg_bound_offset(r):                      # line 1335
    v64 = tnum_intersect(r.v, r.m, *tnum_range(r.umin, r.umax))
    v32 = tnum_intersect(r.v & LO32, r.m & LO32,
                         *tnum_range(ZeroExt(32, r.u32min),
                                     ZeroExt(32, r.u32max)))
    v, m = tnum_or(*clear_subreg(*v64), *v32)
    return r.but(v=v, m=m)


def tail(r):                                  # Agni's BPF_SYNC for 5.x
    return reg_bound_offset(reg_deduce_bounds(update_reg_bounds(r)))


# ---- the operator ------------------------------------------------------
def scalar32_and(d, s, k):                    # v5.13 line 7123
    both = And(lo(s.m) == 0, lo(d.m) == 0)
    v32 = lo(d.v)
    if k == '5.12':                           # v5.12 line 6532
        kept = d                              # return: bounds unchanged
    else:                                     # __mark_reg32_known()
        v, m = tnum_or(*clear_subreg(d.v, d.m), ZeroExt(32, v32),
                       BitVecVal(0, 64))
        kept = d.but(v=v, m=m, s32min=v32, s32max=v32, u32min=v32,
                     u32max=v32)
    n = d.but(u32min=v32, u32max=umin(d.u32max, s.u32max))
    if k == '6.10':                           # commit 1f586614f3ff
        ok = n.u32min <= n.u32max             # (s32) casts: signed <=
    else:
        ok = Not(Or(d.s32min < 0, s.s32min < 0))
    n = n.but(s32min=If(ok, n.u32min, S32_MIN),
              s32max=If(ok, n.u32max, S32_MAX))
    return select(both, kept, n)


def scalar64_and(d, s, k):                    # v5.13 line 7157
    both = And(s.m == 0, d.m == 0)
    n = d.but(umin=d.v, umax=umin(d.umax, s.umax))
    if k == '6.10':
        ok = n.umin <= n.umax
    else:
        ok = Not(Or(d.smin < 0, s.smin < 0))
    n = n.but(smin=If(ok, n.umin, S64_MIN), smax=If(ok, n.umax, S64_MAX))
    return select(both, known(d.v), update_reg_bounds(n))


def bpf_and(d, s, k, with_tail=True):        # adjust_scalar_min_max_vals()
    v, m = tnum_and(d.v, d.m, s.v, s.m)
    r = scalar64_and(scalar32_and(d.but(v=v, m=m), s, k), s, k)
    if with_tail:
        r = tail(r)
    if k == '6.10':                           # is_safe_to_compute_...()
        return r                              # is true for AND
    taint = Or(And(s.m == 0, Or(s.smin != s.smax, s.umin != s.umax)),
               s.smin > s.smax, UGT(s.umin, s.umax))
    return select(taint, unknown(), r)


# ---- membership: is x one of the values each domain allows? -------------
def member(x, r):
    return {'u64': And(ULE(r.umin, x), ULE(x, r.umax)),
            's64': And(r.smin <= x, x <= r.smax),
            'tnum': And(x & ~r.m == r.v, r.v & r.m == 0),
            'u32': And(ULE(r.u32min, lo(x)), ULE(lo(x), r.u32max)),
            's32': And(r.s32min <= lo(x), lo(x) <= r.s32max)}


def inside(x, r):
    return And(*member(x, r).values())


# ---- one verdict per domain --------------------------------------------
def small(r, x):                              # --small: easier to read
    return [ULT(e, 2**34) for e in (x, r.v, r.m, r.umin, r.umax, r.smin,
                                    r.smax)] + \
           [ULT(e, 16) for e in (r.u32min, r.u32max, r.s32min, r.s32max)]


def query(k, spec):
    a, b = Reg('dst'), Reg('src')
    x, y = BitVec('x', 64), BitVec('y', 64)
    pre = small(a, x) + small(b, y) if SMALL else []
    if spec == 'sro':                         # Equation 4: inputs synced
        a, b = tail(a), tail(b)
    out = bpf_and(a, b, k, with_tail=(spec != 'modular'))
    pre += [inside(x, a), inside(y, b)]
    return pre, member(x & y, out), (a, b, out, x, y)


def show(md, name, r):
    ev = lambda e: md.eval(e, model_completion=True).as_long()
    s64 = lambda e: ev(e) - (1 << 64) * (ev(e) >> 63)
    s32 = lambda e: ev(e) - (1 << 32) * (ev(e) >> 31)
    print(f'  {name}: var_off=({ev(r.v):#x}; {ev(r.m):#x})')
    print(f'     u64=[{ev(r.umin):#x}, {ev(r.umax):#x}]')
    print(f'     s64=[{s64(r.smin)}, {s64(r.smax)}]')
    print(f'     u32=[{ev(r.u32min):#x}, {ev(r.u32max):#x}]'
          f' s32=[{s32(r.s32min)}, {s32(r.s32max)}]')


def verify(k, spec):
    pre, post, regs = query(k, spec)
    rows, first = [], None
    for d in DOMAINS:
        s = Solver()
        if TIMEOUT:
            s.set('timeout', TIMEOUT)         # milliseconds, per query
        s.add(*pre)
        s.add(Not(post[d]))
        t = time.perf_counter()
        ans = s.check()
        rows.append((d, ans, time.perf_counter() - t))
        if ans == sat and first is None:
            first = (d, s.model())
    print(f'BPF_AND {k} {spec}: ' + ', '.join(
        f'{d} {"ok" if a == unsat else "VIOLATED" if a == sat else a}'
        for d, a, _ in rows))
    print(f'  {sum(t for *_, t in rows):.2f} s for five queries, '
          + ' '.join(f'{t:.2f}' for *_, t in rows))
    if first:
        d, md = first
        a, b, out, x, y = regs
        ev = lambda e: md.eval(e, model_completion=True).as_long()
        print(f'counterexample for {d}:')
        print(f'  x = {ev(x):#x}, y = {ev(y):#x}')
        print(f'  x & y = {ev(x & y):#x}')
        show(md, 'dst', a)
        show(md, 'src', b)
        show(md, 'out', out)


# ---- differential synthesis on a small scale (CAV 2023, Sec. 4.3) ------
def init(r, x):                               # a constant or unknown
    unk = unknown()
    return Or(And(*[getattr(r, f) == getattr(known(x), f) for f in FIELDS]),
              And(*[getattr(r, f) == getattr(unk, f) for f in FIELDS]))


def synth(k, length):
    """Look for AND instructions on registers that start as constants or
    unknowns, the last of which leaves x & y outside its result."""
    regs, vals, pre = [], [], []
    for i in range(2):                        # two starting registers
        r, x = Reg(f'r{i}'), BitVec(f'x{i}', 64)
        pre += [init(r, x)] + ([ULT(x, 2**34)] if SMALL else [])
        regs.append(r)
        vals.append(x)
    picks = []
    for step in range(length):
        sel = [BitVec(f'pick{step}{j}', 8) for j in (0, 1)]
        ops = []
        for j, sv in enumerate(sel):          # each operand: any register
            n = len(regs)                     # so far, or a new constant
            pre.append(ULE(sv, n))
            c = BitVec(f'c{step}{j}', 64)
            if SMALL:
                pre.append(ULT(c, 2**34))
            r, x = known(c), c
            for i in range(n):
                r = select(sv == i, regs[i], r)
                x = If(sv == i, vals[i], x)
            ops.append((r, x))
        picks.append(sel)
        (d, x), (s, y) = ops
        out = bpf_and(d, s, k)
        z = x & y
        if step < length - 1:
            pre.append(inside(z, out))
        regs.append(out)
        vals.append(z)
    sol = Solver()
    sol.add(*pre)
    sol.add(Not(inside(vals[-1], regs[-1])))
    t = time.perf_counter()
    ans = sol.check()
    dt = time.perf_counter() - t
    print(f'synthesis {k}, {length} instruction(s): {ans} in {dt:.2f} s')
    if ans == sat:
        md = sol.model()
        ev = lambda e: md.eval(e, model_completion=True).as_long()
        for i in range(2):
            unk = ev(regs[i].m) == 2**64 - 1
            print(f'  r{i} = ' + ('unknown' if unk else f'{ev(vals[i]):#x}')
                  + f'        ; runs with {ev(vals[i]):#x}')
        for step, sel in enumerate(picks):
            names = []
            for j, sv in enumerate(sel):
                p = ev(sv)
                names.append(f'r{p}' if p < 2 + step else
                             f'{ev(BitVec(f"c{step}{j}", 64)):#x}')
            print(f'  r{2 + step} = {names[0]} & {names[1]}'
                  f'      ; = {ev(vals[2 + step]):#x}')
        show(md, f'r{1 + length}', regs[-1])


def size(k):
    pre, post, _ = query(k, 'sro')
    s = Solver()
    s.add(*pre)
    s.add(Not(And(*post.values())))
    text = s.to_smt2()
    print(f'{k} sro, five domains: '
          f'{len(text):,} bytes, {text.count(chr(10)):,} lines of SMT-LIB')


SMALL = '--small' in sys.argv
TIMEOUT = next((int(a.split('=')[1]) for a in sys.argv
                if a.startswith('--timeout=')), 0)


def main(argv):
    k = next((a for a in argv if a in KERNELS), '5.12')
    if '--synth' in argv:
        for n in (1, 2):
            synth(k, n)
        return
    if '--size' in argv:
        return size(k)
    spec = ('gen' if '--gen' in argv else
            'modular' if '--modular' in argv else 'sro')
    if k in ('6.9', '6.10') and spec != 'modular':
        sys.exit(f'{k}: only --modular; its reg_bounds_sync() is not '
                 'encoded here')
    verify(k, spec)


if __name__ == '__main__':
    main(sys.argv[1:])
