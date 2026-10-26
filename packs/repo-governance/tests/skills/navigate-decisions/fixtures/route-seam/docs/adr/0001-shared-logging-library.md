# ADR-0001: Services share one logging library

- **Date:** 2026-01-15
- **Status:** Accepted
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none

## Context

Each service formatted logs differently, which made incidents slow to trace.

## Decision

- **D1:** Every service uses the shared logging library for structured logs.

## Consequences

Services depend on one library release cadence.

