# RFC-0088 exposure and cross-round term identity are evidenced at their stated boundaries

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0088](../../rfc/0088-web-pilot-foundation.md)

## Outcome

RFC-0088's browser-endpoint exposure and cross-round term identity claims have evidence at their stated boundaries.

## Opportunity

Current evidence indicates the unauthenticated loopback TCP browser endpoint may expose a wider actor set than the same-UID exposure accepted in disposition B, while cross-chain term identity remains operator-trusted.

## What this absorbs

### rfc0088-same-uid-attach-exposure

The browser endpoint is unauthenticated loopback TCP and current evidence indicates an actor set potentially wider than same-UID, while accepted disposition B remains narrower. The unverified accepted exposure is that another same-UID process can attach to the browser endpoint. This host cannot create the required second-UID control without administrator authority. Re-rule the exposure with an approver-authorized runnable second-UID mechanism or a non-administrative isolation boundary, or equivalent evidence.

### rfc0088-privacy-term-identity-anchor

Cross-round term identity must be anchored by something other than operator trust. Round 13 closed same-file identity within a gate chain with a keyed HMAC. Across chains, identity remains operator-trusted, so this is bounded rather than closed. Unblocks when: cross-round term identity is anchored by something other than operator trust.

## Assumptions

- The authority is recorded as RFC-0088 without a decision identifier on
  purpose. The retired entry cited "rfc/0088 disposition B", and no such
  decision id occurs in the RFC body -- the nearest match is the disposition
  block in `docs/rfc/0088-notes/round13-consolidated-evidence-digest.md`.
  Naming a decision that does not exist would be worse than naming none.

- A dated, authorized second-UID or equivalent non-administrative boundary experiment would settle the browser-endpoint exposure.
- Readable RFC/spec evidence or a recorded cross-chain identity mechanism would settle the cross-round term-identity question.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
