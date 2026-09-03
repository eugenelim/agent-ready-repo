# Product engineering shaping doctrine

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0071 D2](../../rfc/0071-digital-experience-doctrine.md)

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

## Open questions the RFC left

- Record a grep-verified count of PE and XD references before the `voice-and-microcopy` to `ux-writing` rename ships (RFC-0071 OQ3).

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
