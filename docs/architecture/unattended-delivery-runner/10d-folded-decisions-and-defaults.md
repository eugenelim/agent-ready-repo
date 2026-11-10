# Architecture Change — Folded decisions and defaults

**Decision sought:** Review 31 folded sub-options with their parent decisions, and object to any of 18 defaults that `ferryman` takes unless the owner says otherwise.

Every recommendation from the 76 decision numbers is kept, and none is renumbered. Three points carry the page:

- A folded decision keeps its number and its recommendation, and its parent on [page 10c](10c-review-decisions.md) carries the choice.
- A default is cheap to reverse, and the table says how.
- The owner reviews only the parents and objects to defaults by number. A sub-choice marked provisional is recorded under a decided parent (D26, D34, D65, D68, and D27's other sub-choices) and was not walked separately.

**Author(s):** Repository owner (draft)
**Status:** Draft
**Last updated:** 2026-11-07
**Reviewers:** Repository owner

**Baseline — current architecture:** [Owner decisions](10c-review-decisions.md) and [triage](10b-decision-triage.md).

## 1. Scope and Baseline

This page holds detail the owner can skim.

| Delta item | In scope | Why it is here |
| --- | --- | --- |
| 31 folded sub-options | yes | They are facets of one concern each |
| 18 defaults | yes | They are reversible implementation details |
| The 26 owner decisions | no | [Page 10c](10c-review-decisions.md) |

| Unchanged context | Link |
| --- | --- |
| Records | [page 10](10-decisions-and-records.md) |

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

The first table lists folded sub-options with their parent. The second lists the defaults, each with why it is safe and how to reverse it.

| # | Decision | Folded into | Recommendation | Strongest alternative |
| --- | --- | --- | --- | --- |
| D16 | Ticket to intent | D3 | An `intake-ticket` request with inputs from the pinned `[intake]`, default refuse, and a consent gate when the config is absent | A `ferryman` process pre-step with no ledger |
| D18 | Approval-field list | D14 | One `approval-fields.v1` read by `ferryman` and the siblings, with a drift test | Guard only in `ferryman` |
| D20 | Meaning of `session-attested` | D15 | A prompt on `ferryman`'s own terminal | `ferryman answer` on a TTY with the window rule, or default to `host-attested` |
| D21 | Re-park after a recorded approval | D15 | A verified `request-changes` answer returns both artifacts to Draft under the write-ahead rule | A human reverts the scribe commit |
| D22 | Withdrawing a tracker approval | D7 | Revert before `start` only | Route it through history adoption after admission |
| D26 | Claims without a control plane | D24 | Ship the claim contract and build it in P7, because a subject-keyed fence is required before `start` in pool mode. Provisional: pool-mode claims do not expire, carry `{run_id once known, epoch, node_id}`, are released only by the control plane at terminal or abandon, and are re-taken at each re-key. A duplicate-dispatch-across-a-park trial is on [page 12](12-pool-state-integrity-and-signals.md) | Control-plane assignment only |
| D28 | Record level for a relayed tracker signal | D25 | `control-plane-signed`, with the tracker bundle attached as evidence, so the pool defaults need no tracker level ([12](12-pool-state-integrity-and-signals.md)) | `tracker-verified`, with pool gates also listing it |
| D29 | Pinning the user config | D23 | Pin its digest in memory at run start, without a `HEAD` comparison, and keep approval inputs out of it | Drop it from the trusted set and forbid it from naming argv for approval-relevant roles |
| D32 | Per-slice worktree creation | D31 | `ferryman` creates slice worktrees on `brief/<brief-slug>/<spec-slug>` in P6 under [page 08](08-worktree-and-concurrency.md) rules, so the brief-level runner finds them by branch name | The brief-level controller agent creates them, as ADR-0159 says |
| D33 | Worker limits and heartbeat (a P0 contract input: the lease table the loop reads) | D67 | Read the supervisor's `lease` table (`heartbeat_seconds`, `retry_budget`, `stuck_after_seconds`) through the supervisor's loader or `status`, never a second table. `[limits]` stays only as a fallback | Keep `[limits]` as a second authority |
| D34 | Repo-wide config versus a per-brief run grant | D31 | `ferryman` reads grant values only from the brief-level runner's `next` or `status` at the base (a pool clone cannot run it, so provisionally the control plane supplies the grant values in `launch.v1`, and pool runs otherwise refuse a brief that carries a grant), parks when they change mid-run, and does not put the grant file in the trusted configuration set. A grant only narrows | One record for both, with the grant file pinned |
| D35 | Approval route for host, tracker, and pool answers (decided) | D7 | Route (a): a new ADR supersedes ADR-0157 D4 in part (record 18, Proposed until accepted). A recorded answer that carries a verified named-human approve through an enumerated channel, with an attribution record, counts as that human's approve. Every other D4 prohibition stands. v1 ships `session-attested` only | Route (b): host and tracker signals only trigger a session-attested terminal confirmation. Route (c): the approver always writes `Status` by hand |
| D42 | Tracker approval observation | D7 | Observe approvals only while a foreground poller runs | Webhooks through a control plane |
| D43 | Signature scheme for signed commands (decided) | D27 | Public-key verification by subprocess: `ssh-keygen -Y verify -f <allowed_signers> -I <identity> -n ferryman-control@v1.invalid -s <sigfile>` with the signed bytes on standard input.[^6] Nodes hold only public keys, and the control plane keeps the private key. Record 13 still needs to be Accepted | A per-run HMAC key, which needs a secret channel, or one vendored crypto dependency through an ADR |
| D44 | Human-decision assertion in signed answers | D27 | Authenticated-human claim fields (`auth_method`, `authenticated_at`, `session_id`, `actor.kind=user`) and a control-plane duty never to sign an answer without a human act | Attestation of a named human only |
| D46 | Agent-sandbox credentials and egress | D27 | Egress limited to the model endpoint through a control-plane gateway with a per-attempt model token, and a work-tree copy with no Git credentials | Open egress as a recorded accepted risk |
| D47 | Intake ordinals across clones | D24 | The control plane serialises intake per repository, pushes the intake commit to a named intake branch right after the `intake-ticket` step, and waits until the prior intent is visible under `refs/remotes/origin/`, which is what `intent_ordinal.py` reads (read here), and each intake allocates from a fresh remote view. Neither `intent_ordinal.py` nor `intake_transaction.py` accepts a supplied ordinal, so `launch.v1` carries none[^9] | A claim ref keyed on the destination ordinal, or accept serialised intake as a throughput limit |
| D48 | Clock skew | D45 | Absolute times with a stated maximum skew of 60 seconds and a node clock-sync requirement for signed-command expiry, and durations for worker leases | Relative TTLs, with nonce plus epoch as the only replay guard and the 15-minute claim removed |
| D51 | Descriptor file beside the supervisor | D50 | Not yet. Keep built-in descriptors per skill version and declare supported ranges. Revisit after the supervisor's pinned file set is read | The pack ships a descriptor beside the script, which frees `ferryman`'s release but changes the skill directory the manifest records |
| D53 | Compatibility policy | D50 | One rule, owned by [page 02](02-install-trust-and-detection.md): accept patch versions inside a tested minor, refuse outside the declared range, and stop on an unknown version | An exact-version pin per skill release |
| D55 | Execution boundary for key-holding sandboxes | D27 | Sandbox processes that hold the key or a credential execute only digest-pinned `executed_paths`. The P7 gate names which way D55 went, before any P7 slice starts. Until then the ferryman sandbox refuses `execution-boundary-unset` for any post-guard step that runs repository or patch code | Run `report` in a third sandbox with no key, or accept the risk |
| D57 | Checkpoint pushes under RFC-0113 (decided) | D45 | Decided: a pool node never pushes, and the control plane's checkpoint writes go to a separate repository and are not the run's push, so a run grant that keeps push human-only does not hold node checkpoints back.[^10] Single-machine checkpointing is optional and pushes to a local or separate remote. The merged grant text excludes a separate checkpoint remote that accepts refs in one namespace only from "push", so a checkpoint push to any other remote counts as a push, and under `Also human: push` or a grant refusal those checkpoints stay local with an explicit event | none |
| D58 | Branch lifecycle (decided, revised by the owner) | D59 | One branch per subject, `ferryman/<scheme>-<hash of ref>`, one name for that subject's chain. `run` refuses `subject-branch-unmerged` only when the same subject has another unmerged branch, and the frontier skips tickets that carry a `ferryman/*` branch or marker | One branch per ticket with the frontier excluding mirrored tickets, or stacked branches |
| D63 | Where the spec supervisor ships | D4 | Inside the existing `new-spec` skill, driven by `work-loop` | A separate new skill, or `work-loop/scripts/` |
| D65 | `session-attested` actor in team use | D15 | Provisional v1 default: compare Git `user.email` with `[identities.<owner_ref>] git_emails` (moved from P5 to P0), require `plan_reviewer_ref` equal to `owner_ref`, and refuse otherwise | Accept any local terminal user as the approver, with no `[identities]` comparison |
| D68 | Launch-file layering for pool keys | D27 | A committed `[pool]` table in `ferryman.toml` applies only when `mode = pool`, which keeps the trusted-set invariant. It commits the allowed control-plane signer principals, and the allowed-signers file has one home, TB5 provisioning. The checkpoint remote is control-plane configuration, which the launch file does not carry, and the table on page 01 lists each `launch.v1` field as settable or data-only. Provisional, not decided | Widen the launch-settable list as a stated exception, accept the control plane as the authority anchor, or use separate repository configs |
| D69 | External effects in a pool | D27 | Effect requests park for a human in pool mode until a control-plane effect path exists. The `store` compare-and-swap before an effect applies only once the alternative is taken | The control plane performs effects on an `effect-requested` event, or a scoped per-effect credential with revocation |
| D71 | Merge and push ownership | D27 | The control plane merges only on a recorded human merge decision, stated on [page 11](11-remote-agent-pool-seams.md) | The control plane only pushes a branch or opens a pull request |
| D72 | Parked gate in a pool | D24 | Exit 10 and re-dispatch with a restore when the answer arrives | Hold the node |
| D73 | `ferryman` package and image integrity | D27 | The distribution's file-hash record digest in `launch.v1`, plus an image-integrity control-plane duty | A build provenance attestation |
| D74 | P0 gate for the v1 scribe | D15 | Gate P0 on records 11 and 12 Accepted. The terminal act is the approver's own act, so no ADR-0157 D4 change is needed for v1 | Gate P0 on record 18 |

| # | Default taken unless the owner objects | Why it is safe | How to reverse |
| --- | --- | --- | --- |
| D11 | A distinct worker profile per review round, and a weaker fresh session only if configured | the weaker mode is configuration | set the configuration key |
| D12 | This design lives in `docs/architecture/unattended-delivery-runner/` as a Draft | it is documentation | move the folder and update links |
| D13 | On one machine stop at `terminal` and a human merges (D71 covers a pool) | a human keeps the merge | add opt-in pull-request opening later |
| D19 | Keep page 09 as an end-to-end flow page | it is documentation | fold it into README section 3 |
| D38 | Accept `hold` from an actor with triage permission via `[identities]` | a tightening signal | relax it in configuration |
| D39 | Own checker for the JSON Schema subset, with equal fixtures against a full validator in repository tests | the fixtures fail on drift | swap to a vendored validator through an ADR |
| D40 | Copied file-safety helpers with an equal-behaviour test | the test fails on drift | extract a shared stdlib-only package |
| D41 | Run root per worktree, locks in the common Git directory | lock tests cover both | move the lock directory |
| D49 | Defer GitHub Projects: user-owned Projects reject fine-grained and App tokens, and a classic token needs `project` plus `repo`[^7] | Issues, labels, and milestones work now | add an organisation-project adapter |
| D52 | `ferryman init` generates `ferryman.toml` and no configuration is seeded, because seeds are never upgraded | a human reviews and commits the file | ship a seed, or evaluate the RFC-0112 pack-defaults projection for non-sensitive defaults |
| D54 | Show each role's permissions, model, and CLI version and ask once before the first real run, storing consent in `~/.ferryman/consent.json` keyed on profile, model, and CLI version, and asking again when one changes | it adds consent | show on request only |
| D60 | `ferryman` passes scribe commit shas to the siblings on `next` and `report` | provisional and tested at P0 | the siblings read a closed scribe record |
| D61 | Park an orphan worker `needs-attention` and never kill it | it destroys nothing | add a kill option |
| D62 | Respawn once per refusal with the refusal text, up to the lease `retry_budget` of 2 | the count is bounded | set respawns to 0 |
| D64 | Create the discovery directory in a second commit after the intake commit | kill point B8 covers the gap | use one commit |
| D66 | Ship `setup-ferryman` and `--demo` in P0. The demo calls `work-supervisor park` over a fixture, runs no worker, and makes no model call or network call | both are additive | defer them to P1 |
| D70 | Wall-clock enforcement only, plus after-the-fact usage and a control-plane duty | usage is still recorded | make `status.usage` mandatory |
| D76 | Keep the v1 worker floor (per-profile allow list, allow-listed environment, guard) and add five cheap changes: credential stripping at spawn, an `enforcement` level per attempt, a probe record before a run, the all-ref snapshot (already in the guard), and a token scan of returned diffs. A container executor kind is a later item, not scheduled ([03b](03b-headless-worker-launch.md), [05b](05b-approval-integrity-and-trusted-configuration.md), [11](11-remote-agent-pool-seams.md)) | each change only narrows what a worker receives or records more, and the guard is unchanged in shape | set `enforcement_required = false` and pass `--accept-unprobed` to run unprobed, or drop a change in `ferryman.toml` and the launch code |

| Semantic name | Change type | Baseline reference | Compatibility during transition | Enforcement | Verification |
| --- | --- | --- | --- | --- | --- |
| none | n/a | n/a | n/a | n/a | n/a |

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

[^6]: OpenBSD `ssh-keygen(1)`, SIGNING and `-Y verify`: `ssh-keygen -Y verify -f allowed_signers_file -I signer_identity -n namespace -s signature_file`, message on standard input, exit status zero on success by an authorized signer, allowed signers lines `principals options keytype base64-key` with an optional `namespaces` option — https://man.openbsd.org/ssh-keygen.1 — verified by fetch. The page states no specific failure status for verify.

[^7]: GitHub REST docs, project items — https://docs.github.com/en/rest/projects/items — verified by fetch. The report that the gap is still open as of August 2026 — https://github.com/orgs/community/discussions/36441 — was not re-fetched: unverified.

[^9]: `intent_ordinal.py` usage is `--dir <dir> --token <TOKEN>` or `--check <dir>`, and it allocates from the local and remote view. `intake_transaction.py` names no ordinal — verified (read).

[^10]: `references/brief-runner.md` (Run grants, "Push and pull requests": "push" means publishing to the shared remote and excludes a separate checkpoint remote that accepts refs in one namespace only) — verified (read, merged, core 4.0.28). That the control plane's checkpoint repository meets the one-namespace condition, and how `ferryman` learns what a remote accepts, are unverified.
