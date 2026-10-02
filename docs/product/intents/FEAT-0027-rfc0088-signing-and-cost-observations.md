# RFC-0088 signing and destination-cost observations are complete

- **Slug:** `rfc0088-signing-and-cost-observations`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:rfc0088-browser-follow-on-specs
- **Governed by:** [spec/rfc0088-round12-consumer-shaped-residuals AC5](../../specs/rfc0088-round12-consumer-shaped-residuals/spec.md); [RFC-0088 item 6 per-group amendment](../../rfc/0088-web-pilot-foundation.md)

## Outcome

RFC-0088 has the missing dated observations for signing-identity update survival and destination-group interactive sign-in cost.

## Opportunity

Present-run signing identity and tamper discrimination are measured, but update survival is unobserved; the attended three-arm destination measurement produced no discriminating authentication oracle.

## Boundary

This feature obtains or bounds evidence for the named signing and cost claims.
It does not amend RFC-0088, author delivery specifications, implement the
browser foundation, or treat an unresolved observation as settled.

## What this absorbs

### rfc0088-signing-identity-update-survival

The present run measures signing identity and tamper discrimination, but one installation cannot prove survival across a vendor update. `docs/rfc/0088-notes/spikes/2026-08-24-reference-consumer-observation.md:96` records that the item stays carried. **Unblocks when:** a second dated observation records the same system browser after a real vendor update.

### rfc0088-destination-group-split-cost

The reference-consumer spike was a null result because neither browser channel supplied a discriminating authentication oracle. `docs/rfc/0088-notes/spikes/2026-08-24-reference-consumer-observation.md:30` says no discriminating oracle could be established on either channel. **Unblocks when:** per-group interactive sign-in cost is measured on a destination class with a proven discriminating oracle.

## Assumptions

- **Riskiest assumption:** both open observations can be settled with dated live evidence: a real vendor update for signing survival and a proven discriminating authentication oracle for destination-group cost.
- **Knowledge surface:** In-repository RFC-0088, the round-12 residuals spec, dated reference-consumer observations, and workspace registration history.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
