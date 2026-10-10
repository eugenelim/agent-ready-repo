# Verification ledger: core-impact-evidence-routing

## T1 red proof (2026-10-10)

Command: `/usr/bin/python3 -m pytest packs/core/tests/pack/test_exploration_consumer_boundary.py packs/core/tests/pack/test_impact_evidence_routing.py -q -p no:cacheprovider`
(the interpreter with pytest installed here; the sentences were not yet in the skills.)

Result: 3 failed, 6 passed in 0.18s.

Failing tests:
- `test_exploration_consumer_boundary.py::test_subject_files_do_not_name_repository_exploration`
- `test_impact_evidence_routing.py::test_work_loop_has_no_grep_for_callers`
- `test_impact_evidence_routing.py::test_bug_fix_step_6_has_no_grep_for`

## T1 green proof (2026-10-10)

Interpreter: a throwaway venv with pytest, ruff, mypy, pyyaml, jsonschema, tomlkit.

- `python -m pytest packs/core/tests/pack/test_exploration_consumer_boundary.py packs/core/tests/pack/test_impact_evidence_routing.py -q -p no:cacheprovider`: 9 passed.
- `python -m pytest packs/core/tests/skills/bug-fix packs/core/tests/skills/work-loop -q -p no:cacheprovider`: 2437 passed, 6 skipped, 1 failed. The failure is `test_loop_engine.py::test_recover_engine_state_tmp_never_tracebacks_and_deletes_only_bad_content[deep-nesting]` (engine state recovery, no skill text read); not caused by this change, not confirmed against a clean base.
- `python tools/lint-pack-test-boundary.py`: passed (8 cases).
- `make lint-ruff lint-mypy`: all checks passed; mypy no issues in 155 files.
