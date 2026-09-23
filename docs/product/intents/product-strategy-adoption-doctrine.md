# Product strategy adoption doctrine

- **Slug:** `product-strategy-adoption-doctrine` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:digital-experience-doctrine
- **Milestone:** M2a in RFC-0071's implementation sequence
- **Governed by:** [RFC-0071 D8](../../rfc/0071-digital-experience-doctrine.md)

## Outcome

Product-strategy practitioners can turn a strategy into an adoption hypothesis, causal metric tree, experience handoff, and reviewable evidence instead of stopping at a choice-free strategy artifact.

## Opportunity

The product-strategy pack has useful strategy methods but does not yet require the adoption and measurement structure that makes a strategy observable in the digital experience it directs.

## Assumptions

- The shipped Digital Experience Contract remains the shared outcome boundary for the doctrine.

## What the decision requires

- Require a 14-point strategy output structure with an adoption hypothesis: acquisition context, promise, proof, first action, first-success event, repeat-value behavior, and economic behavior where material (RFC-0071 Area B / D8).
- Add `strategy-to-experience` with eight named fields covering recognition, problem, demonstration, objections, credible proof, secondary concepts, value-loop action, and what must be visibly true (RFC-0071 Area B).
- Review for the eleven named anti-patterns, including vision-without-choices, target-everyone segment, launch-as-adoption, and validated-without-evidence (RFC-0071 Area B).
- Use natural strategic-question triggers and near-misses for routine backlog shaping and copyediting without a strategy question (RFC-0071 Area B).

### Observed state — 2026-09-20

Each row is a check against the live tree (`packs/`, `guides/`, `web/`,
`docs-site/`, `tools/`, `packages/`), re-runnable rather than trusted. Frozen
spec bodies under `docs/specs/` are historical records and were not counted as
evidence. This is an observation on a date, not a status field.

| Requirement | Observed | Check |
| --- | --- | --- |
| 14-point strategy output with adoption hypothesis | not started | `adoption hypothesis` → 2 hits, both in `guides/core/explanation/digital-experience-contract.md`; 0 in `packs/product-strategy/` |
| `strategy-to-experience` handoff, eight named fields | not started | `strategy-to-experience` → 0 files across all six live roots |
| review for eleven named anti-patterns | not started | the four named ones (`vision-without-choices`, `target-everyone`, `launch-as-adoption`, `validated-without-evidence`) → 0 hits; generic `## Anti-patterns` exists in all 9 skills but carries none of them |
| natural triggers plus near-misses | partial | all 9 `product-strategy` skills carry 5 `should_trigger: false` near-misses each (45 total); none is the "no strategy question at all" class the requirement names — `backlog`/`copyedit` → 0 hits across those files |

**0 shipped · 1 partial · 3 not started.** No stale wording: every path and
skill name it references either exists or was never created.

## Non-goals

- Growth operations—AARRR, PLG, PMF testing, experimentation operations, paid acquisition, lifecycle campaigns, and SEO—remain for a future growth pack; product-strategy owns the hypothesis, not the programs (RFC-0071 D8).

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
