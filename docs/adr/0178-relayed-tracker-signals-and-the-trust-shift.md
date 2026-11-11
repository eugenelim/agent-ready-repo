# ADR-0178: Relayed tracker signals move trust to the control plane

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** security, orchestration
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0117 (the proposal this records); ADR-0168 (standing write-back policy); ADR-0169 (approval from a verified tracker signal); ADR-0172 (levels and the approval invariant); ADR-0175 (pool core and signed commands); ADR-0181 (verified-human approve counts)

## Context

In a pool, one tracker token feeds many nodes. A poller on each node would multiply the token's rate budget by the number of checkouts. The control plane can poll once or take webhooks. The ferryman on a node holds no tracker credential, so it cannot re-read the event.

## Decision

We will let the control plane poll or take webhooks in `relayed` mode and send the ferryman a signed `signal` command.

- **D1:** The control plane runs the six checks of ADR-0169 and sends a signed `signal` with an evidence bundle: tracker ref, event id, actor id, login and kind, tag, event time, prompt comment id and time, and the gate digest.
- **D2:** The control plane recomputes the gate digest from the repository at the parked commit. It never takes the digest from the relayed signal. (D25)
- **D3:** Ferryman verifies the signature and expiry. Without credentials it re-checks that the tag names the parked gate, that the bundle digest equals the gate digest, that the event follows the prompt time, and that the actor id resolves to the gate's approvers with kind `user`. It cannot check that the event exists or re-read the label, and the signature stands in for those two checks.
- **D4:** The attribution record stores `verification: control-plane-signed`, `relayed_by` and the whole bundle as evidence. (D28)
- **D5:** Tightening signals (hold, source-revision-drift, an unverified request-changes) relay too and need no actor verification.
- **D6:** Ferryman emits `mirror-requested` events. The control plane performs the mirror writes under the policy of ADR-0168, idempotent per request id.

## Consequences

**Positive:**
- Pool defaults need no tracker level, because the signature stands in for the two checks a node cannot make without a tracker credential.
- One poller serves the pool, so the rate budget holds.

**Negative:**
- A compromised control plane can sign a false approval, and the `control-plane-signed` level names that.
- Ferryman cannot catch a forged event that the control plane signs.
- GitHub event retention beyond a day is undocumented.
- The relay needs ADR-0169 and ADR-0175. ADR-0181 must be Accepted before the level counts as approval.

**Revisit if:** a node can verify an event without a tracker credential, or the control plane's key custody changes.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a forged-signal corpus of eight shapes (forged, replayed, wrong digest, wrong actor, actor swapped, tag off the gate, event before the prompt, bot actor) is refused.
- **Owner:** eugenelim

## Alternatives considered

- **Ferryman-side re-verification with a node token:** it multiplies the rate budget and puts a tracker credential on each node.
- **Node-reported digests as a recorded risk:** a node could report any digest.
- **Record the relayed signal as `tracker-verified`:** pool gates would also list a level that the node cannot check.

## References

- `docs/rfc/0117-approval-and-the-trust-model-for-unattended-delivery.md`
- `docs/architecture/unattended-delivery-runner/12-pool-state-integrity-and-signals.md`
- `docs/architecture/unattended-delivery-runner/10c-review-decisions.md`
- `docs/architecture/unattended-delivery-runner/10d-folded-decisions-and-defaults.md`
