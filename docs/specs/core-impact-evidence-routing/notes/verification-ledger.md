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

## T2 (2026-10-10)

Interpreter: Python 3.11 for pytest; a throwaway venv with ruff, mypy, pyyaml, jsonschema, tomlkit for lint and catalogue lint (`PYTHONPATH` set to `packages/*/`).

- `pytest packs/core/tests/pack/test_impact_evidence_routing.py packs/core/tests/pack/test_readme_repository_exploration.py packs/core/tests/skills/repository-exploration packs/core/tests/skills/new-spec -q -p no:cacheprovider`: 327 passed, 79 subtests passed.
- `python3 tools/lint-pack-test-boundary.py`: passed (8 cases).
- `make lint-ruff lint-mypy`: all checks passed; mypy no issues in 155 files.
- `agentbundle catalogue lint --root . --deep`: ok, 75 findings (warnings only, none from this change).
- Grep of `packs/core/tests` for the two changed `new-spec` eval prompts: no pin (only an unrelated `code-intelligence pack` literal in `test_readme_repository_grounding.py`).

## T3 (2026-10-10)

- `pytest packs/core/tests/pack packs/core/tests/skills/repository-exploration packs/core/tests/skills/bug-fix -q -p no:cacheprovider` (Python 3.11): 468 passed.
- Work-loop tests that reference `evals.json` (9 files): 389 passed. No test pins the work-loop or bug-fix eval id lists or counts beyond the existing `>= 14` floor.
- `python3 tools/lint-pack-test-boundary.py`: passed (8 cases).
- `make lint-ruff lint-mypy`: all checks passed; mypy no issues in 155 files.
- `agentbundle catalogue lint --root . --deep`: ok, 75 findings (warnings only, none from this change).
- The `Fix the bug where saving a draft loses the title` negative equals a `should_trigger: true` query in `bug-fix/evals/eval_queries.json` (checked in the build script).
