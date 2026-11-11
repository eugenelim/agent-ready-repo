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

## T4 (2026-10-10)

- Versions: `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` set to 3.0.2; both grep counts print 1.
- Changelog: `## [core][3.0.2] — 2026-10-10` sits beneath `[Unreleased]`; `grep -n -m3 '^## \['` shows Unreleased (63), core 3.0.2 (67), core 3.0.1 (81).
- Pointer sub-bullet added after VI-0008 in `optional-intelligence-exploration-composition/spec.md`; the slice check printed `slice ok`; `lint-spec-status.py --root .` reported metadata clean.
- Self-host: needed `--force` (the dirty-tree check only, because the T4 edits are uncommitted). 16 projected files changed (14 modified, 2 new `repository-exploration/evals/eval_queries.json`), including `new-spec/evals/evals.json` from earlier source changes. A second run left `git status --porcelain` identical. `catalogue verify --root .`: ok. The projected `.claude/skills/repository-exploration/SKILL.md` description equals the source.
- `tools/test_build_site_routing.py` (Python 3.11): 94 passed, 1 skipped. No test in `packs/core/tests` or `tests/roster` pins core 3.0.1 or plugin.json parity (the "3.0.1" hits are unrelated fixtures and IP literals), so no pin was updated.
- `make lint-ruff lint-mypy` (throwaway env): ruff passed; mypy no issues in 155 files. No `uv.lock` in the root.

## Review round 1 follow-up (2026-10-10)

- Full `packs/core/tests/skills/work-loop` suite on HEAD `18b113336`, Python 3.11 (CI's version): 2432 passed, 7 skipped, 70 subtests passed, 168.7s.
- `test_loop_engine.py::test_recover_engine_state_tmp_never_tracebacks_and_deletes_only_bad_content[deep-nesting]` passes on Python 3.11 and fails only on local Python 3.14.3. Neither `loop-engine.py` nor that test is in this branch's diff, so the failure is environment-specific and not caused by this change.
- The `bug-fix` and `work-loop` decision-bound behavior evals now accept an explicit evidence limit when no code is supplied, and refuse invented caller locations or module names.
