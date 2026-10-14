# Verification ledger: execution supervisor core

## Plan lock

- The owner approved the spec and plan on 2026-10-13. Their pre-execute reviews ran during shaping (PR #1551), so the engine run `e6f903a5-ab29-4437-b4c5-1e67486692c6` recorded `reviewers-clean`, `spec-approved`, `plan-approved`, `approve-plan`, `schedule`, and `plan-locked` on that basis on 2026-10-13. The spec then moved to `Implementing` and the plan to `Executing`.
- Project-knowledge capture at `spec-approved` and `plan-locked`: no reusable practice had accrued since the preceding gates, so nothing was admitted.

## AC-0029: merge-base suites pass unchanged (VI-4062)

- Merge-base with `main` when T1 started: `9662d3780458f9f475505a0bcc0fde6af930c63f`.
- At that commit, under Python 3.11 (the CI version), `pytest packs/core/tests/skills/work-loop -n 8` gave 3021 passed, 7 skipped, 46.16 s. Under Python 3.14, one merge-base test fails on its own (`test_loop_engine.py::test_recover_engine_state_tmp_never_tracebacks_and_deletes_only_bad_content[deep-nesting]`), so every gate here runs on 3.11.
- `git diff 9662d3780 HEAD -- <every work-loop test file present at the merge-base>` is empty, and so is the diff of `loop-engine.py` and `loop-cohort.py`. Both were checked once here instead of as standing tests, because the cutover spec deletes both engine scripts and later work edits those suites legitimately.
- The full work-loop suite on the final tree is recorded under "Final gates".

## Departures from the plan text

These change no accepted criterion. The first one contradicts the sealed plan's text, so it goes to the owner as a plan amendment rather than an edit here.

- **The plan parser stayed in `loop-cohort.py` (plan Approach and T2 `Touches:`).** Two merge-base tests pin the parser's location inside that file's source: `test_loop_cohort_schedule.py::test_detect_unknown_deps_has_exactly_one_call_site` and `::test_boundary_walk_has_exactly_one_owner`. A third, `test_loop_guards.py::test_a_lock_holding_verb_refuses_an_unloadable_parser_without_writing[schedule]`, loads `loop-cohort.py` with only `_loop_guards.py` beside it. Moving the parser turned all three red, which AC-0029 forbids. `_supervisor_projector.py` carries its own task-section walk and `Depends on:` reader; the duplicate ends when the cutover removes `loop-cohort.py`.
- **Finish-effect key.** "The HEAD commit when terminal was first reached for that tree" is the HEAD recorded in the first finish intent whose product tree (the tree without the spec directory) equals the current one. A rebase that keeps the tree reuses the key; new upstream content is a new tree, so its finish effect is a new operation. An intent whose recorded HEAD can no longer be read is skipped.
- **Query outcomes that need a decision are evidence.** When the effect source answers `unknowable`, or `absent` at the dispatch cap or under a claimed or confirmed decision, the supervisor commits that answer as an `evidence` step. `next` then re-derives the `human-decision` request after any crash, so the decision never depends on the advisory journal.
- **A default review policy.** `supervisor-policy.json` carries one mandatory `adversarial-reviewer` role so the readiness check can call the shared review readiness. The review-gate spec replaces it with `review-rules.json`.
- **The approvals line.** Each line holds `run_id`, `sequence`, `base`, `code_trust`, `terminal_intent`, `authority_ref`, `review_authority_ref`, the `envelope` record, and the `approval` and `initial_plan_review` records. The two records keep their canonical schemas; their ids and timestamps are set deterministically from the run and sequence so crash variants compare equal.
- **Stub fences in a CRLF plan, or with a blank line before the closing fence, are refused.** That keeps `tdd-stubs.md`'s byte-identity rule exact.
- **Integration suites run in their own CI lane.** The crash corpus, effects, step-loop, TDD, readiness, and isolated-run suites drive whole git-backed runs. They skip in the 10-minute pack lane, naming the `Gate A-supervisor` lane in `catalogue-tooling-ci-gates.yml`, which runs them with `WORK_SUPERVISOR_INTEGRATION=1`.
- **One new advisory lint warning.** `agentbundle catalogue lint` reports `supervisor-policy.json` as a loose file at the skill root (CAT-S004, warn). The plan's Data table names that path.

## Construction tests

Results are under "Final gates".

## Environment note

On this macOS host, git is very slow in repositories under the default pytest temporary root (`/private/var/folders/...`), and in parallel runs. Local runs therefore use `--basetemp` under `/tmp` and run serially.
