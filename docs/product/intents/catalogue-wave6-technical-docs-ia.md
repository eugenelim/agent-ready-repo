# Catalogue technical documentation architecture

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0076 D9](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md)

## Outcome

Catalogue authors and evaluators can reach an organized Build a Catalogue path, including contract references and packaging guidance, from the technical documentation site.

## Opportunity

Technical documentation currently favors catalogue consumers, leaving authoring and evaluation paths hard to find and lacking a maintained route to the contracts that govern them.

## Assumptions

- Machine contracts will determine which reference material can be generated and which needs narrative explanation.

## What the decision requires

- Add a top-level docs-site section named "Build a Catalogue" with the ten routes named in RFC-0076 D9, from Create a catalogue through Package and publish (RFC-0076 D9).
- Update `index.mdx` with distinct "Use the catalogue" and "Build or evaluate a catalogue" routes (RFC-0076 D9).
- Leave the central guide-rendering and existing pack-guide routes unchanged (RFC-0076 D9).
- Generate or contract-test sidebar facts instead of maintaining an independent inventory (RFC-0076 D9).
- Generate `pack.toml` and `skill.schema.json` field references from machine contracts where practical (RFC-0076 D9).

## Open questions the RFC left

- Wave 6 determines which `pack.schema.json` fields can use schema annotations for generated references and which need manual narrative explanation (RFC-0076 OQ4).

## Source

- Mode: repo-origin
- Locator: docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
