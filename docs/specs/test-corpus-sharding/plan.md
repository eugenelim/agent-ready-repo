# Plan: Shard the test corpus across parallel runners

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `Makefile:513-651` (the `test` target, the
  `run-test-suite` macro, and its two call sites);
  `tools/test_local_ci_shared_test_deduplication.py:1000-1018,1052-1070`
  (which Makefile surfaces are digest-pinned and which target rules are
  structurally pinned); `tools/lint-ci-parity.py:87-100,1150-1158`
  (`WORKFLOW_SCOPE` and the only check it applies to an out-of-scope file);
  `Makefile:235-240` with `.github/workflows/build-check.yml:866` (the existing
  `print-*` convention for exposing Makefile-owned data to CI).
  Named uncertainty: the per-invocation timing table is complete only for the
  six invocations the owner measured; the rest fall back to a declared default,
  which degrades balance but never correctness.

> **Plan contract:** this is the implementation strategy.

## Approach

The shape of the change is a *selector*, not a second roster. The Makefile
already holds the only roster, inside the `override define run-test-suite`
macro. `make -n test-unleased` expands that macro — including the `$(3)`
parameter in its correct roster position — into the exact command list the
target would run. The shard runner reads that expansion, classifies each line,
partitions the work lines by measured time, and executes its slice. Nothing
restates a suite anywhere.

The riskiest part is not the partitioning arithmetic; it is the possibility of
*silently* dropping a suite. Every design choice below is bent toward making
that loud: an unclassifiable line is a hard error rather than a skip, an
out-of-range or empty shard is a hard error rather than a no-op success, and the
union property is asserted mechanically against the live Makefile rather than
read from output.

Order of operations: build and prove the selector first (T1–T3), wire the
Makefile only once the selector is correct (T4), then the workflow (T5), then
measure on real runners and write the measurement down (T6), then the companion
prose (T7). The measurement task depends on the workflow already being pushed,
so it is necessarily last among the code tasks.

`test-unleased` and `run-test-suite` are not edited. Only the `test:` target
changes, and it is the one surface in this area that is neither digest-pinned
nor structurally pinned.

## Constraints

- **ADR-0101** and `tools/pack_test_compatibility.py` own which suites may share
  a pytest process. Sharding redistributes whole invocations only; it never
  regroups them, so the approved classes are untouched and
  `tools/lint-pack-test-boundary.py` re-derives the same answer.
- **`tools/lint-ci-parity.py`'s `WORKFLOW_SCOPE`** keeps `test-corpus.yml` out
  of scope. That disposition rests on the workflow invoking `make test`
  undecomposed, which stays true per job: the workflow enumerates nothing. The
  reason text is refreshed to describe the matrix without changing the
  classification.
- **`MAKE_BASELINE_DIGESTS`** pins eight Makefile surfaces including their
  comments. None of them is `test:`, `test-unleased`, or `run-test-suite`, so
  none of those eight moves.
- **`APPROVED_STANDALONE_PLAN_DIGEST` and `APPROVED_COMPOSED_PLAN_DIGEST`**
  (`tools/test_local_ci_shared_test_deduplication.py:552-557`) hash the whole
  normalized command plan of `make test` and `make test-after-build-check`.
  Both stay put: no file joins the roster, so neither plan changes. Verified
  before any edit — both reproduce exactly (`7fadaf20…` over 62 lines,
  `e48c8b01…` over 61), which is also the evidence that a later unexpected move
  would be caused by this change rather than pre-existing drift.
- **`tools/test_marketplace_envelope_parity.py:731`'s `_assert_gate_wiring`**
  requires the Makefile's pytest group and `build-check.yml`'s to be exactly
  equal. This is why no test file is added to the roster: doing so would force
  an edit to `build-check.yml`, which is a non-goal.
- **`test-corpus.yml:36-40`** forbids `self-hosted`, runner groups, expressions,
  and larger-runner names. `runs-on: ubuntu-latest` stays an exact literal; the
  matrix varies only a shard integer.

## Construction tests

**Integration tests:** the union property (T3) drives real `make` against the
working tree's Makefile rather than a fixture, so it fails when the roster
changes shape in a way the classifier cannot handle. This is the one test that
must not use a synthetic roster — a partitioner proven only against a fixture
proves nothing about the roster that actually runs.

**Manual verification:** dispatch the sharded workflow and read the per-job
durations from the real run (T6). No local timing substitutes: this machine is
at a load average above 80 and its figures are not transferable.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current architecture truth (`verification-graph.md`) | T7 | Updated prose | Statement matches shipped workflow |
| Maintainer procedure (`AGENTS.md`) | T7 | Dispatch line verified against the shipped workflow | Command as written dispatches it |
| Reusable learning (posture-assertions intent) | T7 | Intent cites this spec as a multi-job instance | Open question cites a real multi-job workflow |

## Design (LLD)

### Design decisions

- **Roster by expansion, not by parsing.** The runner obtains the roster from
  `make -n test-unleased`, not by re-implementing Make's macro expansion. The
  alternative — parsing the `define` body and substituting `$(1)`/`$(2)`/`$(3)`
  — would be a second implementation of Make, and would silently diverge the
  moment a parameter or conditional changed. Traces to: AC: roster unchanged from 28a169531 · AC: union is exact.
- **Roster acquisition is fail-closed in two directions, one of them before
  Make runs.** A non-zero dry-run status aborts before anything executes,
  because a truncated expansion would otherwise be sharded and run as if it
  were the whole roster. That check is necessary but not sufficient for one
  specific hazard: GNU Make *executes* a recipe line containing `$(MAKE)`, and
  runs a `+`-prefixed line, even under `-n` — so by the time such a line
  appeared in the output, a roster line would already have run. The runner
  therefore scans the `test-unleased` recipe and the `run-test-suite` body for
  those two constructs and refuses before invoking Make at all. Neither exists
  there today.

  The scan claims nothing wider, because nothing wider is checkable. Expanding
  the roster is *not* side-effect-free and never was: `Makefile:10` resolves
  `PYTHON` through `$(shell python3 …)`, which launches a process on every Make
  invocation, `-n` included, sharded or not. A guard over transitive variable
  expansion has no bounded form, and asserting one would be a check that cannot
  fail honestly. What this scan buys is exact and worth having — a roster
  *line* cannot acquire the power to run while it is being read.
  Traces to: AC: non-zero expansion refuses · AC: recursive-Make construct refuses.
- **The proofs live in a module the roster already invokes.** A construction
  test that only ever ran by hand would let a later selector regression ship
  green — but adding a new test file to the roster is not available:
  `tools/test_marketplace_envelope_parity.py:731`'s `_assert_gate_wiring`
  requires the Makefile's pytest group and `build-check.yml`'s to be *equal*,
  so a new file would force an edit to `build-check.yml`, which is an explicit
  non-goal. It would also change the unsharded expansion and so contradict the roster-unchanged criterion.
  The proofs therefore go into
  `tools/test_local_ci_shared_test_deduplication.py`, which the roster already
  invokes, which already owns Makefile roster semantics, and whose node-set
  pins (`CORE_COLLECTIONS`, `PROVEN_COMPATIBLE_FILES`) do not cover itself. No
  file joins the roster, no plan digest moves, and `build-check.yml` is
  untouched. Traces to: AC: roster unchanged from 28a169531 · AC: proofs run inside make test.
- **Fail-closed classification.** Every roster line is classified as a declared
  precondition, a recognized runner invocation, or a comment. Anything else is a
  hard error naming the line. A future Makefile line in an unanticipated shape
  therefore stops the shard runner rather than being silently dropped from every
  shard. Traces to: AC: unclassifiable line refuses.
- **Preconditions replicate; work partitions.** The roster's preconditions (the
  editable-install guard, the `import httpx` probe, the npm and `node_modules`
  guards) are cheap and exist to convert a silent skip into a named failure. If
  the `import httpx` probe landed in a different shard from the Atlassian suites
  it guards, it would stop protecting them. Replicating every precondition in
  every shard costs milliseconds and preserves the fail-closed posture each one
  was added for. Traces to: AC: preconditions run in every shard.
- **Longest-processing-time-first partitioning.** With 66% of measured time in
  three invocations, round-robin leaves one shard at roughly five minutes while
  others finish in seconds. LPT assigns the heaviest invocation first to the
  currently-lightest shard. Ties break on roster index so the partition is
  deterministic and a test can assert it. Traces to: AC: partition uses the weight table.
- **Weight lookup keyed on the first path argument.** Invocation flags change
  more often than target paths do. A key derived from the first path argument
  survives a flag edit; if a key ever does miss, the invocation falls back to a
  declared default weight, degrading balance without touching correctness.
  Traces to: AC: partition uses the weight table.

### Component / module decomposition

`tools/shard_test_roster.py` — new, pure-stdlib, underscore-named so the test
can import it (matching `tools/pack_test_compatibility.py` and
`tools/posture_harness.py`). Four responsibilities, each independently
testable:

- `roster_lines()` — refuse a recursive-Make construct in the roster-bearing
  bodies, run `make -n test-unleased`, refuse a non-zero status, return raw
  lines.
- `classify(line)` — precondition / work / comment / error.
- `partition(units, shards)` — pure; LPT over the weight table.
- `main()` — validate the selector, then execute preconditions followed by this
  shard's work units, failing fast on the first non-zero exit.

`tools/test_local_ci_shared_test_deduplication.py` — **existing** (about 2,400
lines), extended with the shard-runner construction tests. Not a new file: it is
already invoked by the roster, already owns Makefile roster semantics, and its
node-set pins do not cover itself, which is exactly why the proofs live here.

### Failure, edge cases & resilience

- Shard index out of range, non-integer, or one variable set without the other
  → exit non-zero before any invocation runs.
- Shard count exceeding the number of work units → exit non-zero, because an
  empty shard is a job that passes while proving nothing.
- Unclassifiable roster line → exit non-zero naming the line.
- A work invocation exiting non-zero → the shard stops there and propagates the
  code. Fail-fast is preserved *within* a shard only: with `fail-fast: false` on
  the matrix, the other shards run to completion rather than being cancelled, so
  one dispatch reports every shard's real result instead of only the first
  failure. That is a deliberate difference from the serial target, which stops
  the whole roster at its first failure.

### Quality attributes (NFRs)

The sharding floor is the longest single invocation, currently 174.7s. No shard
count lowers the makespan below it. Four shards put the predicted makespan near
that floor, which is why the spec's timeout criterion is expressed as a multiple
of the measured slowest shard rather than as an absolute minute count.

## Tasks

### T1: The shard runner classifies every roster line or fails

**Depends on:** none

**Touches:** tools/shard_test_roster.py, tools/test_local_ci_shared_test_deduplication.py

**Tests:**
- A declared precondition line classifies as a precondition. (AC: preconditions run in every shard)
- A `-m pytest <path>` line classifies as work. (AC: union is exact)
- A comment line and a blank line classify as ignorable.
- A command line matching neither a precondition nor a recognized runner shape
  raises, and the message contains the offending line. (AC: unclassifiable line refuses)

- A `test-unleased` recipe or `run-test-suite` body containing `$(MAKE)`,
  `${MAKE}`, or a `+`-prefixed line is refused *before* Make is invoked,
  asserted with a fixture Makefile carrying each construct.
  (AC: recursive-Make construct refuses)

**Approach:**
- Write `classify()` with an explicit precondition tuple, each entry commented
  with the precondition it enforces, and a recognized-runner tuple.
- Raise a named error on anything else.
- Put the recursive-Make scan on the Makefile text, ahead of the subprocess
  call, so the refusal precedes the hazard rather than reporting it.

**Done when:** the four classification tests are green and the error message
names the unclassified line verbatim.

### T2: Selector validation refuses every shard that would prove less

**Depends on:** T1

**Touches:** tools/shard_test_roster.py, tools/test_local_ci_shared_test_deduplication.py

**Tests:**
- Parameterized across both variables: negative, zero, and non-integer values
  for each of `SHARD` and `SHARDS` each exit non-zero. (AC: invalid selector refuses)
- `SHARD` greater than `SHARDS` exits non-zero. (AC: invalid selector refuses)
- `SHARD` set without `SHARDS`, and `SHARDS` set without `SHARD`, each exit
  non-zero. (AC: one-sided selector refuses)
- `SHARDS` greater than the work-unit count exits non-zero. (AC: empty shard refuses)
- A dry-run expansion returning non-zero aborts. (AC: non-zero expansion refuses)
- Each rejection happens before any invocation is executed, asserted by a
  recording double in place of the executor recording zero calls.

**Approach:**
- Validate in `main()` before constructing the partition.
- Keep the executor injectable so the "nothing ran" half is observable.

**Done when:** every listed selector exits non-zero with the executor recording
zero invocations.

### T2a: Execution boundaries and precondition replication are observable

**Depends on:** T2

**Touches:** tools/shard_test_roster.py, tools/test_local_ci_shared_test_deduplication.py

**Tests:**
- The recording executor receives exactly one call per work unit assigned to
  the shard — never one call carrying two units, never two calls splitting one.
  (AC: one process per invocation)
- Every declared precondition appears in the executor's call list for every
  shard index, including a shard owning no work that precondition guards.
  (AC: preconditions run in every shard)
- A non-zero exit from one work unit stops the shard and propagates that code,
  with no later unit executed.

**Approach:**
- Execute each unit as its own subprocess invocation rather than joining units
  into one shell string.
- Assert on the recorded argument lists, not on a count alone: a count cannot
  tell a merged call from a split one.

**Done when:** the merge case and the split case are both caught by the
recorded argument lists.

### T3: The shards' union is exactly the unsharded roster

**Depends on:** T1

**Touches:** tools/shard_test_roster.py, tools/test_local_ci_shared_test_deduplication.py

**Tests:**
- For each shard count 1 through 8, concatenating `partition()`'s output over
  shards `1..N` equals the live roster's work units as a multiset — no
  duplicate, no omission. Driven against the real Makefile, not a fixture. (AC: union is exact)
- Every shard is non-empty at each of those counts.
- The partition is deterministic: two calls return identical assignments.
- The partition balances by the recorded weight table, not by roster position:
  at a shard count of 4 the heaviest and second-heaviest invocations land in
  different shards, which a round-robin or roster-order assignment fails.
  (AC: partition uses the weight table)
- Mutation proofs, each recorded with its expected failure: dropping the last
  unit from the partition output; assigning one unit to two shards; and
  replacing the weight lookup with a constant.

**Approach:**
- Compare multisets so an accidental duplicate is caught as loudly as an
  omission.
- Read the roster through `roster_lines()` so the test and the runtime share one
  source.

**Done when:** the union test is green at all eight counts and red under each of
the three recorded mutations.

### T4: `make test` gains a selector without changing its unsharded behavior

**Depends on:** T2, T3

**Touches:** Makefile

**Tests:**
- `make -n test-unleased` expands identically to the same command run against
  the Makefile this change merges into (`git show origin/main:Makefile`), proven by diffing
  the two expansions. The baseline is that committed file, not a
  remembered or re-derived one. (AC: roster unchanged from 28a169531)
- `make test SHARD=1 SHARDS=4` and its siblings 2, 3, 4 each run green.
- `python3 -m pytest tools/test_local_ci_shared_test_deduplication.py -q` stays
  green, including the `test-unleased` target-rule and `MAKE_BASELINE_DIGESTS`
  assertions.

**Approach:**
- Edit only the `test:` target, guarding on whether `SHARD`/`SHARDS` are set.
- Leave `test-unleased`, `test-after-build-check-unleased`, and
  `run-test-suite` byte-identical.
- Keep the coordination lease on both branches.

**Done when:** the expansion diff is empty, all four shards run green, and the
deduplication suite passes.

### T4a: The roster is unchanged and both plan digests hold

**Depends on:** T4

**Touches:** nothing — this task is verification only

**Tests:**
- `make -n test-unleased` output is byte-identical to the same command run
  against the Makefile this change merges into (`git show origin/main:Makefile`). (AC: roster unchanged from 28a169531)
- Both approved plan digests still reproduce: `7fadaf20…` over 62 standalone
  lines and `e48c8b01…` over 61 composed lines, recomputed through
  `_effective_composition_errors`. (AC: proofs run inside make test)
- `python3 -m pytest tools/test_local_ci_shared_test_deduplication.py -q` is
  green with no digest edited.

**Approach:**
- Confirm no file was added to the roster and `build-check.yml` is untouched.
- Recompute both digests and compare against the unchanged pinned values.

**Done when:** the expansion diff is empty, both digests match their existing
pins, and no pinned value was edited.

### T5: The workflow runs one undecomposed command per shard

**Depends on:** T4a

**Touches:** .github/workflows/test-corpus.yml, tools/test_local_ci_shared_test_deduplication.py,
tools/lint-ci-parity.py

**Tests:**
- The workflow contains no suite path, no pytest invocation, and no test-file
  name, asserted by a pinned predicate with mutation cases for each of those
  three shapes rather than an ad-hoc pattern. (AC: no roster in an executable run: scalar)
- The job has exactly one test-execution step, whose command is a single
  `make test` invocation. (AC: one test-execution step)
- The matrix's shard indexes are exactly `1..SHARDS`, read from the same
  workflow file: the test parses the `SHARDS=` literal out of the `make`
  command and compares it against the matrix list, so the two cannot drift
  apart. Mutation cases: a matrix of `[1,2,3]` against `SHARDS=4`, and a matrix
  with a duplicated index. (AC: matrix equals 1..SHARDS)
- `runs-on:` is the exact literal `ubuntu-latest`. (AC: runs-on is the exact literal)
- `python3 tools/lint-ci-parity.py` exits 0. (AC: lint-ci-parity exits 0)
- `test-corpus.yml` is still out of scope in `WORKFLOW_SCOPE`. (AC: test-corpus stays out of scope)

**Approach:**
- Add `strategy: matrix: shard: [1,2,3,4]` with `fail-fast: false`, so one
  failing shard does not mask another's result.
- Change the final step to `make test SHARD=${{ matrix.shard }} SHARDS=4`.
- Refresh the `WORKFLOW_SCOPE` reason to describe the matrix without changing
  the classification.

**Done when:** the matrix/`SHARDS` agreement test is red under both recorded
mutations and green as shipped, and `lint-ci-parity.py` exits 0.

### T6: The sizing comment states a measurement from a sharded run

**Depends on:** T5

**Touches:** .github/workflows/test-corpus.yml

**Tests:** no stub (manual QA) — the figure is read from a dispatched run.

**Approach:**
- Push the branch, dispatch `test-corpus.yml` against it, and read each job's
  duration from the completed run.
- Replace the estimate comment with the slowest shard's measured duration, the
  run it came from, and no instruction for a later reader. (AC: sizing comment states a measured run)
- Set `timeout-minutes` to the greater of three times that figure and the
  recorded 17.0-minute serial maximum, plus headroom. Three times a
  four-minute shard is twelve minutes, which is *below* the serial maximum — so
  a shard that degraded to running the whole corpus would time out instead of
  reporting its real result. The serial figure is the binding floor. (AC: timeout floors on the serial maximum)
- If the shard count or timeout changes for any reason, repeat the whole loop:
  commit, push, dispatch, re-measure, and re-verify. A figure describing a
  superseded configuration is the same defect this task exists to remove.

**Done when:** the comment names a real run id, the durations came from that
run's jobs rather than this machine, and the recorded configuration is the one
that produced them.

### T7: Companion statements describe the workflow as it now runs

**Depends on:** T6

**Touches:** docs/architecture/verification-graph.md, AGENTS.md,
docs/product/intents/dispatch-workflow-posture-assertions.md

**Tests:**
- `python3 '<skill-dir>/scripts/lint-spec-status.py' --root .` reports no
  dangling reference introduced by this change.
- Each edited statement is checked against the shipped workflow, not against
  this plan. (AC: verification-graph and the posture intent match the shipped workflow)

**Approach:**
- Update `verification-graph.md`'s description of what `test-corpus.yml` runs.
- Verify `AGENTS.md`'s dispatch line still works unchanged; edit only if it does
  not.
- Add a line to the posture-assertions intent naming this spec as a concrete
  instance of the multi-job workflow its open question anticipates.

**Done when:** every edited statement matches the shipped workflow.

## Rollout

- **Delivery:** big bang, fully reversible. The change is additive: reverting
  the workflow restores a single-job dispatch, and reverting the Makefile
  restores the pre-change `test:` target. Nothing is migrated and nothing is
  published.
- **Infrastructure:** none beyond GitHub-hosted `ubuntu-latest` runners, which
  are free for this public repository. Measured peak concurrency across the last
  25 runs was 20 jobs; four more is within observed headroom.
- **External-system integration:** none.
- **Deployment sequencing:** the workflow must be pushed before it can be
  dispatched, so T6's measurement necessarily follows T5's push.

## Risks

- **A future Makefile line in an unanticipated shape stops the shard runner.**
  This is the intended trade: a loud stop is the correct response, because the
  alternative is a suite silently absent from every shard. The error message
  names the line and the file to edit.
- **Weight drift.** The timing table is a snapshot. As suites change, balance
  degrades gradually while correctness holds exactly. The makespan is bounded
  below by the longest invocation regardless, so drift costs minutes, never
  coverage.
- **Four shards is a guess until measured.** The floor is 174.7s; if the
  measured makespan lands well above it, the shard count is a one-integer edit
  in two places.

## Changelog

- 2026-09-13: initial plan.
- 2026-09-13: revised from pre-EXECUTE adversarial review. Seven blockers,
  five concerns and two nits were all sustained. The substantive changes: the
  new test module joins `FINAL_TOOL_BATCH` and both approved plan digests are
  re-pinned (T4a), because a construction test outside the roster protects
  nothing; the workflow matrix and its `SHARDS` literal are pinned to agree
  (T5), because two independent literals let a shard silently never run; the
  timeout floor became the recorded serial maximum rather than three times the
  slowest shard, which would have timed out below it; roster acquisition became
  fail-closed on a non-zero dry run; execution boundaries and precondition
  replication gained a recording-executor task (T2a); and the baseline for the
  unsharded-preservation check is now a committed Makefile rather than an
  uncaptured "before".
- 2026-09-13: revised again from review round 2. Four blockers and two concerns
  sustained. The decisive one: `tools/test_marketplace_envelope_parity.py:731`
  requires the Makefile's pytest group and `build-check.yml`'s to be *equal*, so
  round one's plan to add a new test file to the roster would have forced an
  edit to `build-check.yml` — a non-goal — and would also have changed the
  unsharded expansion, contradicting AC1. The proofs moved into
  `tools/test_local_ci_shared_test_deduplication.py`, which the roster already
  invokes and whose node-set pins do not cover itself; T4a became verification
  only and both digest re-pins disappeared. Also: roster acquisition now refuses
  recursive-Make and `$(shell)` constructs by scanning Makefile *text* before
  invoking Make, because `-n` executes them before any output check could see
  them; the six measured weights and the derived default are now recorded
  values rather than an implementer's choice, with a 6-minute makespan bound
  that forces a re-dispatch; the workflow predicate is scoped to executable
  `run:` scalars, because the file's comments legitimately mention `tests/` and
  a test name; and the baseline names the branch point literally rather than
  the moving `HEAD`.
- 2026-09-13: round 3 closed five of six round-2 findings. The sixth was
  answered by narrowing the claim rather than hardening the check. The reviewer
  correctly observed that scanning two recipe bodies cannot make `make -n`
  side-effect-free, because `Makefile:10` resolves `PYTHON` through
  `$(shell python3 …)` and launches a process on every invocation. That is
  pre-existing, identical for serial `make test`, and has no bounded guard — so
  the criterion now claims only what it can hold: a roster *line* cannot
  execute during discovery, via a scan for `$(MAKE)` and `+`-prefixed lines in
  the roster-bearing bodies. Also: the plan's positional `ACn` references were
  replaced with stable descriptors, because inserting criteria in round 2 had
  silently shifted every one of them.
- 2026-09-14: amended after measuring on a runner. The brief's per-invocation
  figures were a partial decomposition -- six invocations named, 52 guessed --
  and the guess was wrong by two orders of magnitude for
  `packages/agentbundle/tests/`, which carries 174.7s of real work and was
  weighted 6.1s. Shard 3 of run 34791356312 came in at 6.37 minutes against a
  3.55-minute prediction, above the spec's own bound. The runner now emits a
  duration per executed unit; the table holds measured values for every
  invocation at or above 5s and a measured mean below it; and the floor moved to
  `packages/agentbundle/tests/`, with `tools/test_check_artifact_contents.py`
  measuring 132.3s on a runner rather than the brief's 174.7s. Predicted
  makespan with measured weights is 203.1s across a 202.2-203.1s spread.
- 2026-09-14: merged `origin/main` (28 commits) before landing. It touched all
  three files this change touches most — `Makefile`, `lint-ci-parity.py` and
  `test_local_ci_shared_test_deduplication.py` — and added a roster suite,
  `packs/frontend-engineering/tests/skills/frontend-engineering/`. The merge was
  clean. Re-verified after it: the unsharded expansion is identical to
  `origin/main`'s at 63 lines, no composition drift, no `MAKE_BASELINE_DIGESTS`
  surface moved, and the four-shard balance holds at 202.9-203.1s over 59 work
  units. The new suite carries `DEFAULT_WEIGHT` until a run measures it, which
  is the drift the `shard-timing` output exists to correct.
  AC1's baseline moved from a frozen commit to the branch point, because `main`
  adding a suite is not this change altering the roster.
