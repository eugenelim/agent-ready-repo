# Verification ledger — verified-infrastructure-parallelism

The approved `spec.md` and `plan.md` hold the obligations. This file records, for each criterion, the tests that prove it and the run that checked them.

## Runs

- **Supervisor run:** `run-ec4131b1f275a84b`, tasks T1–T12, terminal on 2026-11-08. Its full history, including the `delivery/` records, is on the branch `feat/vip-t1-contracts-evidence`.
- **Final local sweep (2026-11-08):** every suite below, in its own pytest call with `WORK_SUPERVISOR_INTEGRATION=1`, on the T11 tree; 39 of 39 steps passed with zero failures and zero skips. The T12 tree changed only the plan and one architecture row; `test_supervisor_integration.py` passed 64 of 64 twice on it.
- **CI:** the PR CI runs and the `test-roster.yml` and `test-corpus.yml` dispatches for each PR of the stack are listed under *CI evidence* below.

| Ref | Suite | Result |
| --- | --- | --- |
| G1 | `make lint-ruff lint-mypy` | clean |
| G2 | `tools/lint-pack-test-boundary.py` | ok |
| G3 | `tools/lint-ci-parity.py` | ok |
| S1 | `test_supervisor_concurrency_admission.py` | 15 passed |
| S2 | `test_supervisor_launcher.py` | 77 passed |
| S3 | `test_supervisor_ingestion.py` | 58 passed |
| S4 | `test_supervisor_meets.py` | 88 passed |
| S5 | `test_supervisor_integration.py` | 64 passed |
| S6 | `test_supervisor_failure_handling.py` | 21 passed |
| S7 | `test_supervisor_reason_codes.py` | 77 passed |
| S8 | `test_supervisor_concurrency_permutations.py` | 9 passed |
| S9 | `test_supervisor_projector.py` | 70 passed |
| S10 | `test_supervisor_policy_keys.py` | 29 passed |
| S11 | `test_supervisor_git.py` | 60 passed |
| S12 | `test_supervisor_admission.py` | 24 passed |
| R1–R4 | `test_supervisor_product_ref.py`, `_step_loop.py`, `_attempt.py`, `_commit.py` | 100, 40, 79, 21 passed |
| N1–N9 | review, review_closure, lint_spec_status, review_carry, review_contracts, review_obligation_policy, review_obligation_rules, review_tiers, risk_trigger_record_contract | all passed |
| U1 | `test_supervisor_untrusted_unsafe_host.py` | 18 passed |
| T1–T10 | roster: concurrency_records, fixture_launcher_not_installed, integration_records_match_contract, execution_supervisor_records, containment_attestation_parity, delivery_contract_bundle, supervisor_ci_shards, registry_upgrade_notes, review_rules_merge_base, access_kinds_parity | 3, 9, 2, 13, 25, 118, 6, 32, 1, 2 passed |

Test prefixes: `L::` launcher, `A::` concurrency_admission, `I::` integration, `F::` failure_handling, `RC::` reason_codes, `P::` concurrency_permutations, `ING::` ingestion, `M::` meets, `PR::` projector, `PK::` policy_keys, `G::` git, each `packs/core/tests/skills/work-loop/test_supervisor_<name>.py`; `RR::` is `tests/roster/`.

## Criteria

| AC | Outcome | Proving tests | Run |
| --- | --- | --- | --- |
| AC-0001 | pass | `A::test_the_shipped_policy_issues_no_run_concurrent_and_changes_nothing`; `PK::test_the_shipped_policy_is_the_sequential_floor`; `P::test_a_sequential_run_issues_no_concurrent_request`; `G::test_a_same_size_rewrite_in_the_index_second_is_seen_by_the_seeded_scan` (T11: the seeded scan's index copy keeps the source times, so a same-second, same-size rewrite is seen) | S1, S10, S8 |
| AC-0002 | pass | `A::test_a_task_missing_one_plan_member_goes_to_the_floor[reads,writes,protected,glob,stub]`; `A::test_a_sequential_policy_is_the_opt_in_member`; `A::test_a_spent_reprojection_bound_goes_to_the_floor`; `A::test_a_non_posix_host_goes_to_the_floor`; `A::test_an_old_git_goes_to_the_floor`; `A::test_a_non_driver_merge_key_goes_to_the_floor`; `A::test_no_launcher_pin_goes_to_the_floor`; `G::test_a_merge_key_that_is_not_a_driver_does_not_refuse_start_and_names_a_floor_reason` | S1, S11 |
| AC-0003 | pass | `I::test_two_disjoint_tasks_are_named_in_one_request` | S5 |
| AC-0004 | pass | `A::test_meeting_tasks_are_never_named_in_one_request`; `I::test_a_meeting_task_is_left_out_and_a_later_disjoint_one_joins`; `M::test_meets_row[*]`; `M::test_tasks_meet_in_either_direction_and_a_disjoint_pair_does_not` | S1, S5, S4 |
| AC-0005 | pass | `A::test_a_floor_request_issues_only_while_no_attempt_is_open` (an open request is issued again, never a second one) | S1 |
| AC-0006 | pass | `I::test_three_admissible_tasks_under_a_cap_of_two_name_the_first_two` | S5 |
| AC-0007 | pass | `A::test_a_floor_request_issues_only_while_no_attempt_is_open`; `A::test_a_floor_attempt_that_is_open_is_never_replaced_by_a_concurrent_one` | S1 |
| AC-0008 | pass | `I::test_a_held_result_leaves_a_floor_attempt_free_and_lands_with_its_report` (passed in the full S5 run this pass) | S5 |
| AC-0009 | pass | `I::test_a_held_result_leaves_a_floor_attempt_free_and_lands_with_its_report` (T3 depends on held T2 and is not issued); `I::test_a_task_whose_dependency_is_not_complete_is_not_named` | S5 |
| AC-0010 | pass | `PR::test_each_malformed_declared_entry_marks_the_task_floor_only[*]` (17 forms); `RC::test_each_code_is_emitted_in_status_and_in_the_journal[invalid-path,invalid-glob,writes-listing,protected-path]` | S9, S7 |
| AC-0011 | pass | `PR::test_a_change_to_reads_or_writes_changes_the_revision[reads,writes]` | S9 |
| AC-0012 | pass | Amended to concurrent-mode runs, policy opt-in excluded. `RC::test_the_production_table_names_every_code_the_spec_requires` (hand-written set: AC-0002 members minus the opt-in, AC-0017, AC-0020, AC-0067, refusals, cancellation); `RC::test_every_code_in_the_table_has_a_scenario_and_every_scenario_a_code`; `RC::test_each_code_is_emitted_in_status_and_in_the_journal[*]` (each code in both, both subsets of the closed set); `RC::test_no_launcher_supplied_byte_reaches_status_or_the_journal[*]` (8) | S7 |
| AC-0013 | pass | `L::test_a_named_launcher_is_copied_privately_and_pinned`; `L::test_a_named_digest_with_no_matching_file_pins_nothing_and_records_an_event`; `L::test_a_launcher_inside_the_work_tree_is_not_pinned`; `L::test_no_named_digest_pins_nothing_and_records_no_event` | S2 |
| AC-0014 | pass | `L::test_the_pin_does_not_change_for_the_life_of_the_run` | S2 |
| AC-0015 | pass | `L::test_a_copy_changed_just_before_the_spawn_goes_to_the_floor_without_a_spawn`; `L::test_a_copy_changed_after_the_containment_line_goes_to_the_floor_without_a_release`; `L::test_a_changed_copy_goes_to_the_floor_at_admission` | S2 |
| AC-0016 | pass | `L::test_the_launcher_starts_in_a_clean_private_environment` (planted PATH, HOME, TMPDIR, LANG, PYTHONPATH, LD_PRELOAD, DYLD_INSERT_LIBRARIES, and a secret; checks env keys, values, empty cwd, no extra fds) | S2 |
| AC-0017 | pass | `L::test_a_containment_defect_goes_to_the_floor_without_a_release[*]` (21 cases, including all 6 denials; `[silent]` passed in the full run this pass); `L::test_complete_trace_demands_trace_enforcement` | S2 |
| AC-0018 | pass | `L::test_a_containment_defect_goes_to_the_floor_without_a_release[run-id,attempt-id,grant-id,nonce,launcher]`; `L::test_an_access_defect_fails_the_attempt_without_integrating[oversized,not-json,schema,binding,envelope-binding,token,extra-line,second-access]` (each asserts its security event) | S2 |
| AC-0019 | pass | `L::test_the_release_token_appears_in_no_output_channel` (now skips the fixture's own `recv.log`/`sent.log`; checks run store, journal, status, next, git log, events; planted-leak control still reds); `L::test_the_release_token_is_not_in_the_launchers_argument_or_environment` | S2 |
| AC-0020 | pass | `L::test_an_incomplete_access_attestation_integrates_by_exact_source_only[incomplete,mode,read-outside,bad-path,too-many,write-missing]`; `I::test_a_result_without_a_complete_attestation_integrates_on_exact_source_only` (refusal once the tip moves) | S2, S5 |
| AC-0021 | pass | `L::test_a_run_concurrent_report_asserting_a_fact_is_refused[attestation,reads,writes,binding,access-sha,gate]` | S2 |
| AC-0022 | pass | `L::test_the_fixture_marker_refuses_whatever_candidate_switch_is_set` (5 env vars, 2 policy keys, a file, a CLI flag, then the in-process seam) | S2 |
| AC-0072 | pass | `I::test_the_environment_cannot_choose_completion_order` (4 env vars, policy key `integrate_in_completion_order: true`, a marker file in the run store and in `.supervisor/`, and a `--completion-order` flag refused as usage with nothing run; lands in floor order); `I::test_the_in_process_seam_integrates_in_completion_order` | S5 |
| AC-0023 | pass | `RR::test_fixture_launcher_not_installed.py::*` (9); D2 re-run at `aecafe423`: marker only in `packs/core/tests/.../fixture_launcher.py` and the roster scanner. `build-self` not run (read-only) | T2, D2 |
| AC-0024 | pass | `L::test_a_second_invocation_for_a_run_request_spawns_nothing` | S2 |
| AC-0067 | pass | `L::test_an_access_defect_fails_the_attempt_without_integrating[*]` (each defect: no integration, then a floor issue) | S2 |
| AC-0069 | pass | `L::test_the_process_group_is_durable_before_any_line_is_sent`; `L::test_a_kill_before_the_group_is_recorded_sends_no_release` | S2 |
| AC-0068 | pass | `F::test_an_attempt_silent_past_its_timeout_is_cancelled_and_projected_again`; `F::test_an_attempt_silent_past_its_timeout_whose_end_never_confirms_goes_to_the_floor`; `L::test_an_attempt_silent_past_its_timeout_is_cancelled_and_never_integrates` | S6, S2 |
| AC-0025 | pass | `L::test_a_dead_verb_whose_commit_landed_is_recorded_as_landed`; `L::test_start_settles_a_dead_verbs_attempt_first`; `I::test_recovery_keeps_a_real_held_result_held_and_cancels_the_rest`; `L::test_a_dead_leader_with_a_live_group_member_has_its_group_ended` | S2, S5 |
| AC-0065 | pass | `L::test_a_recorded_group_whose_leader_id_another_process_holds_is_never_signalled`; `L::test_a_dead_leader_with_a_live_group_member_has_its_group_ended`; `L::test_a_recorded_group_with_no_holder_and_no_members_is_confirmed_without_a_signal` (real `group_alive`, no non-zero signal, `cancelled`/`attempt-lost`, dir removed, floor issue) | S2 |
| AC-0066 | pass | `L::test_an_end_recovery_cannot_confirm_is_residue_and_the_task_goes_to_the_floor`; `L::test_an_end_that_never_confirms_leaves_residue_and_goes_to_the_floor` | S2 |
| AC-0026 | pass | `L::test_a_denied_read_does_not_enter_the_attested_set` (end to end: lands with no access defect; `attested_reads` on an `allowlist` attestation drops the denied read). Wording re-checked: production maps `enforced-allowlist` to attestation mode `allowlist` (`_supervisor_concurrent.py:858`, `_supervisor_launcher.py:527`), and `attested_reads` drops denied reads only in that mode (`_supervisor_launcher.py:675-684`). The new `L::test_a_denied_read_stays_in_the_attested_set_under_complete_trace` and `I::test_a_traced_read_listed_as_denied_still_meets_a_change_since_the_source` cover `complete-trace` only, so the criterion still holds | S2, S5 |
| AC-0027 | pass | `I::test_a_traced_read_of_a_path_a_sibling_changed_is_the_refusal_outcome`; `I::test_an_undeclared_traced_read_that_meets_nothing_integrates` | S5 |
| AC-0028 | pass | `I::test_a_case_alias_meets_on_an_ignore_case_repository_only` | S5 |
| AC-0029 | pass | `L::test_an_access_defect_fails_the_attempt_without_integrating[not-ended,child]` | S2 |
| AC-0030 | pass | `ING::test_a_symbolic_link_is_recorded_as_a_link_and_never_read_through` | S3 |
| AC-0031 | pass | Refusal of each defect at the ingestion boundary: `ING::test_a_fifo_is_refused`, `::test_a_socket_is_refused`, `::test_a_device_node_is_refused`, `::test_a_hard_linked_file_is_refused`, `::test_a_git_equivalent_name_is_refused_before_any_object_is_written[*]`, `::test_more_paths_than_the_cap_is_refused_and_exactly_the_cap_passes`, `::test_more_file_bytes_than_the_cap_is_refused_from_the_listing`, `::test_the_shipped_caps_are_the_specified_ones`. Reprojection end to end: `F::test_an_attempt_refused_at_ingestion_reprojects_its_task_and_counts_toward_the_bound[fifo,path-cap]` (`cancelled`, `reproject: true`, `:r1` `run-concurrent`, then the bound sends it to the floor). Production maps every `AttemptRefused` to `_Defect(code, "cancelled")` (`_supervisor_concurrent.py` `_ingest`), so the other defects take the same path | S3, S6 |
| AC-0070 | pass | `ING::test_a_link_that_reaches_git_a_trusted_file_delivery_or_outside_is_refused[*]` (9); `::test_a_link_through_a_directory_link_into_git_is_refused`; `::test_a_chain_of_links_into_a_trusted_file_is_refused`; `::test_the_link_then_dot_dot_pair_resolves_as_the_checked_out_tree_would[*]`; `::test_forty_link_hops_pass_and_forty_one_fail`; `::test_a_link_cycle_is_refused_as_too_many_hops`; new this pass: `::test_a_link_the_protected_index_write_would_refuse_fails_before_any_object[*]` (10), `::test_link_resolution_work_is_bounded_across_all_links` | S3 |
| AC-0073 | pass | `ING::test_a_file_swapped_for_a_link_between_listing_and_read_fails_the_attempt`; `::test_a_parent_directory_swapped_for_a_link_between_listing_and_read_fails_the_attempt`; `::test_a_file_replaced_by_another_of_the_same_size_or_grown_after_listing_fails`; `::test_a_file_that_grows_after_listing_fails` | S3 |
| AC-0071 | pass | `Rig.refused` asserts no new loose objects in every ingestion refusal; `ING::test_more_file_bytes_than_the_cap_is_refused_from_the_listing`; `ING::test_a_large_sparse_file_streams_in_bounded_memory` (200 MiB file, Python peak under 16 MiB by tracemalloc) | S3 |
| AC-0032 | pass | `ING::test_ingestion_admits_exactly_what_the_floor_change_set_admits`; `ING::test_an_unchanged_attempt_directory_ingests_to_the_source_tree` | S3 |
| AC-0033 | pass | `I::test_integration_reads_the_held_identity_not_the_attempt_directory` (first half); `I::test_a_floor_attempt_that_rewrites_a_held_record_is_residue`, `I::test_a_floor_attempt_that_rewrites_a_held_tree_ref_is_residue`, new `I::test_a_held_record_added_during_a_floor_attempt_is_residue[record,record-and-ref]` and `I::test_integration_never_lists_a_held_record_no_consumed_record_matches`, new in T8 `I::test_a_held_ref_added_with_no_record_during_a_floor_attempt_is_residue`, new in T10 `I::test_a_packed_only_held_ref_with_no_record_during_a_floor_attempt_is_residue[small-packed-refs,packed-refs-over-64k]` (the forged held ref lives only in `packed-refs`, small and over 64 KiB; the next verb answers `attempt-residue`, product ref unchanged) and `I::test_an_oversized_packed_refs_makes_the_held_ref_check_refuse_not_admit` (`packed-refs` over the bound: `report` refused `denied-git-control-state`, product ref unchanged) (a held ref forged with no record: the floor manifest now lists the held-ref namespace, so `report` is refused and the next verb answers `attempt-residue`; product ref unchanged) (report refused; the next verb answers exactly `attempt-residue`). Judgment: the `report` refusal code itself is `attempt-refused`, the documented report-side name for the same change (`_supervisor_attempt.py` `_refuse`; `supervisor.md` reason table); the approved plan's T6 defines the proof as the next verb's `attempt-residue` | S5 |
| AC-0034 | pass | `I::test_a_batch_finishing_in_reverse_order_lands_in_floor_order`; `I::test_three_tasks_finishing_in_reverse_land_in_floor_order`; `I::test_a_sibling_ingesting_while_a_result_lands_never_sees_the_ref_ahead_of_its_record` (T12: a sibling's control check never sees the supervisor's own product-ref move before its record; reproduced `denied-git-control-state` without the check-side lock, passed 3 of 3 with it) | S5 |
| AC-0035 | pass | `I::test_an_attested_read_meets_a_changed_path_by_the_closed_rows[*]`; `I::test_an_attested_write_meets_a_rename_at_either_end`; `I::test_a_traced_read_of_a_path_a_sibling_changed_is_the_refusal_outcome` | S5 |
| AC-0036 | pass | `I::test_two_results_changing_the_same_line_conflict_at_the_apply`; refusal outcome: `I::test_a_refusal_leaves_refs_index_and_delivery_and_reprojects_the_task` | S5 |
| AC-0037 | pass | `I::test_a_union_merge_attribute_in_the_checked_out_gitattributes_resolves_nothing` | S5 |
| AC-0038 | pass | `I::test_a_merge_attribute_from_info_attributes_is_refused` | S5 |
| AC-0039 | pass | `I::test_a_merge_config_key_is_refused_even_over_a_same_line_change` | S5 |
| AC-0040 | pass | `G::test_start_refuses_a_merge_driver_in_repository_config`; `G::test_start_refuses_a_merge_driver_in_worktree_config` | S11 |
| AC-0074 | pass | `I::test_a_link_that_resolves_through_a_merged_link_to_a_protected_path_is_refused` | S5 |
| AC-0041 | pass | `I::test_an_apply_that_changes_a_path_outside_the_result_is_refused` | S5 |
| AC-0042 | pass | `I::test_a_compare_and_swap_lost_to_a_ref_move_is_the_refusal_outcome` | S5 |
| AC-0043 | pass | `I::test_a_ref_moved_between_the_check_and_the_swap_is_the_refusal_outcome` | S5 |
| AC-0044 | pass | `I::test_a_kill_at_each_integration_write_converges_through_the_next_verb[6 points]` (product ref read by value at the kill: equals old for `integration-start`/`commit-built`, else a child of old carrying `Supervisor-Attempt`; then converges to the uninterrupted run's tree) | S5 |
| AC-0045 | pass | `I::test_a_kill_at_each_integration_write_converges_through_the_next_verb[post-swap points]` (no new commit, no conflict record and empty `conflicts/`, next is not an `:r1` `run-concurrent`, record `landed` with no `reproject`) | S5 |
| AC-0046 | pass | `L::test_an_honest_attempt_lands_its_tree_and_completes_on_report` (T9 fixed: expects stored kind `run-concurrent` with no `gate`; `ls.git_clean` then the attestation digest, completion-only report and follow-up request all ran); `ls.git_clean` after each integration in `I::test_a_batch_finishing_in_reverse_order_lands_in_floor_order`, `I::test_a_held_result_leaves_a_floor_attempt_free_and_lands_with_its_report`, `I::test_a_kill_at_each_integration_write_converges_through_the_next_verb[*]` | S2, S5 |
| AC-0047 | pass | `I::test_a_conflict_over_the_path_cap_is_written_truncated_in_byte_order`; `I::test_a_conflict_record_holds_paths_and_no_file_contents`; `RR::test_integration_records_match_contract.py::test_a_conflict_record_validates_whole_and_truncated` | S5, T3 |
| AC-0048 | pass | `I::test_a_successful_integration_records_one_result_integration`; `RR::test_integration_records_match_contract.py::test_a_result_integration_record_validates`; `RR::test_concurrency_records.py::test_every_corpus_record_validates` | S5, T3, T1 |
| AC-0049 | pass | `L::test_each_attempt_runs_in_a_fresh_directory_outside_every_denied_location`; `ING::test_attempt_directory_is_a_fresh_plain_directory_outside_every_protected_place`; `ING::test_attempt_directory_refuses_a_protected_location_and_leaves_nothing[*]`; `F::test_a_cancelled_attempt_is_aborted_and_ended_before_its_task_runs_again_on_a_fresh_directory` | S2, S3, S6 |
| AC-0050 | pass | `I::test_a_protected_change_while_a_sibling_is_open_refuses_the_attempt[trusted-file,git-control-state,delivery]` (each `attempt-residue`, product ref unchanged); new `I::test_a_result_changing_the_installed_skill_fails_its_attempt_before_integration[*]` (`protected-path-changed`, product ref unchanged) | S5 |
| AC-0051 | pass | `F::test_a_failed_attempt_reprojects_itself_and_the_sibling_that_meets_it_only`; `F::test_a_conflicting_attempt_cancels_a_running_sibling_that_meets_it`; `I::test_a_sibling_ingesting_while_a_result_lands_never_sees_the_ref_ahead_of_its_record` (T12: a sibling's control check never sees the supervisor's own product-ref move before its record; reproduced `denied-git-control-state` without the check-side lock, passed 3 of 3 with it) | S6 |
| AC-0052 | pass | `F::test_a_cancelled_attempt_is_aborted_and_ended_before_its_task_runs_again_on_a_fresh_directory` | S6 |
| AC-0053 | pass | `F::test_a_cancelled_attempt_whose_end_is_not_confirmed_goes_to_the_floor_as_residue` | S6 |
| AC-0054 | pass | `F::test_a_result_that_returns_after_its_cancellation_never_integrates` | S6 |
| AC-0055 | pass | `F::test_a_task_that_conflicts_the_bound_many_times_runs_its_next_attempt_on_the_floor`; `F::test_a_cancellation_and_a_conflict_count_toward_the_same_bound`; `I::test_a_spent_reprojection_bound_sends_the_task_to_the_floor` | S6, S5 |
| AC-0056 | pass | the same two `F::` bound tests check the journal lines and `status` `reprojected`; `F::test_a_failed_attempt_reprojects_itself_and_the_sibling_that_meets_it_only` | S6 |
| AC-0057 | pass | `F::test_a_replan_waits_for_the_open_attempts_then_discards_held_results_without_counting`; `F::test_a_stub_fence_revision_waits_for_the_open_attempts_then_discards_held_results` (refused `attempt-residue` while open; admitted after; held record `discarded`/`plan-changed`; no reprojection counted) | S6 |
| AC-0058 | pass | `F::test_no_gate_review_or_evidence_issues_while_a_result_is_held_and_each_names_a_held_commit`; `F::test_a_held_result_with_every_task_complete_stops_the_run_rather_than_gating` | S6 |
| AC-0059 | pass | `P::test_each_forced_completion_order_is_the_order_the_journal_records` (order read from the journal's `settled` lines; every permutation of each batch under each mode ran); `P::test_the_allowlisted_read_after_write_keeps_its_two_tasks_in_separate_batches`; `P::test_every_concurrent_run_matches_the_sequential_run` (asserts journal order, then tree id and per-criterion outcomes equal the sequential reference); `P::test_reprojecting_schedules_reproject_and_the_others_do_not`; `P::test_the_floor_task_runs_on_the_floor_between_the_concurrent_ones`. All 9 passed with the new `concurrent-integration` receipt (`_supervisor_integration.py:716-722`); `I::test_a_concurrent_landing_records_no_task_gate_pass_and_the_run_still_gates` also passed (S5), so concurrent runs still match the sequential tree and per-criterion outcomes; the corpus passed 9 of 9 after T11's two fixes (the racy index copy and the landing race), where run-gates 7 had failed it | S8 |
| AC-0060 | pass | `P::test_integrating_in_completion_order_fails_the_read_after_write_comparison` (mode `complete-trace`) | S8 |
| AC-0061 | pass | `P::test_the_corpus_holds_at_most_six_schedules_of_at_most_three_attempts` (4 schedules, at most 3 attempts) | S8 |
| AC-0062 | pass | `P::test_every_corpus_subprocess_ran_isolated_with_no_pi_on_its_path`; `Isolation.assert_clean()` runs in the module fixture before the first run. It checks that the corpus PATH, which the launcher spawn also uses, holds only a Git link, so the Pi executable cannot resolve; the launcher is `-I` and reports `sys.flags.isolated == 1`, and the launcher's PATH is the corpus PATH. | S8 |
| AC-0063 | pass | `RR::test_concurrency_records.py::test_every_corpus_record_validates`; `::test_the_corpus_writes_at_least_one_of_each_kind`. It collects one completion order per schedule and mode, not every permutation. | T1 |
| AC-0064 | pass | The parity and record suites' existing fixtures validate: `RR::test_containment_attestation_parity.py` (25), `RR::test_delivery_contract_bundle.py` (118), `RR::test_execution_supervisor_records.py` (13), `RR::test_integration_records_match_contract.py` (2) | T3–T6 |

## CI evidence

The slice shipped as three PRs. T5 to T12 and this closeout ride with T3 and T4 in the last one, because the review-round fixes in T6 to T12 are what make T3 and T4 pass on current `main`.

| PR | Tasks | Core | PR checks | `test-roster.yml` | `test-corpus.yml` | Merge |
| --- | --- | --- | --- | --- | --- | --- |
| #1723 | T1 | 4.0.25 | 48 pass, 1 skipped (head `c914db3fd`) | 42529107784 | 42524241272 | `f6ce81c9b` |
| #1725 | T2 | 4.0.27 | 48 pass, 1 skipped (head `7e5b79e49`) | 42550076378 | 42550045170 | `5b81ed626` |
| #1727 | T3–T12 and closeout | 4.0.29 | 53 pass, 1 skipped (head `d6b49e7f5`) | 42629030637 | 42629034232 | this PR's squash commit |

## Defects found during the run

- **Racy index copy (T11; shipped standalone as PR #1722, Core 4.0.24).** The seeded scan's private index copy was newer than its entries, so Git trusted the stat data of a same-second, same-size rewrite and the change set missed it. The copy now keeps the source index's access and modification times. Proved by `G::test_a_same_size_rewrite_in_the_index_second_is_seen_by_the_seeded_scan` (failed 3 of 3 without the fix).
- **Product-ref landing race (T11 code, T12 plan task).** Inside one `run-concurrent` verb, a sibling attempt's Git control check could read the product ref after the supervisor moved it and before it recorded the move, and refused the batch with `denied-git-control-state`. `GitPort.landing`, an in-process lock, now covers the move through its record, and the check reads the ref and its record under it. Proved by the T12 test above; the permutation corpus then passed 9 of 9.

## Review and owner decisions

- Code review ran four rounds with security-reviewer, adversarial-reviewer and quality-engineer, then one final pass on T12. Every Blocker and Concern was repaired in the run (T6–T12).
- The owner capped review after round 4 (2026-11-07) and chose to fix round 4's two traceability findings in T12 (2026-11-08).
- The final T12 pass left three wording nits (adv5-1 Rollout line, adv5-2 AC-0059 mapping, qe5-1 race-row citation). The owner chose to fix all three as closeout commits after terminal (2026-11-08); they are fixed in this PR. No risk was accepted.

## Known limit

No shipped host can attest containment, so every adopter stays on the sequential floor (`concurrency: sequential`). The concurrent path runs only under the test fixture launcher, which a roster test keeps out of every installed skill.
