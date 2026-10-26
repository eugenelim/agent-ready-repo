# ADR-0002: Store web sessions in Redis

- **Date:** 2026-01-15
- **Status:** Accepted
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none

## Context

Web sessions must survive a single server restart.

## Decision

- **D1:** Web sessions are stored in Redis.

## Consequences

Redis becomes a runtime dependency of the web tier.

