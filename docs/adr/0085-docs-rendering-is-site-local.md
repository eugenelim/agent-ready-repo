# ADR-0085: Docs rendering is site-local

- **Status:** Accepted
- **Date:** 2026-08-17
- **Decision-makers:** eugenelim
- **Supersedes:** [ADR-0055](0055-starlight-replaces-mkdocs-for-reference-docs.md) in part — shared palette and design-token implementation
- **Related:** [RFC-0089](../rfc/0089-starlight-docs-boundary.md), [ADR-0055](0055-starlight-replaces-mkdocs-for-reference-docs.md)

## Decision summary

- **Decision:** The marketing and technical-documentation sites retain renderer-local palettes, components, and framework controls.
- **Because:** Their separate Astro renderers serve different purposes and the shipped Starlight documentation design has an intentionally docs-specific palette.
- **Applies to:** `web/` marketing rendering and `docs-site/` Starlight documentation rendering.
- **Tradeoff accepted:** Shared visual changes may require separate implementations.
- **Revisit if:** A future accepted RFC establishes a renderer-neutral design system that satisfies both sites without weakening their framework contracts.

## Context

ADR-0055 selected Starlight and described sharing the marketing site's design-token system. The later documentation refresh instead shipped a self-contained docs palette and recorded that boundary in `docs-site/AGENTS.md`.

RFC-0089 ratified the shipped structure: `web/` is the marketing project, `docs-site/` is the technical-documentation project, and their generated outputs form one ordered publication artifact.

## Decision

The marketing and technical-documentation sites will own their palettes, components, and framework controls locally.

Shared product identity may be expressed through information architecture, destination vocabulary, and generated content data. It does not require shared CSS, runtime components, or colour alignment.

This supersedes only ADR-0055's palette and design-token-sharing decision. Its decisions about Starlight, the sibling project boundary, the Node/Astro toolchain, and build order remain authoritative.

## Decision drivers

- Preserve the accepted sibling-project boundary.
- Honour the docs-specific palette and pinned Starlight contracts.
- Describe shipped behavior without triggering a redesign.
- Avoid coupling two renderer implementations through visual internals.

## Consequences

**Positive:**

- Each site can evolve within its framework's native contracts.
- Documentation accessibility and visual tuning remain locally governable.
- Shared content and navigation contracts do not create CSS or component coupling.

**Negative:**

- Similar chrome may require two implementations.
- Cross-site consistency must be reviewed as an outcome rather than inferred from shared tokens.
- Future visual changes must identify the affected renderer explicitly.

**Revisit if:** A future accepted RFC establishes a renderer-neutral design system that satisfies both sites without weakening their framework contracts.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** Site changes preserve renderer-local implementation and do not align the docs palette with `web/` without an accepted superseding decision.
- **Owner:** Tech-site maintainers

## Alternatives considered

**Share one palette and token implementation:** rejected because it contradicts the shipped docs-specific palette and couples independent renderers.

**Move technical documentation into `web/`:** rejected because Starlight's routing and ownership model are intentionally isolated in the sibling project.

**Keep separate projects but align their colours:** rejected because visual sameness is not required for shared product identity and would reopen an already settled docs design decision.

## References

- [RFC-0089: Starlight docs boundary](../rfc/0089-starlight-docs-boundary.md)
- [ADR-0055: Starlight replaces MkDocs for reference docs](0055-starlight-replaces-mkdocs-for-reference-docs.md)
