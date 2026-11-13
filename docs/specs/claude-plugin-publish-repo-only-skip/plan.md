# Plan: Claude plugin publish skips repo-only pack changes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `.github/workflows/publish-claude-plugins.yml` (the push filter), `tools/lint-plugin-roster.py` (`PUBLISH_JOB_INPUTS`, `expected_paths`, `check_publish_trigger`), `tools/test-lint-plugin-roster.py` (the existing allowlist cases). Named uncertainty: the lint's current comment and one test say the two catch-alls keep a scope narrowing triggerable; the reasoning here is that the roster lint forces any roster change into a commit that also edits the workflow file, a push path.

## Approach

Delete two list entries in the workflow and in the lint's `PUBLISH_JOB_INPUTS`, then pin the safety argument in tests: a glob matcher over the workflow's real path list shows repo-only pack files match nothing, published pack files match, and the workflow file matches. The riskiest part is the argument that dropping the catch-alls loses no trigger: a pack changing publication status needs a roster edit, the roster lint fails without the matching workflow list edit, and that edit is a push path.

## Constraints

- GitHub path filters: `*` does not cross `/`, `**` does; the matcher in the tests follows that.
- The roster lint stays the single place that pins the list; its existing equality check is what keeps the workflow and roster in step.
- No pack, no package, and no environment setting changes.

## Construction tests

**Unit tests:** the lint's expected set, the extra-path failure, and the path-matching cases in `tools/test-lint-plugin-roster.py`.

**Manual verification:** T3 replays the 200 most recent first-parent `main` commits through the old and new filters.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Architecture passages | T2 | the passages match the workflow | read whole |
| Workflow header | T2 | header text | read whole |

## Design (LLD)

### Design decisions

- The matcher is a small helper in the test file that turns a GitHub path pattern into a regular expression.
- The expected set loses exactly `packs/*/pack.toml` and `packs/*/.claude-plugin/plugin.json`; nothing else moves.

## Tasks

### T1: The lint and the workflow carry the narrower filter and the matching cases pass

**Verification mode:** TDD, at the lint boundary.

**Depends on:** none

**Tests:**
- The expected set is the sixteen published globs plus ten job inputs, and has no wildcard in the pack segment (AC1, AC2).
- A workflow carrying `packs/*/pack.toml` fails the lint, and one carrying `packs/*/.claude-plugin/plugin.json` fails it, each tested separately; a published pack missing, a repo-only pack present, and a dropped job input still fail (AC3, AC4, AC8).
- Repo-only packs' `pack.toml`, `plugin.json`, and a skill file match no path in the real workflow; published packs' `pack.toml` and `plugin.json` match; the workflow file matches (AC5, AC6, AC7).
- Moving a pack between the rosters without the workflow list changing fails the lint (AC8).
- The real workflow keeps `workflow_dispatch` and `environment: claude-plugin-publish`; the gate chain names both lints (AC9, AC10, AC11).

**Done when:** the assertions for the narrower expected set, the rejection of each catch-all, and the exclusion of repo-only files failed against the old filter, while the preservation assertions pass before and after; both catch-all entries are removed from `PUBLISH_JOB_INPUTS` and from the workflow's `paths:`; and `python3 tools/test-lint-plugin-roster.py` and `python3 tools/lint-plugin-roster.py` pass (AC12, AC13).

### T2: The workflow header, lint comments, and architecture passages state the new reach

**Verification mode:** goal-based check.

**Depends on:** T1

**Done when:** the workflow header and inline path-filter comments, the lint's comment on `PUBLISH_JOB_INPUTS`, and the `expected_paths` docstring give the current reasoning without the stale counts or the claim that the two catch-alls keep a withdrawal triggerable, the header names `workflow_dispatch` on `main` as the recovery for a missed trigger, the two architecture passages match the workflow, and `python3 tools/lint-plugin-roster.py` passes (AC1, AC2).

### T3: The replay is recorded and the repository gates are green

**Verification mode:** visual / manual QA, then goal-based.

**Depends on:** T1, T2

**Done when:** the replay counts of the old and new filters are in the PR, and `make lint-ruff`, `make lint-mypy` and `make precheck` pass (AC14, AC15, AC16).

### T4: Review repairs: the roster-move cases and the gate-chain registration are tested for real

**Verification mode:** TDD, at the lint boundary.

**Depends on:** T1

**Tests:**
- Promoting a repo-only pack and withdrawing a published pack, each with the workflow list unchanged, fail the lint naming the pack's path, and pass once the workflow list moves with the roster (AC8).
- The gate-chain check reads registered `_script_step` calls from the parsed source, so a commented-out registration fails it (AC9).

**Done when:** `python3 tools/test-lint-plugin-roster.py` and `python3 tools/lint-plugin-roster.py` pass, a mutation that makes `expected_paths` ignore `PUBLISHED` fails the new cases, and one that comments out the roster lint's registration fails the chain check.

## Rollout

- **Delivery:** one merge; the next push to `main` uses the new filter. Reversible by restoring the two entries.
- **Deployment sequencing:** none.

## Risks

- A future path that changes publishable output but is neither a published pack, a job input, nor a roster edit would not start a run; `workflow_dispatch` recovers it by hand.
- Files of published packs that never ship (for example tests) still start a run; left as a follow-on.

## Changelog

<!--
- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->

- 2026-11-12: spec approved by eugenelim (scope)
- 2026-11-12: plan approved by eugenelim (build strategy)
