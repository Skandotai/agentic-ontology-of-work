# Contributing

AOW is offered as a starting point for a shared model of agentic work, and it gets better through disagreement. Thank you for taking the time.

## The most useful contributions

1. **A case AOW can't describe.** Real work that doesn't fit is worth more than any amount of abstract argument. Describe the work, show what you tried, and say where it broke.
2. **A definition that's wrong or ambiguous.** Quote it and say how two reasonable people could read it differently.
3. **A mapping to another standard.** If you know a standard, protocol, or product vocabulary well, a crosswalk to AOW helps everyone who uses both.
4. **An example from your industry**, as a valid document in `examples/`.

Open an [issue](https://github.com/Skandotai/agentic-ontology-of-work/issues) to discuss anything that changes the ontology before sending a pull request for it. Typos and broken links can go straight to a pull request.

## How changes are made

`aow.yaml` is the only file you should edit to change the ontology. Everything else is generated from it:

```sh
pip install -r requirements.txt
python tools/build.py      # regenerates ontology/, schemas/, CSVs, and the whitepaper's reference sections
python tools/site.py       # regenerates the site in docs/
python tools/validate.py   # checks the ontology, shapes, schemas, examples, and fixtures
```

CI runs the same three commands and fails if a generated file is out of date or any check fails.

Prose in `whitepaper.md` outside the `<!-- aow:generated -->` markers is edited directly.

## What gets accepted into the core

A new class or relationship belongs in the core ontology if:

- it applies across industries and platforms, not only to one
- it can't be expressed with existing classes plus a Policy, a Context variable, or an attribute
- it has a clear definition that doesn't overlap an existing one (see the "minimal redundancy" criterion in the whitepaper)
- there's at least one example that uses it and validates

Everything else is a good extension. The whitepaper's section 14 explains how to extend AOW in your own namespace.

## Versioning

AOW follows semantic versioning: a major version may change the meaning of an existing term, a minor version adds terms, and a patch fixes documentation or tooling. Term changes are recorded in [CHANGELOG.md](CHANGELOG.md).

## Style

Write in plain US English. Define terms by what they are, not by what they're like. Prefer an example to an adjective.

## Conduct

Be direct about ideas and generous with people. Disagreement about modeling choices is expected and welcome; personal attacks, harassment, and discrimination aren't. Maintainers may remove comments or contributors that don't meet that bar.

## License

By contributing, you agree that your contributions are licensed under the same terms as the project: CC-BY 4.0 for prose and documentation, Apache 2.0 for the ontology, schemas, queries, examples, and code.
