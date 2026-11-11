# ADR-0002: Adopt a new configuration API

- **Status:** Accepted
- **Date:** 2026-03-01
- **Areas:** tooling
- **Reversibility:** low
- **Decision-makers:** alice
- **Supersedes:** ADR-0003
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none

## Context

ADR-0003's legacy approach proved inadequate for distributed services.

## Decision

We adopt the new configuration API across all services.

- **D1:** The new API replaces the legacy configuration mechanism from ADR-0003.

## Consequences

Positive: better performance and observability.

**Revisit if:** The new API introduces regressions in existing services.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** All integration tests pass with the new API.
- **Owner:** alice

## Alternatives considered

- **Keep legacy API from ADR-0003:** Rejected because of performance and scalability concerns.
