# Spec: Shard the test corpus across parallel runners

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0101
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer who dispatches `test-corpus.yml` waits about four minutes instead
of fifteen. The workflow runs the repository's declared test target on several
runners at once, each runner executing one undecomposed `make` command over a
disjoint slice of the same roster. The maintainer gains nothing to maintain: the
Makefile stays the single roster, so adding or removing a suite there changes
what every shard runs without anyone editing a workflow. Standalone `make test`
is untouched and remains the complete public gate.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture truth | Applicable — `verification-graph.md` describes what `test-corpus.yml` runs | [`docs/architecture/verification-graph.md`](../../architecture/verification-graph.md) | Repository maintainers | Updated prose naming the sharded shape | Statement matches the shipped workflow |
| Maintainer procedure | Applicable — `AGENTS.md` lists the dispatch command | [`AGENTS.md`](../../../AGENTS.md) | Repository maintainers | Dispatch line still correct | Command as written dispatches the sharded workflow |
| Reusable learning | Applicable — an unshipped intent reasons about per-job posture assertions over a multi-job workflow | [`docs/product/intents/dispatch-workflow-posture-assertions.md`](../../product/intents/dispatch-workflow-posture-assertions.md) | Repository maintainers | Intent names this spec as a concrete instance of its multi-job question | Intent's open question cites a real multi-job workflow |
| Decision rationale | Not applicable — no prior decision is reversed; the workflow's `lint-ci-parity` out-of-scope classification is preserved, not changed | — | — | — | — |

## Boundaries

### Always do

- Keep the Makefile the single roster. Shard selection reads the roster the
  Makefile already declares; it never restates it.
- Run one process per invocation. Sharding may reorder or distribute
  invocations across runners; it may never merge two into one pytest process or
  split one across two.
- Fail loudly on any shard selector that would run less than a full slice, and
  on any roster line the shard runner cannot classify.
- Run every precondition check in every shard, so a shard cannot pass by
  skipping a probe that another shard owns. This deliberately changes *when* a
  missing precondition surfaces: serial `make test` reaches the `import httpx`
  probe only after the suites preceding it, whereas a shard reports the same
  missing dependency before running anything. The failure is the same failure,
  reported earlier and in every shard rather than one.

### Ask first

- Changing `test-corpus.yml`'s `lint-ci-parity` scope classification. The
  classification is preserved by this work; altering it is a separate design
  decision.
- Adding a `pull_request` trigger to `test-corpus.yml`.
- Editing any Makefile surface listed in `MAKE_BASELINE_DIGESTS`.

### Never do

- Enumerate a suite, path, or pytest invocation inside `.github/workflows/`.
- Change `runs-on:` away from the exact literal `ubuntu-latest`.
- Let standalone `make test` (no `SHARD`) run anything less than the full
  roster.
- Select tests from a diff, a changed-file list, or any other content-derived
  predicate.
- Edit `.github/workflows/build-check.yml`.

## Testing Strategy

- **Union completeness and partition correctness: TDD.** The property — that
  the shards' invocation lists concatenate to exactly the unsharded roster, with
  no duplicate and no omission — is a compressible invariant over a pure
  function, so it is asserted mechanically in a test rather than read from
  output. This is the failure class
  [`gates-that-read-clean-while-gating-nothing`](../../product/intents/gates-that-read-clean-while-gating-nothing.md)
  tracks: a shard scheme that drops a suite is green while proving less.
- **Selector validation and fail-closed classification: TDD.** Rejecting an
  out-of-range shard, a missing companion variable, and an unclassifiable roster
  line are pure predicates over inputs.
- **Unsharded roster preservation: goal-based check.** `make -n test-unleased`
  expands to the same command list before and after the change; a diff of the
  two expansions is the one-liner.
- **Workflow shape: TDD.** Whether the workflow enumerates a suite, and whether
  its matrix covers exactly `1..SHARDS`, are predicates over the file's text
  and structure. They are pinned by a test with mutation cases rather than by an
  operator's `grep`, because an ad-hoc pattern silently misses a spelling nobody
  anticipated — and a matrix that disagrees with `SHARDS` produces a run where
  every job is green and one shard never executed.
- **Execution boundaries: TDD.** That each work unit becomes its own process,
  and that every precondition runs in every shard, are observable through a
  recording executor substituted for the real one.
- **Real sharded runtime: visual / manual QA.** The wall-clock figure written
  into the sizing comment is read from a dispatched run of the shipped
  workflow, not computed. A local timing is not transferable.

## Acceptance Criteria

- [ ] Standalone `make test`, invoked with no `SHARD` and no `SHARDS`, expands
      to the same invocation list that `git show 28a169531:Makefile` expands
      to. The baseline names that commit literally, never `HEAD`, which moves
      as this work commits.
- [ ] For every shard count from 1 through 8, concatenating the invocation
      lists of shards `1..N` yields exactly the unsharded roster's work
      invocations as a multiset: every invocation appears in exactly one shard,
      and none is absent.
- [ ] Each roster work invocation is executed as its own operating-system
      process in whichever shard owns it; no shard merges two roster
      invocations into one process or splits one across two.
- [ ] `make test SHARD=<n> SHARDS=<m>` exits non-zero without executing any
      invocation when `n` or `m` is negative, zero, or not an integer, and when
      `n` exceeds `m`.
- [ ] `make test` exits non-zero without executing any invocation when exactly
      one of `SHARD` and `SHARDS` is set.
- [ ] `make test SHARD=<n> SHARDS=<m>` exits non-zero without executing any
      invocation when `m` exceeds the number of work invocations in the roster,
      so no shard is ever empty.
- [ ] A roster line matching neither a declared precondition nor a recognized
      runner invocation makes the shard runner exit non-zero with a message
      naming the unclassified line.
- [ ] Roster acquisition exits non-zero without executing any invocation when
      the dry-run expansion returns a non-zero status, so a partial roster is
      never executed as though it were complete.
- [ ] Roster acquisition refuses, before invoking Make at all, when the
      `test-unleased` recipe or the `run-test-suite` macro body contains a
      construct that would make a *roster line itself* execute during
      discovery: `$(MAKE)`, `${MAKE}`, or a `+`-prefixed recipe line, each of
      which GNU Make runs even under `-n`.

      The claim stops there, and deliberately. This criterion does not assert
      that expanding the roster is free of side effects, because it is not and
      cannot be made so: resolving `$(PYTHON)` runs `$(shell python3 …)` from
      `Makefile:10` on every Make invocation, sharded or not, and a check over
      transitive variable expansion has no bounded form. What the criterion
      buys is narrower and real — a roster *line* cannot acquire the power to
      run while it is being read.
- [ ] Every declared precondition in the roster runs in every shard, including
      a shard that owns none of the work that precondition guards.
- [ ] The weight table records these exact durations, each keyed to its
      invocation and attributed to workflow run 34779996081:
      `tools/test_check_artifact_contents.py` 174.7s;
      `packs/core/tests/skills/work-loop/` 147.2s; `tests/` 91.0s;
      `tools/test_build_gate_chain.py` 54.2s; `tools/test_workspace_status.py`
      31.4s; `tools/test_lint_agents_md_diataxis_block.py` 27.1s.
- [ ] Every roster work invocation with no recorded measurement takes the
      declared default weight, and that default is derived from the recorded
      totals rather than chosen: 843s total less 525.6s measured, over the
      unmeasured work invocations.
- [ ] The partition assigns invocations by that weight table rather than by
      roster position: given the recorded weights, the heaviest invocation and
      the second-heaviest are assigned to different shards at a shard count
      of 4.
- [ ] No `run:` command in `.github/workflows/test-corpus.yml` contains a suite
      path, a pytest invocation, or a test-file name. The predicate is scoped to
      executable `run:` scalars, because the file's comments legitimately
      mention `tests/` and a test name while executing neither.
- [ ] `.github/workflows/test-corpus.yml`'s job runs exactly one
      test-execution step, and that step's command is a single `make test`
      invocation.
- [ ] The shard indexes in `.github/workflows/test-corpus.yml`'s job matrix are
      exactly the integers `1` through the `SHARDS` value in that job's `make`
      command, with no gap and no duplicate.
- [ ] `.github/workflows/test-corpus.yml`'s job `runs-on:` is the exact literal
      `ubuntu-latest`.
- [ ] `tools/lint-ci-parity.py` exits 0.
- [ ] `test-corpus.yml` remains classified out of scope in
      `tools/lint-ci-parity.py`'s `WORKFLOW_SCOPE`.
- [ ] `tools/lint-pack-test-boundary.py` exits 0.
- [ ] The union, selector, classification, execution-boundary, and
      precondition-replication proofs all run as part of `make test`, so a
      later selector regression cannot ship without running them — achieved
      without adding any file to the roster, so the invocation list stays
      identical to the accepted base.
- [ ] The slowest shard's measured duration in the dispatched run is at most
      6 minutes. Above that, the shard count is revised and the branch is
      re-pushed, re-dispatched and re-measured rather than recorded as-is. The
      bound is the 174.7s floor plus the 23s setup, rounded up to leave room for
      runner variance; it cannot be set lower because no shard count beats the
      longest single invocation.
- [ ] `.github/workflows/test-corpus.yml`'s sizing comment states a measured
      duration taken from a dispatched run of the sharded workflow, names that
      run, and carries no instruction for a later reader to execute.
- [ ] `timeout-minutes` in `.github/workflows/test-corpus.yml` is at least the
      greater of three times the slowest shard's measured duration and the
      recorded 17.0-minute serial maximum, so a shard that degrades to the full
      serial corpus reports a real failure rather than a timeout.
- [ ] [`docs/architecture/verification-graph.md`](../../architecture/verification-graph.md)
      describes `test-corpus.yml` as it now runs.
- [ ] [`docs/product/intents/dispatch-workflow-posture-assertions.md`](../../product/intents/dispatch-workflow-posture-assertions.md)
      names this spec as a shipped instance of the multi-job workflow its open
      question anticipates.

## Follow-ons

- Repository maintainers: [`docs/product/intents/dispatch-workflow-posture-assertions.md`](../../product/intents/dispatch-workflow-posture-assertions.md)
  — posture assertions over the now-multi-job `test-corpus.yml` remain that
  intent's work, not this spec's.
- Repository maintainers: `tools/test_check_artifact_contents.py` builds five
  real artifacts with no shared fixture, only three of them distinct. Making it
  faster lowers the sharding floor and is separately queued.

## Assumptions

- Technical: `make -n test-unleased` expands the roster completely, including
  the `$(3)` macro parameter in its roster position (source: probe, 2026-09-13).
- Technical: expanding the roster is not side-effect-free and never was.
  `PYTHON ?= $(eval PYTHON := $(shell python3 …))` at `Makefile:10` launches a
  Python process on the first `$(PYTHON)` reference, under `-n` as well as in a
  real run. This is pre-existing, identical for serial `make test`, and outside
  what sharding changes; the roster-acquisition criterion is scoped to
  recursive-Make constructs in the roster-bearing bodies rather than
  overclaiming a guarantee no bounded check can hold (source: `Makefile:10`,
  read 2026-09-13).
- Technical: `tools/lint-ci-parity.py` requires only a non-empty reason for an
  out-of-scope workflow and never parses its steps, so a job matrix does not
  pull `test-corpus.yml` in scope (source: `tools/lint-ci-parity.py:1150-1158`).
- Technical: the `test:` target appears in neither `MAKE_BASELINE_DIGESTS` nor
  any `_target_rule` assertion in
  `tools/test_local_ci_shared_test_deduplication.py`, so it is the editable
  surface; `test-unleased` and `run-test-suite` are pinned and stay untouched
  (source: `tools/test_local_ci_shared_test_deduplication.py:1009-1018,1052`).
- Process: the six recorded serial runs give a 15.0-minute median and a
  17.0-minute maximum; the sharding floor is the longest single invocation,
  174.7s in `tools/test_check_artifact_contents.py` (source: user brief,
  decomposed from run 34779996081).
- Process: the task owner authorized pushing this branch and dispatching
  `test-corpus.yml` to obtain the sharded measurement (source: user
  confirmation 2026-09-13).
