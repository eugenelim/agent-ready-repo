# Plan: Stuck workflow run watchdog

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `.github/workflows/iac-staleness.yml` (a scheduled, read-only workflow), `.github/workflows/ci-security.yml` (the posture the tests pin), `tools/test-ci-security-workflow.py` (a posture test), `tools/lint-ci-parity.py` roster dicts. Named uncertainty: no existing tool shells out to `gh`, so the fake-runner seam is new.

## Approach

One stdlib script holds three pure steps (classify, render, sync) and a thin `main` that calls `gh api` for the runs and for issues. The workflow runs the script hourly with a read-only token plus issue write. All decisions are pure functions fed by JSON, so tests need no network; the sync takes a `gh` runner callable and tests pass a recorder. The riskiest part is the issue text: workflow names reach it, so they are sanitized and nothing else from a run is rendered.

## Constraints

- New `tools/` additions are pure-stdlib `.py` files (`tools/AGENTS.md`).
- Every `uses:` is SHA-pinned; zizmor and actionlint run over the new file in `ci-security`.
- A new tools suite is registered in the Makefile `run-test-suite` define, the `build-check.yml` pytest invocation, `SUITE_DISPOSITION` in `tools/lint-ci-parity.py`, and the dedup guard's membership list and its standalone and composed plan digests; the workflow is classified in `WORKFLOW_SCOPE` and the roster of workflow reasons. Adding a new build-check step instead of extending an existing line would also need both step dispositions, so the suite joins an existing line.
- `bandit` runs in precheck; the `subprocess` call to `gh` carries a reasoned `nosec` if flagged.

## Construction tests

**Unit tests:** classification thresholds, boundary, own-run exclusion; rendering; sync scenarios through a recording runner.

**Posture test:** parses the workflow YAML and asserts triggers, permissions, pins, `run:` bodies, timeout, concurrency.

**Manual verification:** T4 runs `--dry-run` against the live repository.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Fleet architecture page | T3 | counts equal the workflow directory | page read whole |
| Issue-body runbook | T1 | rendering test | text names both cancel forms |

## Design (LLD)

### Design decisions

- Classification, rendering, and sync are separate functions; `main` only wires `gh` to them.
- The cancel commands are rendered text; the code never runs them.
- Pagination requests single pages through `gh api` with `per_page=100` and explicit page numbers, one status at a time, extracting `.workflow_runs[]` for runs and `.[]` for issues. Runs stop at page 10 per status and mark the report incomplete when page 10 is full; issues stop at page 20 and raise before any write when page 20 is full.
- Issue match: list every page (to 20) of open issues created by `github-actions[bot]` (a server-side `creator` filter, which the API accepts for that login); locally drop items that carry `pull_request`, then require `user.login == 'github-actions[bot]'`, the exact title, and the body marker. More than one match, or an incomplete issue listing, raises before any write.
- Body rendering sorts oldest first, keeps 50 runs, caps names at 120 characters and the body at 60,000 bytes, and appends an incomplete notice when anything was cut.
- A truncated or capped run listing never closes the issue.
- The own-run id comes from the `GITHUB_RUN_ID` environment value.
- The exemption is one anchored pattern over the four exact workflow paths with an optional `@refs/<ref>` suffix; a `waiting` run whose `path` matches it is skipped before its timestamp is parsed. Other statuses of those workflows classify normally. The Pages deploy, which also declares an environment, is deliberately not exempt: it is the stall this watchdog exists to catch.

### Interfaces & contracts

`tools/stuck_runs_watchdog.py --repo OWNER/NAME [--dry-run]`; exit 0 on success, non-zero on any `gh` failure.

### Failure, edge cases & resilience

A `gh` failure raises and exits non-zero; the failed scheduled job is itself the alert. Timestamps are parsed as UTC. After the own-run and approval-gated exclusions, if a candidate run's required timestamp cannot be parsed after the `created_at` fallback, the command exits non-zero before any issue write.

## Tasks

### T1: Classification, rendering, and issue sync are correct

**Verification mode:** TDD, at the module boundary.

**Depends on:** none

**Tests:**
- Threshold, boundary, status set, own-run exclusion (AC11); an invalid required timestamp gives a non-zero exit and zero writes (AC13).
- Rendering fields, hostile workflow name, name cap, run and byte caps with the incomplete notice, elapsed hours (an in-progress run started 3 hours 30 minutes ago renders 3), no other run field, both cancel commands (AC14 to AC18).
- Issue matching: unrelated bot issue, missing marker, title squatter, pull request, two matches before any write, the match found only on page two (AC19, AC20, AC21); a fixture whose issue listing is still full at page 20 gives non-zero exit and zero writes, and page 21 is never requested (AC21).
- Sync: create, edit, no-op, close-with-comment, none-and-none; a run listing that fills page 10 for a status, with an older stuck run omitted, gives the incomplete notice and no closure, and page 11 is never requested; a partial or empty page 10 is a complete listing (AC22 to AC27).
- Call log contains only the allowed write calls in every scenario (AC28).
- A failing runner exits non-zero; `--dry-run` writes nothing (AC29, AC30).

**Done when:** `python3 -m pytest tools/test_stuck_runs_watchdog.py -q` is green.

### T2: The workflow has the pinned posture

**Verification mode:** goal-based check, plus the posture test.

**Depends on:** T1

**Tests:** the posture test asserts AC1 to AC10 on the parsed file, including exact concurrency values and the absence of `continue-on-error`, masking constructs, and `if:` on the job and step.

**Done when:** the posture tests are green and `actionlint` and `zizmor --min-severity high` pass on the file where installed, otherwise CI's `ci-security` is read.

### T3: Rosters, suite registrations, and the fleet page agree

**Verification mode:** goal-based check.

**Depends on:** T1, T2

**Done when:** `python3 tools/lint-ci-parity.py` and `python3 -m pytest tools/test_local_ci_shared_test_deduplication.py -q` pass, and `docs/architecture/verification-graph.md` has the watchdog row, the total of 19 where it states 18, the out-of-scope count recomputed, the dispatch count of eleven with the watchdog in the list, and any disposition count whose roster changed recounted; §2.3 states eleven posture-test files and names `tools/test_stuck_runs_watchdog.py` with its Makefile and build-check callers, and the dated historical evidence line stays untouched (AC31 to AC33).

### T4: Manual QA through the real entry point is recorded

**Verification mode:** visual / manual QA.

**Depends on:** T1

**Done when:** `--dry-run` against the live repository printed a report (or a no-stuck line), exit 0, and the output is recorded in the PR (AC30).

### T5: Repository gates are green

**Verification mode:** goal-based check.

**Depends on:** T1, T2, T3, T4

**Done when:** `make lint-ruff lint-mypy` and `make precheck` pass, and the new suite is green (AC34 to AC36).

### T6: Approval-gated publish workflows are never flagged while waiting

**Verification mode:** TDD, at the module boundary.

**Depends on:** T1

**Tests:**
- A `waiting` run of each of the four workflow files, aged 100 hours, is not stuck; a `waiting` run of another workflow of the same age is stuck (AC12).
- A `queued`, `in_progress`, `pending`, and `requested` run of an exempt workflow, past its limit, is stuck (AC12).
- Each exact approved path and its `@refs/heads/x` form is exempt; a missing or non-string `path`, another directory, a filename prefix or suffix, and `.github/workflows/release-agentbundle.yml@other.yml`, and each approved path followed by `@refs/` with no ref are not exempt (AC12).
- An exempt `waiting` run with an unparseable timestamp makes the command exit 0, not non-zero (AC12, AC13).

**Done when:** `python3 -m pytest tools/test_stuck_runs_watchdog.py -q` is green, `make lint-ruff lint-mypy` and `make precheck` pass, and a dry-run against the live repository no longer lists the waiting Claude plugin publish run.

### T7: Review repairs: the report never says nothing is stuck from a truncated listing, names render in a code span, issue discovery filters by creator, and a truncated listing raises a warning

**Verification mode:** TDD, at the module boundary.

**Depends on:** T1, T6

**Tests:**
- A dry run and a sync whose run listing is incomplete and holds no stuck run print an incomplete-listing message and never the words "no stuck run" (AC27).
- An incomplete listing prints a `::warning::` workflow annotation (AC27).
- A hostile workflow name renders inside a code span in the issue body (AC14).
- Every issue-discovery request carries `creator=github-actions[bot]` (AC21).

**Done when:** `python3 -m pytest tools/test_stuck_runs_watchdog.py -q` is green, `make lint-ruff lint-mypy` and `make precheck` pass.

### T8: Second review repair: a present but empty run_started_at is an invalid timestamp, not an absent one

**Verification mode:** TDD, at the module boundary.

**Depends on:** T7

**Tests:**
- An `in_progress` run whose `run_started_at` is an empty string, with a valid `created_at`, makes the command exit non-zero with zero writes; a missing or null `run_started_at` still falls back to `created_at` (AC11, AC13).

**Done when:** `python3 -m pytest tools/test_stuck_runs_watchdog.py -q` is green, `make lint-ruff lint-mypy` and `make precheck` pass.

## Rollout

- **Delivery:** one merge; the schedule starts on the next hour. Reversible by deleting the workflow.
- **Deployment sequencing:** after merge, dispatch the workflow twice and confirm the job succeeds and at most one watchdog issue exists; a clean repository creates none, so discovery of a bot-created issue rests on the page-two and marker tests.

## Risks

- A new approval-gated publish workflow is flagged after 2 hours of `waiting` until it joins the exemption set in `tools/stuck_runs_watchdog.py`.
- Scheduled workflows are disabled after 60 days without repository activity; the repository is active.

## Changelog

<!--
- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->

- 2026-11-12: spec approved by eugenelim (scope)
- 2026-11-12: plan approved by eugenelim (build strategy)
- 2026-11-12: amendment approved by eugenelim (scope)
- 2026-11-12: plan approved by eugenelim (build strategy)
