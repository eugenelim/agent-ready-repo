# Architecture Change — Decisions, alternatives, and records

**Decision sought:** Record the alternatives, the adjacent work, and the twenty-one ADR-worthy design choices and one RFC this set implies, and record the 26 owner decisions made on 2026-11-07 on [page 10c](10c-review-decisions.md).

The seven decisions on the decide-first list of [page 10b](10b-decision-triage.md) are decided, so P0 waits only for records 11 and 12. Three choices carry it:

- Shape A keeps all procedure in supervisors, so no pinned script changes.
- Every open call has a recommendation and a strongest alternative.
- The records list says which decision needs which record.

**Author(s):** Repository owner (draft)
**Status:** Draft
**Last updated:** 2026-11-07
**Reviewers:** Repository owner

**Baseline — current architecture:** The pages named in the [set index](README.md). This page owns alternatives, owner decisions, and the record list. [Page 13](13-rollout-spikes-and-risks.md) owns rollout, spikes, and risks.

## 1. Scope and Baseline

This page holds the alternatives and the records, and it reopens no prior decision.

| Delta item | In scope | Why it is here |
| --- | --- | --- |
| Open owner decisions with a recommendation and the strongest alternative | yes | Judgment calls belong to the owner |
| Alternatives for the whole shape | yes | One structurally different whole shape is required |
| Record list (ADRs and an RFC) | yes | One place to route the records |

| Unchanged context | Link |
| --- | --- |
| Prior decisions treated as fixed | [ADR-0062](../../adr/0062-workspace-mcp-per-session-only-constraint.md), [ADR-0144](../../adr/0144-work-loop-supervisor-owns-procedure.md), Charter Principle 3 |

Section 4 states each difference from a prior record and leaves the record in force.

## 2. Structural Change

Shape A is chosen, and five other whole shapes each fail on a stated property.

| Shape | Description | Verdict |
| --- | --- | --- |
| A. Foreground ferryman plus sibling supervisors | A stateless ferryman drives generic JSON commands, new supervisors sit beside the pinned one, and contracts are neutral | Chosen |
| B. Extend `work-supervisor.py` to own every phase | One supervisor holds discovery, spec, and execution state | Needs an edit to a pinned script, which voids runs ([ADR-0144](../../adr/0144-work-loop-supervisor-owns-procedure.md)). The supervisor holds no pre-approval state by design |
| C. Ferryman lives in the host repository only | This repository ships contracts and supervisors, and a host ships the loop | Strongest alternative (D1). It keeps the repository free of a `ferryman` process and puts the loop where daemons already live. A team with no host has no unattended path, and each host reimplements the controller |
| D. Persistent daemon with a run registry | One service watches trackers and runs many specs | Excluded by [ADR-0062](../../adr/0062-workspace-mcp-per-session-only-constraint.md) and Charter Principle 3 until a charter decision |
| E. Agent-only controller, no ferryman | A long-lived agent session loops by instruction ([unattended loops](../../../packs/core/.apm/skills/work-loop/references/unattended-loops.md)) | It has no durable stop rule, and that reference limits the pattern to mechanical completion criteria |
| F. Model triage and a first-class light route | A model triages each ticket, writes a `mode-decision`, and a supervisor-driven light session follows | Rejected: nothing commits the work, a model verdict replaces the only human check, and a stateless controller cannot resume it. Light mode is a human-launched session route instead (D75, record 22) |

## 3. Runtime Change

[Page 09](09-flow-ticket-to-merged-spec.md) and [page 03](03-ferryman-runtime.md) own runtime behaviour.

## 4. Contract and Invariant Change

The owner decisions are on [page 10c](10c-review-decisions.md), with folded sub-options and defaults on [page 10d](10d-folded-decisions-and-defaults.md).

| Semantic name | Change type | Baseline reference | Compatibility during transition | Enforcement | Verification |
| --- | --- | --- | --- | --- | --- |
| Whole set | additive | [set index](README.md) | no baseline script changes, so every existing run and every non-ferryman caller behaves as before | no edits to pinned scripts; manifests and policy tables optional | existing supervisor suites stay green; the three tools pin suites run before any push |

**D35 consequences (D35 is folded into D7).** The new ADR changes what each approval level does. Under route (a), v1 ships `session-attested` only, and the other levels count after the ADR is Accepted.

| Level or gate | Under route (a), decided |
| --- | --- |
| `session-attested` | counts as the named human's approve, and the scribe writes `Status` as the approver's recorded delegate |
| `host-attested` | counts after the ADR is Accepted |
| `tracker-verified` | counts after the ADR is Accepted |
| `control-plane-signed` | counts after the ADR is Accepted, so a pool can pass a gate |
| Phases P5 and P7 | gated on the ADR |

The new ADR leaves ADR-0157 D1 to D3 and D5 to D7 untouched, and the baseline wording stays that the approver writes the status.[^1] Its Supersedes-in-part line goes in now, and the back-pointer lines on ADR-0157 follow only after the new ADR is Accepted. ADR-0157 is Accepted and on main.[^2]

ADR-0159 D10 and RFC-0113 pin RFC-0099 section 7 and ADR-0157 D4's no-default rule. The new ADR keeps those guarantees: no approval is removed or inferred. The repository owner holds those records and confirms them when record 18 is accepted.

Adjacent work this set reconciles with. Every item below is on main.[^3]
- ADR-0159 (Accepted, on main, core 4.0.22): a read-only script derives the next ready slice from the Spec map and `dispatch.py` and names `start-slice`, `resume-slice`, `await-gates`, `await-merge`, `complete`, or `blocked`. Slices get linked worktrees on `brief/<brief-slug>/<spec-slug>`, gates are joined per slice worktree (D4), standing orders are one committed file per brief (D6), and heartbeat, stuck-after runtime, and retry budget are lease policy in `supervisor-policy.json` (D8).
- RFC-0113 (Accepted, on main): a committed, optional run grant bounds an unattended run per brief, only narrows what the run would do, and carries no authority. Human merge authority and the `spec-approved` and `plan-approved` gates stay as they are. Spec `run-grant` (Shipped, core 4.0.28) puts it in `docs/product/run-grants/<brief-slug>.toml` with the keys `schema_version`, `brief`, `confirmed_by`, `confirmed_at`, `expires_at`, `done_when`, `slices`, `retry_budget`, `max_slices_in_flight` and `held_actions`.[^4]
- ADR-0157 D4: no verb, flag, default, or record turns a parked gate into an approval.
- ADR-0156 and ADR-0160: concurrent attempts run in host-contained plain directories, and the `run-concurrent` request kind and blocking verb are on main (Slice 7, core 4.0.27 to 4.0.29) with `concurrency` shipped `sequential` and no attesting launcher shipped.[^5] [Page 03](03-ferryman-runtime.md) owns how `ferryman` handles it.

Adjacent Accepted intents under `docs/product/intents/` to update when the records are Accepted.[^7]

| Intent | Overlap |
| --- | --- |
| `tracker-refresh-trusted-authority-inputs` | "No defaulted parameter or tracker-derived value may stand in for authority" conflicts with `tracker-verified` approval (record 18) |
| `work-loop-delivery-efficiency` | Its boundary bars a procedure-engine rewrite and arbitrary round caps, which D37's cap touches |
| `CAP-0004-external-tracker-projection`, `FEAT-0011`, `FEAT-0012`, `FEAT-0013` | Tracker projection family: add a child for the GitHub adapter and approval signal |
| `loop-state-lock-cross-spec-serialization` | Locks for runs on different specs, below the subject lock on page 03c |
| `supervisor-launch-routing-for-plan-authored-commands` | Bounded environment for launched commands, next to `executed_paths` on page 05b |
| `agent-loop-escalation-recovery` | A review loop that stops converging, next to D37 |
| `workspace-mcp-production-readiness` | The status surface, next to page 07 |
| `role-journey-agent-swarm-section` | The headless CLI swarm guide, next to page 14 |
| `agentbundle-install-integrity`, `installed-skill-governance-inventory` | Install integrity, next to pages 14 and 02 |
| `credential-pack-defaults-projection` (RFC-0112) | An installer projection of catalogue defaults, to evaluate before D52 on page 14 |
| A new capability intent for the unattended controller | Parent `opportunity:autonomous-product-team-operating-model` (of `CAP-0012`), to confirm at intake |

Records this set implies. Records 11 and 13 are each split in two, so the plan is 23 ADRs and RFC-0116, and a reference to record 11 or 13 means both parts:

| # | Record | Subject | Page |
| --- | --- | --- | --- |
| 1 | ADR | Foreground ferryman under `packages/`, controller split (D1) | [03](03-ferryman-runtime.md) |
| 2 | ADR | Neutral run-state, event, and control contracts | [01](01-contracts-and-data.md) |
| 3 | ADR | Sibling supervisors and the command contract | [05](05-supervisors-and-gates.md) |
| 4 | ADR | Spec supervisor as a sibling, shipped inside `new-spec` (D4) | [05](05-supervisors-and-gates.md) |
| 5 | ADR | Frontier in `ferryman`, explicit ordering policy | [04](04-frontier-and-waves.md) |
| 6 | ADR | Worktree ownership transaction and peer layout for run and slice worktrees, v1 sequential. ADR-0160 already supersedes ADR-0005 D7 for concurrent-attempt directories | [08](08-worktree-and-concurrency.md) |
| 7 | ADR | Standing bounded write-back policy (D6). No existing ADR covers a recorded standing policy[^6] | [06](06-tracker-integration-and-authority.md) |
| 8 | ADR | Approval and rejection from a verified tracker signal, and drift parking (D7) | [06](06-tracker-integration-and-authority.md) |
| 9 | ADR | Tracker-adapter seam, reuse of pack adapters over an own HTTP client (D8) | [06](06-tracker-integration-and-authority.md) |
| 10 | ADR | Repository copy of supervisors, state-file detection, installer separation, confined file handling. The version rule lives in record 19 | [02](02-install-trust-and-detection.md) |
| 11a | ADR | Approval invariant, the four approval levels, approval attribution record, approval-fields contract, and the delegate reading for `session-attested` (D14, D15, D18) | [05b](05b-approval-integrity-and-trusted-configuration.md) |
| 11b | ADR | Gate scribe with write-ahead intent and recovery, and the rejection route (D14, D21) | [05b](05b-approval-integrity-and-trusted-configuration.md) |
| 12 | ADR | Trusted configuration set pinned per run, and the push and branch-delete allowlist (D17, D23) | [05b](05b-approval-integrity-and-trusted-configuration.md) |
| 13a | ADR | Pool core: the `remote` executor kind and worker interface, signed commands, the `control-plane-signed` level, usage fields (D27, D43) | [11](11-remote-agent-pool-seams.md) |
| 13b | ADR | Pool provisional sub-choices, Proposed until the P7 gate names each: human assertion, sandbox credentials and egress, execution boundary, launch-file layering, pool effects, merge ownership, image integrity (D44, D46, D55, D68, D69, D71, D73) | [11](11-remote-agent-pool-seams.md) |
| 14 | ADR | Checkpoint namespace, control-plane writes, out-of-band digests, claims (D24, D26, D45, D47, D48) | [12](12-pool-state-integrity-and-signals.md) |
| 15 | ADR | Relayed tracker signals and the trust shift (D25) | [12](12-pool-state-integrity-and-signals.md) |
| 16 | ADR | Concurrent attempts: `ferryman` handles `run-concurrent` as a blocking verb, and the pinned launcher is trusted configuration (D36) | [03](03-ferryman-runtime.md) |
| 17 | ADR | Reconciliation with the brief-level runner and run grant (D30 to D34) | [04](04-frontier-and-waves.md) |
| 18 | ADR | A recorded answer that carries a verified named-human approve through an enumerated channel counts as that human's approve, superseding ADR-0157 D4 in part. Number assigned when written, status Proposed until accepted (D35) | [05b](05b-approval-integrity-and-trusted-configuration.md) |
| 19 | ADR | Distribution channel and the one version and compatibility rule for `ferryman`; record 10 points here (D50, D51, D53) | [14](14-installation-and-adoption-experience.md) |
| 20 | ADR | Configuration provenance and the first-run consent display, stating that the consent file is not a security boundary (D52, D54) | [14](14-installation-and-adoption-experience.md) |
| 21 | RFC | Discovery supervisor, superseding RFC-0053's no-engine constraint in part (D5) | [05](05-supervisors-and-gates.md) |
| 22 | ADR | Supervisor-less session route (D75) | [05](05-supervisors-and-gates.md) |

RFC-0053 gets its mirror lines and errata only after the new RFC is Accepted.

Differences from prior records, each left in force:

- RFC-0053 D1 says no engine, and the discovery supervisor is a deterministic script. RFC-0053's reason is that manager agents thrash, and this supervisor routes by file state.
- `work-intake` says tracker content is never authorization evidence. [Page 06](06-tracker-integration-and-authority.md) narrows that for gate answers only.
- The `unattended-loops` reference warns against hand-rolled CLI loops. `ferryman` loops over supervisor commands with a stop rule.
- ADR-0157 scopes parked gates to one checkout and names a multi-worktree ferryman as its revisit trigger. The session route parks no gate and engages neither ADR-0157 nor the approval invariant.

## 5. Data/State Migration

No existing state moves.

| Data element | Old shape | New shape | Migration mechanism | Rollback |
| --- | --- | --- | --- | --- |
| All new state | none | per-page tables | none | per-page rollback |

The only ordering hazard is `[authorization.mirror]`: it stays absent until ADR 7 is Accepted, because a policy needs a cited decision record to be valid.

## 6. Deployment/Operational Change

The rollout, the probe and restore spikes, reversal, and window owners are on [page 13](13-rollout-spikes-and-risks.md).

## 7. Quality Regression and Verification

[Page 13](13-rollout-spikes-and-risks.md) owns the risks.

## 8. Build Mapping

Each page's build mapping covers its elements, and the set-level table is in the [index](README.md).

## Evidence

[^1]: `work-loop/references/pre-execute-review.md` lines 220 to 221 ("the spec approver writes `Status: Approved` in `spec.md`"), `supervisor.md` lines 57 to 58, and ADR-0157 D4 — verified (read).

[^2]: ADR-0157 status Accepted (its header) and merged to main (commit `4c7f17e12`, #1690, core 4.0.16) — verified by reading the ADR and `git log`.

[^3]: ADR-0159, `references/brief-runner.md`, and `scripts/brief-runner.py` read on main; the spec `docs/specs/brief-level-runner/` was not read in full — verified (read, merged) for the ADR.

[^4]: `docs/rfc/0113-run-grant-at-brief-ready.md` decisions D1, D4, D5 and D7 — verified (read, merged). The path, keys and `held_actions` values (`push`, `open-pull-request`) are in spec `run-grant` AC-0003 and `references/brief-runner.md` — verified (read, merged).

[^5]: ADR-0160, ADR-0156 and spec `verified-infrastructure-parallelism` (Shipped; its Known limit says Core ships no attesting launcher) — verified (read, merged); pack version 4.0.29 in `packs/core/pack.toml` — verified.

[^6]: `docs/adr/` filename and keyword search for standing or recorded policies — verified for the search, which found no match.

[^7]: Intent files `docs/product/intents/<name>.md` in the main checkout, read for status, outcome, the two quoted lines, and the `CAP-0012` parent — verified (read).
