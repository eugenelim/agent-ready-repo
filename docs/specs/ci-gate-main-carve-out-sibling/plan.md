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

### T5: The round-1 review findings are repaired — dist/ materialization, comment sweep, stray-file removal

**Depends on:** T1, T2, T3, T4

**Tests:**
- The sibling job materializes `dist/apm/` (the catalogue projection,
  gitignored, so a fresh checkout has none) in an unconditional step after
  Python provisioning and before the probe, and the probe fails closed when
  `dist/apm/` is absent — the projected-variant cases in
  `tests/roster/test_credential_user_scope_invocation.py` run rather than
  silently skip in every PR — repairs review finding R1-001. Inside
  gate-main those cases ran after `make build-check` had materialized
  `dist/`; the sibling reproduces that precondition directly — AC-0001,
  AC-0008.
- The posture test pins the materialization step's name and body and the
  probe's extended check by equality; mutations that remove the step, empty
  or short-circuit its body, drop the probe's `dist/apm/` check, or move the
  step after the dispatch each redden, with no regression in the caught-
  mutation count — AC-0008.
- `grep` over `.github/workflows/build-check.yml` finds no comment still
  asserting the carve-out or dedup guard runs in gate-main, and no comment
  asserting `dist/apm/` skips in gate-main — repairs review finding R1-003
  (T3's sweep missed the step-placement rationales inside gate-main).
- The stray root `uv.lock` (a 3-line stub, `requires-python >= 3.14`, owned
  by no manifest) is deleted from the tree — repairs review findings R1-002
  and SEC-001.
- The ledger's input-revision record names branch-reachable revisions
  (before: the review base `6dc12944e`, whose workflow is byte-identical to
  the recorded before-state; after: the delivered T1 commit `3c690bcc6`)
  with correct labels, and its T4 section records the three verification
  commands' outcomes and runtimes — repairs review findings R1-004 and
  R1-005. These are controller-recorded execution observations: they land
  as controller history the owner adopts, not as an implement-step change
  set (the spec directory is protected for implement results).

**Approach:** the same extend-first order as T1 — the posture test's new
assertions and the fixture's new step redden against the current workflow
first (local red proof, never committed red), then one workflow edit greens
them: a `Materialize catalogue projections (gate-catalogue-tests)` step
running the same catalogue-build invocation gate-main's `make build-check`
chain runs (`python -m agentbundle catalogue build --root . --output dist`),
the probe gaining a `dist/apm/` existence check whose failure message names
the skip it prevents, and the false probe comment ("that suite skips in
gate-main today for the same reason") replaced with the corrected history.
The materialization step is unconditional (the sibling carries no step-level
`if:`); every shard pays its ~30–60 s, inside the 25-minute floor. The
comment sweep rewords the gate-main step-placement rationales that still
reference "the carve-out step below" for the two-job layout. `uv.lock` is
deleted; nothing consumes it.

**Touches:** `.github/workflows/build-check.yml`, `tools/test-build-check-workflow.py`, `tools/fixtures/build-check-good.yml`, `tools/lint-ci-parity.py`, `tools/test-lint-ci-parity.py`, `uv.lock` (deleted)

**Effects:** none

**Done when:** `python3 tools/test-build-check-workflow.py` exits 0,
`--self-test` reports every mutation caught with no count regression,
`python3 tools/lint-ci-parity.py` exits 0, `python3 tools/test-lint-ci-parity.py`
reports all cases passing, `uv.lock` is absent from the tree, the comment
grep comes back clean, and `make build-check` passes end to end — all after
one commit carrying the workflow edit and the tools' updates together.

### T6: The round-2 review findings are repaired — probe completeness, dispatch-channel pins, doc drift

**Depends on:** T1, T2, T3, T4, T5

**Tests:**
- The probe's executable set covers every executable the ledger's own
  static scan recorded as provisioning-relevant (adding `cat` and `grep`,
  the promotion-drain skip sites) — repairs review finding R2-001
  (AC-0008).
- The posture test pins the dispatch step's `env:` mapping by equality
  (`SHARD: ${{ matrix.shard }}` exactly), so a constant or conditional
  value that silently routes every shard to one branch reddens — repairs
  review finding SEC-R3-001 (AC-0007, AC-0001).
- The posture test rejects any step-level `if:` on any step in the
  sibling job (the probe being the load-bearing case: a skipped probe
  converts every provisioning gap back into a silent skip) — repairs
  review finding SEC-R3-002 (AC-0008).
- `docs/guides/how-to/cut-a-package-release.md` no longer attributes the
  roster collection to gate-main's removed step; it names the sibling's
  shard-1 — repairs review finding QE-R2-001 (AC-0004).
- The ledger's T1 red-proof section cites the delivered T1 commit
  `3c690bcc6` (byte-identical workflow), not the unreachable
  `a0ac3a36d`, and its probe-set record names the extended executable
  set — repairs review findings R2-002 and the R2-001 record half
  (controller-recorded; lands as controller history the owner adopts).
- Each new pin's efficacy is mutation-proven: a constant SHARD value, a
  conditional SHARD value, a probe `if:`, and a cat/grep drop from the
  probe each redden, with no count regression.

**Approach:** the same extend-first order — the new posture-test
assertions redden against the current workflow first (local red proof,
never committed red), then one edit greens them: the probe's executable
loop gains `cat grep` (all five are coreutils on every runner image, so
the fail-closed check has no false-positive risk), two new audit checks
(`sibling-dispatch-env-value-exact`, `sibling-no-step-if`) plus their
mutations join the matrix, and the release guide's stale attribution is
rewritten for the two-job layout.

**Touches:** `.github/workflows/build-check.yml`, `tools/test-build-check-workflow.py`, `tools/fixtures/build-check-good.yml`, `docs/guides/how-to/cut-a-package-release.md`

**Effects:** none

**Done when:** `python3 tools/test-build-check-workflow.py` exits 0,
`--self-test` reports every mutation caught with no count regression,
`python3 tools/lint-ci-parity.py` exits 0, `python3 tools/test-lint-ci-parity.py`
reports all cases passing, and the release guide names the sibling — all
after one commit carrying the workflow edit and the tools' updates
together.

### T7: The round-3 review findings are repaired — cwd pin, matrix-exclude pin, install-body pin

**Depends on:** T1, T2, T3, T4, T5, T6

**Tests:**
- The three pinned sibling steps (`Materialize catalogue projections`,
  `Probe provisioning`, `dispatch catalogue-test shard`) appear in
  `_NO_CWD_STEPS`, so a `working-directory:` key added to any of them
  reddens — repairs review finding R3-001 (AC-0001, AC-0008).
- The posture test rejects any `exclude:` (or `include:`) key under the
  sibling job's `strategy.matrix` block, so a one-line matrix exclusion
  that silently drops a shard replica reddens — repairs review finding
  SEC-R4-001 (AC-0007, AC-0001).
- The sibling's `Install Python dependencies` step body is pinned by
  equality (`PINNED_INSTALL_BODY`), so a prepended fetch line or a
  re-pointed requirements source reddens — repairs review finding
  SEC-R4-002 (AC-0008).
- Each new pin's efficacy is mutation-proven: a `working-directory:` key
  on each of the three steps, an `exclude:` entry dropping shard-2, and
  a curl line added to the install body each redden, with no count
  regression in the families that already exist.
- The ledger records the three repairs with their red-before-green
  proof (controller-recorded; lands as controller history the owner
  adopts).

**Approach:** extend-first, the same order as T5/T6 — the new posture-test
assertions redden against the current workflow first (local red proof,
never committed red), then one edit greens them: three `_NO_CWD_STEPS`
entries, one matrix-key rejection check, one `PINNED_INSTALL_BODY` with
its body-equality check, and their mutations join the matrix. No workflow
bytes change except the fixture's mirrored model if it carries the same
steps.

**Touches:** `tools/test-build-check-workflow.py`, `tools/fixtures/build-check-good.yml`

**Effects:** none

**Done when:** `python3 tools/test-build-check-workflow.py` exits 0,
`--self-test` reports every mutation caught with no count regression,
`python3 tools/lint-ci-parity.py` exits 0, and `python3 tools/test-lint-ci-parity.py`
reports all cases passing — all after one commit carrying the tools'
updates.

### T8: The round-4 review findings are repaired — matrix pin closed as a class, job-level defaults pinned

**Depends on:** T1, T2, T3, T4, T5, T6, T7

**Tests:**
- The sibling's entire `strategy:` block is pinned by equality
  (`PINNED_STRATEGY_BODY`, the file's pin-the-whole-set doctrine), so any
  edit to the block — a quoted `'exclude':`, a duplicate `matrix:` key, a
  blank-line-separated `exclude:`, a shrunken or extended shard list —
  reddens — repairs review findings SEC-R5-001, SEC-R5-002, SEC-R6-001
  (AC-0007, AC-0001).
- The posture test asserts exactly one `strategy:` key and exactly one
  `matrix:` key in the sibling job block (the duplicate-aware counting
  mechanism), so a duplicate block reddens even before the equality pin
  compares text — closes the duplicate-key class directly (AC-0007).
- The posture test rejects a `defaults:` block at job level in the sibling
  job (and gate-main), closing the job-level `working-directory:` channel
  the step-level `_NO_CWD_STEPS` entries cannot see — repairs review
  finding SEC-R6-002 (AC-0008, AC-0007).
- The matrix↔case cross-pins keep reading the pinned strategy block's
  shard list; the existing matrix mutations (single shard, shrunk list,
  extra entry, bare exclude) still redden, plus the five recorded bypass
  shapes each redden: quoted `'exclude':`, duplicate `matrix:` with
  `exclude:`, duplicate `matrix:` with `shard: [shard-1]`, blank-line-
  separated `exclude:`, and job-level `defaults: run: working-directory:`.
- The ledger's T7 section is corrected to record what was actually proven
  (mutation-matrix catch of the seven bare spellings) and the round-4
  falsification, per finding QE-R4-002 — no recorded-as-verified claim the
  same run's review records contradict (controller-recorded; lands as
  controller history the owner adopts).

**Approach:** class-closing, not spelling-patching — the strategy block
becomes ONE equality pin exactly like the step bodies (the ladder-doctrine:
set-equality needs no enumeration of the tricks it excludes), with
exactly-one key counts and a job-level defaults rejection beside it. The
old `sibling-matrix-no-exclude` regex check is REPLACED by the equality pin
and counts (not kept alongside: a check that can be bypassed is worse than
no check, because it records a held dimension that is not held).

**Touches:** `tools/test-build-check-workflow.py`

**Effects:** none

**Done when:** `python3 tools/test-build-check-workflow.py` exits 0,
`--self-test` reports every mutation caught with no count regression,
`python3 tools/lint-ci-parity.py` exits 0, and `python3 tools/test-lint-ci-parity.py`
reports all cases passing — all after one commit carrying the tools'
updates.

### T9: The round-5 review findings are repaired — anchor/alias/merge keys rejected, ledger count corrected

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8

**Tests:**
- The posture test rejects YAML anchor, alias, and merge-key syntax anywhere
  in the workflow (`&anchor` definitions, `*alias` references, `<<:` merge
  keys), so a merge-carried job-level `defaults:` — or any other key the
  spelled-key checks read — cannot bypass the pin family — repairs review
  finding R5-001 (AC-0001, AC-0002, AC-0007, AC-0008). The rejection follows
  the file's declared-canonical-subset doctrine (`_UNMODELLED_KEY_RE`): fail
  closed on every unmodelled form rather than model the merge semantics.
- Mutations prove it: a top-level anchor block plus a `<<: *anchor` merge
  line under the sibling job (shell variant) and under the aggregator job
  each redden, and an `*alias` reference and an `&anchor` definition each
  redden on their own.
- The ledger's T8 section records six shapes where it says seven, and
  attributes the duplicate-`strategy:` shape to the strategy pin when the
  count checks catch it — corrected to state exactly what was proven —
  repairs review finding QE-R5-001 (AC-0007) (controller-recorded; lands as
  controller history the owner adopts).
- The pinned-constant comment claiming "every structural edit reddens" is
  narrowed to "every structural edit inside the block", so it cannot be read
  as covering duplicate bindings.

**Approach:** one new audit check (`no-anchor-alias-merge`) scanning the
whole workflow text for the three syntaxes, plus its mutations; the ledger
and comment corrections ride the controller's foreign commit.

**Touches:** `tools/test-build-check-workflow.py`

**Effects:** none

**Done when:** `python3 tools/test-build-check-workflow.py` exits 0,
`--self-test` reports every mutation caught with no count regression,
`python3 tools/lint-ci-parity.py` exits 0, and `python3 tools/test-lint-ci-parity.py`
reports all cases passing — all after one commit carrying the tools'
updates.

### T10: The round-6 review findings are repaired — anchor/alias/merge check closed and scoped

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T9

**Tests:**
- The `no-anchor-alias-merge` arms are separator-, charset-, and
  position-agnostic: any whitespace after the `:`/`-` separator (double
  spaces included), any name characters (digit-initial included), and
  merge keys at line start, in sequence position, and in flow position —
  repairs review finding R6-001 (AC-0001, AC-0002, AC-0003, AC-0007,
  AC-0008).
- The check scans a structural view of the workflow with `run:` block-scalar
  bodies removed, so shell text in run bodies cannot false-positive it —
  repairs review finding QE-R6-002 (AC-0001, AC-0008). A line like
  `echo "- *note:* …"` in a run body stays green.
- Every arm has an exclusive mutation: a flow-mapping merge
  (`<<: {shell: …}`, merge arm only), an alias-only reference, and an
  anchor-only definition each redden the check when the other arms would
  not — repairs review finding QE-R6-001 (AC-0001, AC-0008).
- Mutations carry the non-canonical spellings from R6-001: a
  sequence-position merge with double-space separation and a
  digit-initial anchor name, each verified to redden.

**Approach:** broaden the three regexes, feed them a run-body-free view
of the workflow (the `no-duplicate-step-keys` indent-scoping precedent,
  applied by removing block-scalar content before matching), and add the
  exclusive and non-canonical mutations.

**Touches:** `tools/test-build-check-workflow.py`

**Effects:** none

**Done when:** `python3 tools/test-build-check-workflow.py` exits 0,
`--self-test` reports every mutation caught with no count regression,
`python3 tools/lint-ci-parity.py` exits 0, and `python3 tools/test-lint-ci-parity.py`
reports all cases passing — all after one commit carrying the tools'
updates.

### T11: The round-7 review findings are repaired — env allowlist fail-closed, parse-layer anchor/alias/merge rejection

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

**Tests:**
- The step-env key reader fails closed on a flow-style `env:` mapping: any
  `env:` key line carrying a non-empty inline value reddens the allowlist
  check for every job's steps (block style still enumerates keys as
  before) — repairs review finding SEC-R9-001 (AC-0008). Mutations: a
  flow-style `env: {PIP_INDEX_URL: …}` on the sibling install step and a
  flow-style `env: {MAKEFLAGS: '-n'}` on gate-main's anchor each redden.
- A parse-layer anchor/alias/merge rejection joins the chain as the
  class-closing control: a new PyYAML-based check (in a file that already
  loads PyYAML — `tools/lint-ci-parity.py`'s neighborhood or
  `tools/test-ci-security-workflow.py`) walks the parsed document for
  merge keys, anchors, and aliases as TOKEN classes — position-, spelling-,
  and style-independent — and reddens on any of them anywhere in the
  workflow — repairs review findings R7-001 and QE-R7-002's prescribed
  closure (AC-0001, AC-0002, AC-0003, AC-0007, AC-0008). The stdlib regex
  in the posture test stays as defense-in-depth, and its boundary is
  recorded in the module's deliberately-not-asserted section: the regex
  reader models the canonical spellings only; the parse-layer check owns
  the class.
- The run-body stripper gains committed regression control: a mutation
  carrying an alias-matching echo inside a run body (which the stripper
  must keep out of the check's view) reddens if the stripping is removed
  or narrowed — repairs review finding QE-R7-001 (AC-0001, AC-0008).
- The stripper's own coverage gap (plain `run:` values, folded `run: >-`
  bodies, post-blank `|` content) is closed: the stripper treats every
  `run:` block or flow scalar value as body text — repairs review finding
  R7-002 (AC-0001, AC-0008). A mutation placing an alias-matching echo in
  each body form (plain, folded, post-blank) stays green when the stripper
  is correct.

**Approach:** fail-closed env reading in the stdlib posture test plus
committed regression mutations; the parse-layer check as a new assertion
in the PyYAML-wired chain surface; the boundary record in the posture
test's doctrine section.

**Touches:** `tools/test-build-check-workflow.py`, `tools/test-ci-security-workflow.py`

**Effects:** none

**Done when:** `python3 tools/test-build-check-workflow.py` exits 0,
`--self-test` reports every mutation caught with no count regression,
`python3 tools/test-ci-security-workflow.py` exits 0 with the new
anchor/alias/merge rejection green on the shipped workflow and red on a
merge-key-bearing fixture, `python3 tools/lint-ci-parity.py` exits 0, and
`python3 tools/test-lint-ci-parity.py` reports all cases passing — all
after one commit.

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
