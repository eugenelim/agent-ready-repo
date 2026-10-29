# Verification ledger: execution supervisor cutover

Execution observations for the approved plan. This file is not hash-pinned; it
records how tasks are verified, not new obligations.

## T1: hook discovery uses a standard-library confinement check

The plan's Design names `list_confined_regular_files` for the hooks' run
discovery. The shipped hook runs in adopter repositories where `agentbundle`
may not be importable, so both hook copies use a standard-library check
instead. It refuses a link at `docs/`, `docs/specs/`, the spec directory,
`delivery/`, and `approvals.jsonl`. It requires a regular file, and it requires
the file's real path to stay inside the repository. AC-0017's property is
unchanged, and VI-7003 covers the symlinked-spec case.

## T1: the oversize threshold for a gate question is 4 KiB

AC-0015 refuses an oversized gate question. The bridge treats a question over
4 KiB of UTF-8 as oversized and shows only the fixed placeholder; the
`review-report` content-safety check then runs on what remains. `run.json`
itself is read with a 64 KiB bound. VI-7002 covers the oversized case.

## T1: identical back-to-back gates inside one poll

`run.json` carries no request id. The bridge treats a new `run_id` or a changed
question while a gate is pending as a new gate, and notifies. Two consecutive
gates with identical question text that resolve and reopen inside one 200 ms
poll stay indistinguishable; `workspace_status` still shows the open gate.

## Dispatch accounting

T2 and T3 carry a `human-directed` dispatch decline in wave 0: the owner
directed the first review unit to cover T1 only, because T2 waits on
`execution-supervisor-attempt-security`. Both tasks stay incomplete and get
fresh receipts when they start.

## Deferred review Nits

- T1 security review, Nit: when the hook skips a linked spec that holds
  `approvals.jsonl`, it reports "no delivery/approvals.jsonl" instead of naming
  the skipped spec. Status: deferred.
- T1 quality review, Nit: `test_instruction_shaped_question_is_framed_inert_in_field_and_notification` uses harmless text; the instruction case is the next test. Status: deferred.
- T1 quality review, Nit: nothing but the parametrized hook tests catches drift between `packs/core/.apm/hooks/pre-pr.py` and `tools/hooks/pre-pr.py`; `make build-self` regeneration is the other guard. Status: deferred.
- T1 quality review, Nit: the hook test's `at-cap` case is a label only; the terminal-at-cap exit code is proven by the work-loop supervisor readiness suite. Status: deferred.
- T1 adversarial review, Nit: an untracked root `uv.lock` written by a tool run stays out of the commit. Status: deferred.

## T1: the bridge's run signal is `run_active`

AC-0013's active signal is exposed as `run_active` in `workspace_status`,
because `workspace_status` already returns an `active` list of resumable specs
and a same-named field would overwrite it.

## T2: AC-0026 extends two delivery contracts additively

AC-0026's replan confirmation is a `human-decision` request and result, and
`contracts/delivery/execution-request.v1` and `execution-result.v1` set
`additionalProperties: false`. The request gains an optional `diff` string; the
result's decision enum gains `confirm-replan` and `decline-replan`, shaped like
`reselect-review` (a `selection_key`, no `finding_ids`). Every record that
validated before still validates, so the schemas stay v1. The owner, eugenelim,
approved amending the spec's `Contract:` line for this on 2026-10-29.

## T2: AC-0026 red proof

Command, before production code:
`WORK_SUPERVISOR_INTEGRATION=1 python -m pytest packs/core/tests/skills/work-loop/test_supervisor_tdd.py -q`
Result: 9 failed, 12 passed. The closure test failed because the refused stub
file stayed in the tree, and each recovery test failed with `attempt-residue`
on `docs/specs/calc/plan.md`, today's behaviour. The 12 passing cases are the
existing suite plus three regression guards that hold before and after.

## T2: the supervisor store is the trust root for the owed confirmation

The owed confirmation lives in `recovery.json` in the run store under the Git
directory. AC-0026 requires that deleting the journal, `run.json`, or
`security-events.jsonl` cannot clear it, and the code meets that. A writer that
can delete records in the Git-directory store itself could clear it, but that
store is the attempt-security trust root, and protecting it is outside this
spec. The security reviewer's AC-0026 pass recorded this as out of scope.

## Deferred review Nits (T2, AC-0026 slice)

- Quality, Nit: the `close_not_red` docstring says a retry repeats the steps, but a crash after discard needs the reissued `write-stub` redone. Status: deferred.
- Quality, Nit: when `close_not_red` is a no-op, the `stub-not-red` text still says the attempt closed. Status: deferred.
- Quality, Nit: the authority and digest refusal test asserts only the exit code. Status: deferred.
- Quality, Nit: a comment in the local-state wipe test sits above the wrong line. Status: deferred.
- Quality, Nit: `exempt=True` makes `_refuse_protected_change` read as a skipped check. Status: deferred.
- Quality, Nit: a leftover at a path that is a symlink in HEAD never clears, because `_at_head` matches only regular files or absence. It fails closed. Status: deferred.
- Security, Not checked: two older `unexpected-change` refusals in `_supervisor_loop.py` still join paths without `_named`; they predate this change. Status: deferred.

## T2: AC-0004 admits the light-mode edits AC-0002 forces

AC-0002 removes every reviewer role and condition pairing from skill files
other than `review-rules.json` and `references/light-mode.md`. SKILL.md's
reviewer roster table and its pre-EXECUTE gate table's Reviewer column are
light-mode text, so AC-0004's swap-only rule could not hold alongside AC-0002.
The owner, eugenelim, approved amending AC-0004 on 2026-10-29 to admit edits
that AC-0002 forces: the roster table becomes a pointer to `review-rules.json`,
the gate table drops its Reviewer column, and a table row or list item that
pairs a role with its condition or boundary text is reworded without the role. Every other light-mode line stays swap-only.

## T2: AC-0007 admits a closed set of pinned sites, and T3 owns workspace.toml and the briefs

The owner, eugenelim, approved this amendment on 2026-10-29.

- Three kinds of site must keep a retired name, and the switch had spelled
  them as split strings so the search would miss them. They are: a value
  hashed into every recorded approval digest, so its bytes cannot change; the
  containment deny-list entry that stops a worker planting `engine-state.json`
  for a 3.x rollback to read; and tests that guard the names' absence.
  AC-0007 now admits these as plain literals, but only at the (path, term)
  sites `tests/roster/test_retired_name_pinned_sites.py` lists, so any new mention still fails. That
  test is itself outside the search, because it must spell the terms.
- `workspace.toml` and `docs/product/briefs/` move from T2 to T3. The separate
  T3 session owns them, and the cutover closes only when T3 has merged, so
  AC-0007 is met at spec close.

## T2: every retired or rewritten test, and the guard that survives

Retired tests died with the code they pinned. Where a property outlives the
code, the surviving guard is named; where one does not, the row says so.

| Retired test | Why | Surviving guard |
| --- | --- | --- |
| `pack/test_repair_round_procedure.py` | Pinned the `wave reopen` before a repair transition; the transitions are gone. | A failed gate and a supported finding reissue the task through `next`: `test_supervisor_step_loop.py`, `test_supervisor_review_closure.py`, `test_supervisor_review_gate.py`. |
| `pack/test_review_depth_and_verdict_contract.py` | One of 18 tests read the removed engine reference. | Restored with its 17 other tests; the verdict test now reads `SKILL.md`, `review-verdict-record.md`, `finding-adjudication.md`, and `supervisor.md`. |
| `work-loop/test_compat_facade.py` | The facade is deleted. | Verdicts from evidence: `test_supervisor_readiness.py`, `test_evidence_store.py`; confined writes: `test_supervisor_commit.py`. |
| `work-loop/test_consumer_map_disposable.py` | Its projector is deleted. | `test_supervisor_consumer_map.py` (plan-side deletion or rebuild leaves evidence and readiness; the same map in the spec's scope text is refused). |
| `work-loop/test_loop_cohort.py`, `test_loop_cohort_cli.py` | Cohort state, identity, approval, wave, retry, and review mutations. | Identity and approval: `test_supervisor_admission.py`; retry count and cap: `test_supervisor_step_loop.py`, `test_supervisor_readiness.py`; review: `test_supervisor_review*.py`. |
| `work-loop/test_loop_cohort_max_iter_single_source.py` | The cap lived in the removed state template. | The cap is read from `supervisor-policy.json`; `test_supervisor_readiness.py` and `test_supervisor_crash_corpus.py` drive to it. |
| `work-loop/test_loop_cohort_schedule.py` | Scheduler parsing, order, and cycle detection. | `test_supervisor_step_loop.py::test_tasks_are_issued_in_dependency_order_not_plan_order` and `::test_a_dependency_cycle_is_refused_and_commits_nothing` (added in this batch, because `dependency-cycle` had no test), plus `test_supervisor_projector.py`. |
| `work-loop/test_loop_concurrency.py` | State-lock races in the cohort and engine. | `test_statelock.py` (the lock module is kept); the run lock in `test_supervisor_commit.py`. |
| `work-loop/test_loop_engine.py` | FSM transitions and session state. | Derived-state walks in `test_supervisor_step_loop.py` and `test_supervisor_crash_corpus.py`; the installed-skill run in `tests/roster/test_supervisor_installed_skill_run.py`. |
| `work-loop/test_loop_engine_events_jsonl.py` | Engine outbox protocol. | `tests/roster/test_loop_run_event_contract.py` over `.loop-run/events.jsonl`; event projection in `test_supervisor_step_loop.py`. |
| `work-loop/test_loop_engine_no_child_python.py` | One interpreter per transition. | None as such: the supervisor is one process, and its only child process is Git through the hardened helper (`test_supervisor_git.py`). |
| `work-loop/test_loop_guards_parity.py` | Guard API against the removed guard CLI. | The API half stays in `test_loop_guards.py`; the CLI half has nothing left to compare. |
| `work-loop/test_plan_records_its_approval.py` | The plan template's Changelog and the work-loop sequence each carried half of an approval. | `new-spec/test_plan_changelog_approval_split.py` (added in this batch) pins the human half in the template and the machine half in `delivery/approvals.jsonl`. |
| `work-loop/test_review_assessment.py`, `test_review_compat.py` | The assessment module and compat adapter are deleted. | `test_review_disposition.py`, `test_review_bridge.py`, `test_supervisor_review_closure.py`; the review-boundary policy checks are restored in `test_review_boundary_policy.py`. |
| `work-loop/test_review_boundary_policy.py` | Two of its checks drove the removed engine. | Restored in this batch: the role-literal check, the forbidden-field check, the closed-shape refusal `denied-review-policy-unknown-field`, and the mutation controls. The role-count pin for the skill text is not restored: the roster now lives in `review-rules.json`, which `test_review_rules_roster.py` pins. |
| `work-loop/test_review_record_idempotency.py`, `test_review_record_shipped_statements.py`, `tests/roster/test_review_record_flagless_baseline.py` | `review record --operation-id` against cohort state, and its flagless baseline. | `review-artifact.py record --run-id` is covered in `test_review_relocation.py`; the operation key is covered in `test_review_persistence.py` and `test_supervisor_effects.py`. |
| `work-loop/test_schema_version_alignment.py` | Alignment across the engine's loaders. | `tests/roster/test_delivery_contract_bundle.py` pins the schema copies. |
| `work-loop/test_wave_accounting_walk.py` | Wave accounting over cohort state. | None: waves are gone, and no state is left to account. |
| `tests/roster/test_loop_cohort_wave_decision_contract.py` | Its schema is deleted. | `tests/roster/test_retired_name_pinned_sites.py::test_the_removed_files_are_absent_from_the_source_and_its_generated_copies`. |
| `tests/roster/test_repair_round_predicate_parity.py` | Coupled a spec contract to a removed predicate. | None: the predicate is gone with the engine edge it guarded. |
| `fixtures/golden_cli_streams.json`, `fixtures/review-relocation/golden.json` | Recorded output of removed verbs. | Retired with their tests. |

Rewritten tests keep their property and change what they read. The large cuts
are named with what stayed.

| Rewritten test | What changed | What stayed |
| --- | --- | --- |
| `work-loop/test_contract_amendment_wave4.py` | 50 engine-transition cases for contract amendment removed. | One case; amendment is now an owner re-approval through `start`, covered by `test_supervisor_step_loop.py::test_amendment_and_second_start_keep_run_facts`. |
| `work-loop/test_loop_guards.py` | 70 tests of removed guards and the guard CLI removed. | 28 tests of the kept guard API and the canonicalizer; `test_golden_fixtures.py` pins the digests. |
| `work-loop/test_subject_projection.py` | 25 cases of the file-based subject projector removed. | 4 cases of the kept projection; the supervisor's own subject checks are in `test_supervisor_readiness.py`. |
| `work-loop/test_delivery_knowledge_isolation.py` | 10 shadow-log isolation cases removed. | 3 cases; the feed now reads committed evidence, pinned by `test_delivery_fact_feed.py` and the new `test_delivery_fact_feed_head.py`. |
| `work-loop/test_golden_fixtures.py` | 7 CLI-stream cases removed. | 7 digest cases. |
| `pack/test_finding_adjudication_contract.py` | Text pins moved from the removed engine reference to `supervisor.md`. | All 41 tests. |
| `work-loop/review_relocation_support.py`, `test_review_relocation.py` | Cohort-state fixtures removed. | The `--run-id` relocation cases. |
| `work-loop/test_work_loop_profile.py`, `test_reference_routing.py`, `test_step0_eval_contract.py`, `test_review_rules_roster.py`, `test_sequential_implementer_dispatch.py`, `test_decide_cause_depth.py`, `test_lifecycle_routing_and_plan_digest.py`, `test_fingerprint_width.py`, `test_reviewer_lens_ownership.py`, `test_project_knowledge_handoff.py`, `test_containment_broker.py`, `test_statelock.py`, `test_acceptance.py` | Text pins and module paths repointed to the supervisor files. | Every property they pinned. |
| `work-loop/test_supervisor_admission.py`, `test_supervisor_dark_launch.py`, `test_supervisor_review_closure.py`, `delivery_feed_support.py`, `golden_support.py`, `spawn_support.py` | Fixtures read committed evidence and the supervisor's own records. | Every property they pinned. |
| `new-spec/test_plan_working_material.py`, `pack/test_ride_along_admission_test.py`, `pack/test_spec_authority_scoping.py`, `project-knowledge/candidate_support.py`, `test_candidate_mode.py` | Repointed. | Every property they pinned. |
| `tests/roster/test_tdd_stub_lifecycle_contract.py`, `test_core_pre_pr_hook.py`, `test_t9a_clean_env_fence.py`, `test_verification_ledger_contract.py`, `test_work_loop_root_validation.py`, `test_loop_telemetry_disclosure_contract.py`, `test_sequential_implementer_dispatch_contract.py`, `test_delivery_subject_parity.py`, `test_loop_run_event_contract.py`, `test_policy_family_selector.py`, `test_security_checklists_okf_projection.py`, `test_okf_catalogue_discovery.py`, `test_wave4_durable_outputs_and_release.py`, `test_two_sided_prune_closure_invariant.py` | Repointed to the supervisor; the prune invariant now counts a removed `.apm` file as a removal. | Every property they pinned. |
| `packages/agentbundle/tests/unit/test_workspace_mcp_supervisor_run.py`, `test_workspace_mcp_events_poller.py`, `test_catalogue_skill_spec_lint.py`, `tools/test_build_gate_chain.py`, `frontend-engineering/.../test_rendered_page_shipped_content_limits.py`, `test_rendered_page_reviewer_sight.py` | Repointed; the reviewer-sight pin reads the roster entry in `review-rules.json`. | Every property they pinned. |

## T2: kept light-mode edits that are not command swaps

AC-0004 admits three kinds: a command swap, a qualifier that limits a clause
shared with full-mode code review to light mode and pre-approval, and an edit
AC-0002 forces. Every line below is in text light mode follows. Edits that touch
only full-mode text are not listed.

| Where | Edit | Kind |
| --- | --- | --- |
| `SKILL.md` step 9, gate table | The Reviewer column is dropped. The sentence an earlier pass added to restore the role-to-gate pairing is removed in this batch. | AC-0002 |
| `SKILL.md` step 11 | `review raw-classify` becomes `review-artifact.py raw-classify` (swap). The phrases that named the removed engine's transitions (`guarded transition then`, `fire findings-remain ...`, `fire spec-ready ...`) are removed with no replacement, because pre-approval review runs before any supervisor run exists. | Swap by removal. The owner may rule this a fourth kind. |
| `SKILL.md` REVIEW, roster block | The `select_reviewers` table and the five role bullets become a pointer to `review-rules.json`. The sentence that said light mode runs no `quality-engineer` pass except under the adopter exception goes with them; `light-mode.md` keeps the exception. | AC-0002 |
| `SKILL.md` REVIEW, persistence and classification | `For every warranted reviewer role` becomes `In pre-approval review and light mode, for every ...`; `Classify only the adjudication artifact ...` keeps the light half and drops the full-mode `inspect --adjudication` half. | Qualifier |
| `SKILL.md` REVIEW, parallel dispatch | `Dispatch multiple reviewers in parallel` becomes `In pre-approval review and light mode, dispatch ...`. | Qualifier |
| `SKILL.md` DECIDE, shared clause | The full-mode half becomes a working-plan task; the light half `in light mode and pre-approval review, run GATES, REVIEW, and the human gate again` is restored in this batch unchanged except for the qualifier. | Qualifier |
| `SKILL.md` DECIDE, whole-spec pass | `run quality-engineer against it` becomes `run the high-risk reviewer pass against it`. | AC-0002 |
| `SKILL.md` Finish checklist | The whole-spec pass line drops the role name. | AC-0002 |
| `SKILL.md` Capture | A `Close step` paragraph names the `work-item` capture. | Spec addition (AC-0010), not an edit of an existing line |
| `references/finding-adjudication.md` | The round-number paragraph and the classify block keep their light-mode and pre-approval halves and drop the full-mode halves. | Qualifier |
| `references/capture.md` | `over the human gate's blocker-applied return edge` becomes `as a task the controller adds to the plan`. | Swap by substitution |
| `references/light-mode.md` | Three mentions of the removed engine become `the supervisor`. | Swap |

## T2: VI-7013 search and kept-script callers

The search is the one `tests/roster/test_retired_name_pinned_sites.py` runs: the
five terms `loop-engine`, `loop-cohort`, `engine-state.json`, `full-mode-engine`,
and `cohort state.json`, over `packs/`, `tools/`, `packages/`, `tests/`,
`guides/`, `contracts/`, `.github/`, `docs/product/intents/`, `Makefile`, and
`.snyk`, skipping files named for history and `docs/specs/` references. Run
as `git grep -n -I -E 'loop-engine|loop-cohort|engine-state\.json|full-mode-engine|cohort[ `"-]{1,3}state\.json' -- <those paths> ':!*CHANGELOG.md' ':!*changelog.md'`,
it finds exactly these files:

- the eight pinned (path, term) sites, across six files: `_loop_guards.py` (digest input), `_containment.py` (deny
  list), and four absence assertions (`test_supervisor_admission.py`,
  `test_workspace_mcp_supervisor_run.py`, `test_supervisor_cutover_source_checks.py`,
  and `test_rendered_page_shipped_content_limits.py`);
- three intents whose remaining mentions are dated accounts of past delivery:
  `FEAT-0011-intent-backed-working-view.md`, `work-loop-delivery-efficiency.md`,
  and `contract-amendment-pre-wave-window.md`. The test pins which terms each
  carries, so a new mention fails.

The four intents the search first found are rewritten against the supervisor.
`workspace.toml` and `docs/product/briefs/` stay outside the search for T3.

Kept-script caller check: every script in `work-loop/scripts/` has a caller in
shipped source except two, neither orphaned by this change.

- `_effect_broker.py` has no caller outside its own tests and architecture docs,
  and had none at the base commit.
- `install-pr-template.py` is named only in an adopter guide, and had no shipped
  caller at the base commit.

AC-0009 holds, because no script was invoked only by a removed file. The plan's
looser phrase for VI-7013, `every kept script has a caller`, does not hold for
these two, so the owner should decide whether to wire or retire them.

## T2: security pass over the whole change

One concern and one nit, both fixed in the follow-up batch.

- Concern: `_delivery_feed.py` read each spec's `delivery/evidence.jsonl` from the
  working tree, so an uncommitted frame could reach a page. The feed now compares
  the file with its bytes at `HEAD`, read through the supervisor's hardened Git
  helper, and marks the spec unread (`log-unsafe`) when they differ or the file is
  not in `HEAD`. A root that is not a Git repository has no `HEAD`, so it reads as
  before. `test_delivery_fact_feed_head.py` plants an uncommitted frame and shows
  it never appears.
- Nit: the installed-skill import fence compared path strings by prefix, so a
  directory beside the standard library, or `site-packages` under it, passed, and
  the extension-module directory was not admitted by name. The fence now compares
  whole path components, excludes `site-packages`, admits `DLLs` or `lib-dynload`
  from `sysconfig` and `sys`, and has controls for a sibling directory and for
  `site-packages`.

## T2: controller rulings on the fix batch

- References into `docs/specs/<slug>` are history paths under the spec's
  Definitions, so the AC-0007 search excludes them.
- Three intents (`FEAT-0011`, `work-loop-delivery-efficiency`, and
  `contract-amendment-pre-wave-window`) give dated accounts of past delivery,
  which the Definitions treat as history. The pinned-sites test pins the terms
  each one carries today, which is stricter than AC-0007 requires, so a new
  mention still fails.
- AC-0009 holds. `_effect_broker.py` and `install-pr-template.py` have no
  shipped caller, but neither was called by a removed file either; that was
  already true at the base commit. VI-7013's "every kept script has a caller"
  overstates this, and AC-0009 is the check.
- `guides/core/how-to/run-headless-session.md` now describes the supervisor's
  `workspace_status` fields (stage, `human-decision`, the framed
  `gate_question`, `run_active`) instead of the old engine's gate states.

## T2: final amendment for light-mode engine phrases, VI-7013, and spec-path references

The owner, eugenelim, approved these on 2026-10-29.

- AC-0004 admits a fourth kind of light-mode edit: removing a phrase that
  names an old-engine transition or edge light mode never ran, or replacing it
  with a full-mode-qualified equivalent that leaves the light-mode half
  unchanged.
  That covers step 11's `findings-remain`, `spec-ready`, and guarded-transition
  phrases, and the `blocker-applied` return edge in `references/capture.md`.
- VI-7013's script check is AC-0009's own test: no kept script was called only
  by removed files. `_effect_broker.py` and `install-pr-template.py` meet it.
- AC-0007 also exempts a reference to a `docs/specs/<slug>` path. Such a
  reference points into a history path, just as a `workspace.toml` ref does.

## T2: `_review_assessment.py` and `_subject_source.py` stay

The switch first deleted both as orphans under AC-0009, because only the
removed `_review_compat.py` and `_compat_facade.py` loaded them. While this
branch was in progress, #1650 (grounding-preservation-review) shipped
`test_preservation_review.py`, which loads both directly as the evidence for
its spec. AC-0009 asks only that no kept script was called solely by removed
files; like `_effect_broker.py`, these now have test callers. Both modules and
`test_review_assessment.py` are restored unchanged from main.
