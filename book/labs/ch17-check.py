#!/usr/bin/env python3
"""Chapter 17: try every pair of small abstract values for one abstract operation.

    python3 book/labs/ch17-check.py                  # list the operations
    python3 book/labs/ch17-check.py tnum_add iv_add  # check them on 4 bits
    python3 book/labs/ch17-check.py --bits 6 tnum_add
    python3 book/labs/ch17-check.py rounds           # a loop analysed with and without widening
    python3 book/labs/ch17-check.py query            # Figure 17.5's query, tried case by case

For every pair of abstract inputs (A, B) the checker builds the concrete results
{x op y | x in gamma(A), y in gamma(B)} and reports every pair where one of them
falls outside gamma(op#(A, B)): a counterexample to soundness.  It also counts the
pairs where the result is sound but wider than the best value of its kind (alpha of
the concrete set), which is a loss of precision, not a bug.

Plain Python, no solver.  The kernel operations are transcribed from Linux v7.2
(kernel/bpf/tnum.c, kernel/bpf/cnum_defs.h) with every result cut to N bits,
which is what the kernel's u64 arithmetic does at 64.
"""
import sys, time

N = 4
M = (1 << N) - 1


def setbits(n):
    global N, M
    N, M = n, (1 << n) - 1


# ---------------------------------------------------------------- tnums
# A tnum is (value, mask): a bit set in mask is unknown (x); value holds the known 1s.
def tnums():
    return [(v, m) for m in range(M + 1) for v in range(M + 1) if v & m == 0]


def gamma_t(t):
    v, m = t
    return {x for x in range(M + 1) if x & ~m & M == v}       # member(x, P) of the CGO'22 paper


def alpha_t(s):                                              # the smallest tnum holding every value in s
    s = sorted(s)
    m = 0
    for x in s:
        m |= x ^ s[0]
    return (s[0] & ~m & M, m)


def show_t(t):
    v, m = t
    return ''.join('x' if m >> i & 1 else str(v >> i & 1) for i in range(N - 1, -1, -1))


def T(v, m):
    return (v & M, m & M)


def tnum_add(a, b):                    # tnum.c:63
    sm = a[1] + b[1]
    sv = a[0] + b[0]
    sigma = sm + sv
    chi = sigma ^ sv
    mu = chi | a[1] | b[1]
    return T(sv & ~mu, mu)


def tnum_and(a, b):                    # tnum.c:92
    alpha = a[0] | a[1]
    beta = b[0] | b[1]
    v = a[0] & b[0]
    return T(v, alpha & beta & ~v)


def tnum_or(a, b):                     # tnum.c:102
    v = a[0] | b[0]
    mu = a[1] | b[1]
    return T(v, mu & ~v)


def tnum_union(a, b):                  # tnum.c:188, the join of two tnums
    v = a[0] & b[0]
    mu = (a[0] ^ b[0]) | a[1] | b[1]
    return T(v & ~mu, mu)


def tnum_mul(a, b):                    # tnum.c:137, since 2025 (commit 1df7dad4d5c4)
    acc = (0, 0)
    while a[0] or a[1]:
        if a[0] & 1:
            acc = tnum_add(acc, b)
        elif a[1] & 1:
            acc = tnum_union(acc, tnum_add(acc, b))
        a = (a[0] >> 1, a[1] >> 1)
        b = T(b[0] << 1, b[1] << 1)
    return acc


def tnum_mul_2021(a, b):               # the CGO'22 algorithm, commit 05924717ac70
    acc_v = a[0] * b[0]
    acc_m = (0, 0)
    while a[0] or a[1]:
        if a[0] & 1:
            acc_m = tnum_add(acc_m, (0, b[1]))
        elif a[1] & 1:
            acc_m = tnum_add(acc_m, (0, b[0] | b[1]))
        a = (a[0] >> 1, a[1] >> 1)
        b = T(b[0] << 1, b[1] << 1)
    return tnum_add(T(acc_v, 0), acc_m)


def tnum_add_nocarry(a, b):            # BROKEN: add the values, OR the masks, forget the carries
    mu = a[1] | b[1]
    return T((a[0] + b[0]) & ~mu, mu)


def tnum_and_both(a, b):               # BROKEN: a bit is unknown only if it is unknown in both inputs
    mu = a[1] & b[1]
    return T(a[0] & b[0] & ~mu, mu)


# ---------------------------------------------------------------- intervals
# An unsigned interval [lo, hi] with lo <= hi, on N bits.
def intervals():
    return [(lo, hi) for lo in range(M + 1) for hi in range(lo, M + 1)]


def gamma_i(i):
    return set(range(i[0], i[1] + 1))


def alpha_i(s):
    return (min(s), max(s))


def show_i(i):
    return f'[{i[0]}, {i[1]}]'


def iv_add(a, b):                      # sound: if the largest sum can wrap, give up and say anything
    lo, hi = a[0] + b[0], a[1] + b[1]
    return (lo, hi) if hi <= M else (0, M)


def iv_add_clamp(a, b):                # BROKEN: stops at the largest number instead of wrapping round
    return (min(a[0] + b[0], M), min(a[1] + b[1], M))


def iv_join(a, b):                     # the join of two intervals: the smallest one holding both
    return (min(a[0], b[0]), max(a[1], b[1]))


# ---------------------------------------------------------------- circular ranges (v7.2's cnum)
# (base, size): the size+1 values base, base+1, ... read round the circle; size M is the whole circle.
def arcs():
    return [(b, s) for s in range(M + 1) for b in range(M + 1) if s < M or b == 0]


def gamma_a(a):
    return {(a[0] + k) & M for k in range(a[1] + 1)}


def show_a(a):
    return f'arc({a[0]}, +{a[1]})'


def cnum_add(a, b):                    # cnum_defs.h:189, without the empty case
    if a[1] > M - b[1]:
        return (0, M)
    return ((a[0] + b[0]) & M, a[1] + b[1])


# ---------------------------------------------------------------- the registry
TN = (tnums, gamma_t, show_t, alpha_t)
IV = (intervals, gamma_i, show_i, alpha_i)
AR = (arcs, gamma_a, show_a, None)
ADD = lambda x, y: (x + y) & M
OPS = {
    'tnum_add':         (TN, tnum_add, ADD, '+', 'kernel/bpf/tnum.c, v7.2'),
    'tnum_and':         (TN, tnum_and, lambda x, y: x & y, '&', 'kernel/bpf/tnum.c, v7.2'),
    'tnum_or':          (TN, tnum_or, lambda x, y: x | y, '|', 'kernel/bpf/tnum.c, v7.2'),
    'tnum_mul':         (TN, tnum_mul, lambda x, y: (x * y) & M, '*', 'kernel/bpf/tnum.c, v7.2 (2025)'),
    'tnum_mul_2021':    (TN, tnum_mul_2021, lambda x, y: (x * y) & M, '*', 'CGO 2022, merged 2021'),
    'tnum_union':       (TN, tnum_union, None, 'join', 'kernel/bpf/tnum.c, v7.2'),
    'tnum_add_nocarry': (TN, tnum_add_nocarry, ADD, '+', 'broken on purpose'),
    'tnum_and_both':    (TN, tnum_and_both, lambda x, y: x & y, '&', 'broken on purpose'),
    'iv_add':           (IV, iv_add, ADD, '+', 'sound interval addition'),
    'iv_add_clamp':     (IV, iv_add_clamp, ADD, '+', 'broken on purpose'),
    'iv_join':          (IV, iv_join, None, 'join', 'the interval join'),
    'cnum_add':         (AR, cnum_add, ADD, '+', 'kernel/bpf/cnum_defs.h, v7.2'),
}


def check(name):
    (dom, gamma, show, alpha), op, conc, sym, origin = OPS[name]
    vals = dom()
    g = {a: gamma(a) for a in vals}
    t0 = time.perf_counter()
    pairs = work = 0
    bad, loose = [], 0
    for a in vals:
        for b in vals:
            pairs += 1
            r = op(a, b)
            gr = gamma(r)
            if conc is None:                     # a join: every value of either input
                real = g[a] | g[b]
                work += len(real)
            else:
                real = {conc(x, y) for x in g[a] for y in g[b]}
                work += len(g[a]) * len(g[b])
            miss = real - gr
            if miss:
                bad.append((a, b, r, min(miss)))
            elif alpha and gr != gamma(alpha(real)):
                loose += 1
    dt = time.perf_counter() - t0
    print(f'{name}  ({origin}), {N} bits')
    print(f'  {len(vals)} values, {pairs:,} pairs, {work:,} concrete results, {dt:.2f} s')
    print(f'  counterexamples: {len(bad):,}' + (f'   wider than the best answer: {loose:,}' if alpha else ''))
    if bad:
        small = min(bad, key=lambda e: len(g[e[0]]) + len(g[e[1]]))
        for label, (a, b, r, x) in (('first', bad[0]), ('smallest', small)):
            print(f'  {label:8}  {show(a)} {sym} {show(b)} -> {show(r)},'
                  f' but {x} is a real result outside it')
    print()


def query():
    """Figure 17.5's five constraints, evaluated on plain N-bit numbers instead of handed to a solver."""
    met4 = met5 = 0
    for (Pv, Pm) in tnums():
        for (Qv, Qm) in tnums():
            sv, sm = (Pv + Qv) & M, (Pm + Qm) & M          # the lines of Figure 17.5, cut to N bits
            mu = (((sm + sv) & M) ^ sv) | Pm | Qm
            Rv, Rm = sv & ~mu & M, mu
            for x in range(M + 1):
                for y in range(M + 1):
                    c = [Pv & Pm == 0, Qv & Qm == 0, x & ~Pm & M == Pv, y & ~Qm & M == Qv,
                         ((x + y) & M) & ~Rm & M != Rv]
                    met4 += all(c[:4])
                    met5 += all(c)
    print(f'Figure 17.5 on {N} bits: {met4:,} assignments meet the first four constraints, {met5:,} meet all five')
    print('  (all five met would be a counterexample: the solver would print sat)\n')


def rounds():
    """i = 0; loop { i = i + 1 }: what an interval analysis knows about i at the loop head."""
    print(f'i = 0; loop {{ i = i + 1 }}  on {N} bits: the value of i at the loop head, round by round')
    for widen in (False, True):
        head, k = (0, 0), 0
        line = [show_i(head)]
        while True:
            k += 1
            new = iv_join(head, iv_add(head, (1, 1)))   # paths meet: the entry and the back edge
            if widen and new != head:
                new = (new[0] if new[0] >= head[0] else 0, new[1] if new[1] <= head[1] else M)
            if new == head:
                break
            head = new
            line.append(show_i(head))
        shown = line if len(line) <= 6 else line[:4] + ['…'] + line[-1:]
        print(f'  {"join and widening" if widen else "join only":18} {k} rounds: ' + '  '.join(shown))
    print()


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--bits' in args:
        k = args.index('--bits')
        setbits(int(args[k + 1]))
        del args[k:k + 2]
    if not args:
        print(__doc__.split('\n\n')[0])
        for k, v in OPS.items():
            print(f'  {k:18} {v[4]}')
        sys.exit(0)
    for a in args:
        {'rounds': rounds, 'query': query}.get(a, lambda: check(a))()
