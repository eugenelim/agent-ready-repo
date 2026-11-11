# ADR-0168: Mirror writes to a tracker run under a standing bounded policy

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** security, orchestration
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0117 (the trust model this records); ADR-0169 (approval from a verified tracker signal, which relies on the label rule in D2); ADR-0170 (the tracker-adapter seam that runs the writes); ADR-0174 (the trusted configuration pin that covers the policy file)

## Context

Unattended mirroring cannot ask for a fresh confirmation on every tracker write. The repository stays authoritative, so a mirror write only shows status. It must never carry authority or worker text, and it must stay inside a fixed budget.

## Decision

We will let a repository opt in to unattended mirror writes through a `[authorization.mirror]` table in `.work-intake.toml`, and the processor will enforce that table before every tracker call.

- **D1:** `actions` is a subset of `display-status`, `comment`, `trace-link` and `pull-request-link`. It never lists closure. `comment_kinds` lists the allowed kinds from `prompt`, `mirror` and `question`.
- **D2:** `status_label_prefix` is the only label namespace the policy may touch. It must be disjoint from `approve:`, `changes-requested:` and `rejected:`, and the shim argument allowlist refuses authority labels. The policy never writes ticket fields or authority labels.
- **D3:** `max_writes_per_hour` defaults to 30 per repository per token. `max_retries` defaults to 1.
- **D4:** `decision_record` is an accepted ADR id. A policy without one is invalid.
- **D5:** A repository with no table keeps per-mutation confirmation. The rule narrows only for listed actions, and every other action still needs fresh confirmation.
- **D6:** Mirror comments use fixed templates only, so worker-derived text never reaches the tracker. A `question` comment carries only the gate, a ref, the digest and fixed prompt text.
- **D7:** No human-release exception exists. A human release would otherwise exempt a write from the fixed templates and the action list, and none does.
- **D8:** The processor checks policy before any call and binds the policy fingerprint into every receipt.
- **D9:** A failed mutation may retry as a new mutation with a new receipt. A mutation of unknown effect never retries and parks for the operator. `receipt_update_failed` is such a case.
- **D10:** Import and mirror are separate switches. Either works without the other.
- **D11:** `.work-intake.toml` is part of the trusted configuration set (ADR-0174).

## Consequences

**Positive:**
- Mirroring runs unattended, and its reach is listed in one file.
- A worker or the controller cannot widen what reaches the tracker.
- A retry never repeats an effect of unknown outcome.

**Negative:**
- Every comment kind needs a fixed template.
- The policy needs an accepted decision record before it is valid.
- The hourly budget is shared by every run on one repository and token.
- Mirror writes may disclose private spec text into a public tracker.

**Revisit if:** a tracker needs a mirror action outside the four in D1.

## Confirmation

- **Mode:** lint/CI
- **Signal:** an out-of-policy refusal test shows that closure is always refused, and a receipt-state test covers the no-retry rule for unknown effect.
- **Owner:** eugenelim

## Alternatives considered

- **Keep per-mutation confirmation:** unattended mirroring cannot work with it.
- **Let the worker or controller write freely:** worker text and authority labels could then reach the tracker.

## References

- `docs/rfc/0117-approval-and-the-trust-model-for-unattended-delivery.md`
- `docs/architecture/unattended-delivery-runner/06-tracker-integration-and-authority.md`
- `docs/architecture/unattended-delivery-runner/05b-approval-integrity-and-trusted-configuration.md`
