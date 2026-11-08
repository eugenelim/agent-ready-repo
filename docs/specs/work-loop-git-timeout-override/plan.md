# Plan: the work-loop supervisor's git timeout is overridable

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_git.py` (the timeout constant and its two readers); `packs/core/tests/skills/work-loop/test_supervisor_git.py` (existing tests that monkeypatch `GIT_TIMEOUT_S` and load the module by path); `packs/core/.apm/skills/work-loop/scripts/_git_history.py` (the one reader that records the value). Uncertainty: none beyond the spec's defaulted assumptions.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none. Execution observations
> belong in `docs/specs/work-loop-git-timeout-override/notes/verification-ledger.md`.

## Approach

Replace the literal `GIT_TIMEOUT_S = 60.0` with a call to one pure resolver, `_resolve_git_timeout(raw)`, bound at import. Both launch paths and `_git_history.py` already read the module name, so nothing else in the code moves. The supervisor note and the release bookkeeping follow as a second task. The riskiest part is the release bookkeeping, not the code: a pack content change needs the matching version, fragment and registry pin together.

## Constraints

- Both launch paths keep a hard wall-clock bound: the ceiling is 240 seconds, inside the run lock's 300-second git margin, and the floor is the current 60.
- The variable is read from the environment of whichever process loads the module; git's child environment stays the stripped set in `_INHERITED_ENV` and never carries it.
- Root `AGENTS.md`: cut before adding. No new module, dependency or refusal code.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Operations note in `supervisor.md` | T2 | `grep` finds the note in the source and both projections | close-work reads the note |
| Release history (core patch bump, fragment) | T2 | `tools/changelog.py validate`, `tools/check-core-release.py`, registry pin test | close-work reads the fragment's version |

## Design (LLD)

### Design decisions

- **Resolve at import, bind to the existing name.** Tests and `_git_history.py` use `GIT_TIMEOUT_S` as a module attribute; keeping that name keeps every reader working and makes "read once" true by construction.
- **Parse with `float()`, then require `math.isfinite`.** Anything that is not finite, including a `ValueError` from `float()`, takes the 60.0 default; a finite value is clamped with `min(240.0, max(60.0, value))`.

### Interfaces & contracts

`_resolve_git_timeout(raw: str | None) -> float` is module-private. The two bounds are module-level constants beside it.

### Failure, edge cases & resilience

An unset, empty, negative, zero, non-numeric, `nan` or `inf` value never raises: unset, empty, non-numeric, `nan` and `inf` take the default; zero and negative values are finite and clamp to 60.

## Tasks

### T1: the resolver returns the specified value for every input class

**Depends on:** none

**Tests:** (TDD; AC-0001 to AC-0007)
- A table over the resolver: `None` and `""` → 60.0; `"90"`, `"60"`, `"240"`, `"90.5"`, `" 90 "`, `"1e2"`, `"1_00"` → the number; `"5"`, `"0"`, `"-3"` → 60.0; `"9000"` → 240.0; `"abc"`, `"10m"`, `"nan"`, `"inf"`, `"-inf"`, `"1e309"` → 60.0 (AC-0001 to AC-0004).
- The ceiling constant is no greater than `_supervisor_admission._LOCK_MARGIN_SECONDS` (AC-0007).
- A fresh copy of `_supervisor_git.py` loaded under a unique module name, registered in `sys.modules` before it runs (its dataclasses look the module up by name) and removed afterwards, has `GIT_TIMEOUT_S == 120.0` with the variable set to `"120"` and 60.0 with it unset (AC-0001, AC-0002, at the import boundary). These tests and the resolver table live in a new unmarked module, `test_supervisor_git_timeout.py`, because `test_supervisor_git.py` is skipped without `WORK_SUPERVISOR_INTEGRATION=1`.
- `_launch_bounded` keeps its existing slow-child tests. One added test drives a real slow child through `_launch` with `GIT_TIMEOUT_S` patched small and asserts `denied-git-unavailable` (AC-0005).
- In `test_git_history_evidence.py`, the record test patches `GIT_TIMEOUT_S` on the module copy `_git_history_supervisor_git` that `_git_history.py` loads, and asserts `timeout_s` equals it. The existing `== 60.0` assert is replaced by an assert against a value pinned on that module copy, because the `launches` fixture loads and caches the copy before a test body can clear the variable (AC-0006).

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_git_timeout.py packs/core/tests/skills/work-loop/test_git_history_evidence.py -q` passes with no skips in the new module, and `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_git.py packs/core/tests/skills/work-loop/test_supervisor_effects.py -q` stays green.

### T2: the operations note and the core release are in place

**Depends on:** T1

**Tests:** (goal-based)
- `grep -n WORK_LOOP_GIT_TIMEOUT_S packs/core/.apm/skills/work-loop/references/supervisor.md .agents/skills/work-loop/references/supervisor.md .claude/skills/work-loop/references/supervisor.md` finds the note in all three, after `make build-self`.
- `python3 tools/changelog.py validate`, `python3 tools/check-core-release.py --base=origin/main` and `python3 -m pytest tests/roster/test_registry_upgrade_notes.py -q` pass.

**Approach:**
- The registry pin in `tests/roster/test_registry_upgrade_notes.py` (`_RELEASED["core"]`) moves to the new core version and this release's fragment, in the same commit as the bump; the roster test fails otherwise.

**Done when:** the three checks above pass, and `make precheck` reports self-host consistent.

## Rollout

One pull request, one core patch release. No migration; the default behaviour is unchanged.

## Risks

- Slow calls that each finish under the ceiling add up inside one run-lock hold, and the ceiling does not bound that total; the spec records it as an accepted risk.
- A long timeout can hide a real hang for up to 240 seconds per call; the ceiling bounds it, AC-0007 keeps it inside the lock margin, and the default is unchanged.
- Another core release can land first and take the version; re-derive the bump and the pin by merging `main` before merge.

## Changelog

<!--
Approvals, and nothing else.

- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->

