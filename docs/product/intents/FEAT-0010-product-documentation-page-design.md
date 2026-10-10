# Improve product-documentation page design across code surfaces

- **Slug:** product-documentation-page-design
- **Level:** feature
- **Owner:** Product documentation maintainers
- **Status:** Draft

## Outcome

Product documentation can be created or improved for any code-backed product
surface without assuming the surface is an ARR pack.

## Boundary

- Generalize source discovery and page-design guidance in
  `author-product-docs` beyond pack READMEs and pack journeys.
- Keep pack documentation as one supported case rather than the default model.
- Add evaluation coverage for at least one non-pack code surface before
  changing the skill contract.
- Do not roll this broader skill change into the current workflow-page slice.

## Non-goals

- Do not change `author-product-docs` as part of the workflow-page slice.
- Do not remove or de-prioritize pack documentation support.
- Do not require one page template for every code surface.

## Riskiest assumption

The skill can infer a product surface and its documentation obligations from
heterogeneous code repositories without becoming vague or over-prescriptive.

## Unresolved questions

- What minimum evidence identifies a product surface? Answered: the
  repository's own manifests, entry points, contract files, config schemas,
  and extension registration code. `surface-discovery.md` in
  `author-product-docs` maps each of eight surfaces to that evidence.
- Which page-design rules belong where? Answered: the journey stage map and
  gap report in `references/docs-journey.md`, per-artifact contracts in
  `references/page-contracts.md`, surface evidence and checks in
  `references/surface-discovery.md`, and mode and audit procedure in
  `SKILL.md`; evaluation fixtures pin a CLI README audit and a library journey
  audit.
- Which non-pack surfaces form a representative set? Answered for now: a CLI
  fixture, a Python HTTP library, and an ecommerce framework monorepo with a
  CLI, HTTP API, SDKs, a service, and an admin app. Desktop and mobile apps
  and HTTP-API-only services remain untested.

## De-risk record

The riskiest assumption was tested on 2026-10-10 by running the shipped skill,
read-only, against three repositories with no agent pack:

| Repository | Surfaces the skill identified | Real defects it found |
| --- | --- | --- |
| A throwaway argparse CLI fixture | CLI | A documented flag the parser does not define; an undocumented subcommand |
| A Python HTTP client library | Library, CLI | Removed API members still documented; seven broken anchor links; dependency lists that contradict the manifest; a CLI with no text reference |
| An ecommerce framework monorepo | Two CLIs, HTTP API, SDKs, a service, an admin app | A Node.js prerequisite that contradicts the package engines field on four pages; undocumented CLI commands, flags, and config keys |

**Verdict:** survived. Surface identification held on every run without
pack-specific evidence, and each audit found claims that contradict source.
Both real repositories exposed gaps that the shipped skill now covers: a
framework and extension-point surface, one gap report per surface or
audience, site navigation as the docs index, a bound on large audits, and a
rule to check untrusted repositories against source instead of running their
code. Evidence: `docs/specs/product-docs-any-repo/notes/verification-ledger.md`.

## Projection

- Shape this intent before opening a delivery spec; keep the current
  workflow-page implementation independent.

## Opportunity

The current skill description and workflow are centered on pack documentation,
so they do not establish a reliable route for documenting an arbitrary
application, library, CLI, or service surface.

## Source

- Mode: chat-only
- Locator: conversation/workflow-page-contract
- Revision: 2026-09-25
- Authority: transferred-to-repository
