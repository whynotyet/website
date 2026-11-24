"""Build the CV (.docx, and .pdf via LibreOffice) from the YAML files in _data/.

Usage:  python3 scripts/build_cv.py            # writes cv/Kizilcec_CV.docx and .pdf
        python3 scripts/build_cv.py --no-pdf
"""
import datetime, os, re, subprocess, sys, copy
import yaml
from docx import Document
from docx.enum.text import WD_TAB_ALIGNMENT, WD_BREAK
from docx.shared import Pt, Inches, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "cv")
FONT = "Times New Roman"
YEAR_COL = Inches(1.0)
HANG = Inches(0.35)


def load(name):
    with open(os.path.join(DATA, name + ".yml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, side, Inches(1))
st = doc.styles["Normal"]
st.font.name, st.font.size = FONT, Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
st.paragraph_format.space_after = Pt(6)
st.paragraph_format.space_before = Pt(0)
st.paragraph_format.line_spacing = 1.0

TOKEN = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|https?://\S+)")


def add_md(p, text, size=None, bold=None):
    """Add simple markdown (**bold**, *italic*, bare URLs) as runs."""
    for part in TOKEN.split(text or ""):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = p.add_run(part[2:-2]); r.bold = True
        elif part.startswith("*") and part.endswith("*") and len(part) > 1:
            r = p.add_run(part[1:-1]); r.italic = True
        elif part.startswith("http"):
            add_link(p, part.rstrip(".,;)"), part.rstrip(".,;)"))
            tail = part[len(part.rstrip(".,;)")):]
            r = p.add_run(tail) if tail else None
        else:
            r = p.add_run(part)
        if r is not None:
            if size: r.font.size = Pt(size)
            if bold: r.bold = True
    return p


def add_link(p, url, text):
    part = p.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), r_id)
    r = OxmlElement("w:r"); rPr = OxmlElement("w:rPr")
    c = OxmlElement("w:color"); c.set(qn("w:val"), "1F4E79"); rPr.append(c)
    r.append(rPr); t = OxmlElement("w:t"); t.text = text; t.set(qn("xml:space"), "preserve"); r.append(t)
    h.append(r); p._p.append(h)


def heading(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text.upper()); r.bold = True; r.font.size = Pt(12)
    # bottom border
    pPr = p._p.get_or_add_pPr(); bdr = OxmlElement("w:pBdr"); b = OxmlElement("w:bottom")
    for k, v in (("val", "single"), ("sz", "4"), ("space", "1"), ("color", "808080")):
        b.set(qn("w:" + k), v)
    bdr.append(b); pPr.append(bdr)


def subheading(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text); r.bold = True; r.italic = True


def year_item(year, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent, pf.first_line_indent = YEAR_COL, -YEAR_COL
    pf.tab_stops.add_tab_stop(YEAR_COL)
    pf.space_after = Pt(4)
    p.add_run((year or "") + "\t")
    add_md(p, text)
    return p


def hang_item(text, note=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent, pf.first_line_indent = HANG, -HANG
    add_md(p, text)
    if note:
        r = p.add_run("  " + note); r.bold = True
    return p


# ---------------------------------------------------------------- content
prof = load("profile")
p = doc.add_paragraph(); p.alignment = 2
r = p.add_run("Last updated: " + datetime.date.today().strftime("%b %-d, %Y")); r.font.size = Pt(9); r.italic = True
p = doc.add_paragraph(); p.alignment = 1
r = p.add_run(prof["name"].upper()); r.bold = True; r.font.size = Pt(16)
p = doc.add_paragraph(); p.alignment = 1
add_md(p, " · ".join(prof["address"]) + "\n", size=10)
add_md(p, prof["email"] + " · " + " · ".join(prof["websites"]) + " · ORCID " + prof["orcid"], size=10)

heading("Employment")
for e in prof["employment"]:
    q0 = year_item(e["years"], e["position"])
    if e.get("details"): q0.paragraph_format.space_after = Pt(2)
    for d in e.get("details", []):
        q = year_item("", d); q.paragraph_format.space_after = Pt(2)

heading("Education")
for e in prof["education"]:
    hang_item(e["text"])

heading("Selected Awards")
for a in load("awards"):
    year_item(a.get("year"), a["text"])

heading("Selected Grants")
for g in load("grants"):
    hang_item(g["text"] + (", " + str(g["year"]) if g.get("year") else ""))

heading("Publications")
LABELS = [
    ("science", "General Science Journals (Science, Nature, PNAS, etc.)"),
    ("journal", "Disciplinary Journals"),
    ("conference", "Peer-Reviewed and Published Conference Papers"),
    ("chapter", "Book Chapters"),
    ("special_issue", "Edited Special Issues"),
    ("commentary", "Peer-Reviewed Commentaries and Policy Briefs"),
]
pubs = load("publications")
for key, label in LABELS:
    items = [x for x in pubs if x["type"] == key]
    if not items:
        continue
    subheading(label)
    for x in items:  # order as stored in the file (newest first by convention)
        hang_item(x["cite"], x.get("note"))

talks = load("talks")
heading("Invited Talks/Panels")
for t in talks["invited"]:
    year_item(t.get("year"), t["text"])
heading("Selected Conference Presentations (Non-Archival)")
for t in talks["conference"]:
    year_item(t.get("year"), t["text"])

teach = load("teaching")
heading("Teaching")
for c in teach["courses"]:
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(0); p.paragraph_format.keep_with_next = True
    r = p.add_run(c["title"]); r.bold = True
    if c.get("code"): p.add_run(f" ({c['code']})")
    if c.get("institution"): p.add_run(", " + c["institution"])
    if c.get("offered"):
        q = doc.add_paragraph(); q.paragraph_format.left_indent = HANG
        r = q.add_run("Offered in " + c["offered"]); r.font.size = Pt(10)
subheading("Invited and ad-hoc teaching")
for g in teach["guest"]:
    year_item(g.get("year"), g["text"])

heading("Advising")
for grp in load("advising"):
    subheading(grp["group"])
    for person in grp["people"]:
        q = doc.add_paragraph(style="List Bullet"); q.paragraph_format.space_after = Pt(0)
        add_md(q, person)

heading("Professional Service")
for grp in load("service"):
    subheading(grp["group"])
    for it in grp["items"]:
        year_item(it.get("year"), it["text"])

heading("Selected Media Coverage")
for m in load("media"):
    p = hang_item(m["text"])
    if m.get("url"):
        p.add_run(" "); add_link(p, m["url"], "[link]")

# page numbers in footer
fp = sec.footer.paragraphs[0]; fp.alignment = 1
for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    r = fp.add_run()
    if tag:
        f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), tag); r._r.append(f)
    else:
        it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; r._r.append(it)
    r.font.size = Pt(9)

os.makedirs(OUT, exist_ok=True)
docx_path = os.path.join(OUT, "Kizilcec_CV.docx")
doc.save(docx_path)
print("wrote", docx_path)
if "--no-pdf" not in sys.argv:
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", OUT, docx_path],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", os.path.join(OUT, "Kizilcec_CV.pdf"))
