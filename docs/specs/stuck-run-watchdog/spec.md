# Spec: Stuck workflow run watchdog

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** integration
- **Risk triggers:** security-boundary

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`, `What
> Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material.

## Outcome

Repository maintainers learn within about two hours that a GitHub Actions run is stuck, instead of finding out when deploys silently stop. One open issue lists each stuck run with the commands that cancel it, and closes itself when none remain.

## What Changes

- A scheduled workflow lists runs stuck beyond a limit and keeps one issue current — `.github/workflows/stuck-runs-watchdog.yml`
- The logic that finds stuck runs, renders the report, and syncs the issue — `tools/stuck_runs_watchdog.py`
- Tests for that logic and for the workflow's security posture — `tools/test_stuck_runs_watchdog.py`
- The workflow is classified and the suite registered in the local and CI gate rosters — `tools/lint-ci-parity.py`, `Makefile`, `.github/workflows/build-check.yml`, `tools/test_local_ci_shared_test_deduplication.py`
- The workflow fleet description lists it — `docs/architecture/verification-graph.md`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | The workflow fleet table and its counts change | `docs/architecture/verification-graph.md` | repository owner | the table row and the counts name the new workflow | the page read whole, counts match `.github/workflows/` |
| Maintainer procedure | The issue body is the runbook: it carries the cancel commands | the issue body rendered by `tools/stuck_runs_watchdog.py` | repository owner | the rendering test | the issue text names both cancel forms |
| Release history | A tools-only change, no pack version moves | none — no published pack or package changes | n/a | n/a | n/a |

## Agent Rules

### Always do

- Pass every GitHub-context value into a step through `env:`, never inside a `run:` body.
- Render only run fields from a closed list; sanitize the workflow name to a safe alphabet.
- Query only the five candidate statuses, 100 results per page, at most 10 pages per status for runs (GitHub's 1,000-result search ceiling) and 20 pages for issues; say so in the report when a limit truncated it.

### Ask first

- Any permission beyond `actions: read` and `issues: write`.
- Cancelling a run automatically, or any other write to an Actions resource.

### Never do

- Report a run that waits on a human approval of a publish environment: the four approval-gated publish workflows are never flagged while `waiting`.
- Cancel, re-run, or delete a workflow run.
- Render contributor-controlled text in the issue except the workflow name sanitized to the alphabet the rendering criterion defines.
- Add a `pull_request`, `pull_request_target`, `push`, or `workflow_run` trigger.
- Swallow a failed API call: the CLI, the step, and the job fail, and the job or step never uses `continue-on-error` or an error-masking shell construct.
- Close the issue, or report that nothing is stuck, from a truncated listing.

## Testing Strategy

- **TDD** for classification, rendering, and issue sync: pure functions plus a sync step driven through a fake `gh` runner.
- **Goal-based check** for the workflow's posture: a test parses the workflow file and asserts triggers, permissions, pins, and `run:` bodies.
- **Manual QA** for the real entry point: the CLI's `--dry-run` runs against the live repository with read-only calls and its output is recorded.

## Acceptance Criteria

- [x] The workflow's triggers are exactly `schedule` (one hourly cron) and `workflow_dispatch`.
- [x] The workflow declares `permissions: {}` at the top.
- [x] Its single job declares exactly `actions: read` and `issues: write`.
- [x] No `run:` body contains a `${{ }}` expression.
- [x] Every `uses:` is pinned to a 40-character commit SHA.
- [x] The job sets `timeout-minutes` between 1 and 5 inclusive.
- [x] The workflow-level concurrency is exactly `group: stuck-runs-watchdog` with `cancel-in-progress: false`, shared by scheduled and dispatched runs on every ref.
- [x] Neither the job nor the watchdog step uses `continue-on-error`.
- [x] The watchdog step's shell contains no error-masking construct.
- [x] Neither the job nor the watchdog step has an `if:` that can skip it.
- [x] Apart from the approval-gated exemption in the next criterion, a run is stuck when its status is `in_progress` and more than 3 hours have passed since `run_started_at` (`created_at` when absent), or its status is `queued`, `waiting`, `pending`, or `requested` and more than 2 hours have passed since `created_at`; a run exactly at a limit, a run of any other status, and the watchdog's own run are never stuck.
- [x] A run in status `waiting` whose `path` is `.github/workflows/publish-claude-plugins.yml`, `.github/workflows/release-agentbundle.yml`, `.github/workflows/release-credbroker.yml`, or `.github/workflows/release-jsonl-otlp-exporter.yml` is never stuck, whatever its age; a `queued`, `in_progress`, `pending`, or `requested` run of those workflows, and a `waiting` run of any other workflow, is classified by the previous criterion. A path is exempt only when it is a string equal to one of those four, optionally followed by `@refs/` and a nonempty ref; every other path, including a missing or non-string one, is not exempt.
- [x] A candidate run not excluded by the own-run rule or the previous criterion, whose required timestamp cannot be parsed, makes the command exit non-zero before any issue write; exempt runs are skipped before timestamp parsing.
- [x] The issue body names each stuck run by numeric id, workflow name restricted to letters, digits, space, `.`, `_`, and `-` and at most 120 characters, status, elapsed whole hours, and run URL, followed by the two cancel commands `gh run cancel <id>` and `gh api -X POST repos/<repo>/actions/runs/<id>/force-cancel`. Elapsed hours are the floor of the time from the timestamp used for classification to the invocation's captured UTC time.
- [x] The issue body contains no field of a run other than those the previous criterion names.
- [x] The issue body lists at most 50 runs.
- [x] The issue body is at most 60,000 UTF-8 bytes.
- [x] The issue body states when a rendering cap or a listing limit left the report incomplete.
- [x] A watchdog issue is an open issue, not a pull request, created by `github-actions[bot]`, titled exactly `Stuck workflow runs`, and containing the exact marker `<!-- stuck-runs-watchdog:v1 -->`; any other issue is never edited, commented on, or closed.
- [x] More than one matching watchdog issue makes the command exit non-zero before any write.
- [x] Issue discovery requests open issues 100 per page, pages 1 through 20 only, and exits non-zero before any write if more pages remain.
- [x] With stuck runs and no watchdog issue open, the sync creates exactly one issue.
- [x] With stuck runs and one watchdog issue open whose body differs, the sync edits that issue and creates none.
- [x] With stuck runs and one watchdog issue open whose body is identical, the sync makes no write.
- [x] With no stuck runs, a complete listing, and a watchdog issue open, the sync comments on and closes it.
- [x] With no stuck runs and no watchdog issue open, the sync creates nothing.
- [x] A run listing for a status whose page 10 returns a full 100 results (GitHub's 1,000-result ceiling) is incomplete, never closes an issue, and never reports that nothing is stuck; page 11 is never requested.
- [x] The only write calls the code makes are issue create, edit, comment, and close; a test over the call log of every scenario asserts it.
- [x] A failed `gh` call makes the command exit non-zero.
- [x] `--dry-run` prints the report and makes no write call.
- [x] `tools/lint-ci-parity.py` exits 0 with the new workflow classified in `WORKFLOW_SCOPE` and the roster of workflow reasons.
- [x] The new suite is registered in the Makefile, `build-check.yml`, `SUITE_DISPOSITION`, and the dedup guard's membership list and plan digests, and the dedup guard passes.
- [x] `docs/architecture/verification-graph.md` lists the workflow and its counts equal the workflow directory and the dispatch-trigger set.
- [x] `make lint-ruff lint-mypy` passes.
- [x] `make precheck` passes.
- [x] The new suite passes.

## Follow-ons

- repository owner: option 2 of the stuck-run proposal (bounded auto-cancel of a stuck Pages deploy) — not started; ask first.

## Assumptions

none
