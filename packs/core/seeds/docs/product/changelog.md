# Changelog

All notable user-visible changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Maintenance: add a `## [pack-name][version] — YYYY-MM-DD` section in the same
> PR that bumps `pack.toml`. You know the version at write time because you are
> setting it. A PR that bumps two packs adds two sections. Keep this file
> newest-first. Rewrite entries for users, not contributors — see the
> [Common Changelog guidance](https://common-changelog.org/).

## [core][1.0.0] — 2026-07-31

### Added

- **`loop-engine.py`** — new Phase-1 FSM phase tracker. Owns `engine-state.json`
  (gitignored); enforces legal phase transitions for `code` and `spec-plan` modes;
  runs per-event guards via `loop-cohort` subcommands; generates `run_id` UUID at
  init that is shared with the cohort state machine.
- **`check-spec-status.py`** — new script; guard for the `reviewers-clean` event in
  code mode. Imports `parse_status` from `lint-spec-status.py` via `importlib`;
  exits 0 iff `spec.md` Status is `Shipped`.
- **`test-loop-cohort.py`** — 67 unit tests for Phase-1 cohort verbs.
- **`test-loop-engine.py`** — 84 unit/integration tests for the Phase-1 FSM engine.

### Changed

- **`loop-cohort.py`** — Phase-1 rewrite. `init` now requires `--run-id <uuid>` and
  refuses if `state.json` already exists (use `reset` to clear). New verbs:
  `identity`, `status`, `reset`, `plan check-current`, `schedule check-current`,
  `record-attempt`, `wave check`, `wave advance`, `review inspect`. Updated
  `approve-plan` and `review record` require `--expect-run-id`. `review record`
  splits into `--fingerprint` (findings path) and `--report` (clean path) with
  separate counter semantics. `schedule` requires `--expect-run-id` and persists
  `plan_hash` + `schedule_waves`. `check --phase implement` is a stub (always exits 0).
  Disabled verbs: `dispatch-decision`, `worktree`, `auto-parallel` (exit non-zero).
- **`assets/state.json`** — updated to Phase-1 field set. Removed: `iteration_count`,
  `max_iterations`, `token_budget_used_pct`, `token_budget_cap_pct`,
  `consecutive_same_error_count`, `consecutive_same_error_threshold`. Added:
  `schema_version`, `run_id`, `approved_spec_hash`, `approved_plan_hash`, `plan_hash`,
  `schedule_waves`, `current_wave_index`, `implementation_retry_count`,
  `max_implementation_retries`, `last_record_attempt_cycle_id`, `review_round_count`,
  `review_retry_count`, `max_review_retries`.
- **`SKILL.md`** — updated init pair (engine + cohort), `approve-plan --expect-run-id`,
  `plan check-current`, review record split, stasis detection via `review inspect`,
  supervisor mode note (parallel disabled), termination conditions.
- **`references/state-schema.md`** — rewritten for Phase-1 field set; documents both
  `state.json` and `engine-state.json` fields.
- **`references/supervisor-mode.md`** — Phase-1 note at top: parallel fan-out disabled.

### Removed (breaking)

- **`approve-plan` top-level command** — replaced by `loop-cohort plan approve`.
  Automation calling `loop-cohort.py approve-plan` must update to `loop-cohort.py plan approve`.
- **`worktree` subcommands** — disabled in Phase 1; all exit non-zero. Phase-2 re-enables.

<!-- Example entry (replace with your first real version):

## [pack-name][version] — YYYY-MM-DD

### Added / Changed / Fixed

- Entry written in the PR that bumps pack.toml version.

-->
