# Tracker refresh carries trusted authority inputs

- **Slug:** `tracker-refresh-trusted-authority-inputs`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Parent intent:** capability:external-tracker-projection

## Outcome

Tracker refresh receives trusted materialized-child scope, verified lifecycle and resolved capabilities, and an explicit projection-repair confirmation before any affected local or remote write.

## Boundary

- Trusted input contracts and propagation for Ready-brief refresh, remote write-back availability and enforcement, and repo-origin projection repair.
- Tracker transport implementations, general result-code vocabularies, credential acquisition, and unrelated refresh behavior remain outside this intent.

## Owner

- eugenelim, with tracker-refresh maintainers.

## Unresolved questions

- None recorded. The three missing inputs are delivered together because they protect the same refresh authority boundary.

## Projection

- One focused security-boundary implementation specification that defines the three trusted inputs, threads them through both status and processor surfaces, and proves check-before-effect refusal when any input is absent or invalid.

## Opportunity

This intent absorbs tracker-refresh-materialized-child-scope, tracker-refresh-enforced-capability-state, and tracker-refresh-projection-repair-confirmation. Current refresh surfaces cannot distinguish materialized child scope, affirmatively report and enforce lifecycle-scoped remote capabilities, or authorize repo-origin projection repair without inferring authority.

## Assumptions

- Each gap requires a new trusted input; no defaulted parameter or tracker-derived value may stand in for authority.
- The projected specification changes authorization-sensitive data flow and therefore requires a security-design review.


## Source

- Mode: repo-origin
- Locator: docs/specs/tracker-refresh-writeback/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

## Current truth

Not re-verified against the code. `refresh.py` already takes `lifecycle` and a capability set from the request. The registry retirement (core 4.0.10 and 4.0.14) may have changed where those come from. The three captured items are identity anchors only, with no detail.

## Readiness

- **Route:** new-spec, after a one-session re-baseline. The re-baseline reads `refresh.py` and its callers and records which of the three inputs still lack a trusted source.
- **First slice:** the re-baseline note, then one spec for the inputs that remain.
- **Agent-only proof:** tests show refusal before any local or remote write when an input is absent or invalid.
- **Manual dependency:** none. Needs a security-design review.

## Riskiest assumption

**Riskiest assumption:** all three inputs still lack a trusted source after the registry retirement. Tested agent-only by the first slice, a re-baseline that reads `refresh.py` and its callers and records which inputs are already supplied by trusted code.

## De-risk result

2026-11-05. Read `refresh.py`, `_header_readiness.py` and the work-intake skill. Result, per input:
- Capability state: `ProcessorRegistration.capabilities` and `resolve(..., required_capability=...)` already refuse with `unsupported_capability`, but no non-test caller passes `required_capability`. The gap is wiring, not a missing input.
- Materialized child scope: `_header_readiness.py` already validates child scope (`invalid_child_scope`, `cooled_child_scope_unknown`) on the work-loop side. `refresh.py` has no equivalent.
- Projection-repair confirmation: no trace in `refresh.py` or the skill beyond the shared repair lock.
Verdict: the premise that all three inputs lack a trusted source is partly false; not stamped De-risked. The first slice narrows to wiring `required_capability`, deciding whether `refresh.py` reuses the work-loop child-scope check, and adding the repair confirmation.
