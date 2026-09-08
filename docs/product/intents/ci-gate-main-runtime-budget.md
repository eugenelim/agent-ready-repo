# CI gate-main meets its runtime budget

- **Status:** Draft
- **Level:** feature

## Outcome

The gate-main job completes within the shipped 200-second runtime budget on docs-only pull requests without narrowing SAST relevance or dropping verification.

## Boundary

- Profile and reduce gate-main cumulative runtime while preserving its existing checks and fail-closed behavior.
- SAST configuration, export-boundary behavior, the required-check aggregator, branch protection, and removal or weakening of tests remain outside this intent.

## Owner

- CI workflow and test-owning maintainers; no individual owner is recorded.

## Unresolved questions

- Select the smallest implementation slice that removes at least 102 seconds from the measured docs-only gate-main path while preserving coverage.

## Projection

- One focused performance specification after profiling the two diagnosed cost centers and their retained setup overhead.

## Opportunity

This intent absorbs ci-gate-parallelization-critical-path-measurement. PR #1203 completed the deferred docs-only measurement: gate-main took 302 seconds against the 200-second budget. Its two largest measured steps were make build-check at 127 seconds and the RFC-0082 catalogue-test carve-out at 74 seconds; the remaining setup and checks accounted for about 101 seconds.

## Assumptions

- The single docs-only sample establishes a target miss but does not characterize runner variance.
- The measurement note is historical evidence, not an amendment to the shipped specification.


## Source

- Mode: repo-origin
- Locator: docs/specs/ci-gate-parallelization/notes/ci-gate-parallelization-critical-path-measurement.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin
