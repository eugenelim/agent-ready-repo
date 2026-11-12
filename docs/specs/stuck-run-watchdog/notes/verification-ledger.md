# Verification ledger: stuck run watchdog

Execution observations for `docs/specs/stuck-run-watchdog`. Settled design lives in the plan.

## Evidence

- Unit and posture suite: `tools/test_stuck_runs_watchdog.py`, 101 cases, green. Deliberate breaks of the stuck threshold, the page-10 incomplete flag, the issue page limit, the bot-login check, the waiting-status condition of the exemption, and the partial-page-ten case each made at least one test fail.
- Real entry point: `python3 tools/stuck_runs_watchdog.py --repo <owner>/<repo> --dry-run` against the live repository made read-only calls only, exited 0, and listed nine stuck runs (two Nov 5 zombies, five 19 to 21 hour queued runs, one 2052 hour queued run, one waiting Claude plugin publish run) before the approval-gated exemption existed. The same run's API record shows `path` as exactly `.github/workflows/publish-claude-plugins.yml`, the form the exemption matches.
- The issues API accepts `creator=github-actions[bot]` and returns that login: read-only probes of three public repositories that hold bot-authored items.
- `actionlint` (1.7.12) and `zizmor` (1.28.0, with and without `--min-severity high`) report nothing on the workflow. Parity lint, the dedup guard, `make lint-ruff lint-mypy` and `make precheck` pass.
- Review: four Codex review rounds on the code (adversarial and security roles) found a misleading "no stuck run" message on a truncated listing, unquoted Markdown in workflow names, a missing creator filter, no warning annotation on a truncated listing, an empty `run_started_at` read as absent, and a weak partial-page test. All were repaired test-first. The last round was clean for both roles.

## Known limits

- The first hourly run cannot be proven before merge: a schedule only starts from the default branch. After merge, dispatch it twice and confirm the job succeeds and at most one watchdog issue exists. The checkout step runs with only `actions: read` and `issues: write`; the repository is public, so it should work. If it does not, the amendment is to add `contents: read`.
- The Pages deploy is deliberately not exempt from the `waiting` rule: it is the stall this watchdog exists to catch.
- The rendered `gh run cancel <id>` has no `--repo`, because the criterion fixes that text; the force-cancel line names the repository.
- One run of `test_state_guard_controls_detect_each_persistent_channel` failed with a `PermissionError` from `os.kill` while the machine was under heavy load, and passed when rerun alone.
- `STEP_DISPOSITION` count in `docs/architecture/verification-graph.md` (167) is older than the roster (185). It was not touched.
