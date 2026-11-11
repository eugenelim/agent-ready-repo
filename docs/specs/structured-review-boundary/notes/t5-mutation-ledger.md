# T5 mutation evidence

Status: incomplete. 37 of the 53 T5 target cases are proven by at least one counted single-property mutation: 36 of the 52 cases in `test_review_disposition.py`, and the one persistence case that routes a disposition through the typed port. Sixteen cases are NOT PROVEN; each is explained below. 84 counted single-property mutations ran; 35 caught at least one case and 49 survived every case. Eight compound diagnostic runs (`T5-DIAG-1` to `T5-DIAG-8`) are evidence for the NOT PROVEN analysis only and do not count. Both runtime hashes matched the frozen baseline after every run. On the restored baseline, `test_review_disposition.py` passed 52 in 1.40 s, `test_review_persistence.py` 33 in 3.65 s, `test_review_bridge.py` 50 in 1.35 s, and `test_evidence_store.py` 110 in 1.91 s.

Three guards named in the task have no code in the mutable runtime, so no mutation can exist for them. A probe confirmed each one is missing: an approval with `decision: "superseded"`, a disposition whose `decision_maker.role` differs from the approval's `authority.role`, and an accept-risk disposition carrying `replacement_report_id` are all admitted, and all three close the finding and make the review acceptance-eligible. See [Absent guards](#absent-guards).

## Scope and method

Targets: the 52 parametrized cases of `packs/core/tests/skills/work-loop/test_review_disposition.py` and `test_review_persistence.py::test_all_six_review_record_families_round_trip_through_batch_port`. A grep for `disposition` across `test_review_persistence.py` finds only this one case that routes dispositions through the typed port. It carries two disposition steps: a raw-batch refusal and a typed-port admission. The task brief expected two persistence cases; only one exists.

The exact command for each run, from the execution root, is `python3 -m pytest packs/core/tests/skills/work-loop/test_review_disposition.py "packs/core/tests/skills/work-loop/test_review_persistence.py::test_all_six_review_record_families_round_trip_through_batch_port" -q -p no:cacheprovider --tb=long --junitxml=<scratch>`. Every mutation reports its whole catching set across all 53 cases.

A catch requires exit 1 and a runtime failure inside a test body of one of four kinds:

- an `assert` failure, including a wrong denial code;
- a `pytest.raises` that did not raise (`DID NOT RAISE`);
- a different exception inside a `pytest.raises` block (refusal-type mismatch);
- the code under test raising in a test that asserts success (`unexpected-raise`). The helper counts this only when the failing test-body statement calls the port, readiness, `disposition_closes`, a store open, or a raw `append_semantic_records`. It does not count a raise from setup helpers (`_setup_report_and_assessment`, report persistence, or the assessment bridge).

Collection, import, syntax, fixture-setup, and timeout failures are excluded. None occurred.

Each mutation is one exact-string replacement in one runtime file. A scratch helper asserts the old string occurs exactly once and the new string exactly once, and it never applies an empty replacement. Restoration is the inverse exact replacement, followed by a sha256 check of both runtime files. Mutable files: `_review_disposition.py` and `_evidence_store.py` (disposition, approval, readiness, and authority-scope code only). No test, spec, or plan file was edited. The scratch registry and results are in `$HOME/.slice2-scratch/t5-mut/`, outside the repository.

**Restoration incident.** The first attempt at compound `T5-DIAG-3` applied T5-MUT-030 and T5-MUT-031 together. Both new strings were identical text, so the helper's uniqueness check stopped the run before pytest started. The automatic inverse edit then could not find a unique string, and `_evidence_store.py` was left at sha256 `7089a842…`. Both lines were restored by exact inverse edits keyed on their distinct message lines, and the hash returned to `6014d514…`. No test ran in the mutated state. The helper now checks every replacement in memory before writing anything. `T5-DIAG-3` was rerun with distinct strings (`if False and not …`).

Baseline sha256, verified before the first run, after every run, and at the end:

| File | sha256 |
| --- | --- |
| `_evidence_store.py` | `6014d514aa94c1b774578eae810bd511e333af13135b637fa55e32998c36b041` |
| `_review_disposition.py` | `7a3f7c28d0bc9d4cbb26722c4d7520688c904fda60a4e1676fe8dabf9b9a7604` |

## Completed checks

| Mutation | Guarded behavior | Catching cases |
| --- | --- | ---: |
| T5-MUT-001 | finding-disposition lifecycle selects the review/disposition capability scope | 23 |
| T5-MUT-002 | an out-of-scope grant (authority not allowed) refuses | 2 |
| T5-MUT-003 | a None / non-grant object refuses with denied-invalid-grant | 0 |
| T5-MUT-004 | an unavailable audit sink at the authority check fails closed | 3 |
| T5-MUT-010 | port refuses a schema-invalid approval record | 0 |
| T5-MUT-011 | port rule 2: lineage.authority_ref equals approval_id | 0 |
| T5-MUT-012 | port rule 3: decision_maker.identity equals approval authority.identity | 0 |
| T5-MUT-013 | port rule 4: approval base.manifest_ref equals the current subject fingerprint | 2 |
| T5-MUT-014 | port rule 4: approval spec_policy_fingerprint equals the subject policy fingerprint | 2 |
| T5-MUT-015 | port rule 5: fixed-by needs a non-empty replacement_report_id | 0 |
| T5-MUT-016 | eligibility: the referenced assessment must be durable | 0 |
| T5-MUT-017 | eligibility: the referenced assessment must be supported | 1 |
| T5-MUT-018 | eligibility: assessment subject fingerprint equals the disposition subject (subject equality) | 0 |
| T5-MUT-019 | eligibility: the assessment source report must be durable | 0 |
| T5-MUT-020 | eligibility: the finding must be in the source report | 0 |
| T5-MUT-021 | eligibility: only material findings can be disposed | 1 |
| T5-MUT-022 | port converts store refusals into its own ReviewDispositionRefused | 8 |
| T5-MUT-030 | raw batch path refuses approval-record records | 0 |
| T5-MUT-031 | an approval must be paired with a disposition in the same frame | 1 |
| T5-MUT-032 | a superseding approval keeps the predecessor's authority role | 0 |
| T5-MUT-033 | raw batch path refuses finding-disposition records | 2 |
| T5-MUT-034 | store: a disposition needs a durable or in-frame approval | 0 |
| T5-MUT-035 | store rule 1: approval decision_scope is review-disposition | 4 |
| T5-MUT-036 | store rule 2: authority_ref equals approval_id | 0 |
| T5-MUT-037 | store rule 3: decision_maker identity equals approval identity | 0 |
| T5-MUT-038 | store rule 4 runs when the review subject is durable | 0 |
| T5-MUT-039 | store rule 4: approval manifest_ref equals the disposition subject | 0 |
| T5-MUT-040 | store rule 4: approval policy equals the durable subject policy | 0 |
| T5-MUT-041 | store rule 5: fixed-by needs a non-empty replacement id | 0 |
| T5-MUT-042 | store rule 5: the fixed-by replacement report must be durable | 1 |
| T5-MUT-043 | store rule 5: the replacement subject fingerprint differs | 1 |
| T5-MUT-044 | a durable approval id with a different body refuses | 0 |
| T5-MUT-045 | accept-risk does not supersede the contradicting bridge receipts | 7 |
| T5-MUT-046 | a new approval is persisted in the disposition frame | 13 |
| T5-MUT-050 | a lifecycle refusal after allow emits a paired denial with the same operation id | 3 |
| T5-MUT-051 | a reused lifecycle transaction id is either an exact retry or refused | 2 |
| T5-MUT-052 | an identical disposition retry is recognized as the committed transaction | 1 |
| T5-MUT-053 | disposition retry: the disposition id must be in the committed frame | 0 |
| T5-MUT-054 | disposition retry: the disposition body equals the committed body | 0 |
| T5-MUT-055 | disposition retry: an in-frame approval body equals the committed approval | 0 |
| T5-MUT-056 | replay re-runs the review transition checker on every frame | 1 |
| T5-MUT-057 | replay admits disposition frames under the full rule check | 2 |
| T5-MUT-058 | the lifecycle path admits disposition frames under the full rule check | 18 |
| T5-MUT-060 | closes: disposition subject equals the queried subject | 0 |
| T5-MUT-061 | closes: paired approval must be durable | 0 |
| T5-MUT-062 | closes: a superseded approval (named as predecessor) stops closing | 1 |
| T5-MUT-063 | closes: approval scope is review-disposition | 0 |
| T5-MUT-064 | closes: decision_maker identity equals approval identity | 0 |
| T5-MUT-065 | closes: the referenced assessment must be durable | 0 |
| T5-MUT-066 | closes: the assessment key must be current (tip + exact receipts) | 0 |
| T5-MUT-067 | closes: the disposition's assessment is the latest for the finding | 1 |
| T5-MUT-068 | closes: a current accept-risk closes | 3 |
| T5-MUT-069 | closes fixed-by: non-empty replacement id | 0 |
| T5-MUT-070 | closes fixed-by: replacement must be durable | 0 |
| T5-MUT-071 | closes fixed-by: replacement subject fingerprint differs | 0 |
| T5-MUT-072 | closes fixed-by: original report must be durable | 0 |
| T5-MUT-073 | closes fixed-by: replacement has the same role | 0 |
| T5-MUT-074 | closes fixed-by: replacement shares the delivery subject id | 0 |
| T5-MUT-075 | closes fixed-by: replacement is the current tip | 1 |
| T5-MUT-076 | closes fixed-by: replacement admitted after the assessment | 0 |
| T5-MUT-077 | closes fixed-by: every replacement finding has a current assessment | 0 |
| T5-MUT-078 | closes fixed-by: no replacement assessment is indeterminate | 1 |
| T5-MUT-079 | closes fixed-by: a supported same-failure replacement assessment stops closing | 1 |
| T5-MUT-080 | closes fixed-by: only a SAME actual_failure blocks (equality clause) | 0 |
| T5-MUT-081 | closes fixed-by: an empty original failure never matches | 0 |
| T5-MUT-082 | closes: repair-request (any other kind) never closes | 2 |
| T5-MUT-090 | current assessments: only the current report tip counts | 0 |
| T5-MUT-091 | current assessments: a supported entry needs the exact active receipt set | 0 |
| T5-MUT-092 | current assessments: the latest assessment per finding wins | 1 |
| T5-MUT-093 | current assessments: a non-supported entry needs no active derived receipts | 0 |
| T5-MUT-094 | current assessments: scoped to the queried subject fingerprint | 0 |
| T5-MUT-100 | readiness: a blocking (mandatory unsatisfied) obligation clears eligibility | 1 |
| T5-MUT-101 | readiness: only blocking decisions clear eligibility (waived role does not) | 6 |
| T5-MUT-102 | readiness: any open finding (incl. optional role) clears eligibility | 0 |
| T5-MUT-103 | readiness: verified closure flips an open-finding obligation to satisfied-findings | 5 |
| T5-MUT-104 | readiness obligation recompute re-verifies each disposition via disposition_closes | 0 |
| T5-MUT-105 | readiness open findings re-verify each disposition via disposition_closes | 5 |
| T5-MUT-106 | readiness recompute skips only non-supported assessments | 0 |
| T5-MUT-107 | readiness open findings: only material findings are open | 0 |
| T5-MUT-108 | readiness open findings: only supported assessments are open | 0 |
| T5-MUT-109 | readiness: dispositions scoped to the target subject | 0 |
| T5-MUT-110 | readiness: assessments scoped to the target subject | 0 |
| T5-MUT-111 | readiness recompute only runs on a current tip | 5 |
| T5-MUT-112 | readiness open findings: a supported material finding is listed as open | 6 |
| T5-DIAG-1 | COMPOUND: port rule 2 + store no-approval (authority_ref) | 3 |
| T5-DIAG-2 | COMPOUND: port rule 3 + store rule 3 (identity) | 2 |
| T5-DIAG-3 | COMPOUND: raw-approval refusal + unpaired-approval refusal | 2 |
| T5-DIAG-4 | COMPOUND: None-grant check + authority-check exception fail-closed | 5 |
| T5-DIAG-5 | COMPOUND: port manifest_ref + store replacement durability | 4 |
| T5-DIAG-6 | COMPOUND: port policy fp + store replacement durability | 4 |
| T5-DIAG-7 | COMPOUND: scope selection + store replacement durability | 24 |
| T5-DIAG-8 | COMPOUND: obligation block + open-findings block | 8 |

`T5-DIAG-1` to `T5-DIAG-8` are compound diagnostics. Each applies two counted mutations at once. None is a single-property mutation, so none counts toward proof.

## Mutation details

Snippets are whitespace-collapsed (`⏎` marks a newline) and long ones are cut with `…`. The exact old and new strings are in the scratch registry `$HOME/.slice2-scratch/t5-mut/mutations.py`. "@N" is the test-file line of the failing statement.

| Mutation | File | Exact mutation (old → new) | Observed catching cases | Restored hash |
| --- | --- | --- | --- | --- |
| T5-MUT-001 | `_evidence_store.py` | `"review/disposition"⏎ if _lifecycle_kind_peek == "finding-disposition"` → `"evidence"⏎ if _lifecycle_kind_peek == "finding-disposition"` | 23 cases: assertion, did-not-raise, unexpected-raise; incl. `test_repair_request_admitted_but_finding_stays_open` @430; `test_accept_risk_closes_review_and_contradiction_preserved` @481; `test_fixed_by_closes_on_replacement_subject` @595 … | OK |
| T5-MUT-002 | `_evidence_store.py` | `if not allowed:⏎ raise EvidenceStoreRefused(⏎ "denied-producer-authority",` → `if False:⏎ raise EvidenceStoreRefused(⏎ "denied-producer-authority",` | `test_evidence_only_grant_refused_out_of_scope[repair-request]` @1017 (did-not-raise); `test_evidence_only_grant_refused_out_of_scope[accept-risk]` @1017 (did-not-raise) | OK |
| T5-MUT-003 | `_evidence_store.py` | `if grant is None or not hasattr(grant, "grant_id"):` → `if False:` | none — survived | OK |
| T5-MUT-004 | `_evidence_store.py` | `except Exception as exc: # noqa: BLE001 — wraps AuditSinkUnavailable from any module load⏎ raise EvidenceStoreRefused(⏎ "denied-audit-sink-u…` → `except Exception as exc: # noqa: BLE001 — wraps AuditSinkUnavailable from any module load⏎ allowed = True⏎` | `test_audit_sink_unavailable_refused_no_effect[repair-request]` @1097 (did-not-raise); `test_audit_sink_unavailable_refused_no_effect[fixed-by]` @1110 (assertion); `test_audit_sink_unavailable_refused_no_effect[accept-risk]` @1097 (did-not-raise) | OK |
| T5-MUT-010 | `_review_disposition.py` | `ok, code = _policy_import().validate_approval_dict(safe_approval)⏎ if not ok:` → `ok, code = _policy_import().validate_approval_dict(safe_approval)⏎ if False:` | none — survived | OK |
| T5-MUT-011 | `_review_disposition.py` | `if authority_ref != approval_record.get("approval_id", ""):` → `if False:` | none — survived | OK |
| T5-MUT-012 | `_review_disposition.py` | `if maker_identity != approval_identity:` → `if False:` | none — survived | OK |
| T5-MUT-013 | `_review_disposition.py` | `if approval_record.get("base", {}).get("manifest_ref", "") != subject_fp:` → `if False:` | `test_subject_manifest_ref_mismatch_refused[repair-request]` @979 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[accept-risk]` @979 (did-not-raise) | OK |
| T5-MUT-014 | `_review_disposition.py` | `if approval_record.get("spec_policy_fingerprint", "") != policy_fp:` → `if False:` | `test_policy_fingerprint_mismatch_refused[repair-request]` @942 (did-not-raise); `test_policy_fingerprint_mismatch_refused[accept-risk]` @942 (did-not-raise) | OK |
| T5-MUT-015 | `_review_disposition.py` | `if disposition.get("disposition") == "fixed-by" and not disposition.get(⏎ "replacement_report_id"⏎ ):` → `if False and not disposition.get(⏎ "replacement_report_id"⏎ ):` | none — survived | OK |
| T5-MUT-016 | `_review_disposition.py` | `if target_assessment is None:⏎ _refuse(⏎ "denied-disposition-no-assessment",` → `if False:⏎ _refuse(⏎ "denied-disposition-no-assessment",` | none — survived | OK |
| T5-MUT-017 | `_review_disposition.py` | `if target_assessment.get("assessment") != "supported": # type: ignore[union-attr]` → `if False: # type: ignore[union-attr]` | `test_unsupported_assessment_cannot_be_disposed` @1215 (did-not-raise) | OK |
| T5-MUT-018 | `_review_disposition.py` | `if target_assessment.get("review_subject_fingerprint") != review_subject_fingerprint: # type: ignore[union-attr]` → `if False: # type: ignore[union-attr]` | none — survived | OK |
| T5-MUT-019 | `_review_disposition.py` | `if source_report is None:⏎ _refuse(⏎ "denied-disposition-no-report",` → `if False:⏎ _refuse(⏎ "denied-disposition-no-report",` | none — survived | OK |
| T5-MUT-020 | `_review_disposition.py` | `if source_finding is None:⏎ _refuse(⏎ "denied-disposition-no-finding",` → `if False:⏎ _refuse(⏎ "denied-disposition-no-finding",` | none — survived | OK |
| T5-MUT-021 | `_review_disposition.py` | `if not source_finding.get("material", False): # type: ignore[union-attr]` → `if False: # type: ignore[union-attr]` | `test_nonmaterial_finding_cannot_be_disposed` @1287 (did-not-raise) | OK |
| T5-MUT-022 | `_review_disposition.py` | `if denial_code is not None:⏎ raise ReviewDispositionRefused(denial_code, str(exc)) from exc` → `if False:⏎ raise ReviewDispositionRefused(denial_code, str(exc)) from exc` | 8 cases: refusal-type-mismatch; incl. `test_fixed_by_without_replacement_report_stays_open[True]` @655; `test_fixed_by_same_subject_fingerprint_refused` @706; `test_wrong_decision_scope_refused[repair-request]` @829 … | OK |
| T5-MUT-030 | `_evidence_store.py` | `if not check_disposition_rules:⏎ raise EvidenceStoreRefused(⏎ "denied-approval-authority-required",` → `if False:⏎ raise EvidenceStoreRefused(⏎ "denied-approval-authority-required",` | none — survived | OK |
| T5-MUT-031 | `_evidence_store.py` | `if not frame_dispositions:⏎ raise EvidenceStoreRefused(⏎ "denied-approval-authority-required",` → `if False:⏎ raise EvidenceStoreRefused(⏎ "denied-approval-authority-required",` | `test_replayed_raw_approval_frame_refuses_on_open` @2359 (did-not-raise) | OK |
| T5-MUT-032 | `_evidence_store.py` | `if _pred is not None and (` → `if False and (` | none — survived | OK |
| T5-MUT-033 | `_evidence_store.py` | `if not check_disposition_rules:⏎ raise EvidenceStoreRefused(⏎ "denied-disposition-authority-required",` → `if False:⏎ raise EvidenceStoreRefused(⏎ "denied-disposition-authority-required",` | `test_raw_batch_with_disposition_refused` @1338 (assertion); `test_all_six_review_record_families_round_trip_through_batch_port` @796 (assertion) | OK |
| T5-MUT-034 | `_evidence_store.py` | `if approval is None:⏎ raise EvidenceStoreRefused(⏎ "denied-disposition-no-approval",` → `if False:⏎ raise EvidenceStoreRefused(⏎ "denied-disposition-no-approval",` | none — survived | OK |
| T5-MUT-035 | `_evidence_store.py` | `if approval.get("decision_scope") != "review-disposition":⏎ raise EvidenceStoreRefused(` → `if False:⏎ raise EvidenceStoreRefused(` | `test_wrong_decision_scope_refused[repair-request]` @828 (did-not-raise); `test_wrong_decision_scope_refused[accept-risk]` @828 (did-not-raise); `test_post_allow_denial_has_same_operation_id[repair-request]` @1137 (did-not-raise); `test_post_allow_denial_has_same_operation_id[accept-risk]` @1137 (did-not-raise) | OK |
| T5-MUT-036 | `_evidence_store.py` | `if authority_ref != approval.get("approval_id", ""):` → `if False:` | none — survived | OK |
| T5-MUT-037 | `_evidence_store.py` | `if maker_identity != approval.get("authority", {}).get("identity", ""):` → `if False:` | none — survived | OK |
| T5-MUT-038 | `_evidence_store.py` | `if durable_subject is not None:` → `if False:` | none — survived | OK |
| T5-MUT-039 | `_evidence_store.py` | `if approval.get("base", {}).get("manifest_ref", "") != disp_fp:` → `if False:` | none — survived | OK |
| T5-MUT-040 | `_evidence_store.py` | `if approval.get("spec_policy_fingerprint", "") != durable_subject.get(` → `if False and approval.get("spec_policy_fingerprint", "") != durable_subject.get(` | none — survived | OK |
| T5-MUT-041 | `_evidence_store.py` | `if not replacement_id:⏎ raise EvidenceStoreRefused(⏎ "denied-disposition-missing-replacement",` → `if False:⏎ raise EvidenceStoreRefused(⏎ "denied-disposition-missing-replacement",` | none — survived | OK |
| T5-MUT-042 | `_evidence_store.py` | `replacement = semantic_records.get("review-report.v1", {}).get(replacement_id)` → `replacement = semantic_records.get("review-report.v1", {}).get(replacement_id, {})` | `test_fixed_by_without_replacement_report_stays_open[True]` @654 (did-not-raise) | OK |
| T5-MUT-043 | `_evidence_store.py` | `if replacement_fp == disp_fp:` → `if False:` | `test_fixed_by_same_subject_fingerprint_refused` @705 (did-not-raise) | OK |
| T5-MUT-044 | `_evidence_store.py` | `elif _canonical_json(existing_approval) != _canonical_json(approval_record):` → `elif False:` | none — survived | OK |
| T5-MUT-045 | `_evidence_store.py` | `frame.append(copy.deepcopy(seed_disposition))⏎ return frame` → `frame.append(copy.deepcopy(seed_disposition))⏎ _mut_ids = [rid for rid, r in self._receipts.items() if rid not in self._superseded and _is_b…` | 7 cases: unexpected-raise; incl. `test_accept_risk_closes_review_and_contradiction_preserved` @481; `test_identical_retry_is_idempotent` @1368; `test_changed_retry_refused` @1406 … | OK |
| T5-MUT-046 | `_evidence_store.py` | `if existing_approval is None:⏎ frame.append(copy.deepcopy(approval_record))` → `if False:⏎ frame.append(copy.deepcopy(approval_record))` | 13 cases: unexpected-raise; incl. `test_repair_request_admitted_but_finding_stays_open` @430; `test_accept_risk_closes_review_and_contradiction_preserved` @481; `test_fixed_by_closes_on_replacement_subject` @595 … | OK |
| T5-MUT-050 | `_evidence_store.py` | `return tx, composed⏎⏎ try:⏎ if _HAS_FCNTL:⏎ with _advisory_lock(self._root, self._log_path) as lock_fd:⏎ committed, committed_records = deci…` → `return tx, composed⏎⏎ try:⏎ if _HAS_FCNTL:⏎ with _advisory_lock(self._root, self._log_path) as lock_fd:⏎ committed, committed_records = deci…` | `test_post_allow_denial_has_same_operation_id[repair-request]` @1153 (assertion); `test_post_allow_denial_has_same_operation_id[fixed-by]` @1153 (assertion); `test_post_allow_denial_has_same_operation_id[accept-risk]` @1153 (assertion) | OK |
| T5-MUT-051 | `_evidence_store.py` | `if prev_tx.get("transaction_id") == transaction_id:⏎ if self._check_lifecycle_idempotent(` → `if False:⏎ if self._check_lifecycle_idempotent(` | `test_identical_retry_is_idempotent` @1374 (unexpected-raise); `test_changed_retry_refused` @1415 (did-not-raise) | OK |
| T5-MUT-052 | `_evidence_store.py` | `if _canonical_json(committed_approval) != _canonical_json(approval_record):⏎ return False⏎ return True` → `if _canonical_json(committed_approval) != _canonical_json(approval_record):⏎ return False⏎ return False` | `test_identical_retry_is_idempotent` @1374 (unexpected-raise) | OK |
| T5-MUT-053 | `_evidence_store.py` | `if disposition_id not in committed_ids:⏎ return False` → `if False:⏎ return False` | none — survived | OK |
| T5-MUT-054 | `_evidence_store.py` | `if _canonical_json(committed_disposition) != _canonical_json(disposition):⏎ return False` → `if False:⏎ return False` | none — survived | OK |
| T5-MUT-055 | `_evidence_store.py` | `if _canonical_json(committed_approval) != _canonical_json(approval_record):` → `if False:` | none — survived | OK |
| T5-MUT-056 | `_evidence_store.py` | `_validate_review_transition(⏎ records,⏎ acceptance_fingerprint=tx["acceptance_fingerprint"],` → `(lambda *a, **k: None)(⏎ records,⏎ acceptance_fingerprint=tx["acceptance_fingerprint"],` | `test_replayed_raw_approval_frame_refuses_on_open` @2359 (did-not-raise) | OK |
| T5-MUT-057 | `_evidence_store.py` | `# via the lifecycle port, and rules 1–5 are re-validated here.⏎ check_disposition_rules=True,` → `# via the lifecycle port, and rules 1–5 are re-validated here.⏎ check_disposition_rules=False,` | `test_fresh_store_reopen_yields_identical_readiness` @1523 (unexpected-raise); `test_all_six_review_record_families_round_trip_through_batch_port` @822 (unexpected-raise) | OK |
| T5-MUT-058 | `_evidence_store.py` | `# pre-validated by the typed port and composed by this store.⏎ check_disposition_rules=True,` → `# pre-validated by the typed port and composed by this store.⏎ check_disposition_rules=False,` | 18 cases: assertion, unexpected-raise; incl. `test_repair_request_admitted_but_finding_stays_open` @430; `test_accept_risk_closes_review_and_contradiction_preserved` @481; `test_fixed_by_closes_on_replacement_subject` @595 … | OK |
| T5-MUT-060 | `_evidence_store.py` | `if disposition.get("review_subject_fingerprint") != subject_fp:⏎ return False⏎⏎ # 2. Find the paired approval.` → `if False:⏎ return False⏎⏎ # 2. Find the paired approval.` | none — survived | OK |
| T5-MUT-061 | `_evidence_store.py` | `approval = self._semantic_records.get("approval-record.v1", {}).get(authority_ref)⏎ if approval is None:⏎ return False` → `approval = self._semantic_records.get("approval-record.v1", {}).get(authority_ref)⏎ if False:⏎ return False` | none — survived | OK |
| T5-MUT-062 | `_evidence_store.py` | `if _other.get("lineage", {}).get("predecessor_id") == authority_ref:⏎ return False` → `if False:⏎ return False` | `test_accept_risk_stops_closing_after_approval_superseded` @2187 (assertion) | OK |
| T5-MUT-063 | `_evidence_store.py` | `if approval.get("decision_scope") != "review-disposition":⏎ return False` → `if False:⏎ return False` | none — survived | OK |
| T5-MUT-064 | `_evidence_store.py` | `disposition.get("decision_maker", {}).get("identity")⏎ != approval.get("authority", {}).get("identity")` → `False` | none — survived | OK |
| T5-MUT-065 | `_evidence_store.py` | `if assessment is None:⏎ return False⏎ report_id = assessment.get("report_id", "")` → `if False:⏎ return False⏎ report_id = assessment.get("report_id", "")` | none — survived | OK |
| T5-MUT-066 | `_evidence_store.py` | `if entry is None:⏎ return False⏎ if entry["assessment"]` → `if False:⏎ return False⏎ if entry["assessment"]` | none — survived | OK |
| T5-MUT-067 | `_evidence_store.py` | `if entry["assessment"].get("assessment_id") != assessment_id:⏎ return False` → `if False:⏎ return False` | `test_accept_risk_stops_closing_after_assessment_replaced` @2276 (assertion) | OK |
| T5-MUT-068 | `_evidence_store.py` | `if disp_kind == "accept-risk":⏎ return True` → `if disp_kind == "accept-risk":⏎ return False` | `test_accept_risk_closes_review_and_contradiction_preserved` @530 (assertion); `test_accept_risk_stops_closing_after_approval_superseded` @2152 (assertion); `test_accept_risk_stops_closing_after_assessment_replaced` @2246 (assertion) | OK |
| T5-MUT-069 | `_evidence_store.py` | `if not replacement_id:⏎ return False⏎⏎ replacement` → `if False:⏎ return False⏎⏎ replacement` | none — survived | OK |
| T5-MUT-070 | `_evidence_store.py` | `if replacement is None:⏎ return False⏎⏎ # Replacement must belong` → `if False:⏎ return False⏎⏎ # Replacement must belong` | none — survived | OK |
| T5-MUT-071 | `_evidence_store.py` | `if replacement_fp == subject_fp:⏎ return False` → `if False:⏎ return False` | none — survived | OK |
| T5-MUT-072 | `_evidence_store.py` | `if original_report is None:⏎ return False⏎ if replacement.get("role")` → `if False:⏎ return False⏎ if replacement.get("role")` | none — survived | OK |
| T5-MUT-073 | `_evidence_store.py` | `if replacement.get("role") != original_report.get("role"):` → `if False:` | none — survived | OK |
| T5-MUT-074 | `_evidence_store.py` | `if orig_delivery_id != repl_delivery_id:` → `if False:` | none — survived | OK |
| T5-MUT-075 | `_evidence_store.py` | `if tip is None or tip.get("report_id") != replacement_id:⏎ return False` → `if False:⏎ return False` | `test_fixed_by_with_replacement_not_tip_stays_open` @1776 (assertion) | OK |
| T5-MUT-076 | `_evidence_store.py` | `if replacement_tx_idx < 0 or replacement_tx_idx <= assessment_tx_idx:` → `if False:` | none — survived | OK |
| T5-MUT-077 | `_evidence_store.py` | `return False # No current assessment for this replacement finding.` → `continue # No current assessment for this replacement finding.` | none — survived | OK |
| T5-MUT-078 | `_evidence_store.py` | `if repl_assessment.get("assessment") == "indeterminate":⏎ return False` → `if False:⏎ return False` | `test_fixed_by_stops_closing_on_indeterminate_replacement_assessment` @2090 (assertion) | OK |
| T5-MUT-079 | `_evidence_store.py` | `repl_assessment.get("assessment") == "supported"⏎ and original_failure` → `False⏎ and original_failure` | `test_fixed_by_stops_closing_on_same_failure_supported_assessment` @1937 (assertion) | OK |
| T5-MUT-080 | `_evidence_store.py` | `and original_failure⏎ and repl_finding.get("actual_failure", "") == original_failure⏎` → `and original_failure⏎` | none — survived | OK |
| T5-MUT-081 | `_evidence_store.py` | `and original_failure⏎ and repl_finding` → `and repl_finding` | none — survived | OK |
| T5-MUT-082 | `_evidence_store.py` | `return True⏎⏎ return False⏎⏎ def get_transaction` → `return True⏎⏎ return True⏎⏎ def get_transaction` | `test_repair_request_admitted_but_finding_stays_open` @448 (assertion); `test_accept_risk_stops_closing_after_approval_superseded` @2195 (assertion) | OK |
| T5-MUT-090 | `_evidence_store.py` | `if tip_report is None or tip_report.get("report_id") != report_id:⏎ continue` → `if False:⏎ continue` | none — survived | OK |
| T5-MUT-091 | `_evidence_store.py` | `if not expected_ids or expected_ids != active_ids:` → `if not expected_ids:` | none — survived | OK |
| T5-MUT-092 | `_evidence_store.py` | `latest_by_source[key] = assessment` → `latest_by_source.setdefault(key, assessment)` | `test_fixed_by_stops_closing_on_indeterminate_replacement_assessment` @2090 (assertion) | OK |
| T5-MUT-093 | `_evidence_store.py` | `if active_receipts:⏎ continue⏎ receipt_ids = []` → `if False:⏎ continue⏎ receipt_ids = []` | none — survived | OK |
| T5-MUT-094 | `_evidence_store.py` | `if assessment.get("review_subject_fingerprint") != review_subject_fingerprint:⏎ continue⏎ key =` → `if False:⏎ continue⏎ key =` | none — survived | OK |
| T5-MUT-100 | `_review_disposition.py` | `if decision.get("acceptance_block"):⏎ acceptance_eligible = False` → `if False:⏎ acceptance_eligible = False` | `test_mandatory_unsatisfied_not_eligible` @1447 (assertion) | OK |
| T5-MUT-101 | `_review_disposition.py` | `if decision.get("acceptance_block"):⏎ acceptance_eligible = False` → `if True:⏎ acceptance_eligible = False` | `test_accept_risk_closes_review_and_contradiction_preserved` @530 (assertion); `test_fixed_by_closes_on_replacement_subject` @613 (assertion); `test_waived_obligation_does_not_block` @1570 (assertion); `test_verified_fixed_by_obligation_decision_is_satisfied_findings` @1664 (assertion); `test_fixed_by_stops_closing_on_same_failure_supported_assessment` @1908 (assertion); `test_accept_risk_stops_closing_after_approval_superseded` @2160 (assertion) | OK |
| T5-MUT-102 | `_review_disposition.py` | `if open_findings:⏎ acceptance_eligible = False` → `if False:⏎ acceptance_eligible = False` | none — survived | OK |
| T5-MUT-103 | `_review_disposition.py` | `if all_closed:⏎ decision = {` → `if False:⏎ decision = {` | `test_accept_risk_closes_review_and_contradiction_preserved` @530 (assertion); `test_fixed_by_closes_on_replacement_subject` @613 (assertion); `test_verified_fixed_by_obligation_decision_is_satisfied_findings` @1660 (assertion); `test_fixed_by_stops_closing_on_same_failure_supported_assessment` @1908 (assertion); `test_accept_risk_stops_closing_after_approval_superseded` @2160 (assertion) | OK |
| T5-MUT-104 | `_review_disposition.py` | `store.disposition_closes(d.get("disposition_id", ""), review_subject)⏎ for d in dispositions⏎ if d.get("finding_id") == finding_id_loop` → `True⏎ for d in dispositions⏎ if d.get("finding_id") == finding_id_loop` | none — survived | OK |
| T5-MUT-105 | `_review_disposition.py` | `store.disposition_closes(d.get("disposition_id", ""), review_subject)⏎ for d in dispositions⏎ if d.get("finding_id") == finding_id⏎` → `True⏎ for d in dispositions⏎ if d.get("finding_id") == finding_id⏎` | `test_repair_request_admitted_but_finding_stays_open` @450 (assertion); `test_fixed_by_with_replacement_not_tip_stays_open` @1779 (assertion); `test_fixed_by_stops_closing_on_same_failure_supported_assessment` @1948 (assertion); `test_fixed_by_stops_closing_on_indeterminate_replacement_assessment` @2101 (assertion); `test_accept_risk_stops_closing_after_approval_superseded` @2198 (assertion) | OK |
| T5-MUT-106 | `_review_disposition.py` | `if finding_assessment.get("assessment") != "supported":⏎ continue` → `if False:⏎ continue` | none — survived | OK |
| T5-MUT-107 | `_review_disposition.py` | `if finding is None or not finding.get("material", False):` → `if finding is None:` | none — survived | OK |
| T5-MUT-108 | `_review_disposition.py` | `if assessment.get("assessment") != "supported":⏎ continue⏎ source_report = next(` → `if False:⏎ continue⏎ source_report = next(` | none — survived | OK |
| T5-MUT-109 | `_review_disposition.py` | `if d.get("review_subject_fingerprint") == review_subject_fingerprint⏎ ]` → `if True⏎ ]` | none — survived | OK |
| T5-MUT-110 | `_review_disposition.py` | `if a.get("review_subject_fingerprint") == review_subject_fingerprint⏎ ]` → `if True⏎ ]` | none — survived | OK |
| T5-MUT-111 | `_review_disposition.py` | `if tip is not None:⏎ all_closed = True` → `if tip is not None and False:⏎ all_closed = True` | `test_accept_risk_closes_review_and_contradiction_preserved` @530 (assertion); `test_fixed_by_closes_on_replacement_subject` @613 (assertion); `test_verified_fixed_by_obligation_decision_is_satisfied_findings` @1660 (assertion); `test_fixed_by_stops_closing_on_same_failure_supported_assessment` @1908 (assertion); `test_accept_risk_stops_closing_after_approval_superseded` @2160 (assertion) | OK |
| T5-MUT-112 | `_review_disposition.py` | `if finding is None or not finding.get("material", False):` → `if finding is None or finding.get("material", False):` | `test_repair_request_admitted_but_finding_stays_open` @450 (assertion); `test_open_supported_finding_blocks_eligibility` @1483 (assertion); `test_fixed_by_with_replacement_not_tip_stays_open` @1779 (assertion); `test_fixed_by_stops_closing_on_same_failure_supported_assessment` @1948 (assertion); `test_fixed_by_stops_closing_on_indeterminate_replacement_assessment` @2101 (assertion); `test_accept_risk_stops_closing_after_approval_superseded` @2198 (assertion) | OK |
| T5-DIAG-1 | `_evidence_store.py+_review_disposition.py` | compound: T5-MUT-011+T5-MUT-034 | `test_authority_ref_mismatch_refused[repair-request]` @868 (refusal-type-mismatch); `test_authority_ref_mismatch_refused[fixed-by]` @868 (refusal-type-mismatch); `test_authority_ref_mismatch_refused[accept-risk]` @868 (refusal-type-mismatch) | OK |
| T5-DIAG-2 | `_evidence_store.py+_review_disposition.py` | compound: T5-MUT-012+T5-MUT-037 | `test_identity_mismatch_refused[repair-request]` @905 (did-not-raise); `test_identity_mismatch_refused[accept-risk]` @905 (did-not-raise) | OK |
| T5-DIAG-3 | `_evidence_store.py` | compound: T5-MUT-030+T5-MUT-031 | `test_raw_approval_write_refused_and_store_reopens` @2311 (did-not-raise); `test_replayed_raw_approval_frame_refuses_on_open` @2359 (did-not-raise) | OK |
| T5-DIAG-4 | `_evidence_store.py` | compound: T5-MUT-003+T5-MUT-004 | `test_invalid_grant_refused[repair-request]` @1058 (did-not-raise); `test_invalid_grant_refused[accept-risk]` @1058 (did-not-raise); `test_audit_sink_unavailable_refused_no_effect[repair-request]` @1097 (did-not-raise); `test_audit_sink_unavailable_refused_no_effect[fixed-by]` @1110 (assertion); `test_audit_sink_unavailable_refused_no_effect[accept-risk]` @1097 (did-not-raise) | OK |
| T5-DIAG-5 | `_evidence_store.py+_review_disposition.py` | compound: T5-MUT-013+T5-MUT-042 | `test_fixed_by_without_replacement_report_stays_open[True]` @654 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[repair-request]` @979 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[fixed-by]` @979 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[accept-risk]` @979 (did-not-raise) | OK |
| T5-DIAG-6 | `_evidence_store.py+_review_disposition.py` | compound: T5-MUT-014+T5-MUT-042 | `test_fixed_by_without_replacement_report_stays_open[True]` @654 (did-not-raise); `test_policy_fingerprint_mismatch_refused[repair-request]` @942 (did-not-raise); `test_policy_fingerprint_mismatch_refused[fixed-by]` @942 (did-not-raise); `test_policy_fingerprint_mismatch_refused[accept-risk]` @942 (did-not-raise) | OK |
| T5-DIAG-7 | `_evidence_store.py` | compound: T5-MUT-001+T5-MUT-042 | 24 cases: assertion, did-not-raise, unexpected-raise; incl. `test_repair_request_admitted_but_finding_stays_open` @430; `test_accept_risk_closes_review_and_contradiction_preserved` @481; `test_fixed_by_closes_on_replacement_subject` @595 … | OK |
| T5-DIAG-8 | `_review_disposition.py` | compound: T5-MUT-100+T5-MUT-102 | 8 cases: assertion; incl. `test_repair_request_admitted_but_finding_stays_open` @448; `test_mandatory_unsatisfied_not_eligible` @1447; `test_open_supported_finding_blocks_eligibility` @1482 … | OK |

## Test-to-mutation map

All rows are `test_review_disposition.py` cases unless prefixed.

| Test case | Catching mutation |
| --- | --- |
| `test_repair_request_admitted_but_finding_stays_open` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-082, T5-MUT-105, T5-MUT-112 (supplementary: T5-DIAG-7, T5-DIAG-8) |
| `test_accept_risk_closes_review_and_contradiction_preserved` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-058, T5-MUT-068, T5-MUT-101, T5-MUT-103, T5-MUT-111 (supplementary: T5-DIAG-7) |
| `test_fixed_by_closes_on_replacement_subject` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-101, T5-MUT-103, T5-MUT-111 (supplementary: T5-DIAG-7) |
| `test_fixed_by_without_replacement_report_stays_open[True]` | T5-MUT-001, T5-MUT-022, T5-MUT-042, T5-MUT-058 (supplementary: T5-DIAG-5, T5-DIAG-6, T5-DIAG-7) |
| `test_fixed_by_same_subject_fingerprint_refused` | T5-MUT-001, T5-MUT-022, T5-MUT-043, T5-MUT-058 (supplementary: T5-DIAG-7) |
| `test_missing_approval_refused[repair-request]` | NOT PROVEN |
| `test_missing_approval_refused[fixed-by]` | NOT PROVEN |
| `test_missing_approval_refused[accept-risk]` | NOT PROVEN |
| `test_wrong_decision_scope_refused[repair-request]` | T5-MUT-001, T5-MUT-022, T5-MUT-035, T5-MUT-058 (supplementary: T5-DIAG-7) |
| `test_wrong_decision_scope_refused[fixed-by]` | T5-MUT-001, T5-MUT-022, T5-MUT-058 (supplementary: T5-DIAG-7) |
| `test_wrong_decision_scope_refused[accept-risk]` | T5-MUT-001, T5-MUT-022, T5-MUT-035, T5-MUT-058 (supplementary: T5-DIAG-7) |
| `test_authority_ref_mismatch_refused[repair-request]` | NOT PROVEN (supplementary: T5-DIAG-1) |
| `test_authority_ref_mismatch_refused[fixed-by]` | NOT PROVEN (supplementary: T5-DIAG-1) |
| `test_authority_ref_mismatch_refused[accept-risk]` | NOT PROVEN (supplementary: T5-DIAG-1) |
| `test_identity_mismatch_refused[repair-request]` | NOT PROVEN (supplementary: T5-DIAG-2) |
| `test_identity_mismatch_refused[fixed-by]` | NOT PROVEN |
| `test_identity_mismatch_refused[accept-risk]` | NOT PROVEN (supplementary: T5-DIAG-2) |
| `test_policy_fingerprint_mismatch_refused[repair-request]` | T5-MUT-014 (supplementary: T5-DIAG-6) |
| `test_policy_fingerprint_mismatch_refused[fixed-by]` | NOT PROVEN (supplementary: T5-DIAG-6) |
| `test_policy_fingerprint_mismatch_refused[accept-risk]` | T5-MUT-014 (supplementary: T5-DIAG-6) |
| `test_subject_manifest_ref_mismatch_refused[repair-request]` | T5-MUT-013 (supplementary: T5-DIAG-5) |
| `test_subject_manifest_ref_mismatch_refused[fixed-by]` | NOT PROVEN (supplementary: T5-DIAG-5) |
| `test_subject_manifest_ref_mismatch_refused[accept-risk]` | T5-MUT-013 (supplementary: T5-DIAG-5) |
| `test_evidence_only_grant_refused_out_of_scope[repair-request]` | T5-MUT-001, T5-MUT-002 (supplementary: T5-DIAG-7) |
| `test_evidence_only_grant_refused_out_of_scope[fixed-by]` | NOT PROVEN (supplementary: T5-DIAG-7) |
| `test_evidence_only_grant_refused_out_of_scope[accept-risk]` | T5-MUT-001, T5-MUT-002 (supplementary: T5-DIAG-7) |
| `test_invalid_grant_refused[repair-request]` | NOT PROVEN (supplementary: T5-DIAG-4) |
| `test_invalid_grant_refused[fixed-by]` | NOT PROVEN |
| `test_invalid_grant_refused[accept-risk]` | NOT PROVEN (supplementary: T5-DIAG-4) |
| `test_audit_sink_unavailable_refused_no_effect[repair-request]` | T5-MUT-004 (supplementary: T5-DIAG-4) |
| `test_audit_sink_unavailable_refused_no_effect[fixed-by]` | T5-MUT-004 (supplementary: T5-DIAG-4) |
| `test_audit_sink_unavailable_refused_no_effect[accept-risk]` | T5-MUT-004 (supplementary: T5-DIAG-4) |
| `test_post_allow_denial_has_same_operation_id[repair-request]` | T5-MUT-001, T5-MUT-022, T5-MUT-035, T5-MUT-050 (supplementary: T5-DIAG-7) |
| `test_post_allow_denial_has_same_operation_id[fixed-by]` | T5-MUT-001, T5-MUT-022, T5-MUT-050 (supplementary: T5-DIAG-7) |
| `test_post_allow_denial_has_same_operation_id[accept-risk]` | T5-MUT-001, T5-MUT-022, T5-MUT-035, T5-MUT-050 (supplementary: T5-DIAG-7) |
| `test_unsupported_assessment_cannot_be_disposed` | T5-MUT-017 |
| `test_nonmaterial_finding_cannot_be_disposed` | T5-MUT-021 |
| `test_raw_batch_with_disposition_refused` | T5-MUT-033 |
| `test_identical_retry_is_idempotent` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-051, T5-MUT-052, T5-MUT-058 (supplementary: T5-DIAG-7) |
| `test_changed_retry_refused` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-051, T5-MUT-058 (supplementary: T5-DIAG-7) |
| `test_mandatory_unsatisfied_not_eligible` | T5-MUT-100 (supplementary: T5-DIAG-8) |
| `test_open_supported_finding_blocks_eligibility` | T5-MUT-112 (supplementary: T5-DIAG-8) |
| `test_fresh_store_reopen_yields_identical_readiness` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-057, T5-MUT-058 (supplementary: T5-DIAG-7) |
| `test_waived_obligation_does_not_block` | T5-MUT-101 |
| `test_verified_fixed_by_obligation_decision_is_satisfied_findings` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-101, T5-MUT-103, T5-MUT-111 (supplementary: T5-DIAG-7) |
| `test_fixed_by_with_replacement_not_tip_stays_open` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-075, T5-MUT-105, T5-MUT-112 (supplementary: T5-DIAG-7, T5-DIAG-8) |
| `test_fixed_by_stops_closing_on_same_failure_supported_assessment` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-079, T5-MUT-101, T5-MUT-103, T5-MUT-105, T5-MUT-111, T5-MUT-112 (supplementary: T5-DIAG-7, T5-DIAG-8) |
| `test_fixed_by_stops_closing_on_indeterminate_replacement_assessment` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-078, T5-MUT-092, T5-MUT-105, T5-MUT-112 (supplementary: T5-DIAG-7, T5-DIAG-8) |
| `test_accept_risk_stops_closing_after_approval_superseded` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-058, T5-MUT-062, T5-MUT-068, T5-MUT-082, T5-MUT-101, T5-MUT-103, T5-MUT-105, T5-MUT-111, T5-MUT-112 (supplementary: T5-DIAG-7, T5-DIAG-8) |
| `test_accept_risk_stops_closing_after_assessment_replaced` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-058, T5-MUT-067, T5-MUT-068 (supplementary: T5-DIAG-7, T5-DIAG-8) |
| `test_raw_approval_write_refused_and_store_reopens` | NOT PROVEN (supplementary: T5-DIAG-3) |
| `test_replayed_raw_approval_frame_refuses_on_open` | T5-MUT-031, T5-MUT-056 (supplementary: T5-DIAG-3) |
| `test_review_persistence.py::test_all_six_review_record_families_round_trip_through_batch_port` | T5-MUT-001, T5-MUT-033, T5-MUT-045, T5-MUT-046, T5-MUT-057, T5-MUT-058 (supplementary: T5-DIAG-7) |

## Guard coverage

Each guard named in the task, with its mutation and outcome. "Caught" means at least one target case failed in a counted way.

### Capability scope and producer authority

- Review/disposition scope selection: T5-MUT-001, caught (23 cases).
- Out-of-scope grant refusal: T5-MUT-002, caught (2).
- None-grant refusal: T5-MUT-003, survived. See UNCAUGHT GUARD.
- Audit sink fails closed: T5-MUT-004, caught (3).

### Approval bindings

- Decision is `approved`: ABSENT GUARD. No code in either mutable file checks it.
- `decision_scope`: store rule 1 (T5-MUT-035) caught (4). The `disposition_closes` re-check (T5-MUT-063) survived.
- `authority_ref`: port rule 2 (T5-MUT-011), store no-approval (T5-MUT-034), and store rule 2 (T5-MUT-036) all survived.
- Identity: port rule 3 (T5-MUT-012), store rule 3 (T5-MUT-037), and the closes re-check (T5-MUT-064) all survived.
- Role (`decision_maker.role` equals `authority.role`): ABSENT GUARD. The only role check is the predecessor-role check (T5-MUT-032), which survived.
- Policy fingerprint: port (T5-MUT-014) caught (2). Store (T5-MUT-040) and its durable-subject gate (T5-MUT-038) survived.
- `manifest_ref` subject: port (T5-MUT-013) caught (2). Store (T5-MUT-039) survived.
- Predecessor supersession: T5-MUT-062, caught (1).
- Changed approval body under the same id: T5-MUT-044, survived.
- Approval persisted in the frame: T5-MUT-046, caught (13).

### Eligibility and currency

- Subject equality: eligibility (T5-MUT-018) survived. The closes re-check (T5-MUT-060) survived.
- Latest assessment: T5-MUT-067 caught (1). T5-MUT-092 caught (1).
- Supported: port (T5-MUT-017) caught (1). The readiness filters (T5-MUT-106, T5-MUT-108) survived.
- Material: port (T5-MUT-021) caught (1). The readiness filter drop (T5-MUT-107) survived. The readiness filter inversion (T5-MUT-112) caught (6).
- Current tip of the original report: T5-MUT-090 and T5-MUT-066 survived.
- Exact active receipt set: T5-MUT-091 survived.
- Replacement id absent on repair-request or accept-risk: ABSENT GUARD.

### fixed-by replacement conditions

- Durable replacement: write path (T5-MUT-042) caught (1). Closes (T5-MUT-070) survived.
- Non-empty replacement id: port (T5-MUT-015), store (T5-MUT-041), and closes (T5-MUT-069) all survived.
- Different subject fingerprint: write path (T5-MUT-043) caught (1). Closes (T5-MUT-071) survived.
- Same role: T5-MUT-073 survived.
- Shared delivery subject: T5-MUT-074 survived.
- Replacement is the tip: T5-MUT-075 caught (1).
- Admitted after the assessment: T5-MUT-076 survived.
- All replacement findings assessed: T5-MUT-077 survived.
- None indeterminate: T5-MUT-078 caught (1).
- No supported same-failure finding: T5-MUT-079 caught (1). The equality clause (T5-MUT-080) and the empty-failure clause (T5-MUT-081) survived.

### Raw paths, replay, retry, and post-allow pairing

- Raw disposition refusal: T5-MUT-033, caught (2), by a wrong denial code.
- Raw approval refusal: T5-MUT-030, survived. The unpaired-approval refusal (T5-MUT-031) caught (1).
- Replay re-check: T5-MUT-056 caught (1). T5-MUT-057 caught (2). T5-MUT-058, the same flag on the live lifecycle path, caught (18).
- Retry identity: T5-MUT-051 caught (2). T5-MUT-052 caught (1). T5-MUT-053, T5-MUT-054, and T5-MUT-055 survived.
- Post-allow denial pairing: T5-MUT-050, caught (3).
- The port wraps store refusals in its own exception: T5-MUT-022, caught (8).

### Readiness

- Mandatory-only eligibility: T5-MUT-100 caught (1). T5-MUT-101 caught (6).
- Optional-role open finding blocks: T5-MUT-102, survived.
- Waived role does not block: T5-MUT-101, caught by `test_waived_obligation_does_not_block`.
- fixed-by recompute flips the obligation: T5-MUT-103 caught (5). T5-MUT-111 caught (5). The obligation-loop re-verification (T5-MUT-104) survived. The open-findings re-verification (T5-MUT-105) caught (5).
- Repair-request never closes: T5-MUT-082, caught (2).
- Accept-risk leaves contradicting receipts active: T5-MUT-045, caught (7), but only by unexpected refusal. See the caveat below.
- Subject scoping of dispositions and assessments: T5-MUT-109, T5-MUT-110, and T5-MUT-094 all survived.

## UNCAUGHT GUARD

Each guard below has code and a mutation, but no target case fails under that mutation alone. None of these is a runtime defect. The guard still holds in every case shown. What is missing is a test that would fail if only that guard were removed.

**Unreachable path: the fixtures never produce the input the guard rejects.**

- T5-MUT-018, eligibility subject equality. No case disposes with a fingerprint that differs from its assessment's. A scratch probe confirms the guard refuses that input with `denied-disposition-subject-mismatch`.
- T5-MUT-060, closes subject equality. Readiness pre-filters dispositions by subject, and every direct `disposition_closes` call passes the matching subject.
- T5-MUT-063 and T5-MUT-064, closes scope and identity re-checks. The write path refuses a wrong scope or identity, so no durable disposition can reach these lines. No case replays a crafted log either.
- T5-MUT-016, T5-MUT-019, T5-MUT-020, T5-MUT-061, T5-MUT-065, T5-MUT-070, T5-MUT-072. These are missing-record checks for the assessment, report, finding, approval, replacement, and original report. Every case references records that exist.
- T5-MUT-015, T5-MUT-041, T5-MUT-069, the non-empty replacement id checks. Every fixed-by case supplies an id.
- T5-MUT-036, store rule 2. The approval is looked up by `authority_ref`, so a found approval always has a matching id. This guard is unreachable by construction.
- T5-MUT-038, T5-MUT-039, T5-MUT-040, store rule 4. It runs only when the review subject is durable, and no T5 case persists a `review-subject.v1`. The port's rule 4 (T5-MUT-013, T5-MUT-014) is the only mechanism the suite exercises.
- T5-MUT-032, predecessor role binding. The only superseding approval has the same role as its predecessor.
- T5-MUT-044, changed approval body under a reused approval id. No case reuses an id with a different body.
- T5-MUT-054 and T5-MUT-055, retry body and approval comparison. The changed retry differs in `disposition_id`, so an earlier check refuses first.
- T5-MUT-071, closes replacement subject differs. The write path refuses a same-subject replacement first.
- T5-MUT-073, T5-MUT-074, T5-MUT-076, closes same role, shared delivery subject, and later admission. Every replacement has the same role and delivery id and is admitted after the assessment.
- T5-MUT-077, every replacement finding assessed. Every direct `disposition_closes` call and every readiness call comes after the replacement finding is assessed.
- T5-MUT-080 and T5-MUT-081, the same-failure equality clause and the non-empty failure clause. No replacement finding is supported with a different failure, and the original failure is never empty.
- T5-MUT-090, T5-MUT-091, T5-MUT-066, current tip and exact receipt set for the original report. No case replaces the original report or partially supersedes its receipts.
- T5-MUT-093, T5-MUT-094, T5-MUT-106, T5-MUT-107, T5-MUT-108, T5-MUT-109, T5-MUT-110. These are readiness filters for non-supported or non-material findings and for other subjects. No case reaches readiness with such a record under the queried subject.

**Two sufficient mechanisms.**

- T5-MUT-011 with T5-MUT-034 (authority_ref). Port rule 2 and the store's no-approval lookup each refuse. `T5-DIAG-1` removes both, and all three `test_authority_ref_mismatch_refused` cases then fail.
- T5-MUT-012 with T5-MUT-037 (identity). Port rule 3 and store rule 3 each refuse. `T5-DIAG-2` catches the repair-request and accept-risk cases.
- T5-MUT-003, None-grant refusal. If the explicit check is removed, `grant.grant_id` raises inside the authority `try`, which refuses with `denied-audit-sink-unavailable`. `T5-DIAG-4` (T5-MUT-003 plus T5-MUT-004) catches the repair-request and accept-risk cases.
- T5-MUT-010, approval schema refusal. Port rule 2 then refuses the stub approval.
- T5-MUT-030, raw approval refusal. The unpaired-approval refusal returns the same code. `T5-DIAG-3` catches the raw-approval case.
- T5-MUT-053, retry id check. The committed-record lookup returns None and refuses.
- T5-MUT-102, the open-findings block. Every fixture has a mandatory role, so the obligation decision already blocks. No fixture has an optional role. `T5-DIAG-8` (with T5-MUT-100) catches 8 cases.
- T5-MUT-104, obligation-loop re-verification. The open-findings re-verification keeps eligibility False, and no case asserts the obligation decision for a disposition that does not close.

## Absent guards

These guards were named in the task, but there is no code for them in `_review_disposition.py` or `_evidence_store.py`, so no mutation can be applied. The scratch probe `$HOME/.slice2-scratch/t5-mut/probe/probe.py` uses the suite's own fixtures on the frozen baseline:

| Probe | Result |
| --- | --- |
| accept-risk with approval `decision: "superseded"` (an allowed enum value) | admitted; `disposition_closes` True; acceptance-eligible True |
| accept-risk with `decision_maker.role` ≠ approval `authority.role` | admitted; closes True; eligible True |
| accept-risk with `replacement_report_id: "report-t5"` | admitted; closes True; eligible True |
| repair-request with `replacement_report_id` | admitted; never closes |
| disposition fingerprint ≠ assessment fingerprint (control) | refused `denied-disposition-subject-mismatch` |

The first three are runtime gaps against the guard list, not test gaps. Each needs a decision by the spec owner before any test can pin it.

A related dead-code finding: `_review_disposition._validate_fixed_by_replacement` is defined but never called. Store rule 5 is the only mechanism for replacement durability and subject difference on the write path.

## NOT PROVEN

Each case below survived every single-property mutation of the property it names. In each one the refusal still holds. Most of these tests assert only a `denied-` or `denied-disposition-` prefix. All fixed-by authority negatives point at `report-t5-replacement-neg`, which is never persisted. So store rule 5 (`denied-disposition-replacement-not-durable`) refuses every fixed-by variant on its own.

- `test_missing_approval_refused[repair-request]`, `[fixed-by]`, `[accept-risk]`: survive T5-MUT-010. Shape: **two sufficient mechanisms** (several here). With the schema check removed, the stub approval `{"schema_version": 1}` is refused by port rule 2, and rules 3 and 4 and, for fixed-by, rule 5 would refuse it too. No single mutation reaches admission.
- `test_authority_ref_mismatch_refused[repair-request]`, `[fixed-by]`, `[accept-risk]`: survive T5-MUT-011, T5-MUT-034, and T5-MUT-036. Shape: **two sufficient mechanisms**: port rule 2 and the store's approval lookup by `authority_ref`. Store rule 2 is unreachable. Caught only by compound `T5-DIAG-1`.
- `test_identity_mismatch_refused[repair-request]`, `[accept-risk]`: survive T5-MUT-012 and T5-MUT-037. Shape: **two sufficient mechanisms**: port rule 3 and store rule 3. Caught only by `T5-DIAG-2`.
- `test_identity_mismatch_refused[fixed-by]`: as above, plus store rule 5 on the never-persisted replacement. Three mechanisms. `T5-DIAG-2` does not catch it.
- `test_policy_fingerprint_mismatch_refused[fixed-by]`: survives T5-MUT-014. Shape: **two sufficient mechanisms**: port rule 4 policy and store rule 5 replacement durability. Caught only by `T5-DIAG-6`.
- `test_subject_manifest_ref_mismatch_refused[fixed-by]`: survives T5-MUT-013. Shape: **two sufficient mechanisms**: port rule 4 manifest and store rule 5. Caught only by `T5-DIAG-5`.
- `test_evidence_only_grant_refused_out_of_scope[fixed-by]`: survives T5-MUT-001 and T5-MUT-002. Shape: **two sufficient mechanisms**: the scope refusal and store rule 5. Its denial-event assertion is also met by the post-allow denial. Caught only by `T5-DIAG-7`.
- `test_invalid_grant_refused[repair-request]`, `[accept-risk]`: survive T5-MUT-003. Shape: **two sufficient mechanisms**: the explicit None check and the authority-check exception wrap. Caught only by `T5-DIAG-4`.
- `test_invalid_grant_refused[fixed-by]`: as above, plus store rule 5. `T5-DIAG-4` does not catch it.
- `test_raw_approval_write_refused_and_store_reopens`: survives T5-MUT-030 and T5-MUT-031. Shape: **two sufficient mechanisms**: the raw-path approval refusal and the unpaired-approval refusal both return `denied-approval-authority-required`. Caught only by `T5-DIAG-3`.

## Proven, with a caveat

- `test_accept_risk_closes_review_and_contradiction_preserved`: no mutation pins its receipt-count or `contradicted` verdict assertions. T5-MUT-045 composes an accept-risk supersession of the bridge receipts. The store's bridge-supersession justification rule then refuses the disposition, so the case fails by unexpected refusal before those assertions run. The case is proven through readiness (T5-MUT-068, T5-MUT-101, T5-MUT-103, T5-MUT-111).
- `test_open_supported_finding_blocks_eligibility`: its eligibility assertion is guarded twice; T5-MUT-100 and T5-MUT-102 each survive. It is proven only through its `open_findings` membership assertion (T5-MUT-112).
- `test_wrong_decision_scope_refused[fixed-by]` and `test_post_allow_denial_has_same_operation_id[fixed-by]`: store rule 1 (T5-MUT-035) does not catch these, because store rule 5 refuses next. They are caught by T5-MUT-001 and T5-MUT-022, and the post-allow case also by T5-MUT-050.
- `test_changed_retry_refused`: T5-MUT-053 and T5-MUT-054 survive. It is caught by T5-MUT-051, which removes the whole lifecycle transaction-id reuse check.
- `test_accept_risk_stops_closing_after_assessment_replaced`: T5-MUT-092 (first assessment wins) survives. The replacement frame supersedes the old receipts, so the stale key drops out on the exact-receipt rule. It is caught by T5-MUT-067.
- T5-MUT-001 catches 13 success-path cases only because the review grant has no `evidence` root. Its catches of the negative cases (wrong scope, evidence-only, post-allow) are what bear on scope selection.

## Restored baseline

Both runtime hashes equal the frozen baseline after the last run (table under Scope and method). Each suite was run once, one at a time, on the restored baseline with `python3 -m pytest packs/core/tests/skills/work-loop/<suite> -q -p no:cacheprovider`:

| Suite | Result | Time |
| --- | --- | ---: |
| `test_review_disposition.py` | 52 passed | 1.40 s |
| `test_review_persistence.py` | 33 passed | 3.65 s |
| `test_review_bridge.py` | 50 passed | 1.35 s |
| `test_evidence_store.py` | 110 passed | 1.91 s |
