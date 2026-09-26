# Information architecture archetypes and objects

- **Slug:** `xd-ia-archetypes-objects` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:digital-experience-doctrine
- **Milestone:** M3c in RFC-0071's implementation sequence
- **Governed by:** [RFC-0071 § Implementation sequence — M3c](../../rfc/0071-digital-experience-doctrine.md)

## Outcome

Experience-design practitioners can select a page archetype and map the product objects, attention, permission, and navigation rules that make a surface understandable and actionable.

## Opportunity

Information architecture guidance needs a shared way to connect page purpose and product objects to the hierarchy, state, and navigation decisions that users encounter.

## Assumptions

- The XD skill-boundary work will establish the ownership boundary for this guidance.

## What the decision requires

- Add `references/page-archetypes.md` with at least 12 surface types (RFC-0071 Area D / M3c).
- For each archetype, record its primary user, job, first-screen contract, primary action, expected result, next action, proof, read/write consequence, critical states, and navigation behavior (RFC-0071 Area D).
- Add product-object mapping guidance, an attention contract, and a read/write permission contract to relevant skills (RFC-0071 Area D).
- Deliver M3c after M3a and before M3d in the accepted implementation sequence (RFC-0071 § Implementation sequence).

### Observed state — 2026-09-26

Each row is a check against the live tree (`packs/`, `guides/`, `web/`,
`docs-site/`, `tools/`, `packages/`), re-runnable rather than trusted. Frozen
spec bodies under `docs/specs/` are historical records and were not counted as
evidence. This is an observation on a date, not a status field.

| Requirement | Observed | Check |
| --- | --- | --- |
| `references/page-archetypes.md` with ≥12 surface types | not started, but the starting structure changed | no file of that name anywhere. The nearest live structure is now the genre-reference set under `information-architecture/references/`: **6** genre method files plus shared IA references, reached by the routing table at `information-architecture/SKILL.md:69-74`. That is still surface-genre method, not page-archetype guidance. The file is referenced by 4 shipped `digital-experience-contract.md` copies and resolves to nothing |
| per-archetype field set | partial, wrong pack and wrong axis | the field set ships as a **per-screen** contract in `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md:368-386` (12 fields). No archetype axis, no navigation-behavior field, nothing equivalent in `packs/experience-design` |
| product-object mapping, attention contract, permission contract in the relevant skills | partial, template only | the three headings exist in the contract template copies. In XD skill bodies: `product object` → 0 hits, `attention contract` → 0, `permission contract` → 0 |
| deliver M3c after M3a, before M3d | not started | M3a is Shipped (`docs/specs/xd-skill-boundaries/`); no spec exists for this intent |

**0 shipped · 2 partial · 2 not started.**

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
