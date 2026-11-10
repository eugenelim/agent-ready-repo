# Brief: tracker-approved write-back, parallel worktrees and a remote pool

- **Slug:** `authority-and-scale-delivery`
- **Received:** 2026-11-07
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** [`docs/architecture/unattended-delivery-runner/`](../../architecture/unattended-delivery-runner/README.md), pages 06 (tracker integration and authority), 08 (worktrees and concurrency), 11 (remote agent pool seams), 12 (pool state integrity and signals) and 13 (phases P5, P6 and P7). The set is a Draft architecture, uncommitted at the time of writing.
- **Parent intent:** capability:mechanized-delivery

## Outcome

A team can let a tracker approval or a control plane's signed answer move a gate, mirror delivery status to its tracker under a bounded standing policy, run several slices in parallel worktrees on one machine, and run `ferryman` on nodes of a remote agent pool. The repository stays the only authority, and a lost node loses only the attempt.

## Success metrics

Not yet set. The architecture names tests: a forged-signal corpus, a pool corpus (forged command, fencing, duplicate dispatch across a park, lease, tamper before `start`, repeated effect), two specs in separate worktrees with no lock race, and a non-Studio host passing a conformance suite. These are candidates for the Ready review, not agreed metrics.

## Scope / Non-goals

In scope:

- P5: the standing write-back policy and tracker approval from a verified signal. The mirror is one-way and display-only: display status, comment, trace link and pull-request link, never closure and never field content.
- P6: per-slice and parallel worktrees on one machine, with an ownership transaction.
- P7: the pool contract shapes and signature fields, a `remote` executor, checkpoint push and restore, subject fence and claims, out-of-band digests, signed commands, relayed signals, and a host conformance suite.

Non-goals:

- The control plane, which is built separately.
- Continuous two-way sync, ticket creation, and importing by itself.
- Changes in the Studio repository, a generic command center, and concurrent attempts through `run-concurrent`.
- Anything in the first two briefs.

## Constraints / Appetite

Appetite is not set. Constraints from the architecture: approval from a tracker or a control plane counts only after the superseding ADR for ADR-0157 D4 is accepted, a pool node runs `ferryman` and the agent in separate sandboxes, and a pool cannot pass a gate until that ADR exists.

## Assumptions / Risks

- **Riskiest assumption:** a restored checkpoint passes the supervisor's own integrity checks on a real remote. A local test passed only when the restore reproduced the attempt fingerprint.
- **Risk:** approval from a relayed tracker signal shifts trust from the repository to the control plane, which can then forge a signal.
- **Risk:** a worker running as the same OS user can read host credentials. Credential stripping narrows it and does not remove it.
- **Risk:** a host cannot enforce a one-namespace remote on the tested tier (a credential is whole-repository, and rulesets are unavailable on a free private repository), so the control plane's own writer enforces the one namespace it writes. The owner decides that a checkpoint write is never a push under a run grant, because the merged run-grant spec excludes a one-namespace checkpoint remote from "push".

## Ready gaps (Draft only)

- Records 7, 8, 13 to 15 and 18 are not Accepted.
- Credential scoping against a real remote is untested.
- A follow-on request to the run-grant owners asks them to word the push exclusion by writer and repository instead of by host-side enforcement.
- A ruleset on a paid or public repository is not tested and not planned, because a separate checkpoint repository is the design either way.
- No control plane exists in this repository. Its contract is a seam only.
- A local pool, meaning several runs on one machine, is not designed or tested.
- Linear and Jira shims and a second host appear in the wave plan, and whether they belong to this brief is undecided.
- Success metrics and appetite are not set.

## Rabbit holes

- Do not design the control plane here. This brief writes the seams and conformance tests it must meet.
- Do not widen write-back past the bounded standing policy.

## Spec map

| Spec | Status |
| --- | --- |
