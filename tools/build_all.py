"""Build every question circuit, write the Logisim files and run all tests in Logisim's engine.
usage: python build_all.py [unit modules...]   (default: all units)"""
import sys, os, re, importlib
import harness, lgen
from qbase import REG

mods = sys.argv[1:] or ["q_unit1", "q_unit2", "q_unit3", "q_unit4"]
for m in mods:
    importlib.import_module(m)

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
circs = [p["c"] for q in REG for p in q["parts"]] if False else [p["c"] for q in REG for p in q.parts]
items = [(p["c"], p["rows"]) for q in REG for p in q.parts]

# helper subcircuits get a clear name prefix so they sort after the questions
master = os.path.join(OUT, "DE_Lab_All_Circuits.circ")
harness.write_project(master, circs, circs[0].name)
open(os.path.join(OUT, "tools", "all_vectors.txt"), "w").write(harness.vectors_text(items))

# one file per question as well
ind = os.path.join(OUT, "Individual_Circuits")
os.makedirs(ind, exist_ok=True)
for q in REG:
    cs = [p["c"] for p in q.parts]
    fn = re.sub(r"[^A-Za-z0-9_]+", "_", f"Q{q.num}_{q.title}").strip("_")[:70] + ".circ"
    harness.write_project(os.path.join(ind, fn), cs, cs[0].name)

res = harness.run_logisim_tests(master, os.path.join(OUT, "tools", "all_vectors.txt"))
bad = [l for l in res.splitlines() if not l.startswith("PASS")]
print("\n".join(bad))
d = harness.run_dangling(master)
print("\n".join(l for l in d.splitlines() if "7-Segment" not in l))
print("questions:", len(REG), "circuits:", len(circs))
