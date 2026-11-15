# Plan: supervisor trust gaps

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/adr/0144-work-loop-supervisor-owns-procedure.md`, `0154-work-loop-product-result-is-a-protected-ref.md`, `0157-work-loop-approval-gates-park-instead-of-halting.md`; analogues `scripts/_supervisor_gates.py` (parked-gate approval and digest, `docs/specs/parked-approvals/`) for a controller-owned verb and `scripts/_supervisor_commit.py` `GitPort.build_commit` for exact-byte commits; spec-stage rounds already use `review-artifact.py --run-id` numbered record files, so the budget needs no supervisor run; tests `packs/core/tests/skills/work-loop/test_supervisor_product_ref.py`, `test_supervisor_attempt.py`, `test_supervisor_pinning.py`. Uncertainty: the gate-declaration syntax and the pre-admission home of the spec-stage budget are `implementation-discovered`.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open, and
> the run continues with every finished task still finished. Execution
> observations belong in `docs/specs/<feature>/notes/verification-ledger.md` (or
> the adopter's equivalent). A genuine error in a protected section follows the
> controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are working
> material the controller corrects in place, before or after approval, while no
> attempt is open. After approval, grounding for a seam or design means recorded
> as `implementation-discovered`, and each later correction, is a controller edit
> of the plan's `## Design (LLD)`, never a ledger line; a settled design decision
> that execution falsified is a plan error the owner agrees to, corrected the same
> way unless it reaches a protected section. A TDD task's `stub` fence is likewise
> written by the controller at task start, not carried in the approved plan.
> Treating working material as contract is how a review spends a round on prose
> no gate consumes — the measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

<!-- Existing plans without this field remain valid. Treat its absence as a
named assurance gap during structural review, not a universal lint failure. -->

<!-- **Durable-plan fill.** This template is the implementation and verification
strategy for a durable delivery slice. Fill Approach, Constraints, Risks,
Design, Tasks, and Changelog to the depth the durable work requires. Its sibling
spec is the durable behavior contract. Eligible direct-light work does not
create this artifact. -->

## Approach

Four slices in dependency order, each a PR that leaves the repository green: execution proof (T1-T4), record commits (T5), review budget (T6-T7), checkout ownership (T8), then reference text and release (T9-T10). Execution proof goes first because it closes the largest trust gap and gives the review budget its invalidation semantics. The riskiest part is T2, running the declared commands against a frozen copy without widening what a worker can influence. Every slice edits pinned supervisor scripts, so it releases as a core patch and active runs finish on the prior release.

## Constraints

ADR-0144 (the supervisor owns procedure), ADR-0154 (the product result is a protected ref, moved by compare-and-swap) and ADR-0157 (approval gates park) bound every verb. Core's version bump rule (`packs/AGENTS.md`) applies to each slice. New tools tests go in registered suites, and a pack test names each `.apm` path as a literal.

## Construction tests

**Integration tests:** one real-Git, real-subprocess run per slice driving the new verb end to end (T2, T4, T5, T8 Tests).
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Maintainer procedure (supervisor reference, state schema, SKILL.md) | T9 | doc-pin tests, evals | `lint-spec-status` clean |
| Release history | T10 | `check-core-release`, roster upgrade-notes suite | fragment names core at the released version |

## Design (LLD)

Shape is `service`; sub-sections below.

### Design decisions
- **Supervisor-observed execution, not richer reports.** A worker can invent any field, so proof is a record the supervisor writes after running the declared commands itself. Rejected: report fields (forgeable), external CI attestation (service dependency and latency per task). Rests on: the supervisor can run a command and read its exit code without trusting the worker. Traces to AC-0001 to AC-0016. Owned by: T1, T2, T3.
- **Commands come from the approved spec.** The existing approval digest then binds them. Rejected: a separate pinned policy file (a second home to keep in sync). Rests on: the Agent Rules section is inside the approved, digest-bound text. Traces to AC-0008. Owned by: T1.
- **Record commits are an allowlist plus a manifest, not path-based auto-adoption.** A path name proves neither authorship nor approval. Rejected: auto-adopting any commit touching only record paths. Rests on: the controller, not the worker, supplies the manifest. Traces to AC-0017 to AC-0023. Owned by: T5.
- **One budget record, existing caps kept.** Counters share an identity carried from spec review through admission; the five-record, five-gate-failure and two-round caps remain extra guards. Traces to AC-0024 to AC-0030. Owned by: T6, T7.
- **Prevention, not relocation, for checkouts.** Rests on: committed delivery records already survive worktree removal. Traces to AC-0031 to AC-0035. Owned by: T8.

### Data & schema
New closed records, each with `schema_version: 1`: `gate-execution.v1` (`execution_id`, run, request, issuance, task revision, candidate tree digest, gate-declaration digest, per-command argv/cwd/exit/timeout, bounded output digests, outcome), `task-correction.v1` (correction id, run, task, revision, target commit, affected receipt ids, reason, authority reference, invalidation epoch), `record-commit.v1` (manifest digest, admitted bindings) and a review-budget record. Stored in the run store, or under `delivery/` where a record must be committed with the run (`implementation-discovered`: which records are committed). An unknown version or an unreadable record refuses. Traces to AC-0002, AC-0013, AC-0017, AC-0024. Owned by: T2, T4, T5, T6.

### Interfaces & contracts
New verbs on `work-supervisor.py`: `execute-gates`, `correct-task`, `commit-record`, `extend-review`; new refusals `gate-execution-missing`, `gate-execution-mismatch`, `review-budget-exhausted`, `checkout-not-isolated`, `checkout-reserved`. Test seam at each crossed boundary: the CLI process boundary and the Git port. Traces to AC-0001 to AC-0035. Owned by: T2, T4, T5, T6, T8.

### State & control flow
`execute-gates` runs under the run lock, freezes candidate entries through the commit machinery's private index, materializes them in a scratch directory, runs commands, and appends a started then completed record. `report` consumes a completed record in the same atomic step that admits the commit; an interrupted execution cannot pass. `commit-record` runs under the run lock with `HEAD` equal to the recorded product revision and no open attempt. `correct-task` reopens by an invalidation epoch that task derivation reads before commit-derived completion. Traces to AC-0005 to AC-0007, AC-0012 to AC-0015, AC-0021, AC-0022. Owned by: T2, T3, T4, T5.

### Failure, edge cases & resilience
Crash between ref move and record write keeps the existing `history-adoption` recovery. A reservation whose run store is absent is stale and does not block. Output is bounded and gate time is capped. Traces to AC-0005, AC-0009 to AC-0011, AC-0023, AC-0034. Owned by: T2, T5, T8.

### Quality attributes (NFRs)
Security: no worker or reviewer result mints proof, correction or a record path; script pins, protected paths, confined writes and locks stay. Owner references attribute, they do not authenticate; this limit is stated in the reference. Observability: every refusal carries its code, the failed Git verb and its duration where Git was involved. Traces to AC-0008, AC-0019, AC-0020. Owned by: T3, T5, T9.

### Dependencies & integration
`_supervisor_commit.py` (`GitPort.build_commit`, private index), `_evidence_store.py` (append-only supersession), `_supervisor_projector.py` (approved-section parse), `review-artifact.py` (existing round counts). No new dependency.

## Tasks

The work-breakdown. Tasks are sized so each one is a coherent commit or PR.
**Phrase each task as a verifiable goal, not a procedure.** The task name
*is* the success criterion: *"Add validation"* → *"All invalid-input tests
pass"*; *"Refactor X"* → *"Tests for X green before and after; public
surface unchanged"*. Tests drive implementation, not the other way around, so
`Tests:` leads every task. Use red-green-refactor with separate commits when
the change is non-trivial.

**`Approach:` is conditional.** Write one when the task carries a decision a
reader cannot infer from `Tests:` and `Done when:` — an *ordering* decision
(step B must follow step A for a reason the tests do not show) or a *seam*
decision (which module, which existing helper, which boundary). Omit it when
those two fields already say what to build and how it is observed: an
`Approach:` that restates them is a second home for the same instruction, and
no completion gate reads it. The field order is unchanged where it appears —
`Tests:`, then `Approach:`, then `Done when:`.

**Every task must declare `Depends on:` explicitly** — list prior task IDs
or `none`. Don't omit the field; "obvious from order" is the failure mode
that hides serial-by-default thinking. `none` is a valid and common answer.

Planning is sufficient when the plan supplies an observable contract, owner,
boundaries, ordering, discovery predicates where a seam is not grounded,
required outcomes, and verification modes adequate to begin safely. It need
not settle a helper name, symbol, fixture-internal detail, or complete edge-case
matrix before implementation. Such questions are build-time guidance unless
their absence makes the plan unable to start or verify the contract.

Keep observable behavior in `spec.md`. Use an exact path or symbol here only
when repository evidence grounds it. For an implementation-discovered callable
seam, record `implementation-discovered` and its discovery predicate,
constraint, required outcome, and verification mode; do not invent a helper,
fixture, module, path, or symbol.

**`Depends on:` grammar** (so the supervisor can read it). The field is a
comma-separated list of:
local task IDs (`T1`, `T1a`), ranges (`T1-T6`), or a **cross-spec marker**
`spec:<name>/TN` for a dependency on another spec's task (e.g.
`spec:auth-tokens/T7`). Parenthetical prose after the IDs is
ignored, so `T11 (lands after the shim)` is fine. Cross-spec deps are
*spec-sequencing*, not intra-plan ordering, and are excluded from this plan's
DAG. The supervisor issues a task only once the tasks it depends on are
complete, so a dependency authored later in the file still runs first, and it
**refuses a dependency cycle**. An entry that names no task in the plan is
ignored rather than refused, so a mistyped ID silently drops an edge: check
each ID against the task headings.

**Optional `Touches:` grammar.**
A task *may* add a `**Touches:**` line listing the file globs it expects to
touch — a comma-separated list of paths/globs (`src/api/*.py, docs/api.md`),
trailing prose ignored. The supervisor runs one task at a time, so the field
predicts no parallelism; it records the declared surface in the task's
revision, which makes a change to it a task change. The field is **optional** —
omit it freely; a task with no `Touches:` is never an error.

**Optional `Reads:` and `Writes:` grammar.** A task *may* add a `**Reads:**` line and a
`**Writes:**` line, each a comma-separated list of repository paths, naming what the task
reads and what it changes. An entry is a file path (`src/api/routes.py`), a
`dir/` listing (`Reads:` only), or `root/**` for everything under a directory (a walk
in `Reads:`, a subtree in `Writes:`). The supervisor may run several tasks at once only
when the host and policy allow it, and then only tasks that declare both lines and whose
declared sets do not meet one another's writes. A task that omits either line, or lists an
entry of any other form (another glob, a malformed path, a `Writes:` entry ending in `/`),
runs one at a time on the sequential floor, which is never an error. Both fields are part
of the task's revision, so a change to either is a task change.

**Optional `Effects:` grammar.** A task *may* add an `**Effects:**` line naming
the external effects it performs once its change lands — a comma-separated list
of names such as `push, publish-release`, or `none`. A name is lowercase letters,
digits, `.`, `_`, and `-`, and is unique across every `Effects:` line in the plan.
An effect is an operation outside the repository whose repetition would do harm;
it is recorded before it runs and is never repeated automatically. An
`**Effects:**` line in the plan's header, outside every task, names effects that
run once when the whole plan is done. Renaming a task keeps its effects; renaming
an effect makes a new one.

### T1: The gate declaration and the execution record are defined

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_projector.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_execution.py`, `packs/core/tests/skills/work-loop/test_supervisor_execution.py`

**Tests:** TDD — unit, at the declaration parser and the record validator
- AC-0008: a declaration in the approved Agent Rules section parses to ordered argument vectors, and an edit to it changes the approval digest.
- AC-0002: a `gate-execution.v1` record round-trips; an unknown schema version, a missing field and an extra field each refuse.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_execution.py -q` exits 0.

### T2: `execute-gates` runs the declared commands and records the result

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_execution.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_loop.py`, `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_execution.py`

**Tests:** TDD — integration, real Git and a real subprocess, at the `execute-gates` verb
- AC-0001, AC-0002: a passing and a failing command each run as an argument vector against the frozen copy and yield a record.
- AC-0005: a nonzero exit, a timeout and a kill mid-run each leave no passing record.
- AC-0007: the recorded digest matches the admitted product tree after the work tree is mutated post-run.
- AC-0009: several individually short commands whose summed running time passes 1200 seconds are ended and record no pass (a per-command fresh budget fails this case).
- AC-0010: a command printing over 1 MiB is ended and records no pass.
- AC-0011: the lock is not stale at the end of an execution, cleanup included.

**Approach:** freeze entries through the private-index machinery before running, `implementation-discovered` for the scratch materialization; discovery predicate: the candidate tree is reproducible from the recorded digest alone.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_execution.py -q` exits 0.

### T3: `report` requires matching proof

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_tdd.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_readiness.py`, `packs/core/tests/skills/work-loop/test_supervisor_results.py`, `packs/core/tests/skills/work-loop/test_supervisor_tdd.py`

**Tests:** TDD — unit and CLI, at `report_task` and `report_readiness`
- AC-0003, AC-0004: boolean-only reports and each mismatched field refuse with their codes and no ref moves.
- AC-0006: a consumed record refuses a second admission; an identical retry creates no second commit.
- AC-0016: a run pinned to the prior scripts still accepts the boolean (behavior pin on the existing path).

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_results.py packs/core/tests/skills/work-loop/test_supervisor_tdd.py -q` exits 0.

### T4: `correct-task` reopens a falsely admitted task

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_loop.py`, `packs/core/.apm/skills/work-loop/scripts/_evidence_store.py`, `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_step_loop.py`

**Tests:** TDD — integration, at the `correct-task` verb
- AC-0012: without an owner authority reference the request stays open and nothing is appended.
- AC-0013, AC-0014: with one, a correction record is appended and the task is issued again.
- AC-0015: dependent gates, reviews and later tasks go stale and earlier records remain.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_step_loop.py -q` exits 0.

### T5: `commit-record` lands declared ledger paths without adoption

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_loop.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_recovery.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_projector.py`, `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_product_ref.py`, `packs/core/tests/skills/work-loop/test_supervisor_integration.py`

**Tests:** TDD — integration with real Git, at the `commit-record` verb
- AC-0017, AC-0022: a declared ledger path lands once with its audit entry and no adoption request.
- AC-0018: a failed compare on either ref moves neither.
- AC-0019, AC-0020, AC-0021: one refusal case per listed cause moves no ref.
- AC-0023: a foreign commit still raises `history-adoption`; a kill between ref move and record write recovers through adoption.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_product_ref.py packs/core/tests/skills/work-loop/test_supervisor_integration.py -q` exits 0.

### T6: The review budget record and the spec-stage refusal

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/work-loop/scripts/review-artifact.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_readiness.py`, `packs/core/tests/skills/work-loop/test_review_carry.py`

**Tests:** TDD — unit, at the budget functions
- AC-0024, AC-0027, AC-0030: counts by phase and class under the definitions in the spec; the refusal at each cap lists open findings and never records clean; cases for the retained caps' scopes, simultaneous exhaustion of two limits, and the owner extension past each.
- AC-0028, AC-0029: one owner extension allows one round for either limit; a format-only replacement leaves the round count unchanged.

**Approach:** spec-stage rounds happen before a run exists, so the record's pre-admission home is `implementation-discovered`; predicate: the identity survives into `start`.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_review_carry.py -q` exits 0.

### T7: The budget carries across replan and adoption

**Depends on:** T6

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_loop.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_recovery.py`, `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_step_loop.py`

**Tests:** TDD — integration, at `status` and the replan and `adopt-history` paths
- AC-0026: counts are equal before and after each.
- AC-0025: `status` prints every count.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_step_loop.py -q` exits 0.

### T8: `start` refuses a primary or reserved checkout

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_admission.py`, `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_admission.py`, `packs/core/tests/skills/work-loop/test_supervisor_pinning.py`

**Tests:** TDD — integration with real Git, at `start` and `status`
- AC-0031, AC-0032, AC-0034: refusals, the recorded override, release on terminal, and a stale reservation.
- AC-0033: two concurrent `start` processes for different specs in one worktree leave one owner.
- AC-0035: `status` prints the store path and the worktree-removal warning.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_admission.py packs/core/tests/skills/work-loop/test_supervisor_pinning.py -q` exits 0.

### T9: Reference, skill text and evals describe each slice's behavior

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/work-loop/references/supervisor.md`, `packs/core/.apm/skills/work-loop/references/state-schema.md`, `packs/core/.apm/skills/work-loop/references/pre-execute-review.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/evals/evals.json`

**Tests:** goal-based, the existing doc-pin suites under `packs/core/tests/skills/work-loop/` and `packs/core/tests/pack/`

**Done when:** `python3 -m pytest packs/core/tests/pack packs/core/tests/skills/work-loop -q -k "doc or eval or reference"` exits 0 and `lint-spec-status.py` is clean.

### T10: Release each slice

**Depends on:** T9

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `tests/roster/test_registry_upgrade_notes.py`

**Tests:** goal-based, `check-core-release` and the roster upgrade-notes suite

**Done when:** `make precheck` exits 0 and `python3 -m pytest tests/roster/test_registry_upgrade_notes.py -q` exits 0.

### T11: The acceptance gaps found at final verification are closed

**Depends on:** T10

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_tdd.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_loop.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_readiness.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_review.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_commit.py`, `packs/core/tests/skills/work-loop/test_supervisor_execution.py`, `packs/core/tests/skills/work-loop/test_supervisor_results.py`, `packs/core/tests/skills/work-loop/test_review_obligation_policy.py`, `packs/core/tests/skills/work-loop/test_supervisor_admission.py`, `packs/core/tests/skills/work-loop/test_supervisor_step_loop.py`, `packs/core/tests/skills/work-loop/test_supervisor_crash_corpus.py`

**Tests:** TDD — unit and CLI, at the same seams as T2, T3, T6 and T8
- AC-0008: a `gate` object carrying any key beyond `passed`, at top level or nested, is refused under the new protocol, and a legacy run keeps its shape.
- AC-0009, AC-0010, AC-0011: a deterministic clock around the 1200 s cutoff, an overflow of 1 MiB plus one byte by a command that stays alive, and preparation and cleanup clocks near 2400 s.
- AC-0024: active hours are measured from issuance to report with a fake clock, reloaded, and printed by `status`; a waiting human decision writes nothing to the run store.
- AC-0027, AC-0030: a protected unit at its third numbered record gets an owner decision named `review-budget-exhausted` that offers only `extend-review` and `reselect-review`, and an `accept-risk` answer for it is refused.
- AC-0033: the losing concurrent `start` leaves the final `HEAD` and product ref at the winner's commit.

**Done when:** the T11 `Tests:` suites above exit 0 under `WORK_SUPERVISOR_INTEGRATION=1`, and the crash corpus compares killed and uninterrupted runs exactly.

### T12: The first review round's supported findings are closed

**Depends on:** T11

**Touches:** `packs/core/.apm/skills/work-loop/scripts/review-artifact.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_loop.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_execution.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_admission.py`, `packs/core/tests/skills/work-loop/test_review_carry.py`, `packs/core/tests/skills/work-loop/test_review_obligation_policy.py`, `packs/core/tests/skills/work-loop/test_supervisor_execution.py`, `packs/core/tests/skills/work-loop/test_supervisor_step_loop.py`

**Tests:** TDD — unit and CLI, at the seams the findings name
- AC-0028: after an owner `extend-review` the supervisor recorded, the numbered review recorder admits exactly the next round with no second extension flag, and refuses the round after it.
- AC-0009, AC-0010: a gate command whose supervisor is killed with SIGTERM or SIGKILL is ended at the execution deadline, leaves no completed record, and its scratch directory is removed by the next supervisor verb that finds the started record.
- AC-0032: reopening a terminal run with `correct-task` takes the checkout reservation again, and a start for another spec in that checkout is refused `checkout-reserved` until the run is terminal again.

**Done when:** the T12 `Tests:` suites above exit 0 under `WORK_SUPERVISOR_INTEGRATION=1`.

## Rollout

Delivery: one PR carrying all four slices, by the owner's decision at the T4 checkpoint. T9 and T10 run once after the last slice, so the reference, skill text, evals, version bump and changelog fragment cover every slice together. T11 closes the gaps that acceptance verification found after those tasks. The PR is reversible by revert before release. Active runs finish on the prior release and hit `supervisor-changed` until they regenerate, as the reference describes.

## Risks

Running gate commands is new authority for the supervisor; a malicious test still passes honestly, which the reference states. A gate-declaration syntax adopters must write is a new adopter-facing text (T1). The review budget touches the finding-adjudication path; a mistake could refuse a legitimate round, so the owner extension is the escape. Pinned-script churn can strand active runs.

## Changelog

- 2026-11-14: spec approved by eugenelim
- 2026-11-14: plan approved by eugenelim
