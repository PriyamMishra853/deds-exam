"""Unit 1: number systems, codes, Boolean algebra, K-maps."""
from qbase import Q, C, comb, num, bitsof, fn_of, canon_sop, sop_expr, pos_expr
import boolmin as bm

U = "Unit 1 - Number Systems, Codes and Boolean Algebra"
UK = "Unit 1 - Boolean Minimisation and Karnaugh Maps"

# ---------------------------------------------------------------- Q1
q = Q("01", "Basic Logic Gates", U, "F,L",
      "To verify the truth tables of the basic logic gates AND, OR, NOT, NAND, NOR, XOR and XNOR.",
      "Logic gates are the building blocks of digital circuits. AND gives 1 only when all inputs are 1; "
      "OR gives 1 when any input is 1; NOT inverts. NAND and NOR are the complements of AND and OR and are "
      "called universal gates. XOR gives 1 when the inputs differ and XNOR gives 1 when they are equal.",
      ["AND: Y = A.B", "OR: Y = A + B", "NOT: Y = A'", "NAND: Y = (A.B)'", "NOR: Y = (A + B)'",
       "XOR: Y = A'B + AB' = A XOR B", "XNOR: Y = AB + A'B'"])
c = C("01", "Basic Logic Gates", ["Inputs A, B  ->  outputs of all seven basic gates"])
a, b = c.inp("A", "B")
c.out("AND", c.AND(a, b)); c.out("OR", c.OR(a, b)); c.out("NOT_A", c.NOT(a, gate=True))
c.out("NAND", c.NAND(a, b)); c.out("NOR", c.NOR(a, b)); c.out("XOR", c.XOR(a, b)); c.out("XNOR", c.XNOR(a, b))
q.part(c, comb(c, lambda a, b: (a & b, a | b, 1 - a, 1 - (a & b), 1 - (a | b), a ^ b, 1 - (a ^ b))))

# ---------------------------------------------------------------- Q2
q = Q("02", "De Morgan's Theorems", U, "N",
      "To verify De Morgan's first and second theorems using logic gates.",
      "De Morgan's theorems show how to complement AND/OR expressions. Theorem 1: the complement of a product "
      "equals the sum of the complements. Theorem 2: the complement of a sum equals the product of the "
      "complements. The circuit builds both sides of each theorem; equal outputs for every input prove them.",
      ["Theorem 1: (A.B)' = A' + B'", "Theorem 2: (A + B)' = A'.B'"])
c = C("02", "De Morgans Theorems", ["T1: (AB)' = A'+B'     T2: (A+B)' = A'B'   (compare L and R outputs)"])
a, b = c.inp("A", "B")
c.out("L1", c.NOT(c.AND(a, b), gate=True)); c.out("R1", c.OR(~a, ~b))
c.out("L2", c.NOT(c.OR(a, b), gate=True)); c.out("R2", c.AND(~a, ~b))
q.part(c, comb(c, lambda a, b: (1 - (a & b),) * 2 + (1 - (a | b),) * 2))

# ---------------------------------------------------------------- Q3
q = Q("03", "Redundancy (Consensus) Theorem", U, "N",
      "To verify the redundancy (consensus) theorem AB + A'C + BC = AB + A'C.",
      "In the expression AB + A'C + BC the term BC is redundant: whenever B=C=1 either A=1 (AB=1) or A=0 "
      "(A'C=1). Conditions for the theorem: three variables, each appears twice, one variable is "
      "complemented and the redundant term is formed by the other two. Both circuits give identical outputs.",
      ["F1 = AB + A'C + BC", "F2 = AB + A'C   (F1 = F2)"])
c = C("03", "Redundancy Theorem", ["F1 = AB + A'C + BC   and   F2 = AB + A'C  are always equal"])
a, b, cc = c.inp("A", "B", "C")
ab, ac = c.AND(a, b), c.AND(~a, cc)
c.out("F1", c.OR(ab, ac, c.AND(b, cc))); c.out("F2", c.OR(ab, ac))
q.part(c, comb(c, lambda a, b, cc: ((a & b) | ((1 - a) & cc),) * 2))

# ---------------------------------------------------------------- Q4
q = Q("04", "4-bit Binary to Gray Code Converter", U, "N,F",
      "To design and verify a 4-bit binary to Gray code converter.",
      "Gray code (reflected binary / unit-distance code) changes only one bit between successive values, "
      "which reduces switching errors. Rule: the MSB is copied; every other Gray bit is the XOR of the "
      "binary bit and the binary bit to its left.",
      ["G3 = B3", "G2 = B3 XOR B2", "G1 = B2 XOR B1", "G0 = B1 XOR B0"])
c = C("04", "Binary to Gray", ["G3 = B3,  G2 = B3^B2,  G1 = B2^B1,  G0 = B1^B0"])
B3, B2, B1, B0 = c.inp("B3", "B2", "B1", "B0")
c.out("G3", B3); c.out("G2", c.XOR(B3, B2)); c.out("G1", c.XOR(B2, B1)); c.out("G0", c.XOR(B1, B0))
q.part(c, comb(c, lambda *b: bitsof(num(b) ^ (num(b) >> 1), 4)))

# ---------------------------------------------------------------- Q5
q = Q("05", "4-bit Gray to Binary Code Converter", U, "N,F",
      "To design and verify a 4-bit Gray to binary code converter.",
      "To convert Gray to binary the MSB is copied, then each binary bit is the XOR of the previous binary "
      "bit (already found) and the current Gray bit. The XOR gates therefore form a chain.",
      ["B3 = G3", "B2 = B3 XOR G2", "B1 = B2 XOR G1", "B0 = B1 XOR G0"])
c = C("05", "Gray to Binary", ["B3 = G3,  B2 = B3^G2,  B1 = B2^G1,  B0 = B1^G0"])
G3, G2, G1, G0 = c.inp("G3", "G2", "G1", "G0")
b2 = c.XOR(G3, G2); b1 = c.XOR(b2, G1); b0 = c.XOR(b1, G0)
c.out("B3", G3); c.out("B2", b2); c.out("B1", b1); c.out("B0", b0)


def g2b(*g):
    v = num(g); r = v
    while v:
        v >>= 1; r ^= v
    return bitsof(r, 4)


q.part(c, comb(c, g2b))

# ---------------------------------------------------------------- Q6
CODE2421 = [0b0000, 0b0001, 0b0010, 0b0011, 0b0100, 0b1011, 0b1100, 0b1101, 0b1110, 0b1111]
q = Q("06", "BCD to 2421 Code Converter", U, "N",
      "To design a BCD (8421) to 2421 code converter using K-maps (inputs 10-15 are don't-cares).",
      "2421 is a weighted, self-complementing code: the 9's complement of a digit is obtained by inverting its "
      "code. Digits 0-4 are the same as BCD, digits 5-9 are 1011, 1100, 1101, 1110, 1111. Each output bit is "
      "minimised with a 4-variable K-map using the unused combinations 10-15 as don't-cares.", [], star=False)
names = ["A", "B", "C", "D"]
c = C("06", "BCD to 2421", ["Inputs ABCD = BCD digit 0-9 (10-15 not used)"])
sig = c.inp(*names)
bld = bm.Builder(c, sig)
outs = []
for k, lab in enumerate(["W", "X", "Y", "Z"]):
    ones = [d for d in range(10) if CODE2421[d] >> (3 - k) & 1]
    t = q.kmap(names, ones, range(10, 16), label=lab)
    q.exprs.append(f"{lab} = {sop_expr(t, names)}")
    c.out(lab, bld.sop(t))
q.part(c, [(bitsof(d, 4), tuple(bitsof(CODE2421[d], 4))) for d in range(10)], "Rows 10-15 are don't-care inputs.")

# ---------------------------------------------------------------- Q7
q = Q("07", "4-bit Binary to BCD Converter", U, "N",
      "To convert a 4-bit binary number (0-15) into a 2-digit BCD number.",
      "Binary 0-15 needs two BCD digits: a tens bit T and a ones digit O3O2O1O0. With the shift-and-add-3 "
      "(double dabble) method, 3 is added to a BCD digit whenever it is 5 or more before shifting; for a "
      "4-bit input this is equivalent to adding 6 when the value is 10 or more. The resulting truth table is "
      "minimised with K-maps to give the gate circuit.", [])
names = ["B3", "B2", "B1", "B0"]
c = C("07", "Binary to BCD", ["Input 0-15 -> tens digit T and ones digit O3..O0"])
sig = c.inp(*names)
bld = bm.Builder(c, sig)
for k, lab in enumerate(["T", "O3", "O2", "O1", "O0"]):
    ones = [n for n in range(16) if (((n // 10) << 4) | (n % 10)) >> (4 - k) & 1]
    t = q.kmap(names, ones, label=lab)
    q.exprs.append(f"{lab} = {sop_expr(t, names)}")
    c.out(lab, bld.sop(t))
q.part(c, comb(c, lambda *b: [num(b) // 10] + bitsof(num(b) % 10, 4)))

# ---------------------------------------------------------------- Q8
q = Q("08", "1's and 2's Complement Generator", U, "N",
      "To design a circuit that produces the 1's complement and 2's complement of a 4-bit number.",
      "The 1's complement (r-1's complement) inverts every bit. The 2's complement (r's complement) is the "
      "1's complement plus 1. Bit by bit: copy bits from the LSB up to and including the first 1, then invert "
      "the rest - so T_i = B_i XOR (B_{i-1} + ... + B_0). 2's complement is used for subtraction.",
      ["1's: O_i = B_i'", "T0 = B0", "T1 = B1 XOR B0", "T2 = B2 XOR (B1 + B0)", "T3 = B3 XOR (B2 + B1 + B0)"])
c = C("08", "1s and 2s Complement", ["O = 1's complement,  T = 2's complement of B3B2B1B0"])
B3, B2, B1, B0 = c.inp("B3", "B2", "B1", "B0")
for lab, s in zip(["O3", "O2", "O1", "O0"], [B3, B2, B1, B0]):
    c.out(lab, c.NOT(s, gate=True))
o1 = c.OR(B1, B0); o2 = c.OR(B2, o1)
c.out("T3", c.XOR(B3, o2)); c.out("T2", c.XOR(B2, o1)); c.out("T1", c.XOR(B1, B0)); c.out("T0", B0)
q.part(c, comb(c, lambda *b: bitsof(15 - num(b), 4) + bitsof((16 - num(b)) % 16, 4)))

# ---------------------------------------------------------------- Q9
q = Q("09", "Even Parity Generator and Checker", U, "N",
      "To design a 4-bit even parity generator and a 5-bit even parity checker.",
      "A parity bit is added to data so that the total number of 1s is even (even parity). The generator "
      "output is the XOR of all data bits (the K-map is a checkerboard, so no grouping is possible). At the "
      "receiver the checker XORs all bits including the parity bit; output 1 means an error is detected.",
      ["P = B3 XOR B2 XOR B1 XOR B0", "Error (PEC) = P XOR B3 XOR B2 XOR B1 XOR B0"])
c = C("09a", "Even Parity Generator", ["P = B3 ^ B2 ^ B1 ^ B0"])
s = c.inp("B3", "B2", "B1", "B0")
c.out("P", c.XOR(c.XOR(s[0], s[1]), c.XOR(s[2], s[3])))
q.part(c, comb(c, lambda *b: sum(b) & 1))
c = C("09b", "Even Parity Checker", ["ERR = P ^ B3 ^ B2 ^ B1 ^ B0  (1 = error)"])
s = c.inp("P", "B3", "B2", "B1", "B0")
c.out("ERR", c.XOR(c.XOR(c.XOR(s[0], s[1]), c.XOR(s[2], s[3])), s[4]))
q.part(c, comb(c, lambda *b: sum(b) & 1))

# ---------------------------------------------------------------- Q10
q = Q("10", "Hamming (7,4) Code Generator", U, "N",
      "To generate the 7-bit Hamming code for 4 data bits (even parity).",
      "Hamming code adds parity bits at positions 1, 2 and 4 (powers of 2). P1 checks positions 1,3,5,7; "
      "P2 checks 2,3,6,7; P4 checks 4,5,6,7. Data bits sit at positions 3, 5, 6, 7. The code can detect and "
      "correct any single-bit error.",
      ["P1 = D3 XOR D5 XOR D7", "P2 = D3 XOR D6 XOR D7", "P4 = D5 XOR D6 XOR D7",
       "Code word = P1 P2 D3 P4 D5 D6 D7"])
c = C("10", "Hamming Code Generator", ["P1 = D3^D5^D7,  P2 = D3^D6^D7,  P4 = D5^D6^D7"])
D3, D5, D6, D7 = c.inp("D3", "D5", "D6", "D7")
p1, p2, p4 = c.XOR(D3, D5, D7), c.XOR(D3, D6, D7), c.XOR(D5, D6, D7)
for lab, s in zip(["C1", "C2", "C3", "C4", "C5", "C6", "C7"], [p1, p2, D3, p4, D5, D6, D7]):
    c.out(lab, s)


def ham(d3, d5, d6, d7):
    return (d3 ^ d5 ^ d7, d3 ^ d6 ^ d7, d3, d5 ^ d6 ^ d7, d5, d6, d7)


q.part(c, comb(c, ham))

# ---------------------------------------------------------------- Q11
q = Q("11", "Hamming Code Error Detector and Corrector", U, "N",
      "To detect and correct a single-bit error in a received 7-bit Hamming code word.",
      "The receiver recomputes three parity checks to form the syndrome S4 S2 S1. A syndrome of 000 means "
      "no error; otherwise its binary value is the position of the wrong bit. The corresponding data bit is "
      "inverted using XOR to obtain the corrected data.",
      ["S1 = C1^C3^C5^C7, S2 = C2^C3^C6^C7, S4 = C4^C5^C6^C7",
       "D3 = C3 ^ (S4'S2S1), D5 = C5 ^ (S4S2'S1), D6 = C6 ^ (S4S2S1'), D7 = C7 ^ (S4S2S1)"], star=False)
c = C("11", "Hamming Error Corrector", ["Syndrome S4S2S1 = position of the error; data bits are corrected"])
cw = c.inp("C1", "C2", "C3", "C4", "C5", "C6", "C7")
s1 = c.XOR(cw[0], cw[2], cw[4], cw[6]); s2 = c.XOR(cw[1], cw[2], cw[5], cw[6]); s4 = c.XOR(cw[3], cw[4], cw[5], cw[6])
n1, n2, n4 = c.NOT(s1), c.NOT(s2), c.NOT(s4)
c.out("S4", s4); c.out("S2", s2); c.out("S1", s1)
c.out("D3", c.XOR(cw[2], c.AND(n4, s2, s1))); c.out("D5", c.XOR(cw[4], c.AND(s4, n2, s1)))
c.out("D6", c.XOR(cw[5], c.AND(s4, s2, n1))); c.out("D7", c.XOR(cw[6], c.AND(s4, s2, s1)))


def hamc(*cw):
    s1 = cw[0] ^ cw[2] ^ cw[4] ^ cw[6]; s2 = cw[1] ^ cw[2] ^ cw[5] ^ cw[6]; s4 = cw[3] ^ cw[4] ^ cw[5] ^ cw[6]
    pos = s4 * 4 + s2 * 2 + s1
    fixed = list(cw)
    if pos:
        fixed[pos - 1] ^= 1
    return (s4, s2, s1, fixed[2], fixed[4], fixed[5], fixed[6])


q.part(c, comb(c, hamc))

# ---------------------------------------------------------------- Q12
q = Q("12", "Majority Function", U, "N",
      "To design a 3-input majority circuit whose output is 1 when two or more inputs are 1.",
      "Truth table: F = 1 for minterms 3, 5, 6, 7. Canonical SOP A'BC + AB'C + ABC' + ABC is simplified "
      "(K-map or Boolean algebra) to AB + BC + CA. The same function is the carry of a full adder.",
      ["F = Sum m(3,5,6,7) = AB + BC + CA"])
q.kmap(["A", "B", "C"], [3, 5, 6, 7])
c = C("12", "Majority Function", ["F = AB + BC + CA"])
a, b, cc = c.inp("A", "B", "C")
c.out("F", c.OR(c.AND(a, b), c.AND(b, cc), c.AND(a, cc)))
q.part(c, comb(c, lambda a, b, cc: int(a + b + cc >= 2)))

# ================================================================= K-MAP BLOCK
q = Q("13", "Lab Assignment Expressions", UK, "F",
      "To implement the Boolean expressions given in Lab Assignments 1 and 2 with basic gates.",
      "Each expression is built directly from its operators: product terms use AND gates, sums use OR gates "
      "and complemented variables use NOT gates. F4 and F5 are the XOR and XNOR functions written in SOP form.",
      ["F1 = AB' + C", "F2 = (A + B)C", "F3 = AB + C", "F4 = AB' + A'B", "F5 = AB + A'B'"])
c = C("13", "Lab Assignment Expressions", ["F1=AB'+C  F2=(A+B)C  F3=AB+C  F4=AB'+A'B  F5=AB+A'B'"])
a, b, cc = c.inp("A", "B", "C")
c.out("F1", c.OR(c.AND(a, ~b), cc)); c.out("F2", c.AND(c.OR(a, b), cc)); c.out("F3", c.OR(c.AND(a, b), cc))
c.out("F4", c.OR(c.AND(a, ~b), c.AND(~a, b))); c.out("F5", c.OR(c.AND(a, b), c.AND(~a, ~b)))
q.part(c, comb(c, lambda a, b, cc: ((a & (1 - b)) | cc, (a | b) & cc, (a & b) | cc, a ^ b, 1 - (a ^ b))))

q = Q("14", "Simplification of AC + B'C + ABC' (Practice-01)", UK, "F",
      "To show that AC + B'C + ABC' = Sum m(1,5,6,7) = Prod M(0,2,3,4) and implement its minimal SOP and POS forms.",
      "Expanding each term gives the minterms 1, 5, 6, 7, so the zeros are 0, 2, 3, 4 (maxterm list). "
      "Grouping the 1s on a K-map gives the minimal SOP; grouping the 0s gives the minimal POS. All three "
      "outputs are identical for every input.", [])
names = ["A", "B", "C"]
t = q.kmap(names, [1, 5, 6, 7])
tp = q.kmap(names, [1, 5, 6, 7], form="POS", label="F (POS)")
q.exprs += ["Given: F = AC + B'C + ABC' = Sum m(1,5,6,7) = Prod M(0,2,3,4)",
            f"Minimal SOP: F = {sop_expr(t, names)}", f"Minimal POS: F = {pos_expr(tp, names)}"]
c = C("14", "Practice-01 Simplification", ["F_GIVEN = AC+B'C+ABC'   F_SOP = " + sop_expr(t, names) +
                                          "   F_POS = " + pos_expr(tp, names)])
sg = c.inp(*names); bld = bm.Builder(c, sg)
a, b, cc = sg
c.out("F_GIVEN", c.OR(c.AND(a, cc), c.AND(~b, cc), c.AND(a, b, ~cc)))
c.out("F_SOP", bld.sop(t)); c.out("F_POS", bld.pos(tp))
q.part(c, comb(c, lambda *b: (int(num(b) in (1, 5, 6, 7)),) * 3))


def kmap_question(nm, title, names, ones, dcs=(), src="N", form="SOP", canonical=False, nor=False, extra="",
                  star=True):
    n = len(names)
    fdesc = f"F({','.join(names)}) = Sum m({','.join(map(str, ones))})" + \
        (f" + d({','.join(map(str, dcs))})" if dcs else "")
    if form == "POS":
        zeros = [m for m in range(2 ** n) if m not in ones and m not in dcs]
        fdesc = f"F({','.join(names)}) = Prod M({','.join(map(str, zeros))})" + \
            (f" + d({','.join(map(str, dcs))})" if dcs else "")
    q = Q(nm, title, UK, src, f"To minimise {fdesc} using a K-map and implement the minimal circuit.",
          extra or ("Adjacent cells of the K-map differ in one variable, so groups of 1, 2, 4, 8 or 16 "
                    "adjacent 1s (wrapping round the edges) eliminate variables. The largest possible groups "
                    "are chosen (prime implicants), essential ones first, until every 1 is covered."
                    + (" Don't-care cells (X) may be used as 1 when they help make bigger groups." if dcs else "")
                    + (" For POS the 0s are grouped and each group gives a sum term." if form == "POS" else "")),
          [fdesc], star=star)
    t = q.kmap(names, ones, dcs, form=form)
    expr = sop_expr(t, names) if form == "SOP" else pos_expr(t, names)
    q.exprs.append(f"Minimal {form}: F = {expr}")
    c = C(nm, title, [fdesc, f"Minimal {form}: F = {expr}"])
    sg = c.inp(*names); bld = bm.Builder(c, sg)
    if form == "SOP":
        c.out("F", bld.sop(t))
    elif nor:
        c.out("F", _pos_nor(c, sg, t))
    else:
        c.out("F", bld.pos(t))
    if canonical:
        c.out("F_CANON", canon_sop(c, sg, ones))
    on = set(ones)
    dc = set(dcs)
    rows = []
    for m in range(2 ** n):
        v = "x" if m in dc else int(m in on)
        rows.append((bitsof(m, n), (v,) * (2 if canonical else 1)))
    q.part(c, rows)
    return q


def _pos_nor(c, sg, terms_fbar):
    n = len(sg)
    level1 = []
    for t in terms_fbar:
        lits = []
        for i in range(n):
            bit = 1 << (n - 1 - i)
            if t[1] & bit:
                continue
            lits.append(~sg[i] if t[0] & bit else sg[i])
        level1.append(c.NOR(*lits) if len(lits) > 1 else c.NOT(lits[0]))
    return c.NOR(*level1)


kmap_question("15", "3-Variable K-map: Sum m(2,3,4,5)", ["x", "y", "z"], [2, 3, 4, 5], canonical=True,
              extra="The canonical SOP needs four 3-input AND gates. On the K-map the 1s form two pairs, giving "
                    "the minimal SOP x'y + xy'. The circuit builds both forms; the outputs F and F_CANON are equal.")
kmap_question("16", "3-Variable K-map: Sum m(3,4,6,7)", ["x", "y", "z"], [3, 4, 6, 7])
kmap_question("17", "3-Variable K-map: Sum m(0,2,4,5,6)", ["x", "y", "z"], [0, 2, 4, 5, 6], star=False)
kmap_question("18", "K-map with Don't Cares: Sum m(2,3,4,5) + d(6,7)", ["A", "B", "C"], [2, 3, 4, 5], [6, 7])
kmap_question("19", "POS using K-map (NOR-NOR): Prod M(0,1,2,4,5)", ["x", "y", "z"], [3, 6, 7], form="POS",
              nor=True, extra="The 0s (maxterms 0,1,2,4,5) are grouped to get the minimal POS. A two-level "
                              "OR-AND (POS) circuit is converted to NOR-NOR form: each OR becomes a NOR and the "
                              "final AND becomes a NOR whose inputs are the NOR outputs.")
kmap_question("20", "4-Variable K-map: Sum m(0,1,2,4,5,6,8,9,12,13,14)", ["w", "x", "y", "z"],
              [0, 1, 2, 4, 5, 6, 8, 9, 12, 13, 14])
kmap_question("21", "4-Variable K-map: Sum m(0,2,3,5,7,8,9,10,11,13,15)", ["A", "B", "C", "D"],
              [0, 2, 3, 5, 7, 8, 9, 10, 11, 13, 15])
kmap_question("22", "4-Variable K-map with Don't Cares", ["w", "x", "y", "z"], [1, 3, 7, 11, 15], [0, 2, 5])
kmap_question("23", "4-Variable POS: Sum m(1,3,4,5,9,11,14,15)", ["A", "B", "C", "D"],
              [1, 3, 4, 5, 9, 11, 14, 15], form="POS")

# Q24 prime & essential prime implicants
names = ["A", "B", "C", "D"]; ones = [0, 2, 3, 4, 5, 7, 8, 10, 13, 15]
q = Q("24", "Prime and Essential Prime Implicants", UK, "N",
      "To find all prime implicants and essential prime implicants of F(A,B,C,D) = Sum m(0,2,3,4,5,7,8,10,13,15) "
      "and implement the minimal SOP.",
      "An implicant is any group of 1s. A prime implicant (PI) is a group that cannot be made larger. An "
      "essential prime implicant (EPI) is a PI that covers at least one 1 that no other PI covers - every EPI "
      "must appear in the answer. Remaining 1s are covered with the fewest extra PIs.", [])
pis = bm.prime_implicants(4, ones)
ess = bm.essential_pis(4, ones, pis)
t = q.kmap(names, ones)
q.exprs += ["Prime implicants: " + ", ".join(bm.term_str(p, names) for p in pis),
            "Essential PIs: " + (", ".join(bm.term_str(p, names) for p in ess) or "none"),
            "Minimal SOP: F = " + sop_expr(t, names)]
c = C("24", "Prime and Essential PIs", ["F = Sum m(0,2,3,4,5,7,8,10,13,15)", "F = " + sop_expr(t, names)])
sg = c.inp(*names); bld = bm.Builder(c, sg)
c.out("F", bld.sop(t))
q.part(c, comb(c, fn_of(ones)))

kmap_question("25", "Checkerboard K-map: Sum m(1,3,4,6,9,11,12,14)", ["w", "x", "y", "z"],
              [1, 3, 4, 6, 9, 11, 12, 14],
              extra="When no two 1s are adjacent but they form a pattern of pairs in alternate columns the "
                    "map simplifies to an XOR. Here F = x'z + xz' = x XOR z, independent of w and y.")
kmap_question("26", "5-Variable K-map", ["A", "B", "C", "D", "E"], [0, 2, 4, 6, 9, 13, 21, 23, 25, 29, 31],
              extra="A 5-variable map is drawn as two 4-variable maps (A = 0 and A = 1) placed side by side. "
                    "Cells in the same position of the two maps are also adjacent, so groups may span both maps.")

names = ["A", "B", "C", "D"]; ones = [0, 1, 3, 7, 8, 9, 11, 15]
q = Q("27", "Quine-McCluskey (Tabular) Method", UK, "N",
      "To minimise Y(A,B,C,D) = Sum m(0,1,3,7,8,9,11,15) by the Quine-McCluskey method and verify with a K-map.",
      "Minterms are grouped by the number of 1s. Terms in adjacent groups that differ in one bit are combined "
      "(the bit is replaced by '-'), repeating until no more combinations are possible. Unticked terms are the "
      "prime implicants; a prime implicant chart then selects the essential ones. The result matches the K-map.",
      [])
t = q.kmap(names, ones, label="Y")
q.exprs.append("Y = " + sop_expr(t, names))
q.html = "QM"
c = C("27", "Quine-McCluskey Result", ["Y = Sum m(0,1,3,7,8,9,11,15) = " + sop_expr(t, names)])
sg = c.inp(*names); bld = bm.Builder(c, sg)
c.out("Y", bld.sop(t))
q.part(c, comb(c, fn_of(ones)))
q.qm = (4, ones)
