# ADR-0169: A verified tracker label can approve one gate, and ticket drift parks the run

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** security, orchestration
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0117 (the trust model this records); ADR-0157 (parked gates); ADR-0168 (the mirror policy, which owns the label-prefix rule); ADR-0170 (the adapter seam); ADR-0172 (approval levels and the attribution record); ADR-0173 (the scribe); ADR-0174 (the pinned approver set); ADR-0181 (verified-human approve counts)

## Context

A human at a ticket should be able to answer a gate. A tracker label is still tracker content, and a false approval costs trust. A false pause costs only time. This ADR also holds the drift rule, because record 8 bundles tracker signals and ticket drift on purpose.

## Decision

We will count a tracker label as an approval or rejection only when the gate opts in and the verifier passes all six checks, and an approve counts only once ADR-0181 is Accepted. We will also park a run when a ticket's mapped fields change.

- **D1:** A verified label counts for one gate only when `ferryman.toml` lists `tracker-verified` for that gate. It is off by default, and an approve counts only once ADR-0181 is Accepted.
- **D2:** The verifier accepts only when all six checks pass. The label names the current parked gate. The latest event is `labeled` with no later `unlabeled`. The event is later than the prompt comment. The actor resolves through a committed identity table to the gate's approvers with kind `user`. The gate digest equals the digest in the prompt. A fresh read just before the scribe write still shows the label.
- **D3:** Only an actor with a numeric id counts. Page 06 allows a `login` fallback, and this ADR refuses it, so a renamed account cannot pass.
- **D4:** The verifier refuses an event whose actor is the mirror or poller token's own identity.
- **D5:** The prompt is bound to the comment id `ferryman` posted, and that comment's author id is checked (RFC-0117 D3, page 06).
- **D6:** A comment never counts. A reply is listed as `untrusted-reply`. The label-prefix rule that keeps mirror labels apart from authority labels is in ADR-0168 D2.
- **D7:** Tightening signals need no verified identity. These are hold, drift and an unverified `changes-requested`. An unverified `changes-requested` only parks as `untrusted-request-changes`, and the scribe revert needs a verified human.
- **D8:** A change to the mapped fields of the intent's ticket, or of a brief milestone's issues, parks the run as `source-revision-drift`. A label-only change does not. The refresh decision stays human.
- **D9:** Only a verified approve, `changes-requested` or `rejected` that the scribe applies, after ADR-0181, lands as one attributed `approval-attribution.v1` line. Tightening signals write no record.
- **D10:** In v1, `gh` runs as the owner, so `tracker-verified` is unreachable until a separate mirror or poller identity exists.
- **D11:** What v1 does with a verified label before ADR-0181 is Accepted is in ADR-0181 D5.

## Consequences

**Positive:**
- A forged, stale, bot or out-of-set signal leaves the gate parked.
- Ticket edits cannot change a run silently.
- Reversal removes the level from the accept list.

**Negative:**
- The path stays idle in v1.
- A team needs a second identity before it can use it.

**Revisit if:** the tracker's event data stops carrying a numeric actor id.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a forged-signal corpus shows that each of the six checks fails closed, including login-only, self-actor and forged-prompt-author shapes. A drift test shows that a label-only change does not park.
- **Owner:** eugenelim

## Alternatives considered

- **Treat a label as "please review" only:** a human at the ticket could not answer a gate.
- **Count comments as answers:** an edited comment keeps its author, so a comment is no proof.

## References

- `docs/rfc/0117-approval-and-the-trust-model-for-unattended-delivery.md`
- `docs/architecture/unattended-delivery-runner/06-tracker-integration-and-authority.md`
- `docs/architecture/unattended-delivery-runner/05b-approval-integrity-and-trusted-configuration.md`
