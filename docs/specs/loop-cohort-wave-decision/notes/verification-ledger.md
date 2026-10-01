# Verification ledger: loop-cohort wave decision

## T1 verification

- Named wave-decision selection: `23 passed, 89 deselected in 35.76s`.
- Full touched suite: `112 passed in 125.21s`.
- Ruff gate: `All checks passed!`.
- MyPy gate: `Success: no issues found in 149 source files`.
- The T2 mutation series below begins and ends with the same production-source
  digest, preserving the verified T1 implementation bytes.

## T2 mutation proof

Date: 2026-09-29

Execution root: `<repository-root>`

Source under mutation: `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`

Source digest before mutation series: `b59c74736a9bfb2cc44b532ddfab7f896bdc6482892087db15e908a14d8e32e8`

Source digest after mutation series: `b59c74736a9bfb2cc44b532ddfab7f896bdc6482892087db15e908a14d8e32e8`

Baseline command:

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py -q
```

Observed baseline: `112 passed in 80.69s (0:01:20)`.

### Mutants

| # | Invariant | Exact mutation | Red command | Observed failure | Restoration green |
| --- | --- | --- | --- | --- | --- |
| 1 | Pre-index state-shape guards reject malformed state before later checks. | Replaced the `current_wave_index` malformed-state return with `wave_index = 0`. | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_json_refusals_cover_closed_vocabulary -q` | Failed: expected `state-malformed`, observed `plan-missing` for the malformed fixture. | Same command: `1 passed in 13.85s`. |
| 2 | Task IDs must match the closed task-ID grammar before verdict construction. | Removed `_TASK_ID_RE.fullmatch(task_id) is not None` from `_valid_wave_task_id`. | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_state_malformed_folds_task_id_and_width_limits -q` | Failed: invalid `BAD` task ID returned exit `0` instead of refusal exit `1`. | Same command: `1 passed in 3.37s`. |
| 3 | The unfinished wave bound refuses 65 tasks before pair construction. | Changed `len(wave) > MAX_WAVE_DECISION_TASKS` to `len(wave) > MAX_WAVE_DECISION_TASKS + 1`. | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_state_malformed_folds_task_id_and_width_limits -q` | Failed: 65-task fixture returned exit `0` instead of `state-malformed`. | Same command: `1 passed in 3.35s`. |
| 4 | Completed tasks are subtracted before deciding the selected wave. | Replaced the completed-task filtered list with `wave = list(waves[wave_index])`. | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_wave_argument_and_completed_subtraction -q` | Failed: default selected wave was `['T3', 'T4']` instead of `['T4']`. | Same command: `1 passed in 2.48s`. |
| 5 | Verdict envelopes carry `admission_pending: true`. | Changed payload field `"admission_pending": True` to `False`. | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_json_reports_scheduled_wave -q` | Failed schema validation because `admission_pending` must be `true`. | Same command: `1 passed in 1.84s`. |
| 6 | The wave-decision handler stays read-only and does not reach writer/gate paths. | Inserted a temporary `write_state_atomic` sentinel inside `cmd_wave_decision`. | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_does_not_touch_dispatch_gate_or_write_paths -q` | Failed source-shape assertion: `write_state_atomic` appeared in `cmd_wave_decision`. | Same command: `1 passed in 0.89s`. |
| 7 | The overlap walk short-circuits on the first admitted peer. | Changed the two `if overlap_reason is not None: break` statements in the overlap walk to `continue`. | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_overlap_short_circuits_on_first_admitted_peer -q` | Failed: reason changed from peer `T1` with `src/a/*` to peer `T2` with `src/b/*`. | Same command: `1 passed in 1.84s`. |
| 8 | Pair rows carry relation only, with no task disposition. | Added `"disposition": "parallel-capable"` to each pair row. | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_pairs_match_combination_formula -q` | Failed for widths 2-5: schema rejected the added pair-level `disposition`; width 1 still passed because it emits no pair row. | Same command: `5 passed in 3.83s`. |

### Notes

- A preliminary overlap mutation that changed only the outer admitted-peer break still passed `test_wave_decision_overlap_short_circuits_on_first_admitted_peer`; it was not counted as proof because the test did not fail under that weaker mutation.
- No `git checkout`, `git reset`, or `git stash` was used. Each source mutation and restoration was done by editing the source.

## T3 verification

Date: 2026-09-29

Execution root: `<repository-root>`

Source under mutation: `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`

Source digest before T3 mutation: `680518c2670818e79aa6d232966e4eda2fe0e6cab951c61a80bdd4ad58b2b548`

Source digest after T3 mutation restoration: `680518c2670818e79aa6d232966e4eda2fe0e6cab951c61a80bdd4ad58b2b548`

TDD red command:

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_json_refusal_detail_is_public_safe -q
```

Observed red: failed because JSON `detail` echoed the raw repository-confinement diagnostic, including the caller-controlled `DO-NOT-ECHO` path marker, instead of `cohort state could not be read`.

Historical targeted green command (the final selector later moved to the
repository-owned roster test and this exact command is superseded):

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_json_refusal_detail_is_public_safe packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_json_refusals_cover_closed_vocabulary packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_state_malformed_folds_task_id_and_width_limits packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_path_confinement_folds_escape_to_state_unreadable packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_schema_rejects_negative_contract_mutants -q
```

Observed targeted green: `5 passed in 15.38s`.

Current schema-mutant coverage lives in the CI-owned roster selector
`tests/roster/test_loop_cohort_wave_decision_contract.py::test_wave_decision_schema_rejects_forbidden_contract_mutants`;
repository rules prohibit running `tests/roster/` locally. The final pack-suite
results below supersede the four remaining pack-local selectors.

### Public-detail mutation proof

| Invariant | Exact mutation | Red command | Observed failure | Restoration green |
| --- | --- | --- | --- | --- |
| JSON refusal detail is fixed and public-safe; raw diagnostics stay on the human stderr path. | Replaced `_emit_wave_refusal`'s JSON detail value `WAVE_DECISION_REFUSAL_DETAILS[code]` with `_diag(detail)`. | `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py::test_wave_decision_json_refusal_detail_is_public_safe -q` | Failed: expected fixed `cohort state could not be read`, observed raw repository-confinement diagnostic containing the `DO-NOT-ECHO` path marker. | Same command: `1 passed in 1.07s`; source digest restored to `680518c2670818e79aa6d232966e4eda2fe0e6cab951c61a80bdd4ad58b2b548`. |

No `git checkout`, `git reset`, or `git stash` was used. The mutant and restoration were done by editing the source.

## T4 verification

Date: 2026-09-29

Execution root: `<repository-root>`

### Release and projection checks

- Version equality command: `env PYTHONDONTWRITEBYTECODE=1 python3 -c '...'`
- Observed equality before rebasing onto current `origin/main`: `{'pack': '2.28.0', 'plugin': '2.28.0', 'seed_changelog': '2.28.0', 'repo_changelog': '2.28.0'}`. Current repository-owned version policy subsequently selected `2.27.6` from the `2.27.5` base because the new verb remains inside the existing `skills/work-loop` primitive root.
- Eval JSON parse: `env PYTHONDONTWRITEBYTECODE=1 python3 -m json.tool packs/core/.apm/skills/work-loop/evals/evals.json` exited 0.
- Projection parity: `diff -qr packs/core/.apm/skills/work-loop .claude/skills/work-loop` exited 0.
- Projection parity: `diff -qr packs/core/.apm/skills/work-loop .agents/skills/work-loop` exited 0.
- Normal `env PYTHONDONTWRITEBYTECODE=1 make build-self` was attempted after the user's successful forced build; it refused before writing because the worktree is dirty: `self-host: working tree is dirty -- refusing to write. Pass --force to override (the dirty-tree check only).`

### Built projected-verb smoke

Fixture: `.pytest-tmp-wave-decision-smoke`, created only for this smoke and removed afterward.

Setup commands:

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 .claude/skills/work-loop/scripts/loop-cohort.py init .pytest-tmp-wave-decision-smoke --run-id 00000000-0000-4000-8000-000000002800
env PYTHONDONTWRITEBYTECODE=1 python3 .claude/skills/work-loop/scripts/loop-cohort.py approve-plan .pytest-tmp-wave-decision-smoke --expect-run-id 00000000-0000-4000-8000-000000002800
env PYTHONDONTWRITEBYTECODE=1 python3 .claude/skills/work-loop/scripts/loop-cohort.py schedule .pytest-tmp-wave-decision-smoke --expect-run-id 00000000-0000-4000-8000-000000002800
```

Observed smoke:

- Command: `.claude/skills/work-loop/scripts/loop-cohort.py wave-decision .pytest-tmp-wave-decision-smoke --json`
- Exit status: `0`.
- Stderr: empty.
- State SHA-256 before: `2c0d6df94bd7dbd2d78e4c407dde7ce9b1d25c5f1251e7c6b83530cabe23b1de`.
- State SHA-256 after: `2c0d6df94bd7dbd2d78e4c407dde7ce9b1d25c5f1251e7c6b83530cabe23b1de`.
- State unchanged: yes.
- Stdout JSON: `{"schema_version": 2, "payload_version": 1, "run_id": "00000000-0000-4000-8000-000000002800", "plan_hash": "39fe71f8b69530f8595fcea34ed2bc3753e429b24d311aeb9010fa243aa51bca", "wave_index": 0, "wave": ["T1", "T2"], "wave_disposition": "all-parallel-capable", "cohort": ["T1", "T2"], "serialized": [], "admission_pending": true, "tasks": [{"task_id": "T1", "touches": ["src/smoke/a.py"], "disposition": "parallel-capable", "reasons": []}, {"task_id": "T2", "touches": ["src/smoke/b.py"], "disposition": "parallel-capable", "reasons": []}], "pairs": [{"tasks": ["T1", "T2"], "touches_relation": "disjoint"}]}`.

### Targeted suite and local gate

- Targeted touched suite: `env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py -q`
- Observed result: `113 passed in 49.50s`.
- Local gate attempted: `make lint-ruff lint-mypy`.
- Observed policy refusal: the host rejected repository-provided `make` execution as untrusted code execution, both without and with escalation, and directed not to work around the denial without explicit approval.

### Controller completion checks

- Contract audit corrected the existing guard order so an absent or empty-list
  `schedule_waves` is `no-schedule`, while a present non-list value is
  `state-malformed`; the closed-refusal test now also exercises malformed
  `schedule_waves` and `completed_task_ids`.
- Named guard test: `1 passed in 11.31s`.
- Full touched suite after the correction: `113 passed in 53.25s`.
- Ruff gate: `All checks passed!`.
- MyPy gate: `Success: no issues found in 149 source files`.
- A final forced self-host attempt from the managed runtime again stopped on
  the protected generated `.claude/skills/assimilate-primitive/scripts`
  directory. No hand-edited projection was substituted; external sanctioned
  `FORCE=1 make build-self` remains the required regeneration step.
- The user ran the sanctioned external `FORCE=1 make build-self` after that
  correction. Final `diff -qr` checks passed for `.apm` against both `.agents`
  and `.claude`; the eval JSON parsed successfully.
- Final projected-verb smoke used run ID
  `00000000-0000-4000-8000-000000002801`: exit `0`, empty stderr,
  `all-parallel-capable`, `admission_pending: true`, one `disjoint` pair, and
  state SHA-256 `e3bae29491f504b6f21d66c7eb6221562138b0c117c5d98f1788938c615af1f5`
  both before and after.

### Post-review resource-bound repair

Source digest before mutation series: `bfaa1e48e7507e9922dde23b5e23d85746341229b6a554a50209c710b0e8eeab`.

Source digest after mutation series: `bfaa1e48e7507e9922dde23b5e23d85746341229b6a554a50209c710b0e8eeab`.

All five mutants and restorations used source edits only. No checkout, reset,
or stash command was used.

| Invariant | Exact mutation | Named red | Observed failure | Restoration green |
| --- | --- | --- | --- | --- |
| `run_id` must be a non-empty string before success construction. | Gated the `run_id` malformed-state branch behind `False`. | `test_wave_decision_json_refusals_cover_closed_vocabulary` | Failed: missing `run_id` produced `plan-missing` instead of `state-malformed`. | `1 passed in 20.85s`. |
| Selected unfinished task IDs must be unique. | Gated the duplicate-ID branch behind `False`. | `test_wave_decision_state_malformed_folds_task_id_and_width_limits` | Failed: duplicate `T1` IDs produced a success verdict instead of a refusal. | `1 passed in 5.15s`. |
| One task contributes at most 64 effective globs. | Changed the guard from `> limit` to `> limit + 1`. | `test_wave_decision_touches_per_task_limit_is_folded_to_plan_status_illegal` | Failed: the 65-glob fixture produced a success verdict. | `1 passed in 3.00s`. |
| One selected wave contributes at most 256 effective globs. | Changed the guard from `> limit` to `> limit + 1`. | `test_wave_decision_touches_per_wave_limit_is_folded_to_plan_status_illegal` | Failed: the 257-glob fixture produced a success verdict. | `1 passed in 3.26s`. |
| One effective glob contains at most 256 characters. | Changed the guard from `> limit` to `> limit + 1`. | `test_wave_decision_touch_glob_length_limit_is_folded_to_plan_status_illegal` | Failed: the 257-character fixture produced a success verdict. | `1 passed in 3.30s`. |

The admission walk now caches each task-pair relation for pair-row rendering.
The named construction test observed exactly `6 * 4 * 4 = 96` calls for four
tasks with four mutually disjoint globs each, rather than comparing each pair a
second time during rendering. Together with AC-0018, this makes the documented
32,256-comparison ceiling true for a 64-task wave.

### Final external gates and projection parity

- After the three Ruff findings in the touched pack test were corrected, the
  user reran `make lint-ruff` and reported completion without another error.
- `make lint-mypy` had already completed with `Success: no issues found in 149
  source files`.
- The user reran `python3 tools/test-lint-pack-test-boundary.py` to completion;
  the earlier `KeyboardInterrupt` was an interrupted attempt, not a failing
  assertion.
- The user ran `FORCE=1 PYTHONDONTWRITEBYTECODE=1 make build-self` to
  completion. Controller-side byte comparisons then confirmed the canonical
  `loop-cohort.py` is identical to both `.agents` and `.claude` projections;
  `git diff --check` also exited 0.

### Post-gates review round 2 repairs

Independent adversarial, quality, and security review produced five unique
sustained findings after adjudication; the duplicate read-only-state finding
was fingerprinted once. Two findings were refuted: V-004 does not require the
roster schema suite itself to invoke the live CLI, and the contract does not
require a distinct unreadable-plan fixture once the folded
`plan-status-illegal` code is exercised.

Repairs made:

- Boundary refusal fixtures now route through the state-byte comparison helper,
  including both JSON and human forms of every AC-0018 resource refusal.
- The live 64-task case asserts all 2,016 pair rows in
  `itertools.combinations` order.
- `check_schedule_current(..., include_snapshot=True)` returns the exact state
  and plan text whose status and hash it validated; `wave-decision` constructs
  success only from that snapshot.
- The superseded T3 selector is labeled historical and points to the current
  CI-owned roster coverage.
- Verification roots use `<repository-root>` rather than a local home path.

Verification:

- Repair-focused selectors: `6 passed in 9.27s`.
- Full touched pack suite: `118 passed in 66.32s`.
- Schedule-guard branch plus API/CLI golden parity selectors: `47 passed in
  29.17s`.

Same-snapshot mutation proof:

| Source | Mutation | Named red | Restoration green | Digest restored |
| --- | --- | --- | --- | --- |
| `loop-cohort.py` | Built the payload from the pre-check state instead of the validated snapshot state. | `test_wave_decision_uses_the_validated_schedule_snapshot` failed because `plan_hash` came from the earlier state. | `1 passed in 1.01s`. | `c4938d8664f4dc702bd07a80ab98096a170a9a6332ce7921cd0256d5a2483684` |
| `_loop_guards.py` | Suppressed the requested validated snapshot from the successful guard result. | `test_schedule_guard_returns_the_hash_checked_snapshot` failed because `result.data` was `None`. | `1 passed in 0.98s`. | `d1143bf6794a18117caca1c39d338b68965cf4ae062f428f63dd4b68ef5ce3ab` |

Both mutants and restorations were source edits. No checkout, reset, or stash
command was used.

Final repair gates were run externally after the restored source was projected:

- `FORCE=1 PYTHONDONTWRITEBYTECODE=1 make build-self` passed.
- `make lint-ruff` passed.
- `make lint-mypy` passed.
- `python3 tools/test-lint-pack-test-boundary.py` passed.
- Controller-side byte comparisons confirmed both `loop-cohort.py` and
  `_loop_guards.py` match their `.agents` and `.claude` projections; `git diff
  --check` exited 0.

### Post-gates review round 3 repairs

Adjudication sustained two new concerns and confirmed the security review
clean. The schedule guard now returns a closed `failure_kind` for state-read,
plan-missing, plan-status, and plan-hash failures. `wave-decision` maps that
field directly instead of rereading plan bytes to guess the refusal class. A
late state-read failure therefore remains `state-unreadable` on JSON stdout and
retains its raw diagnostic only on the human stderr path. The roster schema's
green verdict now gives T4 declared disjoint touches, so its cohort membership,
task disposition, reasons, and pair rows describe a producible CLI result.

Verification:

- Focused refusal, schedule-guard, and API/CLI parity selectors: `51 passed in
  43.71s`.
- Full touched wave-decision suite: `121 passed in 64.19s`.
- `tests/roster/` was not run locally; its named build-check step owns the
  schema fixture on CI.

Structured-refusal mutation proof:

| Source | Mutation | Named red | Restoration green | Digest restored |
| --- | --- | --- | --- | --- |
| `_loop_guards.py` | Classified a late missing state as `plan-status-illegal`. | `test_schedule_guard_classifies_state_read_failure` failed on the structured kind. | `1 passed in 0.90s`. | `dad24ec005e80dbc5c94aaa12440ab36ff1f43ddb7cf6df98480ae93f4dd1e7b` |
| `loop-cohort.py` | Mapped the structured `state-unreadable` kind to `plan-status-illegal`. | `test_wave_decision_late_state_read_refuses_state_unreadable` failed because JSON emitted the wrong refusal and fixed detail. | `2 passed in 1.09s`. | `18908c6c7d7326139dc46a2cfe93131c78e01177e08e291460a66e7932b21f2f` |

Both mutants and restorations were source edits. No checkout, reset, or stash
command was used.

Final round-3 gates were run externally after projection:

- `FORCE=1 PYTHONDONTWRITEBYTECODE=1 make build-self` passed.
- `make lint-ruff` passed.
- `make lint-mypy` passed.
- `python3 tools/test-lint-pack-test-boundary.py` passed.
- Controller-side byte comparisons confirmed both changed scripts match their
  `.agents` and `.claude` projections; `git diff --check` exited 0.

### Post-gates review round 4 portability repair

Adjudication sustained one portability finding, refuted the repeated proposal
to require the roster schema test itself to invoke the live CLI, and confirmed
security clean. The pack seed changelog and canonical work-loop eval now state
the populated-branch post-write gate and disabled concurrent execution directly
without naming catalogue-only ADRs. Repository-owned architecture and release
history retain their internal decision links.

The canonical eval JSON parsed successfully with `python3 -m json.tool`, and
`git diff --check` exited 0. No behavior code changed in this repair.

Final round-4 gates were run externally after projection:

- `FORCE=1 PYTHONDONTWRITEBYTECODE=1 make build-self` passed.
- `make lint-ruff` passed.
- `make lint-mypy` passed.
- `python3 tools/test-lint-pack-test-boundary.py` passed.
- Controller-side byte comparisons confirmed canonical eval parity with both
  generated projections; no internal ADR citation remains on the two repaired
  pack-owned surfaces, and `git diff --check` exited 0.

### Post-gates review round 5 repairs

Adjudication sustained three findings. The branch-freshness proposal was
refuted because the repository requires updating a behind branch before merge,
not before this pre-push review stage. The final standard repair round made
these changes:

- `wave-decision` folds `OSError` and `RuntimeError` from spec-path resolution
  into its fixed `state-unreadable` JSON refusal, alongside `ValueError`.
- The safety-separation test walks top-level local functions reachable from
  `cmd_wave_decision` and rejects forbidden gate, writer, worktree, and
  merge-tree calls anywhere on that path.
- `_DANGER_PATH_RE` now says at its declaration that it is shared by the
  post-write classifier and pre-dispatch screen, and that changes require both
  test surfaces to be reviewed.

Mutation proof:

| Invariant | Exact mutation | Named red | Observed failure | Restoration green |
| --- | --- | --- | --- | --- |
| Spec-path resolution failures remain inside the JSON refusal contract. | Restored the handler to catching only `ValueError`. | `test_wave_decision_resolution_failures_use_json_refusal` | Both cases failed: `OSError` and `RuntimeError` escaped from `_resolve_spec_dir` (`2 failed in 0.68s`). | `2 passed`. |
| No reachable `wave-decision` helper calls the post-write gate. | Added `dispatch_decision([], merge_tree_clean=True)` to `_build_wave_decision`. | `test_wave_decision_does_not_touch_dispatch_gate_or_write_paths` | The reachable-symbol disjointness assertion failed on `dispatch_decision` (`1 failed in 0.49s`). | `1 passed`. |

Both mutants and restorations were source edits. No checkout, reset, or stash
command was used. Direct Ruff checking of the changed canonical source and test
reported `All checks passed!` after restoration.

Final round-5 verification was run after `wave-complete` placed the engine in
`CODE-VERIFICATION`. The user reported passing `make lint-ruff`,
`make lint-mypy`, the full touched `test_loop_cohort_schedule.py` suite,
`tools/test-lint-pack-test-boundary.py`, and `tools/lint-ci-parity.py`, then
fired `gates-clean`. The forced self-host build completed before those gates;
controller-side comparisons confirmed canonical `loop-cohort.py` and
`supervisor-mode.md` parity with both generated projections, and `git diff
--check` exited 0.

### Post-gates review rounds 6 and 7

Round 6 quality review was directly clean. Security review was adjudicated
clean; its scanner, fuzzing, and alternate-platform limits were bounded review
limits rather than source findings. Adversarial adjudication sustained one
documentation concern: `docs/architecture/README.md` still described § 4 as
planned after the owning architecture page marked it implemented.

The five standard review retries were already consumed. The Owner approved one
retry-cap override limited to correcting that index. The repair now marks §§ 1,
2, and 4 implemented, leaves § 3 planned, describes the shipped read-only
`wave-decision` screen, and keeps ADR-0061 D5 deferred. A focused assertion
checked those three claims, `tools/test_documentation_entry_links.py` passed,
the local Ruff and MyPy gates passed, and the engine returned through
`gates-clean`. The authorized round-7 adversarial rerun returned the exact
`Clean — ready to commit.` sentinel after the first attempt was interrupted
without a report.

Tail triage counted 2,374 changed tracked lines before lifecycle-only spec and
plan edits. Canonical behavior and test changes remain below 2,000 lines; most
raw volume is the two generated adapter projections of the `.apm` source.
Review followed the plan's dependency-ordered T1–T4 boundaries and included
whole-spec adversarial, quality, and security passes.
