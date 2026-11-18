"""Unit 4: sequential logic circuits (latches, flip-flops, counters, state machines)."""
from lgen import Circuit
from qbase import Q, C, bitsof, num
import boolmin as bm

U = "Unit 4 - Sequential Logic Circuits"


# ------------------------------------------------------------------ building blocks
def nor_latch(c, s_int, r_int, clr=None):
    """Cross-coupled NOR latch.  Q = (R + CLR + Q')',  Q' = (S + Q)'."""
    qn = c.fwd()
    q = c.NOR(*([r_int, clr] if clr is not None else [r_int]), qn)
    c.bind(qn, c.NOR(s_int, q))
    return q, qn.r()


def nand_latch(c, sn, rn):
    """Cross-coupled NAND latch with active-low inputs.  Q = (S'.Q')',  Q' = (R'.Q)'."""
    qn = c.fwd()
    q = c.NAND(sn, qn)
    c.bind(qn, c.NAND(rn, q))
    return q, qn.r()


def build_dff(c, d, clk, clr):
    """Positive-edge master-slave D flip-flop (master open while CLK = 0)."""
    qm, qmn = nor_latch(c, c.AND(d, ~clk), c.AND(~d, ~clk), clr)
    return nor_latch(c, c.AND(qm, clk), c.AND(qmn, clk), clr)


def build_ms(c, s_fn, r_fn, clk, clr):
    """Master-slave (pulse triggered): master open while CLK = 1, output changes when CLK falls.
    s_fn/r_fn(q, qn) give the master set/reset inputs (feedback allowed)."""
    q_f, qn_f = c.fwd(), c.fwd()
    qm, qmn = nor_latch(c, s_fn(q_f, qn_f), r_fn(q_f, qn_f), clr)
    q, qn = nor_latch(c, c.AND(qm, ~clk), c.AND(qmn, ~clk), clr)
    c.bind(q_f, q); c.bind(qn_f, qn)
    return q, qn


def build_jk(c, j, k, clk, clr):
    return build_ms(c, lambda q, qn: c.AND(j, qn, clk), lambda q, qn: c.AND(k, q, clk), clk, clr)


def build_t(c, t, clk, clr):
    return build_ms(c, lambda q, qn: c.AND(t, qn, clk), lambda q, qn: c.AND(t, q, clk), clk, clr)


def build_sr(c, s, r, clk, clr):
    return build_ms(c, lambda q, qn: c.AND(s, clk), lambda q, qn: c.AND(r, clk), clk, clr)


def helper(name, short, ins, builder):
    h = Circuit("Helper - " + name, "Helper block: " + name, ["Used as a sub-circuit by the counters"])
    h.short = short
    sig = h.inp(*ins)
    q, qn = builder(h, *sig)
    h.out("Q", q); h.out("Qn", qn)
    return h.layout()


DFF = helper("D Flip-Flop", "D-FF", ["D", "CLK", "CLR"], build_dff)
JKFF = helper("JK Flip-Flop", "JK-FF", ["J", "K", "CLK", "CLR"], build_jk)
TFF = helper("T Flip-Flop", "T-FF", ["T", "CLK", "CLR"], build_t)
SRFF = helper("SR Flip-Flop", "SR-FF", ["S", "R", "CLK", "CLR"], build_sr)


# ------------------------------------------------------------------ behavioural models for tests
def run(steps, model, outs_fn):
    st, prev, rows = None, None, []
    for s in steps:
        st = model(prev, s, st)
        rows.append((s, outs_fn(st)))
        prev = s
    return rows


def qq(q):
    return ("x", "x") if q is None else (q, 1 - q)


def pulses(data_list, clr_first=True, n_extra=1):
    """[(data..)] -> steps (data.., CLK, CLR): clear, then for each data a full clock pulse 0-1-0."""
    steps = []
    d0 = data_list[0]
    steps.append(tuple(d0) + (0, 0))
    if clr_first:
        steps.append(tuple(d0) + (0, 1)); steps.append(tuple(d0) + (0, 0))
    for d in data_list:
        steps += [tuple(d) + (0, 0), tuple(d) + (1, 0), tuple(d) + (0, 0)]
    return steps


def ms_model(nxt):
    """master-slave: state changes on falling CLK edge using data held during the high phase."""
    def m(prev, cur, q):
        *data, clk, clr = cur
        if clr:
            return 0
        if prev is not None and prev[-2] == 1 and clk == 0 and q is not None:
            return nxt(q, *prev[:-2])
        return q
    return m


# ------------------------------------------------------------------ Q68 SR latch
q = Q("68", "SR Latch using NOR and NAND Gates", U, "N,F,L",
      "To construct and verify SR latches using cross-coupled NOR gates and cross-coupled NAND gates.",
      "A latch is the basic 1-bit memory element; its outputs are fed back to the inputs. NOR latch: S = 1 sets "
      "Q = 1, R = 1 resets Q = 0, S = R = 0 holds the previous state, S = R = 1 is not allowed (Q = Q' = 0). "
      "The NAND latch has active-low inputs S' and R': 0 sets/resets, 11 holds and 00 is forbidden.",
      ["NOR: Q = (R + Q')',  Q' = (S + Q)'", "NAND: Q = (S'.Q')',  Q' = (R'.Q)'"])
q.char = ("NOR latch", ["S", "R", "Q(t+1)", "State"],
          [["0", "0", "Q(t)", "No change"], ["0", "1", "0", "Reset"], ["1", "0", "1", "Set"], ["1", "1", "0*", "Not allowed"]])
c = C("68a", "SR Latch using NOR", ["S=1 set, R=1 reset, S=R=0 hold, S=R=1 not allowed"])
s, r = c.inp("S", "R")
qo, qno = nor_latch(c, s, r)
c.out("Q", qo); c.out("Qn", qno)


def srl(prev, cur, q):
    s, r = cur
    return 1 if s else 0 if r else q


steps = [(0, 0), (1, 0), (0, 0), (0, 1), (0, 0), (1, 0), (0, 0), (0, 1)]
q.part(c, run(steps, srl, qq))
c = C("68b", "SR Latch using NAND", ["Active-low inputs: S'=0 set, R'=0 reset, S'=R'=1 hold",
                                    "Pins start at 00 (forbidden): first make R' = 1, then S' = 1 (change one at a time)"])
sn, rn = c.inp("S'", "R'")
qo, qno = nand_latch(c, sn, rn)
c.out("Q", qo); c.out("Qn", qno)
steps = [(0, 1), (1, 1), (1, 0), (1, 1), (0, 1), (1, 1), (1, 0)]
q.part(c, run(steps, lambda p, cur, q_: 1 if cur[0] == 0 else 0 if cur[1] == 0 else q_, qq))

# ------------------------------------------------------------------ Q69 clocked SR
q = Q("69", "Clocked (Gated) SR Flip-Flop using NAND and NOR", U, "N,F,L",
      "To construct a clocked SR flip-flop (gated SR latch) using NAND gates and using NOR gates.",
      "Adding a clock (enable) input makes the latch respond to S and R only while CLK = 1; when CLK = 0 the "
      "state is held whatever S and R do. In the NAND version two input NAND gates steer S and R into a NAND "
      "latch; in the NOR version AND gates feed a NOR latch. S = R = 1 with CLK = 1 is not allowed.",
      ["Q(t+1) = S + R'Q (when CLK = 1, SR = 0)", "CLK = 0 : Q(t+1) = Q(t)"])
q.char = ("Clocked SR flip-flop", ["CLK", "S", "R", "Q(t+1)"],
          [["0", "X", "X", "Q(t)"], ["1", "0", "0", "Q(t)"], ["1", "0", "1", "0"], ["1", "1", "0", "1"], ["1", "1", "1", "Not allowed"]])
gsr_steps = [(0, 0, 0), (1, 0, 1), (0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 0), (0, 0, 1), (1, 0, 1), (0, 0, 0)]


def gsr(prev, cur, q_):
    s, r, clk = cur
    if clk:
        return 1 if s else 0 if r else q_
    return q_


c = C("69a", "Clocked SR Flip-Flop using NAND", ["Responds to S, R only while CLK = 1"])
s, r, clk = c.inp("S", "R", "CLK")
qo, qno = nand_latch(c, c.NAND(s, clk), c.NAND(r, clk))
c.out("Q", qo); c.out("Qn", qno)
q.part(c, run(gsr_steps, gsr, qq))
c = C("69b", "Clocked SR Flip-Flop using NOR", ["AND gates gate S and R with CLK into a NOR latch"])
s, r, clk = c.inp("S", "R", "CLK")
qo, qno = nor_latch(c, c.AND(s, clk), c.AND(r, clk))
c.out("Q", qo); c.out("Qn", qno)
q.part(c, run(gsr_steps, gsr, qq))

# ------------------------------------------------------------------ Q70 D latch
q = Q("70", "Gated D Latch using NAND and NOR", U, "F",
      "To construct a gated D latch using NAND gates and using NOR gates.",
      "The D latch removes the forbidden SR = 11 state by driving S with D and R with D'. While the enable "
      "(CLK) is 1 the output follows D (transparent); when it is 0 the last value is stored.",
      ["CLK = 1 : Q = D", "CLK = 0 : Q holds"])
q.char = ("Gated D latch", ["CLK", "D", "Q(t+1)"], [["0", "X", "Q(t)"], ["1", "0", "0"], ["1", "1", "1"]])
dl_steps = [(0, 1), (1, 1), (0, 0), (1, 0), (1, 1), (0, 1), (0, 0), (1, 0), (0, 1)]
dlm = lambda p, cur, q_: cur[0] if cur[1] else q_
c = C("70a", "Gated D Latch using NAND", ["Q follows D while CLK = 1"])
d, clk = c.inp("D", "CLK")
qo, qno = nand_latch(c, c.NAND(d, clk), c.NAND(~d, clk))
c.out("Q", qo); c.out("Qn", qno)
q.part(c, run(dl_steps, dlm, qq))
c = C("70b", "Gated D Latch using NOR", ["Q follows D while CLK = 1"])
d, clk = c.inp("D", "CLK")
qo, qno = nor_latch(c, c.AND(d, clk), c.AND(~d, clk))
c.out("Q", qo); c.out("Qn", qno)
q.part(c, run(dl_steps, dlm, qq))

# ------------------------------------------------------------------ Q71 D flip-flop
q = Q("71", "Edge-Triggered D Flip-Flop (Master-Slave)", U, "F,L",
      "To construct a positive-edge-triggered D flip-flop from two gated D latches (master-slave) with an "
      "asynchronous clear input.",
      "A flip-flop changes state only at a clock edge. The master latch is open while CLK = 0 and the slave "
      "while CLK = 1, so D is captured at the rising edge and appears at Q; at no time is there a direct path "
      "from D to Q. CLR = 1 forces Q = 0 immediately (used to start in a known state).",
      ["Q(t+1) = D  (at the rising edge of CLK)", "Characteristic equation: Q(t+1) = D"])
q.char = ("D flip-flop", ["CLK", "D", "Q(t+1)"], [["rising edge", "0", "0"], ["rising edge", "1", "1"], ["no edge", "X", "Q(t)"]])
q.excite = ("D excitation table", ["Q(t)", "Q(t+1)", "D"], [["0", "0", "0"], ["0", "1", "1"], ["1", "0", "0"], ["1", "1", "1"]])
c = C("71", "D Flip-Flop (positive edge)", ["Press CLR once, set D, then click CLK 0 -> 1"])
d, clk, clr = c.inp("D", "CLK", "CLR")
qo, qno = build_dff(c, d, clk, clr)
c.out("Q", qo); c.out("Qn", qno)


def dffm(prev, cur, q_):
    d, clk, clr = cur
    if clr:
        return 0
    if prev is not None and prev[1] == 0 and clk == 1 and q_ is not None:
        return d
    return q_


steps = [(0, 0, 0), (0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 0), (0, 1, 0), (1, 1, 0),
         (1, 0, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0), (0, 1, 0)]
q.part(c, run(steps, dffm, qq))

# ------------------------------------------------------------------ Q72 JK
JK_NEXT = lambda q_, j, k: (j & (1 - q_)) | ((1 - k) & q_)
q = Q("72", "JK Flip-Flop (Master-Slave)", U, "N,F,L",
      "To construct a master-slave JK flip-flop and verify its characteristic table.",
      "The JK flip-flop refines the SR flip-flop: J = K = 1 is allowed and makes the output toggle. Feeding Q "
      "and Q' back to the input gates causes the race-around problem in a simple clocked JK, so a master-slave "
      "arrangement is used: the master follows J, K while CLK = 1 and the slave copies the master when CLK "
      "falls, so the output changes only once per clock pulse.",
      ["Characteristic equation: Q(t+1) = JQ' + K'Q"])
q.char = ("JK flip-flop", ["J", "K", "Q(t+1)", "Action"],
          [["0", "0", "Q(t)", "No change"], ["0", "1", "0", "Reset"], ["1", "0", "1", "Set"], ["1", "1", "Q'(t)", "Toggle"]])
q.excite = ("JK excitation table", ["Q(t)", "Q(t+1)", "J", "K"],
            [["0", "0", "0", "X"], ["0", "1", "1", "X"], ["1", "0", "X", "1"], ["1", "1", "X", "0"]])
c = C("72", "JK Flip-Flop (master-slave)", ["Press CLR once; output changes when CLK goes 1 -> 0"])
j, k, clk, clr = c.inp("J", "K", "CLK", "CLR")
qo, qno = build_jk(c, j, k, clk, clr)
c.out("Q", qo); c.out("Qn", qno)
data = [(1, 0), (0, 0), (1, 1), (1, 1), (0, 1), (1, 1), (0, 0), (1, 0), (1, 1)]
q.part(c, run(pulses(data), ms_model(JK_NEXT), qq), "Each data row is applied with one full clock pulse 0-1-0.")

# ------------------------------------------------------------------ Q73 T
q = Q("73", "T Flip-Flop", U, "N,F,L",
      "To construct a T (toggle) flip-flop from a master-slave JK flip-flop with J = K = T.",
      "With J and K tied together as T, the flip-flop holds its state when T = 0 and toggles at every clock "
      "pulse when T = 1. T flip-flops are the basic element of binary counters (each stage divides the "
      "frequency by 2).",
      ["Characteristic equation: Q(t+1) = TQ' + T'Q = T XOR Q"])
q.char = ("T flip-flop", ["T", "Q(t+1)"], [["0", "Q(t)  (hold)"], ["1", "Q'(t)  (toggle)"]])
q.excite = ("T excitation table", ["Q(t)", "Q(t+1)", "T"], [["0", "0", "0"], ["0", "1", "1"], ["1", "0", "1"], ["1", "1", "0"]])
c = C("73", "T Flip-Flop", ["T = 1 toggles at every clock pulse (CLK 1 -> 0)"])
t, clk, clr = c.inp("T", "CLK", "CLR")
qo, qno = build_t(c, t, clk, clr)
c.out("Q", qo); c.out("Qn", qno)
data = [(1,), (1,), (0,), (1,), (0,), (1,), (1,)]
q.part(c, run(pulses(data), ms_model(lambda q_, t_: q_ ^ t_), qq), "Each row is one full clock pulse.")


# ------------------------------------------------------------------ state machines with SR flip-flops
def sr_excitation(q_, nq):
    return {(0, 0): (0, "x"), (0, 1): (1, 0), (1, 0): (0, 1), (1, 1): ("x", 0)}[(q_, nq)]


def design_sr(nbits, has_x, nxt):
    """Derive SR inputs for every flip-flop from the state table. Returns ([names], {ff: (S_terms,R_terms)}, table)."""
    names = ["A", "B"][:nbits] + (["x"] if has_x else [])
    n = len(names)
    eq, table = {}, []
    for ff in range(nbits):
        s1, sdc, r1, rdc = [], [], [], []
        for m in range(2 ** n):
            bits = bitsof(m, n)
            st = num(bits[:nbits]); x = bits[nbits] if has_x else None
            ns = nxt(st, x)
            cur, new = bits[ff], bitsof(ns, nbits)[ff]
            s, r = sr_excitation(cur, new)
            (s1 if s == 1 else sdc if s == "x" else []).append(m)
            (r1 if r == 1 else rdc if r == "x" else []).append(m)
        eq[ff] = (bm.minimise(n, s1, sdc), bm.minimise(n, r1, rdc), (s1, sdc, r1, rdc))
    for m in range(2 ** n):
        bits = bitsof(m, n)
        st = num(bits[:nbits]); x = bits[nbits] if has_x else None
        ns = nxt(st, x)
        row = [str(b) for b in bits] + [str(b) for b in bitsof(ns, nbits)]
        for ff in range(nbits):
            s, r = sr_excitation(bits[ff], bitsof(ns, nbits)[ff])
            row += [str(s).upper(), str(r).upper()]
        table.append(row)
    return names, eq, table


def sr_machine(nm, title, aim, theory, nxt, has_x, ydef=None, src="N"):
    names, eq, table = design_sr(2, has_x, nxt)
    q = Q(nm, title, U, src, aim, theory, [])
    hdr = ["A(t)", "B(t)"] + (["x"] if has_x else []) + ["A(t+1)", "B(t+1)", "SA", "RA", "SB", "RB"]
    q.state_table = (hdr, table)
    for ff, lab in ((0, "A"), (1, "B")):
        st_, rt_, (s1, sdc, r1, rdc) = eq[ff]
        q.kmap(names, s1, sdc, label="S" + lab, terms=st_)
        q.kmap(names, r1, rdc, label="R" + lab, terms=rt_)
        q.exprs.append(f"S{lab} = {bm.sop_str(st_, names)},   R{lab} = {bm.sop_str(rt_, names)}")
    if ydef:
        q.exprs.append(ydef[0])
    c = C(nm, title, ["Two SR flip-flops; press CLR once, then clock with CLK 0 -> 1 -> 0"] +
          ([" x = input"] if has_x else []))
    ins = c.inp(*(["x"] if has_x else []), "CLK", "CLR")
    if has_x:
        x, clk, clr = ins
    else:
        clk, clr = ins
    fA, fB, fAn, fBn = c.fwd(), c.fwd(), c.fwd(), c.fwd()
    lit = {0: (fA, fAn), 1: (fB, fBn)}

    def build(terms):
        if not terms:
            return c.const(0)
        ts = []
        for t in terms:
            l = []
            for i in range(len(names)):
                bit = 1 << (len(names) - 1 - i)
                if t[1] & bit:
                    continue
                pos = bool(t[0] & bit)
                if i < 2:
                    l.append(lit[i][0] if pos else lit[i][1])
                else:
                    l.append(x if pos else ~x)
            ts.append(c.AND(*l) if len(l) > 1 else l[0])
        return ts[0] if len(ts) == 1 else c.OR(*ts)

    qa, qan = c.SUB(SRFF, build(eq[0][0]), build(eq[0][1]), clk, clr)
    qb, qbn = c.SUB(SRFF, build(eq[1][0]), build(eq[1][1]), clk, clr)
    c.bind(fA, qa); c.bind(fAn, qan); c.bind(fB, qb); c.bind(fBn, qbn)
    c.out("A", qa); c.out("B", qb)
    if ydef:
        c.out("y", ydef[1](c, qa, qb, qan, qbn, x if has_x else None))
    # test: clear, then pulses with x pattern
    xs = [1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1] if has_x else [None] * 9
    steps, exp = [], []
    st = None

    def outs(s_, xv):
        if s_ is None:
            return ("x", "x") + (("x",) if ydef else ())
        o = tuple(bitsof(s_, 2))
        return o + ((ydef[2](s_, xv),) if ydef else ())

    def add(xv, clk_, clr_):
        steps.append(((xv,) if has_x else ()) + (clk_, clr_))

    rows = []
    add(xs[0], 0, 0); rows.append((steps[-1], outs(None, xs[0])))
    add(xs[0], 0, 1); st = 0; rows.append((steps[-1], outs(st, xs[0])))
    add(xs[0], 0, 0); rows.append((steps[-1], outs(st, xs[0])))
    for xv in xs:
        add(xv, 0, 0); rows.append((steps[-1], outs(st, xv)))
        add(xv, 1, 0); rows.append((steps[-1], outs(st, xv)))
        st = nxt(st, xv)
        add(xv, 0, 0); rows.append((steps[-1], outs(st, xv)))
    q.part(c, rows, "Each group of three rows is one clock pulse (CLK 0-1-0).")
    return q


sr_machine("74", "2-bit Synchronous Counter using SR Flip-Flops",
           "To design a 2-bit synchronous binary up counter (00-01-10-11-00) using SR flip-flops.",
           "Design steps: (1) state diagram, (2) state table with present and next states, (3) SR excitation "
           "for every flip-flop (0->0: S=0,R=X; 0->1: S=1,R=0; 1->0: S=0,R=1; 1->1: S=X,R=0), (4) K-maps for "
           "SA, RA, SB, RB using the X entries as don't-cares, (5) the logic diagram.",
           lambda st, x: (st + 1) % 4, False)
GRAY = [0, 1, 3, 2]
sr_machine("75", "Sequential Circuit from a State Diagram (SR Flip-Flops)",
           "To implement a given state diagram with input x and output y using SR flip-flops: the circuit moves "
           "00 -> 01 -> 11 -> 10 -> 00 when x = 1, stays in the same state when x = 0, and y = 1 in state 10.",
           "The state diagram is converted to a state table listing, for each present state and input, the "
           "next state. From the SR excitation table the required S and R inputs of flip-flops A and B are "
           "found and minimised with K-maps (X = don't care). The output y depends only on the state (Moore).",
           lambda st, x: GRAY[(GRAY.index(st) + 1) % 4] if x else st, True,
           ("y = AB'", lambda c, a, b, an, bn, x: c.AND(a, bn), lambda s_, xv: int(s_ == 2)))
sr_machine("76", "2-bit Up/Down Counter Controlled by x (SR Flip-Flops)",
           "To design a 2-bit synchronous counter that counts up when x = 1 and down when x = 0, using SR flip-flops.",
           "The counter has four states. With x = 1 the next state is (present + 1) mod 4, with x = 0 it is "
           "(present - 1) mod 4. The state table, SR excitation table and 3-variable K-maps (A, B, x) give the "
           "flip-flop input equations.",
           lambda st, x: (st + 1) % 4 if x else (st - 1) % 4, True)

# ------------------------------------------------------------------ Q77 synchronous JK counter
q = Q("77", "3-bit Synchronous Up Counter using JK Flip-Flops", U, "F",
      "To design a 3-bit synchronous binary up counter using JK flip-flops.",
      "In a synchronous counter all flip-flops share the same clock. A bit toggles when all lower bits are 1, "
      "so with JK flip-flops in toggle mode: J0 = K0 = 1, J1 = K1 = Q0, J2 = K2 = Q0Q1. The count goes "
      "000 -> 001 -> ... -> 111 -> 000.",
      ["J0 = K0 = 1", "J1 = K1 = Q0", "J2 = K2 = Q0.Q1"])
c = C("77", "3-bit Synchronous Counter (JK)", ["Press CLR once, then each clock pulse (CLK 1 -> 0) adds 1"])
clk, clr = c.inp("CLK", "CLR")
one = c.const(1)
f0, f1 = c.fwd(), c.fwd()
q0, _ = c.SUB(JKFF, one, one, clk, clr)
q1, _ = c.SUB(JKFF, q0, q0, clk, clr)
a01 = c.AND(q0, q1)
q2, _ = c.SUB(JKFF, a01, a01, clk, clr)
c.out("Q2", q2); c.out("Q1", q1); c.out("Q0", q0)


def counter_rows(n, step_fn, extra_in=()):
    rows = [((0, 0), ("x",) * n), ((0, 1), tuple([0] * n)), ((0, 0), tuple([0] * n))]
    v = 0
    for _ in range(2 ** n + 2):
        rows.append(((1, 0), tuple(bitsof(v, n))))
        v = step_fn(v)
        rows.append(((0, 0), tuple(bitsof(v, n))))
    return rows


q.part(c, counter_rows(3, lambda v: (v + 1) % 8), "Two rows per clock pulse (CLK = 1, then CLK = 0).")

# ------------------------------------------------------------------ Q78 ripple counter + shift register
q = Q("78", "Ripple Counter using T Flip-Flops and 4-bit Shift Register", U, "L",
      "To build a 3-bit asynchronous (ripple) counter using T flip-flops and a 4-bit serial-in parallel-out "
      "shift register using D flip-flops.",
      "Ripple counter: every T flip-flop has T = 1 and is clocked by the output of the previous stage, so a "
      "stage toggles when the previous one goes 1 -> 0; the change ripples through the stages (asynchronous). "
      "Shift register: D flip-flops in a chain share one clock; at each rising edge every bit moves one place "
      "(SIN -> Q0 -> Q1 -> Q2 -> Q3), so data entered serially appears in parallel after 4 clocks.",
      ["Counter: T0 = T1 = T2 = 1, CLK1 = Q0, CLK2 = Q1", "Shift register: Q0+ = SIN, Q1+ = Q0, Q2+ = Q1, Q3+ = Q2"])
c = C("78a", "3-bit Ripple Counter (T flip-flops)", ["Each stage is clocked by the previous Q (falling edge)"])
clk, clr = c.inp("CLK", "CLR")
one = c.const(1)
q0, _ = c.SUB(TFF, one, clk, clr)
q1, _ = c.SUB(TFF, one, q0, clr)
q2, _ = c.SUB(TFF, one, q1, clr)
c.out("Q2", q2); c.out("Q1", q1); c.out("Q0", q0)
q.part(c, counter_rows(3, lambda v: (v + 1) % 8), "Two rows per clock pulse (CLK = 1, then CLK = 0).")
c = C("78b", "4-bit Shift Register (SIPO, D flip-flops)", ["Data at SIN shifts one place at every rising CLK edge"])
sin, clk, clr = c.inp("SIN", "CLK", "CLR")
prev, qs = sin, []
for i in range(4):
    qi, _ = c.SUB(DFF, prev, clk, clr)
    qs.append(qi); prev = qi
for i in range(4):
    c.out(f"Q{i}", qs[i])
bits_in = [1, 0, 1, 1, 0, 0, 1, 0]
rows = [((0, 0, 0), ("x",) * 4), ((0, 0, 1), (0,) * 4), ((0, 0, 0), (0,) * 4)]
reg = [0, 0, 0, 0]
for bval in bits_in:
    rows.append(((bval, 0, 0), tuple(reg)))
    reg = [bval] + reg[:3]
    rows.append(((bval, 1, 0), tuple(reg)))
    rows.append(((bval, 0, 0), tuple(reg)))
q.part(c, rows, "Three rows per clock pulse; the register shifts at the rising edge.")
