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
| thin-slice field in `place-bet` | not started in `place-bet`; defined but unwired | `place-bet`'s betting table and emitted artifact enumerate their fields exhaustively and no slice concept appears under any wording. The definition already exists at `frame-intent/references/digital-experience-contract.md` § Thin Slice (`Required: pilot+`), which no skill reads |
| post-launch learning contract | not started in `place-bet`; partly defined and unwired | `place-bet` has no events, telemetry, dashboards, cadence, thresholds, rollback or expansion anywhere; its optional `kill-condition` is a pre-commit falsification trigger, not a post-launch plan. The contract template defines § Learning Plan, § Instrumentation and § Rollout and Recovery Plan — but **qualitative feedback and expansion conditions are named nowhere in the pack** |
| evidence ladder (observed → unknown) | not started in `place-bet`; defined and unwired | `place-bet`'s `confidence: high / medium / low` is a different axis — one scalar for the decision, not a per-claim provenance grade. It has no level meaning "we did not check" as distinct from "we reasoned it out", which is the ladder's whole purpose. The ladder exists verbatim at `digital-experience-contract.md` § Evidence Ladder (`Required: explore+`) |
| replace fixed-count options | **shipped** | `diverge-solutions` states no minimum option count on any surface — description, body, output contract, or journey entry — and asks for enough materially different options to expose the real decision |
| `G0`/`G1.5`/`G2` → plain English | barely started | Only `JOURNEY.md`'s four `humanGates` labels are plain English, and even that file keeps `globalGate: "G0"` and `"G3"`. Codes survive on every other user-facing surface: the frontmatter `description` of `discovery-loop` and `frame-domain`, all three agent `description`s, `discovery-loop`'s gate-ladder table, five guide files including their section headings, `README.md`'s sample transcript and `DESIGN.md`'s diagram and gate table. The five `description` fields matter most — they are what the harness surfaces at activation |
| evals with weak fixtures | not started | The pack ships no weak fixture. `eval_queries.json` carries `should_trigger: false` near-misses, but those route between sibling skills and never exercise output, so none could catch gate vocabulary. The one fixture file the pack loads is a well-written exemplar, not a defective input. The convention exists elsewhere — `product-documentation` ships `evals/files/fixture_weak_*` graded on being rejected. Worse, `discovery-loop`'s own eval prompts are written in gate-code vocabulary, so they need rewriting as part of the conversion rather than extending |
| `voice-and-microcopy` → `ux-writing` | shipped | the skill is renamed, no `voice-and-microcopy` directory exists in any pack, and `git ls-files \| xargs grep -Hl` returns no live reference — every remaining hit is a frozen governance record under `docs/rfc/` or `docs/specs/`. The cross-references the rename left behind were closed in `experience-design` 2.0.7 and `product-engineering` 0.13.13 |
| `JOURNEY.md` `whatChanges` → Digital Experience Contract | not started | `whatChanges` describes the discovery loop's mechanics only; nothing in the pack, the guides or the projection links the contract. The regeneration half is live and wired — `tools/build-site.py --journeys-only` generates the web journey from the pack source and CI runs it — so the edit must be followed by that command and its result committed |

Four are unstarted, one is barely started, two have shipped. The gate-vocabulary
row is split in two because its evals half has a different owner and a different
fix from its prose half.

The three unstarted rows share a cause worth stating before anyone picks them
up: **the concepts are already defined in this pack and wired to nothing.**
`frame-intent/references/digital-experience-contract.md` carries § Thin Slice,
§ Evidence Ladder, § Learning Plan and § Instrumentation — and no skill in the
pack, including `frame-intent` itself, references that file. So the work is not
"design these concepts"; it is "wire `place-bet` to definitions that already
ship". Two gaps survive even there: qualitative feedback and expansion
conditions are named nowhere in the pack.

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
