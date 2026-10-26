# ADR-0001: Use a hosted job queue for background work

- **Date:** 2026-01-15
- **Status:** Accepted
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Decision-makers:** @queue-owner
- **Consulted:** @data-team, @ops-guild, release managers

## Context

Background jobs need retries and visibility.

## Decision

- **D1:** Background work runs on a hosted job queue.

## Consequences

The queue vendor owns availability.

