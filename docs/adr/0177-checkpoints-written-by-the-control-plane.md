# ADR-0177: The control plane writes checkpoints, digests and claims

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** orchestration, security
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0117 (the proposal this records); ADR-0174 (the single-machine pin that D4 extends); ADR-0175 (pool core); ADR-0176 (provisional pool sub-choices); ADR-0180 (run grant, which cites D3)

## Context

A pool run must survive a change of node. The run store and the product ref are local to one clone, and a default clone does not fetch `refs/ferryman/*`. A fresh clone has no supervisor pins, so the first `start` pins whatever it finds. A shared checkpoint credential would let one node rewrite another run's state.

## Decision

We will keep run state in checkpoint refs that only the control plane writes.

- **D1:** (D24) Checkpoints are refs under `refs/ferryman/checkpoints/<run-id>/` in a dedicated checkpoint repository. They carry an epoch, a counter that makes a stale writer's push fail, and a restore step. Each checkpoint writes exactly three refs: head, product and store.
- **D2:** (D45, revised) A node returns a bundle (head, product, store content, manifest) at each boundary with no open attempt. The control plane validates it against the manifest and writes the refs with `git push --atomic` and a `--force-with-lease` per ref, and ferryman calls `next` only after the write is acknowledged. A node holds no checkpoint credential, so no host push audit is needed.
- **D3:** (D57, decided by the owner 2026-11-10) A checkpoint write is never a push under a run grant.
- **D4:** The control plane supplies expected supervisor digests at launch, so a fresh clone does not pin whatever it finds.
- **D5:** (D26) Claims ship in P7. Pool-mode claims do not expire, and only the control plane releases them, at terminal or abandon.
- **D6:** (D47) The control plane serialises intake ordinals per repository across clones.
- **D7:** (D48) Times are absolute, with a stated maximum clock skew of 60 seconds. Signed-command expiry needs node clock sync, and worker leases use durations.
- **D8:** A restoring node never copies a recorded `.git/config`. Before any Git command runs, it writes the file from a fixed template that denies `include*`, `credential.*`, `core.sshCommand`, `core.fsmonitor`, `core.hooksPath`, `filter.*`, `diff.*` and any unlisted key. `launch.v1` pins the template digest.

## Consequences

**Positive:**
- One node cannot rewrite another run's checkpoint.
- A stale writer fails on the lease. Atomic pushes with per-ref leases fenced a stale writer on a real host (tested, single run, 2026-11-08).
- A node that is lost mid-attempt loses only the work after the last written checkpoint.
- A hostile recorded config was dropped in a local restore test (single run, 2026-11-07).

**Negative:**
- The control-plane writer, the bundle validation and the acknowledgment before `next` are not built or tested.
- A host cannot enforce a one-namespace remote on the tested tier, so the control plane's writer enforces the namespace.
- D5 is provisional. The duplicate-dispatch trial for claims is a plan, not a result.

**Revisit if:** a host offers enforceable namespace scoping, or the P7 gate changes the claim rule.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a push-scope test shows a node without a checkpoint credential cannot write the checkpoint repository. Restore tests run against the real supervisor, including a hostile-config restore case. A tamper-before-`start` test refuses `supervisor-digest-mismatch`.
- **Owner:** eugenelim

## Alternatives considered

- **Per-run credentials:** one repository per run, which is unverified on a free tier.
- **Control-plane observations only:** the weakest integrity basis.
- **A documented restart on the branch:** the run refuses with `checkpoint-conflict` and loses state.
- **Control-plane assignment only, with no claims:** a subject-keyed fence is required before `start` in pool mode.

## References

- `docs/rfc/0117-approval-and-the-trust-model-for-unattended-delivery.md`
- `docs/architecture/unattended-delivery-runner/12-pool-state-integrity-and-signals.md`
- `docs/architecture/unattended-delivery-runner/10c-review-decisions.md`
- `docs/architecture/unattended-delivery-runner/10d-folded-decisions-and-defaults.md`
