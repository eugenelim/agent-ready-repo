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

## Open items found while shaping

Each item below surfaced while working in this pack and is deliberately not
carried by this intent. None is covered by any existing spec.

- **A `shaping-review` slot.** `frame-intent` asks the author to hold the
  dispatched-intent-revision binding in prose, because "an empty pass state
  carries no bytes to carry it" — so nothing records that an optional review
  ran, or against which revision. Cut from the slice after two spec-stage
  security rounds: storing reviewer-authored text in the blackboard is a
  data-handling design, not a documentation edit. Five questions it must
  answer, in the order they were raised: how a stored outcome binds to its
  classification's handling rather than being written "as returned"; what the
  surfacing target is when the originating role and the `regulated` escalation
  target are both `discovery-threat-reviewer`; whether sensitivity reaching the
  slot **by reference** — an id, revision and reviewer role revealing that a
  threat review ran, carrying no finding — escalates it; whether classification
  is fixed at write or re-evaluated on promotion; and where the outcome text
  lives as a single delimited field so a consumer cannot place it in an
  instruction position.
- **`frame-situation/SKILL.md:77` claims `diverge-solutions` and `place-bet`
  are "not yet shipped".** Both ship, and `docs/specs/m2-diverge-solutions/`
  and `docs/specs/m2-place-bet/` are Shipped — the line went stale when they
  landed and the degrade branch that cites it was not revisited. It reads as
  evidence and is not.
- **Two dangling `voice-and-microcopy` references in
  `packs/experience-design/DESIGN.md`**, at lines 19 and 276. The skill was
  renamed to `ux-writing` by [`ux-writing-rename`](../../specs/ux-writing-rename/spec.md),
  which also discharged RFC-0071 OQ3 — its `spec.md:53` records the
  grep-verified count that question asked for. No `voice-and-microcopy`
  directory exists in any pack, so both references name a skill that is not
  there. This is the residue of RFC-0071 OQ3 above: the rename shipped before
  the cross-reference count was taken. Both live in the experience-design pack,
  so the correction is that pack's, not this intent's slice.
- **`contracts/skill.schema.json` types `allowed-tools` as an `array`; all 25
  skills that carry the key write a space-separated scalar.** Inert today —
  `packages/agentbundle/tests/contracts/test_skill_schema.py` validates the
  schema's own structure and synthetic payloads, never a real `SKILL.md`, and
  nothing in `packages/agentbundle/src/` reads either. It is a latent trap
  rather than a live defect: wiring the schema to real files fails 25 skills at
  once, and the correction is most likely to the schema.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
