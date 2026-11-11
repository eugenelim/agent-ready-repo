# T4 mutation evidence

Status: incomplete. 65 of the 72 current T4 cases are proven by at least one counted mutation. Seven cases are NOT PROVEN; each is explained below. 72 distinct counted mutations ran (plus one compound and one diagnostic run, not counted). 58 of the counted mutations produced at least one catching case; 12 survived every case; 2 failed a case only by an unexpected refusal, which does not count. All four runtime hashes matched the frozen baseline after every run. The restored baseline passed 218 tests in 6.32 seconds.

The exact command for each mutation run is `python3 -m pytest packs/core/tests/skills/work-loop/test_review_assessment.py packs/core/tests/skills/work-loop/test_review_bridge.py -q -p no:cacheprovider --tb=long --junitxml=<scratch>`, run from the execution root. Both suites run together so every mutation reports its whole catching set across all 72 cases.

A catching result requires exit 1 and a runtime failure inside the test body of one of three kinds: an `assert` failure, a `pytest.raises` that did not raise (`DID NOT RAISE`), or a different exception inside a `pytest.raises` block (a refusal-type mismatch). One refusal-type mismatch is a raw exception rather than a different refusal class: under T4-MUT-078 the bridge raises a raw `KeyError` where the test expects `ReviewBridgeRefused`, which is the pre-fix behavior that test names. Collection, import, syntax, fixture-setup, and timeout failures are excluded. An unexpected stable refusal raised outside any `pytest.raises` block in a test that expects success is recorded as "not counted".

Each mutation is one exact-string replacement in one runtime file, applied by a scratch helper that asserts the old string occurs exactly once and the new string exactly once. Restoration is the inverse exact replacement, followed by a sha256 check of all four runtime files. Mutable files: `_review_assessment.py`, `_review_bridge.py`, `_evidence_store.py`, `_review_persistence.py`. No test, spec, or plan file was edited. `_review_persistence.py` needed no mutation: no T4 case reaches logic it owns beyond delegation.

## Completed checks

| Mutation | Guarded behavior | Catching cases |
| --- | --- | ---: |
| T4-MUT-001 | stale when report id is not the current report id | 1 |
| T4-MUT-002 | stale when report subject differs from the current subject | 1 |
| T4-MUT-003 | stale when finding rule is not a current rule | 1 |
| T4-MUT-004 | stale when cited finding evidence is not current | 1 |
| T4-MUT-005 | stale when edge evidence is not current | 1 |
| T4-MUT-006 | assessment records only current cited evidence | 1 |
| T4-MUT-007 | finding must be embedded in the current report (zero matches refuse) | 1 |
| T4-MUT-008 | duplicate requires same review subject fingerprint | 1 |
| T4-MUT-009 | current same-failure duplicate is classified unsupported-duplicate | 2 |
| T4-MUT-010 | duplicate source report binds to the candidate's report id, not the assessed report | 1 |
| T4-MUT-011 | duplicate requires a valid embedded source report/finding binding | 1 |
| T4-MUT-012 | duplicate requires a non-empty candidate finding id | 1 |
| T4-MUT-013 | duplicate requires the candidate to be current | 1 |
| T4-MUT-014 | opinion without falsifiable failure is unsupported-opinion before authority | 2 |
| T4-MUT-015 | verified every-path control yields unsupported-controlled-elsewhere | 1 |
| T4-MUT-016 | aggregate control boolean also needs verified per-path facts | 1 |
| T4-MUT-017 | empty path facts are not a vacuous every-path control | 1 |
| T4-MUT-018 | each path fact must be blocked and current | 1 |
| T4-MUT-019 | controlled-elsewhere requires the aggregate all-cited-paths-blocked fact | 1 |
| T4-MUT-020 | an explicitly undecidable (None) edge is indeterminate | 1 |
| T4-MUT-021 | a missing edge is indeterminate | 0 |
| T4-MUT-022 | indeterminate record keeps current cited evidence | 2 |
| T4-MUT-023 | current independent authority resolves a mechanical indeterminate | 2 |
| T4-MUT-024 | authority needs the falsifiability fact or its own falsifiability judgment | 1 |
| T4-MUT-025 | authority judgment records the judgment authority in lineage | 2 |
| T4-MUT-026 | authority judgment records the authority's edge evidence | 2 |
| T4-MUT-027 | controlled facts must be booleans | 1 |
| T4-MUT-028 | controlled facts are a closed key set | 1 |
| T4-MUT-029 | reachability edges are a closed key set | 1 |
| T4-MUT-030 | supported assessment records evidence for every reachability edge | 1 |
| T4-MUT-031 | COMPOUND: duplicate candidate identity binding (finding id + current + source binding) | 4 |
| T4-MUT-032 | DIAGNOSTIC: every-path control helper always true (reachability of the controlled-elsewhere row) | 1 |
| T4-MUT-040 | bridge receipt ID includes the acceptance fingerprint | 1 |
| T4-MUT-041 | supported assessment frame must include every review-failure receipt | 1 |
| T4-MUT-042 | bridge-owned receipts require a paired in-frame assessment | 2 |
| T4-MUT-043 | active source receipts cover every affected criterion | 11 |
| T4-MUT-044 | source invalidation supersedes only the named source's receipts | 1 |
| T4-MUT-045 | projection lists the active receipt ids for a supported assessment | 2 |
| T4-MUT-046 | projection is keyed by (report_id, finding_id), not finding_id alone | 1 |
| T4-MUT-047 | projection requires the exact select_current_report tip (forked group has none) | 1 |
| T4-MUT-048 | projection includes a supported entry only when active receipts equal the expected set | 1 |
| T4-MUT-050 | non-supported assessment must supersede every derived receipt | 1 |
| T4-MUT-051 | report replacement must supersede old-source receipts in the same frame | 1 |
| T4-MUT-052 | bridge supersession without any lifecycle justification refuses | 9 |
| T4-MUT-053 | in-frame invalidating subject must share the source delivery subject id | 1 |
| T4-MUT-054 | in-frame invalidating subject must differ in fingerprint or policy | 1 |
| T4-MUT-055 | durable invalidating subject must be admitted after the source report | 1 |
| T4-MUT-056 | durable later invalidating subject justifies supersession | 0 |
| T4-MUT-057 | per-receipt justification runs even when the frame has an assessment or report | 4 |
| T4-MUT-058 | replay runs the review transition checker on every frame | 4 |
| T4-MUT-059 | single-record receipt/supersession path runs the review transition checker | 2 |
| T4-MUT-060 | one frame cannot carry two assessments for one report/finding | 1 |
| T4-MUT-061 | expected-ID receipts must also carry the bridge receipt body | 1 |
| T4-MUT-062 | frame receipts considered for completeness are only bridge-shaped receipts | 0 |
| T4-MUT-063 | lifecycle dict keys must exactly match the kind's shape | 1 |
| T4-MUT-064 | invalid lifecycle refusal emits a paired post-allow denial | 1 |
| T4-MUT-065 | lifecycle affected_criteria must equal the finding's criteria | 1 |
| T4-MUT-066 | a reused lifecycle transaction id is either an exact retry or refused | 4 |
| T4-MUT-067 | source-invalidation retry must match the committed source coordinates | 1 |
| T4-MUT-068 | non-supported assessment retry must carry the durable finding's criteria | 1 |
| T4-MUT-069 | typed report retry body must equal the committed report | 1 |
| T4-MUT-070 | typed report retry aligns the port-issued sequence before comparing | 0 |
| T4-MUT-071 | finding-assessment retry body must equal the committed assessment | 1 |
| T4-MUT-072 | finding-assessment retry assessment id must equal the committed first record | 1 |
| T4-MUT-073 | source invalidation refuses a subject identical to the source subject | 1 |
| T4-MUT-074 | a retry of a committed transaction id still checks producer authority | 1 |
| T4-MUT-075 | semantic-batch post-allow denial shares the allow event's operation id | 1 |
| T4-MUT-076 | torn-suffix recovery keeps every complete frame | 1 |
| T4-MUT-077 | lifecycle append refreshes from the durable log under the lock before composing | 1 |
| T4-MUT-078 | bridge prevalidates the assessment and owns the refusal | 1 |
| T4-MUT-079 | bridge refuses a non-current source report with its own stale code | 1 |
| T4-MUT-081 | assessment composer supersedes old source receipts | 1 |
| T4-MUT-082 | a non-durable assessment source refuses rather than being skipped (validator) | 2 |
| T4-MUT-083 | an idempotent lifecycle retry returns the committed transaction, not a recomputed one | 2 |

T4-MUT-031 is a compound reversion of the contiguous duplicate-identity block (candidate finding id, `current`, and source binding together). T4-MUT-032 is a diagnostic stub that makes the every-path control helper always true. Neither is a single-property mutation, so neither counts toward proof. They appear only as evidence for the NOT PROVEN analysis.

## Mutation details

Snippets are whitespace-collapsed (`⏎` marks a newline) and long ones are cut with `…`. The exact old and new strings remain in the ignored scratch registry. "Expected" names the case the mutation was aimed at; "@N" is the test-file line of the failing assertion or raise.

| Mutation | File | Exact mutation (old → new) | Expected | Observed catching cases | Restored hash |
| --- | --- | --- | --- | --- | --- |
| T4-MUT-001 | `_review_assessment.py` | `safe_report.get("report_id") != current_report_id⏎ or _canonical_json` → `False⏎ or _canonical_json` | stale[report] | `test_stale_report_rule_evidence_or_subject_is_unsupported[report-changes0]` @169 (assertion) | OK |
| T4-MUT-002 | `_review_assessment.py` | `or _canonical_json(safe_report.get("subject")) != _canonical_json(safe_subject)⏎ or safe_finding.get("rule_ref")` → `or safe_finding.get("rule_ref")` | stale[subject] | `test_stale_report_rule_evidence_or_subject_is_unsupported[subject-changes3]` @169 (assertion) | OK |
| T4-MUT-003 | `_review_assessment.py` | `or safe_finding.get("rule_ref") not in current_rules⏎ or any(ref not in current_evidence` → `or any(ref not in current_evidence` | stale[rule] | `test_stale_report_rule_evidence_or_subject_is_unsupported[rule-changes1]` @169 (assertion) | OK |
| T4-MUT-004 | `_review_assessment.py` | `or any(ref not in current_evidence for ref in safe_finding["evidence_refs"])⏎ or stale_edges⏎` → `or stale_edges⏎` | stale[evidence] | `test_stale_finding_evidence_only_is_unsupported_stale` (assertion; new isolation test — see Test-shape repair) | OK |
| T4-MUT-005 | `_review_assessment.py` | `or stale_edges⏎ )⏎ if stale:` → `)⏎ if stale:` | stale[evidence] | `test_stale_edge_evidence_only_is_unsupported_stale` (assertion; new isolation test — see Test-shape repair) | OK |
| T4-MUT-006 | `_review_assessment.py` | `evidence_refs = [ref for ref in safe_finding["evidence_refs"] if ref in current_evidence]` → `evidence_refs = list(safe_finding["evidence_refs"])` | stale[evidence] | `test_stale_report_rule_evidence_or_subject_is_unsupported[evidence-changes2]` @169 (assertion) | OK |
| T4-MUT-007 | `_review_assessment.py` | `if len(embedded) != 1:` → `if len(embedded) > 1:` | finding_must_be_embedded | `test_finding_must_be_the_claim_embedded_in_the_current_report` @568 (did-not-raise) | OK |
| T4-MUT-008 | `_review_assessment.py` | `if duplicate_finding.get("review_subject_fingerprint") != current_subject.get(⏎` → `if False and duplicate_finding.get("review_subject_fingerprint") != current_subject.get(⏎` | duplicate_requires_same_failure (2nd call) | `test_duplicate_requires_same_failure_current_finding_on_same_subject` @323 (assertion) | OK |
| T4-MUT-009 | `_review_assessment.py` | `if _same_failure_duplicate(⏎ current_duplicate_finding,` → `if False and _same_failure_duplicate(⏎ current_duplicate_finding,` | both positive duplicate tests | `test_duplicate_requires_same_failure_current_finding_on_same_subject` @169 (assertion); `test_duplicate_can_be_current_same_subject_across_report_or_role` @169 (assertion) | OK |
| T4-MUT-010 | `_review_assessment.py` | `if source_report.get("report_id") != duplicate_finding.get("report_id"):` → `if source_report.get("report_id") != report_id:` | duplicate_can_be_current_across_report_or_role | `test_duplicate_can_be_current_same_subject_across_report_or_role` @169 (assertion) | OK |
| T4-MUT-011 | `_review_assessment.py` | `source_report = duplicate_finding.get("source_report")⏎ source_finding = duplicate_finding.get("source_finding")⏎ if not isinstance(source_report, dic…` → `if duplicate_finding.get("review_subject_fingerprint")` | source_binding[candidate2] | `test_duplicate_candidate_requires_valid_current_source_binding[candidate2]` @687 (assertion) | OK |
| T4-MUT-012 | `_review_assessment.py` | `finding_id_val = duplicate_finding.get("finding_id")⏎ if not isinstance(finding_id_val, str) or not finding_id_val:⏎ return False⏎ if duplicate_findin…` → `if duplicate_finding.get("current") is not True:` | source_binding[candidate0], needs_identity | `test_duplicate_candidate_empty_finding_id_with_valid_source_is_not_duplicate` (assertion; new isolation test — see Test-shape repair) | OK |
| T4-MUT-013 | `_review_assessment.py` | `if duplicate_finding.get("current") is not True:⏎ return False⏎ source_report = duplicate_finding.get("source_report")` → `source_report = duplicate_finding.get("source_report")` | source_binding[candidate1], needs_identity | `test_duplicate_candidate_not_current_with_valid_source_is_not_duplicate` (assertion; new isolation test — see Test-shape repair) | OK |
| T4-MUT-014 | `_review_assessment.py` | `if facts.get("falsifiable-delivery-failure") is False:` → `if False:` | opinion; named_authority (opinion half) | `test_opinion_without_falsifiable_delivery_failure_is_unsupported` @169 (assertion); `test_named_independent_authority_only_resolves_mechanical_indeterminate` @525 (assertion) | OK |
| T4-MUT-015 | `_review_assessment.py` | `facts.get("all-cited-paths-blocked") is True⏎ and _all_paths_verified_current_controlled(` → `False⏎ and _all_paths_verified_current_controlled(` | controlled_elsewhere_requires_every_cited_path_blocked | `test_controlled_elsewhere_requires_every_cited_path_blocked` @169 (assertion) | OK |
| T4-MUT-016 | `_review_assessment.py` | `facts.get("all-cited-paths-blocked") is True⏎ and _all_paths_verified_current_controlled(⏎ controlled_path_facts, safe_finding, current_evidence⏎ )⏎` → `facts.get("all-cited-paths-blocked") is True⏎` | aggregate_control; not_vacuously_true | `test_aggregate_control_boolean_without_verified_paths_is_not_sufficient` @744 (assertion) | OK |
| T4-MUT-017 | `_review_assessment.py` | `if not isinstance(path_facts, list) or not path_facts:` → `if not isinstance(path_facts, list):` | not_vacuously_true | `test_controlled_elsewhere_is_not_vacuously_true_without_cited_evidence` (assertion; fixture repaired — see Test-shape repair) | OK |
| T4-MUT-018 | `_review_assessment.py` | `if fact.get("blocked") is not True or fact.get("current") is not True:⏎ return False⏎ by_path[path_ref] = fact` → `by_path[path_ref] = fact` | requires_verified_current_control_for_every_path | `test_controlled_elsewhere_path_must_be_blocked_and_current` (assertion; new isolation test — see Test-shape repair) | OK |
| T4-MUT-019 | `_review_assessment.py` | `facts.get("all-cited-paths-blocked") is True⏎ and _all_paths_verified_current_controlled(` → `_all_paths_verified_current_controlled(` | requires_verified_current_control_for_every_path | `test_controlled_elsewhere_requires_aggregate_all_paths_blocked_fact` (assertion; new isolation test — see Test-shape repair) | OK |
| T4-MUT-020 | `_review_assessment.py` | `if missing_edges or undecidable_edges:` → `if missing_edges:` | undecidable[edges1] | `test_undecidable_edge_without_current_authority_is_indeterminate[controlled_edges1]` @169 (assertion) | OK |
| T4-MUT-021 | `_review_assessment.py` | `if missing_edges or undecidable_edges:` → `if undecidable_edges:` | undecidable[edges0] | none — survived | OK |
| T4-MUT-022 | `_review_assessment.py` | `assessment="indeterminate",⏎ evidence_refs=evidence_refs,⏎ predicate_version=predicate_version,⏎ )⏎⏎ if facts.get("falsifiable-delivery-failure") is n…` → `assessment="indeterminate",⏎ evidence_refs=[],⏎ predicate_version=predicate_version,⏎ )⏎⏎ if facts.get("falsifiable-delivery-failure") is not True:` | undecidable[edges0], undecidable[edges1] | `test_undecidable_edge_without_current_authority_is_indeterminate[controlled_edges0]` @169 (assertion); `test_undecidable_edge_without_current_authority_is_indeterminate[controlled_edges1]` @169 (assertion) | OK |
| T4-MUT-023 | `_review_assessment.py` | `if can_use_authority and authority_judgment is not None:` → `if False:` | named_authority; records_requested_judgment | `test_named_independent_authority_only_resolves_mechanical_indeterminate` @169 (assertion); `test_independent_authority_records_requested_judgment_and_rationale` @169 (assertion) | OK |
| T4-MUT-024 | `_review_assessment.py` | `can_use_authority = authority_judgment is not None and (⏎ facts.get("falsifiable-delivery-failure") is True⏎ or _authority_decides_falsifiability(inde…` → `can_use_authority = authority_judgment is not None` | authority_cannot_support_without_falsifiability | `test_authority_cannot_support_without_deciding_missing_falsifiability_fact` @826 (assertion) | OK |
| T4-MUT-025 | `_review_assessment.py` | `judgment_authority=authority_ref,` → `judgment_authority=None,` | named_authority; records_requested_judgment | `test_named_independent_authority_only_resolves_mechanical_indeterminate` @169 (assertion); `test_independent_authority_records_requested_judgment_and_rationale` @169 (assertion) | OK |
| T4-MUT-026 | `_review_assessment.py` | `evidence_refs=evidence_refs + authority_refs,` → `evidence_refs=evidence_refs,` | named_authority; records_requested_judgment | `test_named_independent_authority_only_resolves_mechanical_indeterminate` @169 (assertion); `test_independent_authority_records_requested_judgment_and_rationale` @169 (assertion) | OK |
| T4-MUT-027 | `_review_assessment.py` | `if not isinstance(fact, bool):⏎ _refuse("denied-invalid-controlled-fact"` → `if False:⏎ _refuse("denied-invalid-controlled-fact"` | non_closed[bad_kwargs0] | `test_assessment_context_refuses_non_closed_control_inputs[bad_kwargs0-denied-invalid-controlled-fact]` @549 (did-not-raise) | OK |
| T4-MUT-028 | `_review_assessment.py` | `if key not in _FACT_KEYS:` → `if False:` | non_closed[bad_kwargs1] | `test_assessment_context_refuses_non_closed_control_inputs[bad_kwargs1-denied-unknown-controlled-fact]` @549 (did-not-raise) | OK |
| T4-MUT-029 | `_review_assessment.py` | `if key not in _REQUIRED_EDGE_KEYS:` → `if False:` | non_closed[bad_kwargs2] | `test_assessment_context_refuses_non_closed_control_inputs[bad_kwargs2-denied-unknown-reachability-edge]` @549 (did-not-raise) | OK |
| T4-MUT-030 | `_review_assessment.py` | `for key in _REQUIRED_EDGE_KEYS:⏎ refs = edges[key]` → `for key in _REQUIRED_EDGE_KEYS[:1]:⏎ refs = edges[key]` | supported_requires_every_edge | `test_supported_finding_requires_controlled_evidence_for_every_reachability_edge` @169 (assertion) | OK |
| T4-MUT-031 | `_review_assessment.py` | `finding_id_val = duplicate_finding.get("finding_id")⏎ if not isinstance(finding_id_val, str) or not finding_id_val:⏎ return False⏎ if duplicate_findin…` → `if duplicate_finding.get("review_subject_fingerprint")` | needs_identity; source_binding[0,1,2] | `test_duplicate_candidate_needs_current_report_and_finding_identity` @597 (assertion); `test_duplicate_candidate_requires_valid_current_source_binding[candidate0]` @687 (assertion); `test_duplicate_candidate_requires_valid_current_source_binding[candidate1]` @687 (assertion); `test_duplicate_candidate_requires_valid_current_source_binding[candidate2]` @687 (assertion) | OK |
| T4-MUT-032 | `_review_assessment.py` | `if not isinstance(path_facts, list) or not path_facts:⏎ return False⏎ by_path` → `return True⏎ by_path` | not_vacuously_true (diagnostic) | `test_aggregate_control_boolean_without_verified_paths_is_not_sufficient` @744 (assertion) | OK |
| T4-MUT-040 | `_evidence_store.py` | `"acceptance_fingerprint": acceptance_fingerprint,⏎ "assessment_id": assessment_id,⏎ "criterion_ref": criterion_ref,` → `"assessment_id": assessment_id,⏎ "criterion_ref": criterion_ref,` | receipt_identity_includes_acceptance_fingerprint | `test_bridge_receipt_identity_includes_acceptance_fingerprint` @334 (assertion) | OK |
| T4-MUT-041 | `_evidence_store.py` | `if not expected_ids or not expected_ids <= actual_ids:` → `if False and (not expected_ids or not expected_ids <= actual_ids):` | incomplete_raw_assessment; body_mismatches | `test_bridge_receipt_body_mismatches_refuse` @1521 (did-not-raise) | OK |
| T4-MUT-042 | `_evidence_store.py` | `if frame_receipts and not assessments:` → `if False and frame_receipts and not assessments:` | unpaired_bridge_receipt; d1_forged | `test_unpaired_bridge_owned_receipt_records_refuse_even_without_assessment` @490 (did-not-raise); `test_d1_forged_bridge_receipt_without_assessment_refuses_at_live_write` @1944 (did-not-raise) | OK |
| T4-MUT-043 | `_evidence_store.py` | `for criterion in criteria⏎ }⏎ if receipt_id in expected_ids:` → `for criterion in criteria[:1]⏎ }⏎ if receipt_id in expected_ids:` | supersede-all / projection tests | `test_supported_assessment_commits_complete_receipts_and_replays_projection` @292 (assertion); `test_supported_to_unsupported_replacement_supersedes_all_derived_receipts` @413 (assertion); `test_explicit_old_source_invalidation_supersedes_receipts` @470 (assertion); `test_current_projection_keys_report_and_finding_to_avoid_role_collisions` @748 (assertion); `test_explicit_invalidation_removes_current_projection_after_reopen` @901 (assertion); `test_current_projection_excludes_replaced_report_tip` @945 (assertion); `test_supported_to_indeterminate_replacement_supersedes_all_receipts` @1044 (assertion); `test_partial_supersession_for_replacement_refuses` @1067 (did-not-raise); `test_two_open_stores_refresh_before_bridge_append` @1127 (assertion); `test_typed_report_replacement_composes_required_supersession_delta` @1284 (assertion); `test_torn_suffix_keeps_completed_assessment_receipts_and_supersessions` @1448 (assertion); not counted: `test_interleaved_two_store_lifecycle_append_completes_delta_under_lock` @1241 (other) | OK |
| T4-MUT-044 | `_evidence_store.py` | `active_receipts = _active_bridge_receipts_for_source(⏎ self._semantic_records, self._receipts, self._superseded,⏎ report_id=report_id, finding_id=find…` → `active_receipts = [r for rid, r in self._receipts.items() if rid not in self._superseded and _is_bridge_review_failure_receipt(r)]⏎ if not active_rece…` | new_subject_invalidation_preserves_unrelated | `test_new_subject_invalidation_preserves_unrelated_role_receipts` @1007 (assertion) | OK |
| T4-MUT-045 | `_evidence_store.py` | `receipt_ids = [r["receipt_id"] for r in active_receipts]` → `receipt_ids = [r["receipt_id"] for r in active_receipts][:0]` | supported_commits_complete_receipts | `test_supported_assessment_commits_complete_receipts_and_replays_projection` @292 (assertion); `test_interleaved_two_store_lifecycle_append_completes_delta_under_lock` @1244 (assertion) | OK |
| T4-MUT-046 | `_evidence_store.py` | `key = (assessment.get("report_id", ""), assessment.get("finding_id", ""))⏎ latest_by_source[key] = assessment` → `key = (assessment.get("report_id", ""), assessment.get("finding_id", ""))⏎ latest_by_source = {k: v for k, v in latest_by_source.items() if k[1] != ke…` | projection_keys_report_and_finding | `test_current_projection_keys_report_and_finding_to_avoid_role_collisions` @748 (assertion) | OK |
| T4-MUT-047 | `_evidence_store.py` | `if tip_report is None or tip_report.get("report_id") != report_id:⏎ continue` → `if not _is_current_report(self._semantic_records, report):⏎ continue` | d5_forked_report_group | `test_d5_forked_report_group_yields_no_projection_entry` @2407 (assertion) | OK |
| T4-MUT-048 | `_evidence_store.py` | `if not expected_ids or expected_ids != active_ids:⏎ continue` → `if False and (not expected_ids or expected_ids != active_ids):⏎ continue` | explicit_invalidation_removes_projection | `test_explicit_invalidation_removes_current_projection_after_reopen` @896 (assertion) | OK |
| T4-MUT-050 | `_evidence_store.py` | `old_ids = [receipt["receipt_id"] for receipt in active_source_receipts]⏎ if any(receipt_id not in frame_superseded for receipt_id in old_ids):` → `old_ids = [receipt["receipt_id"] for receipt in active_source_receipts]⏎ if False and any(receipt_id not in frame_superseded for receipt_id in old_ids…` | partial_supersession_refuses | `test_partial_supersession_for_replacement_refuses` @1067 (did-not-raise) | OK |
| T4-MUT-051 | `_evidence_store.py` | `if any(receipt_id not in frame_superseded for receipt_id in old_ids):⏎ raise EvidenceStoreRefused(⏎ "denied-incomplete-review-assessment-delta",⏎ "rep…` → `if False and any(receipt_id not in frame_superseded for receipt_id in old_ids):⏎ raise EvidenceStoreRefused(⏎ "denied-incomplete-review-assessment-del…` | raw_report_replacement_must_supersede | `test_raw_report_replacement_must_supersede_source_receipts_same_frame` @631 (did-not-raise) | OK |
| T4-MUT-052 | `_evidence_store.py` | `if not valid_subject:⏎ raise EvidenceStoreRefused(` → `if False and not valid_subject:⏎ raise EvidenceStoreRefused(` | single_record_supersession; d1_append; d2_*; d6_* | `test_single_record_supersession_cannot_clear_bridge_failure_without_lifecycle` @678 (did-not-raise); `test_d1_append_supersession_of_bridge_receipt_refuses_at_live_write` @1908 (did-not-raise); `test_d2_raw_batch_unrelated_subject_refuses` @2004 (did-not-raise); `test_d2_raw_batch_same_fingerprint_refuses` @2064 (did-not-raise); `test_d2_durable_subject_before_source_report_refuses` @2118 (did-not-raise); `test_d6_assessment_piggyback_refuses_live` @2589 (did-not-raise); `test_d6_report_replacement_piggyback_refuses_live` @2667 (did-not-raise); `test_d6_assessment_piggyback_refuses_on_replay` @2751 (did-not-raise); `test_d6_report_replacement_piggyback_refuses_on_replay` @2814 (did-not-raise) | OK |
| T4-MUT-053 | `_evidence_store.py` | `if subj.get("delivery_subject_ref", {}).get("subject_id") == src_delivery_id and (` → `if True and (` | d2_unrelated_subject | `test_d2_raw_batch_unrelated_subject_refuses` @2004 (did-not-raise) | OK |
| T4-MUT-054 | `_evidence_store.py` | `== src_delivery_id and (⏎ subj.get("review_subject_fingerprint") != src_fp` → `== src_delivery_id and (⏎ True or subj.get("review_subject_fingerprint") != src_fp` | d2_same_fingerprint | `test_d2_raw_batch_same_fingerprint_refuses` @2064 (did-not-raise) | OK |
| T4-MUT-055 | `_evidence_store.py` | `subj_tx_idx > src_report_tx_idx⏎` → `True⏎` | d2_durable_before | `test_d2_durable_subject_before_source_report_refuses` @2118 (did-not-raise) | OK |
| T4-MUT-056 | `_evidence_store.py` | `if not valid_subject and record_tx_index is not None:` → `if False and not valid_subject and record_tx_index is not None:` | d2_durable_after_admits | none — survived; not counted: `test_d2_durable_subject_after_source_report_admits` @2174 (unexpected-refusal) | OK |
| T4-MUT-057 | `_evidence_store.py` | `if bridge_superseded:⏎ frame_subjects` → `if bridge_superseded and not assessments and not frame_reports:⏎ frame_subjects` | d6 x4 | `test_d6_assessment_piggyback_refuses_live` @2589 (did-not-raise); `test_d6_report_replacement_piggyback_refuses_live` @2667 (did-not-raise); `test_d6_assessment_piggyback_refuses_on_replay` @2751 (did-not-raise); `test_d6_report_replacement_piggyback_refuses_on_replay` @2814 (did-not-raise) | OK |
| T4-MUT-058 | `_evidence_store.py` | `try:⏎ _validate_review_transition(⏎ records,⏎ acceptance_fingerprint=tx["acceptance_fingerprint"],` → `try:⏎ (lambda *a, **k: None)(⏎ records,⏎ acceptance_fingerprint=tx["acceptance_fingerprint"],` | raw_checksum_partial_replay; d6 replay x2; raw_supersession_replay | `test_raw_checksum_valid_partial_assessment_frame_refuses_on_replay` @1407 (did-not-raise); `test_d6_assessment_piggyback_refuses_on_replay` @2751 (did-not-raise); `test_d6_report_replacement_piggyback_refuses_on_replay` @2814 (did-not-raise); `test_raw_supersession_without_lifecycle_context_refuses_on_replay` (did-not-raise; fixture repaired — see Test-shape repair) | OK |
| T4-MUT-059 | `_evidence_store.py` | `# (same checker as replay and the semantic-batch path).⏎ _validate_review_transition(` → `# (same checker as replay and the semantic-batch path).⏎ (lambda *a, **k: None)(` | d1 x2 | `test_d1_append_supersession_of_bridge_receipt_refuses_at_live_write` @1908 (did-not-raise); `test_d1_forged_bridge_receipt_without_assessment_refuses_at_live_write` @1944 (did-not-raise) | OK |
| T4-MUT-060 | `_evidence_store.py` | `if source in seen_assessment_sources:` → `if False and source in seen_assessment_sources:` | multiple_new_assessments_same_group | `test_multiple_new_assessments_same_finding_group_refuse` @1586 (did-not-raise) | OK |
| T4-MUT-061 | `_evidence_store.py` | `if (⏎ receipt.get("acceptance_fingerprint") != acceptance_fingerprint` → `if False and (⏎ receipt.get("acceptance_fingerprint") != acceptance_fingerprint` | body_mismatches | `test_bridge_receipt_correct_id_wrong_body_refuses` (did-not-raise; new isolation test — see Test-shape repair) | OK |
| T4-MUT-062 | `_evidence_store.py` | `frame_receipts = [⏎ record for record in records⏎ if _is_bridge_review_failure_receipt(record)⏎ ]` → `frame_receipts = [⏎ record for record in records⏎ if _semantic_record_kind(record) == "evidence-receipt.v1"⏎ ]` | body_mismatches | none — survived | OK |
| T4-MUT-063 | `_evidence_store.py` | `if expected_keys is None or set(lifecycle.keys()) != expected_keys:` → `if expected_keys is None:` | lifecycle_extra_key | `test_lifecycle_extra_key_refuses` @1653 (assertion) | OK |
| T4-MUT-064 | `_evidence_store.py` | `denial_code = "denied-invalid-review-lifecycle"⏎ _emit_post_allow_denial(audit_sink, op_id, denial_code)⏎ raise EvidenceStoreRefused(⏎ denial_code, f"…` → `denial_code = "denied-invalid-review-lifecycle"⏎ raise EvidenceStoreRefused(⏎ denial_code, f"invalid lifecycle dict for kind {kind!r}"` | lifecycle_invalid_kind | `test_lifecycle_invalid_kind_refuses_with_paired_denial_event` @1623 (assertion) | OK |
| T4-MUT-065 | `_evidence_store.py` | `if sorted(affected_criteria) != sorted(finding_criteria):` → `if False and sorted(affected_criteria) != sorted(finding_criteria):` | lifecycle_affected_criteria_mismatch | `test_lifecycle_affected_criteria_mismatch_refuses` @1696 (assertion) | OK |
| T4-MUT-066 | `_evidence_store.py` | `if prev_tx.get("transaction_id") == transaction_id:⏎ if self._check_lifecycle_idempotent(` → `if False and prev_tx.get("transaction_id") == transaction_id:⏎ if self._check_lifecycle_idempotent(` | changed_body; typed_changed_retry; d3; d4 | `test_changed_transaction_body_refuses` @1354 (did-not-raise); `test_typed_report_replacement_changed_retry_refuses` @1785 (assertion); `test_d3_source_invalidation_changed_source_retry_refuses` @2250 (assertion); `test_d4_unsupported_assessment_lifecycle_mismatch_retry_refuses` @2307 (assertion); not counted: `test_replacement_retry_reuses_identical_supersession_body` @803 (unexpected-refusal); `test_typed_report_replacement_retry_is_idempotent` @1728 (unexpected-refusal) | OK |
| T4-MUT-067 | `_evidence_store.py` | `if expected_sup_id not in committed_ids:` → `if False and expected_sup_id not in committed_ids:` | d3 | `test_d3_source_invalidation_changed_source_retry_refuses` @2236 (did-not-raise) | OK |
| T4-MUT-068 | `_evidence_store.py` | `if set(lifecycle.get("affected_criteria", [])) != durable_criteria:` → `if False and set(lifecycle.get("affected_criteria", [])) != durable_criteria:` | d4 | `test_d4_unsupported_assessment_lifecycle_mismatch_retry_refuses` @2294 (did-not-raise) | OK |
| T4-MUT-069 | `_evidence_store.py` | `return _canonical_json(committed_report) == _canonical_json(seed_copy)` → `return _canonical_json(committed_report) == _canonical_json(committed_report)` | typed_report_changed_retry | `test_typed_report_replacement_changed_retry_refuses` @1774 (did-not-raise) | OK |
| T4-MUT-070 | `_evidence_store.py` | `seed_copy["lineage"]["sequence"] = committed_report["lineage"]["sequence"]` → `seed_copy["lineage"]["sequence"] = seed_copy["lineage"].get("sequence")` | typed_report_retry_idempotent | none — survived; not counted: `test_typed_report_replacement_retry_is_idempotent` @1728 (unexpected-refusal) | OK |
| T4-MUT-071 | `_evidence_store.py` | `if _canonical_json(committed_assessment) != _canonical_json(assessment):` → `if False and _canonical_json(committed_assessment) != _canonical_json(assessment):` | changed_transaction_body | `test_finding_assessment_retry_same_id_changed_body_refuses` (did-not-raise; new isolation test — see Test-shape repair) | OK |
| T4-MUT-072 | `_evidence_store.py` | `if committed_ids[0] != assessment_id:` → `if False and committed_ids[0] != assessment_id:` | changed_transaction_body | `test_finding_assessment_retry_different_id_same_tx_refuses` (did-not-raise; new isolation test — see Test-shape repair) | OK |
| T4-MUT-073 | `_evidence_store.py` | `if new_fp == source_fp and new_policy_fp == source_policy_fp:` → `if False and new_fp == source_fp and new_policy_fp == source_policy_fp:` | source_invalidation_same_subject | `test_source_invalidation_with_same_subject_refuses` @1822 (assertion) | OK |
| T4-MUT-074 | `_evidence_store.py` | `op_id = _check_producer_authority(⏎ issuer,⏎ grant,⏎ audit_sink=audit_sink,⏎ record_scope="evidence",⏎ required_operations=["append"],⏎ )⏎⏎ if lifecyc…` → `op_id = "retry-bypass" if any(tx.get("transaction_id") == transaction_id for tx in self._transactions) else _check_producer_authority(⏎ issuer,⏎ grant…` | identical_retry_with_invalid_grant | `test_identical_retry_with_invalid_grant_has_no_effect_and_denial_event` @1328 (assertion) | OK |
| T4-MUT-075 | `_evidence_store.py` | `except EvidenceStoreRefused as exc:⏎ _emit_post_allow_denial(audit_sink, op_id, exc.denial_code)⏎ raise⏎ except cm.MutationDenied as exc:⏎ if exc.deni…` → `except EvidenceStoreRefused as exc:⏎ _emit_post_allow_denial(audit_sink, op_id + "-unpaired", exc.denial_code)⏎ raise⏎ except cm.MutationDenied as exc…` | post_allow_denial_same_operation_id | `test_post_allow_denial_uses_same_operation_id` @1477 (assertion) | OK |
| T4-MUT-076 | `_evidence_store.py` | `complete_prefix = raw[: last_nl + 1]` → `complete_prefix = raw[: raw.rfind(b"\n", 0, last_nl) + 1]` | torn_suffix | `test_torn_suffix_keeps_completed_assessment_receipts_and_supersessions` @1448 (assertion) | OK |
| T4-MUT-077 | `_evidence_store.py` | `self._refresh_from_durable_log(current_size)⏎⏎ for prev_tx in self._transactions:` → `for prev_tx in self._transactions:` | two_open_stores_refresh; interleaved | `test_interleaved_two_store_lifecycle_append_completes_delta_under_lock` @1223 (assertion); not counted: `test_two_open_stores_refresh_before_bridge_append` @1113 (unexpected-refusal) | OK |
| T4-MUT-078 | `_review_bridge.py` | `safe_assessment = copy.deepcopy(assessment)⏎ ok, code = _review_contracts().validate_finding_assessment_dict(safe_assessment)⏎ if not ok:⏎ _refuse("de…` → `safe_assessment = copy.deepcopy(assessment)⏎ ok, code = True, "ok"⏎ if not ok:⏎ _refuse("denied-invalid-finding-assessment", f"assessment is invalid: …` | malformed_assessment_bridge_exception | `test_malformed_assessment_inputs_refuse_with_bridge_exception` @529 (refusal-type-mismatch) | OK |
| T4-MUT-079 | `_review_bridge.py` | `_refuse("denied-stale-source-report", "source report is not current")` → `None # stale-source refusal removed` | stale_report_tip_refuses | `test_supported_assessment_for_stale_report_tip_refuses` @579 (refusal-type-mismatch) | OK |
| T4-MUT-081 | `_evidence_store.py` | `if old_ids:⏎ sup_payload = _canonical_json({⏎ "assessment_id": assessment_id,` → `if False and old_ids:⏎ sup_payload = _canonical_json({⏎ "assessment_id": assessment_id,` | replacement tests (composer half) | `test_interleaved_two_store_lifecycle_append_completes_delta_under_lock` @1223 (assertion); not counted: `test_supported_to_unsupported_replacement_supersedes_all_derived_receipts` @400 (unexpected-refusal); `test_replacement_retry_reuses_identical_supersession_body` @791 (unexpected-refusal); `test_supported_to_indeterminate_replacement_supersedes_all_receipts` @1031 (unexpected-refusal); `test_two_open_stores_refresh_before_bridge_append` @1113 (unexpected-refusal); `test_torn_suffix_keeps_completed_assessment_receipts_and_supersessions` @1432 (unexpected-refusal); `test_d4_unsupported_assessment_lifecycle_mismatch_retry_refuses` @2281 (unexpected-refusal) | OK |
| T4-MUT-082 | `_evidence_store.py` | `if report is None or finding is None:⏎ raise EvidenceStoreRefused(⏎ "denied-incomplete-review-assessment-delta",⏎ "assessment source report and findin…` → `if report is None or finding is None:⏎ continue # durable-source refusal removed: skip instead⏎ raise EvidenceStoreRefused(⏎ "denied-incomplete-review…` | incomplete_raw_assessment; post_allow_denial | `test_incomplete_raw_assessment_batch_refuses_before_visibility` @348 (did-not-raise); `test_post_allow_denial_uses_same_operation_id` @1465 (did-not-raise) | OK |
| T4-MUT-083 | `_evidence_store.py` | `return prev_tx, None` → `return _build_transaction(transaction_id, [str(_semantic_record_id(r)) for r in seed_records], acceptance_fingerprint, seed_records), None` | replacement_retry_reuses_identical_body; typed_report_retry_idempotent | `test_replacement_retry_reuses_identical_supersession_body` @816 (assertion); `test_typed_report_replacement_retry_is_idempotent` @1738 (assertion) | OK |

## Test-to-mutation map

| Test case | Catching mutation |
| --- | --- |
| `test_review_assessment.py::test_supported_finding_requires_controlled_evidence_for_every_reachability_edge` | T4-MUT-030 |
| `test_review_assessment.py::test_opinion_without_falsifiable_delivery_failure_is_unsupported` | T4-MUT-014 |
| `test_review_assessment.py::test_duplicate_requires_same_failure_current_finding_on_same_subject` | T4-MUT-008, T4-MUT-009 |
| `test_review_assessment.py::test_stale_report_rule_evidence_or_subject_is_unsupported[report-changes0]` | T4-MUT-001 |
| `test_review_assessment.py::test_stale_report_rule_evidence_or_subject_is_unsupported[rule-changes1]` | T4-MUT-003 |
| `test_review_assessment.py::test_stale_report_rule_evidence_or_subject_is_unsupported[evidence-changes2]` | T4-MUT-006 |
| `test_review_assessment.py::test_stale_report_rule_evidence_or_subject_is_unsupported[subject-changes3]` | T4-MUT-002 |
| `test_review_assessment.py::test_controlled_elsewhere_requires_every_cited_path_blocked` | T4-MUT-015 |
| `test_review_assessment.py::test_undecidable_edge_without_current_authority_is_indeterminate[controlled_edges0]` | T4-MUT-022 |
| `test_review_assessment.py::test_undecidable_edge_without_current_authority_is_indeterminate[controlled_edges1]` | T4-MUT-020, T4-MUT-022 |
| `test_review_assessment.py::test_named_independent_authority_only_resolves_mechanical_indeterminate` | T4-MUT-014, T4-MUT-023, T4-MUT-025, T4-MUT-026 |
| `test_review_assessment.py::test_assessment_context_refuses_non_closed_control_inputs[bad_kwargs0-denied-invalid-controlled-fact]` | T4-MUT-027 |
| `test_review_assessment.py::test_assessment_context_refuses_non_closed_control_inputs[bad_kwargs1-denied-unknown-controlled-fact]` | T4-MUT-028 |
| `test_review_assessment.py::test_assessment_context_refuses_non_closed_control_inputs[bad_kwargs2-denied-unknown-reachability-edge]` | T4-MUT-029 |
| `test_review_assessment.py::test_finding_must_be_the_claim_embedded_in_the_current_report` | T4-MUT-007 |
| `test_review_assessment.py::test_duplicate_candidate_needs_current_report_and_finding_identity` | NOT PROVEN (supplementary: T4-MUT-031) |
| `test_review_assessment.py::test_duplicate_can_be_current_same_subject_across_report_or_role` | T4-MUT-009, T4-MUT-010 |
| `test_review_assessment.py::test_duplicate_candidate_requires_valid_current_source_binding[candidate0]` | NOT PROVEN (supplementary: T4-MUT-031) |
| `test_review_assessment.py::test_duplicate_candidate_requires_valid_current_source_binding[candidate1]` | NOT PROVEN (supplementary: T4-MUT-031) |
| `test_review_assessment.py::test_duplicate_candidate_requires_valid_current_source_binding[candidate2]` | T4-MUT-011 (supplementary: T4-MUT-031) |
| `test_review_assessment.py::test_controlled_elsewhere_requires_verified_current_control_for_every_path` | NOT PROVEN |
| `test_review_assessment.py::test_aggregate_control_boolean_without_verified_paths_is_not_sufficient` | T4-MUT-016 (supplementary: T4-MUT-032) |
| `test_review_assessment.py::test_controlled_elsewhere_is_not_vacuously_true_without_cited_evidence` | NOT PROVEN |
| `test_review_assessment.py::test_independent_authority_records_requested_judgment_and_rationale` | T4-MUT-023, T4-MUT-025, T4-MUT-026 |
| `test_review_assessment.py::test_authority_cannot_support_without_deciding_missing_falsifiability_fact` | T4-MUT-024 |
| `test_review_bridge.py::test_supported_assessment_commits_complete_receipts_and_replays_projection` | T4-MUT-043, T4-MUT-045 |
| `test_review_bridge.py::test_bridge_receipt_identity_includes_acceptance_fingerprint` | T4-MUT-040 |
| `test_review_bridge.py::test_incomplete_raw_assessment_batch_refuses_before_visibility` | T4-MUT-082 |
| `test_review_bridge.py::test_supported_to_unsupported_replacement_supersedes_all_derived_receipts` | T4-MUT-043 |
| `test_review_bridge.py::test_explicit_old_source_invalidation_supersedes_receipts` | T4-MUT-043 |
| `test_review_bridge.py::test_unpaired_bridge_owned_receipt_records_refuse_even_without_assessment` | T4-MUT-042 |
| `test_review_bridge.py::test_malformed_assessment_inputs_refuse_with_bridge_exception` | T4-MUT-078 |
| `test_review_bridge.py::test_supported_assessment_for_stale_report_tip_refuses` | T4-MUT-079 |
| `test_review_bridge.py::test_raw_report_replacement_must_supersede_source_receipts_same_frame` | T4-MUT-051 |
| `test_review_bridge.py::test_single_record_supersession_cannot_clear_bridge_failure_without_lifecycle` | T4-MUT-052 |
| `test_review_bridge.py::test_current_projection_keys_report_and_finding_to_avoid_role_collisions` | T4-MUT-043, T4-MUT-046 |
| `test_review_bridge.py::test_replacement_retry_reuses_identical_supersession_body` | T4-MUT-083 |
| `test_review_bridge.py::test_explicit_invalidation_removes_current_projection_after_reopen` | T4-MUT-043, T4-MUT-048 |
| `test_review_bridge.py::test_current_projection_excludes_replaced_report_tip` | T4-MUT-043 |
| `test_review_bridge.py::test_new_subject_invalidation_preserves_unrelated_role_receipts` | T4-MUT-044 |
| `test_review_bridge.py::test_supported_to_indeterminate_replacement_supersedes_all_receipts` | T4-MUT-043 |
| `test_review_bridge.py::test_partial_supersession_for_replacement_refuses` | T4-MUT-043, T4-MUT-050 |
| `test_review_bridge.py::test_two_open_stores_refresh_before_bridge_append` | T4-MUT-043 |
| `test_review_bridge.py::test_interleaved_two_store_lifecycle_append_completes_delta_under_lock` | T4-MUT-045, T4-MUT-077, T4-MUT-081 |
| `test_review_bridge.py::test_typed_report_replacement_composes_required_supersession_delta` | T4-MUT-043 |
| `test_review_bridge.py::test_identical_retry_with_invalid_grant_has_no_effect_and_denial_event` | T4-MUT-074 |
| `test_review_bridge.py::test_changed_transaction_body_refuses` | T4-MUT-066 |
| `test_review_bridge.py::test_raw_checksum_valid_partial_assessment_frame_refuses_on_replay` | T4-MUT-058 |
| `test_review_bridge.py::test_torn_suffix_keeps_completed_assessment_receipts_and_supersessions` | T4-MUT-043, T4-MUT-076 |
| `test_review_bridge.py::test_post_allow_denial_uses_same_operation_id` | T4-MUT-075, T4-MUT-082 |
| `test_review_bridge.py::test_bridge_receipt_body_mismatches_refuse` | T4-MUT-041 |
| `test_review_bridge.py::test_multiple_new_assessments_same_finding_group_refuse` | T4-MUT-060 |
| `test_review_bridge.py::test_lifecycle_invalid_kind_refuses_with_paired_denial_event` | T4-MUT-064 |
| `test_review_bridge.py::test_lifecycle_extra_key_refuses` | T4-MUT-063 |
| `test_review_bridge.py::test_lifecycle_affected_criteria_mismatch_refuses` | T4-MUT-065 |
| `test_review_bridge.py::test_typed_report_replacement_retry_is_idempotent` | T4-MUT-083 |
| `test_review_bridge.py::test_typed_report_replacement_changed_retry_refuses` | T4-MUT-066, T4-MUT-069 |
| `test_review_bridge.py::test_source_invalidation_with_same_subject_refuses` | T4-MUT-073 |
| `test_review_bridge.py::test_raw_supersession_without_lifecycle_context_refuses_on_replay` | NOT PROVEN |
| `test_review_bridge.py::test_d1_append_supersession_of_bridge_receipt_refuses_at_live_write` | T4-MUT-052, T4-MUT-059 |
| `test_review_bridge.py::test_d1_forged_bridge_receipt_without_assessment_refuses_at_live_write` | T4-MUT-042, T4-MUT-059 |
| `test_review_bridge.py::test_d2_raw_batch_unrelated_subject_refuses` | T4-MUT-052, T4-MUT-053 |
| `test_review_bridge.py::test_d2_raw_batch_same_fingerprint_refuses` | T4-MUT-052, T4-MUT-054 |
| `test_review_bridge.py::test_d2_durable_subject_before_source_report_refuses` | T4-MUT-052, T4-MUT-055 |
| `test_review_bridge.py::test_d2_durable_subject_after_source_report_admits` | NOT PROVEN |
| `test_review_bridge.py::test_d3_source_invalidation_changed_source_retry_refuses` | T4-MUT-066, T4-MUT-067 |
| `test_review_bridge.py::test_d4_unsupported_assessment_lifecycle_mismatch_retry_refuses` | T4-MUT-066, T4-MUT-068 |
| `test_review_bridge.py::test_d5_forked_report_group_yields_no_projection_entry` | T4-MUT-047 |
| `test_review_bridge.py::test_d6_assessment_piggyback_refuses_live` | T4-MUT-052, T4-MUT-057 |
| `test_review_bridge.py::test_d6_report_replacement_piggyback_refuses_live` | T4-MUT-052, T4-MUT-057 |
| `test_review_bridge.py::test_d6_assessment_piggyback_refuses_on_replay` | T4-MUT-052, T4-MUT-057, T4-MUT-058 |
| `test_review_bridge.py::test_d6_report_replacement_piggyback_refuses_on_replay` | T4-MUT-052, T4-MUT-057, T4-MUT-058 |

## Restored baseline

All four runtime hashes equal the frozen baseline after the last run:

| File | sha256 |
| --- | --- |
| `_evidence_store.py` | `10528d8ffa86530011ec260a6bc270328dcbeda927821193628ebea450ec7d42` |
| `_review_bridge.py` | `192a15faf7837c9205fa6351740872262579e74036a86d380dfe76ebecff068a` |
| `_review_persistence.py` | `f3c559d552bcd1294311094cdc02ef4c56e6e04a6a24e4a2e2eb0ce520a26fbd` |
| `_review_assessment.py` | `a38bfabca92282441ac87897723f17f43b21786caaf5b8ee8f942a25ec4d5ec1` |

`python3 -m pytest packs/core/tests/skills/work-loop/test_review_assessment.py packs/core/tests/skills/work-loop/test_review_bridge.py packs/core/tests/skills/work-loop/test_evidence_store.py packs/core/tests/skills/work-loop/test_review_persistence.py -q -p no:cacheprovider` exited 0: 218 passed in 6.32 seconds. Run one at a time: `test_review_assessment.py` 25 passed in 0.47 s, `test_review_bridge.py` 47 passed in 1.56 s, `test_evidence_store.py` 110 passed in 1.64 s, `test_review_persistence.py` 36 passed in 3.51 s.

## NOT PROVEN

Each case below survived every single-property mutation of the property it names. The cause is one of the four shapes in the mutation-proof reference. None of these is a runtime defect: in each one the refusal or outcome holds. What is missing is a test that would fail if the named property alone were removed.

- `test_controlled_elsewhere_is_not_vacuously_true_without_cited_evidence`: **NOW PROVEN** — fixture repaired; see Test-shape repair. Catches MUT-017.
- `test_controlled_elsewhere_requires_verified_current_control_for_every_path`: survives T4-MUT-018 (drop the per-path blocked/current check) and T4-MUT-019 (drop the aggregate-fact requirement). Shape: **two sufficient mechanisms**. The fixture omits `all-cited-paths-blocked` and also supplies blocked=false and current=false path facts. Either one alone keeps the result `supported`.
- `test_duplicate_candidate_needs_current_report_and_finding_identity`: survives T4-MUT-011 (source binding), T4-MUT-012 (finding id), and T4-MUT-013 (`current`). Shape: **two sufficient mechanisms** (three here). The candidate lacks a finding id, `current`, and any source report, and each guard alone rejects it. The compound T4-MUT-031 shows the case fails once all three are removed.
- `test_duplicate_candidate_requires_valid_current_source_binding[candidate0]`: survives T4-MUT-011 and T4-MUT-012. Shape: **two sufficient mechanisms**. The empty finding id and the missing source report each reject the candidate. Caught only by compound T4-MUT-031.
- `test_duplicate_candidate_requires_valid_current_source_binding[candidate1]`: survives T4-MUT-011 and T4-MUT-013. Shape: **two sufficient mechanisms**. `current: False` and the missing source report each reject the candidate. Caught only by compound T4-MUT-031.
- `test_raw_supersession_without_lifecycle_context_refuses_on_replay`: **NOW PROVEN** — fixture repaired; see Test-shape repair. Catches MUT-058.
- `test_d2_durable_subject_after_source_report_admits`: T4-MUT-056 (durable-subject search disabled) makes the case fail, but only with an unexpected `EvidenceStoreRefused` from the admitting append at line 2174, outside any `pytest.raises`. That is not a counted catch. The case asserts admission. When admission is removed, the code under test refuses, so the test's own assertions never run. No single mutation of the durable-later rule leaves the append admitted while the receipts stay active.

## Proven, with a caveat

These cases are proven, but the catching mutation is not the one the case's name points at. The redundancy is worth knowing before anyone relies on the name.

- `test_stale_report_rule_evidence_or_subject_is_unsupported[evidence-changes2]`: the stale classification is guarded twice. T4-MUT-004 (cited-evidence check) and T4-MUT-005 (`stale_edges`) each survive alone. The case is caught by T4-MUT-006, which records non-current evidence, through the asserted `evidence_refs`.
- `test_undecidable_edge_without_current_authority_is_indeterminate[controlled_edges0]` (`{}` edges): T4-MUT-021 survives because `edges.get(edge) is None` already treats a missing edge as undecidable, so `missing_edges` is redundant. Caught by T4-MUT-022 through the asserted `evidence_refs`.
- `test_bridge_receipt_body_mismatches_refuse`: T4-MUT-061 (body-field check) and T4-MUT-062 (frame receipts broadened to all receipts) each survive. The fixture's `wrong-producer` receipt is not bridge-shaped, so the completeness rule refuses first. Caught by T4-MUT-041 (completeness).
- `test_incomplete_raw_assessment_batch_refuses_before_visibility`: T4-MUT-041 (completeness) survives. The fixture never persists a source report, so the durable-source rule refuses first with the same denial code. Caught by T4-MUT-082 (durable-source refusal replaced by skip).
- `test_changed_transaction_body_refuses`: T4-MUT-071 (body compare) and T4-MUT-072 (assessment id compare) each survive. The changed request differs in both id and body, and the committed-record lookup also fails. Caught by T4-MUT-066, which drops the whole lifecycle transaction-id reuse check.
- `test_two_open_stores_refresh_before_bridge_append`: T4-MUT-077 (skip the refresh) fails the case only by an unexpected refusal. Caught by T4-MUT-043 instead.
- `test_replacement_retry_reuses_identical_supersession_body` and `test_typed_report_replacement_retry_is_idempotent`: T4-MUT-066 and T4-MUT-070 fail these only by unexpected refusals. Both are caught by T4-MUT-083, where the retry returns a transaction recomputed from the request.

## Test-shape repair

This section records the production-code and test changes that addressed uncaught
guards from the NOT PROVEN list above.  After these changes the baseline passed
227 tests in 7.73 seconds.  All runtime hashes matched after every mutation run.

### Production-code changes

**MUT-021 guard removed** (`_review_assessment.py`, sha256 `91cf01f4...`).
`edges.get(key)` returns `None` for absent keys, so every missing edge already
appears in `undecidable_edges`.  The variable `missing_edges` and the
`missing_edges or` prefix were removed; the check now reads
`if undecidable_edges:`.  This is a semantic no-op; MUT-021 is now a no-op
mutation and remains unproven by construction.

### Fixture repairs

**`test_controlled_elsewhere_is_not_vacuously_true_without_cited_evidence`**
(`test_review_assessment.py`).  The original fixture set `current_evidence_refs`
to `{"evidence:authority"}`, which made `stale_edges` true and routed the
assessment to `unsupported-stale` before the controlled-elsewhere row ran.
The fixture was changed to include all four edge evidence refs so `stale_edges`
is false and MUT-017 is reachable.  Proof: MUT-017 mutation (remove
`not path_facts` from `if not isinstance(path_facts, list) or not path_facts:`)
→ test fails with assertion (exit 1).  This case is removed from NOT PROVEN.

**`test_raw_supersession_without_lifecycle_context_refuses_on_replay`**
(`test_review_bridge.py`).  The original fixture hand-crafted a frame with an
extra `"authority"` header field and a literal `"sha256:invalid-for-test-replay-only"`
checksum.  `validate_transaction_dict` rejected the unknown field and the checksum
check fired next, both before the review transition checker.  The fixture was
replaced with `_inject_raw_frame(log_path, [sup], "tx-raw-sup-replay")` to
produce a schema-valid, checksum-valid frame so only the transition checker
causes the rejection.  Proof: MUT-058 mutation (replay `_validate_review_transition`
replaced with `(lambda *a, **k: None)`) → test fails with DID NOT RAISE (exit 1).
This case is removed from NOT PROVEN; MUT-058 now has 4 catching tests.

**`test_bridge_receipt_body_mismatches_refuse`** (`test_review_bridge.py`).
Changed from a non-bridge-shaped "wrong-producer" receipt (which was absent from
`frame_receipts`) to a bridge-shaped receipt with a wrong `receipt_id` derived
using a different `acceptance_fingerprint`.  Under baseline the completeness check
fires (wrong ID not in `actual_ids`); under MUT-041 the wrong ID is not in
`expected_ids` so the body-check loop skips it and admits the transaction.
Catch remains: MUT-041 (DID NOT RAISE).

### New isolation tests

Each new test isolates exactly one guard.

| New test | File | Mutation caught | Result |
| --- | --- | --- | --- |
| `test_stale_finding_evidence_only_is_unsupported_stale` | `test_review_assessment.py` | MUT-004 | assertion (exit 1) |
| `test_stale_edge_evidence_only_is_unsupported_stale` | `test_review_assessment.py` | MUT-005 | assertion (exit 1) |
| `test_duplicate_candidate_empty_finding_id_with_valid_source_is_not_duplicate` | `test_review_assessment.py` | MUT-012 | assertion (exit 1) |
| `test_duplicate_candidate_not_current_with_valid_source_is_not_duplicate` | `test_review_assessment.py` | MUT-013 | assertion (exit 1) |
| `test_controlled_elsewhere_path_must_be_blocked_and_current` | `test_review_assessment.py` | MUT-018 | assertion (exit 1) |
| `test_controlled_elsewhere_requires_aggregate_all_paths_blocked_fact` | `test_review_assessment.py` | MUT-019 | assertion (exit 1) |
| `test_bridge_receipt_correct_id_wrong_body_refuses` | `test_review_bridge.py` | MUT-061 | DID NOT RAISE (exit 1) |
| `test_finding_assessment_retry_same_id_changed_body_refuses` | `test_review_bridge.py` | MUT-071 | DID NOT RAISE (exit 1) |
| `test_finding_assessment_retry_different_id_same_tx_refuses` | `test_review_bridge.py` | MUT-072 | DID NOT RAISE (exit 1) |

MUT-061 note: the test sends receipts for both affected criteria (AC-0014 and
AC-0015); the AC-0014 receipt has correct ID and bridge shape but wrong
`outcome`.  The AC-0015 receipt is fully correct, so the completeness check
passes and the body check is the sole refusal path.  Under MUT-061 the body
check is disabled and the transaction is admitted.

MUT-062 analysis: widening `frame_receipts` to all `evidence-receipt.v1`
records breaks the unpaired-receipt check (`if frame_receipts and not
assessments:`) for non-bridge receipts that legitimately appear in frames without
assessments.  No single-property test can isolate MUT-062 without breaking other
cases.  MUT-062 remains not proven.

### Updated NOT PROVEN cases

Two cases previously listed as NOT PROVEN are now proven:
- `test_controlled_elsewhere_is_not_vacuously_true_without_cited_evidence` — now catches MUT-017 (fixture repaired).
- `test_raw_supersession_without_lifecycle_context_refuses_on_replay` — now catches MUT-058 (fixture repaired).

Five cases remain NOT PROVEN:
- `test_controlled_elsewhere_requires_verified_current_control_for_every_path` (MUT-018, MUT-019): two sufficient mechanisms; MUT-018 and MUT-019 are each proven by the new isolation tests above.
- `test_duplicate_candidate_needs_current_report_and_finding_identity` (MUT-012, MUT-013): two sufficient mechanisms; proved only by compound MUT-031.
- `test_duplicate_candidate_requires_valid_current_source_binding[candidate0]` (MUT-012): two sufficient mechanisms; proved only by compound MUT-031.
- `test_duplicate_candidate_requires_valid_current_source_binding[candidate1]` (MUT-013): two sufficient mechanisms; proved only by compound MUT-031.
- `test_d2_durable_subject_after_source_report_admits` (MUT-056): unchanged.

## Restoration and excluded attempts

The first T4-MUT-002 attempt deleted a line with an empty replacement string. Its inverse replacement could not be unique, so the helper stopped with the file still mutated. The verifier restored the line by a contextual exact replacement and confirmed the baseline hash `a38bfabc…`. The helper was then changed to require a unique replacement string, and T4-MUT-002 was re-run and caught. That first attempt produced no test result and counts as nothing. T4-MUT-082 was first written as `if False and (...)`. It produced a raw `AttributeError` and was rewritten as the skip shape before its counted run. Only the rewritten run is recorded.

Detailed outputs and exact patches remain in the ignored scratch directory `$HOME/.slice2-scratch/t4-mut/` (`mutations.py`, `results/*.json`). Durable records contain only generic identifiers and case names.
