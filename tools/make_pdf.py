"""Builds the lab-file HTML (questions, K-maps, tables, circuit diagrams, 7-segment notes) and prints it to PDF."""
import html, os, subprocess, importlib
import boolmin as bm
from qbase import REG, bitsof

for m in ["q_unit1", "q_unit2", "q_unit3", "q_unit4"]:
    importlib.import_module(m)

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
E = lambda s: html.escape(str(s))
COLORS = ["#e53935", "#1e88e5", "#43a047", "#fb8c00", "#8e24aa", "#00897b", "#d81b60", "#6d4c41", "#3949ab", "#7cb342"]


# ---------------------------------------------------------------- K-map rendering
def kmap_html(k):
    names, n = k["names"], len(k["names"])
    ones, dcs, terms, form = set(k["ones"]), set(k["dcs"]), k["terms"], k["form"]
    target = ones if form == "SOP" else {m for m in range(2 ** n) if m not in ones and m not in dcs}
    cover = {m: [i for i, t in enumerate(terms) if bm.covers(t, m)] for m in range(2 ** n)}

    def cellval(m):
        return "X" if m in dcs else ("1" if m in ones else "0")

    def one_map(sub_names, offset, title=""):
        nn = len(sub_names)
        rv, cv, rc, cc = bm.kmap_layout(nn)
        rn = "".join(sub_names[:rv]); cn = "".join(sub_names[rv:])
        h = ['<table class="km">']
        if title:
            h.append(f'<caption>{E(title)}</caption>')
        h.append(f'<tr><th class="corner">{E(rn)}\\{E(cn)}</th>' +
                 "".join(f'<th>{format(c, "0%db" % (nn - rv))}</th>' for c in cc) + '</tr>')
        for r in rc:
            h.append(f'<tr><th>{format(r, "0%db" % rv)}</th>')
            for col in cc:
                m = offset + (r << (nn - rv)) + col
                v = cellval(m)
                dots = "".join(f'<span class="dot" style="background:{COLORS[i % 10]}"></span>' for i in cover[m]
                               if (m in target or m in dcs))
                cls = "one" if v == ("1" if form == "SOP" else "0") else ("dc" if v == "X" else "")
                h.append(f'<td class="{cls}"><b>{v}</b><sub>{m}</sub><div>{dots}</div></td>')
            h.append('</tr>')
        h.append('</table>')
        return "".join(h)

    if n <= 4:
        maps = one_map(names, 0)
    else:
        maps = one_map(names[1:], 0, f"{names[0]} = 0") + one_map(names[1:], 16, f"{names[0]} = 1")
    if form == "SOP":
        gl = "".join(f'<li><span class="dot" style="background:{COLORS[i % 10]}"></span> '
                     f'm({",".join(str(m) for m in bm.minterms_of(t, n) if m not in dcs) or "-"})'
                     f' &rarr; <b>{E(bm.term_str(t, names))}</b></li>' for i, t in enumerate(terms))
        res = bm.sop_str(terms, names)
    else:
        gl = "".join(f'<li><span class="dot" style="background:{COLORS[i % 10]}"></span> '
                     f'M({",".join(str(m) for m in bm.minterms_of(t, n) if m not in dcs) or "-"})'
                     f' &rarr; <b>{E(bm.sumterm_str(t, names))}</b></li>' for i, t in enumerate(terms))
        res = bm.pos_str(terms, names)
    return (f'<div class="kbox"><div class="ktitle">K-map for {E(k["label"])} '
            f'({"grouping 1s" if form == "SOP" else "grouping 0s"})</div><div class="kmaps">{maps}</div>'
            f'<ul class="groups">{gl}</ul><div class="kres">{E(k["label"])} = {E(res)}</div></div>')


# ---------------------------------------------------------------- tables
def table_html(headers, rows, n_in=None, cls="tt"):
    h = [f'<table class="{cls}"><tr>']
    for i, x in enumerate(headers):
        sep = ' class="sep"' if n_in is not None and i == n_in else ""
        h.append(f'<th{sep}>{E(x)}</th>')
    h.append('</tr>')
    for r in rows:
        h.append('<tr>' + "".join(f'<td{" class=\"sep\"" if n_in is not None and i == n_in else ""}>{E(v)}</td>'
                                  for i, v in enumerate(r)) + '</tr>')
    h.append('</table>')
    return "".join(h)


def truth_table(part, sequential):
    c, rows = part["c"], part["rows"]
    ins, outs = c.pins_in, [l for l, _ in c.outputs]
    show = rows
    note = part["note"]
    if not sequential and len(rows) > 32:
        step = max(1, len(rows) // 16)
        show = rows[::step][:16]
        note = (note + " " if note else "") + f"Showing {len(show)} sample rows; all {len(rows)} combinations " \
                                             f"were verified in Logisim."
    body = [list(i) + list(o) for i, o in show]
    hdr = (["Step"] if sequential else []) + ins + outs
    if sequential:
        body = [[k + 1] + r for k, r in enumerate(body)]
    t = table_html(hdr, body, len(ins) + (1 if sequential else 0))
    return t + (f'<div class="note">{E(note)}</div>' if note else "")


def qm_html(n, ones, names):
    """Quine-McCluskey tabulation: columns of combined terms with ticks, then PI chart."""
    def s(t):
        return "".join("-" if t[1] >> (n - 1 - i) & 1 else str(t[0] >> (n - 1 - i) & 1) for i in range(n))
    cols, cur = [], {(m, 0): [m] for m in ones}
    while cur:
        nxt, used = {}, set()
        lst = sorted(cur, key=lambda t: (bin(t[0] & ~t[1]).count("1"), t[0]))
        for i, a in enumerate(lst):
            for b in lst[i + 1:]:
                if a[1] == b[1]:
                    d = a[0] ^ b[0]
                    if d and d & (d - 1) == 0:
                        key = (a[0] & ~d, a[1] | d)
                        nxt.setdefault(key, sorted(set(cur[a] + cur[b])))
                        used.add(a); used.add(b)
        cols.append([(t, cur[t], t in used) for t in lst])
        cur = nxt
    h = ['<div class="qm">']
    for ci, col in enumerate(cols):
        h.append(f'<table class="tt"><tr><th colspan="3">Step {ci+1}</th></tr><tr><th>Group</th><th>Minterms</th><th>{E("".join(names))}</th></tr>')
        last = None
        for t, ms, used in col:
            g = bin(t[0] & ~t[1]).count("1")
            gl = str(g) if g != last else ""
            last = g
            h.append(f'<tr><td>{gl}</td><td>{",".join(map(str, ms))}</td><td>{s(t)} {"&#10003;" if used else "<b>PI</b>"}</td></tr>')
        h.append('</table>')
    h.append('</div>')
    pis = bm.prime_implicants(n, ones)
    ess = bm.essential_pis(n, ones, pis)
    ch = ['<table class="tt"><tr><th>Prime implicant</th>' + "".join(f'<th>{m}</th>' for m in ones) + '</tr>']
    for p in pis:
        ch.append(f'<tr><td>{E(bm.term_str(p, names))}{" (EPI)" if p in ess else ""}</td>' +
                  "".join(f'<td>{"X" if bm.covers(p, m) else ""}</td>' for m in ones) + '</tr>')
    ch.append('</table>')
    return "".join(h) + '<div class="sub">Prime implicant chart</div>' + "".join(ch)


# ---------------------------------------------------------------- 7 segment notes
def seg_digit_svg(segs, label):
    shape = {"a": (8, 4, 24, 5), "b": (32, 8, 5, 24), "c": (32, 36, 5, 24), "d": (8, 60, 24, 5),
             "e": (3, 36, 5, 24), "f": (3, 8, 5, 24), "g": (8, 32, 24, 5)}
    p = [f'<svg viewBox="0 0 40 78" width="40" height="78"><rect x="0" y="0" width="40" height="68" rx="3" fill="#222"/>']
    for s_, (x, y, w, h) in shape.items():
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="1.5" fill="{"#ff3d00" if s_ in segs else "#3a3a3a"}"/>')
    p.append(f'<text x="20" y="77" font-size="9" text-anchor="middle">{E(label)}</text></svg>')
    return "".join(p)


def seven_seg_notes():
    from q_unit3 import DIG10
    segsvg = ('<svg viewBox="0 0 120 150" width="150" height="190">'
              '<rect x="0" y="0" width="120" height="150" rx="8" fill="#f4f4f4" stroke="#999"/>'
              + "".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#e53935"/>'
                        f'<text x="{tx}" y="{ty}" font-size="13" font-weight="bold">{s}</text>'
                        for s, x, y, w, h, tx, ty in [("a", 30, 12, 60, 10, 55, 9), ("b", 92, 24, 10, 46, 106, 50),
                                                       ("c", 92, 80, 10, 46, 106, 106), ("d", 30, 128, 60, 10, 55, 148),
                                                       ("e", 18, 80, 10, 46, 4, 106), ("f", 18, 24, 10, 46, 4, 50),
                                                       ("g", 30, 70, 60, 10, 55, 67)]) + '</svg>')
    digits = "".join(seg_digit_svg(DIG10[d], str(d)) for d in range(10))
    rows = [[d] + bitsof(d, 4) + [int(s in DIG10[d]) for s in "abcdefg"] for d in range(10)]
    rows += [[d] + bitsof(d, 4) + ["X"] * 7 for d in range(10, 16)]
    tbl = table_html(["Digit", "A", "B", "C", "D", "a", "b", "c", "d", "e", "f", "g"], rows, 5)
    return f"""
<section class="q notes" id="seg7notes"><span class="mk">@@SEG7@@</span>
<h2>Notes: The 7-Segment Display</h2>
<div class="flex"><div>{segsvg}</div><div>
<p>A <b>7-segment display</b> shows a decimal digit using seven LED bars named <b>a</b> (top), <b>b</b> (upper right),
<b>c</b> (lower right), <b>d</b> (bottom), <b>e</b> (lower left), <b>f</b> (upper left) and <b>g</b> (middle); many
displays also have a decimal point <b>dp</b>.</p>
<ul>
<li><b>Common cathode (CC):</b> all LED cathodes are tied to ground, so a segment glows when its input is <b>1</b>
(driven by an active-high decoder such as IC 7448). The Logisim <i>7-Segment Display</i> behaves this way.</li>
<li><b>Common anode (CA):</b> all anodes are tied to +V, so a segment glows when its input is <b>0</b> (active-low
decoder such as IC 7447). The CA truth table is simply the complement of the CC table.</li>
<li>A <b>BCD to 7-segment decoder</b> is a combinational circuit with 4 inputs (A B C D, A = MSB) and 7 outputs.
Inputs 1010-1111 never occur in BCD, so they are <b>don't-cares</b> (X) in every K-map.</li>
<li>Each segment output is designed separately: write the truth table, put the 1s (and Xs) on a 4-variable K-map,
group, and read the minimal SOP. Product terms common to several segments are shared (multiple-output design).</li>
<li>The 3-bit version (Q54) uses x y z (digits 0-7) and 3-variable K-maps; in the class notes these outputs are
called F1...F7.</li>
</ul></div></div>
<div class="sub">Digits 0-9 as shown by the circuit (6 and 9 are drawn with their tails)</div>
<div class="digits">{digits}</div>
<div class="sub">Truth table (common cathode, 1 = segment ON)</div>{tbl}
<p class="note">The K-maps and minimal expressions for every segment, and the working circuits, are given in
Q54 (3-bit, digits 0-7) and Q55 (BCD, digits 0-9). In Logisim the outputs a-g are also connected through tunnels
([a]...[g]) to a real 7-Segment Display component, so poking the inputs shows the digit.</p>
</section>"""


# ---------------------------------------------------------------- question page
def question_html(q):
    seq = q.unit.startswith("Unit 4")
    star = '<span class="star" title="Taught in class notes">&#9733;</span>' if q.star and "N" in q.src else ""
    src = {"N": "Class notes", "F": "Folder circuit", "L": "Lab file / photo"}
    tags = " ".join(f'<span class="tag">{src[s]}</span>' for s in q.src.split(","))
    h = [f'<section class="q" id="q{q.num}"><span class="mk">@@Q{q.num}@@</span><div class="qhead"><span class="qno">Q{E(q.num)}</span> '
         f'{E(q.title)} {star}</div><div class="unit">{E(q.unit)} &nbsp; {tags}</div>']
    h.append(f'<p><b>Aim:</b> {E(q.aim)}</p><p><b>Theory:</b> {E(q.theory)}</p>')
    if q.exprs:
        h.append('<div class="sub">Boolean expressions</div><ul class="expr">' +
                 "".join(f'<li>{E(x)}</li>' for x in q.exprs) + '</ul>')
    for attr in ("char", "excite"):
        if hasattr(q, attr):
            title, hdr, rows = getattr(q, attr)
            h.append(f'<div class="sub">{E(title)}</div>' + table_html(hdr, rows))
    if hasattr(q, "state_table"):
        hdr, rows = q.state_table
        h.append('<div class="sub">State table with SR excitation</div>' + table_html(hdr, rows))
    if getattr(q, "html", "") == "QM":
        h.append('<div class="sub">Quine-McCluskey tabulation</div>' + qm_html(q.qm[0], q.qm[1], ["A", "B", "C", "D"]))
    if q.kmaps:
        h.append('<div class="sub">K-map simplification</div><div class="kgrid">' +
                 "".join(kmap_html(k) for k in q.kmaps) + '</div>')
    for p in q.parts:
        c = p["c"]
        if len(q.parts) > 1:
            h.append(f'<div class="sub part">{E(c.title)}</div>')
        svg = c.to_svg().replace("<svg ", '<svg class="circ" ', 1)
        h.append(f'<div class="blk"><div class="sub">Circuit diagram (Logisim circuit "{E(c.name)}")</div>'
                 f'<div class="cbox">{svg}</div></div>')
        small = len(p["rows"]) <= 40 or not seq
        h.append(f'<div class="{"blk" if small else ""}"><div class="sub">' +
                 ("Test sequence (verified in Logisim)" if seq else "Truth table") + '</div>' + truth_table(p, seq) + '</div>')
    n_rows = sum(len(p["rows"]) for p in q.parts)
    h.append(f'<p class="result"><b>Result:</b> The circuit was built in Logisim 2.7.1 and simulated with '
             f'{n_rows} test {"steps" if seq else "input combinations"}; every output matched the expected '
             f'{"sequence" if seq else "truth table"}.</p></section>')
    if q.num == "55":
        h.append(seven_seg_notes())
    return "".join(h)


CSS = """
@page { size: A4; margin: 14mm 13mm 14mm 13mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.5pt; color: #1a1a1a; line-height: 1.35; }
.cover { text-align: center; padding-top: 30mm; break-after: page; }
.cover h1 { font-size: 30pt; margin: 6mm 0 2mm; color: #0d47a1; letter-spacing: 1px; }
.cover h2 { font-size: 16pt; margin: 0; font-weight: 500; }
.cover .uni { font-size: 13pt; margin-top: 4mm; }
.cover .meta { margin: 18mm auto 0; text-align: left; width: 120mm; font-size: 12.5pt; line-height: 2; }
.cover .stat { margin-top: 16mm; display: flex; justify-content: center; gap: 8mm; }
.cover .stat div { border: 2px solid #0d47a1; border-radius: 8px; padding: 4mm 6mm; }
.cover .stat b { display: block; font-size: 20pt; color: #0d47a1; }
h2 { color: #0d47a1; border-bottom: 2px solid #0d47a1; padding-bottom: 2px; }
.q { break-before: page; }
.qhead { font-size: 15pt; font-weight: 700; color: #0d47a1; }
.qno { background: #0d47a1; color: #fff; border-radius: 4px; padding: 0 6px; margin-right: 4px; }
.star { color: #f9a825; font-size: 16pt; }
.unit { color: #555; font-size: 9pt; margin: 1mm 0 3mm; }
.tag { background: #e3f2fd; color: #0d47a1; border-radius: 3px; padding: 0 4px; font-size: 8pt; margin-left: 2px; }
.sub { font-weight: 700; margin: 3mm 0 1.5mm; color: #263238; break-after: avoid; }
.blk { break-inside: avoid; }
.sub.part { font-size: 12pt; color: #0d47a1; border-top: 1px dashed #90caf9; padding-top: 2mm; }
ul.expr { margin: 0; padding-left: 6mm; font-family: Consolas, 'Courier New', monospace; font-size: 10pt; }
table.tt { border-collapse: collapse; font-size: 8.5pt; margin: 1mm 0; break-inside: avoid; }
table.tt th, table.tt td { border: 1px solid #9e9e9e; padding: 1px 6px; text-align: center; }
table.tt th { background: #e8eaf6; }
table.tt .sep { border-left: 3px double #333; }
.note { font-size: 8.5pt; color: #555; font-style: italic; }
.result { background: #e8f5e9; border-left: 4px solid #43a047; padding: 2mm 3mm; margin-top: 3mm; break-inside: avoid; }
.cbox { border: 1px solid #ddd; padding: 2mm; break-inside: avoid; text-align: center; }
svg.circ { max-width: 100%; height: auto; max-height: 225mm; }
.kgrid { display: flex; flex-wrap: wrap; gap: 3mm; }
.kbox { border: 1px solid #ccc; border-radius: 4px; padding: 2mm; break-inside: avoid; }
.ktitle { font-weight: 700; font-size: 9pt; margin-bottom: 1mm; }
.kmaps { display: flex; gap: 3mm; }
table.km { border-collapse: collapse; font-size: 8.5pt; }
table.km caption { font-size: 8pt; font-weight: 700; }
table.km th { background: #eceff1; padding: 1px 4px; border: 1px solid #90a4ae; font-weight: 600; }
table.km td { border: 1px solid #90a4ae; width: 26px; height: 26px; text-align: center; vertical-align: top; padding: 1px; }
table.km td.one { background: #fff8e1; }
table.km td.dc { background: #f3e5f5; }
table.km td sub { color: #999; font-size: 6pt; margin-left: 1px; }
table.km td div { line-height: 6px; }
.dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin: 0 1px; }
ul.groups { margin: 1mm 0; padding-left: 4mm; font-size: 8pt; list-style: none; }
.kres { font-family: Consolas, monospace; font-size: 9pt; font-weight: 700; color: #0d47a1; }
.qm { display: flex; flex-wrap: wrap; gap: 3mm; align-items: flex-start; }
table.tt.index { break-inside: auto; width: 100%; }
.index tr { break-inside: avoid; }
.index td, .index th { font-size: 8.6pt; padding: 1px 5px; }
.index td:nth-child(2) { text-align: left; }
.flex { display: flex; gap: 6mm; align-items: flex-start; }
.digits { display: flex; gap: 2mm; }
.howto li { margin-bottom: 1.5mm; }
.mk { font-size: 1px; color: #fff; line-height: 0; }
"""


def build_html(pages=None):
    pg = lambda k: str(pages.get(k, "--")) if pages else "--"
    total_c = sum(len(q.parts) for q in REG)
    total_rows = sum(len(p["rows"]) for q in REG for p in q.parts)
    h = [f'<!doctype html><html><head><meta charset="utf-8"><title>Digital Electronics Lab File</title>'
         f'<style>{CSS}</style></head><body>']
    h.append(f"""<div class="cover">
<div class="uni">University Institute of Engineering and Technology, CSJMU, Kanpur</div>
<div class="uni">Computer Science &amp; Engineering</div>
<h1>DIGITAL ELECTRONICS LAB FILE</h1><h2>CSE-S202 &nbsp;|&nbsp; Logisim Experiments</h2>
<div class="meta">NAME: ______________________________<br>ROLL NO: CSJMA24001390085<br>
BRANCH: B.Tech CSE - 2nd Year<br>SUBMITTED TO: Dr. Ram Nayan Mishra<br>SUBMITTED BY: ______________________</div>
<div class="stat"><div><b>{len(REG)}</b>questions</div><div><b>{total_c}</b>Logisim circuits</div>
<div><b>{total_rows}</b>test cases passed</div></div></div>""")
    # index
    h.append('<section><h2>Index</h2><table class="tt index"><thead><tr><th>Q</th><th>Experiment</th><th>Unit</th>'
             '<th>Taught</th><th>Circuits</th><th>Page No.</th><th>Remark</th><th>Sign</th></tr></thead>')
    h.append(f'<tr><td>-</td><td><b>How to use the Logisim files</b></td><td></td><td></td><td></td>'
             f'<td>{pg("HOWTO")}</td><td></td><td></td></tr>')
    for q in REG:
        st = "&#9733;" if q.star and "N" in q.src else ""
        h.append(f'<tr><td>{q.num}</td><td>{E(q.title)}</td><td>{q.unit[5]}</td><td style="color:#f9a825">{st}</td>'
                 f'<td>{len(q.parts)}</td><td>{pg("Q" + q.num)}</td><td></td><td></td></tr>')
        if q.num == "55":
            h.append(f'<tr><td>-</td><td><b>Notes: The 7-Segment Display</b></td><td>3</td><td style="color:#f9a825">&#9733;</td>'
                     f'<td></td><td>{pg("SEG7")}</td><td></td><td></td></tr>')
    h.append('</table><p class="note">&#9733; = topic taught in class (found in the class notes) - give these priority. '
             'Tags on each page show the source: class notes, circuit already in the lab folder, or the lab file / photo.</p></section>')
    h.append("""<section class="q"><span class="mk">@@HOWTO@@</span><h2>How to use the Logisim files</h2><ol class="howto">
<li>Open <b>DE_Lab_All_Circuits.circ</b> in Logisim 2.7.1 (File &rarr; Open). Every question is a separate circuit in the
explorer panel on the left (Q01 ... Q78). Double-click a circuit to open it. The same circuits are also saved one
per file in the <b>Individual_Circuits</b> folder.</li>
<li>Select the <b>Poke tool</b> (hand icon) and click an input pin to change it between 0 and 1. Output pins show the
result immediately.</li>
<li>Circuits whose names start with <b>Helper -</b> (full adder, decoder, multiplexer, flip-flops ...) are the
sub-circuit blocks used inside bigger circuits. Double-click a block in a circuit to look inside it.</li>
<li><b>Sequential circuits (Q68-Q78):</b> a latch built from gates starts in an unknown state. Flip-flops and
counters have a <b>CLR</b> input: set CLR = 1 and back to 0 first, then toggle <b>CLK</b>. Master-slave JK/T/SR
flip-flops change when CLK goes 1 &rarr; 0; the D flip-flop and shift register change when CLK goes 0 &rarr; 1.
To run a counter automatically you may replace the CLK pin with a Logisim <i>Clock</i> component and press Ctrl+K.</li>
<li>All circuits use ordinary gates, wires, pins and tunnels, so they can be edited freely - move, delete or add
gates exactly as in your own lab work.</li>
<li>Every circuit was checked automatically by loading the .circ file into Logisim's own simulation engine and
comparing every output with the expected truth table or sequence.</li></ol></section>""")
    for q in REG:
        h.append(question_html(q))
    h.append('</body></html>')
    return "\n".join(h)


def print_pdf(html_text, pdf):
    path = os.path.join(OUT, "tools", "lab_file.html")
    open(path, "w", encoding="utf-8").write(html_text)
    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if os.path.exists(pdf):
        os.remove(pdf)
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--print-to-pdf=" + pdf, "file:///" + path.replace("\\", "/")],
                   capture_output=True, text=True, timeout=300)


def find_pages(pdf):
    import re, fitz
    pages = {}
    for i, p in enumerate(fitz.open(pdf)):
        for k in re.findall(r"@@(\w+)@@", p.get_text()):
            pages.setdefault(k, i + 1)
    return pages


def stamp(src, dst):
    """Footer with page numbers on every page except the cover."""
    import fitz
    doc = fitz.open(src)
    n = len(doc)
    for i, p in enumerate(doc):
        if i == 0:
            continue
        w, h = p.rect.width, p.rect.height
        p.draw_line((36, h - 30), (w - 36, h - 30), color=(0.05, 0.28, 0.63), width=0.6)
        p.insert_text((36, h - 18), "Digital Electronics Lab File  |  CSE-S202", fontsize=8, color=(0.35, 0.35, 0.35))
        txt = f"Page {i + 1} of {n}"
        p.insert_text((w - 36 - fitz.get_text_length(txt, fontsize=9), h - 18), txt, fontsize=9, color=(0, 0, 0))
    doc.save(dst, garbage=3, deflate=True)


if __name__ == "__main__":
    final = os.path.join(OUT, "DE_Lab_File_78_Questions.pdf")
    tmp = os.path.join(OUT, "tools", "_pass.pdf")
    print_pdf(build_html(), tmp)
    pages = find_pages(tmp)
    for _ in range(3):  # repeat until the page numbers in the index are stable
        print_pdf(build_html(pages), tmp)
        new = find_pages(tmp)
        if new == pages:
            break
        pages = new
    staged = final[:-4] + "_new.pdf"
    stamp(tmp, staged)
    os.remove(tmp)
    try:
        os.replace(staged, final)
    except PermissionError:
        print("NOTE: old PDF is open in another program; new file saved as", staged)
        final = staged
    print("pages:", len(__import__("fitz").open(final)), " markers:", len(pages), " stable:", new == pages)
    print({k: pages[k] for k in ("HOWTO", "Q01", "Q27", "Q55", "SEG7", "Q78")})
