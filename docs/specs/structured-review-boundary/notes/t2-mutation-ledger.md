# T2 mutation verification

Controller verification on 2026-10-08: 38 distinct narrow mutations were
caught by the 59-case T2 suite. Every current case has a catching mutation
below. Each run finished before its inverse patch was applied. Full outputs
and exact reversible patches remain in ignored `.context/t2-mutations/`.

The first T2-MUT-023 run survived. A supported nonmaterial finding fixture
was added, and the same mutant then failed that case. The survivor is retained
as an unearned attempt; it is not counted as proof. Two malformed-policy
mutants were repeated after exact-code assertions replaced prefix checks.

Provenance mutants change only fingerprint inputs, keeping record shape
valid. T2-MUT-003 and T2-MUT-035 prove stable denial-code mapping, rather
than invalid-input admission. Decision-row mutants check the returned
truth-table classification; blocking-state checks have separate mutations.

The restored baseline passed 59 tests in 0.85 s. Its runtime source SHA-256 is
`5f8fe9fe105e0772ea4dfbd7cd02d71e0adbd548a44d31a520f26c7ef02881e7`.
The final cleanup removes only the unused `_string_list` helper; read-only
comparison confirms every remaining function body is unchanged. Its SHA-256
is `333d5f21f6583c0b530ced46d7b75c23b166fa1fdd789771159571ad7ccc2f6d`.
The pack-boundary gate passes eight checks. Post-cleanup Ruff and mypy pass;
the final suite passes 59 tests in 1.24 s, and the T2 receipt is recorded.
Mypy covers 155 typed package files; runtime scripts are outside that target.

## Catching cases

| Current test case | Catching mutation IDs |
| --- | --- |
| `test_adapter_callers_refuse_malformed_policy_stably[current-engine]` | `T2-MUT-009`, `T2-MUT-011` |
| `test_adapter_callers_refuse_malformed_policy_stably[synthetic]` | `T2-MUT-009`, `T2-MUT-011` |
| `test_conflicting_current_assessments_fail_closed` | `T2-MUT-018`, `T2-MUT-024` |
| `test_current_engine_and_synthetic_adapter_select_same_ordered_obligations` | `T2-MUT-001`, `T2-MUT-002`, `T2-MUT-005`, `T2-MUT-031` |
| `test_disposition_currentness_or_replacement_gaps_keep_finding_open[fixed-by-missing-replacement]` | `T2-MUT-020`, `T2-MUT-022`, `T2-MUT-038` |
| `test_disposition_currentness_or_replacement_gaps_keep_finding_open[fixed-by-other-role-replacement]` | `T2-MUT-020`, `T2-MUT-022`, `T2-MUT-038` |
| `test_disposition_currentness_or_replacement_gaps_keep_finding_open[fixed-by-replacement-still-open]` | `T2-MUT-020`, `T2-MUT-022`, `T2-MUT-030`, `T2-MUT-038` |
| `test_disposition_currentness_or_replacement_gaps_keep_finding_open[fixed-by-same-subject-current-finding]` | `T2-MUT-020`, `T2-MUT-022`, `T2-MUT-038` |
| `test_disposition_currentness_or_replacement_gaps_keep_finding_open[stale-subject]` | `T2-MUT-019`, `T2-MUT-022`, `T2-MUT-038` |
| `test_engine_and_synthetic_parity_independently_ignores_provenance[plan_digest-plan-digest-other]` | `T2-MUT-001` |
| `test_engine_and_synthetic_parity_independently_ignores_provenance[task_hash-task-hash-other]` | `T2-MUT-031` |
| `test_engine_and_synthetic_parity_independently_ignores_provenance[task_projection_revision-task-rev-other]` | `T2-MUT-002` |
| `test_fixed_by_with_fresh_replacement_subject_current_report_closes_finding` | `T2-MUT-028`, `T2-MUT-030` |
| `test_forked_mandatory_report_lineage_is_unsatisfied` | `T2-MUT-027`, `T2-MUT-037` |
| `test_indeterminate_report_with_no_findings_is_unusable[mandatory]` | `T2-MUT-017`, `T2-MUT-027` |
| `test_indeterminate_report_with_no_findings_is_unusable[optional]` | `T2-MUT-017`, `T2-MUT-026` |
| `test_invalid_waiver_subject_policy_or_currentness_falls_back_to_mandatory[mutation0]` | `T2-MUT-013`, `T2-MUT-037` |
| `test_invalid_waiver_subject_policy_or_currentness_falls_back_to_mandatory[mutation1]` | `T2-MUT-014`, `T2-MUT-037` |
| `test_invalid_waiver_subject_policy_or_currentness_falls_back_to_mandatory[mutation2]` | `T2-MUT-015`, `T2-MUT-037` |
| `test_malformed_or_unknown_major_mandatory_report_is_unsatisfied[report_mutation0]` | `T2-MUT-027`, `T2-MUT-037` |
| `test_malformed_or_unknown_major_mandatory_report_is_unsatisfied[report_mutation1]` | `T2-MUT-027`, `T2-MUT-037` |
| `test_malformed_or_unknown_major_mandatory_report_is_unsatisfied[report_mutation2]` | `T2-MUT-027`, `T2-MUT-037` |
| `test_obligation_deciding_input_mutations_select_mutated_row[finding-open-supported-material-finding]` | `T2-MUT-038` |
| `test_obligation_deciding_input_mutations_select_mutated_row[policy-mandatory-report-unsatisfied]` | `T2-MUT-037` |
| `test_obligation_deciding_input_mutations_select_mutated_row[report-mandatory-report-unsatisfied]` | `T2-MUT-037` |
| `test_obligation_deciding_input_mutations_select_mutated_row[subject-mandatory-report-unsatisfied]` | `T2-MUT-037` |
| `test_obligation_deciding_input_mutations_select_mutated_row[waiver-mandatory-report-unsatisfied]` | `T2-MUT-012`, `T2-MUT-037` |
| `test_obligation_truth_table_current_authorized_waiver_removes_requirement` | `T2-MUT-029` |
| `test_obligation_truth_table_invalid_waiver_falls_back_to_mandatory` | `T2-MUT-012`, `T2-MUT-027`, `T2-MUT-037` |
| `test_obligation_truth_table_mandatory_rows[mandatory-clean-report-expected0]` | `T2-MUT-028` |
| `test_obligation_truth_table_mandatory_rows[mandatory-findings-closed-expected1]` | `T2-MUT-036` |
| `test_obligation_truth_table_mandatory_rows[mandatory-findings-indeterminate-assessment-expected3]` | `T2-MUT-025` |
| `test_obligation_truth_table_mandatory_rows[mandatory-findings-missing-assessment-expected2]` | `T2-MUT-024` |
| `test_obligation_truth_table_mandatory_rows[mandatory-findings-unsupported-expected5]` | `T2-MUT-021` |
| `test_obligation_truth_table_mandatory_rows[mandatory-missing-report-expected7]` | `T2-MUT-027`, `T2-MUT-037` |
| `test_obligation_truth_table_mandatory_rows[mandatory-supported-nonmaterial-expected6]` | `T2-MUT-023` |
| `test_obligation_truth_table_mandatory_rows[mandatory-supported-open-expected4]` | `T2-MUT-022`, `T2-MUT-036`, `T2-MUT-038` |
| `test_obligation_truth_table_mandatory_rows[mandatory-unable-report-expected8]` | `T2-MUT-027`, `T2-MUT-037` |
| `test_obligation_truth_table_optional_missing_report_does_not_block` | `T2-MUT-026` |
| `test_policy_parse_refuses_malformed_containers_stably[None-denied-review-policy-not-a-dict]` | `T2-MUT-009` |
| `test_policy_parse_refuses_malformed_containers_stably[policy1-denied-review-policy-not-a-dict]` | `T2-MUT-009` |
| `test_policy_parse_refuses_malformed_containers_stably[policy2-denied-review-policy-missing-field]` | `T2-MUT-033` |
| `test_policy_parse_refuses_malformed_containers_stably[policy3-denied-review-policy-invalid-role]` | `T2-MUT-010` |
| `test_policy_parse_refuses_malformed_containers_stably[policy4-denied-review-policy-invalid-role]` | `T2-MUT-034` |
| `test_review_subject_projection_rejects_invalid_delivery_subject_shape[mutation0]` | `T2-MUT-004` |
| `test_review_subject_projection_rejects_invalid_delivery_subject_shape[mutation1]` | `T2-MUT-035` |
| `test_review_subject_projection_rejects_invalid_delivery_subject_shape[mutation2]` | `T2-MUT-003` |
| `test_review_subject_projection_rejects_noncanonical_changed_paths[../outside.py]` | `T2-MUT-008`, `T2-MUT-032` |
| `test_review_subject_projection_rejects_noncanonical_changed_paths[./relative.py]` | `T2-MUT-008`, `T2-MUT-032` |
| `test_review_subject_projection_rejects_noncanonical_changed_paths[/absolute/path.py]` | `T2-MUT-008`, `T2-MUT-032` |
| `test_review_subject_projection_rejects_noncanonical_changed_paths[C:/path.py]` | `T2-MUT-006`, `T2-MUT-032` |
| `test_review_subject_projection_rejects_noncanonical_changed_paths[C:path.py]` | `T2-MUT-006`, `T2-MUT-032` |
| `test_review_subject_projection_rejects_noncanonical_changed_paths[file://path.py]` | `T2-MUT-032` |
| `test_review_subject_projection_rejects_noncanonical_changed_paths[packs/core/../path.py]` | `T2-MUT-008`, `T2-MUT-032` |
| `test_review_subject_projection_rejects_noncanonical_changed_paths[packs/core/./path.py]` | `T2-MUT-008`, `T2-MUT-032` |
| `test_review_subject_projection_rejects_noncanonical_changed_paths[packs/core//path.py]` | `T2-MUT-008`, `T2-MUT-032` |
| `test_review_subject_projection_rejects_noncanonical_changed_paths[packs\\core\\path.py]` | `T2-MUT-007`, `T2-MUT-032` |
| `test_stale_bound_obligation_identity_refuses` | `T2-MUT-016` |
| `test_stale_mandatory_report_subject_is_unsatisfied` | `T2-MUT-027`, `T2-MUT-037` |
