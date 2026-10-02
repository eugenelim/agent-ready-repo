# Product strategy adoption doctrine

- **Slug:** `product-strategy-adoption-doctrine` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Accepted
- **Accepted:** 2026-10-01 by eugenelim, lifecycle owner. Revision `17fb2e52c77906f0` returned zero `MALFORMED` tokens in an independent intent-mode shaping review, and a fresh adversarial intent read returned no material open question or replacement validation hook. The feature-level assumption survived its predeclared kill condition, and the remaining work stays one feature projected to one spec and plan.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:digital-experience-doctrine
- **Milestone:** M2a in RFC-0071's implementation sequence
- **Governed by:** [RFC-0071 D8](../../rfc/0071-digital-experience-doctrine.md)
- **De-risked:** 2026-10-01
- **Shaping-reviewed:** 2026-10-01
- **Decomposed:** 2026-10-01 spec

## Outcome

- **Input (steerable):** the share of new or amended strategy artifacts that carry an adoption hypothesis, user-goal first success, a causal metric tree, and a named experience handoff with evidence.
- **Outcome (lagging):** Product Engineering and Experience Design can act on strategy without re-deriving who should adopt, what value looks like, how it will be observed, or what the experience must make visibly true.
- **Guardrail:** the strategy pack states hypotheses, decisions, and measures without absorbing growth-program operations, telemetry implementation, or adapter-specific event schemas.

## Opportunity

- **Functional job:** turn a strategic choice into a downstream-usable account of adoption, first value, measurement, and experience intent.
- **Emotional job:** trust that a strategy will guide a real product experience rather than end as a polished document downstream teams reinterpret.
- **Social job:** give product, design, and engineering one defensible account of what the strategy asks them to achieve and how they will know.
- **Struggling moment:** the current strategy methods name direction and measures, but the adoption hypothesis, first-success event, and experience proof are not carried together, so each downstream discipline fills the gaps differently.

## Product-to-experience handoff

- **Affected journey or surface:** the first-value path and the surfaces that must express the strategy's promise, proof, objections, and next valuable action.
- **User outcome and first-success behavior:** the user completes the goal or receives the accepted result named by the strategy; a tool call, task creation, or page view alone is not first success.
- **Product mechanism or proof:** the strategy names what must be recognizably true, what credible proof is available, and which value-loop action should follow.
- **Evidence for user-visible claims:** every claim is tied to observed, supported, inferred, assumed, or unknown evidence and to its source.
- **Constraints, prohibited claims, and material unknowns:** no growth-program execution, adapter event schema, or unsupported success claim is decided here.

## Assumptions

- The shipped Digital Experience Contract remains the shared outcome boundary for the doctrine. The repository probe below survived; adopter use remains `to-validate`.
- **Knowledge surface:** the in-repository RFC, pack, guide, contract, and spec corpus plus the 2026-10-01 current-standards survey.

## Riskiest assumption

Product-strategy can state adoption, first success, causal metrics, and
experience handoff semantics in a host-neutral way that downstream packs can
use without turning this feature into growth operations or telemetry
implementation.

## De-risk record — 2026-10-01

- **Level kind:** feature, so the dominant risk is whether practitioners and downstream consumers will use one portable strategy-to-adoption contract rather than re-derive it.
- **Reversibility triage:** one-way door because the fields become a published cross-pack handoff used by several skills and guides.
- **Prototype approach:** `validate-first`; the cheapest failing probe was a producer/consumer and boundary walk over the live pack methods.

### Kill condition, predeclared

Kill or reframe if any of adoption hypothesis, first success, causal metrics, or experience handoff has no named downstream decision or consumer, or if delivering one of them requires growth-program or adapter-specific ownership.

### Probe and verdict — survived

- `define-ux-strategy` already produces experience goals and behavioral measures for `journey-mapping`; `define-content-strategy` hands purpose and governance to `content-design`; `run-okr-cascade` routes strategic gaps into Product Engineering; and `write-prfaq` already asks for the acquisition path and success metric.
- The shared Digital Experience Contract already names the metric tree and first-success operationalization, while Product Engineering's product-to-experience handoff carries first-success behavior, proof, evidence, constraints, and unknowns to Experience Design.
- `packs/product-strategy/DESIGN.md` keeps growth programs and cohort operations outside the pack. Nothing in the required semantic handoff needs a host event schema.

All four groups have a producer, a downstream decision, and a portable artifact seam. No kill arm fired. The gap is that these facts are not yet required together or reviewed as one contract; that is spec work, not evidence against the feature.

### Validation hook

```yaml
validation_hook:
  assumption: Strategists and downstream product/design practitioners will use one portable adoption, first-success, metric, and experience handoff rather than re-derive those decisions.
  kill_condition: Reframe if any of three representative strategy-to-delivery walks causes Product Engineering or Experience Design to re-derive one of the four groups, or requires growth-program operations or adapter-specific fields to proceed.
  activity: to-validate — after the feature ships, walk three real strategy artifacts through Product Engineering and Experience Design with the practitioners who own each handoff, recording which fields drove a decision and which were ignored or recreated.
```

## What the decision requires

- Require the 14-point strategy semantics with an adoption hypothesis:
  acquisition context, promise, proof, first action, first-success event,
  repeat-value behavior, and economic behavior where material (RFC-0071 Area B
  / D8). A field may be `not applicable` only with evidence; the count is not a
  fill-the-form target.
- Define first success as a completed user goal or accepted result, not a tool
  call or task creation. The metric tree must cover leading behavior,
  repeat-value and longer-term outcomes, guardrails, data-quality checks,
  expected direction and time horizon, decision thresholds, and evidence
  provenance.
- Add `strategy-to-experience` with eight named semantics covering recognition,
  problem, demonstration, objections, credible proof, secondary concepts,
  value-loop action, and what must be visibly true (RFC-0071 Area B). For
  agentic experiences, the last field also records user authority or consent
  and the visible proof that an automated action succeeded.
- Review for the eleven named anti-patterns, including vision-without-choices, target-everyone segment, launch-as-adoption, and validated-without-evidence (RFC-0071 Area B).
- Use natural strategic-question triggers and near-misses for routine backlog shaping and copyediting without a strategy question (RFC-0071 Area B).

### Observed state — 2026-10-01

Each row is a check against the live tree (`packs/`, `guides/`, `web/`,
`docs-site/`, `tools/`, `packages/`), re-runnable rather than trusted. Frozen
spec bodies under `docs/specs/` are historical records and were not counted as
evidence. This is an observation on a date, not a status field.

| Requirement | Observed | Check |
| --- | --- | --- |
| 14-point strategy output with adoption hypothesis | not started | `adoption hypothesis`, `first success`, and `causal metric tree` have no hit in `packs/product-strategy/` or its guides |
| `strategy-to-experience` handoff, eight named fields | not started | `strategy-to-experience` has no hit in the product-strategy pack or guide |
| review for eleven named anti-patterns | not started | the four named examples (`vision-without-choices`, `target-everyone`, `launch-as-adoption`, `validated-without-evidence`) have no hit in the product-strategy pack or guide |
| natural triggers plus near-misses | partial | skill-local negative activation cases remain, but the required routine-backlog and copyediting cases with no strategy question are still absent |

**0 shipped · 1 partial · 3 not started.** No stale wording: every path and
skill name it references either exists or was never created.

### Current-standards pressure test — 2026-10-01

The [external survey](../research/digital-experience-doctrine-current-standards-survey.md)
confirms the outcome and tightens its measurement semantics. Strategy remains
host-neutral: protocol names and adapter event shapes belong in engineering
projections. Add negative fixtures for tool-call-as-adoption,
task-created-as-first-success, adapter-specific metrics, success without
guardrails, and metrics without data-quality evidence.

## Non-goals

- Growth operations—AARRR, PLG, PMF testing, experimentation operations, paid acquisition, lifecycle campaigns, and SEO—remain for a future growth pack; product-strategy owns the hypothesis, not the programs (RFC-0071 D8).

## Decomposition

One same-repository spec and plan at
`docs/specs/product-strategy-adoption-doctrine/` own the remaining M2a outcome.
They update the strategy methods, reviews, activation cases, pack guidance, and
release evidence together so the adoption contract cannot land as an unwired
template. This remains one feature because each surface proves the same
portable strategy-to-adoption contract. Re-decompose if growth-program
operations or runtime-specific telemetry implementation enters scope.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
