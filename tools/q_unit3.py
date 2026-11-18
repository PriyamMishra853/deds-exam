"""Unit 3: combinational logic circuits."""
from lgen import Circuit
from qbase import Q, C, comb, num, bitsof, fn_of, sop_expr
import boolmin as bm

U = "Unit 3 - Combinational Logic Circuits"


# ------------------------------------------------------------------ helper blocks
def helper(name, short):
    c = Circuit("Helper - " + name, "Helper block: " + name, ["Used as a sub-circuit by other questions"])
    c.short = short
    return c


HA = helper("Half Adder", "HA")
a, b = HA.inp("A", "B"); HA.out("S", HA.XOR(a, b)); HA.out("C", HA.AND(a, b)); HA.layout()

FA = helper("Full Adder", "FA")
a, b, ci = FA.inp("A", "B", "Cin")
FA.out("S", FA.XOR(a, b, ci)); FA.out("Cout", FA.OR(FA.AND(a, b), FA.AND(b, ci), FA.AND(a, ci))); FA.layout()

HS = helper("Half Subtractor", "HS")
a, b = HS.inp("A", "B"); HS.out("D", HS.XOR(a, b)); HS.out("Bo", HS.AND(~a, b)); HS.layout()

FS = helper("Full Subtractor", "FS")
a, b, bi = FS.inp("A", "B", "Bin")
FS.out("D", FS.XOR(a, b, bi)); FS.out("Bo", FS.OR(FS.AND(~a, b), FS.AND(~a, bi), FS.AND(b, bi))); FS.layout()

ADD4 = helper("4-bit Adder", "ADD4")
A = ADD4.inp("A3", "A2", "A1", "A0"); B = ADD4.inp("B3", "B2", "B1", "B0"); cin = ADD4.inp("Cin")
cy, S = cin, {}
for i in (3, 2, 1, 0):
    S[i], cy = ADD4.SUB(FA, A[i], B[i], cy)
ADD4.out("Cout", cy)
for i in (0, 1, 2, 3):
    ADD4.out(f"S{3-i}", S[i])
ADD4.layout()


def dec_helper(n, enable):
    c = helper(f"{n} to {2**n} Decoder" + (" with Enable" if enable else ""), f"DEC{n}x{2**n}")
    e = c.inp("E") if enable else None
    s = c.inp(*["A", "B", "C", "D"][:n])
    for m in range(2 ** n):
        lits = [s[i] if m >> (n - 1 - i) & 1 else ~s[i] for i in range(n)]
        c.out(f"D{m}", c.AND(*([e] if enable else []) + lits))
    return c.layout()


DEC24 = dec_helper(2, False)
DEC38E = dec_helper(3, True)

DMX18 = helper("1 to 8 Demultiplexer", "DEMUX")
iin = DMX18.inp("I"); sel = DMX18.inp("S2", "S1", "S0")
for m in range(8):
    DMX18.out(f"Y{m}", DMX18.AND(iin, *[sel[i] if m >> (2 - i) & 1 else ~sel[i] for i in range(3)]))
DMX18.layout()


def mux_helper(n):
    c = helper(f"{2**n} to 1 Multiplexer", f"MUX{2**n}")
    s = c.inp(*[f"S{n-1-i}" for i in range(n)])
    d = c.inp(*[f"I{k}" for k in range(2 ** n)])
    terms = [c.AND(d[k], *[s[i] if k >> (n - 1 - i) & 1 else ~s[i] for i in range(n)]) for k in range(2 ** n)]
    c.out("Y", c.OR(*terms))
    return c.layout()


MUX4 = mux_helper(2)
MUX8 = mux_helper(3)


def nxor(c, a, b):
    n1 = c.NAND(a, b)
    return c.NAND(c.NAND(a, n1), c.NAND(b, n1)), n1


def nrxor(c, a, b):
    """XOR from NOR gates: returns (xor, and)."""
    n1 = c.NOR(a, b)
    land = c.NOR(c.NOR(a, a), c.NOR(b, b))
    return c.NOR(n1, land), land


def ab_split(bits, n):
    return num(bits[:n]), num(bits[n:2 * n])


# ------------------------------------------------------------------ Q38 half adder
q = Q("38", "Half Adder (Basic, NAND-only, NOR-only)", U, "N,F,L",
      "To design a half adder and realise it with basic gates, NAND gates only and NOR gates only.",
      "A half adder adds two bits and gives Sum and Carry; it cannot accept a carry from a previous stage. "
      "From the truth table S = A'B + AB' = A XOR B and C = AB. With NAND only: N1 = (AB)', S = ((A N1)'(B N1)')', "
      "C = (N1 N1)' (5 gates). With NOR only: C = (A' + B')', S = ((A+B)' + C)' (5 gates).",
      ["S = A XOR B", "C = A.B"])
c = C("38a", "Half Adder (basic gates)", ["S = A ^ B,  C = AB"])
a, b = c.inp("A", "B"); c.out("S", c.XOR(a, b)); c.out("C", c.AND(a, b))
q.part(c, comb(c, lambda a, b: (a ^ b, a & b)))
c = C("38b", "Half Adder using NAND only", ["5 NAND gates"])
a, b = c.inp("A", "B"); s, n1 = nxor(c, a, b); c.out("S", s); c.out("C", c.NAND(n1, n1))
q.part(c, comb(c, lambda a, b: (a ^ b, a & b)))
c = C("38c", "Half Adder using NOR only", ["5 NOR gates"])
a, b = c.inp("A", "B"); s, cc = nrxor(c, a, b); c.out("S", s); c.out("C", cc)
q.part(c, comb(c, lambda a, b: (a ^ b, a & b)))

FAF = lambda a, b, c: ((a + b + c) & 1, (a + b + c) >> 1)
q = Q("39", "Full Adder", U, "N,F,L",
      "To design a full adder using K-maps and implement it with basic gates.",
      "A full adder adds three bits A, B and the carry-in Cin. The Sum K-map is a checkerboard, so "
      "S = A XOR B XOR Cin. The carry K-map gives Cout = AB + BCin + ACin (also written AB + Cin(A XOR B)).",
      ["S = A'B'Cin + A'BCin' + AB'Cin' + ABCin = A XOR B XOR Cin", "Cout = AB + BCin + ACin"])
q.kmap(["A", "B", "Cin"], [1, 2, 4, 7], label="S"); q.kmap(["A", "B", "Cin"], [3, 5, 6, 7], label="Cout")
c = C("39", "Full Adder", ["S = A^B^Cin,  Cout = AB + BCin + ACin"])
a, b, ci = c.inp("A", "B", "Cin")
c.out("S", c.XOR(a, b, ci)); c.out("Cout", c.OR(c.AND(a, b), c.AND(b, ci), c.AND(a, ci)))
q.part(c, comb(c, FAF))

q = Q("40", "Full Adder using Two Half Adders", U, "N,F,L",
      "To construct a full adder from two half adders and an OR gate.",
      "The first half adder adds A and B (S1 = A XOR B, C1 = AB). The second adds S1 and Cin giving "
      "S = A XOR B XOR Cin and C2 = Cin(A XOR B). The final carry is Cout = C1 + C2 = AB + Cin(A XOR B).",
      ["S = (A XOR B) XOR Cin", "Cout = AB + Cin(A XOR B)"])
c = C("40", "Full Adder from Half Adders", ["HA1(A,B) -> HA2(S1,Cin) -> OR of carries"])
a, b, ci = c.inp("A", "B", "Cin")
s1, c1 = c.SUB(HA, a, b); s2, c2 = c.SUB(HA, s1, ci)
c.out("S", s2); c.out("Cout", c.OR(c1, c2))
q.part(c, comb(c, FAF))

q = Q("41", "Full Adder using NAND Gates Only", U, "N",
      "To implement a full adder using nine 2-input NAND gates.",
      "Two NAND-XOR stages produce the sum. The first NAND of each stage, (AB)' and (X.Cin)', are reused: "
      "Cout = ((AB)' . (X.Cin)')' = AB + Cin(A XOR B). Total = 4 + 4 + 1 = 9 NAND gates.",
      ["X = A XOR B (4 NAND)", "S = X XOR Cin (4 NAND)", "Cout = ((AB)'(X Cin)')'"])
c = C("41", "Full Adder using NAND only", ["9 NAND gates"])
a, b, ci = c.inp("A", "B", "Cin")
x, n1 = nxor(c, a, b); s, n2 = nxor(c, x, ci)
c.out("S", s); c.out("Cout", c.NAND(n1, n2))
q.part(c, comb(c, FAF))

HSF = lambda a, b: (a ^ b, (1 - a) & b)
q = Q("42", "Half Subtractor (Basic and NAND-only)", U, "N,F,L",
      "To design a half subtractor (A - B) and implement it with basic gates and with NAND gates only.",
      "A half subtractor subtracts B from A giving the Difference D and the Borrow Bo. "
      "From the truth table D = A XOR B and Bo = A'B. Using NAND gates, the XOR needs four NANDs and "
      "A'B needs three more (an inverter for A, a NAND and an output inverter).",
      ["D = A'B + AB' = A XOR B", "Bo = A'B"])
c = C("42a", "Half Subtractor", ["D = A ^ B,  Bo = A'B"])
a, b = c.inp("A", "B"); c.out("D", c.XOR(a, b)); c.out("Bo", c.AND(~a, b))
q.part(c, comb(c, HSF))
c = C("42b", "Half Subtractor using NAND only", ["D: 4 NAND,  Bo = ((A'B)')'"])
a, b = c.inp("A", "B"); s, _ = nxor(c, a, b); t = c.NAND(c.NAND(a, a), b)
c.out("D", s); c.out("Bo", c.NAND(t, t))
q.part(c, comb(c, HSF))

FSF = lambda a, b, bi: ((a - b - bi) & 1, int(a - b - bi < 0))
q = Q("43", "Full Subtractor", U, "N,F,L",
      "To design a full subtractor (A - B - Bin) using K-maps.",
      "The full subtractor also takes the borrow from the previous stage. The difference K-map is a "
      "checkerboard so D = A XOR B XOR Bin. The borrow K-map gives Bo = A'B + A'Bin + B.Bin.",
      ["D = A XOR B XOR Bin", "Bo = A'B + A'Bin + B Bin"])
q.kmap(["A", "B", "Bin"], [1, 2, 4, 7], label="D"); q.kmap(["A", "B", "Bin"], [1, 2, 3, 7], label="Bo")
c = C("43", "Full Subtractor", ["D = A^B^Bin,  Bo = A'B + A'Bin + B.Bin"])
a, b, bi = c.inp("A", "B", "Bin")
c.out("D", c.XOR(a, b, bi)); c.out("Bo", c.OR(c.AND(~a, b), c.AND(~a, bi), c.AND(b, bi)))
q.part(c, comb(c, FSF))

q = Q("44", "Full Subtractor using Two Half Subtractors", U, "L",
      "To construct a full subtractor using two half subtractors and an OR gate.",
      "HS1 computes A - B giving D1 = A XOR B and B1 = A'B. HS2 computes D1 - Bin giving D = A XOR B XOR Bin and "
      "B2 = (A XOR B)'Bin. The total borrow is Bo = B1 + B2.",
      ["D = (A XOR B) XOR Bin", "Bo = A'B + (A XOR B)' Bin"])
c = C("44", "Full Subtractor from Half Subtractors", ["HS1(A,B) -> HS2(D1,Bin) -> OR of borrows"])
a, b, bi = c.inp("A", "B", "Bin")
d1, b1 = c.SUB(HS, a, b); d2, b2 = c.SUB(HS, d1, bi)
c.out("D", d2); c.out("Bo", c.OR(b1, b2))
q.part(c, comb(c, FSF))

# ------------------------------------------------------------------ 4-bit adders
q = Q("45", "4-bit Ripple Carry Adder and Ripple Borrow Subtractor", U, "F",
      "To build a 4-bit parallel adder from four full adders and a 4-bit subtractor from four full subtractors.",
      "In a ripple carry adder the carry out of each full adder feeds the carry in of the next, so the carry "
      "'ripples' from the LSB to the MSB (this is the IC 7483 function). The ripple borrow subtractor is "
      "built the same way from full subtractors, passing the borrow to the next stage.",
      ["S_i = A_i XOR B_i XOR C_i,  C_(i+1) = A_iB_i + C_i(A_i XOR B_i)", "D_i = A_i XOR B_i XOR Bin_i"])
c = C("45a", "4-bit Ripple Carry Adder", ["Four full adders, carry ripples from FA0 to FA3"])
A = c.inp("A3", "A2", "A1", "A0"); B = c.inp("B3", "B2", "B1", "B0"); cy = c.inp("C0")
S = {}
for i in (3, 2, 1, 0):
    S[i], cy = c.SUB(FA, A[i], B[i], cy)
c.out("C4", cy)
for i in (0, 1, 2, 3):
    c.out(f"S{3-i}", S[i])


def add4(*b):
    a, bb = ab_split(b, 4); t = a + bb + b[8]
    return [t >> 4] + bitsof(t & 15, 4)


q.part(c, comb(c, add4))
c = C("45b", "4-bit Ripple Borrow Subtractor", ["Four full subtractors, borrow ripples from FS0 to FS3"])
A = c.inp("A3", "A2", "A1", "A0"); B = c.inp("B3", "B2", "B1", "B0"); bw = c.inp("Bin")
D = {}
for i in (3, 2, 1, 0):
    D[i], bw = c.SUB(FS, A[i], B[i], bw)
c.out("Bout", bw)
for i in (0, 1, 2, 3):
    c.out(f"D{3-i}", D[i])


def sub4(*b):
    a, bb = ab_split(b, 4); t = a - bb - b[8]
    return [int(t < 0)] + bitsof(t & 15, 4)


q.part(c, comb(c, sub4))

q = Q("46", "4-bit Binary Adder-Subtractor", U, "N,F",
      "To design a 4-bit circuit that adds when M = 0 and subtracts (2's complement) when M = 1.",
      "Each B bit passes through an XOR gate controlled by the mode bit M: when M = 0 B is unchanged and "
      "Cin = 0 (addition); when M = 1 B is complemented and Cin = 1, so the adder computes A + B' + 1 = A - B. "
      "In subtraction the end carry C4 = 1 means the result is positive (A >= B).",
      ["B_i' = B_i XOR M,  C0 = M", "M = 0: S = A + B;  M = 1: S = A - B"])
c = C("46", "4-bit Adder-Subtractor", ["M = 0 : A + B      M = 1 : A - B (2's complement)"])
m = c.inp("M"); A = c.inp("A3", "A2", "A1", "A0"); B = c.inp("B3", "B2", "B1", "B0")
cy, S = m, {}
for i in (3, 2, 1, 0):
    S[i], cy = c.SUB(FA, A[i], c.XOR(B[i], m), cy)
c.out("C4", cy)
for i in (0, 1, 2, 3):
    c.out(f"S{3-i}", S[i])


def addsub(*b):
    m = b[0]; a, bb = num(b[1:5]), num(b[5:9])
    t = a + (bb ^ (15 if m else 0)) + m
    return [t >> 4] + bitsof(t & 15, 4)


q.part(c, comb(c, addsub))

q = Q("47", "BCD Adder", U, "N,F",
      "To design a single-digit BCD adder using two 4-bit binary adders and correction logic.",
      "Two BCD digits and a carry are first added in binary giving K Z3Z2Z1Z0. If the sum exceeds 9 "
      "(K = 1, or Z3Z2 = 1, or Z3Z1 = 1) the result is invalid BCD, so 6 (0110) is added by the second adder "
      "and the output carry is 1. Correction condition: C = K + Z3Z2 + Z3Z1.",
      ["C = K + Z3.Z2 + Z3.Z1", "If C = 1 add 0110 to Z3Z2Z1Z0"])
c = C("47", "BCD Adder", ["Binary sum, then add 0110 when sum > 9.   C = K + Z3Z2 + Z3Z1"])
A = c.inp("A3", "A2", "A1", "A0"); B = c.inp("B3", "B2", "B1", "B0"); cin = c.inp("Cin")
zero = c.const(0)
K, z3, z2, z1, z0 = c.SUB(ADD4, *A, *B, cin)
cc = c.OR(K, c.AND(z3, z2), c.AND(z3, z1))
r = c.SUB(ADD4, z3, z2, z1, z0, zero, cc, cc, zero, zero)
c.out("Cout", cc)
for k, lab in enumerate(["S3", "S2", "S1", "S0"]):
    c.out(lab, r[k + 1])
rows = []
for a_ in range(10):
    for b_ in range(10):
        for ci_ in (0, 1):
            t = a_ + b_ + ci_
            rows.append((bitsof(a_, 4) + bitsof(b_, 4) + [ci_], tuple([t // 10] + bitsof(t % 10, 4))))
q.part(c, rows, "Only valid BCD inputs (0-9) are tested: 200 combinations.")

q = Q("48", "4-bit Carry Look-Ahead Adder", U, "N,F",
      "To design a 4-bit carry look-ahead adder.",
      "A ripple adder is slow because each carry waits for the previous one. A CLA computes every carry "
      "directly from the inputs using generate G_i = A_iB_i and propagate P_i = A_i XOR B_i: "
      "C_(i+1) = G_i + P_iC_i, expanded so that all carries need only two gate levels.",
      ["P_i = A_i XOR B_i,  G_i = A_i B_i,  S_i = P_i XOR C_i",
       "C1 = G0 + P0C0", "C2 = G1 + P1G0 + P1P0C0", "C3 = G2 + P2G1 + P2P1G0 + P2P1P0C0",
       "C4 = G3 + P3G2 + P3P2G1 + P3P2P1G0 + P3P2P1P0C0"])
c = C("48", "Carry Look-Ahead Adder", ["Pi = Ai^Bi, Gi = AiBi, carries computed in two levels"])
A = c.inp("A3", "A2", "A1", "A0"); B = c.inp("B3", "B2", "B1", "B0"); c0 = c.inp("C0")
P = {i: c.XOR(A[3 - i], B[3 - i]) for i in range(4)}
G = {i: c.AND(A[3 - i], B[3 - i]) for i in range(4)}
Cs = {0: c0}
for i in range(1, 5):
    terms = [G[i - 1]]
    for j in range(i - 2, -2, -1):
        src = G[j] if j >= 0 else c0
        terms.append(c.AND(*[P[k] for k in range(i - 1, j, -1)], src))
    Cs[i] = c.OR(*terms)
c.out("C4", Cs[4])
for i in (3, 2, 1, 0):
    c.out(f"S{i}", c.XOR(P[i], Cs[i]))
q.part(c, comb(c, add4))

# ------------------------------------------------------------------ multipliers
def multiplier(c, A, B):
    """A, B lists MSB first. Array multiplier made of AND gates, HA and FA blocks."""
    n = len(A)
    a = A[::-1]; b = B[::-1]
    pp = [[c.AND(a[j], b[i]) for j in range(n)] for i in range(n)]
    P = [pp[0][0]]
    cur = pp[0][1:] + [None]
    for i in range(1, n):
        new, carry = [], None
        for j in range(n):
            x, y = cur[j], pp[i][j]
            if x is None and carry is None:
                s = y
            elif x is None:
                s, carry = c.SUB(HA, y, carry)
            elif carry is None:
                s, carry = c.SUB(HA, x, y)
            else:
                s, carry = c.SUB(FA, x, y, carry)
            new.append(s)
        P.append(new[0])
        cur = new[1:] + [carry]
    return P + cur


def mul_spec(n):
    return lambda *b: bitsof(num(b[:n]) * num(b[n:]), 2 * n)


q = Q("49", "2-bit by 2-bit Binary Multiplier", U, "F",
      "To design a 2 x 2 binary multiplier using AND gates and half adders.",
      "Binary multiplication forms partial products A_iB_j with AND gates and adds them column by column. "
      "P0 = A0B0; P1 = A1B0 + A0B1 (half adder); P2 and P3 are the sum and carry of A1B1 plus the previous carry.",
      ["P0 = A0B0", "P1 = A1B0 XOR A0B1", "P2 = A1B1 XOR C1,  P3 = A1B1.C1   (C1 = A1B0.A0B1)"])
c = C("49", "2x2 Binary Multiplier", ["4 AND gates + 2 half adders"])
A = c.inp("A1", "A0"); B = c.inp("B1", "B0")
P = multiplier(c, A, B)
for k in range(3, -1, -1):
    c.out(f"P{k}", P[k])
q.part(c, comb(c, mul_spec(2)))

q = Q("50", "3x3 and 4x4 Array Multipliers", U, "F",
      "To build 3-bit x 3-bit and 4-bit x 4-bit binary array multipliers.",
      "An n x n array multiplier generates n^2 partial products with AND gates. Each row of partial products "
      "is added to the shifted running sum with a row of adders (half adder at the ends, full adders inside). "
      "The 3x3 multiplier gives a 6-bit product and the 4x4 an 8-bit product.",
      ["Partial products  A_j B_i", "Product = Sum over i of (A x B_i) shifted left by i"], star=False)
for nb, tag in ((3, "50a"), (4, "50b")):
    c = C(tag, f"{nb}x{nb} Binary Multiplier", [f"{nb*nb} AND gates + rows of HA/FA blocks"])
    A = c.inp(*[f"A{k}" for k in range(nb - 1, -1, -1)]); B = c.inp(*[f"B{k}" for k in range(nb - 1, -1, -1)])
    P = multiplier(c, A, B)
    for k in range(2 * nb - 1, -1, -1):
        c.out(f"P{k}", P[k])
    q.part(c, comb(c, mul_spec(nb)))

# ------------------------------------------------------------------ comparators
names = ["A1", "A0", "B1", "B0"]
q = Q("51", "2-bit Magnitude Comparator (K-map design)", U, "N",
      "To design a 2-bit magnitude comparator with outputs A>B, A=B and A<B using K-maps.",
      "The comparator compares two binary numbers. Each output is 1 for a set of the 16 input combinations; "
      "plotting them on 4-variable K-maps and grouping gives the minimal SOP expressions.", [])
c = C("51", "2-bit Comparator", ["Outputs G (A>B), E (A=B), L (A<B)"])
sg = c.inp(*names); bld = bm.Builder(c, sg)
for lab, f in (("G", lambda a, b: a > b), ("E", lambda a, b: a == b), ("L", lambda a, b: a < b)):
    ones = [m for m in range(16) if f(m >> 2, m & 3)]
    t = q.kmap(names, ones, label=lab)
    q.exprs.append(f"{lab} = {sop_expr(t, names)}")
    c.out(lab, bld.sop(t))
q.part(c, comb(c, lambda *b: (int(num(b[:2]) > num(b[2:])), int(num(b[:2]) == num(b[2:])), int(num(b[:2]) < num(b[2:])))))

q = Q("52", "4-bit Magnitude Comparator", U, "F",
      "To design a 4-bit magnitude comparator.",
      "x_i = A_i XNOR B_i is 1 when the bits are equal. A = B when all x_i are 1. A > B when the first unequal "
      "bit (from the MSB) has A_i = 1, B_i = 0; A < B is the opposite. This is the logic of IC 7485.",
      ["x_i = A_iB_i + A_i'B_i'", "E = x3x2x1x0", "G = A3B3' + x3A2B2' + x3x2A1B1' + x3x2x1A0B0'",
       "L = A3'B3 + x3A2'B2 + x3x2A1'B1 + x3x2x1A0'B0"])
c = C("52", "4-bit Magnitude Comparator", ["xi = Ai XNOR Bi;   E = x3x2x1x0"])
A = c.inp("A3", "A2", "A1", "A0"); B = c.inp("B3", "B2", "B1", "B0")
X = [c.XNOR(A[k], B[k]) for k in range(4)]
g, l = [], []
for k in range(4):
    g.append(c.AND(*X[:k], A[k], ~B[k])); l.append(c.AND(*X[:k], ~A[k], B[k]))
c.out("G", c.OR(*g)); c.out("E", c.AND(*X)); c.out("L", c.OR(*l))
q.part(c, comb(c, lambda *b: (int(num(b[:4]) > num(b[4:])), int(num(b[:4]) == num(b[4:])), int(num(b[:4]) < num(b[4:])))))

# ------------------------------------------------------------------ code converters
names = ["A", "B", "C", "D"]
q = Q("53", "BCD to Excess-3 Code Converter", U, "N,L",
      "To design a BCD to Excess-3 code converter using K-maps (10-15 are don't-cares).",
      "Excess-3 code = BCD + 0011. It is an unweighted, self-complementing code. Four K-maps (one per output "
      "bit) are drawn with don't-cares for the unused inputs 10-15 and minimised.", [])
c = C("53", "BCD to Excess-3", ["WXYZ = ABCD + 0011 (inputs 10-15 are don't care)"])
sg = c.inp(*names); bld = bm.Builder(c, sg)
for k, lab in enumerate(["W", "X", "Y", "Z"]):
    ones = [d for d in range(10) if (d + 3) >> (3 - k) & 1]
    t = q.kmap(names, ones, range(10, 16), label=lab)
    q.exprs.append(f"{lab} = {sop_expr(t, names)}")
    c.out(lab, bld.sop(t))
q.part(c, [(bitsof(d, 4), tuple(bitsof(d + 3, 4))) for d in range(10)], "Rows 10-15 are don't-care inputs.")

SEG = "abcdefg"
DIG3 = {0: "abcdef", 1: "bc", 2: "abdeg", 3: "abcdg", 4: "bcfg", 5: "acdfg", 6: "acdefg", 7: "abc"}
DIG10 = dict(DIG3); DIG10.update({8: "abcdefg", 9: "abcdfg"})


def seg_question(nm, title, names, digits, dcs, src, aim, theory):
    q = Q(nm, title, U, src, aim, theory, [])
    q.html = "SEG7"
    c = C(nm, title, ["Common-cathode display: segment = 1 lights it.  Outputs a-g also drive the display"])
    sg = c.inp(*names); bld = bm.Builder(c, sg)
    n = len(names)
    for s in SEG:
        ones = [d for d, segs in digits.items() if s in segs]
        t = q.kmap(names, ones, dcs, label=s)
        q.exprs.append(f"{s} = {sop_expr(t, names)}")
        c.out(s, bld.sop(t))
    c.seven_seg()
    q.part(c, [(bitsof(d, n), tuple(int(s in segs) for s in SEG)) for d, segs in digits.items()],
           ("Rows 10-15 are don't-care inputs." if dcs else ""))
    q.digits = digits
    return q


seg_question("54", "3-bit Binary to 7-Segment Display (0-7)", ["x", "y", "z"], DIG3, (), "N,L",
             "To display the digits 0-7 given by a 3-bit binary input on a 7-segment display.",
             "A 7-segment display has segments a-g. For each digit 0-7 the segments that must glow are listed "
             "in a truth table (common cathode: 1 = ON). Each segment is a function of x, y, z and is minimised "
             "with a 3-variable K-map (F1...F7 in the class notes correspond to a...g).")
seg_question("55", "BCD to 7-Segment Decoder", ["A", "B", "C", "D"], DIG10, range(10, 16), "N,F,L",
             "To design a BCD to 7-segment decoder (like IC 7448) and display digits 0-9.",
             "The decoder converts a BCD digit ABCD into the seven segment signals a-g. Inputs 10-15 never occur "
             "in BCD, so they are don't-cares, which greatly simplifies each 4-variable K-map.")

# ------------------------------------------------------------------ decoders
q = Q("56", "2:4 and 3:8 Decoders with Enable", U, "N,F,L",
      "To design 2-to-4 and 3-to-8 line decoders with an enable input.",
      "An n-to-2^n decoder activates exactly one output - the one whose number equals the binary input - by "
      "generating every minterm with an AND gate. The enable input E is added to each AND gate; when E = 0 all "
      "outputs are 0. Decoders are used to generate minterms and to select memory chips.",
      ["2:4  D0 = E A'B', D1 = E A'B, D2 = E AB', D3 = E AB", "3:8  D_m = E . (minterm m of A, B, C)"])
for n, tag in ((2, "56a"), (3, "56b")):
    c = C(tag, f"{n} to {2**n} Decoder with Enable", ["Exactly one output is 1 when E = 1"])
    e = c.inp("E"); s = c.inp(*["A", "B", "C"][:n])
    for mm in range(2 ** n):
        c.out(f"D{mm}", c.AND(e, *[s[i] if mm >> (n - 1 - i) & 1 else ~s[i] for i in range(n)]))
    q.part(c, comb(c, lambda e, *b, n=n: [int(e and num(b) == k) for k in range(2 ** n)]))

q = Q("57", "4:16 Decoder using Two 3:8 Decoders", U, "F",
      "To build a 4-to-16 decoder from two 3-to-8 decoders with enable.",
      "The three low bits B, C, D go to both 3:8 decoders. The MSB A selects which decoder is enabled: A' "
      "enables the first (outputs D0-D7) and A enables the second (outputs D8-D15).",
      ["Decoder 1: E = A' -> D0..D7", "Decoder 2: E = A -> D8..D15"])
c = C("57", "4 to 16 Decoder", ["A' enables the upper 3:8 decoder, A enables the lower one"])
a, b, cc, d = c.inp("A", "B", "C", "D")
lo = c.SUB(DEC38E, ~a, b, cc, d); hi = c.SUB(DEC38E, a, b, cc, d)
for k in range(8):
    c.out(f"D{k}", lo[k])
for k in range(8):
    c.out(f"D{k+8}", hi[k])
q.part(c, comb(c, lambda *b: [int(num(b) == k) for k in range(16)]))

q = Q("58", "Adders using Decoders", U, "N",
      "To implement a full adder with a 3:8 decoder and two OR gates, and a half adder with a 2:4 decoder.",
      "A decoder generates all minterms of its inputs, so any function in SOP form can be made by ORing the "
      "decoder outputs of its minterms. Full adder: S = Sum m(1,2,4,7), C = Sum m(3,5,6,7). Half adder: "
      "S = x XOR y = D1 + D2 and C = D3.",
      ["FA: S = D1 + D2 + D4 + D7,  C = D3 + D5 + D6 + D7", "HA: S = D1 + D2,  C = D3"])
c = C("58a", "Full Adder using 3x8 Decoder", ["S = D1+D2+D4+D7,  C = D3+D5+D6+D7   (enable tied to 1)"])
x, y, z = c.inp("x", "y", "z"); one = c.const(1)
D = c.SUB(DEC38E, one, x, y, z)
c.out("S", c.OR(D[1], D[2], D[4], D[7])); c.out("C", c.OR(D[3], D[5], D[6], D[7]))
q.part(c, comb(c, FAF))
c = C("58b", "Half Adder using 2x4 Decoder", ["S = x XOR y = D1 + D2,  C = D3"])
x, y = c.inp("x", "y")
D = c.SUB(DEC24, x, y)
c.out("S", c.OR(D[1], D[2])); c.out("C", D[3])
q.part(c, comb(c, lambda x, y: (x ^ y, x & y)))

q = Q("59", "1:4 Demultiplexer with Enable", U, "N,L",
      "To design a 1-to-4 demultiplexer with an enable input.",
      "A demultiplexer sends one data input to one of 2^n outputs chosen by n select lines (a 'data "
      "distributor'). Y_k = E.D.(minterm k of S1S0). With D held at 1 the same circuit works as a 2:4 decoder "
      "with enable, which is why decoders and demultiplexers are the same IC.",
      ["Y0 = E D S1'S0'", "Y1 = E D S1'S0", "Y2 = E D S1S0'", "Y3 = E D S1S0"])
c = C("59", "1 to 4 Demultiplexer", ["Data D is routed to output Y(S1S0) when E = 1"])
e, s1, s0, d = c.inp("E", "S1", "S0", "D")
for k in range(4):
    c.out(f"Y{k}", c.AND(e, d, s1 if k & 2 else ~s1, s0 if k & 1 else ~s0))
q.part(c, comb(c, lambda e, s1, s0, d: [int(e and d and s1 * 2 + s0 == k) for k in range(4)]))

q = Q("60", "Full Subtractor using 1:8 Demultiplexer", U, "N",
      "To implement a full subtractor using a 1-to-8 demultiplexer and OR gates.",
      "With the data input I = 1 and A, B, Bin on the select lines, the demultiplexer output Y_m is 1 only for "
      "minterm m. ORing the outputs for D = Sum m(1,2,4,7) and Bo = Sum m(1,2,3,7) gives the full subtractor.",
      ["D = Y1 + Y2 + Y4 + Y7", "Bo = Y1 + Y2 + Y3 + Y7", "Keep data input I = 1"])
c = C("60", "Full Subtractor using DEMUX", ["Set I = 1.  D = Y1+Y2+Y4+Y7,  Bo = Y1+Y2+Y3+Y7"])
i_, a, b, bi = c.inp("I", "A", "B", "Bin")
Y = c.SUB(DMX18, i_, a, b, bi)
c.out("D", c.OR(Y[1], Y[2], Y[4], Y[7])); c.out("Bo", c.OR(Y[1], Y[2], Y[3], Y[7]))
q.part(c, comb(c, lambda i_, a, b, bi: tuple(i_ & v for v in FSF(a, b, bi))))

# ------------------------------------------------------------------ encoders
def onehot_rows(n_in, fn):
    rows = []
    for k in range(n_in):
        rows.append(([int(j == k) for j in range(n_in)], tuple(fn(k))))
    return rows


q = Q("61", "8:3 Encoder (Octal to Binary)", U, "N,F,L",
      "To design an 8-to-3 line encoder (octal to binary).",
      "An encoder does the reverse of a decoder: when exactly one of its 2^n inputs is 1 it outputs that "
      "input's number in binary. Each output is the OR of the inputs whose number has a 1 in that bit.",
      ["Y2 = D4 + D5 + D6 + D7", "Y1 = D2 + D3 + D6 + D7", "Y0 = D1 + D3 + D5 + D7"])
c = C("61", "8 to 3 Encoder", ["Only one input may be 1 at a time"])
D = c.inp(*[f"D{k}" for k in range(8)])
for bit, lab in ((2, "Y2"), (1, "Y1"), (0, "Y0")):
    c.out(lab, c.OR(*[D[k] for k in range(8) if k >> bit & 1]))
q.part(c, onehot_rows(8, lambda k: bitsof(k, 3)), "Valid inputs: exactly one line high.")

q = Q("62", "Decimal to BCD and Hexadecimal to Binary Encoders", U, "N,F",
      "To design a decimal (10-line) to BCD encoder and a hexadecimal (16-line) to binary encoder.",
      "Both are simple encoders built from OR gates. For the decimal encoder A = D8 + D9, B = D4+D5+D6+D7, "
      "C = D2+D3+D6+D7, D = D1+D3+D5+D7+D9. The hexadecimal encoder ORs the eight inputs that have a 1 in each "
      "of the four output bits. Input 0 is not connected because its code is 0000.",
      ["Decimal: A = 8+9, B = 4+5+6+7, C = 2+3+6+7, D = 1+3+5+7+9",
       "Hex: B3 = 8..15, B2 = 4-7,12-15, B1 = 2,3,6,7,10,11,14,15, B0 = odd inputs"])
for tag, n_in, outl in (("62a", 10, ["A", "B", "C", "D"]), ("62b", 16, ["B3", "B2", "B1", "B0"])):
    c = C(tag, "Decimal to BCD Encoder" if n_in == 10 else "Hexadecimal to Binary Encoder",
          ["Only one input may be 1 at a time"])
    D = c.inp(*[f"D{k}" for k in range(n_in)])
    for bit, lab in zip((3, 2, 1, 0), outl):
        c.out(lab, c.OR(*[D[k] for k in range(n_in) if k >> bit & 1]))
    q.part(c, onehot_rows(n_in, lambda k: bitsof(k, 4)), "Valid inputs: exactly one line high.")

q = Q("63", "4:2 Priority Encoder", U, "N,F",
      "To design a 4-input priority encoder with a valid output V.",
      "If more than one input is 1, a priority encoder outputs the code of the highest-priority input (D3 "
      "highest). V = 1 shows that at least one input is active. From the K-maps (with X for lower-priority "
      "inputs): Y1 = D2 + D3, Y0 = D3 + D1D2', V = D0 + D1 + D2 + D3.",
      ["Y1 = D2 + D3", "Y0 = D3 + D1 D2'", "V = D0 + D1 + D2 + D3"])
c = C("63", "4 to 2 Priority Encoder", ["D3 has the highest priority; V = 1 when any input is 1"])
d3, d2, d1, d0 = c.inp("D3", "D2", "D1", "D0")
c.out("Y1", c.OR(d2, d3)); c.out("Y0", c.OR(d3, c.AND(d1, ~d2))); c.out("V", c.OR(d0, d1, d2, d3))


def prio(d3, d2, d1, d0):
    for k, v in ((3, d3), (2, d2), (1, d1), (0, d0)):
        if v:
            return (k >> 1, k & 1, 1)
    return (0, 0, 0)


q.part(c, comb(c, prio))

# ------------------------------------------------------------------ multiplexers
q = Q("64", "2:1, 4:1 (with Enable) and 8:1 Multiplexers", U, "N,F,L",
      "To design 2:1, 4:1 (with enable) and 8:1 multiplexers using gates.",
      "A multiplexer (data selector) connects one of 2^n data inputs to the single output according to n "
      "select lines. Each data input is ANDed with its select minterm and all products are ORed. An enable "
      "input forces the output to 0 when E = 0.",
      ["2:1  Y = S'I0 + SI1", "4:1  Y = E(S1'S0'I0 + S1'S0I1 + S1S0'I2 + S1S0I3)",
       "8:1  Y = Sum over k of (minterm_k(S2S1S0) . I_k)"])
c = C("64a", "2 to 1 Multiplexer", ["Y = S'I0 + S I1"])
s, i0, i1 = c.inp("S", "I0", "I1")
c.out("Y", c.OR(c.AND(~s, i0), c.AND(s, i1)))
q.part(c, comb(c, lambda s, i0, i1: i1 if s else i0))
c = C("64b", "4 to 1 Multiplexer with Enable", ["Y = I(S1S0) when E = 1, else 0"])
e, s1, s0 = c.inp("E", "S1", "S0"); I = c.inp("I0", "I1", "I2", "I3")
c.out("Y", c.OR(*[c.AND(e, s1 if k & 2 else ~s1, s0 if k & 1 else ~s0, I[k]) for k in range(4)]))
q.part(c, comb(c, lambda e, s1, s0, *I: e & I[s1 * 2 + s0]))
c = C("64c", "8 to 1 Multiplexer", ["Y = I(S2S1S0)"])
S = c.inp("S2", "S1", "S0"); I = c.inp(*[f"I{k}" for k in range(8)])
c.out("Y", c.OR(*[c.AND(*[S[i] if k >> (2 - i) & 1 else ~S[i] for i in range(3)], I[k]) for k in range(8)]))
q.part(c, comb(c, lambda *b: b[3 + num(b[:3])]))


def mux_inputs(c, n_sel, ones, a, total_vars):
    """For F with first variable 'a' on the data lines: return data-line signals."""
    res = []
    for k in range(2 ** n_sel):
        lo, hi = k in ones, (k + 2 ** n_sel) in ones
        if lo and hi:
            res.append(("1", c.const(1)))
        elif not lo and not hi:
            res.append(("0", c.const(0)))
        elif hi:
            res.append(("A", a))
        else:
            res.append(("A'", ~a))
    return res


q = Q("65", "F(A,B,C) = Sum m(1,3,5,6) using 4:1 Multiplexer", U, "N",
      "To implement F(A,B,C) = Sum m(1,3,5,6) using a 4-to-1 multiplexer.",
      "B and C are applied to the select lines. For each data input I_k the two minterms k (A = 0) and k + 4 "
      "(A = 1) are compared in an implementation table: both in F -> 1, neither -> 0, only the A = 1 one -> A, "
      "only the A = 0 one -> A'.", [])
c = C("65", "Function using 4x1 MUX", ["Select lines B, C;  data inputs from the implementation table"])
a, b, cc = c.inp("A", "B", "C")
ins = mux_inputs(c, 2, {1, 3, 5, 6}, a, 3)
q.exprs += ["Implementation table:  " + ",  ".join(f"I{k} = {v}" for k, (v, _) in enumerate(ins))]
(y,) = c.SUB(MUX4, b, cc, *[s for _, s in ins])
c.out("F", y)
q.part(c, comb(c, fn_of([1, 3, 5, 6])))

ones66 = [1, 3, 4, 11, 12, 13, 14, 15]
q = Q("66", "F(A,B,C,D) = Sum m(1,3,4,11,12,13,14,15) using 8:1 Multiplexer", U, "N",
      "To implement a 4-variable function with an 8-to-1 multiplexer.",
      "Three variables B, C, D drive the select lines and the fourth variable A (with 0 and 1) is used on the "
      "data lines. The implementation table lists minterms 0-7 (A' row) and 8-15 (A row); circling the "
      "minterms of F in each column gives each data input.", [])
c = C("66", "Function using 8x1 MUX", ["Select lines B, C, D;  A, A', 0, 1 on the data lines"])
a, b, cc, d = c.inp("A", "B", "C", "D")
ins = mux_inputs(c, 3, set(ones66), a, 4)
q.exprs += ["Implementation table:  " + ",  ".join(f"I{k} = {v}" for k, (v, _) in enumerate(ins))]
(y,) = c.SUB(MUX8, b, cc, d, *[s for _, s in ins])
c.out("F", y)
q.part(c, comb(c, fn_of(ones66)))

# ------------------------------------------------------------------ PLDs
q = Q("67", "ROM and PLA Implementation", U, "N",
      "To implement combinational functions in ROM form (decoder + OR array) and in PLA form "
      "(programmable AND array + OR array).",
      "A ROM contains a fixed decoder (all minterms) and a programmable OR array: each output ORs the "
      "minterms where it is 1. Here an 8 x 6 ROM gives the square of a 3-bit number. A PLA has programmable "
      "AND and OR arrays, so only the product terms actually needed are made and they can be shared "
      "(AC is shared by F1 and F2). A PAL has a programmable AND array but a fixed OR array.",
      ["ROM: Q = N^2 (N = 0..7)", "PLA: F1 = AB' + AC + A'BC',  F2 = AC + BC"], star=False)
c = C("67a", "ROM (Decoder + OR array) - Squares", ["Q5..Q0 = N^2 : each output ORs the decoder lines where it is 1"])
n2, n1, n0 = c.inp("N2", "N1", "N0"); one = c.const(1); zero = c.const(0)
D = c.SUB(DEC38E, one, n2, n1, n0)
for bit in range(5, -1, -1):
    ms = [k for k in range(8) if (k * k) >> bit & 1]
    c.out(f"Q{bit}", c.OR(*[D[k] for k in ms]) if len(ms) > 1 else (D[ms[0]] if ms else zero))
q.part(c, comb(c, lambda *b: bitsof(num(b) ** 2, 6)))
c = C("67b", "PLA - Shared Product Terms", ["F1 = AB' + AC + A'BC'     F2 = AC + BC   (AC is shared)"])
a, b, cc = c.inp("A", "B", "C")
ac = c.AND(a, cc)
c.out("F1", c.OR(c.AND(a, ~b), ac, c.AND(~a, b, ~cc))); c.out("F2", c.OR(ac, c.AND(b, cc)))
q.part(c, comb(c, lambda a, b, cc: ((a & (1 - b)) | (a & cc) | ((1 - a) & b & (1 - cc)), (a & cc) | (b & cc))))
