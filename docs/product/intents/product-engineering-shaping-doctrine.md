# Product engineering shaping doctrine

- **Slug:** `product-engineering-shaping-doctrine` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Accepted
- **Accepted:** 2026-10-01 by eugenelim, lifecycle owner. Revision `8c9328fc8bf98443` returned zero `MALFORMED` tokens in an independent intent-mode shaping review, and a fresh adversarial intent read returned no material open question or replacement validation hook. The feature-level assumption survived its predeclared kill condition, and the remaining work stays one feature projected to one spec and plan.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:digital-experience-doctrine
- **Milestone:** M2b in RFC-0071's implementation sequence
- **Governed by:** [RFC-0071 Area C and D2](../../rfc/0071-digital-experience-doctrine.md)
- **De-risked:** 2026-10-01
- **Shaping-reviewed:** 2026-10-01
- **Decomposed:** 2026-10-01 spec

## Outcome

- **Input (steerable):** the share of accepted bets that name one end-to-end thin slice, classify their load-bearing evidence, and carry a post-launch learning contract with decision thresholds and recovery.
- **Outcome (lagging):** shipped work can be traced to an observable first-success result and a reviewable expand, change, hold, or roll-back decision instead of ending at implementation completion.
- **Guardrail:** shaping stays host-neutral and proportionate; it does not implement telemetry storage, adapter transports, or a second discovery loop.

## Opportunity

- **Functional job:** turn a chosen bet into the smallest useful end-to-end result whose evidence, recovery, and post-launch decision can be inspected.
- **Emotional job:** feel confident that “thin” still means useful and learnable rather than merely fewer implementation tasks.
- **Social job:** give delivery, design, and product reviewers one defensible account of why the slice is worth shipping and what evidence will change the next decision.
- **Struggling moment:** `place-bet` records rationale, appetite, risk, assumptions, and confidence, but the shipped contract's thin-slice, evidence, and learning concepts are not wired into the artifact the delivery loop receives.

## Product-to-experience handoff

- **Affected journey or surface:** the bounded end-to-end user path named by the thin slice, including one material failure and recovery path.
- **User outcome and first-success behavior:** one user begins a real task and reaches a meaningful accepted result; internal execution milestones do not count.
- **Product mechanism or proof:** the bet names the capability, visible result, and evidence that the experience may expose without deciding its design.
- **Evidence for user-visible claims:** load-bearing claims use the observed, supported, inferred, assumed, or unknown ladder with source, producer, time, revision, and derivation.
- **Constraints, prohibited claims, and material unknowns:** capability gaps, consent or permission boundaries, fallback, retry, duplicate, cancellation, and recovery semantics are recorded without choosing an adapter protocol.

## Assumptions

- The Digital Experience Contract supplies the shared definitions of thin slice, first success, evidence ladder, rollout/recovery, and learning plan. The repository probe below survived; use on real bets remains `to-validate`.
- **Knowledge surface:** the in-repository RFC, pack, guide, contract, and spec corpus plus the 2026-10-01 current-standards survey.

## Riskiest assumption

The right fix is to wire the already-shipped Digital Experience Contract
concepts into `place-bet`, not to redesign the product-engineering shaping
loop or implement adapter protocols inside it.

## De-risk record — 2026-10-01

- **Level kind:** feature, so the dominant risk is whether one enriched bet artifact will help practitioners make a thinner and more learnable delivery decision.
- **Reversibility triage:** one-way door because the bet artifact is a published handoff into capability mapping, spec authoring, and delivery.
- **Prototype approach:** `validate-first`; the cheapest failing probe was a contract-to-writer ownership walk over the live `place-bet` output and adjacent shaping skills.

### Kill condition, predeclared

Kill or reframe if thin slice, evidence ladder, or learning contract cannot be emitted through one `place-bet`-owned portable artifact using existing definitions, or if doing so requires redesigning the shaping loop or implementing runtime protocols.

### Probe and verdict — survived

- The pack-local Digital Experience Contract already defines Evidence Ladder, First-Success Operationalization, Thin Slice, Capabilities, Rollout and Recovery Plan, and Learning Plan. The missing qualitative-feedback and expansion-condition details are additive fields, not a second owner.
- `place-bet` already owns one `bet.md` handoff and emits rationale, risks, assumptions, a kill condition, and the pointer to capability mapping. It is the natural single writer; no new artifact or loop is needed.
- `frame-intent` now supplies the human-facing outcome and evidence context, while `de-risk-intent` supplies the predeclared kill condition. `place-bet` can consume those facts without absorbing either skill's job.
- Capability availability, consent, fallback, retry, duplicate, cancellation, and recovery can remain semantic fields. No required criterion needs MCP, A2A, Agent Skills, or host-specific transport implementation.

The three required additions fit one existing writer and one portable artifact. No kill arm fired. The spec must wire the contract into `place-bet` and its review/eval surfaces rather than redesigning the shaping sequence.

### Validation hook

```yaml
validation_hook:
  assumption: One enriched bet artifact will let product engineers choose and review a useful thin slice, evidence quality, and post-launch learning decision without protocol-specific implementation.
  kill_condition: Reframe if any of three representative bets needs a second authoritative artifact, cannot state an end-to-end useful slice and decision threshold, or requires a runtime protocol choice before spec authoring can proceed.
  activity: to-validate — after the feature ships, replay three recent shaped bets through the revised place-bet flow with their product engineer and delivery reviewer, then record whether the resulting artifact changed the slice or learning decision and what they had to reconstruct.
```

## What the decision requires

- Add a thin-slice required field to `place-bet` output (RFC-0071 Area C). It
  names one end-to-end user path, usable result, bounded cohort, observable
  signal, recovery path, and learning decision rather than a smaller
  implementation ticket.
- Add a post-launch learning contract covering events, dashboards, qualitative feedback, review cadence, decision thresholds, and rollback or expansion conditions (RFC-0071 Area C).
- Implement the evidence ladder: observed, supported, inferred, assumed, and
  unknown (RFC-0071 Area C). Each claim also carries source, producer,
  observed-at time, revision, derivation, and a stable link to the claim it
  supports. Observable events carry identity, source, type, occurrence time,
  schema version, and correlation context.
- Replace fixed-count options with: "explore enough materially different options to expose the real decision; do not invent alternatives to satisfy a number" (RFC-0071 Area C).
- Replace G0/G1.5/G2 with plain English in user-facing output and update evals with weak fixtures (RFC-0071 Area C).
- Rename `voice-and-microcopy` to `ux-writing` following the ADR-0038 alias-free precedent, and update cross-references in the PE and XD packs (RFC-0071 D2 / Area C).
- Update `packs/product-engineering/JOURNEY.md` so its `whatChanges` field links
  the shaping doctrine to the Digital Experience Contract, then regenerate the
  journey projection. This absorbs
  `digital-experience-contract-pe-journey-xref`; the generated web file is not
  edited directly.
- Keep the shaping contract portable across hosts. A bet records required and
  optional capabilities, permission or consent boundaries, a named fallback
  when a capability is unavailable, and retry, duplicate, cancellation, and
  recovery behavior for asynchronous work. Adapter or protocol revisions may
  project this semantic contract; this intent does not implement MCP or A2A.

### Observed state — 2026-10-01

Each row is a grep over the live tree, re-runnable rather than trusted. This is
an observation on a date, not a status field: the requirements above stay as
RFC-0071 wrote them.

| Requirement | Observed | Check |
| --- | --- | --- |
| thin-slice field in `place-bet` | not started in `place-bet`; defined but unwired | the betting table and emitted artifact still have no thin-slice field. The contract template defines Thin Slice, but no shaping skill reads that section |
| post-launch learning contract | not started in `place-bet`; partly defined and unwired | events, dashboards, cadence, thresholds, qualitative feedback, rollback, and expansion conditions are still absent from `place-bet`. The contract template carries only part of the required shape |
| evidence ladder (observed → unknown) | partial outside `place-bet` | the shipped Product-to-experience handoff now asks for evidence behind user-visible claims using the five ladder labels, but `place-bet` still emits only one confidence scalar and does not grade claims |
| replace fixed-count options | **shipped** | No option-count floor survives on any live surface, in symbolic or prose form. The skill's activation description, body, output contract, anti-patterns and worked example, the pack journey entry and its web projection, and the two guides that described the skill all ask for options that expose the real decision instead of a number. `docs/product/research/aesthetic-style-survey.md` still quotes the old wording and is left alone — it is a dated survey recording what the skill said when it was written |
| `G0`/`G1.5`/`G2` → plain English | barely started | plain-English labels coexist with the codes, which remain in `JOURNEY.md`, `DESIGN.md`, the README, guide headings, and user-facing discovery instructions |
| evals with weak fixtures | not started | the pack still contains no weak fixture; routing near-misses cannot catch weak shaped output or stale gate vocabulary |
| `voice-and-microcopy` → `ux-writing` | shipped | the skill is renamed, no `voice-and-microcopy` directory exists in any pack, and `git ls-files \| xargs grep -Hl` returns no live reference — every remaining hit is a frozen governance record under `docs/rfc/` or `docs/specs/`. The cross-references the rename left behind were closed in `experience-design` 2.0.7 and `product-engineering` 0.13.14 |
| `JOURNEY.md` `whatChanges` → Digital Experience Contract | not started | neither the pack journey nor its web projection names the contract. The regeneration path remains available once the source changes |

Four are unstarted, one is partial, one is barely started, and two have shipped.
The separate shipped `frame-intent-experience-handoff` work improves the
experience handoff and first-success context, but it does not deliver the
`place-bet` thin-slice, evidence, or post-launch contracts this intent owns.

The unfinished thin-slice, evidence-ladder, and learning-contract rows share a
cause worth stating before anyone picks them up: **the concepts are already
defined in this pack and wired to nothing.**
`frame-intent/references/digital-experience-contract.md` carries § Thin Slice,
§ Evidence Ladder, § Learning Plan and § Instrumentation — and no skill in the
pack, including `frame-intent` itself, references that file. So the work is not
"design these concepts"; it is "wire `place-bet` to definitions that already
ship". Two gaps survive even there: qualitative feedback and expansion
conditions are named nowhere in the pack.

### Current-standards pressure test — 2026-10-01

The [external survey](../research/digital-experience-doctrine-current-standards-survey.md)
confirms the thin-slice and learning outcomes, and adds provenance plus
capability-fallback semantics. Weak fixtures must now include missing optional
capabilities, version mismatch, ignored optional fields, cancellation and
recovery, duplicate delivery, consent denial, and a host that cannot render an
interactive capability. Protocol-specific conformance remains with the adapter
or integration owner.

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
  skills that carry the key write a space-separated scalar.** The Agent Skills
  specification uses the scalar form and marks the field experimental. This is
  a standards-conformance repair for the schema owner, with real-file tests;
  it is not part of the shaping doctrine feature.

## Non-goals

- Implementing MCP, A2A, Agent Skills adapter transports, host-specific runtime
  bridges, or telemetry storage.
- Replacing `frame-intent`, `de-risk-intent`, or the whole product-engineering
  discovery loop.
- Closing the two pack-local open items above; both need their own owner and
  intake route.

## Decomposition

One same-repository spec and plan at
`docs/specs/product-engineering-shaping-doctrine/` own the remaining M2b
outcome. They integrate the six unfinished doctrine obligations with the two
already-shipped changes and the newer Product-to-experience handoff, rather
than repeating those delivered surfaces. This remains one feature because all
acceptance surfaces prove one observable, learning-oriented shaping contract.
Re-decompose if protocol transport or adapter implementation enters scope.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
