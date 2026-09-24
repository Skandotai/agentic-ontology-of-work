"""Check that the ontology, the shapes, the schemas, and the examples agree.

    python tools/validate.py

For every example in examples/:
  1. validate the JSON document against schemas/aow.schema.json
  2. load it as RDF through the AOW JSON-LD context
  3. validate the RDF against ontology/shapes.ttl, with the ontology mixed
     in so that subclasses count (an Agent is an Actor). No RDFS inference:
     it would infer types from property ranges and make range checks vacuous.
  4. run queries/untraced-results.rq and queries/oversight-gaps.rq, which
     must both come back empty

Every fixture in tests/invalid/ must fail at the stage named for it below,
which proves the checks are doing something.

Exits non-zero on any failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from pyshacl import validate as shacl_validate
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, SKOS, OWL

ROOT = Path(__file__).resolve().parent.parent
AOW = Namespace("https://w3id.org/aow#")
CONTEXT_URL = "https://w3id.org/aow/context.jsonld"

EXPECTED_FAILURES = {
    "unknown-key.jsonld": "schema",
    "result-without-action.jsonld": "shacl",
    "agent-cannot-own-role-as-skill.jsonld": "shacl",
    "confidence-out-of-range.jsonld": "schema",
    "unapproved-low-confidence.jsonld": "oversight-gaps",
    "untraceable-result.jsonld": "untraced-results",
}

GATE_QUERIES = ["untraced-results", "oversight-gaps"]


def load_ontology() -> Graph:
    return Graph().parse(ROOT / "ontology/aow.ttl", format="turtle")


def check_ontology(g: Graph) -> list:
    problems = []
    for cls in g.subjects(RDF.type, OWL.Class):
        if not str(cls).startswith(str(AOW)):
            continue
        if not g.value(cls, RDFS.label):
            problems.append(f"{cls} has no rdfs:label")
        if not g.value(cls, SKOS.definition):
            problems.append(f"{cls} has no skos:definition")
    for kind in (OWL.ObjectProperty, OWL.DatatypeProperty):
        for p in g.subjects(RDF.type, kind):
            if not g.value(p, RDFS.comment):
                problems.append(f"{p} has no rdfs:comment")
    return problems


def to_rdf(doc: dict, context: dict) -> Graph:
    """Parse an AOW JSON-LD document, resolving the AOW context locally."""
    doc = json.loads(json.dumps(doc))
    ctx = doc.get("@context")
    if ctx == CONTEXT_URL:
        doc["@context"] = context["@context"]
    elif isinstance(ctx, list):
        doc["@context"] = [context["@context"] if c == CONTEXT_URL else c for c in ctx]
    return Graph().parse(data=json.dumps(doc), format="json-ld")


def run_query(name: str, data: Graph, ontology: Graph) -> list:
    merged = data + ontology
    query = (ROOT / "queries" / f"{name}.rq").read_text(encoding="utf-8")
    return list(merged.query(query))


def check_document(path: Path, schema_validator, context: dict, shapes: Graph, ontology: Graph) -> tuple:
    """Return (stage, messages) for the first stage that fails, or (None, [])."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    errors = sorted(schema_validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
    if errors:
        return "schema", [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}" for e in errors[:10]]
    data = to_rdf(doc, context)
    conforms, _, text = shacl_validate(data, shacl_graph=shapes, ont_graph=ontology, inference="none",
                                       advanced=True, allow_warnings=True)
    if not conforms:
        return "shacl", [line for line in text.splitlines() if line.strip()][:30]
    for name in GATE_QUERIES:
        rows = run_query(name, data, ontology)
        if rows:
            return name, [" ".join(str(v) for v in row if v is not None) for row in rows]
    return None, []


def main() -> int:
    failures = 0
    ontology = load_ontology()
    problems = check_ontology(ontology)
    for p in problems:
        print(f"ontology: {p}")
    failures += len(problems)

    import csv
    for row in csv.DictReader((ROOT / "crosswalks/soa-to-agentic-terms.csv").open(encoding="utf-8")):
        iri = row["aow_iri"]
        if iri and (AOW[iri.split(":", 1)[1]], None, None) not in ontology:
            failures += 1
            print(f"crosswalk: {iri} (for {row['agentic_term']}) is not defined in the ontology")

    shapes = Graph().parse(ROOT / "ontology/shapes.ttl", format="turtle")
    context = json.loads((ROOT / "ontology/context.jsonld").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas/aow.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    examples = sorted((ROOT / "examples").glob("**/*.jsonld"))
    for path in examples:
        stage, messages = check_document(path, validator, context, shapes, ontology)
        rel = path.relative_to(ROOT)
        if stage:
            failures += 1
            print(f"FAIL {rel} at {stage}")
            for m in messages:
                print(f"     {m}")
        else:
            print(f"ok   {rel}")

    for path in sorted((ROOT / "tests/invalid").glob("*.jsonld")):
        expected = EXPECTED_FAILURES.get(path.name)
        stage, messages = check_document(path, validator, context, shapes, ontology)
        rel = path.relative_to(ROOT)
        if expected is None:
            failures += 1
            print(f"FAIL {rel}: no expected failure stage registered in tools/validate.py")
        elif stage != expected:
            failures += 1
            print(f"FAIL {rel}: expected to fail at {expected}, got {stage or 'no failure'}")
            for m in messages:
                print(f"     {m}")
        else:
            print(f"ok   {rel} (fails at {stage}, as intended)")

    missing = set(EXPECTED_FAILURES) - {p.name for p in (ROOT / "tests/invalid").glob("*.jsonld")}
    for name in sorted(missing):
        failures += 1
        print(f"FAIL tests/invalid/{name} is registered but missing")

    print(f"\n{len(examples)} examples, {failures} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
