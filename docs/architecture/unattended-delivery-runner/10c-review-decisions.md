# Architecture Change — Owner decisions

**Decision sought:** Confirm the 26 owner decisions that the owner decided on 2026-11-07.

Seventy-six decision numbers collapse into 26 owner decisions, and all 26 are decided. Three points carry the page:

- Thirty-one facets are folded into a parent decision as sub-options, on [page 10d](10d-folded-decisions-and-defaults.md).
- Eighteen implementation details take a safe default unless the owner objects, also on page 10d. D2 is superseded by D30.
- [Page 10b](10b-decision-triage.md) classifies every number and gives the order.

**Author(s):** Repository owner (draft)
**Status:** Draft
**Last updated:** 2026-11-07
**Reviewers:** Repository owner

**Baseline — current architecture:** [Decisions and records](10-decisions-and-records.md) owns the alternatives, the records, and the adjacent work.

## 1. Scope and Baseline

This page holds the decisions only. D-numbers stay stable, and a merged decision reads "folded into Dn" and sits on page 10d, as D35, D43, D57, and D58 do.

| Delta item | In scope | Why it is here |
| --- | --- | --- |
| The 26 owner decisions | yes | One owner can review 26 in a sitting |
| Folded facets and defaults | no | [Page 10d](10d-folded-decisions-and-defaults.md) |
| Class, gate, and order | no | [Page 10b](10b-decision-triage.md) |

| Unchanged context | Link |
| --- | --- |
| Records and phases | [page 10](10-decisions-and-records.md), [page 13](13-rollout-spikes-and-risks.md) |

## 2. Structural Change

None.

| Element | Change type | Owner |
| --- | --- | --- |
| none | n/a | n/a |

## 3. Runtime Change

None.

| Scenario | Change type | Baseline reference |
| --- | --- | --- |
| none | n/a | n/a |

## 4. Contract and Invariant Change

All 26 owner decisions are decided (2026-11-07).

**Decided.** Each row is decided as the owner chose, and its record carries the text once it exists.

| # | Decision | Decided as | Not chosen | Record |
| --- | --- | --- | --- | --- |
| D1 | Foreground ferryman under `packages/` | It fits Charter Principle 3, with no daemon, port, or registry | Shape C: contracts and supervisors only, and hosts own the loop | 1 |
| D3 | Discovery front door (class 2, gates E2) | Two doors, with discovery optional. `intent frame` stays standalone and writes a plain intent, and `discovery-loop` is the door for raw ideas and tickets that need shaping. The discovery supervisor covers only initiatives that have a sidecar. Until `discovery-supervisor` ships (E2), a ticket becomes an intent through manual `work-intake`. `discovery-supervisor` is optional and no dependency of `spec-supervisor`. The short route (`intent frame`, `intent de-risk`, `intent decompose`) stays in the intent skill, with progress in the intent's headers and no supervisor. State lives in the initiative's own directory under the resolved discovery root (config, then `docs/discovery/` in a repository or `.context/discovery/` outside one, then discovery by marker), never at the install home. The discovery-supervisor and `ferryman` are an optional layer in repository mode or tier B (D9). Cross-repository initiatives live in a coordinating repository (`align-value-stream`), `ferryman` v1 works in one checkout, and a ticket in another repository is unsupported in v1. Known limits: a supervised run is one per checkout per subject, no cross-root list of parked discoveries exists, and no supervision exists outside Git except tier B (D9). Sub-options: D16 (see [page 10d](10d-folded-decisions-and-defaults.md)) | `discovery-loop` as the single door, so standalone `intent frame` becomes its first step (`start --through G0`) | 3 |
| D4 | Spec phase home | A sibling spec-supervisor, shipped as a new `core` skill (D63) | `ferryman` drives spec authoring with no supervisor, or the discovery-supervisor absorbs it | 4 |
| D5 | Discovery supervisor's record | A new RFC supersedes RFC-0053's no-engine constraint in part | An extension with no RFC | 21 |
| D6 | Standing write-back | `[authorization.mirror]` allows `display-status`, `comment`, `trace-link`, `pull-request-link`, never `closure`, with a cited record, 30 writes an hour per repository per token | Per-mutation confirmation, or allow `closure` | 7 |
| D7 | Tracker labels approving a gate | A verified label may approve a gate, off until a repository enables the gate by name, under the six checks, and it needs record 18 (D22, D35, D42) | A label means "please review" only | 8, 18 |
| D8 | Tracker access path | A per-pack shim CLI reusing the existing adapters | A ferryman-owned `gh` argv builder, or an agent following `work-intake` | 9 |
| D9 | Discovery state location | Supervised discovery may keep local-only state in `.context/discovery/` (tier B), next to the committed tier A ([page 03c](03c-run-chain-locks-and-process-boundary.md)). Decided sub-rules: tier B refuses pool mode and any level but `session-attested` | Require repository-mode `docs/discovery/` for supervised runs | 3 |
| D10 | Ordering default | Default `ask`, an optional ordering policy, and the frontier ignores `Priority:` | Read `Priority:` and amend `lint-priority-field.py` | 5 |
| D14 | Gate scribe location | A ferryman-owned scribe inside `ferryman`, the one non-supervisor committer, covered by the guard (D18). The `spec-loop` copy of `approval-fields.v1` is authoritative, because `spec-loop` ships first, and `ferryman` adopts it | The siblings own approval writes, with a second guard home | 11 |
| D15 | v1 verification levels | `session-attested` (the terminal prompt) only, `ferryman answer` refused by default, other levels per gate after record 18 (D20, D21, D65, D74) | A per-run secret outside the worker environment, or separate verbs per gate kind | 11, 18 |
| D17 | Branch deletion | `ferryman` deletes only an untouched branch it created, by compare-and-delete with its marker. `clean` deletes other `ferryman/*` branches only per branch, after a confirmation that shows the unmerged commit count | Marker-only rollback, so no branch is deleted | 12 |
| D23 | Config-to-approval escalation | Pin the trusted configuration set per run and refuse on change (D29). A separate OS user or container stays an opt-in profile mode for later | Run workers as another OS user or in a container now | 12 |
| D24 | Portable run state for a pool | Atomic checkpoints under `refs/ferryman/checkpoints/<run-id>/` with leases and a restore, and a lost `checkpoint-pushed` event reconciled from the `store` ref (D26, D47, D72) | A documented restart on the branch, refusing with `checkpoint-conflict`, or store commits in a parent chain | 14 |
| D25 | Relayed tracker signals | Accept a signed `signal` with an evidence bundle, and the control plane recomputes the gate digest from the pushed head (D28) | Ferryman-side re-verification with a node token, or node-reported digests as a recorded risk | 15 |
| D27 | Pool node trust | Separate sandboxes, public-key signed commands, level `control-plane-signed`. D43 is decided and D44, D46, D55, D68, D69, D71, and D73 stay provisional sub-choices, all on [page 10d](10d-folded-decisions-and-defaults.md) | An environment allowlist and a shared user | 13 |
| D30 | Controller name | `ferryman`, decided.[^1] | none | none |
| D31 | Brief-scoped ordering | Delegated to the brief-level runner's `next` from a clean base checkout, and v1 takes an explicit subject (D32, D34) | Own derivation everywhere | 17 |
| D36 | Concurrent attempts | No phase depends on `run-concurrent`, so sequential stays the floor | Amend ADR-0156 for a launcher-provided gateway | 16 |
| D37 | Review round cap | `max_review_rounds` defaults to 3, then a consent gate names the open findings | A different cap, or none | 4 |
| D45 | Checkpoint credential scope (revised) | The control plane pushes checkpoints and a pool node holds no checkpoint credential: the node returns a bundle at each boundary with no open attempt, and the control plane validates it and writes the refs to a dedicated checkpoint repository with `git push --atomic` and per-ref leases. The shared-credential risk is removed for pool nodes, and no host push audit is needed (D48, D57, [page 12](12-pool-state-integrity-and-signals.md)).[^3] | Per-run credentials (one repository per run on a free GitHub tier), or control-plane observations only (the weakest) | 14 |
| D50 | Distribution channel | PyPI, an isolated tool install, and the clone path, with the name re-checked before the first publish (D51, D53) | Clone-only, or vendoring into `agentbundle` | 19 |
| D56 | Brief-level runner requests | `next` carries `schema_version`, `base`, and spec paths, and the merged runner does[^2] | none | 17 |
| D59 | v1 single-checkout policy | Refuse the default branch, a dirty tree, and a mid-run branch switch, with named codes (sub-option D58, as revised on [page 10d](10d-folded-decisions-and-defaults.md)) | Allow runs on the default branch | none |
| D67 | P0 contract scope | P0 ships the minimal contracts (D33), and pool shapes and signature fields ship at P7 | Gate D43, D44, D48 and the D45 and D47 launch fields at P0 | none |
| D75 | Light mode in v1 (class 2, gates PL, decided 2026-11-07) | A supervisor-less session route of `ferryman`: `ferryman session [--ticket <ref>] <prompt-or-request-file>`, one worker, no spec and no plan, the result left as an uncommitted tree plus a `product` checkpoint ref, no resume, no pool, and the human publishes. The frontier only lists `light_candidates` ([page 05](05-supervisors-and-gates.md)) | Model triage and a first-class light route with a spec supervisor refusal and an automatic full restart | 22 |

## 5. Data/State Migration

None.

| Data element | Old shape | New shape | Migration mechanism | Rollback |
| --- | --- | --- | --- | --- |
| none | n/a | n/a | none | none |

## 6. Deployment/Operational Change

None.

| Deployment unit | Change type | Baseline reference |
| --- | --- | --- |
| none | n/a | n/a |

## 7. Quality Regression and Verification

None beyond [page 13](13-rollout-spikes-and-risks.md).

| Attribute at risk | Baseline target | Stimulus that could regress it | Verification |
| --- | --- | --- | --- |
| none | n/a | n/a | n/a |

## 8. Build Mapping

None.

## Evidence

[^1]: Candidates weighed for the name: `loop-runner` (generic, collides with ADR-0159's brief-level runner), `loop-driver` (collides with an existing npm package for agent-loop extensions), `bosun`, `coxswain`, `gangway` (existing agent tools), `charon` (taken on PyPI and npm, and strongSwan's IKE daemon), `lighterman` (the free alternative). PyPI and npm name lookups of 2026-11-07 — assumption: not reproduced here, because a PyPI fetch was blocked by a client challenge.

[^2]: `references/brief-runner.md` and `scripts/brief-runner.py` (`NEXT_SCHEMA_VERSION`, `spec_path`, `spec_paths`) — verified (read, merged, core 4.0.22).

[^3]: A free private repository offered no push audit for custom refs and no ref-namespace scoping, and atomic push with lease fencing worked on a real host — verified (tested, single run, 2026-11-08; [page 12](12-pool-state-integrity-and-signals.md)). One repository per run on a free tier: assumption.
