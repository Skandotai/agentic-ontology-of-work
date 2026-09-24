"""Render the whitepaper as a paper-style preprint PDF.

    python tools/make_preprint.py [--chromium /path/to/chrome]

Writes docs/downloads/agentic-ontology-of-work-v2.0-preprint.pdf from
whitepaper.md, with a title block, abstract, keywords, continuous sections,
and page numbers. Needs a Chromium that Playwright can drive. For the
intended typefaces, install Source Serif 4, Inter, and JetBrains Mono locally.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model import ROOT, Model  # noqa: E402

OUT = ROOT / "docs/downloads/agentic-ontology-of-work-v2.0-preprint.pdf"
REPO = "https://github.com/Skandotai/agentic-ontology-of-work"
SITE = "https://skandotai.github.io/agentic-ontology-of-work/"
KEYWORDS = ["agentic AI", "ontology", "AI governance", "human oversight", "multi-agent systems",
            "provenance", "OWL", "SHACL", "enterprise architecture"]

CSS = """
@page { size: Letter; margin: 0.9in 1in 0.95in; }
body { font-family: "Source Serif 4", Georgia, serif; font-size: 10.5pt; line-height: 1.45; color: #161714; margin: 0; }
h1, h2, h3, h4, th, .meta, .kw b { font-family: "Inter", Arial, sans-serif; }
.title { text-align: center; margin: 0.2in 0 0.25in; }
.title p { text-align: center; }
.title h1 { font-size: 20pt; line-height: 1.2; margin: 0 0 6pt; font-weight: 700; }
.title .sub { font-size: 12.5pt; margin: 0 0 16pt; font-style: italic; }
.title .author { font-size: 12pt; font-weight: 600; margin: 0; }
.title .aff { font-size: 10.5pt; margin: 2pt 0 10pt; }
.title .meta { font-size: 8.5pt; color: #5e5f58; margin: 1pt 0; }
.abstract { margin: 0.15in 0.35in 0.1in; font-size: 10pt; }
.abstract h2 { font-size: 10.5pt; text-align: center; margin: 0 0 4pt; border: none; }
.kw { margin: 6pt 0.35in 0.2in; font-size: 9.5pt; }
h2 { font-size: 13pt; margin: 18pt 0 6pt; break-after: avoid; }
h3 { font-size: 11pt; margin: 12pt 0 4pt; break-after: avoid; }
p { margin: 0 0 6pt; text-align: justify; hyphens: auto; }
li { margin: 2pt 0; }
hr { display: none; }
table { border-collapse: collapse; width: 100%; font-size: 8.5pt; margin: 6pt 0 10pt; break-inside: auto; }
tr { break-inside: avoid; }
th, td { text-align: left; vertical-align: top; padding: 3pt 5pt; border-bottom: 0.5pt solid #c3c6bb; }
th { font-size: 8pt; border-bottom: 1pt solid #161714; }
code { font-family: "JetBrains Mono", Consolas, monospace; font-size: 8.5pt; }
pre { font-family: "JetBrains Mono", Consolas, monospace; font-size: 6.8pt; line-height: 1.3; background: #f4f5f2; padding: 6pt 8pt; white-space: pre; overflow: hidden; break-inside: avoid; }
pre code { font-size: inherit; }
a { color: #4e287a; text-decoration: none; }
"""


def build_html(m: Model) -> str:
    text = (ROOT / "whitepaper.md").read_text(encoding="utf-8")
    text = re.sub(r"<!-- /?aow:generated[^>]*-->\n?", "", text)
    body = text[text.index("## Abstract"):]
    abstract, rest = body.split("\n---\n", 1)
    abstract_html = markdown.markdown(abstract, extensions=["tables"])
    rest_html = markdown.markdown(rest, extensions=["tables", "fenced_code", "sane_lists"])
    version = m.meta["version"]
    doi = m.meta.get("version_doi")
    cite = f"https://doi.org/{doi}" if doi else REPO
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="title">
  <h1>Agentic Ontology of Work (AOW), Version {version.rsplit('.', 1)[0]}</h1>
  <p class="sub">A semantic model for enterprise work performed by AI agents, people, and systems</p>
  <p class="author">Manish Garg</p>
  <p class="aff">Skan.ai</p>
  <p class="meta">September 2026</p>
  <p class="meta">Ontology, schemas, and examples: {REPO}</p>
  <p class="meta">Licensed CC BY 4.0. Cite as: Garg, M. (2026). Agentic Ontology of Work (AOW), version {version}. Skan.ai. {cite}</p>
</div>
<div class="abstract">{abstract_html}</div>
<p class="kw"><b>Keywords:</b> {", ".join(KEYWORDS)}</p>
{rest_html}
</body></html>"""


def main(chromium: str | None) -> None:
    m = Model()
    html = build_html(m)
    footer = ('<div style="font-size:7.5px;width:100%;padding:0 1in;color:#5e5f58;font-family:Arial;'
              'display:flex;justify-content:space-between"><span>Garg · Agentic Ontology of Work 2.0</span>'
              '<span><span class="pageNumber"></span></span></div>')
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium) if chromium else p.chromium.launch()
        page = browser.new_page()
        page.set_content(html)
        page.wait_for_timeout(400)
        page.pdf(path=str(OUT), format="Letter", print_background=True, display_header_footer=True,
                 header_template="<span></span>", footer_template=footer,
                 margin={"top": "0.9in", "bottom": "0.95in", "left": "1in", "right": "1in"})
        browser.close()
    try:
        import pymupdf

        doc = pymupdf.open(OUT)
        doc.set_metadata({**doc.metadata, "title": "Agentic Ontology of Work (AOW), Version 2.0",
                          "author": "Manish Garg", "subject": "A semantic model for enterprise work performed by AI agents, people, and systems",
                          "keywords": ", ".join(KEYWORDS), "creator": "", "producer": ""})
        doc.saveIncr()
        print(f"wrote {OUT.relative_to(ROOT)} ({doc.page_count} pages)")
    except ImportError:
        print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--chromium")
    main(ap.parse_args().chromium)
