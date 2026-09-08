# RFC-0088 signing and destination-cost observations are complete

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/rfc0088-round12-consumer-shaped-residuals AC5](../../specs/rfc0088-round12-consumer-shaped-residuals/spec.md)
- **Authority:** [RFC-0088 item 6 per-group amendment](../../rfc/0088-web-pilot-foundation.md)

## Outcome

RFC-0088 has the missing dated observations for signing-identity update survival and destination-group interactive sign-in cost.

## Opportunity

Present-run signing identity and tamper discrimination are measured, but update survival is unobserved; the attended three-arm destination measurement produced no discriminating authentication oracle.

## What this absorbs

### rfc0088-signing-identity-update-survival

The present run measures signing identity and tamper discrimination, but one installation cannot prove survival across a vendor update. `docs/rfc/0088-notes/spikes/2026-08-24-reference-consumer-observation.md:96` records that the item stays carried. **Unblocks when:** a second dated observation records the same system browser after a real vendor update.

### rfc0088-destination-group-split-cost

The reference-consumer spike was a null result because neither browser channel supplied a discriminating authentication oracle. `docs/rfc/0088-notes/spikes/2026-08-24-reference-consumer-observation.md:30` says no discriminating oracle could be established on either channel. **Unblocks when:** per-group interactive sign-in cost is measured on a destination class with a proven discriminating oracle.

## Assumptions

- Both open observations need dated live evidence: a real vendor update for signing survival and a proven discriminating authentication oracle for destination-group cost.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
