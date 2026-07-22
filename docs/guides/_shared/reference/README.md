# Reference

> *Information-oriented.* The authoritative description of interfaces, commands, configuration, and data shapes. Dry, complete, accurate. Read by people who already know what they're looking for.

## Pages

- [`agentbundle.md`](agentbundle.md) — install the CLI, install a pack, configure the default adapter.
- [`agentskills-io-standard.md`](agentskills-io-standard.md) — the agentskills.io specification applied: frontmatter keys, description rules, directory layout, independent installation, and OWASP AST01–AST10 mapping.
- [`adapter-support.md`](adapter-support.md) — the per-tool support matrix: which primitives each agent tool receives (skill / subagent / command / hook) and the runtime caveats, sourced from the adapter contract.
- [`product-brief-fields.md`](../../core/reference/product-brief-fields.md) — the product-brief field list and the linkage fields it stamps on derived specs.
- [`research-pack.md`](../../research/reference/research-pack.md) — every primitive in the `research` pack (skills, retrieval subagents).
- [`spec-shape-and-lld.md`](../../core/reference/spec-shape-and-lld.md) — the spec `Shape:` field, the plan's `## Design (LLD)` categories, and stack-derivation.
- [`reference-architecture.md`](../../architect/reference/reference-architecture.md) — the `docs/architecture/reference.md` arc42 sections and the stack-pack contract.

## Writing reference

Reference is the easiest kind of docs to write *badly* (just dump everything) and the hardest to write *well*. The bar:

- **Authoritative.** If reference and code disagree, that's a P0 bug. Reference is the contract; the code must match.
- **Complete.** Every option, parameter, return value, error code is documented. Omission is the most common reference failure.
- **Consistently structured.** Every entry of the same kind has the same shape. Predictability is everything in reference — readers scan, they don't read.
- **Boring.** No personality, no editorializing, no "you might want to use this when…" That's explanation. Reference says *what*.

## What goes in reference

- API endpoints, parameters, response shapes, status codes.
- Configuration options: name, type, default, valid values, what it does.
- CLI commands and flags.
- Error codes and messages.
- Data schemas.
- Glossary terms (definitions only — explanations live in `../explanation/`).

## What does NOT go in reference

- Tutorials (step-by-step learning).
- How-tos (task recipes).
- Why something is the way it is — that's explanation.
- Best-practice opinions — explanation.

## Auto-generation

Reference is the prime candidate for being generated from code:

- API specs from OpenAPI/GraphQL schemas.
- Config docs from typed config schemas.
- CLI docs from `--help` output.

When a section is auto-generated, mark it clearly at the top of the file ("This file is generated from `<source>`. Do not edit by hand.") so the next person doesn't waste time editing it.

## Maintenance

For hand-written reference: review on every release, and at minimum quarterly. The discipline is "code change → reference update in same PR" — enforced by CI checking that public-interface changes touched `docs/guides/reference/`.

For generated reference: check the generator runs in CI on every change. If the generator is broken, the reference is wrong, full stop.
