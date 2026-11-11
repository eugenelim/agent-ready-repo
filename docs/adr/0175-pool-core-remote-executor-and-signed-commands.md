# ADR-0175: Pool core is a `remote` executor and public-key signed commands

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** security, orchestration
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0117 (the proposal this records); ADR-0164 (the foreground ferryman); ADR-0165 (neutral run contracts); ADR-0172 (levels and the approval invariant); ADR-0176 (provisional pool sub-choices); ADR-0177 (checkpoints and the restore step); ADR-0178 (relayed tracker signals); ADR-0181 (verified-human approve counts)

## Context

A pool runs many coding agents on remote nodes under a control plane. An environment allowlist does not protect a credential when the ferryman and the agent share an OS user or container. This rests on reasoning and is untested. The design must hold for one machine and for a pool, so the pool path may change only by configuration.

## Decision

We will run the ferryman and the agent in separate sandboxes in a pool, and the ferryman will accept only control commands signed by the control plane.

- **D1:** Four things change by configuration only: the executor kind, the verification level of control commands, the source of tracker signals (ADR-0178), and a restore step before the first `next` (ADR-0177).
- **D2:** A `remote` executor kind sits behind the generic worker interface (`spawn`, `status`, `cancel`, `result`). A remote profile names four list-form commands supplied by the control plane's transport.
- **D3:** A new level, `control-plane-signed`, is distinct from `host-attested`. A pool sets `accept = ["control-plane-signed"]` per gate.
- **D4:** The canonical signed bytes are fixed `name=value` lines after `ferryman-control-v1`: run id, epoch, command id, command name, the args hash (which carries the gate digest), nonce, expiry, and the actor issuer, subject, kind, auth method, authentication time and session id. A signed actor that differs from the control file refuses `signature-invalid`.
- **D5:** Ferryman verifies by running `ssh-keygen -Y verify` as a subprocess with `-n ferryman-run-control`, `-I` from committed configuration (never from the signed file), `-f` the provisioned allowed-signers file and a required `-r` revocation file. It uses an argument list with no shell and parses only the verified bytes. Page 10d D43 names a different namespace string, which the follow-on aligns.
- **D6:** Nodes hold only public keys, in an allowed-signers file that the ferryman sandbox cannot write. Bootstrap checks its digest against the value the control plane recorded at dispatch. The control plane keeps the private key.
- **D7:** A command expires at most 15 minutes ahead (a design default). The control plane's consumed-nonce set is authoritative, and the checkpoint carries a copy only.
- **D8:** (D70, a default) The work order carries deadline and budget. Ferryman enforces wall-clock time and records usage after the fact.
- **D9:** The pool agent-sandbox claim is a control-plane assertion carried signed in `launch.v1`, not an attestation of runtime state (RFC-0117 D7, page 11 footnote 6). Ferryman verifies the signature and refuses `pool-config-incomplete` when the claim is missing or stale.
- **D10:** The control plane, the scheduler and user authentication stay outside this repository.

## Consequences

**Positive:**
- One ferryman design serves a laptop and a pool.
- A courier between control plane and node can drop, delay or attempt a replay (refused by nonce), and cannot forge one.

**Negative:**
- A compromised control plane can sign any command. Key custody is its job.
- The signature path is untested. The `-r` option is unverified against the `ssh-keygen` manual page (RFC-0117 evidence 13), and the page states no failure status for verify.
- The sandbox claim trusts the control plane.
- Pool gates cannot pass until ADR-0181 is Accepted.

**Revisit if:** a container executor kind is scheduled, or `ssh-keygen -Y verify` proves unfit as a subprocess.

## Confirmation

- **Mode:** lint/CI
- **Signal:** an interface test runs all executor kinds, and a forged-command corpus of 12 shapes is refused: wrong key, expired, replayed, wrong digest, actor swapped, launch file substituted, wrong run or stale epoch, args hash changed, unknown or revoked key, signer not an approver, actor kind not user, and wrong namespace.
- **Owner:** eugenelim

## Alternatives considered

- **A per-run HMAC key:** it needs a secret channel to the node.
- **Vendored crypto:** it is a new dependency and needs its own ADR.
- **An environment allowlist and a shared user:** the credential stays reachable by the agent.

## References

- `docs/rfc/0117-approval-and-the-trust-model-for-unattended-delivery.md`
- `docs/architecture/unattended-delivery-runner/11-remote-agent-pool-seams.md`
- `docs/architecture/unattended-delivery-runner/01-contracts-and-data.md`
- `docs/architecture/unattended-delivery-runner/10c-review-decisions.md`
- `docs/architecture/unattended-delivery-runner/10d-folded-decisions-and-defaults.md`
