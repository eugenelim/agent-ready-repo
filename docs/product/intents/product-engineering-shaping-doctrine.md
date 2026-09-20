# Product engineering shaping doctrine

- **Slug:** `product-engineering-shaping-doctrine` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** [Digital experience doctrine](digital-experience-doctrine.md)
- **Milestone:** M2b in RFC-0071's implementation sequence
- **Authority:** [RFC-0071 Area C and D2](../../rfc/0071-digital-experience-doctrine.md)

## Outcome

Product engineers can shape a delivery bet around a thin slice, a first success event, evidence quality, and a post-launch learning contract that connects the work to an observable customer result.

## Opportunity

The product-engineering methods support discovery and framing but do not consistently require the operational adoption and learning details that make a shaped bet testable after delivery.

## Assumptions

- The Digital Experience Contract supplies the shared definition of an observable outcome.

## What the decision requires

- Add a thin-slice required field to `place-bet` output (RFC-0071 Area C).
- Add a post-launch learning contract covering events, dashboards, qualitative feedback, review cadence, decision thresholds, and rollback or expansion conditions (RFC-0071 Area C).
- Implement the evidence ladder: observed, supported, inferred, assumed, and unknown (RFC-0071 Area C).
- Replace fixed-count options with: "explore enough materially different options to expose the real decision; do not invent alternatives to satisfy a number" (RFC-0071 Area C).
- Replace G0/G1.5/G2 with plain English in user-facing output and update evals with weak fixtures (RFC-0071 Area C).
- Rename `voice-and-microcopy` to `ux-writing` following the ADR-0038 alias-free precedent, and update cross-references in the PE and XD packs (RFC-0071 D2 / Area C).
- Update `packs/product-engineering/JOURNEY.md` so its `whatChanges` field links
  the shaping doctrine to the Digital Experience Contract, then regenerate the
  journey projection. This absorbs
  `digital-experience-contract-pe-journey-xref`; the generated web file is not
  edited directly.

### Observed state — 2026-09-20

Each row is a grep over the live tree, re-runnable rather than trusted. This is
an observation on a date, not a status field: the requirements above stay as
RFC-0071 wrote them.

| Requirement | Observed | Check |
| --- | --- | --- |
| thin-slice field in `place-bet` | not started | 0 matches for `thin.slice` in `place-bet/SKILL.md` |
| post-launch learning contract | not started | 0 matches for `learning contract`, `review cadence`, `rollback or expansion` in `place-bet/SKILL.md` |
| evidence ladder (observed → unknown) | not started | 0 matches for `evidence ladder` in `place-bet/SKILL.md` or `diverge-solutions/SKILL.md` |
| replace fixed-count options | not started | `diverge-solutions/SKILL.md` still states `≥3` in 3 places |
| `G0`/`G1.5`/`G2` → plain English | partial | `JOURNEY.md` carries `G0` and `G3` but no `G1.5`/`G2`; `guides/product-engineering/how-to/run-a-discovery.md` carries all four. The evals half is untouched: 0 matches for `weak` in `discovery-loop/evals/` |
| `voice-and-microcopy` → `ux-writing` | shipped incomplete | the skill is renamed and no `voice-and-microcopy` directory exists in any pack; 2 references survive in `packs/experience-design/DESIGN.md` and now name nothing |
| `JOURNEY.md` `whatChanges` → Digital Experience Contract | not started | 0 matches for `Digital Experience Contract` in `packs/product-engineering/JOURNEY.md` |

Four of seven are unstarted, two are partial, and none is complete. The two
partials are the ones that read as done from a distance, which is why the check
column is here.

## Open items in this pack

Neither is an RFC-0071 requirement. Both surfaced while working in
`packs/product-engineering/` and are recorded here because this is the pack's
intent, not because this intent's decision requires them.

- **A `shaping-review` slot in the discovery sidecar.** `frame-intent` asks the
  author to hold the dispatched-intent-revision binding in prose, because "an
  empty pass state carries no bytes to carry it", so nothing records that an
  optional review ran or against which revision. Storing reviewer-authored text
  in the blackboard is a data-handling design: it needs a home for the outcome
  bound to its classification's handling rather than written as returned; a
  surfacing target for when the originating role and the `regulated` escalation
  target are both `discovery-threat-reviewer`; a decision on whether sensitivity
  reaching the slot by reference escalates it; a choice between write-time and
  promotion-time classification; and a single delimited field so a consumer
  cannot place the text in an instruction position. Its authority is RFC-0053
  and ADR-0111, not RFC-0071.
- **`contracts/skill.schema.json` types `allowed-tools` as an `array`; all 25
  skills that carry the key write a space-separated scalar.** Inert today —
  nothing in `packages/agentbundle/src/` reads either the key or the schema, and
  the schema's own tests validate synthetic payloads rather than real
  `SKILL.md` files. It is a latent trap rather than a live defect: wiring the
  schema to real files fails 25 skills at once, and the correction is most
  likely to the schema.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
