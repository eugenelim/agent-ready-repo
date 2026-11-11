# CI gate-main meets its runtime budget

- **Slug:** `ci-gate-main-runtime-budget`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim

## Outcome

The gate-main job completes within the shipped 200-second runtime budget on docs-only pull requests without narrowing SAST relevance or dropping verification.

## Boundary

- Profile and reduce gate-main cumulative runtime while preserving its existing checks and fail-closed behavior.
- SAST configuration, export-boundary behavior, the required-check aggregator, branch protection, and removal or weakening of tests remain outside this intent.

## Owner

- eugenelim, with the CI workflow and test-owning maintainers.

## Unresolved questions

- Select the smallest implementation slice that removes at least 650 seconds from the median docs-only gate-main path (868 s against the 200 s budget) while preserving coverage.
- The two diagnosed cost centers together take about 624 s at their medians, which leaves a docs-only median near 244 s when both go to zero. Reaching 200 s therefore also needs about 44 s from the remaining steps, or a restated budget. Decide whether the 200 s budget stands once profiling shows what the rest of the job costs.

## Projection

- One focused performance specification after profiling the two diagnosed cost centers and their retained setup overhead.

## Opportunity

This intent absorbs ci-gate-parallelization-critical-path-measurement. PR #1203 measured one docs-only run in August 2026 at 302 seconds against the 200-second budget, with `make build-check` at 127 seconds and the RFC-0082 catalogue-test carve-out at 74 seconds.

A re-measurement on 2026-11-04 shows the miss is about three times larger. Across the 76 completed `build-check.yml` runs created from 2026-10-31 to 2026-11-04, the `gate-main` job took a median of 908 seconds (minimum 338, 90th percentile 1,093, maximum 1,211), and no run finished under 200 seconds. The 21 runs whose head commit changed only `docs/`, `guides/` or Markdown files had a median of 868 seconds and a minimum of 646 seconds.

The same two steps dominate and have grown. `Run make build-check` has a median of 340 seconds. The step `pytest catalogue-test carve-out destinations (RFC-0082)`, which runs the `tests/` tree and many pack suites inside `gate-main`, has a median of 285 seconds. A third step, `pytest shared-test dedup guard`, takes about 31 seconds. The workflow comment that the RFC-0082 sdist budget travels with `gate-export-boundary` concerns that budget only, and the carve-out step still runs here.

Method: `gh api` run and job records for `build-check.yml`, job duration from `started_at` to `completed_at` for `gate-main`, step durations from the job's step records. A run counts as docs-only when its head commit's changed paths are all under `docs/` or `guides/` or are Markdown, which can undercount code in a multi-commit pull request. The per-run data is kept locally and is not part of this repository.

## Assumptions

- Runner variance is wide: docs-only runs range from 646 to 1,098 seconds, about 1.7 times. Even the fastest run is more than three times the budget, so variance does not explain the miss.
- The August measurement note is historical evidence, not an amendment to the shipped specification. Its numbers are superseded by the re-measurement above.


## Source

- Mode: repo-origin
- Locator: docs/specs/ci-gate-parallelization/notes/ci-gate-parallelization-critical-path-measurement.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

## Non-goals

- SAST configuration, export-boundary behavior, the required-check aggregator and branch protection stay as they are.
- No test is removed or weakened to save time.
- The first slice does not split the `make build-check` chain; earlier attempts to split it failed on implicit ordering.

**Riskiest assumption:** moving the carve-out and dedup guard into a sibling job that the aggregator waits on keeps every check running and fail-closed. Agent-only test: the posture test mutation that drops the sibling from the aggregator's `needs` must fail, and a before-and-after listing of commands must show none lost.

## Readiness

Route: new-spec, one focused performance spec, then a second spec only if the first leaves the chain above the target below.

Re-profiled 2026-11-05 from 19 completed `build-check.yml` pull-request runs: `gate-main` median 874 s (minimum 592 s, maximum 1,058 s). Steps by median: `Run make build-check` 326 s, the RFC-0082 catalogue-test carve-out 258 s, the shared-test dedup guard 29 s, everything else 17 s or less. The August and November figures above stand as the baseline; this run agrees with them within 4 percent.

Answer to the budget question: the 200 s figure cannot be met by moving the carve-out alone. With the carve-out (258 s) and dedup guard (29 s) out of the job, about 587 s remain, and `make build-check` is 326 s of that. The budget is restated per slice, not dropped: the first slice targets a `gate-main` median of at most 600 s by moving those two steps into a sharded sibling job that the required aggregator waits on, copying the shard pattern in `test-corpus.yml`. Whether any further target such as 300 s is worth pursuing then depends on profiling `make build-check` step by step, which the first spec also records. The earlier attempts to split that chain failed on implicit ordering, so a second slice needs its own evidence.

First slice and proof: add the sibling sharded job and make the aggregator's `needs` include it, so branch protection needs no change. An agent can verify it with `tools/test-build-check-workflow.py` (the mutation that drops the sibling from `needs` must fail) and with a `gh api` re-measurement after merge; the re-measurement is a non-blocking follow-up.
