# Plan: boundary validation for CLI path arguments in shipped work-loop scripts

- **Status:** Approved
- **Spec:** [`spec.md`](spec.md)

## Constraints

- **Shipped-artifact change.** These scripts install into adopter repos.
  Touching `packs/` forces a `packs/core` version bump across three files
  (`pack.toml`, `plugin.json`, `marketplace.json`) — `make build-self` syncs
  none of them.
- **Projections must be re-synced.** `.claude/` and `.agents/` carry copies;
  `make build-self` regenerates them. Run it *after* the source edit and
  verify `git status` is clean.
- **Engine path-gate.** `packages/agentbundle/**` is untouched by design, so no
  `Engine-Change-RFC` trailer is needed. Do not let the sweep drift into it.
- **CLI surface is frozen.** No new flags, no changed defaults. AC5 is the guard.
- **`check-spec-status.py` is read-only in this change** (AC4).

## Anchor-test sweep

Ran before task 1 — searched `packs/core/tests/` and `tools/` for tests that
pin the content of the four in-scope files.

| Risk | Finding |
|---|---|
| Content hashes / snapshots of the scripts | None found |
| Version-pinned tests against `packs/core` | `packs/core/pack.toml` version is asserted by the agentbundle suite — the bump in task 6 must land with it |
| Line-count or counted assertions | None found |

## Tasks

### T1 — Red tests for the validator contract
**Depends on:** none
**Mode:** TDD
**Tests:** new `packs/core/tests/skills/work-loop/test_root_validation.py`:
- `test_nonexistent_root_exits_nonzero_with_diagnostic` — asserts exit != 0 and the path appears in stderr (AC6)
- `test_file_valued_root_exits_nonzero` — `--root` pointing at a file, not a dir (AC6)
- `test_valid_root_unchanged` / `test_omitted_root_unchanged` / `test_relative_root_unchanged` — exit code + stdout parity vs. current behaviour (AC5)

Invoke via `subprocess` against the real script path — not a synthesised
import — so the test exercises the documented invocation.

**Done when:** all five tests exist and fail for the right reason.

### T2 — `_validated_root()` in `lint-traceability.py`
**Depends on:** T1
**Mode:** TDD
**Tests:** T1 suite goes green for this script.
**Approach:** add the helper adjacent to `_repo_root()` (`:1224`); rewrite
`:1251` to call it. Docstring cites `check-spec-status.py:75` as the reference
pattern. Leave `_within`/`_confined` untouched — they remain the real control.
**Traces to:** AC1, AC5, AC6

### T3 — Same for `lint-spec-status.py`
**Depends on:** T1
**Mode:** TDD
**Tests:** T1 suite goes green for this script.
**Approach:** helper adjacent to `_repo_root()` (`:312`); rewrite `:442`.
**Traces to:** AC2, AC5, AC6

### T4 — `--report` boundary in `loop-cohort.py`
**Depends on:** T1
**Mode:** TDD
**Tests:** T1 suite extended for a nonexistent `--report`.
**Approach:** both sites (`:1083`, `:1147`) call one shared helper. `--report`
names a file, not a directory — assert file-ness, not dir-ness. Do not disturb
the SHA-1 fingerprint logic (`:1003–1027`); it is out of scope here.
**Traces to:** AC3, AC6

### T5 — Semgrep boundary rule + fixtures
**Depends on:** T2, T3, T4
**Mode:** TDD
**Tests:** `tools/test-semgrep-argv-boundary.py` runs the rule over two
committed fixtures and asserts 1 finding on the positive, 0 on the negative.
**Approach:** new `tools/semgrep/argv-path-boundary.yml`, a **structural** rule
(not `mode: taint` — proven unable to cross a call). Must not fire on the
`resolve()`-then-`is_relative_to()` guard shape, or it false-positives on
`check-spec-status.py:72`. Scope via `paths.include` to the three fixed
scripts; record in a rule comment that a repo-wide scope is 73 findings and
name the expansion condition.
**Traces to:** AC7, AC8

### T6 — Version bump, projections, changelog, backlog
**Depends on:** T5
**Mode:** Goal-based
**Done when:** three-file version bump greps clean; `make build-self` run and
`git status` clean afterwards; CHANGELOG `[Unreleased]` entry present;
three backlog slugs parse out of `workspace.toml`.
**Traces to:** AC11, AC12, AC13

### T7 — Real-invocation QA + full gates
**Depends on:** T6
**Mode:** Visual / manual QA
**Done when:** each of the three modified scripts invoked for real against this
repo (valid `--root`, omitted, relative) with exit code and stdout recorded in
the PR; `make sast`, `python3 tools/lint-ruff.py`, `python3 -m pytest packs/core/tests -q`
all green.
**Traces to:** AC5, AC9, AC10

## Risks

| Risk | Mitigation |
|---|---|
| **Fix does not satisfy Snyk** (unverifiable from here — Assumption 2) | Change is independently justified by AC6; if the org scan still reports, escalate to `.snyk` + the YAML-merge backlog item |
| Semgrep rule false-positives on the `is_relative_to` guard | T5 test asserts silence on that shape explicitly |
| `make build-self` reverts projection-only edits | Memory: check `git status` after; close in-PR |
| Directory assertion breaks an adopter invocation | AC5 parity tests across three valid `--root` forms |
| Version bump misses one of three files | T6 greps all three |

## Declined patterns

| Tempted to | Declined because |
|---|---|
| Add `mode: taint` argv sources to `env-path-taint.yml` (the original ask) | Spike proved it cannot reach the finding (0 on the real file) and floods the gate (20 FPs). The structural rule in T5 replaces it. |
| Sweep all 73 sites in one PR | Migration, not a fix. Backlogged as `pack-argv-path-boundary-sweep`. |
| Confine `--root` to a hardcoded prefix | Breaks the linter's documented purpose — `--root` *is* the scan scope. |
| Extract a shared `pathsafe.py` across the four scripts | Skill scripts are standalone by design; no second consumer outside work-loop yet. Inline per file; extract when a real second caller appears. |
| Build the YAML-merge so packs can ship `.snyk` | Large agentbundle change, wrong layer, and still needs each org to enable Consistent Ignores. Backlogged. |
| Change SHA-1 → SHA-256 in `loop-cohort.py` while in the file | Separate concern with a state migration and a SKILL contract edit. Not this PR. |

## Resolve-vs-surface disposition record

| Item | Disposition |
|---|---|
| Are the Snyk findings real? | **Resolved** — CodeQL `py/path-injection` independently clears them |
| Can a taint rule reproduce them? | **Resolved** — spike, empirically no |
| Will the fix satisfy Snyk? | **Surfaced** — unverifiable without Snyk access; recorded as Assumption 2 |
| Scope: 4 files or all 73 sites? | **Surfaced at the approval gate** — spec scopes to 4, backlogs the rest |
| Ship `.snyk` per pack? | **Resolved** — structurally unavailable; backlogged |
