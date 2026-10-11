# T6 mutation evidence, third pass

Status: complete. 79 of 83 cases in `test_review_compat.py` are proven by at least one counted single-property mutation. Four cases are NOT PROVEN, and no mutation of the two runtime files in scope can red them. 103 counted single-property mutations ran: 91 caught at least one case and 12 survived every case. Both runtime hashes matched the baseline after every run.

**Prior defects.** All five defects from ledger-2 (N1–N5) are resolved in this baseline. Six test groups added for them pin the fixes: `test_validate_before_write_refusals_persist_nothing[*]` (N2/N3), `test_unusable_store_root_is_unable_for_direct_clean[*]` (N5), `test_same_status_replay_with_different_findings_conflicts` (N4), and `test_t4_141b_unable_key_set_is_closed` (N1 analog on the unable path). The conflict path now raises `ReviewCompatRefused` rather than returning a seven-key dict.

**New runtime defects.** None found.

## Scope and method

Targets: all 83 cases of `packs/core/tests/skills/work-loop/test_review_compat.py`. That is 65 cases from the prior pass plus 18 new ones added since the baseline changed (`df6818a8…` vs `d1bb92e8…`).

Each run used this command from the execution root: `python3 -m pytest packs/core/tests/skills/work-loop/test_review_compat.py -q -p no:cacheprovider`. Each mutation reports every case it catches.

A catch needs exit 1 and a runtime failure inside a test body. Four kinds count:

- **assertion:** an `assert` in the test body fails.
- **did-not-raise:** a `pytest.raises` block saw no raise.
- **test-body-raise:** the test body raises on the subject's output.
- **unexpected-raise:** the code under test raises while the failing test statement calls `reconcile_review_source_event` or the loop-engine caller.

Collection, import, syntax, fixture-setup, and timeout failures do not count. None occurred.

Each mutation is one exact-string replacement in one runtime file. Helpers lived in `$HOME/.slice2-scratch/t6-mut3/` (`run_batch.py`, `mutations_01.py` through `mutations_12.py`). Every replacement was checked in memory before anything was written: the old string occurs exactly once, the new string occurs exactly once after replacement, no string is empty, and the result compiles. Restoration is the inverse exact replacement followed by a sha256 check. Only `_review_compat.py` and `project_compat_reconcile_review_source_event` in `loop-engine.py` were mutated. No test or other repository file was edited.

Batch 01 was re-run as batch 12 after a parser bug (wrong regex for FAILED lines) caused the caught-test names to be lost. Results were merged with the corrected batch 12 data before compilation.

Baseline sha256, verified before the first run and after every run:

| File | sha256 |
| --- | --- |
| `_review_compat.py` | `df6818a8d2769520e6d2f82f3c59e3b1570cac83d81cc201b7611559fa7945db` |
| `loop-engine.py` | `c2bf88cc8e962d0553bd65f580f260919a2e74e081dba1c131086472d7b4cfa1` |

### Changes from the second pass

Baseline changed: `d1bb92e8…` → `df6818a8…`. The new baseline incorporates 18 new test cases and the following code changes: raw CS loop now covers both `raw_report_text` and `adjudication_text` in a single for-loop; `is_dir()` added to the store-root guard; duplicate `finding_id` check added in `_classify_adjudicated`; all schema-invalid findings now return `unable` (no more `indeterminate` for missing-field); `_unable()` is a local closure that always calls `_structured_present()`; D2 now includes a comprehensive conflict check over the report body and all assessments plus an extra-stored-assessment check.

Added mutations: 021, 022, 023 (D1 byte-equality sub-properties), 032 (footer check direction), 132B (is_dir guard), MUT-NEW-DECODED-CS (decoded string CS), MUT-NEW-DUPID (duplicate finding_id), MUT-NEW-D2-STATUS, MUT-NEW-D2-ASSESS-ONLY, MUT-NEW-D2-EXTRA-ASSESS (D2 sub-properties), MUT-NEW-ASSESS-VALIDATE, MUT-NEW-ASSESSMENT-GUARD (validate-before-write path), MUT-NEW-REPORT-CONTRACT. Removed or renamed: MUT-053C (missing-field now returns `unable`, same as MUT-053B behavior), MUT-012/013 (D5 adj-check gates replaced by the combined loop + decoded CS design), MUT-002 (no separate step-5 fallback in new code).

## Completed checks

| Mutation | Guarded behavior | Catching cases |
| --- | --- | ---: |
| T6-MUT-001 | closed form gate: a form outside the closed set returns unable | 3 |
| T6-MUT-010 | raw content-safety refusal of raw_report_text returns unable | 1 |
| T6-MUT-011 | raw CS loop skips adjudication_text (adj text not checked) | 0 — UNCAUGHT |
| T6-MUT-011B | both raw CS checks removed (loop body disabled) | 1 |
| T6-MUT-020 | D1: direct-clean byte equality check removed | 3 |
| T6-MUT-021 | D1: direct-clean reverted to legacy raw classifier (not byte equality) | 2 |
| T6-MUT-022 | D1: direct-clean strips trailing newline before byte compare | 2 |
| T6-MUT-023 | D1: direct-clean uses prefix match instead of exact byte equality | 3 |
| T6-MUT-030 | structural-clean: classification != clean check removed | 2 |
| T6-MUT-031 | structural-clean: not_checked_present footer check removed | 1 |
| T6-MUT-032 | structural-clean: footer check inverted (refuse when no footer) | 3 |
| T6-MUT-033 | structural-clean: uses byte equality instead of legacy raw classifier | 2 |
| T6-MUT-040 | findings form: grammar-valid check removed (all → indeterminate) | 1 |
| T6-MUT-041 | findings form: indeterminate changed to unable for grammar-valid findings | 2 |
| T6-MUT-050 | adjudicated: missing adjudication_text check removed | 1 |
| T6-MUT-051 | adjudicated: JSON parse failure re-raised instead of indeterminate | 1 |
| T6-MUT-052 | adjudicated: empty finding list check removed | 1 |
| T6-MUT-053 | adjudicated: finding schema validation check removed | 0 — UNCAUGHT |
| T6-MUT-054 | adjudicated: adjudication JSON parse failure re-raised | 1 |
| T6-MUT-055 | adjudicated: audit not-dict check removed | 1 |
| T6-MUT-056 | adjudicated: audit ids one-to-one check removed | 2 |
| T6-MUT-057 | adjudicated: one-to-one check weakened to subset (extra audit id passes) | 1 |
| T6-MUT-058 | adjudicated: audit entry not-dict check removed | 1 |
| T6-MUT-059 | adjudicated: closed decision set check removed | 1 |
| T6-MUT-060 | adjudicated: refuted removed from closed audit decision set | 11 |
| T6-MUT-061 | adjudicated: authority_ref non-empty check removed | 1 |
| T6-MUT-070 | sustained: independent_authority=None (not from audit) | 1 |
| T6-MUT-071 | sustained: refuted branch forced for all decisions | 2 |
| T6-MUT-072 | refuted: branch skipped (refuted → supported instead of unsupported-opinion) | 1 |
| T6-MUT-073 | refuted: controlled_facts falsifiable-delivery-failure set to True | 2 |
| T6-MUT-074 | sustained: requested_judgment changed to unsupported-opinion | 2 |
| T6-MUT-080 | legacy presence: operation_id check removed | 1 |
| T6-MUT-081 | legacy presence: transition_id match in history removed | 13 |
| T6-MUT-082 | legacy presence: any non-None transition_id matches (not source_event_id) | 1 |
| T6-MUT-083 | legacy presence: unrecognised event still claims legacy clean | 1 |
| T6-MUT-084 | legacy presence: findings-remain not mapped to findings outcome | 2 |
| T6-MUT-085 | legacy presence: reviewers-clean not mapped to clean outcome | 11 |
| T6-MUT-090 | agreement: clean legacy agrees with any result (not just clean) | 2 |
| T6-MUT-091 | agreement: findings legacy agrees with any result (not just findings) | 1 |
| T6-MUT-092 | agreement: findings-findings agreement removed | 1 |
| T6-MUT-093 | divergent: not set on disagreement (False instead of True) | 3 |
| T6-MUT-094 | divergent: op_id-only path not excluded from divergent | 1 |
| T6-MUT-095 | agreement: no-legacy short-circuit removed (acknowledges without legacy) | 4 |
| T6-MUT-096 | agreement: no-legacy short-circuit removed (same behavior via None event) | 0 — UNCAUGHT |
| T6-MUT-097 | unable: acknowledged forced True in _unable() return | 3 |
| T6-MUT-098 | agreement: indeterminate allowed to acknowledge against legacy clean | 1 |
| T6-MUT-100 | unable early return removed after classification | 11 |
| T6-MUT-101 | D6: structured_present in _unable() hard-coded to False | 1 |
| T6-MUT-101B | D6: structured_present in _unable() hard-coded to True | 17 |
| T6-MUT-102 | persistence: fresh event report write skipped | 19 |
| T6-MUT-103 | D6: structured_present on success path hard-coded to False | 3 |
| T6-MUT-104 | D6/D2: early store lookup skipped (existing_report always None) | 3 |
| T6-MUT-110 | replay guard: existing report rewritten on any call | 52 |
| T6-MUT-111 | idempotency: lineage lookup always returns None (never finds existing) | 7 |
| T6-MUT-112 | crash recovery: all assessments skipped (never-write path) | 6 |
| T6-MUT-113 | crash recovery: dedup guard removed (already-stored assessments re-written) | 0 — UNCAUGHT |
| T6-MUT-114 | crash recovery: skip-check removed (equivalent formulation of 113) | 0 — UNCAUGHT |
| T6-MUT-116 | assessments: not scoped to this report_id (all assessments loaded) | 1 |
| T6-MUT-117 | persistence: assessments never written for findings result | 6 |
| T6-MUT-120 | deterministic IDs: report_id made non-deterministic (random suffix) | 4 |
| T6-MUT-121 | deterministic IDs: report transaction_id made random | 0 — UNCAUGHT |
| T6-MUT-122 | deterministic IDs: assessment_id made non-deterministic (random suffix) | 2 |
| T6-MUT-123 | deterministic IDs: assessment transaction_id made random | 0 — UNCAUGHT |
| T6-MUT-124 | deterministic IDs: lineage source_event_id made non-deterministic | 8 |
| T6-MUT-130 | temp dir: not created under store root | 1 |
| T6-MUT-131 | temp dir: not removed after classification | 1 |
| T6-MUT-132 | store root check removed entirely | 3 |
| T6-MUT-132B | store root is_dir() check removed (non-directory root allowed) | 2 |
| T6-MUT-133 | classifier I/O: failure re-raised instead of returning error classification | 1 |
| T6-MUT-134 | classifier I/O: failure returns clean instead of error | 1 |
| T6-MUT-140 | return value: divergent field removed from success path | 11 |
| T6-MUT-141 | return value: extra field in success path (7 keys instead of 6) | 1 |
| T6-MUT-141B | return value: extra field in unable path (7 keys) | 1 |
| T6-MUT-142 | return value: source_event_id replaced by role (wrong field) | 7 |
| T6-MUT-143 | return value: legacy_present hard-coded to False in success path | 4 |
| T6-MUT-150 | loop-engine: project_compat_reconcile_review_source_event renamed | 4 |
| T6-MUT-151 | loop-engine caller: legacy_state replaced with empty dict | 1 |
| T6-MUT-152 | loop-engine caller: source_event modified (role substituted) | 1 |
| T6-MUT-153 | loop-engine caller: review_policy replaced with empty dict | 0 — UNCAUGHT |
| T6-MUT-154 | loop-engine caller: return value acknowledged forced to False | 1 |
| T6-MUT-160 | VI-1012: reviewer role-name literal injected | 1 |
| T6-MUT-161 | VI-1018: initial-plan-review.v1 reference injected as constant | 1 |
| T6-MUT-162 | VI-1018: mutable task projection API injected | 1 |
| T6-MUT-163 | VI-1019: agentbundle import injected inside function body | 1 |
| T6-MUT-164 | VI-1019: real contracts/delivery file read injected | 1 |
| T6-MUT-165 | VI-1018: cohort state.json write injected | 1 |
| T6-MUT-166 | legacy_state: caller's dict mutated before deep copy | 3 |
| T6-MUT-190 | D3: clean digest mismatch does not block acknowledgement | 2 |
| T6-MUT-191 | D3: clean digest mismatch does not set divergent | 2 |
| T6-MUT-192 | D3: latest-recorded op_id predicate removed (digest checked for any clean) | 1 |
| T6-MUT-193 | D3: digest check extended to findings results (not just clean) | 1 |
| T6-MUT-194 | D3: digest form hard-coded to direct-clean (ignores actual form) | 1 |
| T6-MUT-195 | D3: digest computed over stripped+newline bytes instead of exact bytes | 6 |
| T6-MUT-196 | D3: digest check condition never true (skipped completely) | 2 |
| T6-MUT-200 | D2: conflict check removed (any replay proceeds without raising) | 3 |
| T6-MUT-NEW-ASSESS-VALIDATE | assessment contract validation removed | 0 — UNCAUGHT |
| T6-MUT-NEW-ASSESSMENT-GUARD | assessment build exception guard removed | 0 — UNCAUGHT |
| T6-MUT-NEW-D2-ASSESS-ONLY | D2: conflict check drops report body comparison | 2 |
| T6-MUT-NEW-D2-EXTRA-ASSESS | D2: extra stored assessment check removed | 0 — UNCAUGHT |
| T6-MUT-NEW-D2-STATUS | D2: conflict reduced to status comparison only | 1 |
| T6-MUT-NEW-DECODED-CS | decoded string CS check removed | 1 |
| T6-MUT-NEW-DUPID | adjudicated: duplicate finding_id check removed | 1 |
| T6-MUT-NEW-REPORT-CONTRACT | report contract validation removed | 0 — UNCAUGHT |

## Test-to-mutation map (proven cases)

Each line names every mutation that caught the case.

| Case | Catching mutations |
| --- | --- |
| `test_vi1012_no_reviewer_role_literals_in_shipped_modules` | 160 |
| `corpus[direct-clean]` | 081 085 195 110 142 |
| `corpus[adjudicated-all-refuted]` | 060 102 110 142 |
| `corpus[adjudicated-sustained]` | 102 110 142 |
| `corpus[findings-no-adjudication]` | 041 110 142 |
| `corpus[unknown-form]` | 097 101B 001 |
| `corpus[content-safety-refused]` | 097 101B |
| `corpus[safe-unmappable]` | 051 110 142 |
| `corpus[one-sided-legacy-present]` | 081 085 195 110 142 |
| `corpus[one-sided-legacy-absent]` | 095 110 142 |
| `test_vi1013_out_of_corpus_input_refused` | 097 001 |
| `test_vi1013_crash_before_acknowledgement_is_idempotent` | 081 085 095 195 102 103 110 111 120 124 |
| `test_vi1013_loop_engine_caller_exists` | 150 |
| `test_vi1018_authority_isolation` | 110 150 165 |
| `test_vi1018_initial_plan_review_not_consumed_as_task_approval` | 161 |
| `test_vi1018_no_mutable_task_projection_api` | 162 |
| `test_vi1019_self_containment` | 060 102 110 164 |
| `test_vi1019_spy_detects_contracts_delivery_access` | 060 102 110 |
| `test_vi1019_static_import_check` | 163 |
| `test_c1_structural_clean_rejects_findings_text` | 030 100 101B |
| `test_c1_structural_clean_accepts_exact_clean_text` | 032 110 |
| `test_c2_sustained_finding_produces_findings_result_not_eligible` | 071 074 102 110 |
| `test_c2_all_refuted_produces_acceptance_eligible` | 060 073 102 110 112 117 |
| `test_c2_id_mismatch_produces_indeterminate` | 056 110 |
| `test_c2_bad_decision_produces_indeterminate` | 059 110 |
| `test_c3_transition_history_clean_acknowledged` | 081 085 195 110 140 143 |
| `test_c3_transition_history_divergent` | 081 084 091 093 110 140 143 |
| `test_c4_crash_recovery_writes_missing_assessments` | 060 103 110 111 112 117 120 122 124 |
| `test_c5_grammar_invalid_findings_produces_unable` | 040 100 101B |
| `test_c6_return_value_has_required_fields` | 102 103 110 111 124 140 |
| `test_t4_010_content_safety_refusal_returns_unable` | 101B 010 011B |
| `test_t4_011_adjudication_text_content_safety_returns_unable` | 101B |
| `test_t4_020_direct_clean_requires_sentinel_text` | 020 021 022 023 100 101B |
| `test_t4_021_022_d1_byte_equality_rejects_trailing_newline` | 020 021 022 023 100 101B |
| `test_t4_023_d1_byte_equality_rejects_prefix_match` | 020 023 100 101B |
| `test_t4_031_structural_clean_rejects_not_checked_footer` | 031 032 100 101B |
| `test_t4_050_adjudicated_none_adjudication_returns_indeterminate` | 050 110 |
| `test_t4_052_adjudicated_empty_finding_list_returns_indeterminate` | 052 110 |
| `test_t4_053_schema_invalid_finding_returns_unable_and_persists_nothing` | 100 101B |
| `test_t4_053b_unknown_major_finding_returns_unable` | 100 101B |
| `test_t4_054_non_json_adjudication_returns_indeterminate` | 054 110 |
| `test_t4_055_audit_not_dict_returns_indeterminate` | 055 110 |
| `test_t4_057_extra_audit_id_returns_indeterminate` | 056 057 110 |
| `test_t4_058_audit_entry_not_dict_returns_indeterminate` | 058 110 |
| `test_t4_061_empty_authority_ref_returns_indeterminate` | 061 110 |
| `test_t4_070_sustained_produces_supported_assessment` | 070 071 074 102 110 112 117 |
| `test_t4_072_refuted_material_produces_unsupported_opinion_and_eligible` | 060 072 073 102 110 112 117 |
| `test_t4_080_operation_id_sets_legacy_present` | 080 110 143 |
| `test_t4_082_different_transition_id_no_legacy_present` | 082 095 110 166 |
| `test_t4_083_unrecognised_event_no_legacy_present` | 083 095 110 |
| `test_t4_090_clean_legacy_with_findings_result_not_acknowledged` | 081 085 090 093 102 110 140 |
| `test_t4_092_findings_legacy_with_findings_result_acknowledged` | 060 081 084 092 193 102 110 140 |
| `test_t4_094_op_id_only_state_is_not_divergent` | 094 110 140 |
| `test_t4_098_indeterminate_never_acknowledged_against_legacy_clean` | 041 081 085 090 093 098 110 140 |
| `test_t4_101_structured_present_on_unable_reads_store` | 101 102 110 111 124 |
| `test_t4_104_early_store_lookup_enables_conflict_detection` | 102 104 110 111 124 200 |
| `test_t4_116_assessments_scoped_to_report` | 060 102 110 112 116 117 120 124 |
| `test_t4_120_123_deterministic_ids` | 060 102 110 112 117 120 122 |
| `test_t4_130_temp_dir_under_store_root` | 033 110 130 |
| `test_t4_131_temp_dir_removed_after_classification` | 110 131 |
| `test_t4_132_store_without_root_returns_unable` | 101B 132 |
| `test_t4_133_classifier_io_failure_returns_unable` | 030 033 133 134 |
| `test_t4_141_return_value_has_exactly_six_keys` | 110 140 141 |
| `test_t4_141b_unable_key_set_is_closed` | 141B 001 |
| `test_t4_151_caller_passes_legacy_state` | 081 085 195 110 150 151 154 |
| `test_t4_152_caller_passes_source_event` | 102 110 150 152 |
| `test_t4_166_legacy_state_not_mutated` | 110 166 |
| `test_t4_192_d3_digest_check_skipped_for_older_event` | 081 085 192 110 166 |
| `test_t4_194_d3_digest_computed_over_form` | 032 081 085 194 195 110 140 |
| `test_t4_200_205_d2_conflict_guard` | 102 104 110 111 124 143 200 NEW-D2-ASSESS-ONLY |
| `test_d3_clean_digest_mismatch_is_divergent[unrelated-digest]` | 081 085 190 191 196 110 140 |
| `test_d3_clean_digest_mismatch_is_divergent[wrong-form-digest]` | 081 085 190 191 196 110 140 |
| `test_validate_before_write_refusals_persist_nothing[escaped-ctrl-in-finding]` | 100 101B |
| `test_validate_before_write_refusals_persist_nothing[escaped-ctrl-in-authority-ref]` | 060 101B NEW-DECODED-CS |
| `test_validate_before_write_refusals_persist_nothing[duplicate-finding-id]` | NEW-DUPID 100 101B |
| `test_validate_before_write_refusals_persist_nothing[wrong-type-field]` | 100 101B |
| `test_unusable_store_root_is_unable_for_direct_clean[missing]` | 132 132B |
| `test_unusable_store_root_is_unable_for_direct_clean[file]` | 132 132B |
| `test_same_status_replay_with_different_findings_conflicts` | 060 102 104 110 111 124 200 NEW-D2-STATUS NEW-D2-ASSESS-ONLY |

## NOT PROVEN

No mutation of `_review_compat.py` or the loop-engine caller can red these four cases.

- `test_vi1012_clean_report_reaches_acceptance_eligible` and `test_vi1012_unsupported_findings_report_reaches_acceptance_eligible`. Shape: **unreachable path.** Both drive `_review_persistence`, `_review_assessment`, `_review_bridge`, and `_review_disposition` directly without calling the compat adapter. Their subject is outside the mutation scope. They can be proven only by mutating those modules.
- `test_vi1019_package_check_detects_violation`. Shape: **unreachable path.** The test exits at the package check before loading any review module. Its outcome depends only on the stub `agentbundle` on `PYTHONPATH`. It proves the harness mechanism, not the compat adapter runtime.
- `test_vi1019_static_check_detects_agentbundle_import`. Shape: **unreachable path.** It appends `import agentbundle` to a copy of the source and scans the copy. The scanner catches any Python file that parses. No compat adapter mutation changes the scan result. It proves the scanner, not the runtime.

## UNCAUGHT GUARD

### (i) Reachable but untested: 8 mutations

These guards are reachable with real inputs, but no current test sends the specific input that would distinguish the guarded code from the removed code.

| Mutation | Guard removed | Single catching input | Baseline | Under mutation |
| --- | --- | --- | --- | --- |
| 113 | crash recovery dedup: `if assessment_id in stored_assessments: continue` | Partial-crash replay where at least one assessment is already stored. Assert each assessment is written exactly once (e.g., spy the bridge). | Each assessment written once. | Already-stored assessments re-written. Wrong if the store rejects duplicate assessment writes; silent if it accepts them. |
| 114 | same guard, alternative formulation | Same as 113. | Same. | Same. |
| 121 | report `transaction_id` determinism | Replay the same event. Assert `transaction_id` equals `compat-tx:{event_id}:report`. | Deterministic. | Random; idempotency depends on the transaction_id. |
| 123 | assessment `transaction_id` determinism | Same event, assert each assessment transaction_id is deterministic. | Deterministic. | Random. |
| 153 | `review_policy` pass-through from caller | A policy that the adapter reads and acts on (if any). | Policy forwarded. | Empty dict forwarded. |
| NEW-ASSESS-VALIDATE | assessment contract validation (`validate_review_record_dict` on each assessment) | An assessment that passes earlier checks but fails the contract schema (e.g., a missing required assessment field). | `unable`, 0 records. | Malformed assessment stored. Wrong. |
| NEW-D2-EXTRA-ASSESS | D2 check: `not set(stored_assessments) <= {a["assessment_id"] for a in assessments}` | Replay where stored_assessments has an extra ID not in the new request. | Conflict, raises. | No conflict detected. Wrong. |
| NEW-REPORT-CONTRACT | report contract validation (`validate_review_record_dict` on report) | A report that passes earlier checks but fails the contract schema. | `unable`, 0 records. | Malformed report stored. Wrong. |

### (ii) Two sufficient mechanisms: 2 mutations

- **011** (raw CS loop skips `adjudication_text`). Two independent mechanisms protect `test_t4_011`: (A) the raw CS loop checks `adjudication_text` as raw bytes and catches any literal credential; (B) the decoded string CS check catches the same credential after JSON decode as a string value in `authority_ref`. Removing A alone (MUT-011) still leaves B; removing B alone (MUT-NEW-DECODED-CS) still leaves A. Only removing both catches the test. A compound mutation would prove it.
- **053** (validate_finding_dict removed). Two independent mechanisms protect `test_t4_053_schema_invalid_finding_returns_unable_and_persists_nothing`: (A) `validate_finding_dict` returns False, causing `_classify_adjudicated` to return `("unable", [], [])`; (B) if A is removed, the finding (missing `rule_ref`) proceeds to `_build_all_assessments`, which does `{f["rule_ref"] for f in findings}` → `KeyError` → caught by `except Exception: return _unable()`. Removing A alone still activates B.

### (iii) Absence something else guarantees: 2 mutations

- **096** (absent-legacy short-circuit: `if not legacy_present: return False, False`). Immediately following this guard is `if legacy_event is None: return False, False`. When `legacy_present` is False, `legacy_event` is always None (the two are set together from the same history lookup). Removing the first guard changes nothing: the second guard fires on every input that the first would have caught.
- **NEW-ASSESSMENT-GUARD** (exception guard around `_build_all_assessments`). Under current test inputs, all invalid findings are caught by `validate_finding_dict` before the build phase. The `except Exception: return _unable()` path is never reached by any test. Removing it changes no observable result for any current test.

## Runtime defects

None. All five defects from ledger-2 (N1–N5) are resolved:

- **N1 (conflict return has seven keys).** The D2 path now raises `ReviewCompatRefused` instead of returning a dict. `test_t4_200_205_d2_conflict_guard` covers the raise and its parameters.
- **N2 (partial write, then raise).** Validate-before-write now catches the escaped-control-char and duplicate-finding-id inputs before any write. `test_validate_before_write_refusals_persist_nothing[escaped-ctrl-in-authority-ref]` and `[duplicate-finding-id]` pin this.
- **N3 (JSON-escaped control character bypasses raw CS).** The decoded string CS check now catches escaped control characters in string values. `test_validate_before_write_refusals_persist_nothing[escaped-ctrl-in-finding]` and `[escaped-ctrl-in-authority-ref]` pin this.
- **N4 (same-status replay with different finding set raises).** The comprehensive D2 check now covers report body and all assessments. `test_same_status_replay_with_different_findings_conflicts` pins this.
- **N5 (missing root directory raises on direct-clean).** The `is_dir()` guard (MUT-132B) now catches both a missing-directory root and a file-path root before classification. `test_unusable_store_root_is_unable_for_direct_clean[missing]` and `[file]` pin this.

## Restored baseline

Both hashes equal the baseline after all runs. `python3 -m pytest packs/core/tests/skills/work-loop/test_review_compat.py -q -p no:cacheprovider`: **83 passed in 4.43s**.
