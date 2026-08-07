# Plan: boundary validation for CLI path arguments in shipped work-loop scripts

- **Status:** Done
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
**Tests:** new `packs/core/tests/skills/work-loop/test-root-validation.py` (hyphens — matches the sibling convention; note pytest's default `test_*.py` will NOT collect it, so it needs an explicit runner):
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
**Tests:** `test-root-validation.py` asserts `classification == "invalid"` at
exit 0 for a missing report — see the amended AC3.
**Approach:** both sites call one shared `_resolved_report()`. **Revised during
EXECUTE:** normalise-only, not file-ness assertion — `_classify_report` returns
`invalid` for an unreadable report and SKILL.md defines that as a Surface
signal, so raising would convert a defined outcome into an operational error.
The `resolve()` is wrapped against `ValueError` (embedded null) so it does not
become a raising site itself.
**Traces to:** AC3

### T5 — Semgrep boundary rule + fixtures
**Depends on:** T2, T3, T4
**Mode:** TDD
**Tests:** `tools/test-semgrep-argv-boundary.py` runs the rule over two
committed fixtures and asserts 1 finding on the positive, 0 on the negative.
**Approach:** new `tools/semgrep/argv-path-boundary.yml`, a **structural** rule
(not `mode: taint` — proven unable to cross a call). Must not fire on the
`resolve()`-then-`is_relative_to()` guard shape, or it false-positives on
`check-spec-status.py:72`. Scope via `paths.include` to the three fixed
scripts; record the repo-wide finding count and the expansion condition in the rule
header — one location, since it drifts as the ratchet expands.
**Traces to:** AC7, AC8

### T6 — Version bump, projections, changelog, backlog
**Depends on:** T5
**Mode:** Goal-based
**Done when:** three-file version bump greps clean; `make build-self` run and
`git status` clean afterwards; changelog entry present; every backlog slug
named by AC13 parses out of `workspace.toml` (count lives in AC13, not here).
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
| ~~Change SHA-1 → SHA-256 in `loop-cohort.py`~~ | **Reversed on request during EXECUTE** — folded in as AC15 after confirming it cannot break the loop: fingerprints are opaque tokens compared set-wise between rounds, and `_RE_FINGERPRINT` accepts both widths so an in-flight cohort survives the upgrade. |
| Convert `test-loop-cohort.sh` to Python in this PR | Raised during EXECUTE. Real portability defect (493 lines, ~20 bash-isms, unrunnable on Windows) but not urgent — `docs.yml:92` runs it on ubuntu and pack tests never install into adopter repos. Bundling a 51-case sequential port into a security fix would obscure both. Backlogged as `loop-cohort-shell-suite-to-python`. |

## Resolve-vs-surface disposition record

| Item | Disposition |
|---|---|
| Are the Snyk findings real? | **Resolved** — CodeQL `py/path-injection` independently clears them |
| Can a taint rule reproduce them? | **Resolved** — spike, empirically no |
| Will the fix satisfy Snyk? | **Surfaced** — unverifiable without Snyk access; recorded as Assumption 2 |
| Scope: 4 files or all 73 sites? | **Surfaced at the approval gate** — spec scopes to 4, backlogs the rest |
| Ship `.snyk` per pack? | **Resolved** — structurally unavailable; backlogged |
