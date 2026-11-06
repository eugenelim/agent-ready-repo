# Verification ledger: Review obligation policy

Execution observations for the approved plan. Obligations stay in `spec.md` and `plan.md`. Run `run-e710f30de8457c18` reached terminal at `511ccbbb4` on 2026-11-06 under approval pair 2 (spec digest `4aa26808…`, plan digest `6becbb74…`).

## Gate evidence (final revision)

The supervisor admitted `run-gates` with all 36 criteria passing on the revision after `regenerate` (`4b8a44c47`). The commands, all exit 0:

| Check | Result |
| --- | --- |
| `make lint-ruff lint-mypy` (ruff 0.16.10) | passed |
| Review unit suites (`test_review_tiers.py`, `test_review_obligation_rules.py`, `test_review_carry.py`, `test_supervisor_review.py`, `test_review_disposition.py`, `test_review_contracts.py`, `test_supervisor_cutover_source_checks.py`) | 416 passed |
| Roster (`test_execution_supervisor_records.py`, `test_delivery_contract_bundle.py`, `test_registry_upgrade_notes.py`) | 137 passed |
| `WORK_SUPERVISOR_INTEGRATION=1 test_review_obligation_policy.py` | 17 passed |
| `WORK_SUPERVISOR_INTEGRATION=1` closure, review gate, and Git suites | 70 passed |
| `WORK_SUPERVISOR_INTEGRATION=1 test_supervisor_readiness.py` | 14 passed |
| `tools/check-core-release.py --base origin/main` | consistent at Core 4.0.19 |

## Criteria

Each criterion maps to the suite that proves it. Unit-level-only coverage is named.

- AC-0001, AC-0005, AC-0007, AC-0009, AC-0010, AC-0012, AC-0020, AC-0022, AC-0023, AC-0024, AC-0026, AC-0027, AC-0028, AC-0029: flows in `test_review_obligation_policy.py` (supervisor harness). AC-0005 and AC-0020's `wording-only` legs run against a fixture copy of the skill's rules file with `wording_only_enabled` true, the only file the tier reads; the flow harness points the in-process supervisor's rules path at it.
- AC-0002, AC-0003, AC-0004, AC-0006, AC-0008, AC-0011, AC-0012 (forcing half): `test_review_tiers.py` over real throwaway repositories. AC-0003's disabled case asserts `full` against the shipped rules.
- AC-0013, AC-0014, AC-0015, AC-0023 (unit cases): `test_review_carry.py` and `test_supervisor_review_closure.py`.
- AC-0016, AC-0032, AC-0033: roster schema tests.
- AC-0017, AC-0018, AC-0019, AC-0021, AC-0022 (parse half), AC-0030, AC-0031, AC-0035, AC-0036: `test_review_obligation_rules.py`.
- AC-0024 (control characters and NUL in ids; two findings sharing a reference) and AC-0025 (request id stable across a HEAD move) are proven at unit level in `test_review_obligation_policy.py`, not through a full flow.
- AC-0034: reported `pass` at run-gates on the owner's decision (2026-11-06) on `check-core-release --base origin/main` evidence. The literal check, with the merge base equal to freshly fetched `origin/main`, runs after the post-run rebase and is recorded below.

## Review

- Code review round 1 (adversarial, security, quality engineer): 17 findings, 9 material; repaired by T7.
- Round 2: security clean; 3 material open; owner chose one more round (T9).
- Round 3: quality clean; 2 material Markdown fence defects; owner chose a class-closing fix (T10).
- T10 and T11 final adversarial checks each found further Markdown inputs; owner chose to ship the `wording-only` tier disabled (amendment, approval pair 2, T12).
- The amendment review and the review of the regenerated projections were clean.
- The run used the supervisor pinned at start until `regenerate`; the new selection rule (`protected_classes`) then applied to the last selection, answered with `[]` under the owner's adversarial-only direction. The unit stays protection-unknown through its earlier selections, so every subject classified `full`.

## Deviations

- The run reported a criterion failure once (AC-0034, after `main` shipped Core 4.0.18 mid-run); T8 moved the release to 4.0.19.
- T12's flow harness uses a rules-file copy, not a whole-skill copy; the plan's T12 text records this.

## Post-run merge and release check

- 2026-11-06: merged freshly fetched `origin/main` (`a947d086d`, Core 4.0.18 from #1699) into the branch at `b284ef2fc`; conflicts in the evals, the ADR index, and the version pins resolved by keeping both eval sets and both index rows and Core 4.0.19; installed projections rebuilt with `agentbundle catalogue self-host --write --force` and `make bootstrap-sites`.
- AC-0034 literal check: `git merge-base origin/main HEAD` equals `origin/main` (`a947d086d`), and `tools/check-core-release.py --base origin/main` reports the release consistent at 4.0.19.
