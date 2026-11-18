"""Unit 2: logic gates and gate networks (universal gates, multilevel, tri-state, multi-output)."""
from qbase import Q, C, comb

U = "Unit 2 - Logic Gates and Gate Networks"


def nxor(c, a, b):
    """XOR from four NAND gates."""
    n1 = c.NAND(a, b)
    return c.NAND(c.NAND(a, n1), c.NAND(b, n1))


q = Q("28", "AND, OR, NOT using NAND Gates Only", U, "N,F,L",
      "To realise NOT, AND and OR gates using only NAND gates (NAND as a universal gate).",
      "NAND is a universal gate: any Boolean function can be built from it. NOT: tie both inputs together. "
      "AND: NAND followed by a NAND inverter. OR: invert each input with a NAND and feed them to a NAND "
      "(by De Morgan, (A'B')' = A + B).",
      ["NOT: (A.A)' = A'", "AND: ((AB)'(AB)')' = AB", "OR: (A'.B')' = A + B"])
c = C("28", "NAND as Universal Gate", ["NOT, AND and OR built only from NAND gates"])
a, b = c.inp("A", "B")
c.out("NOT_A", c.NAND(a, a))
n = c.NAND(a, b); c.out("AND", c.NAND(n, n))
c.out("OR", c.NAND(c.NAND(a, a), c.NAND(b, b)))
q.part(c, comb(c, lambda a, b: (1 - a, a & b, a | b)))

q = Q("29", "XOR and XNOR using NAND Gates Only", U, "N,F,L",
      "To realise XOR (4 NAND gates) and XNOR (5 NAND gates) using NAND gates only.",
      "With N1 = (AB)', the XOR is ((A.N1)'(B.N1)')' which needs only four 2-input NAND gates - the minimum. "
      "Adding a fifth NAND as an inverter gives XNOR.",
      ["N1 = (AB)'", "XOR = ((A N1)' (B N1)')' = A'B + AB'", "XNOR = (XOR . XOR)'"])
c = C("29", "XOR and XNOR using NAND", ["XOR with 4 NAND gates, XNOR with one more NAND"])
a, b = c.inp("A", "B")
x = nxor(c, a, b)
c.out("XOR", x); c.out("XNOR", c.NAND(x, x))
q.part(c, comb(c, lambda a, b: (a ^ b, 1 - (a ^ b))))

q = Q("30", "NOT, OR, AND using NOR Gates Only", U, "N,L",
      "To realise NOT, OR and AND gates using only NOR gates (NOR as a universal gate).",
      "NOR is also universal. NOT: tie the inputs together. OR: NOR followed by a NOR inverter. AND: invert "
      "each input with a NOR and NOR them together, since (A' + B')' = AB.",
      ["NOT: (A + A)' = A'", "OR: ((A+B)' + (A+B)')' = A + B", "AND: (A' + B')' = AB"])
c = C("30", "NOR as Universal Gate", ["NOT, OR and AND built only from NOR gates"])
a, b = c.inp("A", "B")
c.out("NOT_A", c.NOR(a, a))
n = c.NOR(a, b); c.out("OR", c.NOR(n, n))
c.out("AND", c.NOR(c.NOR(a, a), c.NOR(b, b)))
q.part(c, comb(c, lambda a, b: (1 - a, a | b, a & b)))

q = Q("31", "XOR and XNOR using NOR Gates Only", U, "N,L",
      "To realise XNOR (4 NOR gates) and XOR (5 NOR gates) using NOR gates only.",
      "The NOR structure is the dual of the NAND XOR: with N1 = (A+B)', ((A+N1)' + (B+N1)')' gives XNOR with "
      "four NOR gates. One more NOR used as an inverter gives XOR.",
      ["N1 = (A + B)'", "XNOR = ((A+N1)' + (B+N1)')' = AB + A'B'", "XOR = (XNOR + XNOR)'"])
c = C("31", "XOR and XNOR using NOR", ["XNOR with 4 NOR gates, XOR with one more NOR"])
a, b = c.inp("A", "B")
n1 = c.NOR(a, b)
xn = c.NOR(c.NOR(a, n1), c.NOR(b, n1))
c.out("XNOR", xn); c.out("XOR", c.NOR(xn, xn))
q.part(c, comb(c, lambda a, b: (1 - (a ^ b), a ^ b)))

q = Q("32", "F = AB' + C using NAND Gates Only", U, "F",
      "To implement F = AB' + C using only NAND gates (Lab Assignment 2, Problem 2).",
      "An SOP expression becomes a two-level NAND-NAND circuit: each product term is a NAND, and the OR is a "
      "NAND whose inputs are the term outputs. A single literal term (C) must be inverted first. Missing "
      "complements (B') are made with NAND inverters.",
      ["F = AB' + C = ((AB')' . C')'", "B' = (B.B)',  C' = (C.C)'"])
c = C("32", "AB plus C using NAND", ["F = AB' + C = ((AB')' . C')'  - NAND gates only"])
a, b, cc = c.inp("A", "B", "C")
c.out("F", c.NAND(c.NAND(a, c.NAND(b, b)), c.NAND(cc, cc)))
q.part(c, comb(c, lambda a, b, cc: (a & (1 - b)) | cc))

q = Q("33", "Y = (A + B)(C + D) using NOR Gates Only", U, "N",
      "To find the number of NOR gates needed for Y = (A + B)(C + D) and implement it.",
      "A POS expression maps directly onto a two-level NOR-NOR circuit: each sum term is a NOR gate and the "
      "AND is a NOR gate fed by the first-level NORs. Hence Y = ((A+B)' + (C+D)')' needs only 3 NOR gates.",
      ["Y = (A + B)(C + D) = ((A + B)' + (C + D)')'", "Number of NOR gates = 3"])
c = C("33", "POS using NOR only", ["Y = (A+B)(C+D) = ((A+B)' + (C+D)')'  - 3 NOR gates"])
a, b, cc, d = c.inp("A", "B", "C", "D")
c.out("Y", c.NOR(c.NOR(a, b), c.NOR(cc, d)))
q.part(c, comb(c, lambda a, b, cc, d: (a | b) & (cc | d)))

q = Q("34", "3-bit Even Parity Generator using NAND Gates", U, "N",
      "To generate the even parity bit for three data bits x, y, z using NAND gates only.",
      "For even parity P = x XOR y XOR z (P = 1 when the data has an odd number of 1s). Each XOR is built "
      "from four NAND gates, so the generator uses eight NAND gates in two XOR stages.",
      ["P = x'y'z + x'yz' + xy'z' + xyz = x XOR y XOR z"])
c = C("34", "Parity Generator using NAND", ["P = x ^ y ^ z  (two NAND-XOR stages)"])
x, y, z = c.inp("x", "y", "z")
c.out("P", nxor(c, nxor(c, x, y), z))
q.part(c, comb(c, lambda x, y, z: x ^ y ^ z))

q = Q("35", "Tri-state Buffers on a Shared Bus", U, "N",
      "To connect two data sources to one bus line using tri-state buffers controlled by a select line.",
      "A tri-state buffer has outputs 0, 1 and high impedance (Z). When its enable is 0 it disconnects from "
      "the line. Only one buffer may be enabled at a time, so S drives buffer-1 and S' drives buffer-0; the "
      "outputs are wired together to form the bus (this behaves like a 2:1 multiplexer).",
      ["BUS = D0 when S = 0 (buffer 0 enabled by S')", "BUS = D1 when S = 1 (buffer 1 enabled by S)"])
c = C("35", "Tri-state Bus", ["Two tri-state buffers share one bus wire; S selects the source"])
d0, d1, s = c.inp("D0", "D1", "S")
c.out("BUS", c.BUS(c.TRI(d0, ~s), c.TRI(d1, s)))
q.part(c, comb(c, lambda d0, d1, s: d1 if s else d0))

q = Q("36", "Multilevel NAND Network", U, "N",
      "To implement the multilevel function F = (AB + C)D with AND-OR gates and with NAND gates only.",
      "Multilevel circuits are converted to NAND form by replacing each AND by a NAND and each OR by an "
      "OR with inverted inputs (bubbled-OR = NAND, the alternate gate symbol). Where two bubbles meet on a "
      "line they cancel; an unpaired bubble needs a NAND inverter. Mixed logic notation keeps track of the "
      "polarity of each signal.",
      ["F = (AB + C) D", "NAND form: X = ((AB)' . C')' = AB + C,  F = ((X.D)')'"], star=False)
c = C("36", "Multilevel NAND Network", ["F = (AB + C)D : AND-OR version (F1) and NAND-only version (F2)"])
a, b, cc, d = c.inp("A", "B", "C", "D")
c.out("F1", c.AND(c.OR(c.AND(a, b), cc), d))
xx = c.NAND(c.NAND(a, b), c.NAND(cc, cc))
t = c.NAND(xx, d)
c.out("F2", c.NAND(t, t))
q.part(c, comb(c, lambda a, b, cc, d: (((a & b) | cc) & d,) * 2))

q = Q("37", "Multiple-Output Network with Shared Terms", U, "N",
      "To implement three functions that share product terms using the minimum number of gates.",
      "When several outputs are produced from the same inputs, common product terms are generated once and "
      "fanned out to every OR gate that needs them. Here AB, BC' and A'C are each used by two outputs, so "
      "only three AND gates are needed instead of six.",
      ["F1 = AB + BC'", "F2 = AB + A'C", "F3 = BC' + A'C"], star=False)
c = C("37", "Multiple Output Network", ["Shared terms AB, BC', A'C feed three OR gates"])
a, b, cc = c.inp("A", "B", "C")
t1, t2, t3 = c.AND(a, b), c.AND(b, ~cc), c.AND(~a, cc)
c.out("F1", c.OR(t1, t2)); c.out("F2", c.OR(t1, t3)); c.out("F3", c.OR(t2, t3))
q.part(c, comb(c, lambda a, b, cc: ((a & b) | (b & (1 - cc)), (a & b) | ((1 - a) & cc), (b & (1 - cc)) | ((1 - a) & cc))))
