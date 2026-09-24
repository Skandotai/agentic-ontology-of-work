"""Generate the GitHub Pages site in docs/ from aow.yaml, the whitepaper,
and the examples.

    python tools/site.py

Pages:
    docs/index.html                 overview, interactive graph, downloads
    docs/entities/index.html        every class, by layer
    docs/entities/<slug>/index.html one page per class
    docs/ontology/index.html        term reference; target of https://w3id.org/aow#<term>
    docs/whitepaper/index.html      the whitepaper, rendered
    docs/about/index.html           why, who, what changed, how to contribute
    docs/print/card/index.html      the one-page reference card (printed to PDF)
    docs/404.html
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import markdown

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model import ROOT, Model, camel, expand  # noqa: E402

DOCS = ROOT / "docs"
SITE = "https://skandotai.github.io/agentic-ontology-of-work/"
REPO = "https://github.com/Skandotai/agentic-ontology-of-work"
SOA_SITE = "https://skandotai.github.io/soa-to-agentic-terms/"
SOA_REPO = "https://github.com/Skandotai/soa-to-agentic-terms"
FONTS = ("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&"
         "family=Inter+Tight:wght@500;600;700&family=JetBrains+Mono:wght@400&display=swap")
PDF_V2 = "downloads/agentic-ontology-of-work-v2.0.pdf"
PDF_CARD = "downloads/agentic-ontology-of-work-reference-card.pdf"
PDF_V1 = "downloads/agentic-ontology-of-work-v1.0.pdf"

e = html.escape


# ------------------------------------------------------------------ layout
def page(*, title: str, description: str, body: str, path: str, current: str = "",
         head_extra: str = "", og_type: str = "website") -> str:
    depth = path.count("/")
    up = "../" * depth
    canonical = SITE + (path[: -len("index.html")] if path.endswith("index.html") else path)
    nav = [("entities/index.html", "Ontology", "entities"), ("whitepaper/index.html", "Whitepaper", "whitepaper"),
           ("ontology/index.html", "Reference", "reference"), ("about/index.html", "About", "about")]
    cur = ' aria-current="page"'
    nav_html = "".join(
        f'<a href="{up}{href}"{cur if key == current else ""}>{label}</a>'
        for href, label, key in nav)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="{up}favicon.ico" sizes="any">
<link rel="icon" href="{up}favicon.png" type="image/png">
<link rel="apple-touch-icon" href="{up}apple-touch-icon.png">
<meta name="theme-color" content="#161714">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}assets/social-preview.png">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="640">
<meta property="og:image:alt" content="The Agentic Ontology of Work: four layers, Perception, Cognition, Execution, and Assurance, connecting Objectives to Actions to Outcomes.">
<meta property="og:site_name" content="Agentic Ontology of Work">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{up}assets/style.css">
{head_extra}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site">
  <div class="wrap">
    <a class="brand" href="{up}index.html">Agentic Ontology of Work <span>· Skan<b>.ai</b></span></a>
    <nav aria-label="Site">{nav_html}<a href="{REPO}">GitHub</a></nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site">
  <div class="wrap">
    <p>Agentic Ontology of Work, version 2.0 · By Manish Garg, <a href="https://www.skan.ai">Skan.ai</a></p>
    <p>Prose licensed <a href="https://creativecommons.org/licenses/by/4.0/">CC-BY 4.0</a>. Ontology, schemas, and code licensed <a href="https://www.apache.org/licenses/LICENSE-2.0">Apache 2.0</a>.</p>
    <p>Identifiers: <code>https://w3id.org/aow</code> · Source: <a href="{REPO}">{REPO.replace("https://", "")}</a></p>
    <p class="family">Also from Skan.ai: <a href="{SOA_SITE}">SOA-to-Agentic AI Terminology Mapping</a></p>
  </div>
</footer>
</body>
</html>
"""


def write(rel: str, text: str) -> None:
    p = DOCS / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def layer_name(m: Model, lid: str) -> str:
    return next(l["name"] for l in m.layers if l["id"] == lid)


def table(headers: list, rows: list, row_class=None) -> str:
    th = "".join(f"<th scope=\"col\">{h}</th>" for h in headers)
    trs = []
    for i, r in enumerate(rows):
        cls = f' class="{row_class(i)}"' if row_class and row_class(i) else ""
        trs.append(f"<tr{cls}>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    return f'<div class="table-scroll"><table><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>'


def jsonld_script(data: dict) -> str:
    return f'<script type="application/ld+json">\n{json.dumps(data, indent=2, ensure_ascii=False)}\n</script>\n'


# ------------------------------------------------------------------ graph
COL_X = {"perception": 120, "cognition": 380, "execution": 640, "assurance": 900}
NODE_Y = {
    "WorkItem": 166, "Observation": 262, "Signal": 358,
    "Objective": 70, "Intent": 166, "Context": 262, "Policy": 358, "Plan": 454,
    "Task": 70, "Orchestrator": 134, "Actor": 198, "Agent": 262, "HumanActor": 326, "Role": 390,
    "Skill": 454, "Action": 518, "Result": 582,
    "Guardian": 70, "AssuranceLevel": 142, "Confidence": 214, "Outcome": 286, "Feedback": 358,
    "Memory": 430, "OperationalMemory": 502, "KnowledgeBase": 574,
}
NODE_W, NODE_H = 176, 34
SPINE = {
    ("Intent", "serves_objective", "Objective"), ("Intent", "shaped_by", "Context"),
    ("Intent", "constrained_by", "Policy"), ("Plan", "realizes", "Intent"), ("Plan", "has_task", "Task"),
    ("Task", "assigned_to", "Actor"), ("Action", "fulfills", "Task"), ("Action", "performed_by", "Actor"),
    ("Action", "invokes", "Skill"), ("Result", "generated_by", "Action"),
    ("Result", "has_confidence", "Confidence"), ("Confidence", "compared_against", "AssuranceLevel"),
    ("Result", "contributes_to", "Outcome"), ("Outcome", "evaluates", "Objective"),
    ("Feedback", "feedback_on", "Outcome"), ("Feedback", "updates", "Memory"),
    ("Context", "draws_on", "Memory"), ("Context", "draws_on", "Observation"),
    ("Observation", "derived_from", "Signal"), ("Observation", "about", "WorkItem"),
    ("Guardian", "enforces", "Policy"), ("Guardian", "oversees", "Actor"),
}


def graph_svg(m: Model, up: str) -> str:
    pos = {}
    for ent in m.entities:
        pos[ent.id] = (COL_X[ent.layer], NODE_Y[ent.id])
    W, H = 1060, 640
    edges = []
    for r in m.relationships:
        for d in r.domain:
            for c in r.range:
                edges.append((d, r.key, c, r.label))
    for ent in m.entities:
        if ent.subclass_of:
            edges.append((ent.id, "subclass", ent.subclass_of, "is a kind of"))

    def path(a, b):
        (x1, y1), (x2, y2) = pos[a], pos[b]
        hw = NODE_W / 2
        if a == b:
            sx, sy = x1 + hw, y1 - 6
            return f"M{sx},{sy} C{sx + 46},{sy - 30} {sx + 46},{sy + 42} {sx},{sy + 12}", (sx + 40, sy + 4)
        if x1 == x2:
            sx = x1 + hw
            bulge = 40 + abs(y2 - y1) * 0.18
            p = f"M{sx},{y1} C{sx + bulge},{y1} {sx + bulge},{y2} {sx + 4},{y2}"
            return p, (sx + bulge * 0.75, (y1 + y2) / 2)
        if x2 > x1:
            sx, ex = x1 + hw, x2 - hw - 4
        else:
            sx, ex = x1 - hw, x2 + hw + 4
        dx = (ex - sx) / 2
        p = f"M{sx},{y1} C{sx + dx},{y1} {ex - dx},{y2} {ex},{y2}"
        return p, ((sx + ex) / 2, (y1 + y2) / 2)

    parts = [f'<svg id="aow-graph" viewBox="0 0 {W} {H}" role="group" aria-labelledby="g-title g-desc" '
             f'xmlns="http://www.w3.org/2000/svg">',
             '<title id="g-title">The Agentic Ontology of Work as a graph</title>',
             '<desc id="g-desc">Twenty-five classes in four columns, one per layer. Hover over or focus a class '
             'to see its relationships; select it to open its page.</desc>',
             '<defs>'
             '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
             '<path d="M0,0 L10,5 L0,10 z" fill="var(--rule-strong)"/></marker>'
             '<marker id="arrow-hl" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
             '<path d="M0,0 L10,5 L0,10 z" fill="#9677ff"/></marker></defs>']
    for layer in m.layers:
        x = COL_X[layer["id"]]
        parts.append(f'<rect class="g-band" x="{x - 118}" y="18" width="236" height="{H - 30}" rx="10"/>')
        parts.append(f'<text class="g-col-title" x="{x}" y="42" text-anchor="middle">{e(layer["name"])}</text>')
    for i, (a, key, b, label) in enumerate(edges):
        d, (lx, ly) = path(a, b)
        cls = "g-edge"
        if (a, key, b) in SPINE:
            cls += " spine"
        if key == "subclass":
            cls += " sub"
        parts.append(f'<path class="{cls}" d="{d}" data-a="{a}" data-b="{b}" id="edge-{i}" marker-end="url(#arrow)"/>')
    for ent in m.entities:
        x, y = pos[ent.id]
        cls = "g-node" + (" abstract" if ent.abstract else "")
        color = f"var(--layer-{ent.layer})"
        aria = f"{ent.label}: {ent.definition}"
        outs = [f"{r.label} {' / '.join(m.by_id[c].label for c in r.range)}" for r in m.outgoing(ent.id, inherited=False)]
        ins = sorted({f"{m.by_id[d].label} ({r.label})" for r in m.incoming(ent.id) for d in r.domain
                      if ent.id in r.range})
        info = f"<b>{e(ent.label)}</b> {e(ent.definition)}"
        if ent.subclass_of:
            info += f" A kind of {e(m.by_id[ent.subclass_of].label)}."
        if outs:
            info += " <b>Points to:</b> " + e("; ".join(outs)) + "."
        if ins:
            info += " <b>Pointed to by:</b> " + e("; ".join(ins)) + "."
        parts.append(
            f'<a class="{cls}" href="{up}entities/{ent.slug}/index.html" data-id="{ent.id}" data-info="{e(info)}" aria-label="{e(aria)}">'
            f'<rect x="{x - NODE_W / 2}" y="{y - NODE_H / 2}" width="{NODE_W}" height="{NODE_H}"/>'
            f'<circle class="dot" cx="{x - NODE_W / 2 + 15}" cy="{y}" r="5" fill="{color}"/>'
            f'<text x="{x - NODE_W / 2 + 28}" y="{y + 5}">{e(ent.label)}</text></a>')
    parts.append("</svg>")
    return "\n".join(parts)


GRAPH_JS = """<script>
(function () {
  var svg = document.getElementById('aow-graph');
  if (!svg) return;
  var edges = Array.prototype.slice.call(svg.querySelectorAll('.g-edge'));
  var info = document.getElementById('g-info');
  var idle = info ? info.innerHTML : '';
  function on(id) {
    svg.classList.add('focusing');
    var near = {}; near[id] = true;
    edges.forEach(function (p) {
      var hit = p.getAttribute('data-a') === id || p.getAttribute('data-b') === id;
      p.classList.toggle('hl', hit);
      p.setAttribute('marker-end', hit ? 'url(#arrow-hl)' : 'url(#arrow)');
      if (hit) { near[p.getAttribute('data-a')] = true; near[p.getAttribute('data-b')] = true; }
    });
    svg.querySelectorAll('.g-node').forEach(function (n) {
      n.classList.toggle('hl', !!near[n.getAttribute('data-id')]);
      if (info && n.getAttribute('data-id') === id) info.innerHTML = n.getAttribute('data-info');
    });
  }
  function off() {
    svg.classList.remove('focusing');
    svg.querySelectorAll('.hl').forEach(function (n) { n.classList.remove('hl'); });
    edges.forEach(function (p) { p.setAttribute('marker-end', 'url(#arrow)'); });
    if (info) info.innerHTML = idle;
  }
  svg.querySelectorAll('.g-node').forEach(function (n) {
    var id = n.getAttribute('data-id');
    n.addEventListener('mouseenter', function () { on(id); });
    n.addEventListener('focus', function () { on(id); });
    n.addEventListener('mouseleave', off);
    n.addEventListener('blur', off);
  });
})();
</script>
"""


# ------------------------------------------------------------------ helpers
def load_examples():
    """All example nodes, grouped by type, first occurrence per type."""
    by_type: dict = {}
    for path in [ROOT / "examples/claims-processing.jsonld", *sorted((ROOT / "examples/industry").glob("*.jsonld"))]:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for node in doc["@graph"]:
            by_type.setdefault(node["type"], (node, path.relative_to(ROOT).as_posix()))
    return by_type


def explain_rows():
    """Run the explain-result query over the worked example."""
    import validate  # noqa: WPS433 - tools/validate.py

    ctx = json.loads((ROOT / "ontology/context.jsonld").read_text(encoding="utf-8"))
    doc = json.loads((ROOT / "examples/claims-processing.jsonld").read_text(encoding="utf-8"))
    data = validate.to_rdf(doc, ctx)
    ontology = validate.load_ontology()
    nodes = {n["id"]: n for n in doc["@graph"]}

    def name(iri):
        if iri is None:
            return "—"
        n = nodes.get(str(iri).rsplit("/", 1)[-1], {})
        return n.get("label") or n.get("name") or n.get("description") or str(iri).rsplit("/", 1)[-1]

    rows = []
    for r in validate.run_query("explain-result", data, ontology):
        rows.append([e(str(r.summary)), e(name(r.actor)), e(name(r.skill)), e(name(r.task)),
                     e(name(r.intent)), e(name(r.objective))])
    return rows


def attr_type_html(m: Model, a) -> str:
    if a.is_ref:
        return "→ " + " / ".join(
            f'<a href="../{m.by_id[c].slug}/index.html">{e(m.by_id[c].label)}</a>' if c in m.by_id else "any"
            for c in a.range)
    if a.type == "enum":
        return "one of " + ", ".join(f"<code>{e(v)}</code>" for v in a.values)
    if a.type == "class":
        return "class name"
    rng = f" ({a.min:g}–{a.max:g})" if a.min is not None and a.max is not None else ""
    return e(a.type) + rng


# ------------------------------------------------------------------ pages
def home(m: Model) -> str:
    counts = f"{len(m.entities)} classes and {len(m.relationships)} relationships"
    layers = []
    for layer in m.layers:
        items = "".join(
            f'<li><a href="entities/{x.slug}/index.html">{e(x.label)}</a></li>' for x in m.entities_in(layer["id"]))
        layers.append(f'<div class="layer {layer["id"]}"><p class="eyebrow">Layer {layer["order"]}</p>'
                      f'<h3>{e(layer["name"])}</h3><p class="q">{e(layer["question"])}</p><ul>{items}</ul></div>')
    steps = []
    for al in m.assurance_levels:
        floor = ("Default confidence floor " + f"{al['default_confidence_floor']:.2f}"
                 if al["default_confidence_floor"] is not None else "Every state change approved by a person"
                 if al["level"] == 1 else "People do the work")
        steps.append(f'<div class="step" style="--n:{al["level"]}"><p class="lvl">{al["id"]}</p>'
                     f'<p class="nm">{e(al["label"])}</p><p><b>People:</b> {e(al["human_role"])}</p>'
                     f'<p><b>Agents:</b> {e(al["agent_role"])}</p><p class="floor">{e(floor)}</p></div>')
    explain = table(["Result", "Performed by", "Skill", "Task", "Intent", "Objective"], explain_rows())
    downloads = [
        (PDF_V2, "The whitepaper", "PDF", "The full paper, version 2.0: every entity, the Assurance Level scale, the worked example, and how AOW relates to existing standards."),
        (PDF_CARD, "Reference card", "PDF", "Every class on one page, by layer, with the Assurance Level scale. For printing and pinning up."),
        ("ontology/aow.ttl", "The ontology", "OWL · Turtle", "For knowledge graphs, reasoners, and ontology editors such as Protégé. Also as JSON-LD."),
        ("ontology/context.jsonld", "JSON-LD context", "JSON-LD", "Makes plain AOW JSON readable as RDF with no changes."),
        ("ontology/shapes.ttl", "Validation shapes", "SHACL", "Checks that a graph of AOW data is well formed."),
        ("schemas/aow.schema.json", "JSON Schemas", "JSON Schema", "One schema per class, plus a document bundle, for teams that never touch RDF."),
        ("downloads/aow-classes.csv", "Classes, attributes, relationships", "CSV", "The whole model as three spreadsheets. Also attributes and relationships CSVs."),
        (PDF_V1, "Version 1.0", "PDF", "The original January 2026 paper, kept as published."),
    ]
    dl = "".join(f'<a class="download" href="{h}"><p class="dl-name">{e(n)} <span class="dl-meta">{e(t)}</span></p>'
                 f'<p class="dl-desc">{e(d)}</p></a>' for h, n, t, d in downloads)
    standards = ["W3C PROV-O", "W3C Organization Ontology", "W3C SOSA", "W3C ODRL", "schema.org", "OWL 2", "SHACL",
                 "JSON-LD 1.1", "BPMN", "DMN", "IEEE XES", "OCEL 2.0", "Model Context Protocol", "Agent2Agent (A2A)",
                 "OpenTelemetry GenAI", "NIST AI RMF", "ISO/IEC 42001", "EU AI Act"]
    dataset = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Agentic Ontology of Work (AOW)",
        "alternateName": "AOW",
        "description": m.meta["description"],
        "url": SITE,
        "sameAs": REPO,
        "identifier": "https://w3id.org/aow",
        "version": m.meta["version"],
        "datePublished": m.meta["released"],
        "inLanguage": "en",
        "isAccessibleForFree": True,
        "creator": {"@type": "Person", "name": "Manish Garg", "sameAs": "https://www.linkedin.com/in/manishga",
                    "affiliation": {"@type": "Organization", "name": "Skan.ai", "url": "https://www.skan.ai"}},
        "publisher": {"@type": "Organization", "name": "Skan, Inc.", "url": "https://www.skan.ai"},
        "license": ["https://creativecommons.org/licenses/by/4.0/", "https://www.apache.org/licenses/LICENSE-2.0"],
        "keywords": ["agentic AI", "ontology", "enterprise AI", "AI governance", "multi-agent systems",
                     "human-in-the-loop", "knowledge graph", "OWL", "SHACL", "JSON-LD"],
        "isRelatedTo": {"@type": "Dataset", "name": "SOA-to-Agentic AI Terminology Mapping", "url": SOA_SITE,
                        "identifier": "https://doi.org/10.5281/zenodo.21823088"},
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": "text/turtle", "contentUrl": SITE + "ontology/aow.ttl"},
            {"@type": "DataDownload", "encodingFormat": "application/ld+json", "contentUrl": SITE + "ontology/aow.jsonld"},
            {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": SITE + "downloads/aow-classes.csv"},
            {"@type": "DataDownload", "encodingFormat": "application/pdf", "contentUrl": SITE + PDF_V2},
        ],
    }
    body = f"""
<div class="hero wrap">
  <p class="eyebrow">An open ontology for agentic work</p>
  <h1>Agentic Ontology of Work</h1>
  <p class="lede">Agents are being put to work faster than anyone can agree on how to describe that work. AOW is a shared, platform-agnostic model for it: what the work is for, who or what does it, under which rules and how much autonomy, what it changed, and what was learned. It's written precisely enough that software can check it.</p>
  <div class="cta-row">
    <a class="btn primary" href="entities/index.html">Explore the ontology</a>
    <a class="btn" href="whitepaper/index.html">Read the whitepaper</a>
    <a class="btn" href="{REPO}">View on GitHub</a>
  </div>
  <p class="meta">Version 2.0 · By Manish Garg, Skan.ai · Free to use and adapt, with attribution</p>
</div>

<section class="wrap divider-top">
  <div class="two-col">
    <div>
      <h2>Why an ontology</h2>
      <p>Ask three teams what an "agent" is and you get four answers. The same goes for "task," "workflow," and "orchestration." That's why integrations break where one platform hands off to another, why governance policies mean different things in different systems, and why audit trails stop at the seams.</p>
      <p>A glossary gives people the same words. An ontology also fixes what each thing carries and how things connect: an Intent serves an Objective, a Result was generated by an Action, and an Action was performed by an Actor under a Policy. Because it's formal, conformance can be checked instead of asserted.</p>
    </div>
    <div>
      <h2>What's in it</h2>
      <p><b>{counts}</b>, across four layers. It follows work from the business <b>Objective</b> it serves, through <b>Intents</b>, <b>Plans</b>, and <b>Tasks</b>, to the <b>Actions</b> that agents and people take with their <b>Skills</b>, the <b>Results</b> those produce, and the <b>Outcomes</b> they add up to.</p>
      <p>Around that path sit the things that make autonomy safe to grant: <b>Policy</b>, <b>Confidence</b>, a five-level <b>Assurance Level</b> scale, an independent <b>Guardian</b>, and <b>Feedback</b> into <b>Memory</b>.</p>
    </div>
  </div>
</section>

<section class="wrap divider-top" id="model">
  <p class="eyebrow">The model</p>
  <h2>Four layers, one graph</h2>
  <p>Each layer answers one question. Hover over or tab to a class to see what it connects to; select it for the full definition.</p>
  <figure class="graph">
    <div class="graph-scroll">
{graph_svg(m, "")}
    </div>
    <p class="g-info" id="g-info" aria-live="polite">Hover over or tab to a class to see its definition and relationships.</p>
    <figcaption>The main path is drawn by default; hovering shows every relationship of a class, with dashed lines for "is a kind of." <span class="graph-hint">On a small screen, scroll the diagram sideways, or use the lists below.</span></figcaption>
  </figure>
  <div class="layers">{"".join(layers)}</div>
</section>

<section class="wrap divider-top" id="autonomy">
  <p class="eyebrow">Governed autonomy</p>
  <h2>Five levels of autonomy, and a rule for when they disagree</h2>
  <p>An Intent says how much autonomy its work allows. A Task or a Skill can narrow that, and each Agent has been cleared up to a level. The <b>effective level is the lowest of them</b>: autonomy can be narrowed along the way, never widened. Within that level, an Agent that isn't confident enough escalates.</p>
  <div class="scale">{"".join(steps)}</div>
  <p class="small muted">The scale builds on the levels-of-automation literature, from Sheridan and Verplank (1978) and Parasuraman, Sheridan, and Wickens (2000) to SAE J3016. <a href="whitepaper/index.html#7-assurance-levels-and-governed-autonomy">How the levels work →</a></p>
</section>

<section class="wrap divider-top" id="checked">
  <p class="eyebrow">Checked, not claimed</p>
  <h2>Every example passes four gates</h2>
  <ol class="gates">
    <li><b>JSON Schema</b>The document is well formed, and unknown keys (typos) are rejected.</li>
    <li><b>SHACL</b>The graph is well formed: every Result has an Action, every link points to the right kind of thing.</li>
    <li><b>Explainability</b>Every Result traces back to the Objective it served.</li>
    <li><b>Oversight</b>No Agent acted beyond the oversight its effective Assurance Level requires.</li>
  </ol>
  <p>Here's gate 3 applied to the <a href="{REPO}/blob/main/examples/claims-processing.jsonld">worked claims example</a>. The last row is a claim the agent escalated at 0.81 confidence, below its 0.90 floor, which an adjuster then decided. Both are in the same record, in the same shape.</p>
  {explain}
</section>

<section class="wrap divider-top" id="downloads">
  <p class="eyebrow">Use it</p>
  <h2>Downloads</h2>
  <p>Everything is generated from one source file, <a href="{REPO}/blob/main/aow.yaml"><code>aow.yaml</code></a>, so the formats can't drift apart. Terms have permanent identifiers under <code>https://w3id.org/aow</code>.</p>
  <div class="download-grid">{dl}</div>
</section>

<section class="wrap divider-top">
  <p class="eyebrow">Standing on shoulders</p>
  <h2>Built from parts the industry already trusts</h2>
  <p>Where a standard already defines a concept, AOW reuses it or aligns with it rather than inventing its own. <a href="whitepaper/index.html#12-how-aow-relates-to-existing-work">Where each comes from, and where AOW differs →</a></p>
  <div class="standards">{"".join(f"<span>{e(s)}</span>" for s in standards)}</div>
</section>

<section class="wrap divider-top">
  <div class="two-col">
    <div class="callout">
      <p class="eyebrow">Companion project</p>
      <h3 style="margin-top:0">SOA-to-Agentic AI Terminology Mapping</h3>
      <p>Twenty-eight Service-Oriented Architecture terms translated into their agentic equivalents. The mapping is the vocabulary; AOW is the structure. A <a href="{REPO}/blob/main/crosswalks/soa-to-agentic-terms.csv">crosswalk</a> connects the two.</p>
      <p><a href="{SOA_SITE}">Read the mapping →</a></p>
    </div>
    <div>
      <h2>Disagree? Good.</h2>
      <p>AOW is a starting point, not a finished standard. The most useful contribution is a real piece of work it can't describe. <a href="{REPO}/issues/new/choose">Open an issue</a>, or read <a href="{REPO}/blob/main/CONTRIBUTING.md">how to contribute</a>.</p>
      <p class="small muted">Cite as: Garg, M. (2026). <i>Agentic Ontology of Work (AOW)</i>, version 2.0.0. Skan.ai. <a href="{REPO}">{REPO.replace("https://", "")}</a></p>
    </div>
  </div>
</section>
"""
    return page(title="Agentic Ontology of Work (AOW)",
                description="An open, platform-agnostic ontology of agentic enterprise work: 25 classes across Perception, Cognition, Execution, and Assurance, with a five-level autonomy scale. OWL, JSON-LD, SHACL, and JSON Schema.",
                body=body + GRAPH_JS, path="index.html", head_extra=jsonld_script(dataset))


def entities_index(m: Model) -> str:
    blocks = []
    new_chip = ' <span class="chip new">new in 2.0</span>'
    for layer in m.layers:
        cards = "".join(
            f'<a class="card" href="{x.slug}/index.html"><p class="name">{e(x.label)}'
            f'{new_chip if x.since.startswith("2") else ""}</p>'
            f'<p>{e(x.definition)}</p></a>' for x in m.entities_in(layer["id"]))
        blocks.append(f'<section class="wrap divider-top" id="{layer["id"]}"><p class="eyebrow">Layer {layer["order"]}</p>'
                      f'<h2><span class="chip {layer["id"]}">{e(layer["name"])}</span> {e(layer["question"])}</h2>'
                      f'<p class="purpose">{e(layer["summary"])}</p><div class="cards">{cards}</div></section>')
    body = f"""
<div class="hero wrap">
  <p class="eyebrow">The ontology</p>
  <h1>{len(m.entities)} classes, four layers</h1>
  <p class="lede">Each class has a page with its definition, purpose, attributes, relationships, alignments to other standards, and an example from the validated examples. For the terse, machine-oriented listing, see the <a href="../ontology/index.html">term reference</a>.</p>
</div>
{"".join(blocks)}
"""
    return page(title="Classes · Agentic Ontology of Work", current="entities",
                description="All 25 classes of the Agentic Ontology of Work, by layer.", body=body, path="entities/index.html")


def entity_page(m: Model, ent, examples: dict, prev_e, next_e) -> str:
    lname = layer_name(m, ent.layer)
    facts = [f'<span class="chip {ent.layer}">{e(lname)}</span>', f"since {e(ent.since[:3])}",
             f'<code>{e(ent.curie)}</code>']
    if ent.abstract:
        facts.insert(1, '<span class="chip">abstract</span>')
    if ent.since.startswith("2"):
        facts.insert(1, '<span class="chip new">new in 2.0</span>')
    parts = [f'<p class="definition">{e(ent.definition)}</p>', f'<p class="purpose">{e(ent.purpose)}</p>']

    if ent.subclass_of or m.descendants(ent.id):
        bits = []
        if ent.subclass_of:
            p = m.by_id[ent.subclass_of]
            bits.append(f'A kind of <a href="../{p.slug}/index.html">{e(p.label)}</a>.')
        kids = [m.by_id[k] for k in m.descendants(ent.id)]
        if kids:
            bits.append("Kinds: " + ", ".join(f'<a href="../{k.slug}/index.html">{e(k.label)}</a>' for k in kids) + ".")
        parts.append(f'<p>{" ".join(bits)}</p>')

    rows, inherited = [], []
    for a in ent.attributes:
        rows.append([f"<code>{e(a.key)}</code>", attr_type_html(m, a), "yes" if a.required else "", e(a.description)])
    for a in m.common:
        if a.key in ent.required_common:
            rows.append([f"<code>{e(a.key)}</code>", e(a.type), "yes", e(a.description)])
    for anc in m.ancestors(ent.id):
        for a in m.by_id[anc].attributes:
            inherited.append(len(rows))
            rows.append([f"<code>{e(a.key)}</code>", attr_type_html(m, a), "yes" if a.required else "",
                         e(a.description) + f' <span class="muted">(from {e(m.by_id[anc].label)})</span>'])
    parts.append('<h2>Attributes</h2>')
    if rows:
        parts.append(table(["Attribute", "Type", "Required", "Description"], rows,
                           row_class=lambda i: "inherited" if i in inherited else ""))
    parts.append('<p class="small muted">Every entity also has an <code>id</code> and a <code>type</code>, and may carry '
                 '<code>label</code>, <code>description</code>, and the provenance facet: <code>version</code>, '
                 '<code>created_at</code>, <code>created_by</code>, <code>revision_of</code>.</p>')

    out_rows = []
    for r in m.outgoing(ent.id):
        targets = ", ".join(f'<a href="../{m.by_id[c].slug}/index.html">{e(m.by_id[c].label)}</a>' for c in r.range)
        req = "yes" if set(r.required) & set(m.lineage(ent.id)) else ""
        via = "" if ent.id in r.domain else f' <span class="muted">(as {e(m.by_id[next(c for c in m.lineage(ent.id) if c in r.domain)].label)})</span>'
        out_rows.append([f"<code>{e(r.key)}</code>{via}", targets, "many" if r.many else "one", req, e(r.description)])
    in_rows = []
    for r in m.incoming(ent.id):
        sources = ", ".join(f'<a href="../{m.by_id[c].slug}/index.html">{e(m.by_id[c].label)}</a>' for c in r.domain)
        in_rows.append([sources, f"<code>{e(r.key)}</code>", e(r.inverse_label)])
    if out_rows:
        parts.append("<h2>Relationships</h2>")
        parts.append(table(["Relationship", "Points to", "How many", "Required", "Meaning"], out_rows))
    if in_rows:
        parts.append(f"<h3>Pointed to by</h3>")
        parts.append(table(["From", "Relationship", "Read backward as"], in_rows))

    if ent.notes:
        parts.append("<h2>Notes</h2><div class=\"notes\">" + "".join(f"<p>{e(n)}</p>" for n in ent.notes) + "</div>")
    if ent.alignments:
        al_rows = [[e(a["scheme"]), f"<code>{e(a['term'])}</code>", e(a["relation"])] for a in ent.alignments]
        parts.append("<h2>Alignments</h2>")
        parts.append(table(["Standard or protocol", "Term", "Correspondence"], al_rows))

    ex = examples.get(ent.id)
    if ex:
        node, src = ex
        parts.append(f'<h2>Example</h2><p class="small muted">From <a href="{REPO}/blob/main/{src}"><code>{e(src)}</code></a>, '
                     f'which passes every validation gate.</p><pre><code>{e(json.dumps(node, indent=2, ensure_ascii=False))}</code></pre>')

    links = [f'<a href="../../ontology/index.html#{ent.id}">Term reference</a>']
    if not ent.abstract:
        links.append(f'<a href="../../schemas/{ent.slug}.schema.json">JSON Schema</a>')
    links.append(f'<a href="{REPO}/blob/main/ontology/shapes.ttl">SHACL shape <code>aowsh:{ent.id}Shape</code></a>')
    parts.append(f'<p class="small">{" · ".join(links)}</p>')

    pager = '<nav class="pager" aria-label="Classes">'
    pager += f'<a href="../{prev_e.slug}/index.html">← {e(prev_e.label)}</a>' if prev_e else "<span></span>"
    pager += f'<a href="../{next_e.slug}/index.html">{e(next_e.label)} →</a>' if next_e else "<span></span>"
    pager += "</nav>"

    term = {"@context": "https://schema.org", "@type": "DefinedTerm", "name": ent.label, "description": ent.definition,
            "termCode": ent.curie, "url": f"{SITE}entities/{ent.slug}/", "sameAs": expand(ent.curie),
            "inDefinedTermSet": {"@type": "DefinedTermSet", "name": "Agentic Ontology of Work", "url": SITE}}
    body = f"""
<div class="wrap narrow">
  <p class="crumbs"><a href="../index.html">Ontology</a> / <a href="../index.html#{ent.layer}">{e(lname)}</a></p>
  <div class="entity-head">
    <h1>{e(ent.label)}</h1>
    <div class="facts">{" ".join(facts)}</div>
  </div>
  {"".join(parts)}
  {pager}
</div>
"""
    return page(title=f"{ent.label} · Agentic Ontology of Work", current="entities", description=ent.definition,
                body=body, path=f"entities/{ent.slug}/index.html", head_extra=jsonld_script(term), og_type="article")


def reference(m: Model) -> str:
    cls = []
    for ent in m.entities:
        sup = f' A kind of <a href="#{ent.subclass_of}">{e(m.by_id[ent.subclass_of].label)}</a>.' if ent.subclass_of else ""
        cls.append(f'<div class="ref-item" id="{ent.id}"><h3><code>aow:{ent.id}</code> {e(ent.label)} '
                   f'<span class="chip {ent.layer}">{e(layer_name(m, ent.layer))}</span></h3>'
                   f'<p>{e(ent.definition)}{sup}</p><p class="small"><a href="../entities/{ent.slug}/index.html">Full definition →</a></p></div>')
    rels = []
    for r in m.relationships:
        rels.append(f'<div class="ref-item" id="{camel(r.key)}"><h3><code>{e(r.curie)}</code> {e(r.label)}</h3>'
                    f'<p>{e(r.description)}</p><p class="small muted">From {", ".join(m.by_id[c].label for c in r.domain)} '
                    f'to {", ".join(m.by_id[c].label for c in r.range)}{" (many)" if r.many else ""}. JSON key <code>{e(r.key)}</code>.'
                    f'{" Specializes <code>" + e(r.prov) + "</code>." if r.prov else ""}</p></div>')
    attrs = []
    for key, (a, owners) in sorted(m.attribute_index().items()):
        attrs.append(f'<div class="ref-item" id="{camel(key)}"><h3><code>{e(a.curie)}</code></h3>'
                     f'<p>{e(a.description)}</p><p class="small muted">On {", ".join(m.by_id[o].label for o in owners)}. '
                     f'Type {e(a.type)}. JSON key <code>{e(key)}</code>.</p></div>')
    levels = []
    for al in m.assurance_levels:
        levels.append(f'<div class="ref-item" id="{al["id"]}"><h3><code>aow:{al["id"]}</code> {e(al["label"])}</h3>'
                      f'<p><b>People:</b> {e(al["human_role"])} <b>Agents:</b> {e(al["agent_role"])}</p>'
                      f'<p class="small muted">Review: {e(al["review_protocol"])}</p></div>')
    body = f"""
<div class="hero wrap narrow">
  <p class="eyebrow">Term reference</p>
  <h1>Agentic Ontology of Work {e(m.meta["version"])}</h1>
  <p class="lede">Every term in the <code>aow:</code> namespace, <code>https://w3id.org/aow#</code>. Each term's identifier resolves to its entry on this page.</p>
  {table(["", ""], [["Ontology IRI", "<code>https://w3id.org/aow</code>"], ["This version", f"<code>https://w3id.org/aow/{e(m.meta['version'])}</code>"],
                    ["Formats", '<a href="aow.ttl">Turtle</a> · <a href="aow.jsonld">JSON-LD</a> · <a href="context.jsonld">JSON-LD context</a> · <a href="shapes.ttl">SHACL shapes</a> · <a href="../schemas/aow.schema.json">JSON Schema</a>'],
                    ["Released", e(m.meta["released"])], ["Creator", "Manish Garg, Skan.ai"], ["License", "Apache 2.0"]])}
  <p class="small"><a href="#classes">Classes</a> · <a href="#relationships">Relationships</a> · <a href="#attributes">Attributes</a> · <a href="#levels">Assurance Levels</a></p>
</div>
<section class="wrap narrow" id="classes"><h2>Classes</h2>{"".join(cls)}</section>
<section class="wrap narrow" id="relationships"><h2>Relationships</h2>{"".join(rels)}</section>
<section class="wrap narrow" id="attributes"><h2>Attributes</h2><p class="small muted">Common attributes map to existing properties: <code>label</code> to <code>rdfs:label</code>, <code>description</code> to <code>dcterms:description</code>, <code>version</code> to <code>schema:version</code>, <code>created_at</code> to <code>prov:generatedAtTime</code>, <code>created_by</code> to <code>prov:wasAttributedTo</code>, <code>revision_of</code> to <code>prov:wasRevisionOf</code>.</p>{"".join(attrs)}</section>
<section class="wrap narrow" id="levels"><h2>Assurance Levels</h2>{"".join(levels)}</section>
"""
    return page(title="Term reference · Agentic Ontology of Work", current="reference",
                description="Every class, relationship, attribute, and Assurance Level in the aow: namespace.",
                body=body, path="ontology/index.html")


def whitepaper(m: Model) -> str:
    text = (ROOT / "whitepaper.md").read_text(encoding="utf-8")
    text = re.sub(r"<!-- /?aow:generated[^>]*-->\n?", "", text)
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"])
    body_html = md.convert(text)
    body_html = body_html.replace("<table>", '<div class="table-scroll"><table>').replace("</table>", "</table></div>")
    toc = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body_html)
    toc_html = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in toc)
    body = f"""
<div class="wrap">
  <div class="prose" style="padding-top:40px">
    <p class="eyebrow">Whitepaper · version 2.0</p>
    <p class="small"><a href="../{PDF_V2}">Download as PDF</a> · <a href="{REPO}/blob/main/whitepaper.md">Source on GitHub</a> · <a href="../{PDF_V1}">Version 1.0 (PDF)</a></p>
    <details class="toc"><summary>Contents</summary><ol>{toc_html}</ol></details>
    {body_html}
  </div>
</div>
"""
    return page(title="Whitepaper · Agentic Ontology of Work", current="whitepaper",
                description="The Agentic Ontology of Work, version 2.0: a foundational semantic model for intelligent, autonomous, and governed enterprise work.",
                body=body, path="whitepaper/index.html", og_type="article")


def about(m: Model) -> str:
    body = f"""
<div class="hero wrap narrow">
  <p class="eyebrow">About</p>
  <h1>Why this exists, and who made it</h1>
  <p class="lede">The short version of the argument, what changed from version 1.0, and how to take part.</p>
</div>
<section class="wrap narrow">
  <h2>Vocabulary was step one</h2>
  <p>The <a href="{SOA_SITE}">SOA-to-Agentic AI Terminology Mapping</a> borrowed a vocabulary the industry had already agreed on once, Service-Oriented Architecture's, and translated it into agentic terms. That gives people the same words. It doesn't give them the same structure: two teams can agree on what an "Agent" and an "Intent" are and still model the link between them differently, and then their systems still can't share a record of who did what, or why.</p>
  <p>SOA hit the same wall, and the answer then was an ontology: first from The Open Group, then as an ISO standard (ISO/IEC 18384-3), which pinned down how services, contracts, and compositions relate. AOW is that step for agentic work.</p>

  <h2>What's different about agentic work</h2>
  <p>Services execute fixed operations. Agents interpret goals, plan, and act, with more or less autonomy depending on the stakes and on how sure they are. So AOW needs things SOA's ontology never did: graded autonomy, confidence, people in the loop on the record, and a feedback loop that is itself traceable.</p>

  <h2>What it deliberately isn't</h2>
  <ul>
    <li><b>Not tied to a product or platform.</b> Nothing in it assumes a vendor, model, or agent framework.</li>
    <li><b>Not a protocol.</b> MCP and A2A move work between agents and tools; AOW describes the work they move.</li>
    <li><b>Not a policy language.</b> A Policy can hold rules in ODRL, Rego, Cedar, DMN, or plain text.</li>
    <li><b>Not finished.</b> Cross-organization governance, negotiation between agents, and trustworthy confidence are open. <a href="../whitepaper/index.html#15-limitations-and-open-questions">The whitepaper lists them.</a></li>
  </ul>

  <h2>What changed from version 1.0</h2>
  <p>Version 1.0 (January 2026) set out the four layers, fifteen entities, the lifecycle, and the validation criteria. Version 2.0 keeps all of it and:</p>
  <ul>
    <li>adds Work Item, Signal, Observation, Plan, Task, Actor, Human Actor, and Role</li>
    <li>defines Action, which 1.0 named but never defined, and makes it the thing that produces Results</li>
    <li>defines the Assurance Level scale, AL0 to AL4, which 1.0 used but never specified</li>
    <li>makes provenance and versioning a facet of every entity, using W3C PROV-O</li>
    <li>ships the ontology in OWL, JSON-LD, SHACL, and JSON Schema, with validated examples</li>
    <li>pairs each validation criterion with an automated check</li>
  </ul>
  <p>The <a href="{REPO}/blob/main/CHANGELOG.md">changelog</a> has every change. <a href="../{PDF_V1}">Version 1.0 is kept as published.</a></p>

  <h2>Who made it</h2>
  <p>AOW was written by <a href="https://www.linkedin.com/in/manishga">Manish Garg</a> of <a href="https://www.skan.ai">Skan.ai</a>, and is published by Skan, Inc. It reflects a view that runs through Skan.ai's work in process intelligence: that you have to see how work actually happens before you can decide how to automate it, and that agents' work should be as observable as anyone else's. That's why AOW has a Perception layer, and why its Actions leave the same trail whoever performs them.</p>
  <p>AOW is not a Skan.ai product specification. It's offered openly, under licenses that let anyone use, adapt, and build on it commercially.</p>

  <h2>Take part</h2>
  <p>The most useful contribution is a real piece of work AOW can't describe. <a href="{REPO}/issues/new/choose">Open an issue</a> with the case, or propose a term. Pull requests change <code>aow.yaml</code>; everything else is generated. See <a href="{REPO}/blob/main/CONTRIBUTING.md">CONTRIBUTING.md</a>.</p>

  <h2>License and citation</h2>
  <p>Prose: <a href="https://creativecommons.org/licenses/by/4.0/">CC-BY 4.0</a>. Ontology, shapes, schemas, queries, examples, and code: <a href="https://www.apache.org/licenses/LICENSE-2.0">Apache 2.0</a>. Both let you copy, adapt, and use the work commercially, as long as you credit the author and Skan.ai and say what you changed.</p>
  <blockquote>Garg, M. (2026). <i>Agentic Ontology of Work (AOW)</i>, version 2.0.0. Skan.ai. {REPO.replace("https://", "")}</blockquote>
</section>
"""
    return page(title="About · Agentic Ontology of Work", current="about",
                description="Why the Agentic Ontology of Work exists, what changed in version 2.0, who made it, and how to contribute.",
                body=body, path="about/index.html")


def card(m: Model) -> str:
    cols = []
    for layer in m.layers:
        items = "".join(f'<p style="margin:0 0 7px"><b>{e(x.label)}</b> <span style="color:var(--muted)">{e(x.definition)}</span></p>'
                        for x in m.entities_in(layer["id"]))
        cols.append(f'<div class="layer {layer["id"]}" style="padding:10px 12px"><h3 style="font-size:15px">{e(layer["name"])}</h3>'
                    f'<p class="q" style="margin-bottom:8px">{e(layer["question"])}</p><div style="font-size:10.5px;line-height:1.35">{items}</div></div>')
    levels = "".join(f'<div class="step" style="--n:{al["level"]};padding:8px 10px"><p class="lvl" style="font-size:16px">{al["id"]} '
                     f'<span style="font-weight:600;font-size:13px">{e(al["label"])}</span></p><p style="font-size:10.5px;margin:0">{e(al["agent_role"])}</p></div>'
                     for al in m.assurance_levels)
    body = f"""
<div class="wrap" style="max-width:1100px;padding-top:18px">
  <p class="eyebrow" style="margin:0">Reference card · version {e(m.meta["version"])}</p>
  <h1 style="font-size:28px;margin:4px 0 6px">Agentic Ontology of Work</h1>
  <p style="font-size:12.5px;margin:0 0 10px;color:var(--ink-2)">Objective → Intent → Plan → Task → Action (by an Actor, with a Skill) → Result → Outcome → Feedback → Memory. Governed by Policy, Confidence, Assurance Level, and the Guardian.</p>
  <div class="layers" style="grid-template-columns:repeat(4,1fr);gap:10px;margin-top:8px">{"".join(cols)}</div>
  <p style="font-size:12px;margin:12px 0 4px"><b>Assurance Levels.</b> The effective level is the lowest of the Intent's, Task's, and Skill's, and the Agent's clearance. Below the confidence floor, escalate.</p>
  <div class="scale" style="grid-template-columns:repeat(5,1fr);margin:4px 0">{levels}</div>
  <p style="font-size:10.5px;color:var(--muted);margin-top:10px">By Manish Garg, Skan.ai · {SITE} · Identifiers https://w3id.org/aow · Prose CC-BY 4.0, ontology Apache 2.0</p>
</div>
"""
    doc = page(title="Reference card · Agentic Ontology of Work", description="One-page reference card.", body=body,
               path="print/card/index.html")
    return doc.replace("<head>", '<head>\n<meta name="robots" content="noindex">', 1)


def not_found(m: Model) -> str:
    body = """
<div class="hero wrap narrow">
  <p class="eyebrow">404</p>
  <h1>That page isn't here</h1>
  <p class="lede">Try the <a href="/agentic-ontology-of-work/">home page</a>, the <a href="/agentic-ontology-of-work/entities/">list of classes</a>, or the <a href="/agentic-ontology-of-work/ontology/">term reference</a>.</p>
</div>
"""
    doc = page(title="Not found · Agentic Ontology of Work", description="Page not found.", body=body, path="404.html")
    return doc.replace('href="assets/', 'href="/agentic-ontology-of-work/assets/').replace(
        'href="favicon', 'href="/agentic-ontology-of-work/favicon').replace(
        'href="apple-touch', 'href="/agentic-ontology-of-work/apple-touch').replace(
        'href="index.html"', 'href="/agentic-ontology-of-work/"').replace(
        'href="entities/', 'href="/agentic-ontology-of-work/entities/').replace(
        'href="whitepaper/', 'href="/agentic-ontology-of-work/whitepaper/').replace(
        'href="ontology/', 'href="/agentic-ontology-of-work/ontology/').replace(
        'href="about/', 'href="/agentic-ontology-of-work/about/')


def main() -> None:
    m = Model()
    examples = load_examples()
    write("index.html", home(m))
    write("entities/index.html", entities_index(m))
    ordered = [x for layer in m.layers for x in m.entities_in(layer["id"])]
    for i, ent in enumerate(ordered):
        write(f"entities/{ent.slug}/index.html",
              entity_page(m, ent, examples, ordered[i - 1] if i else None, ordered[i + 1] if i + 1 < len(ordered) else None))
    write("ontology/index.html", reference(m))
    write("whitepaper/index.html", whitepaper(m))
    write("about/index.html", about(m))
    write("print/card/index.html", card(m))
    write("404.html", not_found(m))
    write(".nojekyll", "")
    print(f"site: {len(ordered) + 7} pages")


if __name__ == "__main__":
    main()
