# Cross-pack experience evaluation

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0071 D7](../../rfc/0071-digital-experience-doctrine.md)

## Outcome

Maintainers can run a golden-path evaluation across strategy, shaping, experience design, frontend engineering, rendered output, and measurement to prove the whole digital-product arc works together.

## Opportunity

Each affected pack has its own evaluation surfaces, but no executable check currently demonstrates that their combined handoffs produce an observable end-to-end experience.

## Assumptions

- The upstream doctrine slices define the artifacts and handoffs that the golden path must exercise.

## What the decision requires

- Put the cross-pack golden-path eval in `packs/experience-design/evals/`; experience design is the terminal whole-journey reviewer (RFC-0071 D7).
- Cover four fixture types: public marketing plus docs, SaaS onboarding plus workspace, internal dashboard, and transactional service (RFC-0071 Area F).
- Add deterministic `tools/` checks for referenced skills, phantom handoffs, risk-mode contract fields, contract-copy drift, and evidence-manifest entries (RFC-0071 Area F).
- Start integrated evals report-only and calibrate them before promoting them to gates (RFC-0071 Area F).
- Deliver M5 only after M2 through M4 in the accepted implementation sequence (RFC-0071 § Implementation sequence).

## Non-goals

- Promoting the cross-pack eval to a gate is deferred until calibration evidence includes at least two weak-fixture runs and one real-product fixture (RFC-0071 Follow-on work).

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
