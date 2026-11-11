# Claude manifest migration and support claims

- **Slug:** `claude-manifest-migration-support-claims`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:first-class-distribution-routes
- **Depends on:** intent:distribution-route-set-opening
- **Decomposed:** 2026-11-05 brief

## Outcome

Generated-equivalent Claude manifest fields are retired safely and public support claims derive from machine-readable route capability and runtime-verification records.

## Opportunity

Hand-authored Claude manifests duplicate derivable data and published support claims lack the completed route-layer record.

## Boundary

This feature owns retiring generated-equivalent Claude manifest fields and
deriving public support claims from route capability and runtime-verification
records.

It does not remove the compatibility alias before its approved window ends or
promote documentation-only evidence to runtime-verified support.

## Assumptions

- **Riskiest assumption:** migration can retire generated-equivalent fields while preserving enough compatibility for existing Claude consumers.
- **Knowledge surface:** In-repository RFC-0092, distribution-routes programme brief, route capability records, and support-claim evidence.

## Readiness

- **Route:** delivery brief [`claude-manifest-migration-support-claims-delivery`](../briefs/claude-manifest-migration-support-claims-delivery.md), three slices. P1 (verification record and a generated block in `guides/_shared/reference/adapter-support.md`) needs only the route contract; P2 (warn and record the window) follows P1; P3 (removal) follows P2 in a later minor release.
- **Dependency relaxed 2026-11-05:** it formerly waited on the Kiro profile. Neither slice reads Kiro code. Routes shipped later add their own record row.
- **Unresolved question answered:** the owner decided on 2026-11-05 that the compatibility window is one minor release of warning, then removal. P3 decides the window is closed by comparing the build's version with the recorded end release.
- **Agent-only proof:** schema and regeneration fixtures; a hand edit to the matrix fails a check.

## Source

- Mode: repo-origin
- Locator: docs/product/briefs/distribution-routes-programme.md
- Revision: sha256-bytes-v1:329d3aec010ffd0f0b090022bac7faf35b85f337d9b3c719ab8063b7c74dbc45
