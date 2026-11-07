# Plan: gate-main's catalogue-test carve-out runs in a sharded sibling job

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `tools/AGENTS.md` (roster-edit obligations) and
  ADR-0122 (gate-main step conditions) are the convention sources. Analogous
  implementations: `.github/workflows/test-corpus.yml`'s `corpus` matrix job
  (the shard pattern this copies) and `gate-css-tokens` in
  `.github/workflows/build-check.yml` (a small sibling gate job already modeled
  and checkout-pinned by the posture test). Construction path:
  `tools/test-build-check-workflow.py` (extend-first, its mutation matrix is
  the fail-closed oracle) and `tools/test-lint-ci-parity.py` (roster self-test).
  Named uncertainty: the sibling's exact provisioning set — marked
  `implementation-discovered` under Failure & resilience, guarded by a
  fail-closed probe.

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

## Approach

One task, one commit carries the whole structural change: the posture test and
the parity rosters are extended first so their new assertions redden against
the current workflow (the sibling job does not exist yet), then the single
workflow edit — a new `gate-catalogue-tests` matrix job whose one per-shard
dispatch step holds the two moved steps' invocations verbatim in a shard-keyed
`case` dispatch, the two steps deleted from `gate-main`, and the sibling wired
into the aggregator's `needs`, env vars, and guard — turns them green. The
red proof is a local run inside the task, not a committed red state, because
the spec's same-commit rail forbids any commit that carries a workflow edit
without both tools' updates. The command-set preservation proof (a mechanical
before/after listing) and the comment/doc refresh complete the slice. The
riskiest part is extending `tools/test-build-check-workflow.py` without
weakening its existing pins; the mutation matrix's caught-count is the guard
against that.

## Constraints

- ADR-0101 — one pytest process per invocation; compatibility classes must not
  be merged or split across shards.
- ADR-0122 — gate-main step `if:` conditions stay roster-derived; the two steps
  leave gate-main, and the sibling's steps carry no step-level `if:` at all
  (the test-corpus shape), so no new admitted expressions are introduced.
- RFC-0082 — the moved set is exactly the carve-out destinations; the ownership
  boundaries (which suite lives where) do not change.
- `docs/specs/ci-gate-parallelization/` AC3 — the aggregator keeps its shape:
  one env var per dependency, one inline `!= "success"` test with its consequent
  on the same statement, guard running in the aggregator job.
- `docs/specs/test-corpus-sharding/` — the copied shard pattern: matrix entries
  are the only thing that varies per shard, `fail-fast: false`, timeout floored
  on serial maximum, `runs-on: ubuntu-latest` exactly.
- `tools/AGENTS.md` — every added/moved build-check.yml step gets a
  two-axis `STEP_DISPOSITION` entry; hyphenated `tools/test-lint-*.py` files
  are run directly, never via a pytest sweep.
- The spec's same-commit Always-do rail — the workflow edit, the posture-test
  extension, and both parity-roster updates land in one commit; no task is
  done, and no commit exists, in a state `make build-check` rejects.

## Construction tests

Integration tests: `python3 tools/test-build-check-workflow.py` (and
`--self-test` for the mutation matrix) plus `python3 tools/lint-ci-parity.py`
against the edited workflow — both chained by `make build-check`, so the PR's
own gate exercises them end to end.
Manual verification: `python -m pytest tools/test_local_ci_shared_test_deduplication.py -q`
locally (the moved dedup-guard suite must still pass against the unchanged
Makefile), and the before/after invocation listing recorded in
`notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current architecture truth — `docs/architecture/verification-graph.md` | T3 | Updated prose naming the sibling, its shards, and the aggregator edge | Statement matches the shipped workflow |
| Maintainer procedure — the workflow's per-job local-reproduction map | T3 | A `gate-catalogue-tests` entry beside the map's existing entries | Each named local command reproduces its job's checks |
| Command-set preservation record — `notes/verification-ledger.md` | T2 | The mechanical before/after invocation comparison | Listing shows the one-to-one match with zero added/removed |

## Design (LLD)

### Design decisions

- **Workflow-side shard lists (mechanism B), realized as one per-shard dispatch
  step.** The sibling carries a single unconditional step whose run body holds
  every moved invocation verbatim inside a shard-keyed `case` dispatch —
  `env: SHARD: ${{ matrix.shard }}` on the step, `case "$SHARD" in 1) … ;; 2)
  … ;; 3) … ;; *) echo unknown-shard; exit 1 ;; esac` in the body, under
  `set -euo pipefail`. GitHub Actions matrix replicas share one job's steps,
  so distinct per-shard step bodies would require step-level
  `if: matrix.shard == N`, which this plan forbids (the test-corpus shape
  carries no step `if:`) and which `tools/lint-ci-parity.py`'s
  `_source_satisfies_pr_gated` rejects for `PR_GATED` sources — it admits a
  conditional source only when its `if:` exactly equals a roster-derived
  `!cancelled() && …` expression, which no matrix predicate can be. The single
  dispatch step keeps every invocation verbatim in the workflow (mechanism B's
  settled decision), keeps the step unconditional so every `PR_GATED` entry
  naming either moved step corroborates against one step name and keeps its
  kind (the `SUITE_DISPOSITION` roster is the closed set; the
  controller-verified count is 42, all `pr-gated`), and gives the posture
  test one body to pin. Traces to: AC-0001, AC-0006. Rests on: the lint's
  corroboration arm
  reading suite paths from the dispatch body (they remain plain text inside
  the case branches). Owned by: T1.
- **Weight-balanced shard split; canonical count in the spec's Assumptions.**
  `pytest tests/` (~90 s in `tools/shard_test_roster.py`'s WEIGHTS) is the
  floor invocation; the 27-file tools group, the dedup guard (~29–65 s), and
  the pack suites distribute around it. The shard count is the spec's
  Assumptions line, not restated here. The exact split is pinned by the
  posture test's dispatch-body pin, so rebalancing is a deliberate pinned
  edit. Traces to: AC-0007. Owned by: T1.
- **The sibling follows the test-corpus job shape, not gate-main's phase
  pattern.** No step-level `if:` in the sibling; provisioning steps are
  unconditional and a fail-closed probe runs before the dispatch step. This
  keeps ADR-0122's admitted-expression machinery untouched (its scope is
  gate-main) and matches the copied precedent. Traces to: AC-0008. Owned by: T1.

### Interfaces & contracts

The sibling's public surface is its check names and the aggregator edge: job
id `gate-catalogue-tests`, a matrix of the shard count the spec's Assumptions
record, `fail-fast: false`, `runs-on: ubuntu-latest`, `timeout-minutes: 25`
(floored on serial maximum — a shard that somehow ran the whole carve-out
takes serial time, ~6–7 min). The aggregator gains
`GATE_CATALOGUE_TESTS_RESULT: ${{ needs.gate-catalogue-tests.result }}` and
one guard line with its consequent on the same statement. The parity rosters
re-point: `_GATE_MAIN_CHECKS` drops the two moved names, the sibling's steps
join the non-gate-main phase pattern (`CHECK((), "outside gate-main; …")`),
and every `SUITE_DISPOSITION` entry naming the gate-main carve-out or
dedup-guard step keeps its `PR_GATED` kind and names the sibling's dispatch
step. Traces to: AC-0002, AC-0003, AC-0004, AC-0005, AC-0006. Owned by: T1.

### Failure & resilience

Fail-closed paths: a red invocation fails its shard's case branch and the
step, the matrix job fails, the aggregator's `!= "success"` guard fails, the
required check blocks the PR. A cancelled, skipped, or never-instantiated
sibling (empty matrix) reports a non-success result through the same guard.
An unknown `SHARD` value hits the `*)` branch and exits 1 rather than running
nothing. Missing provisioning reddens the probe step by name before the
dispatch step can let suites silently skip. The exact provisioning set is
`implementation-discovered` by a **skip-aware procedure**: the moved
invocations run locally in an environment no richer than the sibling's
candidate provisioning set (a richer environment — gate-main's, for
example, which provisions several tools the sibling does not — hides a
missing dependency as a green run) with skip reporting enabled (a
temporary `-rs`, never committed) and every skipped test accounted for, so
a dependency whose absence manifests as a pytest skip — which exits green
— feeds into the probe rather than shipping silently (pytest exits 0 on
skips and `-q` prints no skip reasons, so a green run alone discovers
nothing; the probe then covers the discovered set — the discovery, not the
probe, is what must be skip-audited). The
starting point is the spec's Assumptions provisioning line (test-corpus's
precedent minus npm). Traces to: AC-0002, AC-0003, AC-0008. Owned by: T1.

### Quality attributes

The runtime claim is structural pre-merge: `gate-main` no longer contains the
two steps whose combined median is ~287 s against a re-profiled ~874 s job
median, which lands the remainder under the intent's 600 s target. The
post-merge median is the intent's non-blocking re-measurement follow-up, not a
gate. Traces to: spec Outcome; AC-0004 is the pre-merge evidence. Owned by: T1,
T2.

## Tasks

### T1: The sibling job exists, is posture-pinned, roster-covered, and aggregator-gated — one commit

**Depends on:** none

**Tests:**
- New posture-test assertions redden against the unmodified workflow (red
  phase, local run, never committed red): job `gate-catalogue-tests` absent,
  aggregator `needs` lacking it — AC-0002, AC-0004, AC-0007.
- After the workflow edit, `python3 tools/test-build-check-workflow.py` exits 0:
  the sibling is in `REQUIRED_WORK_JOBS`/`EXPECTED_JOB_NAMES`, its checkout
  `with:` mapping is pinned (fetch-depth 0, persist-credentials false), its
  matrix and `fail-fast: false` asserted, its dispatch body pinned, and the
  aggregator's needs/env/guard statements pinned — AC-0002, AC-0003, AC-0004,
  AC-0007, AC-0008.
- The posture test pins the probe's checks by equality alongside the
  dispatch body — the probe's step is pinned, its probed-dependency checks
  are pinned, and removal, body-emptying, and dependency-dropping mutations
  each redden — AC-0008.
- `python3 tools/test-build-check-workflow.py --self-test` reports every new
  mutation caught: sibling dropped from `needs`, env-var line dropped, guard
  line dropped, probe step removed, a moved step name reintroduced in
  gate-main, and the matrix↔case-branch cross-pin proven red in each
  direction — a shrunken matrix (an entry removed) and an extra matrix
  entry each caught, or one both-direction set-comparison mutation if the
  cross-pin is implemented as a single comparison — and the probe's
  efficacy proven like its presence: a mutation that empties or
  short-circuits the probe body and a mutation that drops one probed
  dependency each caught — and the pre-existing mutation count does not
  fall — AC-0002, AC-0003, AC-0004, AC-0007, AC-0008.
- `python3 tools/lint-ci-parity.py` exits 0 with every sibling step
  dispositioned on both axes — AC-0005 — and every `SUITE_DISPOSITION` entry
  that gated a moved suite keeping its `PR_GATED` kind and naming the
  sibling's dispatch step; a deliberately stale `where` (pointed back at the
  gate-main step name) reddens the lint — AC-0006.
- `python3 tools/test-lint-ci-parity.py` (run directly; hyphenated entry
  point) passes its full case set including a new case whose mutation flips
  one moved suite's entry to `NO_PR_GATE` and reddens — AC-0006.

**Approach:** extend `tools/test-build-check-workflow.py` and
`tools/lint-ci-parity.py` first and prove the new assertions red against the
current workflow, then make the single workflow edit that greens them — the
red-green order is what proves the pins bite.
- The workflow edit, the posture-test extension, and both parity-roster
  updates land in one commit (the spec's same-commit rail); the red proof is
  the local pre-edit run, not a committed red state.
- The dispatch step carries the shard key via step `env`
  (`SHARD: ${{ matrix.shard }}`), keeping template expressions out of the run
  body so the lint parses pure shell; each invocation moves byte-identical
  inside its case branch, one pytest process per invocation.
- The sibling's provisioning is unconditional (test-corpus shape), ending
  in a fail-closed probe modeled on test-corpus's "Probe provisioning"
  step, derived by the skip-aware procedure the spec's Assumptions record
  (the moved invocations run locally in an environment no richer than the
  sibling's candidate provisioning set, with temporary `-rs`; every skipped
  test is accounted for; provisioning-caused skips feed the probe set).
- Two posture-test allowlists gain deliberate, enumerated entries the
  design forces: `_ALLOWED_STEP_ENV` gains exactly `SHARD` (the dispatch
  step's env key) and `GATE_CATALOGUE_TESTS_RESULT` (the aggregator guard's
  env binding) — it is the control against env-key forgery, so the
  widening is named here rather than made as an unnamed
  make-the-test-pass edit — and `_PROVISIONING_NOT_AUDITED` gains the
  sibling's provisioning step names so they fall outside the gate-main
  phase-condition audit.
- The posture test derives the matrix shard set and the dispatch body's
  case-branch set and cross-pins them against each other in both directions
  (the test-corpus matrix↔`SHARDS` discipline), so a shrunken matrix cannot
  silently un-run a branch's suites while every gate stays green.
- The posture test's recorded empty-matrix safety reason ("once AC2 requires
  it by name the PR hangs") gains the sibling's actual route: the sibling is
  outside branch protection, so an empty or never-instantiated matrix reports
  a non-success result the aggregator's guard catches, plus the AC-0007
  matrix pin reddens the posture test itself.

**Touches:** `.github/workflows/build-check.yml`, `tools/test-build-check-workflow.py`, `tools/lint-ci-parity.py`, `tools/test-lint-ci-parity.py`

**Effects:** none

**Done when:** `python3 tools/test-build-check-workflow.py` exits 0,
`--self-test` reports every mutation caught with no count regression,
`python3 tools/lint-ci-parity.py` exits 0, and
`python3 tools/test-lint-ci-parity.py` reports all cases passing — all after
one commit that carries the workflow edit and both tools' updates together.

### T2: The command-set preservation proof is recorded

**Depends on:** T1

**Tests:**
- A mechanical comparison of the two steps' before-listing (from the base
  commit's workflow) against the invocations inside the sibling's dispatch
  body shows a one-to-one invocation match, zero missing, zero added —
  AC-0001.
- The comparison and its method are recorded in
  `docs/specs/ci-gate-main-carve-out-sibling/notes/verification-ledger.md`.

**Approach:** the comparison is a throwaway script run against two revisions
(base vs. head) — never committed — whose output is pasted into the ledger;
the standing control is the posture test's dispatch-body pin from T1.

**Touches:** `docs/specs/ci-gate-main-carve-out-sibling/notes/verification-ledger.md`

**Effects:** none

**Done when:** the ledger holds the before/after listings and records the
one-to-one result.

### T3: Comments and architecture docs match the two-job layout

**Depends on:** T1

**Tests:**
- The workflow's per-job local-reproduction map carries a
  `gate-catalogue-tests` entry; the stale placement comments that referenced
  the carve-out's position inside gate-main are reworded for the two-job
  layout; `test-corpus.yml`'s header line that credits gate-main with
  `pytest tests/ -q` names the sibling.
- `docs/architecture/verification-graph.md` names the sibling job, its shards,
  and the aggregator edge.
- `grep` over `.github/workflows/` finds no comment still asserting the
  carve-out or dedup guard runs in gate-main.

**Approach:** comment-only and doc-only edits; no behavioral change rides in
this task.

**Touches:** `.github/workflows/build-check.yml`, `.github/workflows/test-corpus.yml`, `docs/architecture/verification-graph.md`

**Effects:** none

**Done when:** the three greps/two reads above come back clean and the
posture test still exits 0 (comments it pins — e.g. the gate-main phase
header — are untouched or updated consistently).

### T4: The moved suites and the full gate chain are green

**Depends on:** T1, T2, T3

**Tests:**
- `python -m pytest tools/test_local_ci_shared_test_deduplication.py -q`
  passes locally — the moved dedup-guard suite against the unchanged Makefile.
- `make lint-ruff lint-mypy` passes.
- `make build-check` passes end to end (it chains the posture test and
  lint-ci-parity, so the PR's own gate is the integration proof).

**Effects:** none

**Done when:** all three commands exit 0; runtime and any failures recorded in
the verification ledger.

## Rollout

One PR, no flag, fully reversible by revert (workflow YAML plus the tools
files; no data, no schema, no external state). The aggregator's new dependency
goes live with the merge. Pull requests open at the merge keep their existing
check results until they next evaluate; a `pull_request` event evaluates the
merge ref, so any subsequent push or re-run then executes the new graph — the
required-check name is unchanged and nothing weakens, so no partial state
exists at any point. The sibling is deliberately not added to branch
protection — the aggregator, a required check, gates it. The post-merge
`gh api` re-measurement is the intent's non-blocking follow-up.

## Risks

- **Weakening the posture test while extending it.** Its existing pins and
  mutation count are the guard: `--self-test` must not report fewer caught
  mutations, and the pre-existing assertion families stay green.
- **A provisioning gap makes suites skip silently in the sibling.** The
  fail-closed probe names the missing dependency before the dispatch step
  runs; the parity lint's reachability checks corroborate.
- **A shard split that regresses wall-time.** The split is weight-balanced from
  measured data and pinned; a rebalance is a deliberate edit, not drift.
- **Stale comments mislead the next editor.** T3 sweeps them; the posture
  test's pinned comments (if any are touched) reddens on inconsistency.

## Changelog

<!--
Approvals, and nothing else.

- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->

- 2026-11-07: spec approved by eugenelim (scope)
- 2026-11-07: plan approved by eugenelim (build strategy)
