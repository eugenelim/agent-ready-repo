# Code-intelligence real-world usage validation

- **Slug:** `native-provider-selection-validation` <!-- canonical identity; the slug and filename keep the original name so no reference changes -->
- **Status:** Draft
- **Reset:** 2026-11-04 by eugenelim, lifecycle owner. Returned from `Accepted` to `Draft`. The accepted outcome, boundary, assumption and validation hook described a blind three-participant six-question exercise. The parent's 2026-10-08 owner scope decision replaced that exercise with guided real-world use of the `code-intelligence` pack, and the delivery spec was reopened to match. The outcome, boundary, assumptions and hook below now describe that guided validation, so the 2026-10-08 shaping review and the de-risk record no longer apply and are removed. A fresh independent shaping review is required before `Accepted`.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:optional-code-intelligence-composition
- **Decomposed:** 2026-10-04 spec
- **Governed by:** [RFC-0079](../../rfc/0079-codebase-context-pack.md)

## Outcome

- **Input (steerable):** Maintainers or adopters complete the self-serve worksheet on their own authorized legacy-app repositories and real pending changes, and return coded summaries.
- **Outcome (lagging):** The capability owner knows whether, after setup and training, people can use the `code-intelligence` pack to get relevant, source-verifiable evidence for grounding and exploration on a real change, and whether the pack's role or onboarding should be retained or changed.
- **Guardrail:** Coaching and optional help are recorded as evidence, never scored as failure. No result is converted into a provider schema, a delivery mandate, a claim about unaided provider selection or arbitrary-provider generalization, or a claim that graph-assisted review is more effective. No credentials, private endpoints, customer data or app source enter a committed record.

## Opportunity

- **Functional job:** Decide whether the shipped pack earns its place in a legacy-app investigation, by running it on work people already need to do rather than on a constructed exercise.
- **Emotional job:** Trust that the pack was tried on real changes, with setup friction and wrong claims recorded, rather than judged from a document exercise its authors shaped.
- **Social job:** Give the capability owner evidence to retain, change or narrow the pack's role and onboarding.
- **Struggling moment:** The construction exercise cleared every question, but it was primed by the RFC and says nothing about whether a maintainer can set the pack up and use its findings on their own app.

## Boundary

This feature owns the guided protocol, the self-serve participant worksheet, the minimized result record, and the retain-or-change recommendation routed to the parent owner. Its delivery contract is the [delivery spec](../../specs/native-provider-selection-validation/spec.md).

It does not implement a provider integration, compare code-review outcomes, select a vendor, normalize provider interfaces, require a facilitator, a second provider shape or public source, or change Core's no-provider path. Blind provider selection, unaided recognition of tool limits and live generalization across native provider shapes are outside this feature and create no new intent or backlog item.

## Assumptions

- **Riskiest assumption:** After setup and training, maintainers and adopters can use the pack to obtain useful, source-verifiable evidence for a real change in their existing legacy apps while recognizing the evidence gaps.
- Participants can complete and return the worksheet without a facilitator, using the linked first-session guide for setup.
- A small, self-reported sample supports a bounded retain-or-change decision and nothing wider; the result reports its actual sample and environment coverage.
- **Knowledge surface:** CAP-0011's owner scope decision of 2026-10-08, RFC-0079, the delivery spec and protocol, the participant worksheet, and the first-session guide.

## Validation hook

```yaml validation_hook
assumption: With setup instructions and pack-specific training, maintainers and adopters can use the code-intelligence pack to obtain useful, source-verifiable evidence for grounding and exploration on a real change in their existing legacy apps while preserving material evidence limits.
kill_condition: Reframe the pack's role or onboarding if guided real-task use cannot produce relevant findings that participants verify in source and use in their investigation, or if setup barriers, incorrect claims, or hidden evidence gaps prevent a usable result. Do not interpret this as a verdict on unaided selection or arbitrary-provider generalization.
activity: Invite maintainers or adopters to complete the self-serve instrument on their own authorized legacy-app repositories and actual pending changes. The instrument links the first-session guide for setup, teaches skill activation through sample prompts, asks participants to check important findings against source, and provides coded response fields they fill in and return. No facilitator is required; help is optional and recorded. Retain only coded summaries of setup, assistance, useful findings, errors, remaining gaps, and participant feedback. Judge usefulness in the grounding and exploration role; do not apply the old blind six-question pass line or require a second provider shape.
```

## Decomposition

One slice, `native-provider-selection-validation`, projected to `new-spec`. The [spec](../../specs/native-provider-selection-validation/spec.md) and its plan own the guided protocol revision, the worksheet, the evidence fields, the privacy boundary and the interpretation rules. Humans run the participation; the plan prepares the artifacts and synthesizes the returned summaries.

## Unresolved questions

- Which maintainers or adopters, and how many, take part? The spec requires the protocol to declare recruitment scope and planned coverage before invitations.
- Can a second reader reproduce the interpretation from the minimized observations alone? The spec requires that check before the result is routed to the owner.
- What should change in CAP-0011 after the result? Its owner decides from the recorded evidence and its stated coverage limits.

## Projection

The [delivery spec](../../specs/native-provider-selection-validation/spec.md) owns its own review and approval. This intent's acceptance does not authorize invitations, data collection or access to any participant environment.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md`
- **Revision:** `fe8a1fde266b83e23ea961a5cdd5f4fcbfb090be`
- **Authority:** eugenelim, parent capability owner
