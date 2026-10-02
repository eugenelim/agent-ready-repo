# Digital product integrative guides

- **Slug:** `digital-product-guides-update` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:digital-experience-doctrine
- **Milestone:** M6 in RFC-0071's implementation sequence
- **Governed by:** [RFC-0071 § Implementation sequence — M6](../../rfc/0071-digital-experience-doctrine.md)
- **De-risked:** no
- **Shaping-reviewed:** no
- **Decomposed:** 2026-10-01 spec

## Outcome

Adopters can follow a coherent end-to-end digital-product guide and find the cross-pack intent and evidence needed to apply the complete experience workflow.

## Opportunity

Guidance exists within individual packs, but there is no integrative tutorial or intent index that explains how the disciplines combine into one digital-product outcome.

## Assumptions

- The approved M5 spec must pin the evaluation receipt, compatibility dimensions, and host-evidence vocabulary that the guide consumes; delivered M5 runs later supply the dated evidence.
- **Knowledge surface:** the in-repository RFC, guide, adapter contract, workflow, and spec corpus plus the 2026-10-01 current-standards survey.

## Riskiest assumption

Once M5 produces evaluation receipts, verified pack indexes, one host-neutral
tutorial, and short host overlays are enough for adopters to apply the whole
workflow without a new docs-generation platform.

## What the decision requires

- Update user guides with mechanically verified intent indexes for each pack
  and one host-neutral end-to-end tutorial (RFC-0071 Reviewer brief).
- Add short host-specific execution overlays and an adapter compatibility
  matrix showing supported, transformed, degraded, and dropped primitives plus
  live-eval coverage. Record the adapter-contract revision and last validated
  host versions and dates, and link the tutorial to M5 evaluation receipts.
- Distinguish filesystem Agent Skills, host-specific plugins, hooks, agents and
  commands, Skills over MCP, and A2A `AgentSkill`; similar names do not make
  these contracts interchangeable.
- Deliver M6 after the M5 cross-pack experience evaluation (RFC-0071 § Implementation sequence).

### Observed state — 2026-10-01

Each row is a check against the live tree (`packs/`, `guides/`, `web/`,
`docs-site/`, `tools/`, `packages/`), re-runnable rather than trusted. Frozen
spec bodies under `docs/specs/` are historical records and were not counted as
evidence. This is an observation on a date, not a status field.

| Requirement | Observed | Check |
| --- | --- | --- |
| an intent index for each of the four doctrine packs | partial | Experience Design has a pack-wide index. Product Strategy, Product Engineering, and Frontend Engineering still do not |
| each index is pack-wide rather than skill-scoped | partial | the Experience Design index is pack-wide; unrelated indexes elsewhere do not satisfy the three missing doctrine-pack indexes |
| the XD index describes the shipped skills | **shipped** | its current routes cover the twelve registered Experience Design skills, including the genre and copy modes created by the consolidation work |
| a new end-to-end tutorial spanning strategy → PE → XD → FE | not started | no tutorial in any of the 11 `guides/*/tutorials/` dirs spans the chain; `docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md:190` states outright that S1 "does not create or satisfy the future digital-product tutorial" |
| deliver M6 after the M5 cross-pack evaluation | waits on M5's contract and receipts | no approved M5 evaluation contract or dated journey receipt exists yet, so the tutorial and compatibility matrix cannot cite a stable evidence shape |
| adapter compatibility and freshness guidance | not started | no doctrine guide records the supported projection matrix, host overlays, adapter-contract revision, host validation dates, or M5 receipts |

**1 shipped · 2 partial · 2 not started · 1 blocked.**

Gate vocabulary is **not** stale here: `G0`/`G1.5`/`G2` appear at 16 lines
across the guides, and `discovery-loop/SKILL.md` still uses them, so guide and
skill agree. The conversion is pending on both sides, not half-done.

### Current-standards pressure test — 2026-10-01

The [external survey](../research/digital-experience-doctrine-current-standards-survey.md)
confirms that static indexes and one tutorial are useful but insufficient.
Agent Skills standardizes the package shape, not equivalent discovery,
loading, inheritance, consent, or runtime behavior across hosts. Generate or
mechanically verify changing indexes and compatibility claims instead of
letting prose assert permanent parity.

### Spec-authoring dependency

Refresh and de-risk this intent after the M5 spec is approved. Its receipt and
compatibility contracts are the minimum inputs needed to specify the generated
freshness signals, host overlays, and evidence links. Guide implementation
still waits for real M5 receipts, but spec authoring need not wait once their
shape is approved.

## Boundary with `pack-guidebook-walkability`

[`pack-guidebook-walkability`](../../specs/pack-guidebook-walkability/spec.md)
owns static guidebooks for the five SOP packs. This intent keeps RFC-0071 M6's
different chain, which includes `frontend-engineering`, plus the cross-pack
intent indexes and end-to-end digital-product tutorial after M5 evaluation.

## Non-goals

- Replacing pack-local guides that already explain one pack's standalone use.
- Building a documentation-generation platform.
- Claiming cross-host parity without versioned adapter evidence and M5 receipts.

## Decomposition

One same-repository spec and plan at
`docs/specs/digital-product-guides-update/` own M6 after the M5 evaluation
validates the journey. They add the three missing doctrine-pack indexes, keep
the current Experience Design index aligned, and publish one host-neutral
tutorial with bounded host overlays and versioned compatibility evidence. This
remains one feature because the indexes and tutorial form one adoption surface.
Re-decompose if a docs-generation platform becomes required rather than a
bounded verification helper.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
