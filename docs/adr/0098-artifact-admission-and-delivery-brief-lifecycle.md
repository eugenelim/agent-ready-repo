# ADR-0098: Artifact admission and delivery briefs use distinct canonical owners

- **Status:** Accepted
- **Date:** 2026-08-27
- **Decision-makers:** eugenelim
- **Supersedes:** ADR-0009 Decision 1; ADR-0019 Decision 2; ADR-0076 public-receiver holding; ADR-0077 feature-projection table; ADR-0078 minimal Core intent fields (each only as specified below)
- **Related:** RFC-0099; ADR-0099

## Decision summary

- **Decision:** Neutral intake, repository-intent admission, and delivery-brief lifecycle are separate responsibilities owned by `work-intake`, `intake-intent`, and `author-delivery-brief`.
- **Because:** artifact content and authority should determine the owner without forcing every route through a feature intent or split brief lifecycle.
- **Applies to:** Core work intake, repository intents, delivery briefs, trackers, and compatibility aliases.
- **Tradeoff accepted:** two old brief names remain temporarily as bounded aliases.
- **Revisit if:** the accepted routing study fails its one-owner or Core-only operation bar.

## Context

Core currently combines neutral intake with repository-intent authoring and divides delivery-brief creation and readiness between two public skills. Earlier ADRs also assume that every brief or tracker route begins from a feature intent.

Those holdings create avoidable routing ambiguity. They also make Product Engineering concepts mandatory for adopters that install only Core, despite Core already having sufficient artifact and authority contracts.

RFC-0099 authorizes clause-level replacements while preserving workspace schemas, lifecycle collections, artifact paths, tracker authority, refresh conflict handling, brief altitude, and plan-owned low-level design.

## Decision

**We will give neutral intake, repository-intent admission, and delivery-brief lifecycle distinct canonical owners.**

`work-intake` remains the neutral entry for raw, ambiguous, acquisition, refresh, and intake-safety requests. Status and explicitly named artifact or work-type requests route directly to their existing owners.

`intake-intent` creates or admits a repository intent. Its minimum contract is status, outcome, boundary, owner, unresolved questions, projection, and source data required by the authority mode. Product fields such as level, opportunity, assumptions, scale, and JTBD remain optional enrichment.

`author-delivery-brief` owns two explicit modes:

- `create` authors a Draft from sufficient authority.
- `continue` evaluates an existing repository brief for Ready and changes status only with human confirmation.

A Ready brief may contain zero specs. Selecting and materializing a delivery slice is a separate human confirmation.

A brief’s coverage map separates governance references from executable delivery slices. Only specs participate in execution and closure rollups.

`author-brief` delegates only to `author-delivery-brief create`. `receive-brief` delegates only to `author-delivery-brief continue`. Both aliases are write-old/read-old compatibility surfaces, emit a deprecation notice, and cannot widen the canonical owner’s authority.

### Clause-level replacements

- ADR-0009 Decision 1 is refined so the brief map has separate governance-reference and spec-slice groups; only specs retain rollup semantics.
- ADR-0019 Decision 2 is refined so intent ancestry is optional and `author-delivery-brief` owns brief creation and continuation.
- ADR-0076’s public-receiver holding is refined so readiness and selected-slice handling belong to `author-delivery-brief continue`.
- ADR-0077’s feature-projection table is refined so sufficient direct artifact authority may bypass feature-intent creation.
- ADR-0078’s minimum Core intent fields are replaced by the minimum repository-intent contract above; its workspace index and dispatch rules remain unchanged.

All unlisted holdings in those ADRs remain authoritative.

## Decision drivers

- Route by artifact content and authority rather than processor history.
- Keep Core complete without requiring Product Engineering.
- Preserve fail-closed source authority, confinement, and refresh behavior.
- Avoid a workspace schema or artifact-path migration.
- Retain compatibility without allowing permanent dual semantics.

## Consequences

**Positive:**

- Every intake scenario has one canonical first owner.
- Repository intent no longer requires product-shaping fields.
- Brief creation and readiness share one lifecycle owner.
- Governance references cannot distort delivery rollups.
- Existing workspace data and old prompts remain usable.

**Negative:**

- The compatibility window temporarily exposes old and new brief names.
- Guides, trackers, receipts, evals, and projections must migrate together.
- Removing either alias requires the accepted support floor, advance notice, rollback evidence, and explicit Approver decision.

**Revisit if:** the accepted routing study fails its one-owner or Core-only operation bar.

## Confirmation

- **Mode:** lint/CI
- **Signal:** routing, activation, alias, trust-boundary, tracker, guide, and projection fixtures prove canonical write-new behavior while workspace schemas remain compatible.
- **Owner:** Core maintainers

## Alternatives considered

**Rename `work-intake` to `intake-intent`.** Rejected because neutral intake also owns direct work, defects, acquisition, refresh, and safety routing.

**Use `author-intent-brief`.** Rejected because a delivery brief is a coordination envelope and does not necessarily descend from an intent.

**Keep `author-brief` and `receive-brief` as separate lifecycle owners.** Rejected because it preserves duplicated doctrine and ambiguous continuation ownership.

**Remove the old names immediately.** Rejected because supported prompts and integrations still invoke them.

## References

- RFC-0099: Cut before adding and artifact shaping.
- ADR-0009, ADR-0019, ADR-0076, ADR-0077, and ADR-0078: clause-level prior holdings.
