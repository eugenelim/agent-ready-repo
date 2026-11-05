# Verification ledger: precheck-path-gates

Execution observations, 2026-11-05. Run `run-a0b23fbabd9eb4f2`, tasks T1 to T8, terminal.

## Gates run locally (targeted only)

- `tools/test_precheck.py` and `tools/test_lint_agents_md_local_gate.py`: 34 passed.
- `tools/test_local_ci_shared_test_deduplication.py` with the roster pins `test_cognitive_load_repository_contract.py`, `test_verify_entry_receipts.py` and `tools/test_agents_md_readability_floor.py`: 99 passed (about 2 minutes, the heaviest local step).
- `tools/lint-agents-md.py`, `tools/lint-ci-parity.py`, `make lint-ruff lint-mypy`: pass. Root `AGENTS.md` stays at 170 lines.
- Not run locally, left to CI: `make test`, the roster, `make ci`.

## Review

Five rounds of `adversarial-reviewer` and `security-reviewer`. Supported findings by round: 8, 3, 1, 1, 0. Every finding was repaired in tasks T5 to T8 except the two deferred items below. `finding-adjudicator` was not run: the controller checked each cited claim against the code before assessing it.

Deferred, not required by the accepted intent: the test `test_option_arguments_are_not_targets` in `tools/test_lint_agents_md_local_gate.py` pins `make -C web build` as reporting `build` against the root Makefile; no `AGENTS.md` uses `-C` yet.

## Manual run for AC-0017

Throwaway worktree cut from `HEAD`, one line appended to `packs/repo-governance/.apm/skills/new-adr/references/infra-decisions.md`, `make precheck PRECHECK_ARGS="--base HEAD"`. Evidence: `.context/verify/repository-precheck/<run-id>/`.

- The first run found that step 3 failed: `self-host --write` refuses a dirty tree. The entry now passes `--force` and says why.
- The second run, from the corrected entry: step 2 exit 2 (drift on the two projections, only the self-host check, pack tests printed as not run); step 3 exit 0; step 4 exit 0 with `self-host --check: ok`. Wall time per `make precheck` was about 24 s under a load average near 20.
- The throwaway worktree and branch were removed; `git worktree list` and `git branch --list 'precheck-qa-*'` show none.

## Supervisor notes

`work-supervisor.py` step commits hit the 60 s `git add -A` limit under load several times; a dry `git add -A -n` to warm the file cache, then an immediate retry, admitted each.

## Delivery records

The supervisor's `delivery/` records for run `run-a0b23fbabd9eb4f2` are not part of the merged tree. The full history, with them committed, is on the remote branch `vlx/verification-cf8b92-evidence`.
