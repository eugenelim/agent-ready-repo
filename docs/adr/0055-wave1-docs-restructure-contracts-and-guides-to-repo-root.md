# ADR-0055: Wave 1 docs restructure — lift contracts/ and guides/ to repo root

**Status:** Accepted  
**Date:** 2026-07-26  
**Areas:** documentation, packaging  
**Reversibility:** high  
**Decision-makers:** eugenelim  
**Supersedes:** none  
**Supersedes in part:** none  
**Superseded by:** none  
**Superseded in part:** none  
**Related:** none

## Context

`docs/contracts/` and `docs/guides/` were nested under `docs/` for historical reasons. As the catalogue matures, these two trees serve distinct, repo-root-level audiences:

- **`contracts/`** — JSON Schema files that govern pack, skill, profile, and adapter formats. Validators, CI, and adopters reference them directly; the `docs/` namespace implied they were prose documentation rather than machine-readable schemas.
- **`guides/`** — Diátaxis-structured guides for users and adopters. Co-locating them with the architecture docs under `docs/` made them harder to discover and linked them semantically to internal design notes.

Both are cross-cutting concerns that belong at the repo root, not nested under `docs/`.

## Decision

Move `docs/contracts/` → `contracts/` and `docs/guides/` → `guides/` at repo root (Wave 1 of a planned docs restructuring).

- **D1:** `docs/contracts/` lives at `contracts/` at the repository root.
- **D2:** `docs/guides/` lives at `guides/` at the repository root.
- **D3:** Path references in the agentbundle engine (`build/`, `commands/`) resolve the new root locations; behavioral paths change, behavioral logic does not.
- **D4:** Adopter seed files under `packs/*/seeds/` keep scaffolding `docs/guides/` in adopter repos and are not moved with this wave.

Consequences:
- Path references in the agentbundle engine (`build/`, `commands/`) updated to reflect the new locations — behavioral paths change, not behavioral logic.
- Adopter seed files (under `packs/*/seeds/`) intentionally left unchanged; they scaffold `docs/guides/` in adopter repos.
- Pack-local docs (`packs/*/docs/`) and the credential-brokers pack docs addition are Wave 1 companions — additive documentation only, no logic change.

## Consequences

**Revisit if:** a later wave of the docs restructuring moves more of `docs/` to the repository root, or adopter seeds must scaffold the new root locations instead of `docs/guides/` (D4).

## Alternatives considered

**Keep under `docs/`.** Discarded — discovery and semantic clarity are worse; validators referencing `docs/contracts/` look like they point to documentation prose rather than schema files.

**Move only `contracts/`.** Discarded — `guides/` has the same root-level ownership problem; splitting the wave creates follow-up churn.
