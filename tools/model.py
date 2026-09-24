"""Load aow.yaml and expose it in the shapes the generators need.

Everything the build produces starts here, so naming rules (snake_case keys
in JSON, lowerCamelCase properties in RDF, kebab-case slugs on the site)
live in one place.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

PREFIXES = {
    "aow": "https://w3id.org/aow#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dcterms": "http://purl.org/dc/terms/",
    "vann": "http://purl.org/vocab/vann/",
    "prov": "http://www.w3.org/ns/prov#",
    "schema": "https://schema.org/",
    "sh": "http://www.w3.org/ns/shacl#",
    "sosa": "http://www.w3.org/ns/sosa/",
    "odrl": "http://www.w3.org/ns/odrl/2/",
    "org": "http://www.w3.org/ns/org#",
}

# Common attributes map onto well-known properties instead of new AOW ones.
COMMON_PROPERTY = {
    "label": "rdfs:label",
    "description": "dcterms:description",
    "version": "schema:version",
    "created_at": "prov:generatedAtTime",
    "created_by": "prov:wasAttributedTo",
    "revision_of": "prov:wasRevisionOf",
}

XSD_FOR = {
    "string": "xsd:string",
    "text": "xsd:string",
    "enum": "xsd:string",
    "string-list": "xsd:string",
    "number": "xsd:double",
    "integer": "xsd:integer",
    "boolean": "xsd:boolean",
    "datetime": "xsd:dateTime",
    "uri": "xsd:anyURI",
    "uri-list": "xsd:anyURI",
    "json": "rdf:JSON",
}

LIST_TYPES = {"string-list", "uri-list"}


def camel(key: str) -> str:
    head, *rest = key.split("_")
    return head + "".join(p[:1].upper() + p[1:] for p in rest)


def slug(class_id: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", class_id).lower()


@dataclass
class Attribute:
    key: str
    type: str
    description: str
    required: bool = False
    values: list | None = None
    range: list | None = None
    min: float | None = None
    max: float | None = None
    prov: str | None = None

    @property
    def curie(self) -> str:
        return COMMON_PROPERTY.get(self.key) or f"aow:{camel(self.key)}"

    @property
    def is_ref(self) -> bool:
        return self.type == "ref"

    @property
    def many(self) -> bool:
        return self.type in LIST_TYPES


@dataclass
class Relationship:
    key: str
    label: str
    inverse_label: str
    domain: list
    range: list
    description: str
    required: list = field(default_factory=list)
    many: bool = False
    prov: str | None = None

    @property
    def curie(self) -> str:
        return f"aow:{camel(self.key)}"


@dataclass
class Entity:
    id: str
    label: str
    layer: str
    since: str
    definition: str
    purpose: str
    attributes: list
    notes: list = field(default_factory=list)
    alignments: list = field(default_factory=list)
    subclass_of: str | None = None
    abstract: bool = False
    required_common: list = field(default_factory=list)

    @property
    def curie(self) -> str:
        return f"aow:{self.id}"

    @property
    def slug(self) -> str:
        return slug(self.id)


class Model:
    def __init__(self, path: Path = ROOT / "aow.yaml"):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.raw = raw
        self.meta = raw["ontology"]
        self.layers = sorted(raw["layers"], key=lambda l: l["order"])
        self.common = [Attribute(**a) for a in raw["common_attributes"]]
        self.entities = []
        for e in raw["entities"]:
            e = dict(e)
            e["attributes"] = [Attribute(**a) for a in e.get("attributes") or []]
            self.entities.append(Entity(**e))
        self.by_id = {e.id: e for e in self.entities}
        self.relationships = [Relationship(**r) for r in raw["relationships"]]
        self.disjoint = raw.get("disjoint", [])
        self.assurance_levels = raw["assurance_levels"]
        self._check()

    # -- structure -----------------------------------------------------------
    def ancestors(self, cid: str) -> list:
        out, cur = [], self.by_id[cid].subclass_of
        while cur:
            out.append(cur)
            cur = self.by_id[cur].subclass_of
        return out

    def descendants(self, cid: str) -> list:
        return [e.id for e in self.entities if cid in self.ancestors(e.id)]

    def lineage(self, cid: str) -> list:
        """The class itself plus its ancestors, nearest first."""
        return [cid] + self.ancestors(cid)

    def own_attributes(self, cid: str) -> list:
        return self.by_id[cid].attributes

    def all_attributes(self, cid: str) -> list:
        """Attributes a JSON document of this class may carry, inherited included."""
        out = list(self.common)
        for c in reversed(self.lineage(cid)):
            out += self.by_id[c].attributes
        return out

    def outgoing(self, cid: str, inherited: bool = True) -> list:
        classes = self.lineage(cid) if inherited else [cid]
        return [r for r in self.relationships if set(r.domain) & set(classes)]

    def incoming(self, cid: str) -> list:
        classes = self.lineage(cid)
        return [r for r in self.relationships if set(r.range) & set(classes)]

    def entities_in(self, layer: str) -> list:
        return [e for e in self.entities if e.layer == layer]

    def attribute_index(self) -> dict:
        """key -> (Attribute, [classes that declare it])."""
        idx: dict = {}
        for e in self.entities:
            for a in e.attributes:
                if a.key in idx:
                    prev, owners = idx[a.key]
                    if XSD_FOR.get(prev.type, prev.type) != XSD_FOR.get(a.type, a.type):
                        raise ValueError(f"attribute {a.key} has conflicting types")
                    owners.append(e.id)
                else:
                    idx[a.key] = (a, [e.id])
        return idx

    def _check(self) -> None:
        ids = set(self.by_id)
        for e in self.entities:
            if e.subclass_of and e.subclass_of not in ids:
                raise ValueError(f"{e.id}: unknown parent {e.subclass_of}")
            if e.layer not in {l["id"] for l in self.layers}:
                raise ValueError(f"{e.id}: unknown layer {e.layer}")
        for r in self.relationships:
            for c in r.domain + r.range + r.required:
                if c not in ids:
                    raise ValueError(f"{r.key}: unknown class {c}")
        keys = [r.key for r in self.relationships] + list(self.attribute_index())
        clash = {k for k in keys if keys.count(k) > 1}
        if clash:
            raise ValueError(f"keys used for both an attribute and a relationship: {clash}")
        self.attribute_index()


def expand(curie: str) -> str:
    prefix, local = curie.split(":", 1)
    return PREFIXES[prefix] + local
