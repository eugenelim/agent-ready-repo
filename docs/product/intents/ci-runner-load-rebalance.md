# Rebalance work onto the CI runner with headroom

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/ci-gate-credbroker AC12](../../specs/ci-gate-credbroker/spec.md)
- **Authority:** [spec/ci-gate-parallelization](../../specs/ci-gate-parallelization/spec.md)

## Outcome

The existing `gate-credbroker` runner carries a safely enumerated additional CI slice when current timing evidence shows the move improves the critical path without weakening parity or its zero-skip guarantees.

## Opportunity

This is not a cost review of whether the runner should exist. The runner is paid for and the recorded CI measurements show headroom; the question is what else can move onto it. The runner also makes the credbroker suite's `[crypto]` precondition and zero-skip property standing gates that did not exist when the step lived in `gate-main`.

## What this absorbs

### ci-gate-credbroker-headroom-what-moves-next

The consequence `ci-gate-credbroker-critical-path-measurement` pre-committed to action if no critical-path shift was observed, and none was. “Does the runner earn its cost?” is the wrong question and previously sent analysis in the wrong direction. The recorded measurements are `gate-credbroker` at 37–44 seconds against a 10-minute timeout, while `gate-main` bound the critical path at 181–204 seconds, mean 193, `n=4`; the runner was described as about 80% idle. The prior scope was “extract the cheapest step that reaches the ceiling and stop,” with `gate-sast` at about 158 seconds, so further extraction was worthless until `gate-sast` fell. Post-merge, recorded `gate-sast` timing was 132–166 seconds, mean about 153, while `gate-main` was 181–204 seconds, mean 193. `gate-sast` is already below `gate-main`; the precondition for further extraction is now satisfied without waiting for a `pip-audit` or `semgrep` change.

On run `32093318277` at `a3d4fcfe`, the movable-work inventory is: 69 seconds for `Run make build-check`, indivisible because it is the chained gate; 34 seconds for the `pytest catalogue-test` carve-out (RFC-0082), movable but known hard; 26 seconds to install `ripgrep`, pure provisioning used only by the two `rg` scrub steps, so it moves with them or is cached; and about 75 seconds across about 50 further steps, each under 6 seconds, each with a parity disposition, whose observability-for-seconds trade was previously declined. Moving the carve-out alone would make `gate-credbroker` about 78 seconds and `gate-main` about 170 seconds. `gate-main` still binds because 69 seconds is one indivisible step. This lever narrows the gap but does not close it.

The hard part is unchanged. The RFC-0082 carve-out runs `pytest tests/`, eight pack test directories, a ten-file tools batch, and an inline `import httpx`. `spec/ci-gate-parallelization` records that four revisions failed to enumerate its coupling graph by inspection. `spec/ci-gate-credbroker` carries a Never-do against extracting it. Neither restriction is revoked: a future spec must enumerate the coupling properly, and apparent headroom is not permission to skip it. What is already proven for that future spec is the four-file coupling — `build-check.yml` plus posture test, fixture, and parity roster — the fourth-placement rule, `PINNED_JOB_STATEMENTS` for pinning a moved step's body, and `add-work-job-unwired` proving that job-set derivation is load-bearing. A second extraction is smaller than the first was.

Unblocks when: dated CI timing records establish the current runner headroom and critical-path ordering, and a future spec enumerates the carve-out coupling graph.

## Assumptions

- The runner-idle percentage and critical-path ordering need dated CI timing records; local Git evidence cannot settle them.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
