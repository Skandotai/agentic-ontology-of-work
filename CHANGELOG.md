# Changelog

All notable changes to the Agentic Ontology of Work. Versions follow [Semantic Versioning](https://semver.org/): a major version may change the meaning of an existing term; a minor version adds terms; a patch version fixes documentation or tooling without changing any term.

## 2.0.0 (2026-09-24)

First open-source release.

### Added
- Classes: `WorkItem`, `Signal`, `Observation`, `Plan`, `Task`, `Actor`, `HumanActor`, `Role`.
- The Assurance Level scale: named individuals `aow:AL0` (Manual) to `aow:AL4` (Autonomous), with default confidence floors, and the effective-level rule.
- `Skill.side_effects` (`none`, `reversible`, `irreversible`).
- `approved_by`, for recording human confirmation of an Action, Plan, or Result.
- Machine-readable releases: OWL 2 (Turtle and JSON-LD), JSON-LD context, SHACL shapes, JSON Schema, SPARQL queries.
- A worked claims-processing example, five industry examples, and negative test fixtures, all checked in CI.
- A crosswalk from the SOA-to-Agentic AI Terminology Mapping to AOW.
- Principle 7, Actor neutrality.

### Changed
- `Action` is defined, and produces `Result`. (1.0 said both "Skill produces Result" and "Result is the effect of an Action.")
- Provenance and Versioning are a facet of every entity, expressed with W3C PROV-O, rather than entities of their own.
- `Orchestrator` and `Guardian` are kinds of `Actor`.
- `Memory` is abstract, with `OperationalMemory` and `KnowledgeBase` as subclasses.
- Every entity is identified by `id` and typed by `type`, replacing `objective_id`, `intent_id`, and so on.
- On `Agent`: `skills` becomes `has_skill`, `memory_link` becomes `writes_to`, `role` becomes `fills_role`; `assurance_level_required` moves to `Intent`, `Task`, and `Skill` as `requires_assurance`; `autonomy_level` now points to an Assurance Level.
- On `Result`: `confidence_measure` becomes `has_confidence`.
- On `Observation`: the observed value is `observed_value`.
- Section 9 ("How AOW relates to existing frameworks") is expanded to cover PROV-O and other W3C standards, process mining, MCP, A2A, OpenTelemetry, NIST AI RMF, ISO/IEC 42001, and the EU AI Act.
- Validation criteria are each paired with a check.
- The closing claim is restated as "a candidate reference model" rather than "a foundational standard for the next decade."

### Fixed
- Section numbering in the design principles and the four-layer stack.
- A reference to "AOW v3" in the validation criteria.
- Example schemas that had lost their YAML indentation.
- A missing word in section 1.1.

## 1.0 (2026-01)

The original paper: the four-layer model, fifteen canonical entities, the lifecycle, metadata schema sketches, the claims example, five industry examples, and validation criteria. [Kept as published](docs/downloads/agentic-ontology-of-work-v1.0.pdf).
