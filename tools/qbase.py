"""Question registry shared by all unit files."""
import itertools
from lgen import Circuit
import boolmin as bm

REG = []


class Q:
    def __init__(self, num, title, unit, src, aim, theory, exprs=(), star=True):
        self.num, self.title, self.unit, self.src = num, title, unit, src
        self.aim, self.theory, self.exprs, self.star = aim, theory, list(exprs), star
        self.parts, self.kmaps, self.html = [], [], ""
        REG.append(self)

    def part(self, c, rows, note=""):
        if not hasattr(c, "_geom"):
            c.layout()
        self.parts.append(dict(c=c, rows=rows, note=note))
        return c

    def kmap(self, names, ones, dcs=(), label="F", form="SOP", terms=None):
        n = len(names)
        if terms is None:
            if form == "SOP":
                terms = bm.minimise(n, ones, dcs)
            else:
                zeros = [m for m in range(2 ** n) if m not in ones and m not in dcs]
                terms = bm.minimise(n, zeros, dcs)
        self.kmaps.append(dict(names=list(names), ones=list(ones), dcs=list(dcs), label=label,
                               form=form, terms=terms))
        return terms


def C(num, title, lines=()):
    return Circuit(f"Q{num} {title}", f"Q{num}. {title}", lines)


def comb(c, fn):
    n = len(c.pins_in)
    rows = []
    for bits in itertools.product((0, 1), repeat=n):
        o = fn(*bits)
        if isinstance(o, int):
            o = (o,)
        rows.append((bits, tuple(o)))
    return rows


def num(bits):
    v = 0
    for b in bits:
        v = v * 2 + b
    return v


def bitsof(v, n):
    return [(v >> (n - 1 - i)) & 1 for i in range(n)]


def fn_of(ones):
    s = set(ones)
    return lambda *b: int(num(b) in s)


def sop_expr(terms, names):
    return bm.sop_str(terms, names)


def pos_expr(terms_fbar, names):
    return bm.pos_str(terms_fbar, names)


def canon_sop(c, sigs, ones):
    terms = []
    n = len(sigs)
    for m in ones:
        terms.append(c.AND(*[sigs[i] if m >> (n - 1 - i) & 1 else ~sigs[i] for i in range(n)]))
    return terms[0] if len(terms) == 1 else c.OR(*terms)
