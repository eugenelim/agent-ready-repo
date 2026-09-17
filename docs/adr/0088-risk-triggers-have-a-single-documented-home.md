# ADR-0088: Risk triggers have a single documented home

- **Status:** Accepted
- **Date:** 2026-08-19
- **Areas:** work-loop, documentation
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0014
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0025

## Context

The risk-trigger block was duplicated across four prose homes and a lint required
byte equality. Duplication was a maintenance hazard, and equality could not detect
deletion of the canonical copy.

## Decision

The `work-loop` skill source is the sole documented home for the risk-trigger
block. Other surfaces name the skill. The lint rejects markers outside the
canonical source and fails when its block is missing or truncated.

- **D1:** The `work-loop` skill source is the sole documented home for the
  risk-trigger block.
- **D2:** Every other surface names the skill instead of carrying a copy of the
  block.
- **D3:** The lint rejects risk-trigger markers outside the canonical source, and
  fails when the canonical block is missing or truncated.
- **D4:** Frozen governance directories are exempt, so historical records may
  quote the block.
- **D5:** This changes the documentation homes only; ADR-0014's trigger set and
  its light/full mode selection are unchanged.

## Consequences

Mode selection is unchanged. A copied block now fails CI. Frozen governance
directories remain exempt so historical records may quote the block.

**Revisit if:** a surface outside the `work-loop` skill needs the risk-trigger
block inline for a reason the frozen-governance exemption (D4) does not already
cover.
