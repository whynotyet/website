# rene.kizilcec.com + CV

One set of data files produces both the website and the CV.

```
data/            <- the only place to edit content
  profile.yml       name, contact, employment, education
  publications.yml  every paper (newest first within each type)
  grants.yml  awards.yml  talks.yml  teaching.yml  advising.yml  service.yml  media.yml
  site.yml          website-only text: bio, roles, news, press, course descriptions, resources
scripts/
  build_cv.py       -> cv/Kizilcec_CV.docx and cv/Kizilcec_CV.pdf
  build_site.py     -> _site/ (static HTML)
templates/  assets/   website look
wp-content/         PDFs carried over from the old WordPress site (same URLs)
```

Every push to `main` rebuilds the CV and the site and publishes them (GitHub Actions → Pages).
The website has four pages (About, Publications, Teaching, Resources), styled after the old
WordPress (Twenty Nineteen) site. The CV has the full record (talks, grants, service, advising).
The CV is always at https://rene.kizilcec.com/cv/Kizilcec_CV.pdf (Word version: `.docx` at the same path).

## Adding things

**A paper** — add to the top of `data/publications.yml`:

```yaml
- type: conference        # science | journal | conference | chapter | special_issue | commentary
  year: 2027              # or "forthcoming"
  authors: Lee, J., Vanacore, K., & Kizilcec, R. F.
  title: Title in sentence case
  venue: In *Proceedings of ... (L@S '27)*.
  note: Best Paper Award  # optional
  url: https://doi.org/...  # optional publisher/DOI/arXiv link
  pdf: /wp-content/uploads/... or /papers/lee2027x.pdf   # optional self-hosted PDF
  cite: 'Lee, J., Vanacore, K., & Kizilcec, R. F. (2027). Title in sentence case. In *Proceedings of ... (L@S ''27)*.'
```

`cite` is exactly how the entry appears in the CV (APA, `*italics*` allowed). The other
fields drive the website. Keep both consistent.

**A talk / award / service role** — add `{year: "2027", text: "**Venue or role**, details"}` to the
right list. **A grant** — `{year: "2027", text: 'Funder, "Title" (N years, $X; PI ..., Co-PIs ...)', amount: "$X"}`.
**A news item** for the home page — add to `news:` at the top of `data/site.yml`.

## Build locally

```
pip install pyyaml jinja2 markupsafe python-docx   # plus LibreOffice for the PDF
python scripts/build_cv.py && python scripts/build_site.py
python -m http.server -d _site
```

## Rules for the weekly update task

- Never push to `main`; open one pull request per week titled `Weekly update: <date>`, with
  each proposed change and its source (email subject/date, DOI, Slack link) in the description.
- Only add things with a verifiable source. Accepted ≠ published: use `forthcoming` until there's a DOI.
- Don't reorder or rewrite existing entries unless fixing a clear error, and say so in the PR.
- Never add student names to advising lists, or private information, without Rene confirming.
