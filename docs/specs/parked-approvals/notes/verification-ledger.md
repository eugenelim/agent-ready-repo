# Verification ledger: parked-approvals

This ledger is the closeout evidence for the parked-approvals delivery. It shipped in core 4.0.16, squash-merged as `4c7f17e12` (#1690). All 36 live criteria pass on supervisor run `run-d820148282bf3eda`. They pass again on `main` at `28098e32b` (2026-11-05).

## Where the evidence lives

- **Supervisor records:** branch `feat/parked-approvals-evidence`, tip `6c733b7f9`, on the remote. It holds `docs/specs/parked-approvals/delivery/`: 4 approval pairs, 597 evidence lines, 9 review selections and 1 review decision. Those records were dropped from the squash.
- **Run artifacts:** a planner worktree outside the repository, `<planner-worktree>/plans/processed/evidence/B/round-1/`. It holds the review reports, adjudications, amendment diffs, the accept-risk note, the AC-0024 note and the CI logs.

## Owner approvals

| Date (UTC) | Approver | What | Spec-policy fingerprint |
| --- | --- | --- | --- |
| 2026-11-04 09:31 | eugenelim | spec (scope) and plan (build strategy) | `49eb481cd6145e21c706b09a290acb31a457d172e4c2e6c765940380643f7113` |
| 2026-11-04 22:17 | eugenelim | amendment 1 (scope and build strategy) | `75224e42c9aa777cb4bceaf0e864d971e9ae57ece7aca3054dede806201c4d0c` |
| 2026-11-05 02:58 | eugenelim | amendment 2 (scope and build strategy) | `41910259e18e5f6fc2ce5ac6dff084ca6e933c2145d4a23b326290c09c7678fc` |
| 2026-11-05 03:17 | eugenelim | amendment 3 (scope and build strategy) | `4e9d1d08d908b3310cf2c0f533c1db3488eb1c2ffaa5551bc08aa0f43efd0868` |

The owner also made these decisions during the run:

- 2026-11-04: T10 narrowed the fence that ends the approval-entry region.
- 2026-11-04 and 2026-11-05: AC-0024 was reported as passing before `regenerate`, while catalogue verify still showed `CAT-V-015`. The real check ran after `regenerate`, once the closeout commit had rebuilt the two new-spec `plan.md` copies.
- 2026-11-05: the owner accepted the risk in findings adv7-1 and sec7-2. The instruction was to record any residue that needs no contract change, then proceed.

## Criteria evidence

The supervisor's last gate run, at acceptance fingerprint `2bd9c3aae179ed44a7ce43b6f532419e86f5e7836125be33efbc5a4065d6a7aa`, recorded `pass` for each of the 36 criteria. It ran on `run-d820148282bf3eda`, and the run then went terminal. Each row names the tests that prove the criterion on `main`. Test files are under `packs/core/tests/skills/work-loop/`:

- `PG` is `test_supervisor_parked_gates.py`.
- `GD` is `test_supervisor_gates_digest.py`.
- `GG` is `test_parked_gates_guidance.py`.

| Criterion | Evidence |
| --- | --- |
| AC-0001 | `PG::test_t2_ac0001_park_writes_one_record`, `PG::test_t2_ac0001_untrusted_and_spec_plan_are_recorded` |
| AC-0002 | `PG::test_t2_ac0002_park_changes_nothing_but_the_record` |
| AC-0003 | `PG::test_t2_ac0003_*`: uncommitted, staged, CRLF-of-LF, unmerged, missing |
| AC-0004 | `PG::test_t2_ac0004_status_gates` |
| AC-0005 | `PG::test_t2_ac0005_admitted_pair_refuses`, `PG::test_t2_ac0005_pair_differing_in_one_value_parks` |
| AC-0006 | `PG::test_t2_ac0006_*`: current, replaced, moved commit, unreadable commit |
| AC-0029 | `PG::test_t2_ac0029_the_first_applicable_refusal_wins`, `PG::test_t11_ac0029_unsafe_content_wins_over_spec_changed_after_a_parked_gate` |
| AC-0038 | `PG::test_t2_ac0038_terminal_intent_rules` |
| AC-0030 | `PG::test_t2_ac0030_plan_gate_carries_the_spec_digest`, `PG::test_t2_ac0030_without_a_valid_record_or_after_a_spec_edit_refuses` |
| AC-0032 | `PG::test_t2_ac0032_unsafe_path_refuses`, `PG::test_t2_ac0032_shared_check_rejection_is_a_usage_error` |
| AC-0039 | `GD::test_t1_unsafe_content_refused`, `GD::test_t1_tab_and_crlf_keep_digest`, `PG::test_t2_ac0039_*`, `PG::test_t3_ac0039_a_hidden_character_makes_the_entry_stale`, `PG::test_t4_ac0035_and_ac0039_the_first_applicable_digest_refusal_wins`, `PG::test_t11_ac0039_*`, `GD::test_t1[1-3]_ac0039_*` |
| AC-0007 | `GD::test_t1_status_token_change_same_digest`, `GD::test_t1_crlf_and_trailing_whitespace_same_digest`, `GD::test_t1_ac0007_ac0008_*`, `GD::test_t10_ac0007_*`, `GD::test_t12_ac0007_*`, `GD::test_t13_ac0007_ac0025_*` |
| AC-0008 | `GD::test_t1_body_change_differs`, `GD::test_t1_ac0007_ac0008_*`, `GD::test_t8_qe9_*`, `GD::test_t10_ac0008_*`, `GD::test_t12_ac0008_*`, `GD::test_t13_ac0025_ac0008_*` |
| AC-0025 | `GD::test_t1_ac0025_*`, `GD::test_t10_ac0025_*`, `GD::test_t12_ac0025_*`, `GD::test_t13_ac0025_*`, `GD::test_t14_qe7_1_*` |
| AC-0009 | `PG::test_t3_ac0009_*`: fields and read commands, empty store, sort order, repository behaviour ignored |
| AC-0010 | `PG::test_t3_ac0010_answers_are_fixed_per_gate` |
| AC-0011 | `PG::test_t3_ac0011_*`: every condition, older commit, unreadable commit and edits |
| AC-0012 | `PG::test_t3_ac0012_an_admitted_record_is_omitted` |
| AC-0013 | `PG::test_t3_ac0013_ac0031_bad_entries_list_invalid_beside_a_good_one` |
| AC-0031 | `PG::test_t3_ac0013_ac0031_bad_entries_list_invalid_beside_a_good_one`, `PG::test_t3_ac0031_a_spec_dir_through_a_link_or_missing_is_invalid` |
| AC-0014 | `PG::test_t3_ac0014_gates_changes_nothing` |
| AC-0015 | `PG::test_t4_ac0015_missing_digest_refuses_and_writes_nothing` |
| AC-0036 | `PG::test_t4_ac0036_malformed_digest_is_a_usage_error_on_every_path` |
| AC-0016 | `PG::test_t4_ac0016_a_differing_digest_refuses_and_writes_nothing` |
| AC-0017 | `PG::test_t4_ac0017_matching_digests_admit_with_one_line_in_one_commit` |
| AC-0033 | `PG::test_t4_ac0033_an_admitted_run_answers_current_without_digests` |
| AC-0034 | `PG::test_t4_ac0034_bytes_changing_before_the_commit_are_refused` |
| AC-0037 | `PG::test_t4_ac0037_a_pair_is_recorded_only_from_verified_bytes` |
| AC-0035 | `PG::test_t4_ac0035_and_ac0039_the_first_applicable_digest_refusal_wins`, `PG::test_t11_ac0035_start_with_unsafe_content_and_no_digests_refuses` |
| AC-0018 | `PG::test_t4_ac0018_the_park_record_never_changes_start` |
| AC-0019 | `PG::test_t5_ac0019_a_parked_gate_with_no_answer_is_never_approved` |
| AC-0020 | `GG::test_t6_verb_table_lists_park_gates_and_start_digest_arguments` |
| AC-0021 | `GG::test_t6_skill_approval_step_carries_the_parked_gate_rules`, `GG::test_t6_every_start_command_line_names_both_digest_arguments`, `GG::test_t11_*`, `GG::test_t12_ac0021_*` |
| AC-0022 | `GG::test_t6_parked_gate_eval_case_is_present` (eval `parked-gate-without-answer-works-the-other-spec`); the `evals.json` schema check inside `catalogue lint --deep` |
| AC-0023 | `packs/core/pack.toml` and `plugin.json` read 4.0.15 at `4c7f17e12^` and 4.0.16 at `4c7f17e12`; fragment `docs/product/changelog.d/d0b4710a-cf10-4788-afeb-56ce8298a4c7.md`; `check-core-release --base origin/main` passed before merge |
| AC-0024 | `catalogue lint --root . --deep` and `catalogue verify --root .` exit 0 on `main`, and the tree stays clean |

AC-0026, AC-0027 and AC-0028 are retired identifiers.

## Test runs on main

These ran at `28098e32b` on 2026-11-05, with Git 2.56.0 and Python 3.14 in a throwaway venv:

| Command | Result |
| --- | --- |
| `python -m pytest packs/core/tests/skills/work-loop/test_supervisor_gates_digest.py packs/core/tests/skills/work-loop/test_parked_gates_guidance.py -q` | 97 passed, 1.3 s |
| `WORK_SUPERVISOR_INTEGRATION=1 python -m pytest packs/core/tests/skills/work-loop/test_supervisor_parked_gates.py packs/core/tests/skills/work-loop/test_supervisor_untrusted_unsafe_host.py -q` | 86 passed, 9 min 15 s |
| `WORK_SUPERVISOR_INTEGRATION=1 python -m pytest packs/core/tests/skills/work-loop/test_supervisor_admission.py packs/core/tests/skills/work-loop/test_supervisor_cutover_source_checks.py -q` | 40 passed, 1 min 26 s |
| `PYTHONPATH=packages/agentbundle python -m agentbundle catalogue lint --root . --deep` | exit 0; 81 warnings, 0 errors |
| `PYTHONPATH=packages/agentbundle python -m agentbundle catalogue verify --root .` | exit 0; `git status --short` empty afterwards |

Before merge, CI on head `471c25d92` passed 9 of 9 workflows, `test-corpus` and `test-roster` included. In the integration lane, 579 supervisor tests passed across 12 suites. The corpus check covered 1,201 spec and plan files. It found no Changelog-shape refusals, and the same 3 hidden-character refusals as before.

## Review verdict

Spec stage: 4 shaping, 4 adversarial and 5 security rounds, with 4 adjudication rounds.

Code stage: 9 rounds by the adversarial reviewer, security reviewer and quality engineer, 94 raw findings in all. Rounds 1 to 7 found 32, 10, 13, 16, 15, 2 and 6. Rounds 8 and 9 were clean for all three reviewers; round 9 reviewed the `regenerate` commit. Of the supported findings, T8 to T14 fixed every one except adv7-1 and sec7-2. The owner, as risk owner, accepted those two on 2026-11-05 (decision `decide:review-not-eligible:012a1f31c3739aef`).

```json review-verdict.v1
{
  "schema_version": "review-verdict.v1",
  "state": "READY_WITH_RESIDUAL_RISK",
  "mode": "full",
  "review_unit": "parked-approvals run-d820148282bf3eda",
  "warranted_reviewers": [
    {"role": "adversarial-reviewer", "mandatory": true, "outcome": "clean", "report_ref": "report-adversarial-reviewer-168"},
    {"role": "security-reviewer", "mandatory": true, "outcome": "clean", "report_ref": "report-security-reviewer-169"},
    {"role": "quality-engineer", "mandatory": true, "outcome": "clean", "report_ref": "report-quality-engineer-170"}
  ],
  "named_skips": [],
  "findings": [],
  "required_gates": [
    {"name": "make lint-ruff lint-mypy", "outcome": "pass", "evidence": "pre-merge local gate on 471c25d92"},
    {"name": "supervisor integration lane", "outcome": "pass", "evidence": "579 passed, 12 suites; 126 re-run on 28098e32b"},
    {"name": "catalogue lint --deep and verify", "outcome": "pass", "evidence": "exit 0 on 28098e32b"},
    {"name": "check-core-release --base origin/main", "outcome": "pass", "evidence": "core 4.0.15 to 4.0.16"},
    {"name": "CI", "outcome": "pass", "evidence": "9 of 9 workflows on 471c25d92"}
  ],
  "deferrals": [
    {"slug": "the-parked-gate-digest-misses-effects-field-and-stub-whitesp-da388e184e45", "reason": "adv7-1 and sec7-2: Effects-field and stub-whitespace edits after park keep the gate digest; closing it needs a contract change", "accepted_by": "eugenelim", "residual_eligible": true}
  ],
  "blind_spots": [
    {"surface": "Windows", "reason": "test_supervisor_parked_gates.py and its pseudo-terminal test do not run on Windows CI", "evidence_limit": "park and gates are untested on Windows", "accepted_by": "eugenelim", "residual_eligible": true}
  ],
  "human_gate_status": "approved",
  "non_authoritative_score": null
}
```

## Accepted residue

The spec's Assumptions record each item. The table gives the owner decision and where any follow-on lives:

| Residue | Owner decision | Follow-on |
| --- | --- | --- |
| A plan-level `**Effects:**` field in the approval-entry region feeds the finish effects. Stub lines keep trailing whitespace that the digest ignores. Either can change after park while the digest stays the same. | Risk accepted 2026-11-05 (adv7-1, sec7-2) | [captured defect](../../../product/captured/the-parked-gate-digest-misses-effects-field-and-stub-whitesp-da388e184e45.md) |
| An attempt record pins the shared `info/refs` file. A sibling worktree's `git fetch` mid-run then makes the next `report` refuse with `denied-git-control-state`. | Accepted at delivery; a later supervisor delivery fixes it | [captured defect](../../../product/captured/a-git-fetch-from-a-sibling-worktree-during-a-supervisor-run--408f6f2509c3.md) |
| `report` stages with a fixed 60-second timeout. Under heavy load it refuses with `denied-git-unavailable`. | Accepted at delivery; a later supervisor delivery fixes it | [captured defect](../../../product/captured/the-supervisor-report-step-refuses-under-heavy-load-because--0e599447cde2.md) |
| The `read` commands use `--no-lazy-fetch`, which needs Git 2.44 or later. | Accepted at delivery | None. The supervisor reference's `gates` row documents the floor, and CI meets it. Older Git fails the command rather than fetching. |

The 2026-11-05 promotion drain routed all three captures (`routed-to-defect-processor`). Their records are in `docs/knowledge/observations/work-item/2026-11.jsonl`.

## Closeout checks

- No adopter guide changed. Parking is controller procedure, owned by work-loop `SKILL.md` step 12 and `references/supervisor.md`. `guides/core/how-to/plan-and-execute-non-trivial-work.md` describes the approval gates without the old halt, and stays accurate.
- The close-work lifecycle projection for spec `Shipped` and plan `Done`, outcome `completed`, is `Closeout-pending` with no blocker. No intent or brief names this spec, so no ancestor closure check is owed.
- Closeout lints on the closing change, all exit 0: `lint-spec-status` (also with `--all`), `lint-graph-pointers --base-ref origin/main`, `lint-priority-field`, `lint-contract-item-alignment`, and `make lint-ruff lint-mypy`. The alignment lint reports the 36 checkbox changes as rewordings and does not fail on them.
- Every durable output in the spec's table is present on `main`: ADR-0157 is Accepted, and the guidance names `park`, `gates` and both `start` digest arguments. The architecture command-surface row lists `park` and `gates`. The state-schema row names `gates/` and its writer, `park`. Release 4.0.16 has its fragment.
