# ADR-0085: The SAST/SCA leg becomes its own CI job, and provenance is command-line origin

- **Status:** Accepted
- **Date:** 2026-08-17
- **Decision-makers:** eugenelim
- **Consulted:** adversarial review, security review (eight pre-EXECUTE rounds)
- **Supersedes:** the **CI-chaining sub-decision** in [ADR-0017](0017-adopt-bandit-pip-audit-semgrep-sast-gate.md) only — that SAST runs "chained into `make build-check` … in the existing `build-check.yml` CI on every PR". That ADR's tool choices, severity floor, three-way real-fix-first ladder, and the requirement that the scanners stay CI-only dev dependencies all stand, and the **Makefile chain is deliberately untouched**
- **Related:** the implementing spec `docs/specs/ci-gate-parallelization/`; `tools/assert-sast-chain-reachable.py` carries the operative guarantee; [ADR-0083](0083-extend-sca-to-npm.md) extends the same gate to npm and travels with it

## Decision summary

- **Decision:** the SAST/SCA leg runs as its own `gate-sast` job inside
  `build-check.yml`, not chained into the `make build-check` step. `gate-main`
  invokes `make build-check PACKS_DIR=packs SAST_DELEGATED=1`; `gate-sast` always
  runs and owns the scan.
- **Second decision, load-bearing and separable:** the signal that a run's SAST leg
  was **deliberately delegated** is `$(origin SAST_DELEGATED) = "command line"`,
  **not any environment variable.**

## Context

`build-check.yml` ran 56 steps in one serial job, and that job is the sole required
status check on `main`. With branch protection `strict: true` and no merge queue,
every merge invalidates every other PR's up-to-date status, so merge throughput was
bounded by one build-check duration. The SAST/SCA leg (~150s) and the
export-boundary gate (~123s) are the two indivisible costs; extracting them is what
shortens the critical path.

ADR-0017 required the leg be "chained into `make build-check` … rather than living
in a separate, skippable workflow." Read literally, that forbids this change. Read
for its **rationale** — dogfooding, so the gate cannot be quietly bypassed — it does
not: `gate-sast` stays inside `build-check.yml`, always runs, and is
independently required by branch protection. What ADR-0017 actually needed was that
a developer running the local gate scans, and that CI cannot skip the leg by
omission.

## Decision detail

**The Makefile chain is untouched.** `make build-check` on a developer machine still
runs `$(MAKE) sast`. That is ADR-0017's dogfooding requirement, and it is now
*enforced* rather than asserted: after this change **no CI path executes that
branch**, so nothing would notice it being deleted — or, subtler, made unreachable
while still present. `tools/assert-sast-chain-reachable.py` pins reachability and is
mutation-proven against both.

**Provenance is command-line origin.** The delegated state must be distinguishable
from an accident, and no environment variable can do it: `GITHUB_WORKFLOW`, `CI`,
`GITHUB_ACTIONS`, `GITHUB_RUN_ID` and `RUNNER_ENVIRONMENT` are each either
synthesised by `act` or exportable from a devcontainer image or a shell profile.
Make's `$(origin)` is not an environment value — it returns `command line` only when
the invoker supplied the assignment on the command line. So an ambient
`SAST_DELEGATED=1` **neither** reaches the quiet banner **nor** skips the leg: the
scan runs and the honest "complete" verdict prints. Without this, an exported
variable in a devcontainer image would make `make ci` skip the entire SAST/SCA leg
and finish with a calm verdict — strictly worse than the state ADR-0017 left.

## Alternatives considered

- **A separate detect job** feeding a conditional `gate-sast` via outputs. Rejected:
  a job-level `if:` cannot run shell, so the relevance predicate needs its own job;
  that adds a job, puts provisioning on the critical path ahead of the scan, and
  reintroduces a *skip* state the aggregator must interpret. An always-running
  `gate-sast` has no skip state.
- **Keying provenance on `GITHUB_WORKFLOW`.** Rejected: `act` sets it to the
  workflow's own name, so the guard is defeated by one of the three tools it was
  written to defend against.
- **Leaving `build-check.yml` alone** and taking the win from the export-boundary
  gate's own cost. Still open as a separate lever; it does not address the ~150s leg.

## Consequences

- **Accepted: the SAST leg is now the critical path.** Additions to it translate 1:1
  into PR latency. #977 and #980 both added to it in a single day, so this is not
  hypothetical.
- **Accepted: a green aggregator does not prove a scan executed.** `pull_request`
  evaluates the workflow, and its posture test, from the PR's own ref. Branch
  protection requiring `gate-sast` directly bounds this — a PR cannot make the job
  disappear — but a job that runs and verifies nothing is a separate class, covered
  by the spec's fail-open ACs. **This is recorded as closable, not inherent:** a
  repository ruleset resolving required workflows from a pinned ref, plus
  `CODEOWNERS` on `.github/workflows/**`, would bound it further. Tracked as
  `ci-gate-parallelization-required-workflow-pinned-ref`.
- **Accepted, pre-existing:** the relevance predicate evaluates `SAST_CONFIG` from
  the head commit, so a PR narrowing it self-certifies as non-scannable. The
  push-to-main run is the belt-and-braces, which is why the trigger is asserted.
- **The terminal verdict's case set changes.** The `GITHUB_WORKFLOW`-keyed
  "CI-intentional skip" branch is retired — after this change `build-check.yml` never
  sets `SKIP_SAST=1`, so it had no producer, and a branch no workflow can reach is
  the gate-that-gates-nothing shape this repo's own comments warn about. This
  reverses acceptance criteria in `docs/specs/local-gate-ci-parity/`, which is
  annotated accordingly.
- **A note for the next author:** `ci-security.yml` documents "cancel-in-progress
  gated to pull_request only — push-to-main scans run to completion", and
  `codeql.yml` uses unconditional `cancel-in-progress` on a push trigger. Both rest
  on a false premise — GitHub permits one running plus one *pending* run per
  concurrency group regardless of that flag, so a third queued run cancels the
  pending one. Do not copy that group shape; see the spec's AC12 for one that keys
  non-PR events uniquely. Tracked as `ci-security-posture-test-unwired`.
