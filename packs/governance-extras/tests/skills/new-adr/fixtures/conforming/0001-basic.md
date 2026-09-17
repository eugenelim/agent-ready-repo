# ADR-0001: Adopt a centralized configuration store

- **Status:** Accepted
- **Date:** 2026-01-15
- **Areas:** tooling, infrastructure
- **Reversibility:** low
- **Decision-makers:** alice
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none

## Decision summary

- **Decision:** Configuration is stored centrally.
- **Because:** Simplifies management across services.
- **Applies to:** All backend services.
- **Revisit if:** The store becomes unavailable or a bottleneck.

## Context

Previously each service maintained its own configuration files, causing drift.

## Decision

We adopt a centralized configuration store for all backend services.

- **D1:** Configuration state is stored in a shared store, not in per-service files.
- **D2:** All services read configuration at startup from the shared store.

## Decision drivers

- Consistency across services.
- Single source of truth.

## Consequences

Positive: simpler management. Negative: single point of failure risk.

**Revisit if:** The store becomes unavailable or introduces unacceptable latency.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** Integration tests confirm all services connect on startup.
- **Owner:** alice

## Alternatives considered

- **Per-service config files:** Rejected because it causes drift between services.
- **Environment variables only:** Rejected because secrets management becomes complex.

## Errata

- 2026-02-01: Clarified that D2 applies only to startup-time reads.
