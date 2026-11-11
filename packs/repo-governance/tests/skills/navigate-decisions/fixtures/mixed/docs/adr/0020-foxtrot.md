# ADR-0020: Foxtrot record for navigation tests

- **Status:** Accepted <!-- approved 2026-01-20 -->
- **Supersedes:** none
- **Supersedes in part:** ADR-0001 D3
- **Superseded by:** none
- **Superseded in part:** none

## Context

Foxtrot record covers: trailing HTML comment in status (raw_value after stripping
the comment is "Accepted") and checked partial supersession with D-ID scope.
"Supersedes in part: ADR-0001 D3" mirrors ADR-0001's "Superseded in part:
ADR-0020 D3". The D-IDs belong to the superseded record (ADR-0001 defines D3).

## Decision

- **D1:** New services must not cache configuration beyond two minutes.
- **D2:** Legacy services have a six-month migration window.
- **D3:** Legacy services may cache configuration for up to two minutes.

## Consequences

Replaces ADR-0001 D3 (the legacy caching rule) in part.
