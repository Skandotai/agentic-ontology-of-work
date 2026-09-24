# Agentic Ontology of Work (AOW)

**Author:** Manish Garg, [Skan.ai](https://www.skan.ai) · **Version:** 2.0.0 · **License:** [CC-BY 4.0](LICENSE) (prose), [Apache 2.0](LICENSE-APACHE) (ontology, schemas, code)

[![validate](https://github.com/Skandotai/agentic-ontology-of-work/actions/workflows/validate.yml/badge.svg)](https://github.com/Skandotai/agentic-ontology-of-work/actions/workflows/validate.yml)

[Website](https://skandotai.github.io/agentic-ontology-of-work/) · [Whitepaper](whitepaper.md) · [Term reference](https://skandotai.github.io/agentic-ontology-of-work/ontology/) · Whitepaper preprint: https://doi.org/10.5281/zenodo.22945754

## Overview

The Agentic Ontology of Work (AOW) is a platform-agnostic semantic model for enterprise work performed by AI agents, people, and systems. It defines the entities involved in that work, their attributes, and the relationships between them, in a form that software can validate.

AOW is intended to give enterprises, vendors, and standards bodies a common basis for describing agentic systems, integrating them, and governing them.

## Scope

AOW 2.0 defines 25 classes and 33 relationships, organized in four layers:

| Layer | Purpose | Classes |
|---|---|---|
| Perception | Records the work items in progress and the signals and observations about them | Work Item, Signal, Observation |
| Cognition | Defines goals, context, constraints, and plans | Objective, Intent, Context, Policy, Plan |
| Execution | Records who performed the work and what it changed | Task, Actor, Agent, Human Actor, Orchestrator, Role, Skill, Action, Result |
| Assurance | Governs autonomy, measures outcomes, and records feedback | Confidence, Assurance Level, Guardian, Outcome, Feedback, Memory, Operational Memory, Knowledge Base |

The model links each business Objective to the Intents, Plans, and Tasks derived from it, the Actions taken to complete them, and the Results and Outcomes produced. It also defines five Assurance Levels, from AL0 (manual) to AL4 (autonomous), which set how much autonomy an agent may exercise and what human oversight is required at each level.

## Formats

| File | Format | Use |
|---|---|---|
| [`ontology/aow.ttl`](ontology/aow.ttl) | OWL 2 (Turtle) | Ontology editors, reasoners, knowledge graphs |
| [`ontology/aow.jsonld`](ontology/aow.jsonld) | OWL 2 (JSON-LD) | As above, in JSON-LD |
| [`ontology/context.jsonld`](ontology/context.jsonld) | JSON-LD context | Reading AOW JSON documents as RDF |
| [`ontology/shapes.ttl`](ontology/shapes.ttl) | SHACL | Validating AOW data in RDF |
| [`schemas/`](schemas/) | JSON Schema 2020-12 | Validating AOW data in JSON |
| [`queries/`](queries/) | SPARQL | Tracing results to objectives; detecting missing human oversight |
| [`docs/downloads/`](docs/downloads/) | CSV, PDF | The model as spreadsheets; the whitepaper, a preprint edition, and a reference card |

All of these files are generated from [`aow.yaml`](aow.yaml), which is the canonical source.

## Out of scope

- **Implementation.** AOW does not assume any vendor, model, or agent framework.
- **Communication protocols.** Protocols such as MCP and A2A transport work between agents and tools. AOW describes the work itself. See [whitepaper section 12.6](whitepaper.md#126-agent-protocols-mcp-and-a2a).
- **Policy languages.** A Policy may contain rules written in ODRL, Rego, Cedar, DMN, or plain text.
- Known limitations are listed in [whitepaper section 15](whitepaper.md#15-limitations-and-open-questions).

## Example

An Intent in AOW JSON. The same document is valid against [`schemas/intent.schema.json`](schemas/intent.schema.json) and can be read as RDF through the JSON-LD context.

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

[`examples/claims-processing.jsonld`](examples/claims-processing.jsonld) models two insurance claims end to end: one decided by an agent, and one escalated to a claims adjuster because the agent's confidence was below the required threshold. [`examples/industry/`](examples/industry/) contains examples for insurance, banking, healthcare, the public sector, and retail.

## Repository contents

```
agentic-ontology-of-work/
├── aow.yaml                  canonical source for all generated files
├── whitepaper.md             whitepaper, version 2.0
├── context.md                summary of the rationale
├── ontology/                 OWL ontology, JSON-LD context, SHACL shapes
├── schemas/                  JSON Schemas, one per class, plus a document schema
├── queries/                  SPARQL queries
├── examples/                 worked examples, all validated
├── crosswalks/               mapping from the SOA-to-Agentic terminology to AOW
├── tests/invalid/            documents that must fail validation
├── tools/                    build.py, site.py, validate.py, make_assets.py, make_preprint.py
├── w3id/                     redirect rules for the w3id.org/aow identifiers
└── docs/                     website, downloads, and the version 1.0 paper
```

## Validation

```sh
pip install -r requirements.txt
python tools/validate.py
```

The validator checks every example against the JSON Schemas and SHACL shapes, confirms that every Result can be traced to an Objective, and confirms that no agent Action lacks the human oversight its Assurance Level requires. It also confirms that each document in `tests/invalid/` fails at the expected check. The same checks run on every push.

To validate your own RDF data with a standard tool:

```sh
pyshacl -s ontology/shapes.ttl -e ontology/aow.ttl -i none your-data.ttl
```

To change the ontology, edit `aow.yaml` and run:

```sh
python tools/build.py && python tools/site.py && python tools/validate.py
```

## Related project

The SOA-to-Agentic AI Terminology Mapping maps 28 Service-Oriented Architecture terms to agentic equivalents.

- Repository: https://github.com/Skandotai/soa-to-agentic-terms
- Website: https://skandotai.github.io/soa-to-agentic-terms/
- Crosswalk from the 28 agentic terms to AOW: [`crosswalks/soa-to-agentic-terms.csv`](crosswalks/soa-to-agentic-terms.csv)

## Related standards

AOW reuses or aligns with existing standards where they apply, including W3C PROV-O, the W3C Organization Ontology, SOSA, ODRL, and schema.org, and the A2A task lifecycle. Whitepaper section 12 describes its relationship to BPMN, DMN, multi-agent systems research, process mining standards (XES, OCEL), MCP, OpenTelemetry, the NIST AI RMF, ISO/IEC 42001, and the EU AI Act.

## Versions

- **2.0.0** (September 2026). Adds eight classes, defines Action and the Assurance Level scale, adopts PROV-O for provenance, and publishes the ontology in machine-readable formats. See [CHANGELOG.md](CHANGELOG.md).
- **1.0** (January 2026). Original paper, [archived as published](docs/downloads/agentic-ontology-of-work-v1.0.pdf).

## Contributing

Issues and pull requests are welcome, particularly reports of real-world work that AOW cannot describe. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Prose and documentation are licensed under [CC-BY 4.0](LICENSE). The ontology, shapes, schemas, queries, examples, and code are licensed under [Apache 2.0](LICENSE-APACHE). Both licenses permit copying, adaptation, and commercial use with attribution to the author and Skan.ai and an indication of any changes.

## Citation

To cite the whitepaper, use the preprint: Garg, M. (2026). *Agentic Ontology of Work (AOW), Version 2.0: A semantic model for enterprise work performed by AI agents, people, and systems*. Zenodo. https://doi.org/10.5281/zenodo.22945754

To cite the ontology and data, use GitHub's "Cite this repository" option, which reads [`CITATION.cff`](CITATION.cff), or cite as:

> Garg, M. (2026). *Agentic Ontology of Work (AOW)*, version 2.0.0. Skan.ai. https://github.com/Skandotai/agentic-ontology-of-work
