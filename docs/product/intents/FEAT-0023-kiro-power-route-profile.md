# Kiro Power route profile

- **Slug:** `kiro-power-route-profile`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:first-class-distribution-routes
- **Depends on:** intent:distribution-route-set-opening

## Outcome

Kiro consumes the portable Agent Plugin artifact through a first-class route profile with Kiro-specific admission, activation, extension, and support claims.

## Opportunity

Kiro Powers are documented but the catalogue has no Kiro-owned route profile.

## Boundary

This feature owns the Kiro route profile over portable package bytes and
Kiro-specific admission, activation, extension, and support claims.

It does not create a new steering source, claim project adaptation, or claim seed
support.

## Assumptions

- **Riskiest assumption:** portable package bytes are sufficient for a useful Kiro Power route profile without project adaptation or seed support.
- **Knowledge surface:** In-repository RFC-0092, ADR-0091, distribution-routes programme brief, and Kiro route evidence.

## Readiness

- **Route:** `new-spec`, one session. ADR-0091 already settled the decision.
- **Dependency relaxed 2026-11-05:** it formerly waited on the Codex route. The profile consumes portable package bytes, which are shipped. Waiting for FEAT-0020 is preferred because the profile is then a contract entry and doubles as a second test of the open route set. It does not need the Codex route.
- **Verified 2026-11-05:** no Kiro Power route exists in `contracts/distribution-routes.toml`.
- **First slice and agent-only proof:** a Kiro route entry, an admission and activation fixture derived from Kiro documentation, and an empty `dev.kiro/steering/` extension point. No steering source is invented.
- **Manual residue, non-blocking:** a real Kiro install check.

## Source

- Mode: repo-origin
- Locator: docs/product/briefs/distribution-routes-programme.md
- Revision: sha256-bytes-v1:329d3aec010ffd0f0b090022bac7faf35b85f337d9b3c719ab8063b7c74dbc45
