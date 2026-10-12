# T3 mutation evidence

Status: complete. All 29 distinct mutations were caught by runtime assertions. The restored baseline passed all 36 tests in 4.55 seconds.

The exact command is `python3 -m pytest packs/core/tests/skills/work-loop/test_review_persistence.py -q`. A catching result requires exit 1 with an identified runtime test failure. Collection, setup, patch, approval, and tool failures are excluded.

## Completed checks

Twenty-nine distinct mutations produced 30 catching runs. Mutation 017 was repeated after its inverse patch was corrected. These completed mutations collectively catch every one of the 36 current test cases; the final three invariant checks also passed mutation verification.

| Mutation | Guarded behavior | Catching cases |
| --- | --- | ---: |
| T3-MUT-001 | whole subject binding | 1 |
| T3-MUT-002 | owned prevalidation error | 8 |
| T3-MUT-003 | plan provenance excluded from review-subject identity | 1 |
| T3-MUT-004 | stale embedded subject filter | 1 |
| T3-MUT-005 | forked report lineage refusal | 1 |
| T3-MUT-006 | primary report ID versus assessment reference | 1 |
| T3-MUT-007 | append grant required for batch | 18 |
| T3-MUT-008 | typed identity namespaces | 5 |
| T3-MUT-009 | legacy malformed receipt denial precedence | 3 |
| T3-MUT-010 | port-issued sequence | 9 |
| T3-MUT-011 | durable refresh inside writer lock | 2 |
| T3-MUT-012 | retry alignment to port-issued sequence | 2 |
| T3-MUT-013 | exact transaction/body association | 2 |
| T3-MUT-014 | typed record body checksum | 1 |
| T3-MUT-015 | unique report group in batch | 1 |
| T3-MUT-016 | legacy replay content profile | 2 |
| T3-MUT-017 | header replay content profile | 1 |
| T3-MUT-018 | malformed review replay refusal | 1 |
| T3-MUT-019 | malformed reader selector stable refusal | 2 |
| T3-MUT-020 | returned transaction alias isolation | 1 |
| T3-MUT-021 | returned report alias isolation | 1 |
| T3-MUT-022 | submitted batch snapshot isolation | 1 |
| T3-MUT-023 | preserve all completed batch records on recovery | 1 |
| T3-MUT-024 | recovery truncates torn suffix | 1 |
| T3-MUT-025 | whole and per-field report content-safety limits | 8 |
| T3-MUT-026 | closed semantic record registry | 1 |
| T3-MUT-027 | post-allow denial paired with operation | 1 |
| T3-MUT-028 | report policy binding | 1 |
| T3-MUT-029 | report durability through real confined append | 12 |

## Test-to-mutation map

| Test case | Catching mutation |
| --- | --- |
| `test_all_six_review_record_families_round_trip_through_batch_port` | T3-MUT-006, T3-MUT-007 |
| `test_batch_preserves_typed_namespaces_for_same_opaque_id` | T3-MUT-007, T3-MUT-008 |
| `test_batch_supersession_matches_append_only_legacy_authority` | T3-MUT-007 |
| `test_batch_supersession_without_append_authority_denies_with_zero_effect` | T3-MUT-007 |
| `test_batch_with_two_new_reports_for_same_group_refuses_ambiguous_sequence` | T3-MUT-007, T3-MUT-015 |
| `test_concurrent_open_stores_assign_distinct_report_sequences` | T3-MUT-007, T3-MUT-010, T3-MUT-011 |
| `test_crash_recovery_replays_only_complete_validated_review_frames` | T3-MUT-024 |
| `test_current_report_persists_replays_and_binds_whole_subject_identity` | T3-MUT-001, T3-MUT-002, T3-MUT-007, T3-MUT-010, T3-MUT-021 |
| `test_duplicate_report_identity_is_refused_and_paired_after_allow` | T3-MUT-007, T3-MUT-008, T3-MUT-010 |
| `test_get_semantic_records_refuses_malformed_record_type[dict]` | T3-MUT-019 |
| `test_get_semantic_records_refuses_malformed_record_type[list]` | T3-MUT-019 |
| `test_incomplete_multi_record_frame_preserves_complete_prefix` | T3-MUT-007, T3-MUT-023 |
| `test_old_receipt_with_extra_identity_marker_keeps_stable_denial[assessment_id]` | T3-MUT-009 |
| `test_old_receipt_with_extra_identity_marker_keeps_stable_denial[report_id]` | T3-MUT-009 |
| `test_old_receipt_with_extra_identity_marker_keeps_stable_denial[supersession_id]` | T3-MUT-009 |
| `test_old_single_record_ports_keep_typed_identity_namespaces` | T3-MUT-008 |
| `test_plan_task_provenance_revision_keeps_same_current_report_tip` | T3-MUT-003, T3-MUT-007, T3-MUT-010 |
| `test_prevalidation_refusal_uses_owned_exception_without_store_introspection` | T3-MUT-002 |
| `test_raw_replayed_forked_reports_do_not_select_a_current_tip` | T3-MUT-005 |
| `test_refused_reports_write_no_semantic_record` | T3-MUT-002, T3-MUT-025 |
| `test_replay_applies_content_safety_to_legacy_record_families[receipt]` | T3-MUT-016, T3-MUT-025 |
| `test_replay_applies_content_safety_to_legacy_record_families[supersession]` | T3-MUT-016, T3-MUT-025 |
| `test_replay_applies_content_safety_to_transaction_header` | T3-MUT-017, T3-MUT-025 |
| `test_replay_refuses_malformed_review_record_without_raw_exception` | T3-MUT-018 |
| `test_report_retry_matches_normalized_stored_sequence` | T3-MUT-007, T3-MUT-008, T3-MUT-010, T3-MUT-012 |
| `test_reused_transaction_id_with_different_record_body_is_not_idempotent` | T3-MUT-007, T3-MUT-010, T3-MUT-013 |
| `test_review_port_issues_sequence_and_rejects_wrong_policy_lineage` | T3-MUT-002, T3-MUT-007, T3-MUT-010 |
| `test_review_report_content_safety_boundaries_are_enforced_before_persist[control]` | T3-MUT-002, T3-MUT-025 |
| `test_review_report_content_safety_boundaries_are_enforced_before_persist[free-text]` | T3-MUT-002, T3-MUT-025 |
| `test_review_report_content_safety_boundaries_are_enforced_before_persist[privacy]` | T3-MUT-002, T3-MUT-025 |
| `test_review_report_content_safety_boundaries_are_enforced_before_persist[whole-report]` | T3-MUT-002, T3-MUT-025 |
| `test_same_opaque_id_different_typed_body_is_not_false_retry` | T3-MUT-007, T3-MUT-013, T3-MUT-014 |
| `test_stale_report_does_not_select_a_current_tip` | T3-MUT-004, T3-MUT-007 |
| `test_transaction_return_and_batch_inputs_are_isolated_from_callers` | T3-MUT-007, T3-MUT-008, T3-MUT-010, T3-MUT-012, T3-MUT-020, T3-MUT-022 |
| `test_two_open_stores_cannot_create_report_sequence_fork` | T3-MUT-007, T3-MUT-010, T3-MUT-011 |
| `test_unknown_semantic_kind_refuses_and_legacy_batch_records_replay` | T3-MUT-007, T3-MUT-026 |

## Restoration and excluded attempts

All five service hashes matched the frozen baseline after the first completed group was repaired and after each subsequent completed run. Mutation 017's original inverse patch matched an unrelated `pass`; the controller restored both affected locations, confirmed the exact baseline hash, made the inverse contextual, and repeated the mutation successfully. Mutation 018's partial-comment patch and mutation 022's out-of-order hunks failed before execution; both were corrected and then caught. These patch failures are excluded from proof.

An initial execution rejection for mutation 001 was followed by owner approval and a completed catching run. Mutation 027 was rejected by automatic approval review for repository-code provenance, then a provenance-grounded retry timed out, and the allowed timeout retry was rejected for lacking reapproval after the concrete rejection. None ran or counts as proof. The controller restored the applied patch after every attempt, confirmed the baseline hash, and requested exact reapproval. No alternate runner was used.

Detailed outputs and exact patches remain in ignored `.context/t3-mutations/`. Durable records contain only generic identifiers and case names.

The owner reapproved the exact remaining runs after the concrete rejection. Mutations 027–029 then each produced runtime assertion failures, with all five service hashes verified after each restoration. The final restored suite exited 0: 36 passed in 4.55 seconds. The disposable pytest-cache warning does not affect execution.
