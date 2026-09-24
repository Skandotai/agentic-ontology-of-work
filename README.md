# Agentic Ontology of Work (AOW)

**By Manish Garg, [Skan.ai](https://www.skan.ai)** · Version 2.0.0 · Prose licensed [CC-BY 4.0](LICENSE) · Ontology, schemas, and code licensed [Apache 2.0](LICENSE-APACHE)

[![validate](https://github.com/Skandotai/agentic-ontology-of-work/actions/workflows/validate.yml/badge.svg)](https://github.com/Skandotai/agentic-ontology-of-work/actions/workflows/validate.yml)

**[Read it as a site →](https://skandotai.github.io/agentic-ontology-of-work/)** · **[Read the whitepaper →](whitepaper.md)**

## Why this exists

Enterprises are putting agents to work faster than they can agree on how to describe that work. "Agent," "task," "workflow," and "orchestration" mean different things to different vendors and teams. The result is integrations that break at the seams, governance policies that cannot be applied consistently, and audit trails that stop wherever one system hands off to the next.

A glossary doesn't fix that. What's needed is an ontology: a precise account of the kinds of things involved in agentic work, what each one carries, and how they connect, specified tightly enough that software can check a description against it.

## What this is

A platform-agnostic semantic model of intelligent, autonomous, and governed work: **25 classes and 33 relationships across four layers.**

| Layer | Question | Classes |
|---|---|---|
| **Perception** | What exists, and what is happening? | Work Item, Signal, Observation |
| **Cognition** | What should happen, and within what limits? | Objective, Intent, Context, Policy, Plan |
| **Execution** | Who does the work, and what did it change? | Task, Actor, Agent, Human Actor, Orchestrator, Role, Skill, Action, Result |
| **Assurance** | Was it safe, did it work, and what did we learn? | Confidence, Assurance Level, Guardian, Outcome, Feedback, Memory, Operational Memory, Knowledge Base |

It follows work from the business **Objective** it serves, through the **Intents**, **Plans**, and **Tasks** derived from it, to the **Actions** that **Actors** (agents and people alike) take with their **Skills**, the **Results** those Actions produce, and the **Outcomes** they add up to. Around that path sit the things that make autonomy safe to grant: **Policy**, **Confidence**, a five-level **Assurance Level** scale from AL0 (Manual) to AL4 (Autonomous), an independent **Guardian**, and **Feedback** into **Memory**.

It's published in the formats people actually use:

- **OWL** ([`ontology/aow.ttl`](ontology/aow.ttl)) for knowledge graphs, reasoners, and ontology editors
- **JSON-LD** ([`ontology/context.jsonld`](ontology/context.jsonld)), so plain AOW JSON is also RDF, with no changes
- **SHACL** ([`ontology/shapes.ttl`](ontology/shapes.ttl)) to check a graph of AOW data is well formed
- **JSON Schema** ([`schemas/`](schemas/)) to check a JSON document, for teams that never touch RDF
- **SPARQL** ([`queries/`](queries/)) to reconstruct why any Result exists, and to find Agents that acted beyond the oversight their Assurance Level requires

## What this isn't

- **Not a product, and not tied to one.** Nothing in it assumes a particular vendor, model, or agent framework.
- **Not a protocol.** MCP and A2A move work between agents and tools; AOW describes the work they move ([whitepaper, section 12.6](whitepaper.md#126-agent-protocols-mcp-and-a2a)).
- **Not a policy language.** A Policy may hold rules in ODRL, Rego, Cedar, DMN, or plain text.
- **Not finished.** [Section 15 of the whitepaper](whitepaper.md#15-limitations-and-open-questions) lists what it doesn't yet handle.

## A taste

An Intent, in AOW JSON. The same document is valid JSON (against [`schemas/intent.schema.json`](schemas/intent.schema.json)) and valid RDF (through the context):

```json
{
  "@context": ["https://w3id.org/aow/context.jsonld", { "@base": "https://example.org/claims/" }],
  "@graph": [
    {
      "id": "intent-eligibility-2026",
      "type": "Intent",
      "goal_statement": "Determine eligibility for incoming disability claims automatically wherever policy allows.",
      "serves_objective": "obj-claims-cycle-time",
      "constrained_by": ["policy-auto-approval"],
      "requires_assurance": "aow:AL2"
    }
  ]
}
```

The [worked example](examples/claims-processing.jsonld) follows two disability claims through every layer: one an agent decides at 0.93 confidence, one it escalates at 0.81 for an adjuster to decide. [`examples/industry/`](examples/industry/) covers banking, healthcare, the public sector, and retail.

## What's here

```
agentic-ontology-of-work/
├── aow.yaml                  the canonical source; everything else is generated from it
├── whitepaper.md             the full paper, version 2.0
├── context.md                the short version: why this ontology exists
├── ontology/
│   ├── aow.ttl                 the ontology, OWL 2 (Turtle)
│   ├── aow.jsonld              the ontology, OWL 2 (JSON-LD)
│   ├── context.jsonld          JSON-LD context for AOW data
│   └── shapes.ttl              SHACL shapes for AOW data
├── schemas/                  JSON Schema, one per class, plus a document bundle
├── queries/                  SPARQL: explain a Result, find untraced Results, find oversight gaps
├── examples/                 the worked example and five industry examples, all valid
├── crosswalks/               the SOA-to-Agentic terms mapped to AOW classes
├── tests/invalid/            documents that must fail validation, to prove the checks work
├── tools/                    build.py, site.py, validate.py, make_assets.py
├── w3id/                     the permanent-identifier redirect rules for w3id.org/aow
└── docs/                     the published site, including downloads and the version 1.0 PDF
```

`aow.yaml` is the single source of truth. The OWL, the context, the shapes, the schemas, the CSVs, the reference sections of the whitepaper, and the site are all generated from it, and CI fails if any of them is out of date. If they ever disagree, `aow.yaml` is right.

## Using it

Validate your own AOW data:

```sh
pip install -r requirements.txt
python tools/validate.py          # checks every file in examples/ and tests/invalid/
```

Or use any standard tool. With [pySHACL](https://github.com/RDFLib/pySHACL):

```sh
pyshacl -s ontology/shapes.ttl -e ontology/aow.ttl -i none your-data.ttl
```

To change the ontology, edit `aow.yaml`, then:

```sh
python tools/build.py && python tools/site.py && python tools/validate.py
```

## Relationship to the SOA-to-Agentic terminology mapping

This is the companion to the [SOA-to-Agentic AI Terminology Mapping](https://github.com/Skandotai/soa-to-agentic-terms), which translates twenty-eight Service-Oriented Architecture terms into agentic equivalents. The mapping is the vocabulary; AOW is the structure. [`crosswalks/soa-to-agentic-terms.csv`](crosswalks/soa-to-agentic-terms.csv) maps each agentic term to the AOW class or property that formalizes it.

## Standing on shoulders

AOW reuses established work wherever it can instead of reinventing it: W3C [PROV-O](https://www.w3.org/TR/prov-o/) for provenance, the W3C [Organization Ontology](https://www.w3.org/TR/vocab-org/) for roles, [SOSA](https://www.w3.org/TR/vocab-ssn/) for observations, [ODRL](https://www.w3.org/TR/odrl-model/) for policy, the [A2A](https://a2a-protocol.org) task lifecycle for Task states, and the levels-of-automation literature for the Assurance Level scale. Section 12 of the whitepaper says where each came from and where AOW differs, including from BPMN, DMN, multi-agent systems research, process mining (XES, OCEL), MCP, OpenTelemetry, the NIST AI RMF, ISO/IEC 42001, and the EU AI Act.

## Version history

- **2.0.0** (September 2026): adds Work Item, Signal, Observation, Plan, Task, Actor, Human Actor, and Role; defines Action and the Assurance Level scale; makes provenance a PROV-O facet; ships OWL, JSON-LD, SHACL, JSON Schema, SPARQL, and validated examples. See [CHANGELOG.md](CHANGELOG.md).
- **1.0** (January 2026): the original paper, [kept as published](docs/downloads/agentic-ontology-of-work-v1.0.pdf).

## Contributing

This is offered as a starting point, not a finished standard. If a definition is wrong, a relationship is missing, or your domain doesn't fit, [open an issue](https://github.com/Skandotai/agentic-ontology-of-work/issues). A concrete case ("here's a piece of work AOW can't describe") is the most useful kind. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Prose and documentation: [CC-BY 4.0](LICENSE). The ontology, shapes, schemas, queries, examples, and code: [Apache 2.0](LICENSE-APACHE).

In plain terms, both permit the same thing: copy it, adapt it, build on it, use it commercially. Just credit the author and Skan.ai, and say if you changed it. You don't need to ask.

## Citing this work

Use GitHub's "Cite this repository" button, which reads [`CITATION.cff`](CITATION.cff), or:

> Garg, M. (2026). *Agentic Ontology of Work (AOW)*, version 2.0.0. Skan.ai. https://github.com/Skandotai/agentic-ontology-of-work
