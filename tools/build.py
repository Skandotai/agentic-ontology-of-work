"""Build every derived artifact from aow.yaml.

    python tools/build.py

Writes:
    ontology/aow.ttl            OWL ontology (Turtle)
    ontology/aow.jsonld         OWL ontology (JSON-LD)
    ontology/context.jsonld     JSON-LD context for AOW instance data
    ontology/shapes.ttl         SHACL shapes for AOW instance data
    schemas/aow.schema.json     JSON Schema bundle (every class + document)
    schemas/<class>.schema.json one standalone JSON Schema per class
    docs/downloads/*.csv        classes, attributes, relationships
    whitepaper.md               regenerates the marked reference sections
    docs/...                    copies of the above, served by GitHub Pages

The Turtle is written by hand rather than by rdflib's serializer so that the
output is stable across runs (CI fails if a build changes a committed file)
and readable in a diff.
"""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model import COMMON_PROPERTY, LIST_TYPES, PREFIXES, ROOT, XSD_FOR, Model, camel, expand  # noqa: E402

W3ID = "https://w3id.org/aow"
SHAPES_NS = "https://w3id.org/aow/shapes#"
LICENSE_DATA = "https://www.apache.org/licenses/LICENSE-2.0"
ALIGN_CURIE = re.compile(r"^(prov|sosa|odrl|org|schema):[A-Za-z]+$")


# ---------------------------------------------------------------- Turtle bits
def lit(text, lang: str | None = "en") -> str:
    s = str(text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()
    return f'"{s}"@{lang}' if lang else f'"{s}"'


def typed(value, datatype: str) -> str:
    return f'"{value}"^^{datatype}'


def block(subject: str, pairs: list) -> str:
    """Render one Turtle subject block. pairs: [(predicate, [objects])]."""
    lines = []
    pairs = [(p, o) for p, o in pairs if o]
    for i, (pred, objs) in enumerate(pairs):
        end = " ." if i == len(pairs) - 1 else " ;"
        lines.append(f"    {pred} {' , '.join(objs)}{end}")
    return f"{subject}\n" + "\n".join(lines) + "\n\n"


def prefix_header(names: list) -> str:
    return "".join(f"@prefix {n}: <{PREFIXES[n]}> .\n" for n in names) + "\n"


def human(key: str) -> str:
    return key.replace("_", " ")


# ------------------------------------------------------------------- Ontology
def build_owl(m: Model) -> str:
    meta = m.meta
    out = io.StringIO()
    out.write(f"# {meta['title']} ({meta['short_title']}) {meta['version']}\n")
    out.write("# Generated from aow.yaml by tools/build.py. Do not edit by hand.\n\n")
    out.write(prefix_header(["aow", "owl", "rdf", "rdfs", "xsd", "skos", "dcterms", "vann", "prov", "schema",
                             "sosa", "odrl", "org"]))

    out.write(block(f"<{W3ID}>", [
        ("a", ["owl:Ontology"]),
        ("dcterms:title", [lit(meta["title"])]),
        ("dcterms:description", [lit(meta["description"])]),
        ("owl:versionIRI", [f"<{W3ID}/{meta['version']}>"]),
        ("owl:versionInfo", [lit(meta["version"], None)]),
        ("dcterms:issued", [typed(meta["released"], "xsd:date")]),
        ("dcterms:creator", [lit(f"{meta['creator']['name']} ({meta['creator']['affiliation']})", None)]),
        ("dcterms:publisher", [lit(meta["publisher"]["name"], None)]),
        ("dcterms:license", [f"<{LICENSE_DATA}>"]),
        ("vann:preferredNamespacePrefix", [lit(meta["prefix"], None)]),
        ("vann:preferredNamespaceUri", [lit(meta["namespace"], None)]),
        ("rdfs:seeAlso", [f"<{meta['site']}>", f"<{meta['repository']}>"]),
    ]))

    out.write("\n# ---- Annotation properties used to document the ontology\n\n")
    for key, comment in [
        ("layer", "The layer of the four-layer stack a class belongs to."),
        ("since", "The AOW version in which a term first appeared."),
        ("inverseLabel", "How to read a relationship from its object back to its subject."),
        ("jsonKey", "The key used for this property in AOW JSON and JSON-LD documents."),
        ("alignment", "A correspondence to a term in a standard or protocol that has no dereferenceable IRI."),
    ]:
        out.write(block(f"aow:{key}", [("a", ["owl:AnnotationProperty"]), ("rdfs:label", [lit(human(re.sub(r'(?<!^)(?=[A-Z])', ' ', key).lower()))]),
                                       ("rdfs:comment", [lit(comment)]), ("rdfs:isDefinedBy", [f"<{W3ID}>"])]))

    out.write("\n# ---- Layers\n\n")
    for layer in m.layers:
        out.write(block(f"aow:{layer['name']}Layer", [
            ("a", ["skos:Concept"]),
            ("skos:prefLabel", [lit(layer["name"] + " layer")]),
            ("skos:notation", [lit(str(layer["order"]), None)]),
            ("skos:definition", [lit(layer["summary"])]),
            ("rdfs:comment", [lit(layer["question"])]),
            ("rdfs:isDefinedBy", [f"<{W3ID}>"]),
        ]))

    out.write("\n# ---- Classes\n\n")
    layer_iri = {l["id"]: f"aow:{l['name']}Layer" for l in m.layers}
    disjoint: dict = {}
    for group in m.disjoint:
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                disjoint.setdefault(a, []).append(f"aow:{b}")
    for e in m.entities:
        supers = [f"aow:{e.subclass_of}"] if e.subclass_of else []
        matches: dict = {}
        notes = []
        for al in e.alignments:
            if ALIGN_CURIE.match(al["term"]):
                rel = "rdfs:subClassOf" if al["relation"] == "subClassOf" else f"skos:{al['relation']}"
                if rel == "rdfs:subClassOf":
                    supers.append(al["term"])
                else:
                    matches.setdefault(rel, []).append(al["term"])
            else:
                notes.append(lit(f"{al['scheme']}: {al['term']} ({al['relation']})"))
        pairs = [
            ("a", ["owl:Class"]),
            ("rdfs:label", [lit(e.label)]),
            ("skos:definition", [lit(e.definition)]),
            ("rdfs:comment", [lit(e.purpose)]),
            ("skos:scopeNote", [lit(n) for n in e.notes]),
            ("rdfs:subClassOf", supers),
            ("owl:disjointWith", disjoint.get(e.id, [])),
            ("aow:layer", [layer_iri[e.layer]]),
            ("aow:since", [lit(e.since, None)]),
        ]
        pairs += sorted(matches.items())
        pairs += [("aow:alignment", notes), ("rdfs:isDefinedBy", [f"<{W3ID}>"])]
        out.write(block(e.curie, pairs))

    def domain_range(pred: str, classes: list) -> tuple:
        if classes == ["any"]:
            return (pred, [])
        curies = [f"aow:{c}" for c in classes]
        if len(curies) == 1:
            return (pred, curies)
        return ("schema:domainIncludes" if pred == "rdfs:domain" else "schema:rangeIncludes", curies)

    out.write("\n# ---- Relationships (object properties)\n\n")
    for r in m.relationships:
        out.write(block(r.curie, [
            ("a", ["owl:ObjectProperty"]),
            ("rdfs:label", [lit(r.label)]),
            ("aow:inverseLabel", [lit(r.inverse_label)]),
            ("rdfs:comment", [lit(r.description)]),
            domain_range("rdfs:domain", r.domain),
            domain_range("rdfs:range", r.range),
            ("rdfs:subPropertyOf", [r.prov] if r.prov else []),
            ("aow:jsonKey", [lit(r.key, None)]),
            ("rdfs:isDefinedBy", [f"<{W3ID}>"]),
        ]))

    out.write("\n# ---- Attributes\n\n")
    for key, (a, owners) in sorted(m.attribute_index().items()):
        if a.is_ref:
            kind, rng = "owl:ObjectProperty", domain_range("rdfs:range", a.range)
        else:
            kind, rng = "owl:DatatypeProperty", ("rdfs:range", [XSD_FOR[a.type]])
        out.write(block(a.curie, [
            ("a", [kind]),
            ("rdfs:label", [lit(human(key))]),
            ("rdfs:comment", [lit(a.description)]),
            domain_range("rdfs:domain", owners),
            rng,
            ("aow:jsonKey", [lit(key, None)]),
            ("rdfs:isDefinedBy", [f"<{W3ID}>"]),
        ]))

    out.write("\n# ---- The Assurance Level scale\n\n")
    for al in m.assurance_levels:
        pairs = [
            ("a", ["owl:NamedIndividual", "aow:AssuranceLevel"]),
            ("rdfs:label", [lit(f"{al['id']} {al['label']}")]),
            ("skos:notation", [lit(al["id"], None)]),
            ("aow:level", [str(al["level"])]),
            ("aow:humanRole", [lit(al["human_role"])]),
            ("aow:agentRole", [lit(al["agent_role"])]),
            ("aow:reviewProtocol", [lit(al["review_protocol"])]),
            ("aow:riskClass", [lit(al["risk_class"])]),
        ]
        if al["default_confidence_floor"] is not None:
            pairs.append(("aow:defaultConfidenceFloor", [typed(al["default_confidence_floor"], "xsd:double")]))
        pairs.append(("rdfs:isDefinedBy", [f"<{W3ID}>"]))
        out.write(block(f"aow:{al['id']}", pairs))
    return out.getvalue()


# -------------------------------------------------------------------- Context
def build_context(m: Model) -> dict:
    ctx: dict = {"@version": 1.1}
    for p in ["aow", "prov", "xsd", "rdf", "rdfs", "dcterms", "schema"]:
        ctx[p] = PREFIXES[p]
    ctx["@vocab"] = PREFIXES["aow"]
    ctx["id"] = "@id"
    ctx["type"] = "@type"

    def term(a) -> dict | str:
        iri = a.curie
        if a.is_ref:
            t = {"@id": iri, "@type": "@id"}
        elif a.type == "datetime":
            t = {"@id": iri, "@type": "xsd:dateTime"}
        elif a.type in ("uri", "uri-list"):
            t = {"@id": iri, "@type": "xsd:anyURI"}
        elif a.type == "json":
            t = {"@id": iri, "@type": "@json"}
        else:
            t = {"@id": iri}
        if a.many:
            t["@container"] = "@set"
        return t if len(t) > 1 else iri

    for a in m.common:
        if a.key in ("id", "type"):
            continue
        ctx[a.key] = term(a)
    for key, (a, _) in sorted(m.attribute_index().items()):
        ctx[key] = term(a)
    for r in m.relationships:
        t = {"@id": r.curie, "@type": "@id"}
        if r.many:
            t["@container"] = "@set"
        ctx[r.key] = t
    return {"@context": ctx}


# --------------------------------------------------------------------- SHACL
def build_shapes(m: Model) -> str:
    out = io.StringIO()
    out.write(f"# SHACL shapes for {m.meta['title']} {m.meta['version']} instance data.\n")
    out.write("# Generated from aow.yaml by tools/build.py. Do not edit by hand.\n")
    out.write("# Validate with the ontology mixed in, so subclasses are recognized, and without\n")
    out.write("# RDFS inference (which would infer types from ranges), for example:\n")
    out.write("#   pyshacl -s shapes.ttl -e aow.ttl -i none data.ttl\n\n")
    out.write(f"@prefix aowsh: <{SHAPES_NS}> .\n")
    out.write(prefix_header(["aow", "sh", "rdf", "rdfs", "xsd", "dcterms", "prov", "schema"]))
    out.write(block(f"<{W3ID}/shapes>", [
        ("a", ["<http://www.w3.org/2002/07/owl#Ontology>"]),
        ("rdfs:label", [lit(f"{m.meta['title']} shapes")]),
        ("<http://www.w3.org/2002/07/owl#versionInfo>", [lit(m.meta["version"], None)]),
        ("dcterms:license", [f"<{LICENSE_DATA}>"]),
    ]))

    def number_or() -> str:
        return "sh:or ( [ sh:datatype xsd:double ] [ sh:datatype xsd:integer ] [ sh:datatype xsd:decimal ] )"

    def attr_shape(a, required: bool) -> str:
        parts = [f"sh:path {a.curie}", f"sh:name {lit(a.key, None)}"]
        if a.is_ref:
            rng = a.range or []
            if rng and rng != ["any"]:
                parts.append(f"sh:class aow:{rng[0]}" if len(rng) == 1 else
                             "sh:or ( " + " ".join(f"[ sh:class aow:{c} ]" for c in rng) + " )")
            parts.append("sh:nodeKind sh:IRI")
        elif a.type in ("number",):
            parts.append(number_or())
        elif a.type == "integer":
            parts.append("sh:datatype xsd:integer")
        elif a.type == "boolean":
            parts.append("sh:datatype xsd:boolean")
        elif a.type == "datetime":
            parts.append("sh:datatype xsd:dateTime")
        elif a.type in ("uri", "uri-list"):
            parts.append("sh:datatype xsd:anyURI")
        elif a.type == "json":
            parts.append("sh:datatype rdf:JSON")
        elif a.type == "enum":
            parts.append("sh:in ( " + " ".join(lit(v, None) for v in a.values) + " )")
        elif a.key != "label":
            parts.append("sh:or ( [ sh:datatype xsd:string ] [ sh:datatype rdf:langString ] )")
        if a.min is not None:
            parts.append(f"sh:minInclusive {a.min}")
        if a.max is not None:
            parts.append(f"sh:maxInclusive {a.max}")
        if required:
            parts.append("sh:minCount 1")
        if a.type not in LIST_TYPES and a.key not in ("label", "description"):
            parts.append("sh:maxCount 1")
        return "[ " + " ; ".join(parts) + " ]"

    def rel_shape(r, required: bool) -> str:
        parts = [f"sh:path {r.curie}", f"sh:name {lit(r.key, None)}", "sh:nodeKind sh:IRI"]
        parts.append(f"sh:class aow:{r.range[0]}" if len(r.range) == 1 else
                     "sh:or ( " + " ".join(f"[ sh:class aow:{c} ]" for c in r.range) + " )")
        if required:
            parts.append("sh:minCount 1")
        if not r.many:
            parts.append("sh:maxCount 1")
        return "[ " + " ; ".join(parts) + " ]"

    roots = [e for e in m.entities if not e.subclass_of]
    common = [a for a in m.common if a.key not in ("id", "type")]
    out.write(block("aowsh:CommonShape", [
        ("a", ["sh:NodeShape"]),
        ("rdfs:comment", [lit("Attributes every AOW entity may carry, including the provenance facet.")]),
        ("sh:targetClass", [e.curie for e in roots]),
        ("sh:property", ["\n        " + attr_shape(a, False) for a in common]),
    ]))

    for e in m.entities:
        props = [attr_shape(a, a.required) for a in e.attributes]
        props += [attr_shape(a, True) for a in m.common if a.key in e.required_common]
        props += [rel_shape(r, e.id in r.required) for r in m.relationships if e.id in r.domain]
        out.write(block(f"aowsh:{e.id}Shape", [
            ("a", ["sh:NodeShape"]),
            ("rdfs:label", [lit(f"{e.label} shape")]),
            ("sh:targetClass", [e.curie]),
            ("sh:property", ["\n        " + p for p in props]),
        ]))
    return out.getvalue()


# --------------------------------------------------------------- JSON Schema
SCHEMA_BASE = f"{W3ID}/schemas/"
EXT_PATTERN = "^[A-Za-z][A-Za-z0-9_-]*:[A-Za-z0-9_-]+$"


def json_type(a) -> dict:
    d = {"description": a.description}
    t = a.type
    if a.is_ref:
        d["$ref"] = "#/$defs/ref"
    elif t in ("string", "text"):
        d["type"] = "string"
    elif t == "enum":
        d["enum"] = list(a.values)
    elif t == "string-list":
        d.update({"type": "array", "items": {"type": "string"}})
    elif t == "uri-list":
        d.update({"type": "array", "items": {"type": "string", "format": "uri-reference"}})
    elif t == "number":
        d["type"] = "number"
    elif t == "integer":
        d["type"] = "integer"
    elif t == "boolean":
        d["type"] = "boolean"
    elif t == "datetime":
        d.update({"type": "string", "format": "date-time"})
    elif t == "uri":
        d.update({"type": "string", "format": "uri-reference"})
    elif t == "class":
        pass
    if a.min is not None:
        d["minimum"] = a.min
    if a.max is not None:
        d["maximum"] = a.max
    return d


def class_schema(m: Model, cid: str) -> dict:
    e = m.by_id[cid]
    props: dict = {}
    required = ["id", "type"]
    for a in m.all_attributes(cid):
        if a.key == "id":
            props["id"] = {"$ref": "#/$defs/ref", "description": a.description}
        elif a.key == "type":
            props["type"] = {"const": cid, "description": a.description}
        else:
            props[a.key] = json_type(a)
            if a.required:
                required.append(a.key)
    for c in m.lineage(cid):
        for key in m.by_id[c].required_common:
            required.append(key)
    for r in m.outgoing(cid):
        ref = {"$ref": "#/$defs/ref"}
        props[r.key] = ({"type": "array", "items": ref, "description": r.description} if r.many
                        else {**ref, "description": r.description})
        if set(r.required) & set(m.lineage(cid)):
            required.append(r.key)
    return {
        "title": e.label,
        "description": e.definition,
        "type": "object",
        "properties": props,
        "patternProperties": {EXT_PATTERN: {"description": "Extension property, namespaced with a prefix."}},
        "additionalProperties": False,
        "required": list(dict.fromkeys(required)),
    }


REF_DEF = {"type": "string", "minLength": 1,
           "description": "Identifier of an entity: an IRI, a compact IRI such as aow:AL2, or an id relative to the document base."}


def build_schemas(m: Model) -> dict:
    concrete = [e.id for e in m.entities if not e.abstract]
    defs = {"ref": REF_DEF}
    for e in m.entities:
        defs[e.id] = class_schema(m, e.id)
    defs["node"] = {
        "type": "object",
        "required": ["type"],
        "properties": {"type": {"enum": concrete}},
        "allOf": [{"if": {"properties": {"type": {"const": c}}}, "then": {"$ref": f"#/$defs/{c}"}} for c in concrete],
    }
    bundle = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_BASE + "aow.schema.json",
        "title": f"{m.meta['title']} {m.meta['version']} document",
        "description": "An AOW JSON-LD document: a @context and a @graph of AOW entities.",
        "type": "object",
        "properties": {
            "@context": {"description": "Must include the AOW context, https://w3id.org/aow/context.jsonld."},
            "@graph": {"type": "array", "items": {"$ref": "#/$defs/node"}},
        },
        "required": ["@context", "@graph"],
        "$defs": defs,
    }
    files = {"aow.schema.json": bundle}
    for e in m.entities:
        if e.abstract:
            continue
        s = {"$schema": "https://json-schema.org/draft/2020-12/schema",
             "$id": SCHEMA_BASE + f"{e.slug}.schema.json", **class_schema(m, e.id), "$defs": {"ref": REF_DEF}}
        files[f"{e.slug}.schema.json"] = s
    return files


# ----------------------------------------------------------------------- CSV
def csv_text(rows: list) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    return buf.getvalue()


def build_csvs(m: Model) -> dict:
    layer_name = {l["id"]: l["name"] for l in m.layers}
    classes = [["class", "label", "layer", "subclass_of", "since", "abstract", "definition", "purpose", "iri"]]
    for e in m.entities:
        classes.append([e.id, e.label, layer_name[e.layer], e.subclass_of or "", e.since, str(e.abstract).lower(),
                        e.definition, e.purpose, expand(e.curie)])
    attrs = [["class", "key", "rdf_property", "type", "required", "allowed_values", "description"]]
    for a in m.common:
        attrs.append(["(all)", a.key, a.curie if a.key not in ("id", "type") else f"@{a.key}", a.type,
                      str(a.required).lower(), "", a.description])
    for e in m.entities:
        for a in e.attributes:
            attrs.append([e.id, a.key, a.curie, a.type if not a.is_ref else f"ref:{'|'.join(a.range)}",
                          str(a.required).lower(), "|".join(a.values or []), a.description])
    rels = [["key", "rdf_property", "label", "inverse_label", "domain", "range", "cardinality", "required_on",
             "prov_superproperty", "description"]]
    for r in m.relationships:
        rels.append([r.key, r.curie, r.label, r.inverse_label, "|".join(r.domain), "|".join(r.range),
                     "many" if r.many else "one", "|".join(r.required), r.prov or "", r.description])
    return {"aow-classes.csv": csv_text(classes), "aow-attributes.csv": csv_text(attrs),
            "aow-relationships.csv": csv_text(rels)}


# ------------------------------------------------ Whitepaper reference blocks
def md_escape(s: str) -> str:
    return s.replace("|", "\\|")


def md_type(a) -> str:
    if a.is_ref:
        return "→ " + " / ".join(a.range)
    if a.type == "enum":
        return "one of " + ", ".join(f"`{v}`" for v in a.values)
    if a.min is not None or a.max is not None:
        return f"{a.type} ({a.min}–{a.max})"
    return a.type


def md_entities(m: Model, section: str) -> str:
    out = []
    n = 0
    for layer in m.layers:
        for e in m.entities_in(layer["id"]):
            n += 1
            head = f"### {section}.{n} {e.label}"
            out.append(head)
            bits = [f"Layer: {layer['name']}", f"since {e.since[:3]}", f"`{e.curie}`"]
            if e.subclass_of:
                bits.insert(1, f"a kind of {m.by_id[e.subclass_of].label}")
            if e.abstract:
                bits.insert(1, "abstract")
            out.append("*" + " · ".join(bits) + "*\n")
            out.append(f"**Definition.** {e.definition}\n")
            out.append(f"**Purpose.** {e.purpose}\n")
            attrs = list(e.attributes) + [a for a in m.common if a.key in e.required_common]
            if attrs:
                out.append("| Attribute | Type | Required | Description |")
                out.append("|---|---|---|---|")
                for a in attrs:
                    req = "yes" if (a.required or a.key in e.required_common) else ""
                    out.append(f"| `{a.key}` | {md_escape(md_type(a))} | {req} | {md_escape(a.description)} |")
                out.append("")
            rels = [r for r in m.relationships if e.id in r.domain]
            if rels:
                out.append("**Relationships.**\n")
                for r in rels:
                    req = " *(required)*" if e.id in r.required else ""
                    many = " (one or more)" if r.many else ""
                    out.append(f"- `{r.key}` → {' / '.join(m.by_id[c].label for c in r.range)}{many}{req}")
                out.append("")
            if e.notes:
                out.append("**Notes.**\n")
                for note in e.notes:
                    out.append(f"- {note}")
                out.append("")
    return "\n".join(out).rstrip() + "\n"


def md_relationships(m: Model) -> str:
    out = ["| Relationship | From | To | Read backward as | Required on |", "|---|---|---|---|---|"]
    for r in m.relationships:
        frm = ", ".join(m.by_id[c].label for c in r.domain)
        to = ", ".join(m.by_id[c].label for c in r.range)
        out.append(f"| `{r.key}` | {frm} | {to}{' (many)' if r.many else ''} | {r.inverse_label} | "
                   f"{', '.join(m.by_id[c].label for c in r.required)} |")
    return "\n".join(out) + "\n"


def md_matrix(m: Model) -> str:
    out = ["| Entity | Points to | Pointed to by |", "|---|---|---|"]
    for e in m.entities:
        if e.abstract:
            continue
        to = sorted({m.by_id[c].label for r in m.outgoing(e.id) for c in r.range})
        frm = sorted({m.by_id[c].label for r in m.incoming(e.id) for c in r.domain})
        out.append(f"| {e.label} | {', '.join(to) or '—'} | {', '.join(frm) or '—'} |")
    return "\n".join(out) + "\n"


def md_assurance(m: Model) -> str:
    out = ["| Level | Name | People | Agents | Default confidence floor | Suited to |", "|---|---|---|---|---|---|"]
    for al in m.assurance_levels:
        floor = "—" if al["default_confidence_floor"] is None else f"{al['default_confidence_floor']:.2f}"
        out.append(f"| **{al['id']}** | {al['label']} | {al['human_role']} | {al['agent_role']} | {floor} | {al['risk_class']} |")
    return "\n".join(out) + "\n"


def md_glossary(m: Model) -> str:
    out = ["| Term | Definition |", "|---|---|"]
    rows = [(e.label, e.definition) for e in m.entities]
    rows += [("Assurance Level scale", "The five levels of permitted autonomy, AL0 (Manual) to AL4 (Autonomous).")]
    rows += [("Provenance facet", "The attributes every entity may carry to record who created it, when, from what, "
                                  "and which version it revises, expressed with W3C PROV-O.")]
    rows += [("Effective Assurance Level", "The lowest of the levels set on the Intent, Task, and Skill, and the "
                                           "performing Agent's autonomy_level.")]
    for term, definition in sorted(rows):
        out.append(f"| {term} | {md_escape(definition)} |")
    return "\n".join(out) + "\n"


GEN = re.compile(r"(<!-- aow:generated (\S+)(?: section=(\S+))? -->\n)(.*?)(<!-- /aow:generated -->)", re.S)


def regenerate_whitepaper(m: Model, path: Path) -> None:
    if not path.exists():
        return
    renderers = {
        "entities": lambda sec: md_entities(m, sec),
        "relationships": lambda sec: md_relationships(m),
        "matrix": lambda sec: md_matrix(m),
        "assurance-levels": lambda sec: md_assurance(m),
        "glossary": lambda sec: md_glossary(m),
    }

    def sub(match):
        name, sec = match.group(2), match.group(3)
        return match.group(1) + "\n" + renderers[name](sec) + "\n" + match.group(5)

    text = path.read_text(encoding="utf-8")
    path.write_text(GEN.sub(sub, text), encoding="utf-8")


# ---------------------------------------------------------------------- main
def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def dumps(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def owl_jsonld(ttl: str) -> str:
    """Serialize the ontology as JSON-LD, with a stable ordering."""
    from rdflib import Graph

    g = Graph().parse(data=ttl, format="turtle")
    data = json.loads(g.serialize(format="json-ld"))

    def norm(x):
        if isinstance(x, dict):
            return {k: norm(v) for k, v in sorted(x.items())}
        if isinstance(x, list):
            return sorted((norm(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True))
        return x

    return dumps(norm(data))


def main() -> None:
    m = Model()
    ttl = build_owl(m)
    files = {
        "ontology/aow.ttl": ttl,
        "ontology/aow.jsonld": owl_jsonld(ttl),
        "ontology/context.jsonld": dumps(build_context(m)),
        "ontology/shapes.ttl": build_shapes(m),
    }
    for name, schema in build_schemas(m).items():
        files[f"schemas/{name}"] = dumps(schema)
    for name, text in build_csvs(m).items():
        files[f"docs/downloads/{name}"] = text

    for rel, text in files.items():
        write(ROOT / rel, text)

    # GitHub Pages serves docs/. Mirror the machine-readable files there, at
    # the paths the w3id.org redirects point to, plus a frozen copy per version.
    version = m.meta["version"]
    for rel in ["ontology/aow.ttl", "ontology/aow.jsonld", "ontology/context.jsonld", "ontology/shapes.ttl"]:
        name = Path(rel).name
        write(ROOT / "docs/ontology" / name, files[rel])
        write(ROOT / "docs/ontology" / version / name, files[rel])
    shutil.rmtree(ROOT / "docs/schemas", ignore_errors=True)
    shutil.copytree(ROOT / "schemas", ROOT / "docs/schemas")

    regenerate_whitepaper(m, ROOT / "whitepaper.md")
    print(f"built {len(files)} files from aow.yaml ({len(m.entities)} classes, "
          f"{len(m.relationships)} relationships, {len(m.attribute_index())} attributes)")


if __name__ == "__main__":
    main()
