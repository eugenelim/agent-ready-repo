# ADR-0003: Bravo record for navigation tests

- **Status:** UnderReview
- **Supersedes:** ADR-0002
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none

## Context

Bravo record covers: an unfamiliar lifecycle status ("UnderReview" is not in
any canonical list) and full supersession (Supersedes: ADR-0002). ADR-0002
mirrors this with Superseded by: ADR-0003 so the edge is checked.

## Decision

- **D1:** Services communicate through the event stream rather than the
  shared message bus.

## Consequences

Replaces ADR-0002 in full; no partial scope.
