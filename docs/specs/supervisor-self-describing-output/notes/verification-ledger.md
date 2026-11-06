# Verification ledger — supervisor-self-describing-output

Execution observations that the mechanical gates cannot settle. The approved
`spec.md` and `plan.md` hold the obligations.

## Review findings and their dispositions

| Finding | Reviewer | Severity | Assessment | Disposition |
| --- | --- | --- | --- | --- |
| ADV-01 | adversarial-reviewer | Nit, non-material | supported | Deferred: the report-after-status case cannot detect a leaked routing context; it still catches an emit that routes another verb. |
| QE-01 | quality-engineer | Concern, material | supported | Repaired by T8: the retry cap is read inside a guard instead of outside every handler. |
| QE-02 | quality-engineer | Nit | unsupported-opinion | None: the usage-error guard in the answer printer is redundant but required by the plan. |
| ADV2-01 | adversarial-reviewer | Concern, material | supported | Repaired by T9: the guard covers every way `int()` of a policy value can fail (`LookupError`, `TypeError`, `ValueError`, `ArithmeticError`). |
| QE3-01 | quality-engineer | Nit, non-material | supported | Deferred: the unreadable-cap test compares exit codes and route presence, not whole answers. |

The last two review rounds on the regenerated subject, by the adversarial reviewer and the quality-engineer, both returned Clean.

## Observations and deviations

- **T4 red-first not seen.** The implementer wrote the routing code before its tests, so the new tests were not observed red. The controller ran two mutation checks on the ungated unit tests (a changed route string, a terminal route pointed at the idle string); both turned the tests red, and the file was restored byte-identical.
- **T9 lint.** The implementer's one-line change made a line 111 characters long and it did not read the ruff output. The controller moved the trailing comment onto its own line (comment-only), then re-ran ruff, mypy and 39 related integration cases.
- **Assessment label.** The ADV2-01 assessment record names `finding-adjudicator` as its judgment authority, but the controller assessed it by a deterministic check (`int(float("inf"))` raises `OverflowError`). Records are immutable; later assessments name `controller`.
- **Known skip.** `make lint-ruff` fails on a `collapsible-if` in `close-work/scripts/closure_index.py:1375` with ruff 0.17.4; the file is unchanged against `origin/main`. Captured as `docs/product/captured/pre-existing-ruff-sim102-closure-index.md`. Ruff and mypy are clean on every file this run changed.
- **Supervisor staging timeouts.** Three `report` calls refused `denied-git-unavailable` under machine load (60 second staging limit). Recovery each time: commit nothing, call no `next`, warm the index with a dry `git add -A -n`, re-send the same result file; each was then admitted.
- **Main moved during the run.** Core 4.0.18 shipped from another change (risk-trigger record). The run was not merged mid-run; T7 took the next patch above fetched `origin/main`, 4.0.19.
- **Roster inventory.** `tests/roster/test_workspace_retirement_inventory.py` requires a row for a spec that names retired workspace files; the row `docs/specs/supervisor-self-describing-output/*` was added after the run ended.
- **Project-knowledge capture.** The captures the work-loop calls for at the spec and plan approval gates were not run: the owner did not ask for them when offered.
- **Spec review.** 18 pre-EXECUTE review rounds and 6 adjudicated stops preceded approval; the frozen-spec refusal (dispatch.py and its packaged mirror) was deferred to a separate change by the owner.

## Evidence at the end of the run

- `status --check` exits 0; stage `terminal`; 9 of 9 tasks complete; retry count 0; all 21 criteria supported.
- `make precheck` exits 0 after the regenerate step: self-host drift clean, core release check consistent.
- Pin suites: `tools/test_workspace_status.py`, `tools/test_workspace_status_cli.py`, `tools/test_local_ci_shared_test_deduplication.py` 187 passed; `tests/roster/test_registry_upgrade_notes.py` 32 passed.

## Completion handoff

| Durable output | Status | Evidence |
| --- | --- | --- |
| Interface reference | Done | `session-resumption.md` routing table, `supervisor.md`, `state-schema.md` sentences, pin tests green |
| Release history | Done | core 4.0.19 in `pack.toml` and `plugin.json`, changelog fragment `5ae0d156-a8ae-438c-9b11-aa04b4b2aeb7`, `_RELEASED["core"]` pin |
| User guides | None applicable | no guide names the changed answers |
| Decision record | None applicable | no decision made or reversed |
