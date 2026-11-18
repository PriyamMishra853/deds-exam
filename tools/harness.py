"""Shared helpers: build project file, generate test vectors, run Logisim tests."""
import itertools, subprocess, os
import lgen

TOOLS = os.path.dirname(os.path.abspath(__file__))


def comb_rows(circ, spec):
    """All input combinations (first input = MSB). spec(*bits) -> tuple/list of outputs."""
    n = len(circ.pins_in)
    rows = []
    for bits in itertools.product((0, 1), repeat=n):
        o = spec(*bits)
        if isinstance(o, int):
            o = (o,)
        rows.append((bits, tuple(o)))
    return rows


def vectors_text(items):
    """items: list of (circuit, rows) where rows=[(inbits, outbits)], 'x' = don't care."""
    out = []
    for c, rows in items:
        out.append("CIRCUIT " + c.name)
        out.append("IN " + " ".join(c.pins_in))
        out.append("OUT " + " ".join(lab for lab, _ in c.outputs))
        for ib, ob in rows:
            out.append("ROW " + " ".join(map(str, ib)) + " | " + " ".join(map(str, ob)))
        out.append("END")
    return "\n".join(out) + "\n"


def write_project(path, circuits, main):
    allc = []
    for c in circuits:
        for s in lgen.subs_needed(c):
            if s not in allc:
                allc.append(s)
    for c in circuits:
        if c not in allc:
            allc.append(c)
    # questions first (in order), helper sub-circuits at the end of the list
    ordered = [c for c in circuits] + [c for c in allc if c not in circuits]
    with open(path, "w", encoding="utf-8") as f:
        f.write(lgen.project_xml(ordered, main))


def run_logisim_tests(circ_path, vec_path):
    cp = "logisim.jar;." if os.name == "nt" else "logisim.jar:."
    r = subprocess.run(["java", "-Djava.awt.headless=true", "-cp", cp, "LogiTest", circ_path, vec_path],
                       cwd=TOOLS, capture_output=True, text=True)
    return r.stdout + r.stderr


def run_dangling(circ_path):
    cp = "logisim.jar;." if os.name == "nt" else "logisim.jar:."
    r = subprocess.run(["java", "-Djava.awt.headless=true", "-cp", cp, "PortDump", circ_path, "dangling"],
                       cwd=TOOLS, capture_output=True, text=True)
    return r.stdout + r.stderr
