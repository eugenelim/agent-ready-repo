# Architecture Change — Rollout, spikes, and risks

**Decision sought:** Approve the phased rollout, the four spikes that run before E0, and the risk register for the set.

Everyday users benefit first, and `ferryman` follows the sibling supervisors. P5 and P7 depend on the D35 ADR, and three choices carry that:

- Every phase ships behind absence, so an unconfigured feature does nothing.
- Four spikes (S0 to S3) check the unverified premises and are recorded before E0 starts.
- Reversal needs no migration, because every new state is local or a revertible commit.

**Author(s):** Repository owner (draft)
**Status:** Draft
**Last updated:** 2026-11-07
**Reviewers:** Repository owner, maintainers

**Baseline — current architecture:** The pages named in the [set index](README.md). [Page 10](10-decisions-and-records.md) owns decisions, alternatives, and records.

## 1. Scope and Baseline

This page owns the plan and the risks, and page 10 owns the decisions.

| Delta item | In scope | Why it is here |
| --- | --- | --- |
| Phases, gates, window owners, reversal | yes | One phased plan covers all pages |
| Spikes S0, S1, S2, and S3 | yes | Each checks an unverified premise before the phase it feeds |
| Risk register | yes | Cross-page risks have no other home |
| Decisions, alternatives, records | no | [Page 10](10-decisions-and-records.md) |

| Unchanged context | Link |
| --- | --- |
| Per-page measurable scenarios | each page's quality section |

## 2. Structural Change

This page adds no element. Each page owns its own.

| Element | Change type | Owner |
| --- | --- | --- |
| none | n/a | the pages in the [index](README.md) |

## 3. Runtime Change

Four spikes run before E0, each with a pass rule. A failed or partial spike changes its phase and does not block E0: S0 feeds P0, S1 P7, S2 PL, and S3 E1 and E2.

| Scenario | Trigger | Path |
| --- | --- | --- |
| Probe S0 | `doctor --probe` | normal |
| Restore spike S1 | before E0 | normal |
| Light-session spike S2 | before E0 | normal |
| In-session sibling drive S3 | before E0 | normal |

**Probe S0: agent CLI capability.** A spike ran for four CLIs, and `doctor --probe` is the standing check. `run` refuses `profile-unprobed` without a record ([03b](03b-headless-worker-launch.md)).

| CLI | Version | Result | Status |
| --- | --- | --- | --- |
| Claude Code | 2.1.311 | Loads a project skill, and an allow list denies an unlisted write | Tested |
| Copilot CLI | 1.0.103 | Loads `.github/skills`, and a write needs its grant | Tested |
| Pi | 1.5.0 | Loads a skill, and `--tools read` leaves no write tool | Tested |
| Codex | 0.164.0 | Loads a project skill from `.codex/skills` and `.agents/skills`, and an outside-repository write is denied[^2][^8] | Tested |
| Gemini, OpenCode, Cursor | not installed | Documented only: Gemini `-p` skills unconfirmed, OpenCode `run` reads three skill folders, Cursor `-p` needs `--trust` | Open |

Launch facts are on [page 03b](03b-headless-worker-launch.md).[^1]

`doctor --probe` is opt-in and costs model calls. For each configured profile it runs a marker skill, a limit test, and a control in a scratch repository, and records the CLI version. A profile with a different installed version fails.
1. Marker: a request names a skill whose instructions write a token from a skill file to `attempts/<id>/result.json`. Pass: the file holds the token.
2. Limit: the same prompt asks for a write outside the allow list. Pass: it is denied or sandboxed.
3. Control: the grant is added. Pass: the write succeeds.
4. Stop: SIGTERM mid-run. Pass: the process tree is gone within 5 seconds.

A CLI that fails the marker serves only `attach` mode.

**Spike S2: light session.** It runs a headless worker on each probed CLI with a light request, and all four are tested with Surface-and-stop observed on Codex. Codex writes its record as prose and the other three print none, and only the Codex risk-trigger run is valid, since the other fixtures had no auth check.[^6]
1. Run the request in a scratch repository.
2. Pass: the controller's deterministic check on [page 05](05-supervisors-and-gates.md) reaches direct-light, with no commit, spec or registry change. The decision-record pass rule is unmet, since Codex's record is prose.
3. Record the Surface and stop behaviour, which maps to `needs-human`.

The Codex session used `workspace-write`, `on-request`, null stdin, and a fixture with a real `check_token`.[^8]
- Run 1 (light request): the worker edited only the two declared files, ran the skill's gates, left the change uncommitted, and created no spec or registry entry. Its record is prose plus a `review-verdict.v1` block, and it claimed a clean review with no reviewer spawn event, so reviewer dispatch is unverified.
- Runs 2 and 3 (ambiguous request, risk trigger): a prose question, and a stop on a full-mode change since `new-spec` was not installed, both exit 0.

**Spike S3: in-session sibling drive.** A session agent drives a supervisor through `start`, `next`, and `report`, loses its context, and resumes from `status` with no controller process. It passes on a stub with Claude Code and on the real `work-supervisor.py` as a proxy, in 4 of 4 resume-capable tries across three CLIs, so the kill condition 'fails in at least two of three tries across different CLIs' is not met ([page 05](05-supervisors-and-gates.md)).[^7]
1. Run the supervisor in a scratch repository, with the session agent as controller.
2. Pass: the resumed session reaches the same request id and no record is lost.

Unverified: `spec-supervisor` (not built), parked-gate and approval flows, resume with `attempt-residue` or `supervisor-changed`, and a kill during `report` or a worker edit.

**Spike S1: restore.** It checks that a snapshot restores in a fresh clone. The local part passed, and atomic pushes, credential scoping, and the push audit were tested on one real host ([page 12](12-pool-state-integrity-and-signals.md)), with the control-plane writer and a restore with an open attempt still open.[^5]
1. Run a spec to a mid-run step on a scratch repository, and snapshot the run store and product ref.
2. Restore the snapshot in a fresh clone, and run `status` and `next`.
3. Pass: `next` re-issues the same request id with no refusal. Controls: with the store missing, `next` refuses `supervisor-changed`, and with the ref missing and an attempt open, the supervisor emits `attempt-residue`.
   - With a changed supervisor file, the pin check refuses.
4. Record the file list the snapshot needed: the whole supervisor directory, since gate records sit outside the run directory.
5. Push-rate, ref-growth, and atomic steps: measured locally, with host limits open.
6. Credential scoping: a deploy key is scoped to one repository, not a namespace (one host). Open: a ruleset on a paid or public repository.
7. Shallow clone: confirm a non-shallow clone restores, and record how a shallow clone behaves. Open.
8. Integrity step: a restored store with no open attempt and a template-built `.git/config` passes the supervisor integrity checks. Open: that `start` on an admitted run re-pins and answers `current` on a fresh clone.

No spike has met every pass rule, so each is recorded before E0 with its open items: S1 steps 6 and 7 and a restore with an open attempt, S2 Codex reviewer dispatch, and S3 `spec-supervisor`. S2's D76 follow-up is stripped-environment authentication: verified for Copilot, Pi, and Codex, and open for Claude Code, whose login failed intermittently in the baseline too (untested, not a pass).[^10]

## 4. Contract and Invariant Change

This page adds no contract.

| Semantic name | Change type | Baseline reference | Compatibility during transition | Enforcement | Verification |
| --- | --- | --- | --- | --- | --- |
| none | n/a | n/a | n/a | n/a | n/a |

## 5. Data/State Migration

No existing state moves, and each page's migration table lists its own new state.

| Data element | Old shape | New shape | Migration mechanism | Rollback |
| --- | --- | --- | --- | --- |
| All new state | none | per-page tables | none | per-page rollback |

The one ordering hazard is `[authorization.mirror]`, which stays absent until record 7 on page 10 (the standing write-back ADR) is Accepted.

## 6. Deployment/Operational Change

Each phase works alone because an unconfigured feature does nothing, and [page 10b](10b-decision-triage.md) names each gate's decisions.

| Phase | Ships | Enter when | Leave when |
| --- | --- | --- | --- |
| S0 | Probe `doctor --probe`, done for four CLIs. No build | none | Probe passes for one CLI |
| S1 | The restore spike above, local part passed. No build, recorded before E0 | none | The restored run answers `status` and `next` as an unbroken run, the push, `--atomic`, and credential-scoping steps pass, and the results are committed |
| S2 | The light-session spike above, tested on four CLIs. No build, recorded before E0 | none | The controller check reaches direct-light with no commit and no spec on each probed CLI, and the Surface behaviour is recorded |
| S3 | The in-session sibling drive spike above, passed on a stub and on the real work supervisor as a proxy. No build | none | The resumed session reaches the same request id with no lost record, and the result is committed |
| E0 | Records 3 and 4, the discovery RFC (record 21, written here and gating E2 only), `supervisor-manifest.v1`, `approval-fields.v1`, and the shared request envelope. No `work-supervisor.py` edit | S0, S1, S2, and S3 have recorded results | Records 3 and 4 Accepted, and the manifest and approval-fields schemas merged |
| E1 | Spec supervisor: new core skill `spec-loop`, repo scope, with an in-session driving reference | E0 exit, D4 and D37 decided, and record 4 Accepted | Review-independence, round-cap, and per-verb refusal tests pass, and one real spec goes Draft to plan-approved in a live session |
| E2 | Discovery supervisor, shipped with `discovery-loop` | D3, D5, and D9 decided, the RFC (record 21) Accepted, and E0 exit | Discovery fixtures pass, and a discovery runs G0 to G3 live and resumes after context loss |
| E3 | Everyday-user path ([page 14](14-installation-and-adoption-experience.md)): one how-to per supervisor, routing, install prerequisites, the `pack-missing` message. Light mode stays direct-light in the session | E1 or E2 exits, per supervisor | Each exited supervisor has its how-to and routing, and a missing pack gives `pack-missing` |
| P0 | The contracts D67 freezes, the `ferryman` loop, workers, `doctor`, the `work-supervisor` descriptor (the only built-in), scribe, guard, trusted configuration pin, locks, `init`, `clean`, `--demo`, and `setup-ferryman` | Records 11 and 12 Accepted. D1, D14, D15, D17, D23, D59, and D67 decided. For the release also D50 and the compatibility rule (D53), and record 19 Accepted | The kill-point and guard corpora pass, and a real spec runs end to end on a scratch repository |
| PL | The light session route of [page 05](05-supervisors-and-gates.md): `ferryman session`, the `light-session` order, `route`, `light_candidates`, five kill boundaries, and two guard shapes | P0's worker interface, guard, projector, and `doctor` exist. Record 22 Accepted, D75 and S2 recorded, and `light-mode.md` records that a local human `ferryman session` launch is an explicit trusted invocation[^9] | The five session kill-boundary tests and two guard shapes pass, and a real light request runs end to end on a scratch repository with no spec or registry change |
| P1 | Frontier and waves, with brief ordering delegated to the brief-level runner's `next` (D31) | D31 and D56 decided, and record 17 Accepted | Determinism corpus passes |
| P4 | GitHub shim, read-only (candidates, events, revisions) | D8 decided and its record Accepted | Rate-budget test passes, and the unverified `gh` claims are checked |
| P5 | Standing write-back and tracker approval | Records 7, 8, and 18 Accepted, D6 and D7 decided | Forged-signal corpus passes |
| P6 | Per-slice and parallel worktrees on one machine (D32) | D31 decided, its D32 facet confirmed, and record 6 Accepted | Page 08 preconditions reviewed under D32 |
| none | Concurrent attempts through `run-concurrent` | No phase depends on it (D36) | `ferryman` documents a stop for the request kind until a decision settles the model channel |
| P7 | Pool contract shapes and signature fields, `remote` executor, checkpoint bundle and restore, subject fence and claims, out-of-band digests, signed commands, relayed signals | Records 13, 14, 15, and 18 Accepted. D24, D25, D27, and D45 decided, the D34 pool facet settled, and D27's D55 facet naming its execution boundary | Spike S1 passes, and the pool corpora pass: forged command (11 shapes), forged signal (8 shapes), fencing, duplicate dispatch across a park, lease, tamper before `start`, effect parked |
| P8 | Spare | none | none |

E1 to E3 and PL to P7 each ship the deliverables in [page 14](14-installation-and-adoption-experience.md) section 6, and P0 ships `ferryman clean`.

E1 and E2 run in parallel after E0, and `discovery-supervisor` is optional (D3).


Text to update: `work-loop/references/unattended-loops.md`, RFC-0053's no-engine constraint, and the ADR-0157 back-pointers after record 18 is Accepted.

**Reversal.** Remove `ferryman` and delete run roots. Committed ledgers stay valid, and each supervisor works without `ferryman`.

Revert step commits to roll back a ledger, and delete `[authorization.mirror]`.

**Window owners.** The repository maintainers own each phase gate, E0, P1, and P6, and the work-loop owners own S0 to S3, E1, P0, and PL. The discovery-loop owners own E2, the tracker-pack owners own P4 and P5, and the control-plane owners own P7 and P8.

## 7. Quality Regression and Verification

33 risks follow, each with a mitigation or a stated acceptance.

| Attribute at risk | Baseline target | Stimulus that could regress it | Verification |
| --- | --- | --- | --- |
| Set-wide safety | existing supervisor suites green | any edit near pinned scripts | the three tools pin suites and precheck before push |
| Operability at 3 a.m. | none | a headless run parks silently, or a rate limit stalls polling | `needs-attention` and `max_requests_per_hour` events, a parked-gate age alarm |

Risks:
- Approval forgery by a worker or a tracker actor. Mitigation: the guard, the six-check verifier, tracker gates off by default, and the 26-shape corpus.
- Configuration escalation through a ticket. Mitigation: the pin (D23). Residual: a crash mid-attempt that also committed a change parks for review.
- A late `answer` from a worker that left its session. Mitigation: `host-attested` off by default (D15).
- A scribe crash between edit and commit. Mitigation: the write-ahead intent and kill points B-S1 to B-S6.
- Principle 3 drift through `--watch`. Mitigation: no port, registry, or daemon.
- A headless worker burns budget. Mitigation: `wall_seconds`, `max_respawns`, and retry and round caps.
- Contract drift between ferryman and supervisors. Mitigation: manifest tests and a descriptor refused on an unknown skill version. Residual: a `work-supervisor.py` bump needs a new descriptor.
- Tracker data poisoning. Mitigation: tracker content is untrusted, and labels hold no free text.
- Ticket drift mid-run. Mitigation: `source-revision-drift` parks the run.

- Control plane compromise and containment limits: the control plane can sign any command (D27) and owns key custody, there is no process containment on Windows, a `setsid` escape exists elsewhere, and token spend is invisible unless the executor reports it. Accepted here.
- Checkpoint credential scope. D45 revised removes the shared credential for pool nodes: the control plane alone writes the refs.[^11] The residual is that the control plane holds the credential, and its compromise is the accepted risk above. Its record of written refs is the integrity basis, since the tested host has no push audit or ref-namespace scoping.
- Lease clock skew. A failed compare-and-swap push halts `ferryman` whatever the clock says.
- Repeated effect after a restore. Mitigation: D69 parks pool effects, so none dispatches. If D69's alternative is taken, a checkpoint follows each `effect-intent` commit, with no progress if the push fails. An effect-intent restore is untested.
- Skill and CLI drift: Claude loads user-level skills by default, and a default or model can change. Mitigation: project-only setting sources, a skill-list check, a pinned version, a named model, and the probe.
- Assumption debt. Unverified: GitHub event retention, a GitHub App actor, `gh` scope handling, the `gh issue list` transport, Codex reviewer dispatch, and documented-only CLIs. P4 waits for the GitHub items.
- Claims from other projects' checkouts are not reproducible here, and the server script's import failure was only read.[^3]
- The model channel for concurrent attempts is undefined: AC-0017 requires denied network, and no record defines a channel. Mitigation: no phase depends on `run-concurrent` (D36), and pool parallelism comes from separate runs (stated by the Slice 7 owner).[^4]
- A worker swaps the pinned launcher. Mitigation: the launcher path and digest are in the trusted configuration set, and the guard corpus has a shape for it ([05b](05b-approval-integrity-and-trusted-configuration.md)).
- Adjacent work changes. Mitigation: pages cite it by record and add only additive seams.
- Duplicate dispatch repeats an external effect. Mitigation: D69 parks pool effects, and only its alternative adds the `store` compare-and-swap before each dispatch.
- A signed command replays across nodes. Mitigation: consumed nonces, epoch binding, 15-minute expiry.
- Spend grows under preemption. Mitigation: usage and retry counters travel in the manifest, under the launch file's budget.
- The standard library has no asymmetric signature verification. Mitigation: verification by `ssh-keygen -Y verify` (D43, decided).
- The agent sandbox has open egress. Mitigation: the pool agent-sandbox attestation (gateway-only egress, per-attempt token, D46), and a missing one refuses `pool-config-incomplete`.
- The `approval-fields.v1` copy in `spec-loop` and the one a `ferryman` release expects drift apart. Mitigation: a `fields_version` mismatch refuses, the pin covers the copy read, and a drift test ([01](01-contracts-and-data.md)).
- A same-user process injects input into the terminal prompt. No mitigation is claimed. Accepted for v1.
- A worker running as the same OS user can read home files. The stripped environment and run-owned git config (D76, [03b](03b-headless-worker-launch.md)) narrow it, and `[protocol] allow = never` blocks a push (tested), but a home-file credential and the CLI's model login remain. A Codex worker ran `gh api user`, so the forge-CLI deny list stays. Accepted for v1, with a separate OS user or container (D23) an input to D7 before P5.
- A headless light worker implements an unreviewed change. Mitigation: the `adversarial-reviewer` runs inside the session, a missing review is `BLOCKED`, and a human publishes. A Pi run stopped `BLOCKED` with the reviewer missing, so the profile carries `reviewer_available` ([03](03-ferryman-runtime.md)). Codex reviewer dispatch is unverified.
- Unverified: that a headless worker's Surface-and-stop is representable on a CLI other than Codex. The queueing and control-plane rows of `light-mode.md` still bar the pool case, and the PL gate holds the `light-mode.md` change for a local human launch.
- Self-approval in a session: the agent can write an approval itself, as under `work-loop` today. Mitigation: the ADR-0157 rule, the `no-human-answer` refusal in `report`, and the `ferryman` guard once adopted ([page 05](05-supervisors-and-gates.md)). Accepted for E1 and E2.
- A session agent resumes from `status` alone: tested on a stub and on the real `work-supervisor.py` across three CLIs, and untested on `spec-supervisor`.
- Tier B discovery state in `.context/discovery/` is lost with the clone or rewritten by a same-user process. Mitigation: the hash chain, the refusals, and journey F on page 14. Accepted for tier B (D9).
- Repository content and transcripts reach model endpoints. Mitigation: per-deployment classification and retention, and D46 egress limits.

## 8. Build Mapping

Each page's build mapping covers its elements, and the set-level table is in the [index](README.md).

## Evidence

[^1]: Claude Code, "Run Claude Code programmatically" — https://code.claude.com/docs/en/headless — verified by fetch.

[^2]: Codex non-interactive mode — https://learn.chatgpt.com/docs/non-interactive-mode — verified by fetch. It does not state skills or `AGENTS.md`.

[^3]: The core pack's workspace MCP server script, line 4 — verified by reading, not run.

[^4]: ADR-0156 D1 and spec `verified-infrastructure-parallelism` AC-0017 require network denial, and no record defines a model gateway — stated by the Slice 7 owner (2026-11-07), not independently checked. The AC-0017 text was read in the unmerged Slice 7 worktree — verified.

[^5]: Spike S1, 2026-11-07, local scratch repositories: the restore reached `status` and `next` once `.git/config` matched, with `attempt-residue` otherwise, and a template-built config restored with no open attempt — verified (tested, single run, 2026-11-07). Shallow clones and a restore with an open attempt: unverified.

[^6]: Spike S2, 2026-11-07, four CLIs, single run each: Claude Code, Copilot and Pi printed no direct-light decision record, skipped Surface-and-stop, and ran a risk-trigger fixture with no auth check — verified (tested, single run, 2026-11-07) for what ran, otherwise unverified.

[^7]: Spike S3, 2026-11-07: a stub supervisor with Claude Code, and the unedited pinned `work-supervisor.py` as a proxy with a killed session and a fresh one (Claude Code, Codex, Copilot) — verified (tested, single run each, 2026-11-07). `spec-supervisor` and the flows listed above: unverified.

[^8]: Codex 0.164.0, 2026-11-07, one run per case: skill loading, the sandbox denials ([03b](03b-headless-worker-launch.md)), and the three S2 runs — verified (tested, single run, 2026-11-07). Skill precedence with both paths, reviewer dispatch, and the custom-agent format: unverified.

[^9]: The maintainer confirms a local human `ferryman session` launch is an explicit trusted invocation under `light-mode.md`; the skill text does not say so yet: unverified.

[^10]: Credential-stripping test, 2026-11-07, git 2.56.0, four CLIs, trivial prompt ([page 03b](03b-headless-worker-launch.md)) — verified (tested, single run, 2026-11-07) for Copilot, Pi, and Codex. Claude Code: inconclusive, 2 of 7 runs passing in each mode.

[^11]: Deploy key on a free private repository: scoped to its own repository, able to write any custom ref in it, no push audit, rulesets HTTP 403 — verified (tested, single run, 2026-11-08; [page 12](12-pool-state-integrity-and-signals.md)). Control-plane writer: unverified.
