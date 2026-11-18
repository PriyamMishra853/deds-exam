"""Quine-McCluskey minimisation + helpers to turn terms into gates and K-map data."""
import itertools

# a term is (value, dashmask) over n variables, MSB = first variable


def prime_implicants(n, ones, dcs=()):
    cur = {(m, 0) for m in set(ones) | set(dcs)}
    primes = set()
    while cur:
        nxt, used = set(), set()
        lst = sorted(cur)
        for a, b in itertools.combinations(lst, 2):
            if a[1] == b[1]:
                d = a[0] ^ b[0]
                if d and d & (d - 1) == 0:
                    nxt.add((a[0] & ~d, a[1] | d))
                    used.add(a); used.add(b)
        primes |= cur - used
        cur = nxt
    return sorted(primes, key=lambda t: (-bin(t[1]).count("1"), t[0]))


def covers(t, m):
    return (m & ~t[1]) == (t[0] & ~t[1])


def minterms_of(t, n):
    return [m for m in range(2 ** n) if covers(t, m)]


def literals(t, n):
    return n - bin(t[1]).count("1")


def essential_pis(n, ones, pis):
    ess = []
    for m in ones:
        c = [p for p in pis if covers(p, m)]
        if len(c) == 1 and c[0] not in ess:
            ess.append(c[0])
    return ess


def minimise(n, ones, dcs=()):
    """Minimal SOP cover (fewest terms, then fewest literals). Returns list of terms."""
    ones = sorted(set(ones))
    if not ones:
        return []
    pis = prime_implicants(n, ones, dcs)
    ess = essential_pis(n, ones, pis)
    left = [m for m in ones if not any(covers(p, m) for p in ess)]
    rest = [p for p in pis if p not in ess and any(covers(p, m) for m in left)]
    best = None
    for k in range(0, len(rest) + 1):
        for combo in itertools.combinations(rest, k):
            if all(any(covers(p, m) for p in combo) for m in left):
                cost = sum(literals(p, n) for p in combo)
                if best is None or cost < best[0]:
                    best = (cost, list(combo))
        if best:
            break
    terms = ess + best[1]
    return sorted(terms, key=lambda t: [((t[0] >> (n - 1 - i)) & 1, (t[1] >> (n - 1 - i)) & 1) for i in range(n)][::1])


def term_str(t, names, prime="'"):
    n = len(names)
    s = ""
    for i, v in enumerate(names):
        bit = 1 << (n - 1 - i)
        if t[1] & bit:
            continue
        s += v + ("" if t[0] & bit else prime)
    return s or "1"


def sop_str(terms, names):
    return " + ".join(term_str(t, names) for t in terms) if terms else "0"


def sumterm_str(t, names):
    """t is a term of F' ; returns the matching sum term of F, e.g. (A + B')."""
    n = len(names)
    lits = []
    for i, v in enumerate(names):
        bit = 1 << (n - 1 - i)
        if t[1] & bit:
            continue
        lits.append(v + ("'" if t[0] & bit else ""))
    return "(" + " + ".join(lits) + ")" if len(lits) > 1 else lits[0]


def pos_str(terms_fbar, names):
    return "".join(sumterm_str(t, names) for t in terms_fbar) if terms_fbar else "1"


class Builder:
    """Builds SOP/POS gate networks on a lgen Circuit, sharing identical gates."""

    def __init__(self, c, sigs):
        self.c, self.sigs, self.cache = c, list(sigs), {}

    def lit(self, i, positive):
        return self.sigs[i] if positive else self.c.NOT(self.sigs[i])

    def term(self, t):
        n = len(self.sigs)
        lits = [(i, bool(t[0] >> (n - 1 - i) & 1)) for i in range(n) if not t[1] >> (n - 1 - i) & 1]
        key = ("AND", tuple(lits))
        if len(lits) == 1:
            return self.lit(*lits[0])
        if key not in self.cache:
            self.cache[key] = self.c.AND(*[self.lit(i, p) for i, p in lits])
        return self.cache[key]

    def sop(self, terms):
        ts = [self.term(t) for t in terms]
        return ts[0] if len(ts) == 1 else self.c.OR(*ts)

    def sumterm(self, t):
        n = len(self.sigs)
        lits = [(i, not bool(t[0] >> (n - 1 - i) & 1)) for i in range(n) if not t[1] >> (n - 1 - i) & 1]
        if len(lits) == 1:
            return self.lit(*lits[0])
        key = ("OR", tuple(lits))
        if key not in self.cache:
            self.cache[key] = self.c.OR(*[self.lit(i, p) for i, p in lits])
        return self.cache[key]

    def pos(self, terms_fbar):
        ts = [self.sumterm(t) for t in terms_fbar]
        return ts[0] if len(ts) == 1 else self.c.AND(*ts)


GRAY2 = [0, 1, 3, 2]


def kmap_layout(n):
    """Return (row_vars, col_vars, row_codes, col_codes) for 2..4 variables."""
    if n == 2:
        return 1, 1, [0, 1], [0, 1]
    if n == 3:
        return 1, 2, [0, 1], GRAY2
    if n == 4:
        return 2, 2, GRAY2, GRAY2
    raise ValueError(n)
