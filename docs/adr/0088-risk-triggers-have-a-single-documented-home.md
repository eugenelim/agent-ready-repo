# ADR-0088: Risk triggers have a single documented home

- **Status:** Accepted
- **Date:** 2026-08-19
- **Decision-makers:** eugenelim
- **Supersedes:** ADR-0014 (in part — the documentation homes of the risk-trigger block; its trigger set and light/full mode selection stand)
- **Related:** RFC-0025

## Context

The risk-trigger block was duplicated across four prose homes and a lint required
byte equality. Duplication was a maintenance hazard, and equality could not detect
deletion of the canonical copy.

## Decision

The `work-loop` skill source is the sole documented home for the risk-trigger
block. Other surfaces name the skill. The lint rejects markers outside the
canonical source and fails when its block is missing or truncated.

## Consequences

Mode selection is unchanged. A copied block now fails CI. Frozen governance
directories remain exempt so historical records may quote the block.
