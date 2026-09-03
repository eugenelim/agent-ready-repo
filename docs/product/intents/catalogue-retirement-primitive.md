# Provide a demand-led catalogue retirement primitive

- **Status:** Draft
- **Level:** feature

## Outcome

When a real retirement need exists, catalogue maintainers can retire a skill, agent, or hook, or deprecate a pack, with clean tombstones.

## Opportunity

Catalogue assimilation has no honest retirement counterpart, but RFC-0059 identifies that capability as rare and explicitly demand-gated.

## What this absorbs

### catalogue-curation-retire-primitive

- **Authority:** [RFC-0059 Non-goals](../../rfc/0059-catalogue-curation-pack.md)
- RFC-0059 names `retire-primitive` and `deprecate-pack` as the honest counterpart to assimilation, but says to build them only when a need is real, not speculatively.
- When that need arises, author a retire/deprecate skill in the catalogue-curation pack to cleanly retire a skill, agent, or hook, or deprecate a pack with tombstones.
- **Unblocks when:** a real pack or skill retirement need arises.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
