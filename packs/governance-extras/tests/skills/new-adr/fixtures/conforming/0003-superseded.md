# ADR-0003: Use the legacy configuration API

- **Status:** Superseded
- **Date:** 2026-01-01
- **Areas:** tooling
- **Reversibility:** low
- **Decision-makers:** alice
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** ADR-0002
- **Superseded in part:** none

## Context

Initial configuration approach adopted at project start.

## Decision

We use the legacy configuration API as our initial interface.

- **D1:** The legacy API is the sole configuration interface at project start.

## Consequences

Simple to implement with the available tooling.

**Revisit if:** Performance becomes a bottleneck or the API is deprecated.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** Basic smoke tests pass with the legacy API.
- **Owner:** alice

## Alternatives considered

- **New API (not yet available):** Deferred because it was not mature at decision time.
