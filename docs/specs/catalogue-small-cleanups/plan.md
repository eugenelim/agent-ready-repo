# Plan: Catalogue small cleanups

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

## Approach

Correct the inaccurate `pages.yml` scope reason without changing behavior.
Prove it by inspecting the actual `WORKFLOW_SCOPE` value, remove its resolved
backlog block and the stale fixture-indentation and engine-build Ruff blocks,
and close the light spec.

## Constraints

- The Gate B workflow and its missing local replay remain unchanged and open.
- The Ruff-canonical self-host fixture indentation remains unchanged; only its
  stale/misdescribed backlog metadata is removed.
- The landed root Ruff `/build` exclusion remains unchanged; only its stale
  backlog metadata is removed.
- `profiles/AGENTS.md`, package versions, generated scaffold copies, and engine
  sources are out of scope.

## Construction tests

- Direct assertion: load `WORKFLOW_SCOPE["pages.yml"]` and require the three
  disposition facts from AC1.
- Backlog-preservation check: parse `workspace.toml` from local `main` and the
  working tree with `tomllib`; the base-minus-current slug set must equal exactly
  `plugin-pages-yml-parity-disposition` plus
  `plugin-fixture-continuation-indent`, and current-minus-base must be empty.
- Repository gates: focused CI-parity checks, Ruff, catalogue verify,
  workspace reconciliation, and the required policy/build checks.

## Tasks

### T1: Plugin parity disposition and queue state agree

**Depends on:** none

**Touches:** `tools/lint-ci-parity.py`, `workspace.toml`, `docs/specs/catalogue-small-cleanups/**`, `docs/specs/README.md`

**Tests:**
- Goal-based: inspect the actual `WORKFLOW_SCOPE["pages.yml"]` value for
  `check-site-plugin-offers.py`, `non-blocking`, and `self-test` (AC1).
- Goal-based: `python3 .agents/skills/workspace-status/scripts/workspace_status.py
  reconcile --root .` reports no new Type 2 or Type 3 findings; a `tomllib`
  comparison against `git show main:workspace.toml` proves exactly the resolved
  and stale slugs were removed and none added (AC2).
- Goal-based: the spec index contains `catalogue-small-cleanups` with the same
  status as `spec.md` (AC3).
- Goal-based: `python3 .agents/skills/work-loop/scripts/lint-spec-status.py`
  and the repository gates pass (AC4).

**Approach:**
- Replace the inaccurate `pages.yml` scope reason with the existing design's
  actual blocking/non-blocking disposition.
- Remove the parity disposition and stale fixture-indentation comment-and-entry
  blocks, plus the stale engine-build Ruff block, from `[backlog].open`; leave
  Gate B, the profile pointer, and every excluded implementation item open.
- Add the spec row after the spec/plan review is clean, then close the spec after
  implementation review and gates.

**Done when:** the resolved and stale slugs are absent, Gate B and the profile
pointer remain open, the spec index is current, and every available gate is
green.

## Risks

- This session cannot run tempfile- or generated-output-dependent gates. The
  exact commands are handed to the user for execution in a writable shell.

## Changelog

- 2026-08-10: Initial light-mode plan after queue reconciliation and user scope
  confirmation.
- 2026-08-10: Deferred Gate B after pre-execution review showed that a safe
  workflow replayer needs independent parser safety coverage and full-mode
  treatment; collapsed the remaining work into one mechanical task.
- 2026-08-10: Left the fixture indentation item open after Ruff 0.15.17
  canonicalized the current source and rewrote the proposed deeper indentation;
  narrowed implementation to the parity disposition only.
- 2026-08-10: User confirmed removing the stale fixture-indentation backlog
  metadata in this cleanup while leaving its Ruff-canonical source untouched.
- 2026-08-10: Final queue audit confirmed local `main` already anchors Ruff's
  exclusion at `/build`; removed the stale completed-work backlog record without
  changing Ruff configuration or engine code.
