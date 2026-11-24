"""Build the static website into _site/ from data/*.yml and templates/.

Usage: python3 scripts/build_site.py
"""
import os, re, shutil, html, datetime
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA, OUT = os.path.join(ROOT, "data"), os.path.join(ROOT, "_site")
BASE = os.environ.get("BASE_PATH", "").rstrip("/")   # e.g. "/website" on a github.io project URL


def load(n):
    with open(os.path.join(DATA, n + ".yml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def local(href):
    """Site-relative files: serve from this repo if present, else from the old WordPress host."""
    if href.startswith("/wp-content/"):
        return (BASE + href) if os.path.exists(os.path.join(ROOT, href.lstrip("/"))) else "https://rene.kizilcec.com" + href
    return href


def md(s):
    """Inline markdown: [text](url), **bold**, *italic*, bare URLs."""
    if s is None:
        return Markup("")
    s = html.escape(str(s), quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: '<a href="%s">%s</a>' % (local(m.group(2)), m.group(1)), s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*]+)\*(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r'(?<!href=")(https?://[^\s<]+[^\s<.,;)])', r'<a href="\1">link</a>', s)
    return Markup(s)


def authors(s):
    """Highlight the site owner's name in author lists."""
    s = html.escape(s or "", quote=False)
    s = re.sub(r"(Kizilcec, R\.\s?F\.|Kizilcec, R\.|Kizilec, R\.)", r'<span class="me">\1</span>', s)
    return Markup(s)


env = Environment(loader=FileSystemLoader(os.path.join(ROOT, "templates")),
                  autoescape=select_autoescape(["html"]))
env.filters["md"] = md
env.filters["authors"] = authors
env.filters["local"] = local
env.filters["striptags_md"] = lambda s: re.sub(r"\*+", "", s or "")


def cite_html(p):
    """The CV citation, with the title linked to the PDF (preferred) or publisher page, as on the old site."""
    cite, title = p["cite"], (p.get("title") or "").strip('"“”')
    href = p.get("pdf") or p.get("url")
    i = cite.find(title) if title and href else -1
    if i < 0:
        return md(cite)
    href = local(href)
    return Markup(md(cite[:i]) + Markup('<a href="%s">' % html.escape(href)) + md(title) + Markup("</a>") + md(cite[i + len(title):]))

site = load("site")
profile = load("profile")
pubs = load("publications")
TYPE_LABEL = {
    "science": "General science journals", "journal": "Journal articles",
    "conference": "Conference papers", "chapter": "Book chapters",
    "special_issue": "Edited special issues", "commentary": "Commentaries",
}
for p in pubs:
    p["type_label"] = TYPE_LABEL.get(p["type"], p["type"])
    y = p.get("year")
    p["sort_year"] = y if isinstance(y, int) else 9999
    p["year_label"] = str(y) if isinstance(y, int) else "Forthcoming"
    p["cite_html"] = cite_html(p)
pubs_sorted = sorted(pubs, key=lambda p: -p["sort_year"])  # stable: keeps CV order within year
by_year = []
for p in pubs_sorted:
    if not by_year or by_year[-1][0] != p["year_label"]:
        by_year.append((p["year_label"], []))
    by_year[-1][1].append(p)

def by_year_desc(items):
    def k(x):
        m = re.search(r"(19|20)\d{2}", str(x.get("year") or ""))
        return -int(m.group(0)) if m else 0
    return sorted(items, key=k)


talks = load("talks")
talks = {k: by_year_desc(v) for k, v in talks.items()}
ctx = dict(
    site=site, profile=profile, pubs=pubs_sorted, by_year=by_year,
    type_labels=[(k, v) for k, v in TYPE_LABEL.items() if any(p["type"] == k for p in pubs)],
    awards=load("awards"), grants=load("grants"), talks=talks,
    teaching=load("teaching"), advising=load("advising"), service=load("service"),
    media=load("media"), year=datetime.date.today().year,
    updated=datetime.date.today().strftime("%B %-d, %Y"),
    selected=[p for p in pubs_sorted if p["type"] == "science"][:5],
)

PAGES = {
    "index.html": ("home.html", "About"),
    "publications/index.html": ("publications.html", "Publications"),
    "teaching/index.html": ("teaching.html", "Teaching"),
    "resources/index.html": ("resources.html", "Resources"),
}
NAV = [("/", "About"), ("/publications/", "Publications"), ("/teaching/", "Teaching"),
       ("/resources/", "Resources"), ("/cv/Kizilcec_CV.pdf", "CV")]

if os.path.exists(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
for out, (tpl, title) in PAGES.items():
    path = os.path.join(OUT, out)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    here = "/" + out.replace("index.html", "")
    with open(path, "w", encoding="utf-8") as f:
        f.write(env.get_template(tpl).render(**ctx, title=title, nav=NAV, here=here, base=BASE,
                                             hero=(tpl == "home.html")))

# old WordPress URLs -> new pages (WordPress used the same slugs for most)
for old in ("cv",):
    os.makedirs(os.path.join(OUT, old), exist_ok=True)
    with open(os.path.join(OUT, old, "index.html"), "w") as f:
        f.write('<!doctype html><meta http-equiv="refresh" content="0; url=' + BASE + '/cv/Kizilcec_CV.pdf">'
                '<a href="' + BASE + '/cv/Kizilcec_CV.pdf">CV</a>')

for d in ("assets", "wp-content"):
    if os.path.exists(os.path.join(ROOT, d)):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(OUT, d))
cvdir = os.path.join(ROOT, "cv")
for fn in ("Kizilcec_CV.pdf", "Kizilcec_CV.docx"):
    if os.path.exists(os.path.join(cvdir, fn)):
        shutil.copy(os.path.join(cvdir, fn), os.path.join(OUT, "cv", fn))
if os.path.exists(os.path.join(ROOT, "CNAME")):
    shutil.copy(os.path.join(ROOT, "CNAME"), OUT)
open(os.path.join(OUT, ".nojekyll"), "w").close()
print("built", len(PAGES), "pages into", OUT)
