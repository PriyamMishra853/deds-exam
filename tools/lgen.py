"""
lgen.py - tiny netlist -> Logisim 2.7.1 (.circ) generator with automatic, tidy layout.

Layout style (classic textbook):
  * input pins at the top-left, each feeding a vertical "rail" (plus a complement
    rail made by a NOT gate when A' is needed),
  * gates arranged in columns by logic level, every gate on its own horizontal band,
  * signals between columns travel on vertical "tracks" in the channel after their gate,
  * outputs are labelled pins on the right.
Every wire is split at every junction so all connections are end-to-end (Logisim-safe).
"""
import html

GATES = ("AND", "OR", "NAND", "NOR", "XOR", "XNOR")
LOGISIM_NAME = {"AND": "AND Gate", "OR": "OR Gate", "NAND": "NAND Gate", "NOR": "NOR Gate",
                "XOR": "XOR Gate", "XNOR": "XNOR Gate", "NOT": "NOT Gate", "TRI": "Controlled Buffer"}


def gate_axis(kind, size=50):
    return size + (10 if kind in ("XOR", "XNOR") else 0) + (10 if kind in ("NAND", "NOR", "XNOR") else 0)


def gate_in_offsets(kind, n, size=50):
    """Exact copy of Logisim 2.7.1 AbstractGate.getInputOffset (facing east)."""
    axis = gate_axis(kind, size)
    if n <= 3:
        if size < 40:
            ss, sd, le = -5, 10, 10
        elif size < 60 or n <= 2:
            ss, sd, le = -10, 20, 20
        else:
            ss, sd, le = -15, 30, 30
    elif n == 4 and size >= 60:
        ss, sd, le = -5, 20, 0
    else:
        ss, sd, le = -5, 10, 10
    out = []
    for i in range(n):
        if n & 1:
            dy = ss * (n - 1) + sd * i
        else:
            dy = ss * n + sd * i
            if i >= n // 2:
                dy += le
        out.append((-axis, dy))
    return out


def _cofs(nf, no, maxothers):
    m = max(nf, no)
    if m <= 1:
        mo = 15 if maxothers == 0 else 10
    elif m == 2:
        mo = 10
    else:
        mo = 5 if maxothers == 0 else 10
    return mo + 10 * ((m - nf) // 2)


def sub_geometry(n_in, n_out):
    """Logisim 2.7.1 DefaultAppearance for a circuit with n_in west pins, n_out east pins."""
    m = max(n_in, n_out)
    ow, oe = _cofs(n_in, n_out, 0), _cofs(n_out, n_in, 0)
    width = 30
    height = 30 if m < 3 else 10 * m
    ins = [(-width, ow - oe + 10 * k) for k in range(n_in)]
    outs = [(0, 10 * k) for k in range(n_out)]
    return ins, outs, (-width, -oe, width, height)  # body box relative to anchor


class Sig:
    def __init__(self, circ, kind, block=None, idx=0, inp=None):
        self.circ, self.kind, self.block, self.idx, self.inp = circ, kind, block, idx, inp
        self.ref = None  # for forward placeholders

    def r(self):
        s = self
        while s.kind == "fwd":
            if s.ref is None:
                raise ValueError("unbound forward signal")
            s = s.ref
        return s

    def __invert__(self):
        return self.circ.NOT(self)


class Block:
    def __init__(self, kind, ins, n_out=1, sub=None, label=None):
        self.kind, self.ins, self.sub, self.label = kind, list(ins), sub, label
        self.outs = []
        if kind in GATES:
            self.in_ofs = gate_in_offsets(kind, len(ins))
            self.out_ofs = [(0, 0)]
            ext = max(25, max(abs(d) for _, d in self.in_ofs) + 5)
            self.box = (-gate_axis(kind), -ext, gate_axis(kind), 2 * ext)
        elif kind == "NOT":
            self.in_ofs, self.out_ofs, self.box = [(-30, 0)], [(0, 0)], (-30, -10, 30, 20)
        elif kind == "TRI":
            self.in_ofs, self.out_ofs, self.box = [(-20, 0), (-10, 10)], [(0, 0)], (-20, -10, 20, 20)
        elif kind == "SUB":
            self.in_ofs, self.out_ofs, self.box = sub_geometry(len(ins), sub.n_out_ports)
        else:
            raise ValueError(kind)


class Circuit:
    def __init__(self, name, title=None, lines=()):
        self.name, self.title, self.lines = name, title or name, list(lines)
        self.inputs = []      # [label, Sig, need_comp, compSig]
        self.blocks = []
        self.outputs = []     # (label, Sig)
        self.seg7 = None
        self.n_out_ports = 0
        self.out_order = None

    # ---- construction API -------------------------------------------------
    def inp(self, *labels):
        res = []
        for lab in labels:
            s = Sig(self, "in")
            rec = [lab, s, False, None, None]
            s.inp = rec
            self.inputs.append(rec)
            res.append(s)
        return res[0] if len(res) == 1 else res

    def const(self, v):
        """Constant 0/1 source (Logisim Constant component) on its own rail."""
        s = Sig(self, "in")
        rec = ["%d" % v, s, False, None, v]
        s.inp = rec
        self.inputs.append(rec)
        return s

    @property
    def pins_in(self):
        return [rec[0] for rec in self.inputs if rec[4] is None]

    def fwd(self):
        return Sig(self, "fwd")

    def bind(self, f, s):
        f.ref = s

    def _blk(self, kind, ins, label=None):
        b = Block(kind, ins, label=label)
        self.blocks.append(b)
        s = Sig(self, "blk", b, 0)
        b.outs = [s]
        return s

    def g(self, kind, *ins, label=None):
        ins = [x for x in ins]
        if len(ins) == 1 and kind in GATES:
            return ins[0] if kind in ("AND", "OR") else self.NOT(ins[0])
        return self._blk(kind, ins, label)

    def AND(self, *a, **k): return self.g("AND", *a, **k)
    def OR(self, *a, **k): return self.g("OR", *a, **k)
    def NAND(self, *a, **k): return self.g("NAND", *a, **k)
    def NOR(self, *a, **k): return self.g("NOR", *a, **k)
    def XOR(self, *a, **k): return self.g("XOR", *a, **k)
    def XNOR(self, *a, **k): return self.g("XNOR", *a, **k)

    def NOT(self, s, gate=False):
        """Complement. For a primary input this uses the A' rail (NOT gate at top)."""
        if s.kind == "in" and not gate:
            rec = s.inp
            if rec[3] is None:
                rec[2] = True
                rec[3] = Sig(self, "inc", inp=rec)
            return rec[3]
        if s.kind == "inc" and not gate:
            return s.inp[1]
        return self._blk("NOT", [s])

    def TRI(self, data, en):
        return self._blk("TRI", [data, en])

    def BUS(self, *tri_outs):
        """Join several tri-state buffer outputs onto one shared bus wire."""
        s = Sig(self, "bus")
        s.members = list(tri_outs)
        return s

    def SUB(self, sub, *ins):
        b = Block("SUB", ins, sub=sub)
        self.blocks.append(b)
        outs = [Sig(self, "blk", b, k) for k in range(sub.n_out_ports)]
        b.outs = outs
        # return in the subcircuit's declared output order
        return [outs[sub.out_order.index(lab)] for lab in sub.out_labels]

    def out(self, label, s):
        self.outputs.append((label, s))

    def outs(self, labels, sigs):
        for l, s in zip(labels, sigs):
            self.out(l, s)

    def seven_seg(self, labels="abcdefg"):
        """Drive a 7-segment display from output pins named a..g (via tunnels)."""
        self.seg7 = labels

    # ---- layout ----------------------------------------------------------------
    def layout(self):
        for b in self.blocks:
            b.ins = [s.r() for s in b.ins]
        self.outputs = [(l, s.r()) for l, s in self.outputs]
        # DFS from outputs: back edges, post-order, levels
        state, order, back = {}, [], set()

        def visit(b):
            stack = [(b, 0)]
            state[b] = 0
            while stack:
                blk, k = stack.pop()
                if k < len(blk.ins):
                    stack.append((blk, k + 1))
                    s = blk.ins[k]
                    for sb in _src_blocks(s):
                        if state.get(sb) == 0:
                            back.add((id(blk), k))
                        elif sb not in state:
                            state[sb] = 0
                            stack.append((sb, 0))
                else:
                    state[blk] = 1
                    order.append(blk)

        for _, s in self.outputs:
            for sb in _src_blocks(s):
                if sb not in state:
                    visit(sb)
        for b in self.blocks:
            if b not in state:
                visit(b)
        level = {}
        for b in order:
            lv = 1
            for k, s in enumerate(b.ins):
                if (id(b), k) not in back:
                    for sb in _src_blocks(s):
                        lv = max(lv, level[sb] + 1)
            level[b] = lv
        ncol = max(level.values()) if level else 0
        self._level, self._back = level, back

        # consumers of every signal
        cons = {}
        for b in self.blocks:
            for k, s in enumerate(b.ins):
                cons.setdefault(id(s), []).append((b, k))
        out_sigs = {}
        for lab, s in self.outputs:
            out_sigs.setdefault(id(s), []).append(lab)

        # ---- vertical placement --------------------------------------------------
        X_PIN, Y_TXT = ((49 + 10 * max([len(r[0]) for r in self.inputs] + [3])) // 10) * 10, 30
        y0 = Y_TXT + 22 * (1 + len(self.lines)) + 30
        ypin = {}
        for i, rec in enumerate(self.inputs):
            ypin[id(rec[1])] = y0 + 40 * i
        y = y0 + 40 * max(1, len(self.inputs)) + 10
        ys, detour = {}, {}
        for b in order:
            top = -b.box[1]
            yb = ((y + top + 9) // 10) * 10
            ys[b] = yb
            y = yb + b.box[1] + b.box[3] + 20
            for k, s in enumerate(b.ins):
                if (id(b), k) in back:
                    detour[(id(b), k)] = y
                    y += 20
        extra_rows = {}  # outputs needing their own row
        seen = set()
        for lab, s in self.outputs:
            if s.kind == "blk" and id(s) not in seen:
                seen.add(id(s))
                continue
            extra_rows[lab] = y
            y += 30
        y_end = y

        # ---- horizontal placement ---------------------------------------------
        rails = {}
        x = X_PIN + 40
        for rec in self.inputs:
            rails[id(rec[1])] = x
            x += 20
            if rec[2]:
                rails[id(rec[3])] = x
                x += 20
        # tracks: per channel L (1..ncol+1)
        chan_tracks = {L: [] for L in range(1, ncol + 2)}
        need_track = set()
        for b in self.blocks:
            for s in b.outs:
                c = cons.get(id(s), [])
                n_extra = len(out_sigs.get(id(s), [])) - 1
                if c or n_extra > 0:
                    need_track.add(id(s))
                    chan_tracks[level[b] + 1].append(("sig", s, ys[b] + b.out_ofs[s.idx][1]))
        buses = {}
        for b in self.blocks:
            for s in b.ins:
                if s.kind == "bus":
                    buses[id(s)] = s
        for _, s in self.outputs:
            if s.kind == "bus":
                buses[id(s)] = s
        for s in buses.values():
            need_track.add(id(s))
            mb = [m.r().block for m in s.members]
            chan_tracks[max(level[b] for b in mb) + 1].append(("sig", s, min(ys[b] for b in mb)))
        for b in self.blocks:
            for k, s in enumerate(b.ins):
                if (id(b), k) in back:
                    chan_tracks[level[b]].append(("fb", (id(b), k), 0))
        xtrack, col_x = {}, {}
        x_cursor = x - 20 + 10 if self.inputs else x
        right_prev = x_cursor
        for L in range(1, ncol + 2):
            tr = chan_tracks[L]
            # signal tracks ordered by y (top signal leftmost), feedback tracks after
            sigs = sorted([t for t in tr if t[0] == "sig"], key=lambda t: t[2])
            fbs = [t for t in tr if t[0] == "fb"]
            xx = right_prev + 20
            for t in sigs + fbs:
                key = id(t[1]) if t[0] == "sig" else t[1]
                xtrack[key] = xx
                xx += 10
            if L <= ncol:
                cx = xx + 20
                col_x[L] = cx
                width = max(-b.box[0] for b in self.blocks if level[b] == L)
                right_prev = cx + width
            else:
                right_prev = xx
        X_OUT = right_prev + 50
        if self.seg7:
            X_OUT += 20
        self._geom = dict(X_PIN=X_PIN, X_OUT=X_OUT, y0=y0, y_end=y_end)

        # ---- emit components & wires ----------------------------------------------
        comps, wires = [], []

        def W(p, q, net):
            if p != q:
                wires.append((p, q, net))

        loc = {}
        for b in self.blocks:
            L = level[b]
            loc[b] = (col_x[L] - b.box[0], ys[b])
            comps.append(("blk", b, loc[b]))

        def sig_point(s):
            b = s.block
            ox, oy = b.out_ofs[s.idx]
            return (loc[b][0] + ox, loc[b][1] + oy)

        # attachments per source: list of y to attach on its vertical
        attach = {}
        for rec in self.inputs:
            lab, s, need, sc, cv = rec
            yi = ypin[id(s)]
            comps.append(("pin_in" if cv is None else "const", lab, (X_PIN, yi)))
            xr = rails[id(s)]
            W((X_PIN, yi), (xr, yi), id(s))
            attach.setdefault(id(s), [yi])
            if need:
                xc = rails[id(sc)]
                W((xr, yi), (xc, yi), id(s))
                comps.append(("not_s", None, (xc, yi + 30)))
                attach.setdefault(id(sc), [yi + 30])

        def src_vertical_x(s):
            return rails[id(s)] if s.kind in ("in", "inc") else xtrack[id(s)]

        for b in self.blocks:
            for k, s in enumerate(b.ins):
                px, py = loc[b][0] + b.in_ofs[k][0], loc[b][1] + b.in_ofs[k][1]
                net = id(s)
                vx = src_vertical_x(s)
                if (id(b), k) in back:
                    yd = detour[(id(b), k)]
                    xl = xtrack[(id(b), k)]
                    attach.setdefault(net, []).append(yd)
                    W((vx, yd), (xl, yd), net)
                    W((xl, yd), (xl, py), net)
                    W((xl, py), (px, py), net)
                else:
                    attach.setdefault(net, []).append(py)
                    W((vx, py), (px, py), net)
        # block outputs -> tracks
        for b in self.blocks:
            for s in b.outs:
                if id(s) in need_track:
                    p = sig_point(s)
                    W(p, (xtrack[id(s)], p[1]), id(s))
                    attach.setdefault(id(s), []).append(p[1])
        for s in buses.values():
            for m in s.members:
                p = sig_point(m.r())
                W(p, (xtrack[id(s)], p[1]), id(s))
                attach.setdefault(id(s), []).append(p[1])
        # outputs
        used_main = set()
        self._out_pins = []
        for lab, s in self.outputs:
            net = id(s)
            if lab in extra_rows:
                yo = extra_rows[lab]
                vx = src_vertical_x(s)
                attach.setdefault(net, []).append(yo)
                W((vx, yo), (X_OUT, yo), net)
            else:
                used_main.add(id(s))
                p = sig_point(s)
                yo = p[1]
                start = (xtrack[id(s)], yo) if id(s) in need_track else p
                W(start, (X_OUT, yo), net)
            comps.append(("pin_out", lab, (X_OUT, yo)))
            self._out_pins.append((lab, yo))
            if self.seg7 and lab in self.seg7:
                W((X_OUT - 20, yo), (X_OUT - 20, yo + 10), net)
                comps.append(("tunnel_n", lab, (X_OUT - 20, yo + 10)))
        # verticals (rails & tracks), split at every attach point
        verticals = {}
        for rec in self.inputs:
            verticals[id(rec[1])] = rails[id(rec[1])]
            if rec[2]:
                verticals[id(rec[3])] = rails[id(rec[3])]
        for b in self.blocks:
            for s in b.outs:
                if id(s) in need_track:
                    verticals[id(s)] = xtrack[id(s)]
        for s in buses.values():
            verticals[id(s)] = xtrack[id(s)]
        for net, vx in verticals.items():
            pts = sorted(set(attach.get(net, [])))
            for a, c in zip(pts, pts[1:]):
                W((vx, a), (vx, c), net)
        # split horizontal wires where junction points of the same net lie inside them
        wires = _split_wires(wires)
        # seven segment display with tunnels
        if self.seg7:
            dx, dy = X_OUT + 140, self._out_pins[0][1] + 40
            comps.append(("seg7", None, (dx, dy)))
            port = {"a": (20, 0), "b": (30, 0), "c": (20, 60), "d": (10, 60), "e": (0, 60),
                    "f": (10, 0), "g": (0, 0)}
            names = dict(zip("abcdefg", self.seg7))
            top = [("b", 80), ("a", 60), ("f", 40), ("g", 20)]
            bot = [("c", 80), ("d", 60), ("e", 40)]
            for seg, up in top:
                px, py = dx + port[seg][0], dy + port[seg][1]
                W((px, py), (px, py - up), "seg" + seg)
                W((px, py - up), (dx - 30, py - up), "seg" + seg)
                comps.append(("tunnel_e", names[seg], (dx - 30, py - up)))
            for seg, dn in bot:
                px, py = dx + port[seg][0], dy + port[seg][1]
                W((px, py), (px, py + dn), "seg" + seg)
                W((px, py + dn), (dx - 30, py + dn), "seg" + seg)
                comps.append(("tunnel_e", names[seg], (dx - 30, py + dn)))
            self._geom["y_end"] = max(y_end, dy + 160)
        self._comps, self._wires = comps, wires
        self._check()
        # subcircuit port order (sorted by y as Logisim does)
        self.out_order = [lab for lab, yo in sorted(self._out_pins, key=lambda t: t[1])]
        self.out_labels = [lab for lab, _ in self.outputs]
        self.n_out_ports = len(self.outputs)
        return self

    def _check(self):
        """Make sure different nets never touch (no endpoint on another net, no overlap)."""
        segs = self._wires
        pts = {}
        for p, q, net in segs:
            for e in (p, q):
                pts.setdefault(e, set()).add(net)
        for e, nets in pts.items():
            if len(nets) > 1:
                raise RuntimeError(f"{self.name}: nets meet at {e}")
        for p, q, net in segs:
            for e, nets in pts.items():
                if net in nets:
                    continue
                if _on_seg(e, p, q, interior=True):
                    raise RuntimeError(f"{self.name}: endpoint {e} lies on another net's wire {p}-{q}")
        # component ports must only touch the intended net: checked by Logisim tests.

    # ---- XML ----------------------------------------------------------------------
    def to_xml(self):
        g = self._geom
        out = [f'  <circuit name="{_x(self.name)}">',
               f'    <a name="circuit" val="{_x(self.name)}"/>',
               '    <a name="clabel" val=""/>', '    <a name="clabelup" val="east"/>',
               '    <a name="clabelfont" val="SansSerif plain 12"/>']
        out.append(_text(20, 30, self.title, "SansSerif bold 16"))
        for i, ln in enumerate(self.lines):
            out.append(_text(20, 30 + 22 * (i + 1), ln, "SansSerif plain 12"))
        for p, q, _ in self._wires:
            out.append(f'    <wire from="({p[0]},{p[1]})" to="({q[0]},{q[1]})"/>')
        for kind, obj, (x, y) in self._comps:
            if kind == "blk":
                b = obj
                if b.kind in GATES:
                    out.append(f'    <comp lib="1" loc="({x},{y})" name="{LOGISIM_NAME[b.kind]}">'
                               f'<a name="size" val="50"/><a name="inputs" val="{len(b.ins)}"/>'
                               + ('<a name="xor" val="odd"/>' if b.kind in ("XOR", "XNOR") and len(b.ins) > 2 else "")
                               + (f'<a name="label" val="{_x(b.label)}"/>' if b.label else "") + '</comp>')
                elif b.kind == "NOT":
                    out.append(f'    <comp lib="1" loc="({x},{y})" name="NOT Gate"/>')
                elif b.kind == "TRI":
                    out.append(f'    <comp lib="1" loc="({x},{y})" name="Controlled Buffer"/>')
                else:
                    out.append(f'    <comp loc="({x},{y})" name="{_x(b.sub.name)}"/>')
            elif kind == "not_s":
                out.append(f'    <comp lib="1" loc="({x},{y})" name="NOT Gate"><a name="facing" val="south"/></comp>')
            elif kind == "pin_in":
                out.append(f'    <comp lib="0" loc="({x},{y})" name="Pin"><a name="tristate" val="false"/>'
                           f'<a name="label" val="{_x(obj)}"/><a name="labelloc" val="west"/></comp>')
            elif kind == "const":
                out.append(f'    <comp lib="0" loc="({x},{y})" name="Constant"><a name="value" val="0x{obj}"/></comp>')
            elif kind == "pin_out":
                out.append(f'    <comp lib="0" loc="({x},{y})" name="Pin"><a name="facing" val="west"/>'
                           f'<a name="output" val="true"/><a name="label" val="{_x(obj)}"/>'
                           f'<a name="labelloc" val="east"/></comp>')
            elif kind == "tunnel_n":
                out.append(f'    <comp lib="0" loc="({x},{y})" name="Tunnel"><a name="facing" val="north"/>'
                           f'<a name="label" val="{_x(obj)}"/></comp>')
            elif kind == "tunnel_e":
                out.append(f'    <comp lib="0" loc="({x},{y})" name="Tunnel"><a name="facing" val="east"/>'
                           f'<a name="label" val="{_x(obj)}"/></comp>')
            elif kind == "seg7":
                out.append(f'    <comp lib="5" loc="({x},{y})" name="7-Segment Display"/>')
        out.append('  </circuit>')
        return "\n".join(out)

    # ---- SVG ----------------------------------------------------------------------
    def to_svg(self, max_w=None):
        return svg_render(self)


def _src_blocks(s):
    if s.kind == "blk":
        return [s.block]
    if s.kind == "bus":
        return [m.r().block for m in s.members]
    return []


def _x(s):
    return html.escape(str(s), quote=True)


def _text(x, y, s, font):
    return (f'    <comp lib="6" loc="({x},{y})" name="Text"><a name="text" val="{_x(s)}"/>'
            f'<a name="font" val="{font}"/><a name="halign" val="left"/><a name="valign" val="base"/></comp>')


def _on_seg(e, p, q, interior=True):
    (x, y), (x1, y1), (x2, y2) = e, p, q
    if x1 == x2 == x:
        lo, hi = sorted((y1, y2))
        return lo < y < hi if interior else lo <= y <= hi
    if y1 == y2 == y:
        lo, hi = sorted((x1, x2))
        return lo < x < hi if interior else lo <= x <= hi
    return False


def _split_wires(wires):
    pts = {}
    for p, q, net in wires:
        pts.setdefault(net, set()).update([p, q])
    res = []
    for p, q, net in wires:
        cut = [e for e in pts[net] if _on_seg(e, p, q)]
        if p[0] == q[0]:
            seq = sorted([p, q] + cut, key=lambda t: t[1])
        else:
            seq = sorted([p, q] + cut, key=lambda t: t[0])
        for a, b in zip(seq, seq[1:]):
            if a != b:
                res.append((a, b, net))
    # dedupe overlapping identical segments
    seen, out = set(), []
    for a, b, n in res:
        k = (min(a, b), max(a, b))
        if k not in seen:
            seen.add(k)
            out.append((a, b, n))
    return out


HEADER = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<project source="2.7.1" version="1.0">
This file is intended to be loaded by Logisim (http://www.cburch.com/logisim/).
  <lib desc="#Wiring" name="0"/>
  <lib desc="#Gates" name="1"/>
  <lib desc="#Plexers" name="2"/>
  <lib desc="#Arithmetic" name="3"/>
  <lib desc="#Memory" name="4"/>
  <lib desc="#I/O" name="5"/>
  <lib desc="#Base" name="6">
    <tool name="Text Tool">
      <a name="text" val=""/>
      <a name="font" val="SansSerif plain 12"/>
      <a name="halign" val="center"/>
      <a name="valign" val="base"/>
    </tool>
  </lib>
  <main name="{main}"/>
  <options>
    <a name="gateUndefined" val="ignore"/>
    <a name="simlimit" val="1000"/>
    <a name="simrand" val="0"/>
  </options>
  <mappings>
    <tool lib="6" map="Button2" name="Menu Tool"/>
    <tool lib="6" map="Ctrl Button1" name="Menu Tool"/>
    <tool lib="6" map="Button3" name="Menu Tool"/>
  </mappings>
  <toolbar>
    <tool lib="6" name="Poke Tool"/>
    <tool lib="6" name="Edit Tool"/>
    <tool lib="6" name="Text Tool">
      <a name="text" val=""/>
      <a name="font" val="SansSerif plain 12"/>
      <a name="halign" val="center"/>
      <a name="valign" val="base"/>
    </tool>
    <sep/>
    <tool lib="0" name="Pin">
      <a name="tristate" val="false"/>
    </tool>
    <tool lib="0" name="Pin">
      <a name="facing" val="west"/>
      <a name="output" val="true"/>
      <a name="labelloc" val="east"/>
    </tool>
    <tool lib="1" name="NOT Gate"/>
    <tool lib="1" name="AND Gate"/>
    <tool lib="1" name="OR Gate"/>
  </toolbar>
"""


def project_xml(circuits, main):
    return HEADER.replace("{main}", _x(main)) + "\n".join(c.to_xml() for c in circuits) + "\n</project>\n"


def subs_needed(c, acc=None):
    """All subcircuits (recursively) used by c, dependencies first."""
    acc = [] if acc is None else acc
    for b in c.blocks:
        if b.kind == "SUB" and b.sub not in acc:
            subs_needed(b.sub, acc)
            acc.append(b.sub)
    return acc


# ============================== SVG rendering ====================================
def svg_render(c):
    g = c._geom
    xs = [p[0] for w in c._wires for p in w[:2]] + [g["X_OUT"] + 90, 8 * len(c.title) + 40]
    W_ = max(xs) + 30
    H_ = g["y_end"] + 10
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W_} {H_}" width="{W_}" height="{H_}" '
         f'font-family="Arial, Helvetica, sans-serif">',
         '<g stroke="#1b5e20" stroke-width="2" stroke-linecap="square">']
    for p, q, _ in c._wires:
        o.append(f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}"/>')
    o.append('</g>')
    cnt = {}
    for p, q, _ in c._wires:
        for e in (p, q):
            cnt[e] = cnt.get(e, 0) + 1
    for e, n in cnt.items():
        if n >= 3:
            o.append(f'<circle cx="{e[0]}" cy="{e[1]}" r="3.5" fill="#1b5e20"/>')
    S = 'fill="#fff" stroke="#111" stroke-width="2"'
    for kind, obj, (x, y) in c._comps:
        if kind == "blk":
            b = obj
            if b.kind in GATES:
                o.append(_svg_gate(b, x, y, S))
            elif b.kind == "NOT":
                o.append(f'<path d="M{x-30},{y-9} L{x-8},{y} L{x-30},{y+9} Z" {S}/>'
                         f'<circle cx="{x-4}" cy="{y}" r="4" {S}/>')
            elif b.kind == "TRI":
                o.append(f'<path d="M{x-20},{y-10} L{x},{y} L{x-20},{y+10} Z" {S}/>'
                         f'<line x1="{x-10}" y1="{y+5}" x2="{x-10}" y2="{y+10}" stroke="#111" stroke-width="2"/>')
            else:
                bx, by, bw, bh = b.box
                o.append(f'<rect x="{x+bx}" y="{y+by}" width="{bw}" height="{bh}" {S}/>')
                o.append(f'<text x="{x+bx+bw/2}" y="{y+by-4}" font-size="11" text-anchor="middle" '
                         f'fill="#0d47a1" font-weight="bold">{_x(b.sub.short)}</text>')
                for k, (ix, iy) in enumerate(b.in_ofs):
                    o.append(f'<text x="{x+ix+3}" y="{y+iy+3}" font-size="7" fill="#555">'
                             f'{_x(b.sub.inputs[k][0])}</text>')
                for k, (ix, iy) in enumerate(b.out_ofs):
                    o.append(f'<text x="{x-3}" y="{y+iy+3}" font-size="7" fill="#555" text-anchor="end">'
                             f'{_x(b.sub.out_order[k])}</text>')
        elif kind == "not_s":
            o.append(f'<path d="M{x-9},{y-30} L{x},{y-8} L{x+9},{y-30} Z" {S}/>'
                     f'<circle cx="{x}" cy="{y-4}" r="4" {S}/>')
        elif kind == "pin_in":
            o.append(f'<rect x="{x-20}" y="{y-10}" width="20" height="20" {S}/>'
                     f'<text x="{x-26}" y="{y+5}" font-size="14" text-anchor="end" font-weight="bold">{_x(obj)}</text>')
        elif kind == "const":
            o.append(f'<text x="{x-4}" y="{y+5}" font-size="15" text-anchor="end" font-weight="bold" fill="#0d47a1">{obj}</text>')
        elif kind == "pin_out":
            o.append(f'<rect x="{x}" y="{y-10}" width="20" height="20" rx="9" {S}/>'
                     f'<text x="{x+26}" y="{y+5}" font-size="14" font-weight="bold">{_x(obj)}</text>')
        elif kind == "tunnel_n":
            o.append(f'<text x="{x}" y="{y+16}" font-size="11" text-anchor="middle" fill="#6a1b9a">[{_x(obj)}]</text>')
        elif kind == "tunnel_e":
            o.append(f'<text x="{x-4}" y="{y+4}" font-size="11" text-anchor="end" fill="#6a1b9a">[{_x(obj)}]</text>')
        elif kind == "seg7":
            o.append(_svg_seg7(x, y))
    o.append(f'<text x="20" y="30" font-size="16" font-weight="bold">{_x(c.title)}</text>')
    for i, ln in enumerate(c.lines):
        o.append(f'<text x="20" y="{30+22*(i+1)}" font-size="12">{_x(ln)}</text>')
    o.append('</svg>')
    return "\n".join(o)


def _svg_gate(b, x, y, S):
    k, n = b.kind, len(b.ins)
    ax = gate_axis(k)
    neg = k in ("NAND", "NOR", "XNOR")
    right = x - 10 if neg else x
    left = right - 50
    h = 25
    parts = []
    ofs = b.in_ofs
    ymin, ymax = min(d for _, d in ofs), max(d for _, d in ofs)
    if k in ("AND", "NAND"):
        parts.append(f'<path d="M{left},{y-h} L{left+25},{y-h} A25,25 0 0 1 {left+25},{y+h} L{left},{y+h} Z" {S}/>')
        back = lambda dy: left
    else:
        parts.append(f'<path d="M{left},{y-h} Q{left+30},{y-h} {right},{y} Q{left+30},{y+h} {left},{y+h} '
                     f'Q{left+15},{y} {left},{y-h} Z" {S}/>')
        back = lambda dy: left + 15 * (1 - (dy / 25.0) ** 2) * 0.5 * 2 if abs(dy) <= 25 else left
        if k in ("XOR", "XNOR"):
            parts.append(f'<path d="M{left-10},{y-h} Q{left+5},{y} {left-10},{y+h}" fill="none" stroke="#111" stroke-width="2"/>')
    if neg:
        parts.append(f'<circle cx="{x-5}" cy="{y}" r="5" {S}/>')
    for ix, dy in ofs:
        bx = back(dy) if abs(dy) <= 25 else left
        x0 = x + ix
        if bx - x0 > 0:
            parts.append(f'<line x1="{x0}" y1="{y+dy}" x2="{bx}" y2="{y+dy}" stroke="#111" stroke-width="2"/>')
    if ymin < -h or ymax > h:
        parts.append(f'<line x1="{left}" y1="{y+min(ymin,-h)}" x2="{left}" y2="{y+max(ymax,h)}" stroke="#111" stroke-width="2"/>')
    if b.label:
        parts.append(f'<text x="{left+20}" y="{y-h-4}" font-size="10" text-anchor="middle" fill="#0d47a1">{_x(b.label)}</text>')
    return "".join(parts)


def _svg_seg7(x, y):
    segs = {"a": (3, 8, 19, 4), "b": (23, 10, 4, 19), "c": (23, 30, 4, 19), "d": (3, 47, 19, 4),
            "e": (-2, 30, 4, 19), "f": (-2, 10, 4, 19), "g": (3, 28, 19, 4)}
    p = [f'<rect x="{x-5}" y="{y}" width="40" height="60" fill="#f5f5f5" stroke="#111" stroke-width="2"/>']
    for s, (a, b2, w, h) in segs.items():
        p.append(f'<rect x="{x+a}" y="{y+b2}" width="{w}" height="{h}" fill="#e53935"/>')
        cx, cy = x + a + w / 2, y + b2 + h / 2
        p.append(f'<text x="{cx}" y="{cy+3}" font-size="7" text-anchor="middle" fill="#fff">{s}</text>')
    return "".join(p)
