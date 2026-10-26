# ADR-0001: Contradictory partial supersession test — superseding side

- **Status:** Accepted
- **Supersedes:** none
- **Supersedes in part:** ADR-0002 D1
- **Superseded by:** none
- **Superseded in part:** none

## Context

This record claims "Supersedes in part: ADR-0002 D1". ADR-0002 mirrors with
"Superseded in part: ADR-0001 D2". The scopes differ (D1 vs D2), so the pair
is contradictory and both entries remain unresolved rather than forming a
checked edge. The D-IDs belong to the superseded record (ADR-0002 must define D1
and D2 for the entry to be parseable, but the scopes still disagree).

## Decision

- **D1:** Contradictory partial supersession scope is unresolved evidence.
