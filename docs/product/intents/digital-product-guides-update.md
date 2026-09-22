# Digital product integrative guides

- **Slug:** `digital-product-guides-update` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** [Digital experience doctrine](digital-experience-doctrine.md)
- **Milestone:** M6 in RFC-0071's implementation sequence
- **Governed by:** [RFC-0071 § Implementation sequence — M6](../../rfc/0071-digital-experience-doctrine.md)

## Outcome

Adopters can follow a coherent end-to-end digital-product guide and find the cross-pack intent and evidence needed to apply the complete experience workflow.

## Opportunity

Guidance exists within individual packs, but there is no integrative tutorial or intent index that explains how the disciplines combine into one digital-product outcome.

## Assumptions

- The cross-pack evaluation will establish the validated journey that the guides explain.

## What the decision requires

- Update user guides with intent indexes for each pack and a new end-to-end tutorial (RFC-0071 Reviewer brief).
- Deliver M6 after the M5 cross-pack experience evaluation (RFC-0071 § Implementation sequence).

### Observed state — 2026-09-20

Each row is a check against the live tree (`packs/`, `guides/`, `web/`,
`docs-site/`, `tools/`, `packages/`), re-runnable rather than trusted. Frozen
spec bodies under `docs/specs/` are historical records and were not counted as
evidence. This is an observation on a date, not a status field.

| Requirement | Observed | Check |
| --- | --- | --- |
| an intent index for each pack | partial | 6 matching headings across 5 of 21 pack guide directories. Of RFC-0071's four target packs, only `experience-design` and `core` have one; `product-engineering`, `product-strategy` and `frontend-engineering` have none |
| the index is pack-wide, not skill-scoped | partial | only `guides/experience-design/reference/experience-design.md:44` and `guides/atlassian/atlassian-skills.md:22` index a whole pack. Three others index a single skill's intents |
| the XD index describes the shipped skills | **shipped** | its 21 rows diff clean against `ls packs/experience-design/.apm/skills` — identical 20-name set, no phantom rows |
| a new end-to-end tutorial spanning strategy → PE → XD → FE | not started | no tutorial in any of the 11 `guides/*/tutorials/` dirs spans the chain; `docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md:190` states outright that S1 "does not create or satisfy the future digital-product tutorial" |
| deliver M6 after the M5 cross-pack evaluation | not started | no `docs/specs/cross-pack-experience-eval/`; that intent is still Draft, and `workspace.toml:519` registers the unmet dependency |

**1 shipped · 2 partial · 2 not started** — the only shipped requirement in the
whole RFC-0071 family.

Gate vocabulary is **not** stale here: `G0`/`G1.5`/`G2` appear at 16 lines
across the guides, and `discovery-loop/SKILL.md` still uses them, so guide and
skill agree. The conversion is pending on both sides, not half-done.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
