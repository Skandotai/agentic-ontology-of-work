# w3id.org/aow

AOW's identifiers (`https://w3id.org/aow#Intent` and so on) use [w3id.org](https://w3id.org), a community-run permanent identifier service, so they keep resolving even if the project's hosting changes.

Registered September 25, 2026: https://github.com/perma-id/w3id.org/pull/6748

The redirect rules are in [`.htaccess`](.htaccess). The registered copy is `ids/aow/.htaccess` in https://github.com/perma-id/w3id.org. To change the rules, update both copies: edit this file, then open a pull request against perma-id/w3id.org from the Skandotai fork (https://github.com/Skandotai/w3id.org).

| Request | Redirects to |
|---|---|
| `https://w3id.org/aow` (browser) | the ontology reference page |
| `https://w3id.org/aow` (`Accept: text/turtle`) | `ontology/aow.ttl` |
| `https://w3id.org/aow` (`Accept: application/ld+json`) | `ontology/aow.jsonld` |
| `https://w3id.org/aow/2.0.0` | the frozen 2.0.0 copy, by the same rules |
| `https://w3id.org/aow/context.jsonld` | the JSON-LD context |
| `https://w3id.org/aow/shapes` | the SHACL shapes |
| `https://w3id.org/aow/schemas/<name>` | the JSON Schemas |
