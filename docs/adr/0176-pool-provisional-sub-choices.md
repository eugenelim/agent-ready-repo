# ADR-0176: Pool sub-choices stay provisional until the P7 gate names them

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** security, orchestration
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0117 (the proposal this records); ADR-0174 (the trusted configuration pin); ADR-0175 (pool core, the parent decision); ADR-0177 (checkpoints and claims)

## Context

ADR-0175 decides the pool core. Seven sub-choices under it were recorded with the parent and not walked separately. This ADR stays Proposed until the P7 gate names each choice. Each choice below is provisional. The pool core proceeds, and its forged-command corpus assumes the D44 field set until the P7 gate names it.

## Decision

We will record seven provisional pool sub-choices, one per constraint, and confirm each at the P7 gate.

- **D1:** (D44) Signed answers carry authenticated-human claim fields. The control plane must never sign an answer without a human act.
- **D2:** (D46) The agent sandbox has gateway-only egress to the model endpoint with a per-attempt model token, and a work-tree copy with no Git credentials. The sandbox claim itself is decided in ADR-0175.
- **D3:** (D55) Sandboxes that hold a key or a credential execute only digest-pinned `executed_paths`. Until the P7 gate names this, a post-guard step that runs repository or patch code refuses `execution-boundary-unset`.
- **D4:** (D68) This is the part RFC-0117 D4 leaves provisional: a committed `[pool]` table applies only when `mode = pool`. Signer principals and the allowed-signers home are decided in ADR-0175.
- **D5:** (D69) External effects park for a human in a pool until a control-plane effect path exists.
- **D6:** (D71) The control plane merges only on a recorded human merge decision.
- **D7:** (D73) `launch.v1` carries the digest of the distribution's file-hash record. The control plane has a duty to verify image integrity.

## Consequences

**Positive:**
- Each unsettled choice has a safe default that refuses or parks.
- The pool core can proceed without waiting on these choices.

**Negative:**
- Until the P7 gate, a pool cannot run a step after the guard that executes repository or patch code.
- Effects in a pool need a human.
- The egress rule depends on a control-plane gateway that is not built.

**Revisit if:** the P7 gate names a choice (that choice leaves this record), or a sandbox provider offers a client-verifiable runtime measurement.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** at the P7 gate each of D1 to D7 is named or replaced, and a reviewer confirms a pool test shows `execution-boundary-unset`.
- **Owner:** eugenelim

## Alternatives considered

- **D1:** attest a named human only.
- **D2:** open egress as a recorded accepted risk.
- **D3:** run `report` in a third sandbox with no key, or accept the risk.
- **D4:** widen the launch-settable list as a stated exception, or use separate repository configs.
- **D5:** the control plane performs effects, or a scoped per-effect credential.
- **D6:** the control plane only pushes a branch or opens a pull request.
- **D7:** a build provenance attestation.

## References

- `docs/architecture/unattended-delivery-runner/10d-folded-decisions-and-defaults.md`
- `docs/architecture/unattended-delivery-runner/11-remote-agent-pool-seams.md`
- `docs/rfc/0117-approval-and-the-trust-model-for-unattended-delivery.md`
