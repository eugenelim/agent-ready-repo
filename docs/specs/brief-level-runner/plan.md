# Plan: brief-level runner

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version bump, self-host, eval harness, no internal citations, UTF-8 streams, pack-test loader rule); `tests/AGENTS.md` (roster tests and their named build-check step); `dispatch.py` `dispatch()` and `_header_readiness.py` as the readiness owner; `author-delivery-brief/scripts/lint-brief-coverage.py` as the Spec map parser precedent; `_supervisor_git.HardenedGit` as the hardened Git launcher; `_file_safety.read_confined_regular_file` as the read path; `lint-knowledge.py` `field_problems` with its `body` policy as the one standing-orders character rule; `_supervisor_admission._check_lease` and its lease key constants as the one lease rule; `_supervisor_loop.State.attempt` as the failed-attempt count; `supervisor_harness.py` and `test_supervisor_parked_gates.py` as the analogous integration tests.

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
> attempt is open.

## Approach

The supervisor-side changes land first (T1: lease policy and `failed_attempts`), because `classify` reads the budget and the controller reads the count. The runner's read core — Spec map, worktree discovery, stop and ordering — is T2, and `next`, `gates` and `status` build on it in T3. Standing orders (T4) slot into `next` and `status` after they exist. The cross-verb no-approval property (T5) runs once every verb exists. Guidance, eval and the roster pin (T6) follow the code they describe; the release (T7) is last.

This delivery runs from the installed supervisor copy, which these edits change only at self-host. T1 edits pinned supervisor files, so it is made while no `WORK_SUPERVISOR_INTEGRATION=1` run is live in this worktree.

## Constraints

- ADR-0159 D1–D10 fix the runner's read-only shape, ordering, worktree-per-slice rule, gates join, derived status, standing orders, pilot, lease policy, failure taxonomy and the human gates; widening any needs a new ADR.
- ADR-0157 D3, D4, D7: `gates` is per checkout, nothing turns a parked gate into an approval, and a parked spec gets no implementation dispatch.
- ADR-0156 is unchanged: each slice keeps its own sequential run.
- RFC-0099 §7 and the root `AGENTS.md` never-cut rule stay intact.
- The supervisor pins every file under `scripts/` and `supervisor-policy.json` at `start`; `brief-runner.py` is pinned with no pin-list edit.
- A pack test may not read above its pack; the governance pin lives in `tests/roster/` with a named step above the bulk step in `.github/workflows/build-check.yml`.
- The supervisor integration lane in `.github/workflows/catalogue-tooling-ci-gates.yml` lists its suites by file; a new integration suite joins that list.
- Two required edits sit outside their task's `Touches`: `tools/lint-ci-parity.py` (T6; registers the new roster step, verified by `tools/lint-ci-parity.py` exiting 0) and `tests/roster/test_registry_upgrade_notes.py` (T7; re-points the core release pin, verified by that suite passing). The PR lists both under `Bundled fixes:`.

## Construction tests

**Unit tests:** `packs/core/tests/skills/work-loop/test_brief_runner_units.py` (Spec map parse, standing-orders format, `classify`, marker function).
**Integration tests:** `packs/core/tests/skills/work-loop/test_brief_runner.py`, gated by `WORK_SUPERVISOR_INTEGRATION=1` and added to the lane in `.github/workflows/catalogue-tooling-ci-gates.yml` by T2, which creates it, over fixture repositories with a bare `origin` and linked worktrees built by `supervisor_harness.py`; `failed_attempts` cases in `test_supervisor_tdd.py`. **Unit tests** also include `test_supervisor_policy_lease.py`.
**Roster test:** `tests/roster/test_human_approval_gates_pinned.py`.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale | none — ADR-0159 committed `Accepted` before approval | ADR file | cited in `Constrained by:` |
| Maintainer procedure | T6 | content tests green | suites green at the delivery commit |
| Current architecture | T6 | § 9 planned-leases bullet edited | bullet names `lease` |
| Operations (policy) | T6 | state-schema row, or recorded rationale | row present |
| Release history | T7 | version-equality assertion; fragment | release check result recorded |

## Design (LLD)

### Interfaces & contracts

Owned by: T2, T3, T4. Traces to AC-0009, AC-0010, AC-0013, AC-0016, AC-0020.

- `brief-runner.py status|next|gates <brief-slug> [--root <dir>]` and `brief-runner.py classify <brief-slug> --slice <slug> --task <task-id> --class <c> [--root <dir>]`. Every verb prints one JSON object. Exit 0 on an answer, 1 on a refusal `{"refusal": {"code", "detail"}}`, 2 on a usage error.
- `next` → `{"base": <commit>, "action": {...}, "standing_orders": ...}`. Action kinds: `resume-slice {slice, worktree, stage}`, `start-slice {slice, branch, mode, spec_status, plan_status}`, `await-gates {gates}`, `await-merge {slices}`, `complete {}`, `blocked {rows: [{slice, reason}]}`. Reason codes are the closed set AC-0009 names.
- `classify` → `{"action": "<name>", "failed_attempts": <n>}`; it reads `lease.retry_budget` from the policy file beside it and `n` from the slice's supervisor `status --json`. The class stays the controller's judgment: it only chooses among bounded actions, and the count that bounds them is supervisor-derived.

### Data & schema

Owned by: T1, T4. Traces to AC-0015, AC-0018, AC-0019.

- `supervisor-policy.json` gains `"lease": {"heartbeat_seconds": 1800, "stuck_after_seconds": {"implementer": 2700, "reviewer": 1800, "slice-session": 5400}, "retry_budget": 2, "max_slices_in_flight": 2}`. Values other than `retry_budget` are starting defaults, correctable by a policy edit.
- `failed_attempts` is `State.attempt(task) - 1` for the task's current revision, the count the supervisor already derives from committed `gate-fail` receipts.
- Standing orders: `docs/product/standing-orders/<brief-slug>.md`, read as the base commit's blob through the hardened Git launcher (`cat-file blob <base>:<path>`, mode checked as a regular file); the 16384-byte cap, the line rule and the hidden-character check run before `text` is emitted. `fence` is a backtick run of length max(3, longest backtick run in `text` + 1).

### Behavior & rules

Owned by: T2, T3. Traces to AC-0002, AC-0004, AC-0006, AC-0007, AC-0008, AC-0009, AC-0012, AC-0014, AC-0028, AC-0029.

- Base: the main worktree is the first `worktree` record of `git worktree list --porcelain -z`; `--root` must resolve to it. The default branch is the target of `refs/remotes/origin/HEAD`. Because `HEAD` equals that commit and `docs/` has no modified, staged or untracked file, the working-tree reads `dispatch.py` makes equal the base commit's bytes; the runner itself reads standing orders as blobs.

- Readiness reuse: the runner loads `dispatch.py` by path and calls `dispatch(root)` once. `dispatch` evaluates only `Approved` specs (`_STATUS_COLLECTION` maps `Approved` to the queue, `Implementing` to active, `Shipped` to shipped; a probe on 2026-11-05 showed the brief's eight `Shipped` specs absent from all three public lists), so its `ready` list decides an `Approved` row, and a `Draft` or missing spec follows the earlier-rows rule with no header read.
- Worktree discovery parses `git worktree list --porcelain -z` through the hardened launcher, skips the main worktree, and keeps entries whose `branch` line is exactly `refs/heads/brief/<brief-slug>/<spec-slug>` for a row in the Spec map.
- Supervisor calls run the `work-supervisor.py` beside the runner (never a slice branch's copy, which a worker controls) with the slice worktree as working directory: `status <spec-dir> --json` and `gates`. `status` is skipped when the branch head has no `<spec-dir>/spec.md` (`work-supervisor.py` `_spec_rel` would exit 2), giving `drafting`. Without `--check`, `status` exits 0 and carries a refusal inside its view (`work-supervisor.py` `main`; `_supervisor_loop.status`), so the runner keys on the view's top-level `refusal`, never on the exit code (`run.refusal` mirrors it; `readiness.refusal` only sets `readiness.ready` false): `no-approval` gives `drafting`, any other refusal gives `refused`, and `run.gate_pending` (a supervisor `human-decision` request) gives `awaiting-decision`. `supervisor-changed` arrives two ways: as exit 1 when the slice's pins differ from the copy beside the runner (`_preflight`), which gives stage `supervisor-changed`, and inside the exit-0 view for an unrecorded first admission (`_supervisor_recovery._unnamed_first_admission`), which is `refused` and carries the supervisor's own detail; the supervisor admits only two exits for that run, finish it on its prior release or start it again (`SKILL.md` regenerate rule; `references/supervisor.md`), so the runner routes it to a human. Other exit-1 answers carry a bare refusal with no `run` view (invalid installed policy, Git error, `internal-error`; `status` takes no run lock, so never `run-locked`) and give `unreadable`, as do exit 2 and a shape mismatch.
- `marker` = SHA-256 over the branch head commit id, the tree id of `<spec-dir>/delivery` at that head (or the empty string), and the canonical JSON of that slice's `gates` entries, or the literal `unavailable`. The `gates` listing reads the working-tree spec directory (`_is_pending`, `_valid_entry`, `_plain_dirs` in `_supervisor_gates.py`), so a spec-directory edit that changes it is a real side effect and moves the marker.

### Failure, edge cases & resilience

Owned by: T2, T3, T5. Traces to AC-0001, AC-0002, AC-0011, AC-0029.

- A dirty base refuses before any supervisor call.
- A missing or unreadable slice worktree path makes that row `unreadable`; it is never `merge-ready`.
- The runner runs no `git fetch`; the controller fetches before calling it.

## Tasks

### T1: Lease policy and failed-attempt count

- **Depends on:** none
- **Touches:** `packs/core/.apm/skills/work-loop/supervisor-policy.json`, `scripts/_supervisor_admission.py`, `scripts/_supervisor_loop.py`, `packs/core/tests/skills/work-loop/test_supervisor_policy_lease.py` (unit, ungated), `packs/core/tests/skills/work-loop/test_supervisor_tdd.py` (the gate-fail suite, already in the integration lane)
- **Mode:** TDD
- **Tests:** policy loader refusals for a missing table, a missing or extra key, a non-integer, a zero value and a `retry_budget` other than 2 (AC-0018); `status --json` after two reported gate failures on one task shows `failed_attempts` 2 for it and 0 for an untouched task, and 0 for the replanned revision while `retry_count` keeps both (AC-0019, AC-0030).
- **Done when:** the T1 tests pass and the existing supervisor integration lane stays green.

### T2: Runner read core

- **Depends on:** T1
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/brief-runner.py`, `packs/core/tests/skills/work-loop/test_brief_runner_units.py`, `test_brief_runner.py`, `.github/workflows/catalogue-tooling-ci-gates.yml` lane list
- **Mode:** TDD
- **Tests:** Spec map parse and refusals (AC-0003); each base refusal in order — a linked worktree as root, no `origin/HEAD`, `HEAD` behind the fetched tip, a modified, a staged and an untracked file under `docs/` and a modified runner skill file (AC-0002); ready rule for `Approved` rows via `dispatch.py` (one blocked by an `Implementing` dependency), `Draft` and spec-less rows behind an unstopped earlier row, and an `Implementing` row (AC-0004); `merged`, `merge-ready` and `none` stops from a fixture worktree with a terminal run (AC-0006); a worktree on another branch name is ignored and a `prunable` one is `unreadable` (AC-0007); `drafting` before the spec directory exists and for the exit-0 `no-approval` view, `refused` for an `unsupported-ref-storage` view beside an independent ready row that `next` still names, `refused` for a view-borne `supervisor-changed` (unrecorded first admission), `supervisor-changed` when the slice's run was started by a differing supervisor copy, for an unfinished run and for a terminal, ready run whose `merge-ready` stop it hides, and `unreadable` for an invalid installed policy and for exit 2 (AC-0032); the supervisor launched is always the runner's sibling (AC-0006).
- **Done when:** the T2 tests pass.

### T3: `next`, `gates`, `status`

- **Depends on:** T2
- **Touches:** `brief-runner.py`, `test_brief_runner.py`
- **Mode:** TDD
- **Tests:** pilot hold with the pilot in flight and with the pilot parked, and a blocked first row whose successor becomes the pilot (AC-0008); one fixture per `next` action and per reason code in AC-0009's order, including a terminal run that is not ready, a `human-decision` row beside an independent ready row that `next` still names, a controller-owned standing refusal `status` really returns (`attempt-residue`), and one row where two reasons apply; a parked non-pilot slice beside a ready one (AC-0012); the in-flight cap (AC-0028); a `stale`, an `invalid` and an `unavailable` gate each blocking `gate-not-clean` (AC-0029); `gates` join across two worktrees after real `park` calls, JSON-equal supervisor fields, and an `invalid` entry with no `spec_dir` sorted last in its slice (AC-0010); a worktree whose supervisor call fails lists `unavailable` (AC-0011); `status` field set (AC-0013); marker equal across two unchanged calls and under `.supervisor/` and `.loop-run/` edits, changed by a commit, a delivery record, a park and a spec edit that turns a parked gate `stale`, and `unavailable` folded in when `gates` fails (AC-0014); store and Git state unchanged after every verb (AC-0001).
- **Done when:** the T3 tests pass in the integration lane.

### T4: Standing orders

- **Depends on:** T3
- **Touches:** `brief-runner.py`, `test_brief_runner_units.py`, `test_brief_runner.py`
- **Mode:** TDD
- **Tests:** format accepts `1.`…`n.` and refuses a gap, a wrapped line, a hidden character and an oversize file (AC-0015); `next` and `status` emit the base blob's bytes even when a slice branch holds other bytes, a fence longer than a backtick run in the text, `null` for no file, and `invalid-standing-orders` for a bad one (AC-0016).
- **Done when:** the T4 tests pass.

### T5: No approval from the runner

- **Depends on:** T4
- **Touches:** `brief-runner.py`, `test_brief_runner.py`, `test_brief_runner_units.py`
- **Mode:** TDD
- **Tests:** `classify` table including the budget edge and an unknown class above the budget, and each refusal — unknown slice, no worktree, unknown task, unavailable status (AC-0020); three failures each reported before `classify` runs, reaching `abandon-and-replan` on the third (AC-0030); the parser's verb set and a launcher seam that records every argv, asserting only read-only Git and supervisor `gates`/`status` (AC-0022); an approve-everything standing-orders file beside a pending gate (AC-0023).
- **Done when:** the T5 tests pass.

### T6: Guidance, eval, pin

- **Depends on:** T5
- **Touches:** work-loop `SKILL.md`, `references/brief-runner.md`, `references/unattended-loops.md`, `references/state-schema.md`, `evals/evals.json`, `docs/architecture/work-loop-execution-supervisor.md`, `tests/roster/test_human_approval_gates_pinned.py`, `.github/workflows/build-check.yml`, the work-loop guidance content test
- **Mode:** goal-based
- **Tests:** content test for AC-0017, AC-0021 and AC-0031 over `references/brief-runner.md`, including the report-before-classify order, the threshold for each dispatch kind, the effect exclusion and the never-clear-a-refusal rule, plus the `SKILL.md` pointer; eval schema check for AC-0025; roster test for AC-0024, each failure shown red by removing the pinned text in a temporary copy.
- **Done when:** the T6 tests pass and the eval harness check is green.

### T7: Release

- **Depends on:** T6
- **Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/<uuid>.md`, self-host projections
- **Mode:** goal-based
- **Tests:** release version check and catalogue lint and verify (AC-0026, AC-0027).
- **Done when:** both checks exit 0 and the tree is clean after self-host.

### T8: Review round 1 repairs

- **Depends on:** T7
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/brief-runner.py`, `references/brief-runner.md`, `evals/evals.json`, `packs/core/tests/skills/work-loop/test_brief_runner.py`, `test_brief_runner_units.py`, `test_brief_runner_guidance.py`
- **Mode:** TDD
- **Tests:**
  - Git hardening (AC-0001, AC-0002): every runner Git call runs with the supervisor's hardening — an allowlisted environment and no attribute-, filter- or diff-defined program — proved by a fixture whose shared config sets a clean filter and an attributes entry for a stat-dirty `docs/` file and whose environment sets `GIT_CONFIG_PARAMETERS` and `GIT_OBJECT_DIRECTORY`; the filter never runs and the base reads are unchanged.
  - Worktree path (AC-0007, AC-0013): a slice worktree whose path holds a control, hidden or line-separator character is `unreadable` and its path is never emitted or used as a working directory.
  - Standing orders (AC-0015): a file holding CR, ESC, DEL, NEL, U+2028, U+2029 or a zero-width run over the knowledge lint's bound is refused `invalid-standing-orders`.
  - Clean base (AC-0002): an uncommitted or untracked `workspace.toml` refuses `base-not-committed`.
  - Lease policy (AC-0020, AC-0033): an unreadable or invalid base policy makes `next`, `status` and `classify` refuse `invalid-policy` instead of acting on 0, reached through a real committed bad policy.
  - Diagnostics (AC-0009, AC-0032, AC-0004): an `unreadable` row and a `not-dispatchable` row caused by a `dispatch.py` failure each carry a bounded `detail` naming the cause, with no new reason code.
  - Spec map (AC-0003): an empty first cell refuses `invalid-spec-map`, and a row whose slug is `spec` after the separator is a row, not a header.
  - Read-only (AC-0001): `classify` joins the before/after Git and store comparison over a slice with a live run.
  - Ordering (AC-0004): a `Draft` row whose `Depends on:` names an unmerged spec, after stopped rows, is ready in `shape` mode.
  - Stop (AC-0006): a `Shipped` row with a live, non-terminal slice worktree reads `merged`.
  - Guidance and eval (AC-0017, AC-0025): the reference passes standing orders to every spawned slice session and every resume as well as every implementer and reviewer dispatch; the eval's first assertion requires working the ready slice with no alternative; the content test fails on an alternative outcome and pins the routing text.
  - Suite cost: the three-failures case classifies in-process and leaves the replan and retry-count assertion to `test_supervisor_tdd.py`; the standing-orders cases share one module-scoped world.
- **Done when:** the T8 tests pass, the existing brief-runner suites stay green, and lint is clean.

### T9: Review round 2 repairs

- **Depends on:** T8
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/brief-runner.py`, `packs/core/tests/skills/work-loop/test_brief_runner.py`, `test_brief_runner_units.py`
- **Mode:** TDD
- **Tests:**
  - Git version and filter names (AC-0002): the runner takes the minimum Git version, the filter-name rule and the filter override list from the supervisor's Git module as the one definition; a Git below the minimum refuses `unsupported-git-version` before any Git command other than `git version`; a repository filter named with `=` and one whose name is not valid UTF-8 each refuse `denied-git-config` before `git status` runs, and the planted filter never runs; the refusal order matches AC-0002.
  - Standing orders (AC-0015): the T8 cases stay; new cases refuse interleaved short joiner runs over the lint's invisible budget and a run of more than the lint's whitespace bound, and accept an ordinary numbered list.
  - Lease policy (AC-0018, AC-0020, AC-0028, AC-0033): the runner judges the base `lease` table with `_check_lease` loaded from the sibling module; committed policies with `max_slices_in_flight` 0, `retry_budget` -1, `retry_budget` 3, `max_slices_in_flight` `true`, a missing top-level key, an extra top-level key, a missing `stuck_after_seconds` kind, an extra kind and a `stuck_after_seconds` value of 0 each refuse `invalid-policy` from `next`, `status` and `classify`; the shipped policy is accepted; `invalid-policy` follows the AC-0002 refusals and precedes `invalid-spec-map`.
- **Done when:** the T9 tests pass, the existing brief-runner suites stay green, and lint is clean.

## Rollout

- **Delivery:** additive; the runner is read-only and opt-in, so a controller that never calls it behaves as before. Reversal is reinstalling the prior Core release.
- **Deployment sequencing:** merge after any open wave-2 change to the supervisor scripts that the planner orders first.

## Risks

- Pin churn: T1 changes pinned supervisor files, so a run started on the prior Core release refuses `supervisor-changed` after this release lands: an unfinished one is finished on the prior release or started again, and a finished one still merges.
- Ordering mismatch: a brief with a wrong `Depends on:` header orders slices wrongly; the runner reports what the headers say.

## Changelog

- 2026-11-05: spec approved by eugenelim (scope)
- 2026-11-05: plan approved by eugenelim (build strategy)
- 2026-11-06: amendment approved by eugenelim (scope)
- 2026-11-06: amendment approved by eugenelim (build strategy)
