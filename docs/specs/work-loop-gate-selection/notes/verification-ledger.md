# Verification ledger: work-loop-gate-selection

Execution observations, 2026-11-05. Run `run-0cb3f2d23fc3ae50`, tasks T1 to T4, terminal.

## Gates run locally (targeted only)

- Work-loop pins `test_gate_selection_contract.py`, `test_verify_entries_contract.py`, `test_evidence_modes_contract.py`: 48 passed.
- `tools/check-core-release.py --base origin/main`: release is consistent. Core is 4.0.16; `origin/main` was at 4.0.15 when fetched.
- After regenerating the projections: `tools/test_workspace_status.py` and `tools/test_workspace_status_cli.py` 136 passed (these need `tomlkit`, which core's `AGENTS.md` pins; the first run without it showed 18 environment failures); `tools/test_local_ci_shared_test_deduplication.py` 51 passed; the 147 roster tests selected by `-k "projection or work_loop or self_host"` passed.
- `make lint-ruff lint-mypy`: pass.
- Not run locally, left to CI: `make test`, the full roster, `make ci`.

## AC-0006 (self-host check)

The supervisor never issued a `regenerate` request: the pack edits touch no file it pins, so the installed copies stayed stale while the run was open. With the owner's approval, AC-0006 was reported `pass` at each `run-gates` request, to be re-checked for real afterwards. The real check after the run: before regenerating, `self-host --check` failed with 6 drifts (the six work-loop copies); after a controller-side `self-host --write` on the terminal tree it reports ok. The projections are committed in their own commit.

## Review

Three rounds of `adversarial-reviewer`; no conditional role was selected, with a recorded reason for each omission (ordinary guidance wording, no authority, untrusted-input, tool or permission effect). Supported findings by round: 1, 1, 0. Repairs: T3 (a `verification entry` / `verify entry` term collision, plus two wording nits) and T4 (two pin tests named for the wrong criteria). `finding-adjudicator` was not run: the controller checked each cited claim before assessing it.

Deferred, not required by the accepted intent: `test_ac0001_section_bars_naming_undeclared_check_and_keeps_task_zero` reads only the verification-modes section, so its AC-0001 name is earned only through the separate SKILL.md pin on line 33 of the same file.

## Heads-up for the pull request

Core is 4.0.16 here and 4.0.15 on `origin/main`: merging `main` conflicts on the version lines of `pack.toml` and `plugin.json` and may conflict in the changelog. Re-run `tools/check-core-release.py --base origin/main` right before merging, since `main` can ship another core patch meanwhile.

## Delivery records

The supervisor's `delivery/` records for run `run-0cb3f2d23fc3ae50` are not part of the merged tree. The full history, with them committed, is on the remote branch `vlx/verification-cf8b92-evidence`.
