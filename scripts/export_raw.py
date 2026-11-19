"""Raw export: every sheet of both source workbooks -> data/raw/*.csv (UTF-8),
cached values exactly as Excel last computed them, original headers/cells as-is
(no header detection, no cleaning: sheet grid starting at A1).
Also: *__formulas.csv sidecars for sheets containing formulas, and
methodology.docx -> methodology.md. Never writes into ./source."""
import csv, re, pathlib, openpyxl, docx
from openpyxl.worksheet.formula import ArrayFormula

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "source", ROOT / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)
BOOKS = {"accidents": "_github-AAC_accidents_tagged_data.xlsx",
         "definitions": "_github-Category-Definitions+Notes.xlsx"}

def slug(s): return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").lower()

def ftext(v):
    if isinstance(v, ArrayFormula): return "{" + (v.text or "") + "}"
    return v

for key, fn in BOOKS.items():
    vals = openpyxl.load_workbook(SRC / fn, data_only=True)
    forms = openpyxl.load_workbook(SRC / fn, data_only=False)
    for i, ws in enumerate(vals.worksheets):
        fws = forms[ws.title]
        nrow, ncol = ws.max_row, ws.max_column
        name = f"{key}__{i:02d}_{slug(ws.title)}"
        with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            for row in ws.iter_rows(min_row=1, max_row=nrow, max_col=ncol, values_only=True):
                w.writerow(["" if v is None else v for v in row])
        has_f = any(isinstance(c.value, ArrayFormula) or (isinstance(c.value, str) and c.value.startswith("="))
                    for r in fws.iter_rows() for c in r)
        if has_f:
            with open(OUT / f"{name}__formulas.csv", "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                for row in fws.iter_rows(min_row=1, max_row=nrow, max_col=ncol, values_only=True):
                    w.writerow(["" if v is None else ftext(v) for v in row])
        print(f"{name}.csv  {nrow}x{ncol}{'  (+formulas)' if has_f else ''}")

# methodology docx -> markdown (headings, lists, tables)
d = docx.Document(SRC / "_github-uncut-methodology.docx")
lines = []
body = d.element.body
from docx.table import Table
from docx.text.paragraph import Paragraph
for el in body.iterchildren():
    tag = el.tag.split("}")[1]
    if tag == "p":
        p = Paragraph(el, d); t = p.text.strip(); st = (p.style.name or "").lower()
        if not t: lines.append(""); continue
        m = re.match(r"heading (\d)", st)
        if m: lines.append("#" * int(m.group(1)) + " " + t)
        elif st == "title": lines.append("# " + t)
        elif "list" in st: lines.append("- " + t)
        else: lines.append(t)
    elif tag == "tbl":
        tb = Table(el, d); rows = [[c.text.strip().replace("\n", " ").replace("|", "\\|") for c in r.cells] for r in tb.rows]
        if rows:
            lines.append(""); lines.append("| " + " | ".join(rows[0]) + " |")
            lines.append("|" + "---|" * len(rows[0]))
            for r in rows[1:]: lines.append("| " + " | ".join(r) + " |")
            lines.append("")
md = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"
(OUT / "methodology.md").write_text(md, encoding="utf-8")
print("methodology.md", len(md), "chars,", len(d.tables), "tables,", len(d.inline_shapes), "inline images (not extracted)")
