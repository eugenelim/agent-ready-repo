# ADR-0004: Keep sessions in a database

- **Date:** 2026-02-01
- **Status:** Accepted
- **Supersedes:** ADR-0003
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Decision-makers:** @example-maintainer

## Context

Sessions must survive a restart.

## Decision

- **D1:** Sessions are kept in a database.

## Consequences

**Revisit if:** session volume outgrows a single database.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** a reviewer confirms no in-memory session store is added.
- **Owner:** @example-maintainer
