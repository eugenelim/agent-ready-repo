# Brief: tracker-approved write-back, parallel worktrees and a remote pool

- **Slug:** `authority-and-scale-delivery`
- **Received:** 2026-11-07
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** [`docs/architecture/unattended-delivery-runner/`](../../architecture/unattended-delivery-runner/README.md), pages 06 (tracker integration and authority), 08 (worktrees and concurrency), 11 (remote agent pool seams), 12 (pool state integrity and signals) and 13 (phases P5, P6 and P7). RFC-0117 (approval and the trust model) and RFC-0115 (mechanized delivery) are Accepted as of 2026-11-10, and the architecture set carries their design.
- **Parent intent:** capability:mechanized-delivery

## Outcome

A team can let a tracker approval or a control plane's signed answer move a gate, mirror delivery status to its tracker under a bounded standing policy, run several slices in parallel worktrees on one machine, and run `ferryman` on nodes of a remote agent pool. The repository stays the only authority, and a lost node loses only the attempt.

## Success metrics

The brief is measured by tests, and adopter numbers wait for the baseline the capability intent names: a forged-signal corpus, a pool corpus (forged command, fencing, duplicate dispatch across a park, lease, tamper before `start`, repeated effect), two specs in separate worktrees with no lock race, a mirror write outside the allowed set (a closure or a field-content edit) refused, and a conformance suite passing against a host.

## Scope / Non-goals

In scope:

- P5: the standing write-back policy and tracker approval from a verified signal. The mirror is one-way and display-only: display status, comment, trace link and pull-request link, never closure and never field content.
- P6: per-slice and parallel worktrees on one machine, with an ownership transaction.
- P7: the pool contract shapes and signature fields, a `remote` executor, checkpoint push and restore, subject fence and claims, out-of-band digests, signed commands, relayed signals, and a host conformance suite.

Non-goals:

- The control plane, which is built separately.
- Continuous two-way sync, ticket creation, and importing by itself.
- Changes in the Studio repository, a generic command center, and concurrent attempts through `run-concurrent`.
- Anything in `everyday-supervisors-delivery` and `ferryman-local-delivery`.

## Constraints / Appetite

Appetite is a stopping rule. Stop and replan if a restored checkpoint cannot pass the supervisor's integrity checks on a real remote, or if record 18 is not Accepted before P5 work begins. Otherwise the brief is done when its success tests pass. Constraints from the architecture: approval from a tracker or a control plane counts only once record 18, the ADR that supersedes ADR-0157 D4 in part, is Accepted, and a pool node runs `ferryman` and the agent in separate sandboxes. The owner decided that a checkpoint write is never a push under a run grant, because the merged run-grant spec excludes a one-namespace checkpoint remote from "push". The remaining task is a wording change to RFC-0113 and spec `run-grant`.

## Assumptions / Risks

- **Riskiest assumption:** a restored checkpoint passes the supervisor's own integrity checks on a real remote. The restore must reproduce the attempt fingerprint.
- **Risk:** approval from a relayed tracker signal shifts trust from the repository to the control plane, which can then forge a signal.
- **Risk:** a worker running as the same OS user can read host credentials. Credential stripping narrows it and does not remove it.
- **Risk:** a host cannot enforce a one-namespace remote on a free private GitHub repository (a credential is whole-repository, and rulesets are unavailable there), so the seam states an obligation that the control plane's own writer writes only the one namespace. The spec tests that obligation against the seam.
- **Open before P5:** the ADRs for records 7 (standing write-back policy), 8 (approval from a verified tracker signal) and 18 (a verified human's recorded approve counts) must be written and Accepted.
- **Open before P7:** the ADRs for records 13a to 15 (pool core, checkpoints, relayed signals) must be written, credential scoping against a real remote is untested, and the wording change to the run-grant push exclusion (by writer and repository) is still to be made.
- **Not tested or not designed:** a ruleset on a paid or public repository (not planned, since a separate checkpoint repository is the design either way), a local pool of several runs on one machine, and a control plane, which is a seam only.
- **Undecided:** whether Linear and Jira shims and a second host belong to this brief.

## Rabbit holes

- Do not design the control plane here. This brief writes the seams and conformance tests it must meet.
- Do not widen write-back past the bounded standing policy.

## Spec map

| Spec | Status |
| --- | --- |
