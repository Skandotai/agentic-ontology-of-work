"""Render the PDFs and images the site links to. Needs a Chromium that
Playwright can drive, so it runs locally rather than in CI.

    pip install playwright && python -m playwright install chromium
    python tools/make_assets.py [--chromium /path/to/chrome]

Writes:
    docs/downloads/agentic-ontology-of-work-v2.0.pdf            the whitepaper
    docs/downloads/agentic-ontology-of-work-reference-card.pdf  the one-page card
    docs/assets/social-preview.png                              link preview, 1280x640
    docs/favicon.png, docs/favicon.ico, docs/apple-touch-icon.png

For the PDFs to use the site's typefaces, install Inter, Inter Tight, and
JetBrains Mono locally first; otherwise the browser's fallback fonts are used.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model import ROOT, Model  # noqa: E402

DOCS = ROOT / "docs"

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{s}" height="{s}">
  <rect width="64" height="64" rx="14" fill="#161714"/>
  <path d="M18 20 L46 20 M18 20 L32 44 M46 20 L32 44" stroke="#c3c6bb" stroke-width="3.2" stroke-linecap="round"/>
  <circle cx="18" cy="20" r="7" fill="#97c8ff"/>
  <circle cx="46" cy="20" r="7" fill="#9677ff"/>
  <circle cx="32" cy="44" r="7" fill="#ff5a5a"/>
</svg>"""

PREVIEW_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body {{ margin:0; width:1280px; height:640px; background:#161714; color:#f7fbf5; font-family:"Inter", Arial, sans-serif; overflow:hidden; }}
.wrap {{ padding:70px 80px; position:relative; height:100%; box-sizing:border-box; }}
.eyebrow {{ font-family:"Inter Tight", Arial, sans-serif; letter-spacing:.14em; text-transform:uppercase; font-size:20px; color:#9677ff; font-weight:600; margin:0 0 18px; }}
h1 {{ font-family:"Inter Tight", Arial, sans-serif; font-size:84px; line-height:1.02; margin:0 0 22px; font-weight:600; letter-spacing:-.02em; }}
p.sub {{ font-size:27px; line-height:1.4; color:#d8dad1; margin:0; max-width:900px; }}
.layers {{ position:absolute; left:80px; right:80px; bottom:96px; display:flex; gap:14px; }}
.layer {{ flex:1; border-radius:10px; padding:14px 18px; font-family:"Inter Tight", Arial, sans-serif; }}
.layer b {{ display:block; font-size:22px; margin-bottom:4px; }}
.layer span {{ font-size:16px; opacity:.85; }}
.foot {{ position:absolute; left:80px; right:80px; bottom:40px; font-size:19px; color:#a9aba2; display:flex; justify-content:space-between; }}
.foot b {{ color:#9677ff; font-weight:600; }}
</style></head><body><div class="wrap">
<p class="eyebrow">An open ontology for agentic work</p>
<h1>Agentic Ontology of Work</h1>
<p class="sub">From Objective to Intent, Plan, Task, Action, Result, and Outcome, governed by Policy, Confidence, and five levels of autonomy.</p>
<div class="layers">
  <div class="layer" style="background:#97c8ff;color:#161714"><b>Perception</b><span>Work Item · Signal · Observation</span></div>
  <div class="layer" style="background:#9677ff;color:#161714"><b>Cognition</b><span>Objective · Intent · Context · Policy · Plan</span></div>
  <div class="layer" style="background:#4e287a;color:#fff"><b>Execution</b><span>Task · Actor · Skill · Action · Result</span></div>
  <div class="layer" style="background:#ff5a5a;color:#161714"><b>Assurance</b><span>Assurance Level · Guardian · Outcome · Memory</span></div>
</div>
<div class="foot"><span>Version {version} · By Manish Garg, Skan<b>.ai</b></span><span>w3id.org/aow · OWL · JSON-LD · SHACL</span></div>
</div></body></html>"""

PRINT_CSS = """
@page { size: Letter; margin: 0.8in 0.85in 0.9in; }
header.site, footer.site, .toc, .skip { display: none !important; }
body { font-size: 10.5pt; background: #fff; }
.prose { max-width: none; padding-top: 0 !important; }
.prose > p.eyebrow, .prose > p.eyebrow + p.small { display: none; }
.prose h1 { font-size: 30pt; margin: 1.6in 0 10pt; }
.prose h1 + p { font-size: 15pt; }
.prose h2 { font-size: 17pt; break-before: page; border-top: none; margin-top: 0; padding-top: 0; }
.prose h3 { font-size: 12.5pt; }
table { font-size: 9pt; }
pre { font-size: 8pt; white-space: pre; }
.table-scroll { overflow: visible; }
"""


def render(chromium: str | None) -> None:
    m = Model()
    version = m.meta["version"]
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium) if chromium else p.chromium.launch()

        page = browser.new_page()
        page.goto((DOCS / "whitepaper/index.html").as_uri())
        page.add_style_tag(content=PRINT_CSS)
        page.wait_for_timeout(500)
        page.pdf(path=str(DOCS / "downloads/agentic-ontology-of-work-v2.0.pdf"), format="Letter",
                 print_background=True, display_header_footer=True,
                 header_template="<span></span>",
                 footer_template=('<div style="font-size:8px;width:100%;padding:0 0.85in;color:#5e5f58;'
                                  'font-family:Arial;display:flex;justify-content:space-between">'
                                  f'<span>Agentic Ontology of Work {version} · Manish Garg, Skan.ai · CC-BY 4.0</span>'
                                  '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'),
                 margin={"top": "0.8in", "bottom": "0.9in", "left": "0.85in", "right": "0.85in"})

        page = browser.new_page()
        page.goto((DOCS / "print/card/index.html").as_uri())
        page.add_style_tag(content="header.site, footer.site { display:none !important; } body { background:#fff; }")
        page.wait_for_timeout(300)
        page.pdf(path=str(DOCS / "downloads/agentic-ontology-of-work-reference-card.pdf"), format="Letter",
                 landscape=True, print_background=True, scale=0.78,
                 margin={"top": "0.35in", "bottom": "0.35in", "left": "0.4in", "right": "0.4in"})

        page = browser.new_page(viewport={"width": 1280, "height": 640})
        page.set_content(PREVIEW_HTML.format(version=version.rsplit(".", 1)[0]))
        page.wait_for_timeout(300)
        page.screenshot(path=str(DOCS / "assets/social-preview.png"))

        pngs = {}
        for size in (16, 32, 48, 180):
            page = browser.new_page(viewport={"width": size, "height": size})
            page.set_content(f'<html><body style="margin:0;background:transparent">{ICON_SVG.format(s=size)}</body></html>')
            pngs[size] = page.screenshot(omit_background=True)
        browser.close()

    (DOCS / "favicon.png").write_bytes(pngs[32])
    (DOCS / "apple-touch-icon.png").write_bytes(pngs[180])
    from PIL import Image

    Image.open(io.BytesIO(pngs[48])).save(DOCS / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("rendered PDFs, social preview, and icons")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--chromium", help="path to a Chromium executable")
    render(ap.parse_args().chromium)
