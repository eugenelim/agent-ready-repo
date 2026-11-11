# ADR-0002: Middle record for lineage depth tests

- **Status:** Accepted
- **Supersedes:** ADR-0001
- **Supersedes in part:** none
- **Superseded by:** ADR-0003
- **Superseded in part:** none

## Context

Middle record — one hop from the root (ADR-0003) and one hop from the leaf
(ADR-0001). Used to verify depth=1 traversal reaches this record but not
ADR-0001, and depth=2 traversal reaches both.

## Decision

- **D1:** Middle decision.
