# Contributing

Contributions to the Agentic Ontology of Work are welcome.

## Types of contribution

1. **Work that AOW cannot describe.** Describe the work, how you attempted to model it, and where the model was insufficient. These reports are the most valuable input to future versions.
2. **Definitions that are incorrect or ambiguous.** Quote the definition and explain the ambiguity or error.
3. **Mappings to other standards.** Crosswalks to standards, protocols, or product vocabularies.
4. **Examples.** Valid AOW documents from additional industries, added to `examples/`.

Please open an [issue](https://github.com/Skandotai/agentic-ontology-of-work/issues) before submitting a pull request that changes the ontology. Corrections to typos and broken links may be submitted directly as pull requests.

## Making changes

`aow.yaml` is the only file to edit when changing the ontology. All other artifacts are generated from it:

```sh
pip install -r requirements.txt
python tools/build.py      # regenerates ontology/, schemas/, CSVs, and the whitepaper's reference sections
python tools/site.py       # regenerates the website in docs/
python tools/validate.py   # validates the ontology, shapes, schemas, examples, and test fixtures
```

Continuous integration runs the same commands and fails if a generated file is out of date or a check fails.

Text in `whitepaper.md` outside the `<!-- aow:generated -->` markers is edited directly.

## Criteria for additions to the core ontology

A new class or relationship is added to the core ontology when:

- it applies across industries and platforms
- it cannot be expressed with existing classes plus a Policy, a Context variable, or an attribute
- its definition does not overlap an existing definition (see the minimal redundancy criterion in the whitepaper)
- at least one valid example uses it

Other additions should be made as extensions in a separate namespace. Whitepaper section 14 describes how.

## Versioning

AOW follows semantic versioning. A major version may change the meaning of an existing term, a minor version adds terms, and a patch version corrects documentation or tooling. All changes to terms are recorded in [CHANGELOG.md](CHANGELOG.md).

## Style

Use plain US English. Define terms by what they are. Use examples where they clarify a definition.

## Conduct

Discussion should remain professional and focused on the work. Harassment, personal attacks, and discrimination are not permitted. Maintainers may remove comments or contributors that do not meet this standard.

## License

Contributions are licensed under the same terms as the project: CC-BY 4.0 for prose and documentation, and Apache 2.0 for the ontology, schemas, queries, examples, and code.
