# Verification ledger: execution supervisor core

## Plan lock

- The owner approved the spec and plan on 2026-10-13. Their pre-execute reviews ran during shaping (PR #1551), so the engine run `e6f903a5-ab29-4437-b4c5-1e67486692c6` recorded `reviewers-clean`, `spec-approved`, `plan-approved`, `approve-plan`, `schedule`, and `plan-locked` on that basis on 2026-10-13. The spec then moved to `Implementing` and the plan to `Executing`.
- Project-knowledge capture at `spec-approved` and `plan-locked`: no reusable practice had accrued since the preceding gates, so nothing was admitted.

## AC-0029: merge-base suites pass unchanged (VI-4062)

- Merge-base with `main` when T1 started: `9662d3780458f9f475505a0bcc0fde6af930c63f`.
- At that commit, under Python 3.11 (the CI version), `pytest packs/core/tests/skills/work-loop -n 8` gave 3021 passed, 7 skipped, 46.16 s. Under Python 3.14, one merge-base test fails on its own (`test_loop_engine.py::test_recover_engine_state_tmp_never_tracebacks_and_deletes_only_bad_content[deep-nesting]`), so every gate here runs on 3.11.
- `git diff 9662d3780 HEAD -- <every work-loop test file present at the merge-base>` is empty except for `test_process_safety.py` (next item), and the diff of `loop-engine.py` and `loop-cohort.py` is empty. Both were checked once here instead of as standing tests, because the cutover spec deletes both engine scripts and later work edits those suites legitimately.
- One merge-base test file changed, without changing what it asserts. `test_process_safety.py::TestRedactionAtTheCapAndAtScale::test_redaction_cost_stays_linear` now names its five cases by their labels (`ids=`). Its megabyte-sized parameters had produced test IDs that Windows cannot hold in `PYTEST_CURRENT_TEST`, which broke the new Windows evidence step (see the attempt-security ledger). Its inputs and assertions are byte-identical, and it passes on POSIX before and after. The owner accepted this edit against AC-0029 and attempt-security AC-0025 on 2026-10-14.
- The full work-loop suite on the final tree is recorded under "Final gates".

## Departures from the plan text

These change no accepted criterion. The first one contradicts the sealed plan's text, so it goes to the owner as a plan amendment rather than an edit here.

- **The plan parser stayed in `loop-cohort.py` (plan Approach and T2 `Touches:`).** Two merge-base tests pin the parser's location inside that file's source: `test_loop_cohort_schedule.py::test_detect_unknown_deps_has_exactly_one_call_site` and `::test_boundary_walk_has_exactly_one_owner`. A third, `test_loop_guards.py::test_a_lock_holding_verb_refuses_an_unloadable_parser_without_writing[schedule]`, loads `loop-cohort.py` with only `_loop_guards.py` beside it. Moving the parser turned all three red, which AC-0029 forbids. `_supervisor_projector.py` carries its own task-section walk and `Depends on:` reader; the duplicate ends when the cutover removes `loop-cohort.py`.
- **Finish-effect key.** "The HEAD commit when terminal was first reached for that tree" is the HEAD recorded in the first finish intent whose product tree (the tree without the spec directory) equals the current one. Each finish intent records that tree digest as `terminal_tree` (`effect-resolution.v1`), so the match reads no old commit: a rebase that keeps the tree reuses the key even after the old HEAD is pruned. New upstream content is a new tree, so its finish effect is a new operation.
- **Query outcomes that need a decision are evidence.** When the effect source answers `unknowable`, or `absent` at the dispatch cap or under a claimed or confirmed decision, the supervisor commits that answer as an `evidence` step. `next` then re-derives the `human-decision` request after any crash, so the decision never depends on the advisory journal.
- **A default review policy.** `supervisor-policy.json` carries one mandatory `adversarial-reviewer` role so the readiness check can call the shared review readiness. The review-gate spec replaces it with `review-rules.json`.
- **The approvals line.** Each line holds `run_id`, `sequence`, `base`, `code_trust`, `terminal_intent`, `authority_ref`, `review_authority_ref`, the `envelope` record, and the `approval` and `initial_plan_review` records. The two records keep their canonical schemas; their ids and timestamps are set deterministically from the run and sequence so crash variants compare equal.
- **Stub fences in a CRLF plan, or with a blank line before the closing fence, are refused.** That keeps `tdd-stubs.md`'s byte-identity rule exact.
- **Integration suites run in their own CI lane.** The crash corpus, effects, step-loop, TDD, readiness, isolated-run, admission, and commit suites drive git-backed runs. They skip in the 10-minute pack lane, naming the `Gate A-supervisor` lane in `catalogue-tooling-ci-gates.yml`, which runs them with `WORK_SUPERVISOR_INTEGRATION=1`.
- **A failed gate run that names no failing criterion.** A lint or typecheck failure maps to no acceptance criterion. `report` records it as one `gate` receipt against `run:gates`, and readiness then asks the owner for a `gates-failed` decision (replan repair work) instead of re-issuing `run-gates`. The receipt is bound to the acceptance fingerprint, so a repaired product starts clean.
- **A killed supervisor's run lock waits out its stale window.** `_statelock` reclaims a lock by age alone, and the run lock's stale window (`run_lock_stale_seconds`, 2400 s) must exceed the red-proof budget. So after a real kill (SIGKILL, OOM) every verb answers `run-locked` for up to 40 minutes, or until the owner removes the lock file as the refusal says. This is an accepted cost: recovery still needs no decision, and a pid-liveness reclaim would add a PID-reuse risk and is not portable to Windows. The crash corpus raises its kill in-process, which releases the lock, so it does not model this stall.
- **Effect records do not pass through `_effect_broker.py` (plan T7 `Touches:`).** The broker performs an outward effect for a contained child process. The supervisor performs no outward effect: it commits the intent, claim, dispatch, and receipt lines for effects the controller performs. So there is no effect for the broker to grant or audit, and that control belongs with whoever performs the effect. The owner accepted this departure on 2026-10-14.
- **VI-4022 follows AC-0012: a `spec-plan` run makes two commits.** The plan's VI-4022 text says one commit touching only `delivery/`. AC-0012 and the plan's Interfaces table require two, `approval` then `terminal`, both touching only `delivery/`, and the test asserts two.
- **One new advisory lint warning.** `agentbundle catalogue lint` reports `supervisor-policy.json` as a loose file at the skill root (CAT-S004, warn). The plan's Data table names that path.

## Construction tests

Every acceptance criterion maps to at least one plan test ID (VI-4010 to VI-4062, VI-4901, VI-4902), and each ID is present in `packs/core/tests/skills/work-loop/` or `tests/roster/`. Their results are under "Final gates".

## Final gates

Code head `8dfc62782` (rebased on `main` at `cf919e2b3`, Core 3.1.9). Commits after it change only `docs/specs/`.

- **Local, Python 3.11:** `make lint-ruff lint-mypy` clean; `tools/lint-pack-test-boundary.py` passes; `tools/changelog.py validate` passes. The full work-loop suite plus `tests/roster/test_execution_supervisor_records.py`, with `WORK_SUPERVISOR_INTEGRATION=1`: 3341 passed, 20 skipped, 1024 s.
- **PR checks on `8dfc62782`:** all 38 pass, one skipped by its path filter.
  - `Gate A-supervisor` (run 39258450742): 265 passed, 253 s.
  - `Gate A-packs` (Ubuntu) job: 7 min 39 s against its 10-minute limit.
  - Windows (run 39258450641): the Job Object suite gave 13 passed, 28 s. The evidence-only POSIX suite gave 3 failed, 86 passed, 21 skipped, 4.5 s; the attempt-security ledger explains the three failures.
- **Dispatch-only suites on `8dfc62782`:** `test-roster.yml` (run 39261754362) succeeded, 2147 passed, 7 skipped. `test-corpus.yml` (run 39261766561) succeeded on every shard.
- **Mutation checks for review repairs.** Each test below failed with its repair removed and passed with it in place:
  - the shared red-proof budget, against a per-stub budget;
  - the `gates-failed` route;
  - the `terminal_tree` finish key, against matching by HEAD after a pruned rebase;
  - the AC-0031 refusal of an effect result over a changed spec directory;
  - the advisory event-log guard, for an over-bound log and for an unwritable log.

## Review

Seven post-gates rounds ran. Rounds 1 and 2 ran before the engine entered review; rounds 3 to 7 ran in `CODE-REVIEW`, using 4 of 5 review retries. In round 7, `adversarial-reviewer` and `quality-engineer` returned clean, and `security-reviewer` was clean after its `Not checked` footer was adjudicated. One Nit stays deferred: effect results check protected paths before checking that the result matches the current request, so a stale effect result over a dirty spec directory gets `protected-path-changed` instead of `not-current-attempt`. Nothing is written in either case.

## Environment note

On this macOS host, git is very slow in repositories under the default pytest temporary root (`/private/var/folders/...`), and in parallel runs. Local runs therefore use `--basetemp` under `/tmp` and run serially.
