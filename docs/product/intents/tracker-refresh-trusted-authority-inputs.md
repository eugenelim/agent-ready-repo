# Tracker refresh carries trusted authority inputs

- **Status:** Draft
- **Level:** feature

## Outcome

Tracker refresh receives trusted materialized-child scope, verified lifecycle and resolved capabilities, and an explicit projection-repair confirmation before any affected local or remote write.

## Boundary

- Trusted input contracts and propagation for Ready-brief refresh, remote write-back availability and enforcement, and repo-origin projection repair.
- Tracker transport implementations, general result-code vocabularies, credential acquisition, and unrelated refresh behavior remain outside this intent.

## Owner

- Tracker-refresh maintainers; no individual owner is recorded.

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
