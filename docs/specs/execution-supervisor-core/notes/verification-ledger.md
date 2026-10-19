# Verification ledger: execution supervisor core

## Plan lock

- The owner approved the spec and plan on 2026-10-13. Their pre-execute reviews ran during shaping (PR #1551), so the engine run `e6f903a5-ab29-4437-b4c5-1e67486692c6` recorded `reviewers-clean`, `spec-approved`, `plan-approved`, `approve-plan`, `schedule`, and `plan-locked` on that basis on 2026-10-13. The spec then moved to `Implementing` and the plan to `Executing`.
- Project-knowledge capture at `spec-approved` and `plan-locked`: no reusable practice had accrued since the preceding gates, so nothing was admitted.

## AC-0029: merge-base suites pass unchanged (VI-4062)

- Merge-base with `main` when T1 started: `9662d3780458f9f475505a0bcc0fde6af930c63f`.
- At that commit, under Python 3.11 (the CI version), `pytest packs/core/tests/skills/work-loop -n 8` gave 3021 passed, 7 skipped, 46.16 s. Under Python 3.14, one merge-base test fails on its own (`test_loop_engine.py::test_recover_engine_state_tmp_never_tracebacks_and_deletes_only_bad_content[deep-nesting]`), so every gate here runs on 3.11.
- `git diff 9662d3780 HEAD -- <every work-loop test file present at the merge-base>` is empty except for `test_process_safety.py` (next item) and `test_loop_cohort_schedule.py` (see the AC-0029 waiver under Departures). `loop-engine.py` is unchanged. `loop-cohort.py` changes only by re-binding the plan grammar from `_loop_guards.py`, with no change in behaviour. Both were checked once here instead of as standing tests, because the cutover spec deletes both engine scripts and later work edits those suites legitimately.
- One merge-base test file changed, without changing what it asserts. `test_process_safety.py::TestRedactionAtTheCapAndAtScale::test_redaction_cost_stays_linear` now names its five cases by their labels (`ids=`). Its megabyte-sized parameters had produced test IDs that Windows cannot hold in `PYTEST_CURRENT_TEST`, which broke the new Windows evidence step (see the attempt-security ledger). Its inputs and assertions are byte-identical, and it passes on POSIX before and after. The owner accepted this edit against AC-0029 and attempt-security AC-0025 on 2026-10-14.
- The full work-loop suite on the final tree is recorded under "Final gates".

## Departures from the plan text

These change no accepted criterion except where an entry names the owner's waiver.

- **The plan parser moved to `_loop_guards.py`, not into `_supervisor_projector.py` (plan Approach and T2 `Touches:`).** The task-section walk, the engine's `Depends on:` line reader (`section_depends_field`), the `Depends on:` value parse, and their patterns now live once in the guard layer. `loop-cohort.py` re-binds them at the same names. The projector reads the walk and the value parse through its sibling loader, but finds the `Depends on:` line with its own bullet-tolerant, case-insensitive field reader. The engine reads only an unbulleted, exact-case line, so on a bulleted plan the engine sees no dependency where the supervisor does. That split predates the move. Merging the two lookups would change either the engine, which stays unchanged, or the supervisor's reading of this repository's bulleted plans, so it is left to a separate change. The guard layer was chosen because `loop-cohort.py` already loads it with a one-line refusal on failure, the projector already depends on it, and the cutover keeps it. The grammar names stay out of `__all__`, which `test_loop_guards.py::test_all_is_pinned_to_the_declared_surface` pins. They sit above the completeness marker, so `loop-cohort.py`'s loader, which checks the marker, refuses a file truncated before them. The projector's loader does not check the marker; there a truncated file fails as the supervisor's `internal-error` refusal.
- **AC-0029 waiver for one merge-base test (owner, 2026-10-19).** `test_loop_cohort_schedule.py::test_boundary_walk_has_exactly_one_owner` read only `loop-cohort.py`. It now reads `loop-cohort.py`, `_loop_guards.py`, and `_supervisor_projector.py`, and requires the heading walk (`TASK_HEADING_RE.finditer`) and the engine's `Depends on:` lookup (`DEPENDS_LINE_RE.search`) to appear exactly once, in `_loop_guards.py`. It fails when a second walk is added to either of the other two files. The owner waived AC-0029 for this test and for two others that pin the parser. Those two, `::test_detect_unknown_deps_has_exactly_one_call_site` and `test_loop_guards.py::test_a_lock_holding_verb_refuses_an_unloadable_parser_without_writing[schedule]`, pass unchanged.
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

Code head `4d7142d8c` (rebased on `main` at `071067bab`, Core 3.1.9). Commits after it change only `docs/specs/`.

- **Local, Python 3.11:** `make lint-ruff lint-mypy` clean. `tools/lint-pack-test-boundary.py` passes. `tools/changelog.py validate` passes.
  - Full work-loop suite plus `tests/roster/test_execution_supervisor_records.py`, with `WORK_SUPERVISOR_INTEGRATION=1`: 3341 passed, 20 skipped, 1071 s.
  - `tests/roster`: 2147 passed, 7 skipped.
  - The three parser-pinning tests under the AC-0029 waiver passed: `test_detect_unknown_deps_has_exactly_one_call_site`, the rewritten `test_boundary_walk_has_exactly_one_owner`, and both cases of `test_a_lock_holding_verb_refuses_an_unloadable_parser_without_writing`.
- **PR checks on `4d7142d8c`:** all pass, one skipped by its path filter.
  - `Gate A-supervisor` (run 39279070392): 265 passed, 249 s.
  - `Gate A-packs` (Ubuntu) job: 7 min 26 s against its 10-minute limit.
  - `Gate B`'s first attempt ran every step to success, then the runner marked the job cancelled. It was rerun.
  - Windows (run 39279070391): the Job Object suite gave 13 passed, 27 s. The evidence-only POSIX suite gave 3 failed, 86 passed, 21 skipped, 3.3 s; the attempt-security ledger explains the three failures.
- **Dispatch-only suites on `4d7142d8c`:** `test-roster.yml` (run 39282368544) succeeded, 2147 passed, 7 skipped. `test-corpus.yml` (run 39282379253) succeeded on every shard.
- **Mutation checks for review repairs.** Each test below failed with its repair removed and passed with it in place:
  - the shared red-proof budget, against a per-stub budget;
  - the `gates-failed` route;
  - the `terminal_tree` finish key, against matching by HEAD after a pruned rebase;
  - the AC-0031 refusal of an effect result over a changed spec directory;
  - the advisory event-log guard, for an over-bound log and for an unwritable log.
  - the single plan-grammar owner, against a second heading walk added to `loop-cohort.py` or to `_supervisor_projector.py`.

## Review

Seven post-gates rounds ran. Rounds 1 and 2 ran before the engine entered review; rounds 3 to 7 ran in `CODE-REVIEW`, using 4 of 5 review retries. In round 7, `adversarial-reviewer` and `quality-engineer` returned clean, and `security-reviewer` was clean after its `Not checked` footer was adjudicated. One Nit stays deferred: effect results check protected paths before checking that the result matches the current request, so a stale effect result over a dirty spec directory gets `protected-path-changed` instead of `not-current-attempt`. Nothing is written in either case.

## Environment note

On this macOS host, git is very slow in repositories under the default pytest temporary root (`/private/var/folders/...`), and in parallel runs. Local runs therefore use `--basetemp` under `/tmp` and run serially.
