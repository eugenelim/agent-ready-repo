# T5 mutation evidence, second pass

Status: incomplete. 78 of the 79 T5 target cases are proven by at least one counted single-property mutation: 77 of the 78 cases in `test_review_disposition.py`, and the persistence case that routes a disposition through the typed port. One case is NOT PROVEN. 95 counted single-property mutations ran: 58 caught at least one case and 37 survived every case. Three compound diagnostics (`T5-DIAG-3`, `T5-DIAG-9`, `T5-DIAG-10`) back the analysis only and do not count. Both runtime hashes matched the frozen baseline after every run.

The new guards are pinned on the write path and on replay. G1 (approval `decision` is `approved`), G2 (`decision_maker.role` equals `authority.role`), and G3 (only fixed-by carries `replacement_report_id`) each have a write-only mutation and a replay-only mutation, and every one of the six is caught. Their `disposition_closes` copies are not pinned: G1 and G2 there are defence-in-depth and cannot be reached, and G3 has no code in `disposition_closes` at all.

**Runtime defect found: Rule 4 can be skipped.** The typed port no longer compares the approval with `current_subject`. The store compares it only when the `current_subject` fingerprint equals the disposition's fingerprint. A caller that passes any other valid subject skips Rule 4 entirely. A probe on the frozen baseline proved it: an accept-risk whose approval has `manifest_ref: "wrong"` and `spec_policy_fingerprint: "wrong"`, sent with `current_subject=_replacement_subject()`, was admitted, `disposition_closes` returned True, and the review became acceptance-eligible. The same approval with the matching subject is refused (`denied-disposition-subject-mismatch` and `denied-disposition-policy-mismatch`). See [Runtime findings](#runtime-findings).

## Scope and method

Targets: the 78 parametrized cases of `packs/core/tests/skills/work-loop/test_review_disposition.py` and `test_review_persistence.py::test_all_six_review_record_families_round_trip_through_batch_port` (its raw-batch refusal step and its typed-port admission step).

Each run used this command, from the execution root: `python3 -m pytest packs/core/tests/skills/work-loop/test_review_disposition.py "packs/core/tests/skills/work-loop/test_review_persistence.py::test_all_six_review_record_families_round_trip_through_batch_port" -q -p no:cacheprovider --tb=long --junitxml=<scratch>`. Each mutation reports its whole catching set across all 79 cases.

A catch needs exit 1 and a runtime failure inside a test body, of one of four kinds:

- an `assert` failure, including a wrong exact denial code;
- a `pytest.raises` that did not raise (`DID NOT RAISE`);
- a different exception inside a `pytest.raises` block (refusal-type mismatch);
- the code under test raising in a test that asserts success (`unexpected-raise`). This counts only when the failing statement calls the port, readiness, `disposition_closes`, a store open, or a raw `append_semantic_records`. A raise from a setup helper does not count.

Collection, import, syntax, fixture-setup, and timeout failures are excluded. None occurred.

Each mutation is one exact-string replacement in one runtime file. The first-pass helper was copied to `$HOME/.slice2-scratch/t5-mut2/`. It checks every replacement in memory before writing: the old string must occur exactly once, the new string must occur exactly once after replacement, and no replacement may be empty. Restoration is the inverse exact replacement, followed by a sha256 check of both runtime files. Only `_evidence_store.py` and `_review_disposition.py` were mutated. No test or other repository file was edited, and no restoration incident occurred. Probes ran either on the baseline or under one registered mutation, using the same apply, restore, and hash-check helper (`probe_under.py`).

Baseline sha256, verified before the first run, after every run and probe, and at the end:

| File | sha256 |
| --- | --- |
| `_evidence_store.py` | `670d61900735ab992ff70b6f4626c19e0a1917c43a21181c73a3f83f67fefb00` |
| `_review_disposition.py` | `668b56895a7864affe41fd1fcdd3f181841b3b542c0069c26b3c51e786bc3dc4` |

### Changes from the first-pass registry

- **Retired:** T5-MUT-011 to T5-MUT-015 (port rules 2 to 5). That code is gone from `_review_disposition.py`. Its single owner is now store rules 2 to 5 (T5-MUT-036 to T5-MUT-043). Compounds `T5-DIAG-1`, `-2`, `-5`, `-6`, and `-7`, which used them, were dropped.
- **Adapted to the new Rule 4 shape:** T5-MUT-038 (`effective_subject` gate), T5-MUT-040 (policy against `effective_subject`), and T5-MUT-058 (live-path flag; its comment changed).
- **New Rule 4 sub-properties:** T5-MUT-038A (the lifecycle-subject fallback), T5-MUT-038B (the fallback applies only on fingerprint equality), and T5-MUT-038C (the call site passes `review_subject`).
- **New guards:** T5-MUT-120 to T5-MUT-123 (G1), T5-MUT-130 to T5-MUT-133 (G2), and T5-MUT-140 to T5-MUT-144 (G3). In each group, `-x0` removes the guard on both the write path and replay. `-x1` removes it on the write path only, keyed on `lifecycle_review_subject is None`, which holds only on replay. `-x2` removes it on replay only. `-23` and `-33` remove the `disposition_closes` copy. T5-MUT-143 and T5-MUT-144 remove G3 for accept-risk only and for repair-request only.
- Every other first-pass mutation matched its exact old string exactly once and ran unchanged.

## Completed checks

| Mutation | Guarded behavior | Catching cases |
| --- | --- | ---: |
| T5-MUT-001 | finding-disposition lifecycle selects the review/disposition capability scope | 55 |
| T5-MUT-002 | an out-of-scope grant (authority not allowed) refuses | 6 |
| T5-MUT-003 | a None / non-grant object refuses with denied-invalid-grant | 3 |
| T5-MUT-004 | an unavailable audit sink at the authority check fails closed | 3 |
| T5-MUT-010 | port refuses a schema-invalid approval record | 3 |
| T5-MUT-016 | eligibility: the referenced assessment must be durable | 0 |
| T5-MUT-017 | eligibility: the referenced assessment must be supported | 1 |
| T5-MUT-018 | eligibility: assessment subject fingerprint equals the disposition subject (subject equality) | 0 |
| T5-MUT-019 | eligibility: the assessment source report must be durable | 0 |
| T5-MUT-020 | eligibility: the finding must be in the source report | 0 |
| T5-MUT-021 | eligibility: only material findings can be disposed | 1 |
| T5-MUT-022 | port converts store refusals into its own ReviewDispositionRefused | 32 |
| T5-MUT-030 | raw batch path refuses approval-record records | 0 |
| T5-MUT-031 | an approval must be paired with a disposition in the same frame | 1 |
| T5-MUT-032 | a superseding approval keeps the predecessor's authority role | 1 |
| T5-MUT-033 | raw batch path refuses finding-disposition records | 2 |
| T5-MUT-034 | store: a disposition needs a durable or in-frame approval | 3 |
| T5-MUT-035 | store rule 1: approval decision_scope is review-disposition | 6 |
| T5-MUT-036 | store rule 2: authority_ref equals approval_id | 0 |
| T5-MUT-037 | store rule 3: decision_maker identity equals approval identity | 3 |
| T5-MUT-038 | store rule 4 runs when an effective subject (durable or lifecycle) exists | 6 |
| T5-MUT-039 | store rule 4: approval manifest_ref equals the disposition subject | 3 |
| T5-MUT-040 | store rule 4: approval policy equals the effective subject policy | 3 |
| T5-MUT-041 | store rule 5: fixed-by needs a non-empty replacement id | 0 |
| T5-MUT-042 | store rule 5: the fixed-by replacement report must be durable | 1 |
| T5-MUT-043 | store rule 5: the replacement subject fingerprint differs | 1 |
| T5-MUT-044 | a durable approval id with a different body refuses | 1 |
| T5-MUT-045 | accept-risk does not supersede the contradicting bridge receipts | 10 |
| T5-MUT-046 | a new approval is persisted in the disposition frame | 49 |
| T5-MUT-050 | a lifecycle refusal after allow emits a paired denial with the same operation id | 3 |
| T5-MUT-051 | a reused lifecycle transaction id is either an exact retry or refused | 2 |
| T5-MUT-052 | an identical disposition retry is recognized as the committed transaction | 1 |
| T5-MUT-053 | disposition retry: the disposition id must be in the committed frame | 0 |
| T5-MUT-054 | disposition retry: the disposition body equals the committed body | 0 |
| T5-MUT-055 | disposition retry: an in-frame approval body equals the committed approval | 0 |
| T5-MUT-056 | replay re-runs the review transition checker on every frame | 4 |
| T5-MUT-057 | replay admits disposition frames under the full rule check | 2 |
| T5-MUT-058 | the lifecycle path admits disposition frames under the full rule check | 49 |
| T5-MUT-060 | closes: disposition subject equals the queried subject | 0 |
| T5-MUT-061 | closes: paired approval must be durable | 0 |
| T5-MUT-062 | closes: a superseded approval (named as predecessor) stops closing | 1 |
| T5-MUT-063 | closes: approval scope is review-disposition | 0 |
| T5-MUT-064 | closes: decision_maker identity equals approval identity | 0 |
| T5-MUT-065 | closes: the referenced assessment must be durable | 0 |
| T5-MUT-066 | closes: the assessment key must be current (tip + exact receipts) | 1 |
| T5-MUT-067 | closes: the disposition's assessment is the latest for the finding | 1 |
| T5-MUT-068 | closes: a current accept-risk closes | 5 |
| T5-MUT-069 | closes fixed-by: non-empty replacement id | 0 |
| T5-MUT-070 | closes fixed-by: replacement must be durable | 0 |
| T5-MUT-071 | closes fixed-by: replacement subject fingerprint differs | 0 |
| T5-MUT-072 | closes fixed-by: original report must be durable | 0 |
| T5-MUT-073 | closes fixed-by: replacement has the same role | 0 |
| T5-MUT-074 | closes fixed-by: replacement shares the delivery subject id | 0 |
| T5-MUT-075 | closes fixed-by: replacement is the current tip | 1 |
| T5-MUT-076 | closes fixed-by: replacement admitted after the assessment | 0 |
| T5-MUT-077 | closes fixed-by: every replacement finding has a current assessment | 1 |
| T5-MUT-078 | closes fixed-by: no replacement assessment is indeterminate | 1 |
| T5-MUT-079 | closes fixed-by: a supported same-failure replacement assessment stops closing | 1 |
| T5-MUT-080 | closes fixed-by: only a SAME actual_failure blocks (equality clause) | 0 |
| T5-MUT-081 | closes fixed-by: an empty original failure never matches | 0 |
| T5-MUT-082 | closes: repair-request (any other kind) never closes | 3 |
| T5-MUT-090 | current assessments: only the current report tip counts | 0 |
| T5-MUT-091 | current assessments: a supported entry needs the exact active receipt set | 0 |
| T5-MUT-092 | current assessments: the latest assessment per finding wins | 1 |
| T5-MUT-093 | current assessments: a non-supported entry needs no active derived receipts | 0 |
| T5-MUT-094 | current assessments: scoped to the queried subject fingerprint | 0 |
| T5-MUT-100 | readiness: a blocking (mandatory unsatisfied) obligation clears eligibility | 1 |
| T5-MUT-101 | readiness: only blocking decisions clear eligibility (waived role does not) | 6 |
| T5-MUT-102 | readiness: any open finding (incl. optional role) clears eligibility | 1 |
| T5-MUT-103 | readiness: verified closure flips an open-finding obligation to satisfied-findings | 5 |
| T5-MUT-104 | readiness obligation recompute re-verifies each disposition via disposition_closes | 0 |
| T5-MUT-105 | readiness open findings re-verify each disposition via disposition_closes | 6 |
| T5-MUT-106 | readiness recompute skips only non-supported assessments | 0 |
| T5-MUT-107 | readiness open findings: only material findings are open | 0 |
| T5-MUT-108 | readiness open findings: only supported assessments are open | 0 |
| T5-MUT-109 | readiness: dispositions scoped to the target subject | 0 |
| T5-MUT-110 | readiness: assessments scoped to the target subject | 0 |
| T5-MUT-111 | readiness recompute only runs on a current tip | 5 |
| T5-MUT-112 | readiness open findings: a supported material finding is listed as open | 8 |
| T5-MUT-038A | store rule 4: the lifecycle subject is used when no durable subject exists | 6 |
| T5-MUT-038B | store rule 4: the lifecycle subject is used only when its fingerprint equals the disposition's | 0 |
| T5-MUT-038C | lifecycle call site passes the review subject into the transition check | 6 |
| T5-MUT-120 | G1 write+replay: approval.decision must be approved | 6 |
| T5-MUT-121 | G1 write path only (replay keeps G1) | 5 |
| T5-MUT-122 | G1 replay only (write path keeps G1) | 1 |
| T5-MUT-123 | G1 closes: a non-approved approval never closes | 0 |
| T5-MUT-130 | G2 write+replay: decision_maker.role equals approval authority.role | 6 |
| T5-MUT-131 | G2 write path only (replay keeps G2) | 5 |
| T5-MUT-132 | G2 replay only (write path keeps G2) | 1 |
| T5-MUT-133 | G2 closes: role mismatch never closes | 0 |
| T5-MUT-140 | G3 write+replay: only fixed-by may carry replacement_report_id | 4 |
| T5-MUT-141 | G3 write path only (replay keeps G3) | 3 |
| T5-MUT-142 | G3 replay only (write path keeps G3) | 1 |
| T5-MUT-143 | G3 accept-risk coverage (repair-request keeps G3) | 3 |
| T5-MUT-144 | G3 repair-request coverage (accept-risk keeps G3) | 1 |
| T5-DIAG-3 | COMPOUND: raw-approval refusal + unpaired-approval refusal | 2 |
| T5-DIAG-9 | COMPOUND: closes subject check + current-assessment subject scope | 1 |
| T5-DIAG-10 | COMPOUND: current-assessment tip check + exact receipt set | 1 |

`T5-DIAG-3`, `T5-DIAG-9`, and `T5-DIAG-10` are compound diagnostics. Each applies two counted mutations at once, so none counts toward proof.

## Mutation details

Snippets are whitespace-collapsed (`⏎` marks a newline), and long ones are cut with `…`. The exact old and new strings are in `$HOME/.slice2-scratch/t5-mut2/mutations.py`. "@N" is the test-file line of the failing statement.

| Mutation | File | Exact mutation (old → new) | Observed catching cases | Restored hash |
| --- | --- | --- | --- | --- |
| T5-MUT-001 | `_evidence_store.py` | `"review/disposition"⏎ if _lifecycle_kind_peek == "finding-disposition"` → `"evidence"⏎ if _lifecycle_kind_peek == "finding-disposition"` | 55 cases: assertion, did-not-raise, unexpected-raise; incl. `test_repair_request_admitted_but_finding_stays_open` @436; `test_accept_risk_closes_review_and_contradiction_preserved` @487; `test_fixed_by_closes_on_replacement_subject` @601 … | OK |
| T5-MUT-002 | `_evidence_store.py` | `if not allowed:⏎ raise EvidenceStoreRefused(⏎ "denied-producer-authority",` → `if False:⏎ raise EvidenceStoreRefused(⏎ "denied-producer-authority",` | `test_evidence_only_grant_refused_out_of_scope[repair-request]` @1058 (did-not-raise); `test_evidence_only_grant_refused_out_of_scope[fixed-by]` @1058 (did-not-raise); `test_evidence_only_grant_refused_out_of_scope[accept-risk]` @1058 (did-not-raise); `test_grant_from_different_issuer_refused[repair-request]` @3091 (did-not-raise); `test_grant_from_different_issuer_refused[fixed-by]` @3091 (did-not-raise); `test_grant_from_different_issuer_refused[accept-risk]` @3091 (did-not-raise) | OK |
| T5-MUT-003 | `_evidence_store.py` | `if grant is None or not hasattr(grant, "grant_id"):` → `if False:` | `test_invalid_grant_refused[repair-request]` @1112 (assertion); `test_invalid_grant_refused[fixed-by]` @1112 (assertion); `test_invalid_grant_refused[accept-risk]` @1112 (assertion) | OK |
| T5-MUT-004 | `_evidence_store.py` | `except Exception as exc: # noqa: BLE001 — wraps AuditSinkUnavailable from any module load⏎ raise EvidenceStoreRefused(⏎ "denied-audit-sink-u…` → `except Exception as exc: # noqa: BLE001 — wraps AuditSinkUnavailable from any module load⏎ allowed = True⏎` | `test_audit_sink_unavailable_refused_no_effect[repair-request]` @1138 (did-not-raise); `test_audit_sink_unavailable_refused_no_effect[fixed-by]` @1138 (did-not-raise); `test_audit_sink_unavailable_refused_no_effect[accept-risk]` @1138 (did-not-raise) | OK |
| T5-MUT-010 | `_review_disposition.py` | `ok, code = _policy_import().validate_approval_dict(safe_approval)⏎ if not ok:` → `ok, code = _policy_import().validate_approval_dict(safe_approval)⏎ if False:` | `test_missing_approval_refused[repair-request]` @844 (assertion); `test_missing_approval_refused[fixed-by]` @844 (assertion); `test_missing_approval_refused[accept-risk]` @844 (assertion) | OK |
| T5-MUT-016 | `_review_disposition.py` | `if target_assessment is None:⏎ _refuse(⏎ "denied-disposition-no-assessment",` → `if False:⏎ _refuse(⏎ "denied-disposition-no-assessment",` | none — survived | OK |
| T5-MUT-017 | `_review_disposition.py` | `if target_assessment.get("assessment") != "supported": # type: ignore[union-attr]` → `if False: # type: ignore[union-attr]` | `test_unsupported_assessment_cannot_be_disposed` @1256 (did-not-raise) | OK |
| T5-MUT-018 | `_review_disposition.py` | `if target_assessment.get("review_subject_fingerprint") != review_subject_fingerprint: # type: ignore[union-attr]` → `if False: # type: ignore[union-attr]` | none — survived | OK |
| T5-MUT-019 | `_review_disposition.py` | `if source_report is None:⏎ _refuse(⏎ "denied-disposition-no-report",` → `if False:⏎ _refuse(⏎ "denied-disposition-no-report",` | none — survived | OK |
| T5-MUT-020 | `_review_disposition.py` | `if source_finding is None:⏎ _refuse(⏎ "denied-disposition-no-finding",` → `if False:⏎ _refuse(⏎ "denied-disposition-no-finding",` | none — survived | OK |
| T5-MUT-021 | `_review_disposition.py` | `if not source_finding.get("material", False): # type: ignore[union-attr]` → `if False: # type: ignore[union-attr]` | `test_nonmaterial_finding_cannot_be_disposed` @1328 (did-not-raise) | OK |
| T5-MUT-022 | `_review_disposition.py` | `if denial_code is not None:⏎ raise ReviewDispositionRefused(denial_code, str(exc)) from exc` → `if False:⏎ raise ReviewDispositionRefused(denial_code, str(exc)) from exc` | 32 cases: refusal-type-mismatch, unexpected-raise; incl. `test_fixed_by_without_replacement_report_stays_open[True]` @661; `test_fixed_by_same_subject_fingerprint_refused` @712; `test_wrong_decision_scope_refused[repair-request]` @870 … | OK |
| T5-MUT-030 | `_evidence_store.py` | `if not check_disposition_rules:⏎ raise EvidenceStoreRefused(⏎ "denied-approval-authority-required",` → `if False:⏎ raise EvidenceStoreRefused(⏎ "denied-approval-authority-required",` | none — survived | OK |
| T5-MUT-031 | `_evidence_store.py` | `if not frame_dispositions:⏎ raise EvidenceStoreRefused(⏎ "denied-approval-authority-required",` → `if False:⏎ raise EvidenceStoreRefused(⏎ "denied-approval-authority-required",` | `test_replayed_raw_approval_frame_refuses_on_open` @2400 (did-not-raise) | OK |
| T5-MUT-032 | `_evidence_store.py` | `if _pred is not None and (` → `if False and (` | `test_predecessor_role_mismatch_refused` @2997 (did-not-raise) | OK |
| T5-MUT-033 | `_evidence_store.py` | `if not check_disposition_rules:⏎ raise EvidenceStoreRefused(⏎ "denied-disposition-authority-required",` → `if False:⏎ raise EvidenceStoreRefused(⏎ "denied-disposition-authority-required",` | `test_raw_batch_with_disposition_refused` @1379 (assertion); `test_all_six_review_record_families_round_trip_through_batch_port` @796 (assertion) | OK |
| T5-MUT-034 | `_evidence_store.py` | `if approval is None:⏎ raise EvidenceStoreRefused(⏎ "denied-disposition-no-approval",` → `if False:⏎ raise EvidenceStoreRefused(⏎ "denied-disposition-no-approval",` | `test_authority_ref_mismatch_refused[repair-request]` @909 (refusal-type-mismatch); `test_authority_ref_mismatch_refused[fixed-by]` @909 (refusal-type-mismatch); `test_authority_ref_mismatch_refused[accept-risk]` @909 (refusal-type-mismatch) | OK |
| T5-MUT-035 | `_evidence_store.py` | `if approval.get("decision_scope") != "review-disposition":⏎ raise EvidenceStoreRefused(` → `if False:⏎ raise EvidenceStoreRefused(` | `test_wrong_decision_scope_refused[repair-request]` @869 (did-not-raise); `test_wrong_decision_scope_refused[fixed-by]` @869 (did-not-raise); `test_wrong_decision_scope_refused[accept-risk]` @869 (did-not-raise); `test_post_allow_denial_has_same_operation_id[repair-request]` @1178 (did-not-raise); `test_post_allow_denial_has_same_operation_id[fixed-by]` @1178 (did-not-raise); `test_post_allow_denial_has_same_operation_id[accept-risk]` @1178 (did-not-raise) | OK |
| T5-MUT-036 | `_evidence_store.py` | `if authority_ref != approval.get("approval_id", ""):` → `if False:` | none — survived | OK |
| T5-MUT-037 | `_evidence_store.py` | `if maker_identity != approval.get("authority", {}).get("identity", ""):` → `if False:` | `test_identity_mismatch_refused[repair-request]` @946 (did-not-raise); `test_identity_mismatch_refused[fixed-by]` @946 (did-not-raise); `test_identity_mismatch_refused[accept-risk]` @946 (did-not-raise) | OK |
| T5-MUT-038 | `_evidence_store.py` | `if effective_subject is not None:` → `if False:` | `test_policy_fingerprint_mismatch_refused[repair-request]` @983 (did-not-raise); `test_policy_fingerprint_mismatch_refused[fixed-by]` @983 (did-not-raise); `test_policy_fingerprint_mismatch_refused[accept-risk]` @983 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[repair-request]` @1020 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[fixed-by]` @1020 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[accept-risk]` @1020 (did-not-raise) | OK |
| T5-MUT-039 | `_evidence_store.py` | `if approval.get("base", {}).get("manifest_ref", "") != disp_fp:` → `if False:` | `test_subject_manifest_ref_mismatch_refused[repair-request]` @1020 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[fixed-by]` @1020 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[accept-risk]` @1020 (did-not-raise) | OK |
| T5-MUT-040 | `_evidence_store.py` | `if approval.get("spec_policy_fingerprint", "") != effective_subject.get(` → `if False and approval.get("spec_policy_fingerprint", "") != effective_subject.get(` | `test_policy_fingerprint_mismatch_refused[repair-request]` @983 (did-not-raise); `test_policy_fingerprint_mismatch_refused[fixed-by]` @983 (did-not-raise); `test_policy_fingerprint_mismatch_refused[accept-risk]` @983 (did-not-raise) | OK |
| T5-MUT-041 | `_evidence_store.py` | `if not replacement_id:⏎ raise EvidenceStoreRefused(⏎ "denied-disposition-missing-replacement",` → `if False:⏎ raise EvidenceStoreRefused(⏎ "denied-disposition-missing-replacement",` | none — survived | OK |
| T5-MUT-042 | `_evidence_store.py` | `replacement = semantic_records.get("review-report.v1", {}).get(replacement_id)` → `replacement = semantic_records.get("review-report.v1", {}).get(replacement_id, {})` | `test_fixed_by_without_replacement_report_stays_open[True]` @660 (did-not-raise) | OK |
| T5-MUT-043 | `_evidence_store.py` | `if replacement_fp == disp_fp:` → `if False:` | `test_fixed_by_same_subject_fingerprint_refused` @711 (did-not-raise) | OK |
| T5-MUT-044 | `_evidence_store.py` | `elif _canonical_json(existing_approval) != _canonical_json(approval_record):` → `elif False:` | `test_changed_approval_body_same_id_refused` @3050 (did-not-raise) | OK |
| T5-MUT-045 | `_evidence_store.py` | `frame.append(copy.deepcopy(seed_disposition))⏎ return frame` → `frame.append(copy.deepcopy(seed_disposition))⏎ _mut_ids = [rid for rid, r in self._receipts.items() if rid not in self._superseded and _is_b…` | 10 cases: unexpected-raise; incl. `test_accept_risk_closes_review_and_contradiction_preserved` @487; `test_identical_retry_is_idempotent` @1409; `test_changed_retry_refused` @1447 … | OK |
| T5-MUT-046 | `_evidence_store.py` | `if existing_approval is None:⏎ frame.append(copy.deepcopy(approval_record))` → `if False:⏎ frame.append(copy.deepcopy(approval_record))` | 49 cases: assertion, unexpected-raise; incl. `test_repair_request_admitted_but_finding_stays_open` @436; `test_accept_risk_closes_review_and_contradiction_preserved` @487; `test_fixed_by_closes_on_replacement_subject` @601 … | OK |
| T5-MUT-050 | `_evidence_store.py` | `return tx, composed⏎⏎ try:⏎ if _HAS_FCNTL:⏎ with _advisory_lock(self._root, self._log_path) as lock_fd:⏎ committed, committed_records = deci…` → `return tx, composed⏎⏎ try:⏎ if _HAS_FCNTL:⏎ with _advisory_lock(self._root, self._log_path) as lock_fd:⏎ committed, committed_records = deci…` | `test_post_allow_denial_has_same_operation_id[repair-request]` @1194 (assertion); `test_post_allow_denial_has_same_operation_id[fixed-by]` @1194 (assertion); `test_post_allow_denial_has_same_operation_id[accept-risk]` @1194 (assertion) | OK |
| T5-MUT-051 | `_evidence_store.py` | `if prev_tx.get("transaction_id") == transaction_id:⏎ if self._check_lifecycle_idempotent(` → `if False:⏎ if self._check_lifecycle_idempotent(` | `test_identical_retry_is_idempotent` @1415 (unexpected-raise); `test_changed_retry_refused` @1456 (did-not-raise) | OK |
| T5-MUT-052 | `_evidence_store.py` | `if _canonical_json(committed_approval) != _canonical_json(approval_record):⏎ return False⏎ return True` → `if _canonical_json(committed_approval) != _canonical_json(approval_record):⏎ return False⏎ return False` | `test_identical_retry_is_idempotent` @1415 (unexpected-raise) | OK |
| T5-MUT-053 | `_evidence_store.py` | `if disposition_id not in committed_ids:⏎ return False` → `if False:⏎ return False` | none — survived | OK |
| T5-MUT-054 | `_evidence_store.py` | `if _canonical_json(committed_disposition) != _canonical_json(disposition):⏎ return False` → `if False:⏎ return False` | none — survived | OK |
| T5-MUT-055 | `_evidence_store.py` | `if _canonical_json(committed_approval) != _canonical_json(approval_record):` → `if False:` | none — survived | OK |
| T5-MUT-056 | `_evidence_store.py` | `_validate_review_transition(⏎ records,⏎ acceptance_fingerprint=tx["acceptance_fingerprint"],` → `(lambda *a, **k: None)(⏎ records,⏎ acceptance_fingerprint=tx["acceptance_fingerprint"],` | `test_replayed_raw_approval_frame_refuses_on_open` @2400 (did-not-raise); `test_g1_replay_refuses` @2793 (did-not-raise); `test_g2_replay_refuses` @2830 (did-not-raise); `test_g3_replay_refuses` @2867 (did-not-raise) | OK |
| T5-MUT-057 | `_evidence_store.py` | `# via the lifecycle port, and rules 1–5 are re-validated here.⏎ check_disposition_rules=True,` → `# via the lifecycle port, and rules 1–5 are re-validated here.⏎ check_disposition_rules=False,` | `test_fresh_store_reopen_yields_identical_readiness` @1564 (unexpected-raise); `test_all_six_review_record_families_round_trip_through_batch_port` @822 (unexpected-raise) | OK |
| T5-MUT-058 | `_evidence_store.py` | `check_disposition_rules=True,⏎ lifecycle_review_subject=(` → `check_disposition_rules=False,⏎ lifecycle_review_subject=(` | 49 cases: assertion, unexpected-raise; incl. `test_repair_request_admitted_but_finding_stays_open` @436; `test_accept_risk_closes_review_and_contradiction_preserved` @487; `test_fixed_by_closes_on_replacement_subject` @601 … | OK |
| T5-MUT-060 | `_evidence_store.py` | `if disposition.get("review_subject_fingerprint") != subject_fp:⏎ return False⏎⏎ # 2. Find the paired approval.` → `if False:⏎ return False⏎⏎ # 2. Find the paired approval.` | none — survived | OK |
| T5-MUT-061 | `_evidence_store.py` | `approval = self._semantic_records.get("approval-record.v1", {}).get(authority_ref)⏎ if approval is None:⏎ return False` → `approval = self._semantic_records.get("approval-record.v1", {}).get(authority_ref)⏎ if False:⏎ return False` | none — survived | OK |
| T5-MUT-062 | `_evidence_store.py` | `if _other.get("lineage", {}).get("predecessor_id") == authority_ref:⏎ return False` → `if False:⏎ return False` | `test_accept_risk_stops_closing_after_approval_superseded` @2228 (assertion) | OK |
| T5-MUT-063 | `_evidence_store.py` | `if approval.get("decision_scope") != "review-disposition":⏎ return False` → `if False:⏎ return False` | none — survived | OK |
| T5-MUT-064 | `_evidence_store.py` | `disposition.get("decision_maker", {}).get("identity")⏎ != approval.get("authority", {}).get("identity")` → `False` | none — survived | OK |
| T5-MUT-065 | `_evidence_store.py` | `if assessment is None:⏎ return False⏎ report_id = assessment.get("report_id", "")` → `if False:⏎ return False⏎ report_id = assessment.get("report_id", "")` | none — survived | OK |
| T5-MUT-066 | `_evidence_store.py` | `if entry is None:⏎ return False⏎ if entry["assessment"]` → `if False:⏎ return False⏎ if entry["assessment"]` | `test_disposition_closes_false_after_source_report_superseded` @3310 (unexpected-raise) | OK |
| T5-MUT-067 | `_evidence_store.py` | `if entry["assessment"].get("assessment_id") != assessment_id:⏎ return False` → `if False:⏎ return False` | `test_accept_risk_stops_closing_after_assessment_replaced` @2317 (assertion) | OK |
| T5-MUT-068 | `_evidence_store.py` | `if disp_kind == "accept-risk":⏎ return True` → `if disp_kind == "accept-risk":⏎ return False` | `test_accept_risk_closes_review_and_contradiction_preserved` @536 (assertion); `test_accept_risk_stops_closing_after_approval_superseded` @2193 (assertion); `test_accept_risk_stops_closing_after_assessment_replaced` @2287 (assertion); `test_disposition_closes_false_for_wrong_subject` @3139 (assertion); `test_disposition_closes_false_after_source_report_superseded` @3282 (assertion) | OK |
| T5-MUT-069 | `_evidence_store.py` | `if not replacement_id:⏎ return False⏎⏎ replacement` → `if False:⏎ return False⏎⏎ replacement` | none — survived | OK |
| T5-MUT-070 | `_evidence_store.py` | `if replacement is None:⏎ return False⏎⏎ # Replacement must belong` → `if False:⏎ return False⏎⏎ # Replacement must belong` | none — survived | OK |
| T5-MUT-071 | `_evidence_store.py` | `if replacement_fp == subject_fp:⏎ return False` → `if False:⏎ return False` | none — survived | OK |
| T5-MUT-072 | `_evidence_store.py` | `if original_report is None:⏎ return False⏎ if replacement.get("role")` → `if False:⏎ return False⏎ if replacement.get("role")` | none — survived | OK |
| T5-MUT-073 | `_evidence_store.py` | `if replacement.get("role") != original_report.get("role"):` → `if False:` | none — survived | OK |
| T5-MUT-074 | `_evidence_store.py` | `if orig_delivery_id != repl_delivery_id:` → `if False:` | none — survived | OK |
| T5-MUT-075 | `_evidence_store.py` | `if tip is None or tip.get("report_id") != replacement_id:⏎ return False` → `if False:⏎ return False` | `test_fixed_by_with_replacement_not_tip_stays_open` @1817 (assertion) | OK |
| T5-MUT-076 | `_evidence_store.py` | `if replacement_tx_idx < 0 or replacement_tx_idx <= assessment_tx_idx:` → `if False:` | none — survived | OK |
| T5-MUT-077 | `_evidence_store.py` | `return False # No current assessment for this replacement finding.` → `continue # No current assessment for this replacement finding.` | `test_disposition_closes_false_until_replacement_finding_assessed` @3219 (assertion) | OK |
| T5-MUT-078 | `_evidence_store.py` | `if repl_assessment.get("assessment") == "indeterminate":⏎ return False` → `if False:⏎ return False` | `test_fixed_by_stops_closing_on_indeterminate_replacement_assessment` @2131 (assertion) | OK |
| T5-MUT-079 | `_evidence_store.py` | `repl_assessment.get("assessment") == "supported"⏎ and original_failure` → `False⏎ and original_failure` | `test_fixed_by_stops_closing_on_same_failure_supported_assessment` @1978 (assertion) | OK |
| T5-MUT-080 | `_evidence_store.py` | `and original_failure⏎ and repl_finding.get("actual_failure", "") == original_failure⏎` → `and original_failure⏎` | none — survived | OK |
| T5-MUT-081 | `_evidence_store.py` | `and original_failure⏎ and repl_finding` → `and repl_finding` | none — survived | OK |
| T5-MUT-082 | `_evidence_store.py` | `return True⏎⏎ return False⏎⏎ def get_transaction` → `return True⏎⏎ return True⏎⏎ def get_transaction` | `test_repair_request_admitted_but_finding_stays_open` @454 (assertion); `test_accept_risk_stops_closing_after_approval_superseded` @2236 (assertion); `test_repair_request_never_closes` @3464 (assertion) | OK |
| T5-MUT-090 | `_evidence_store.py` | `if tip_report is None or tip_report.get("report_id") != report_id:⏎ continue` → `if False:⏎ continue` | none — survived | OK |
| T5-MUT-091 | `_evidence_store.py` | `if not expected_ids or expected_ids != active_ids:` → `if not expected_ids:` | none — survived | OK |
| T5-MUT-092 | `_evidence_store.py` | `latest_by_source[key] = assessment` → `latest_by_source.setdefault(key, assessment)` | `test_fixed_by_stops_closing_on_indeterminate_replacement_assessment` @2131 (assertion) | OK |
| T5-MUT-093 | `_evidence_store.py` | `if active_receipts:⏎ continue⏎ receipt_ids = []` → `if False:⏎ continue⏎ receipt_ids = []` | none — survived | OK |
| T5-MUT-094 | `_evidence_store.py` | `if assessment.get("review_subject_fingerprint") != review_subject_fingerprint:⏎ continue⏎ key =` → `if False:⏎ continue⏎ key =` | none — survived | OK |
| T5-MUT-100 | `_review_disposition.py` | `if decision.get("acceptance_block"):⏎ acceptance_eligible = False` → `if False:⏎ acceptance_eligible = False` | `test_mandatory_unsatisfied_not_eligible` @1488 (assertion) | OK |
| T5-MUT-101 | `_review_disposition.py` | `if decision.get("acceptance_block"):⏎ acceptance_eligible = False` → `if True:⏎ acceptance_eligible = False` | `test_accept_risk_closes_review_and_contradiction_preserved` @536 (assertion); `test_fixed_by_closes_on_replacement_subject` @619 (assertion); `test_waived_obligation_does_not_block` @1611 (assertion); `test_verified_fixed_by_obligation_decision_is_satisfied_findings` @1705 (assertion); `test_fixed_by_stops_closing_on_same_failure_supported_assessment` @1949 (assertion); `test_accept_risk_stops_closing_after_approval_superseded` @2201 (assertion) | OK |
| T5-MUT-102 | `_review_disposition.py` | `if open_findings:⏎ acceptance_eligible = False` → `if False:⏎ acceptance_eligible = False` | `test_optional_role_open_finding_blocks_eligibility` @3415 (assertion) | OK |
| T5-MUT-103 | `_review_disposition.py` | `if all_closed:⏎ decision = {` → `if False:⏎ decision = {` | `test_accept_risk_closes_review_and_contradiction_preserved` @536 (assertion); `test_fixed_by_closes_on_replacement_subject` @619 (assertion); `test_verified_fixed_by_obligation_decision_is_satisfied_findings` @1701 (assertion); `test_fixed_by_stops_closing_on_same_failure_supported_assessment` @1949 (assertion); `test_accept_risk_stops_closing_after_approval_superseded` @2201 (assertion) | OK |
| T5-MUT-104 | `_review_disposition.py` | `store.disposition_closes(d.get("disposition_id", ""), review_subject)⏎ for d in dispositions⏎ if d.get("finding_id") == finding_id_loop` → `True⏎ for d in dispositions⏎ if d.get("finding_id") == finding_id_loop` | none — survived | OK |
| T5-MUT-105 | `_review_disposition.py` | `store.disposition_closes(d.get("disposition_id", ""), review_subject)⏎ for d in dispositions⏎ if d.get("finding_id") == finding_id⏎` → `True⏎ for d in dispositions⏎ if d.get("finding_id") == finding_id⏎` | `test_repair_request_admitted_but_finding_stays_open` @456 (assertion); `test_fixed_by_with_replacement_not_tip_stays_open` @1820 (assertion); `test_fixed_by_stops_closing_on_same_failure_supported_assessment` @1989 (assertion); `test_fixed_by_stops_closing_on_indeterminate_replacement_assessment` @2142 (assertion); `test_accept_risk_stops_closing_after_approval_superseded` @2239 (assertion); `test_repair_request_never_closes` @3476 (assertion) | OK |
| T5-MUT-106 | `_review_disposition.py` | `if finding_assessment.get("assessment") != "supported":⏎ continue` → `if False:⏎ continue` | none — survived | OK |
| T5-MUT-107 | `_review_disposition.py` | `if finding is None or not finding.get("material", False):` → `if finding is None:` | none — survived | OK |
| T5-MUT-108 | `_review_disposition.py` | `if assessment.get("assessment") != "supported":⏎ continue⏎ source_report = next(` → `if False:⏎ continue⏎ source_report = next(` | none — survived | OK |
| T5-MUT-109 | `_review_disposition.py` | `if d.get("review_subject_fingerprint") == review_subject_fingerprint⏎ ]` → `if True⏎ ]` | none — survived | OK |
| T5-MUT-110 | `_review_disposition.py` | `if a.get("review_subject_fingerprint") == review_subject_fingerprint⏎ ]` → `if True⏎ ]` | none — survived | OK |
| T5-MUT-111 | `_review_disposition.py` | `if tip is not None:⏎ all_closed = True` → `if tip is not None and False:⏎ all_closed = True` | `test_accept_risk_closes_review_and_contradiction_preserved` @536 (assertion); `test_fixed_by_closes_on_replacement_subject` @619 (assertion); `test_verified_fixed_by_obligation_decision_is_satisfied_findings` @1701 (assertion); `test_fixed_by_stops_closing_on_same_failure_supported_assessment` @1949 (assertion); `test_accept_risk_stops_closing_after_approval_superseded` @2201 (assertion) | OK |
| T5-MUT-112 | `_review_disposition.py` | `if finding is None or not finding.get("material", False):` → `if finding is None or finding.get("material", False):` | 8 cases: assertion; incl. `test_repair_request_admitted_but_finding_stays_open` @456; `test_open_supported_finding_blocks_eligibility` @1524; `test_fixed_by_with_replacement_not_tip_stays_open` @1820 … | OK |
| T5-MUT-038A | `_evidence_store.py` | `effective_subject = lifecycle_review_subject` → `effective_subject = None` | `test_policy_fingerprint_mismatch_refused[repair-request]` @983 (did-not-raise); `test_policy_fingerprint_mismatch_refused[fixed-by]` @983 (did-not-raise); `test_policy_fingerprint_mismatch_refused[accept-risk]` @983 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[repair-request]` @1020 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[fixed-by]` @1020 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[accept-risk]` @1020 (did-not-raise) | OK |
| T5-MUT-038B | `_evidence_store.py` | `and lifecycle_review_subject.get("review_subject_fingerprint") == disp_fp⏎` → `and True⏎` | none — survived | OK |
| T5-MUT-038C | `_evidence_store.py` | `lifecycle_review_subject=(⏎ lifecycle.get("review_subject")` → `lifecycle_review_subject=(⏎ None` | `test_policy_fingerprint_mismatch_refused[repair-request]` @983 (did-not-raise); `test_policy_fingerprint_mismatch_refused[fixed-by]` @983 (did-not-raise); `test_policy_fingerprint_mismatch_refused[accept-risk]` @983 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[repair-request]` @1020 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[fixed-by]` @1020 (did-not-raise); `test_subject_manifest_ref_mismatch_refused[accept-risk]` @1020 (did-not-raise) | OK |
| T5-MUT-120 | `_evidence_store.py` | `if approval.get("decision") != "approved":⏎ raise EvidenceStoreRefused(` → `if False:⏎ raise EvidenceStoreRefused(` | `test_g1_approval_not_approved_refuses` @2440 (did-not-raise); `test_g1_store_direct_refuses` @2650 (did-not-raise); `test_g1_replay_refuses` @2793 (did-not-raise); `test_decision_not_approved_refused[repair-request]` @2900 (did-not-raise); `test_decision_not_approved_refused[fixed-by]` @2900 (did-not-raise); `test_decision_not_approved_refused[accept-risk]` @2900 (did-not-raise) | OK |
| T5-MUT-121 | `_evidence_store.py` | `if approval.get("decision") != "approved":⏎ raise EvidenceStoreRefused(` → `if lifecycle_review_subject is None and approval.get("decision") != "approved":⏎ raise EvidenceStoreRefused(` | `test_g1_approval_not_approved_refuses` @2440 (did-not-raise); `test_g1_store_direct_refuses` @2650 (did-not-raise); `test_decision_not_approved_refused[repair-request]` @2900 (did-not-raise); `test_decision_not_approved_refused[fixed-by]` @2900 (did-not-raise); `test_decision_not_approved_refused[accept-risk]` @2900 (did-not-raise) | OK |
| T5-MUT-122 | `_evidence_store.py` | `if approval.get("decision") != "approved":⏎ raise EvidenceStoreRefused(` → `if lifecycle_review_subject is not None and approval.get("decision") != "approved":⏎ raise EvidenceStoreRefused(` | `test_g1_replay_refuses` @2793 (did-not-raise) | OK |
| T5-MUT-123 | `_evidence_store.py` | `if approval.get("decision") != "approved":⏎ return False` → `if False:⏎ return False` | none — survived | OK |
| T5-MUT-130 | `_evidence_store.py` | `if maker_role != approval.get("authority", {}).get("role", ""):` → `if False:` | `test_g2_role_mismatch_refuses` @2491 (did-not-raise); `test_g2_store_direct_refuses` @2696 (did-not-raise); `test_g2_replay_refuses` @2830 (did-not-raise); `test_role_mismatch_refused_per_kind[repair-request]` @2937 (did-not-raise); `test_role_mismatch_refused_per_kind[fixed-by]` @2937 (did-not-raise); `test_role_mismatch_refused_per_kind[accept-risk]` @2937 (did-not-raise) | OK |
| T5-MUT-131 | `_evidence_store.py` | `if maker_role != approval.get("authority", {}).get("role", ""):` → `if lifecycle_review_subject is None and maker_role != approval.get("authority", {}).get("role", ""):` | `test_g2_role_mismatch_refuses` @2491 (did-not-raise); `test_g2_store_direct_refuses` @2696 (did-not-raise); `test_role_mismatch_refused_per_kind[repair-request]` @2937 (did-not-raise); `test_role_mismatch_refused_per_kind[fixed-by]` @2937 (did-not-raise); `test_role_mismatch_refused_per_kind[accept-risk]` @2937 (did-not-raise) | OK |
| T5-MUT-132 | `_evidence_store.py` | `if maker_role != approval.get("authority", {}).get("role", ""):` → `if lifecycle_review_subject is not None and maker_role != approval.get("authority", {}).get("role", ""):` | `test_g2_replay_refuses` @2830 (did-not-raise) | OK |
| T5-MUT-133 | `_evidence_store.py` | `disposition.get("decision_maker", {}).get("role")⏎ != approval.get("authority", {}).get("role")` → `False` | none — survived | OK |
| T5-MUT-140 | `_evidence_store.py` | `if disp_kind != "fixed-by" and disposition.get("replacement_report_id"):` → `if False:` | `test_g3_accept_risk_with_replacement_report_id_refuses` @2546 (did-not-raise); `test_g3_repair_request_with_replacement_report_id_refuses` @2601 (did-not-raise); `test_g3_store_direct_refuses` @2742 (did-not-raise); `test_g3_replay_refuses` @2867 (did-not-raise) | OK |
| T5-MUT-141 | `_evidence_store.py` | `if disp_kind != "fixed-by" and disposition.get("replacement_report_id"):` → `if lifecycle_review_subject is None and disp_kind != "fixed-by" and disposition.get("replacement_report_id"):` | `test_g3_accept_risk_with_replacement_report_id_refuses` @2546 (did-not-raise); `test_g3_repair_request_with_replacement_report_id_refuses` @2601 (did-not-raise); `test_g3_store_direct_refuses` @2742 (did-not-raise) | OK |
| T5-MUT-142 | `_evidence_store.py` | `if disp_kind != "fixed-by" and disposition.get("replacement_report_id"):` → `if lifecycle_review_subject is not None and disp_kind != "fixed-by" and disposition.get("replacement_report_id"):` | `test_g3_replay_refuses` @2867 (did-not-raise) | OK |
| T5-MUT-143 | `_evidence_store.py` | `if disp_kind != "fixed-by" and disposition.get("replacement_report_id"):` → `if disp_kind == "repair-request" and disposition.get("replacement_report_id"):` | `test_g3_accept_risk_with_replacement_report_id_refuses` @2546 (did-not-raise); `test_g3_store_direct_refuses` @2742 (did-not-raise); `test_g3_replay_refuses` @2867 (did-not-raise) | OK |
| T5-MUT-144 | `_evidence_store.py` | `if disp_kind != "fixed-by" and disposition.get("replacement_report_id"):` → `if disp_kind == "accept-risk" and disposition.get("replacement_report_id"):` | `test_g3_repair_request_with_replacement_report_id_refuses` @2601 (did-not-raise) | OK |
| T5-DIAG-3 | `_evidence_store.py` | compound: T5-MUT-030+T5-MUT-031 | `test_raw_approval_write_refused_and_store_reopens` @2352 (did-not-raise); `test_replayed_raw_approval_frame_refuses_on_open` @2400 (did-not-raise) | OK |
| T5-DIAG-9 | `_evidence_store.py` | compound: T5-MUT-060+T5-MUT-094 | `test_disposition_closes_false_for_wrong_subject` @3143 (assertion) | OK |
| T5-DIAG-10 | `_evidence_store.py` | compound: T5-MUT-090+T5-MUT-091 | `test_disposition_closes_false_after_source_report_superseded` @3310 (assertion) | OK |

## Test-to-mutation map

All rows are `test_review_disposition.py` cases unless prefixed.

| Test case | Catching mutation |
| --- | --- |
| `test_repair_request_admitted_but_finding_stays_open` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-082, T5-MUT-105, T5-MUT-112 |
| `test_accept_risk_closes_review_and_contradiction_preserved` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-058, T5-MUT-068, T5-MUT-101, T5-MUT-103, T5-MUT-111 |
| `test_fixed_by_closes_on_replacement_subject` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-101, T5-MUT-103, T5-MUT-111 |
| `test_fixed_by_without_replacement_report_stays_open[True]` | T5-MUT-001, T5-MUT-022, T5-MUT-042, T5-MUT-046, T5-MUT-058 |
| `test_fixed_by_same_subject_fingerprint_refused` | T5-MUT-001, T5-MUT-022, T5-MUT-043, T5-MUT-046, T5-MUT-058 |
| `test_missing_approval_refused[repair-request]` | T5-MUT-010 |
| `test_missing_approval_refused[fixed-by]` | T5-MUT-010 |
| `test_missing_approval_refused[accept-risk]` | T5-MUT-010 |
| `test_wrong_decision_scope_refused[repair-request]` | T5-MUT-001, T5-MUT-022, T5-MUT-035, T5-MUT-046, T5-MUT-058 |
| `test_wrong_decision_scope_refused[fixed-by]` | T5-MUT-001, T5-MUT-022, T5-MUT-035, T5-MUT-046, T5-MUT-058 |
| `test_wrong_decision_scope_refused[accept-risk]` | T5-MUT-001, T5-MUT-022, T5-MUT-035, T5-MUT-046, T5-MUT-058 |
| `test_authority_ref_mismatch_refused[repair-request]` | T5-MUT-001, T5-MUT-022, T5-MUT-034, T5-MUT-046, T5-MUT-058 |
| `test_authority_ref_mismatch_refused[fixed-by]` | T5-MUT-001, T5-MUT-022, T5-MUT-034, T5-MUT-046, T5-MUT-058 |
| `test_authority_ref_mismatch_refused[accept-risk]` | T5-MUT-001, T5-MUT-022, T5-MUT-034, T5-MUT-046, T5-MUT-058 |
| `test_identity_mismatch_refused[repair-request]` | T5-MUT-001, T5-MUT-022, T5-MUT-037, T5-MUT-046, T5-MUT-058 |
| `test_identity_mismatch_refused[fixed-by]` | T5-MUT-001, T5-MUT-022, T5-MUT-037, T5-MUT-046, T5-MUT-058 |
| `test_identity_mismatch_refused[accept-risk]` | T5-MUT-001, T5-MUT-022, T5-MUT-037, T5-MUT-046, T5-MUT-058 |
| `test_policy_fingerprint_mismatch_refused[repair-request]` | T5-MUT-001, T5-MUT-022, T5-MUT-038, T5-MUT-040, T5-MUT-046, T5-MUT-058, T5-MUT-038A, T5-MUT-038C |
| `test_policy_fingerprint_mismatch_refused[fixed-by]` | T5-MUT-001, T5-MUT-022, T5-MUT-038, T5-MUT-040, T5-MUT-046, T5-MUT-058, T5-MUT-038A, T5-MUT-038C |
| `test_policy_fingerprint_mismatch_refused[accept-risk]` | T5-MUT-001, T5-MUT-022, T5-MUT-038, T5-MUT-040, T5-MUT-046, T5-MUT-058, T5-MUT-038A, T5-MUT-038C |
| `test_subject_manifest_ref_mismatch_refused[repair-request]` | T5-MUT-001, T5-MUT-022, T5-MUT-038, T5-MUT-039, T5-MUT-046, T5-MUT-058, T5-MUT-038A, T5-MUT-038C |
| `test_subject_manifest_ref_mismatch_refused[fixed-by]` | T5-MUT-001, T5-MUT-022, T5-MUT-038, T5-MUT-039, T5-MUT-046, T5-MUT-058, T5-MUT-038A, T5-MUT-038C |
| `test_subject_manifest_ref_mismatch_refused[accept-risk]` | T5-MUT-001, T5-MUT-022, T5-MUT-038, T5-MUT-039, T5-MUT-046, T5-MUT-058, T5-MUT-038A, T5-MUT-038C |
| `test_evidence_only_grant_refused_out_of_scope[repair-request]` | T5-MUT-001, T5-MUT-002 |
| `test_evidence_only_grant_refused_out_of_scope[fixed-by]` | T5-MUT-001, T5-MUT-002 |
| `test_evidence_only_grant_refused_out_of_scope[accept-risk]` | T5-MUT-001, T5-MUT-002 |
| `test_invalid_grant_refused[repair-request]` | T5-MUT-003 |
| `test_invalid_grant_refused[fixed-by]` | T5-MUT-003 |
| `test_invalid_grant_refused[accept-risk]` | T5-MUT-003 |
| `test_audit_sink_unavailable_refused_no_effect[repair-request]` | T5-MUT-004 |
| `test_audit_sink_unavailable_refused_no_effect[fixed-by]` | T5-MUT-004 |
| `test_audit_sink_unavailable_refused_no_effect[accept-risk]` | T5-MUT-004 |
| `test_post_allow_denial_has_same_operation_id[repair-request]` | T5-MUT-001, T5-MUT-022, T5-MUT-035, T5-MUT-050 |
| `test_post_allow_denial_has_same_operation_id[fixed-by]` | T5-MUT-001, T5-MUT-022, T5-MUT-035, T5-MUT-050 |
| `test_post_allow_denial_has_same_operation_id[accept-risk]` | T5-MUT-001, T5-MUT-022, T5-MUT-035, T5-MUT-050 |
| `test_unsupported_assessment_cannot_be_disposed` | T5-MUT-017 |
| `test_nonmaterial_finding_cannot_be_disposed` | T5-MUT-021 |
| `test_raw_batch_with_disposition_refused` | T5-MUT-033 |
| `test_identical_retry_is_idempotent` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-051, T5-MUT-052, T5-MUT-058 |
| `test_changed_retry_refused` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-051, T5-MUT-058 |
| `test_mandatory_unsatisfied_not_eligible` | T5-MUT-100 |
| `test_open_supported_finding_blocks_eligibility` | T5-MUT-112 |
| `test_fresh_store_reopen_yields_identical_readiness` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-057, T5-MUT-058 |
| `test_waived_obligation_does_not_block` | T5-MUT-101 |
| `test_verified_fixed_by_obligation_decision_is_satisfied_findings` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-101, T5-MUT-103, T5-MUT-111 |
| `test_fixed_by_with_replacement_not_tip_stays_open` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-075, T5-MUT-105, T5-MUT-112 |
| `test_fixed_by_stops_closing_on_same_failure_supported_assessment` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-079, T5-MUT-101, T5-MUT-103, T5-MUT-105, T5-MUT-111, T5-MUT-112 |
| `test_fixed_by_stops_closing_on_indeterminate_replacement_assessment` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-078, T5-MUT-092, T5-MUT-105, T5-MUT-112 |
| `test_accept_risk_stops_closing_after_approval_superseded` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-058, T5-MUT-062, T5-MUT-068, T5-MUT-082, T5-MUT-101, T5-MUT-103, T5-MUT-105, T5-MUT-111, T5-MUT-112 |
| `test_accept_risk_stops_closing_after_assessment_replaced` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-058, T5-MUT-067, T5-MUT-068 |
| `test_raw_approval_write_refused_and_store_reopens` | NOT PROVEN (supplementary: T5-DIAG-3) |
| `test_replayed_raw_approval_frame_refuses_on_open` | T5-MUT-031, T5-MUT-056 (supplementary: T5-DIAG-3) |
| `test_g1_approval_not_approved_refuses` | T5-MUT-001, T5-MUT-022, T5-MUT-046, T5-MUT-058, T5-MUT-120, T5-MUT-121 |
| `test_g2_role_mismatch_refuses` | T5-MUT-001, T5-MUT-022, T5-MUT-046, T5-MUT-058, T5-MUT-130, T5-MUT-131 |
| `test_g3_accept_risk_with_replacement_report_id_refuses` | T5-MUT-001, T5-MUT-022, T5-MUT-046, T5-MUT-058, T5-MUT-140, T5-MUT-141, T5-MUT-143 |
| `test_g3_repair_request_with_replacement_report_id_refuses` | T5-MUT-001, T5-MUT-022, T5-MUT-046, T5-MUT-058, T5-MUT-140, T5-MUT-141, T5-MUT-144 |
| `test_g1_store_direct_refuses` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-120, T5-MUT-121 |
| `test_g2_store_direct_refuses` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-130, T5-MUT-131 |
| `test_g3_store_direct_refuses` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-140, T5-MUT-141, T5-MUT-143 |
| `test_g1_replay_refuses` | T5-MUT-056, T5-MUT-120, T5-MUT-122 |
| `test_g2_replay_refuses` | T5-MUT-056, T5-MUT-130, T5-MUT-132 |
| `test_g3_replay_refuses` | T5-MUT-056, T5-MUT-140, T5-MUT-142, T5-MUT-143 |
| `test_decision_not_approved_refused[repair-request]` | T5-MUT-001, T5-MUT-022, T5-MUT-046, T5-MUT-058, T5-MUT-120, T5-MUT-121 |
| `test_decision_not_approved_refused[fixed-by]` | T5-MUT-001, T5-MUT-022, T5-MUT-046, T5-MUT-058, T5-MUT-120, T5-MUT-121 |
| `test_decision_not_approved_refused[accept-risk]` | T5-MUT-001, T5-MUT-022, T5-MUT-046, T5-MUT-058, T5-MUT-120, T5-MUT-121 |
| `test_role_mismatch_refused_per_kind[repair-request]` | T5-MUT-001, T5-MUT-022, T5-MUT-046, T5-MUT-058, T5-MUT-130, T5-MUT-131 |
| `test_role_mismatch_refused_per_kind[fixed-by]` | T5-MUT-001, T5-MUT-022, T5-MUT-046, T5-MUT-058, T5-MUT-130, T5-MUT-131 |
| `test_role_mismatch_refused_per_kind[accept-risk]` | T5-MUT-001, T5-MUT-022, T5-MUT-046, T5-MUT-058, T5-MUT-130, T5-MUT-131 |
| `test_predecessor_role_mismatch_refused` | T5-MUT-001, T5-MUT-022, T5-MUT-032, T5-MUT-045, T5-MUT-046, T5-MUT-058 |
| `test_changed_approval_body_same_id_refused` | T5-MUT-001, T5-MUT-022, T5-MUT-044, T5-MUT-046, T5-MUT-058 |
| `test_grant_from_different_issuer_refused[repair-request]` | T5-MUT-002 |
| `test_grant_from_different_issuer_refused[fixed-by]` | T5-MUT-002 |
| `test_grant_from_different_issuer_refused[accept-risk]` | T5-MUT-002 |
| `test_disposition_closes_false_for_wrong_subject` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-058, T5-MUT-068 (supplementary: T5-DIAG-9) |
| `test_disposition_closes_false_until_replacement_finding_assessed` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-077 |
| `test_disposition_closes_false_after_source_report_superseded` | T5-MUT-001, T5-MUT-045, T5-MUT-046, T5-MUT-058, T5-MUT-066, T5-MUT-068 (supplementary: T5-DIAG-10) |
| `test_optional_role_open_finding_blocks_eligibility` | T5-MUT-102, T5-MUT-112 |
| `test_repair_request_never_closes` | T5-MUT-001, T5-MUT-046, T5-MUT-058, T5-MUT-082, T5-MUT-105, T5-MUT-112 |
| `test_review_persistence.py::test_all_six_review_record_families_round_trip_through_batch_port` | T5-MUT-001, T5-MUT-033, T5-MUT-045, T5-MUT-046, T5-MUT-057, T5-MUT-058 |

## Guard coverage

"Caught" means at least one target case failed in a counted way under that mutation alone.

### Capability scope and producer authority

- Review/disposition scope selection: T5-MUT-001 caught 55 cases.
- Out-of-scope or foreign-issuer grant: T5-MUT-002 caught 6 cases, including all three `test_grant_from_different_issuer_refused` cases. The issuer check itself lives in `_security_events`, which is outside the mutable files.
- None-grant refusal: T5-MUT-003 caught 3 cases. It was uncaught in the first pass and is caught now because the test asserts the exact code.
- Audit sink fails closed: T5-MUT-004 caught 3 cases.

### Approval bindings (single owner: `_validate_review_transition`)

- Approval schema at the port: T5-MUT-010 caught 3 cases.
- No durable or in-frame approval: T5-MUT-034 caught 3 cases.
- Rule 1, `decision_scope`: T5-MUT-035 caught 6 cases. The `disposition_closes` copy (T5-MUT-063) survived.
- Rule 2, `authority_ref` equals `approval_id`: T5-MUT-036 survived. It cannot be reached (see below).
- Rule 3, identity: T5-MUT-037 caught 3 cases. The closes copy (T5-MUT-064) survived.
- G1, decision `approved`: write and replay together (T5-MUT-120) caught 6 cases. Write only (T5-MUT-121) caught 5. Replay only (T5-MUT-122) caught 1. The closes copy (T5-MUT-123) survived.
- G2, role: write and replay together (T5-MUT-130) caught 6 cases. Write only (T5-MUT-131) caught 5. Replay only (T5-MUT-132) caught 1. The closes copy (T5-MUT-133) survived.
- Rule 4 gate: T5-MUT-038 caught 6 cases. Manifest (T5-MUT-039) caught 3. Policy (T5-MUT-040) caught 3. The lifecycle-subject fallback (T5-MUT-038A) caught 6. The call-site pass-through (T5-MUT-038C) caught 6. The fingerprint-equality condition (T5-MUT-038B) survived. That condition is the Rule 4 bypass described in [Runtime findings](#runtime-findings).
- Predecessor role binding: T5-MUT-032 caught 1 case.
- Changed approval body under the same id: T5-MUT-044 caught 1 case.
- Approval persisted in the frame: T5-MUT-046 caught 49 cases.
- Closes, approval superseded by a successor: T5-MUT-062 caught 1 case.

### Replacement (G3 and Rule 5)

- G3: write and replay together (T5-MUT-140) caught 4 cases. Write only (T5-MUT-141) caught 3. Replay only (T5-MUT-142) caught 1. Accept-risk coverage (T5-MUT-143) caught 3. Repair-request coverage (T5-MUT-144) caught 1. G3 has no code in `disposition_closes` (see [Absent guards](#absent-guards)).
- Rule 5, non-empty id: T5-MUT-041 survived. It is reachable but untested.
- Rule 5, durable replacement: T5-MUT-042 caught 1 case.
- Rule 5, different subject: T5-MUT-043 caught 1 case.

### Eligibility (port only)

- Supported (T5-MUT-017) caught 1 case. Material (T5-MUT-021) caught 1 case.
- Assessment exists (T5-MUT-016), subject equality (T5-MUT-018), report exists (T5-MUT-019), and finding in report (T5-MUT-020) all survived.

### fixed-by closure (`disposition_closes`)

- Caught: tip (T5-MUT-075), every replacement finding assessed (T5-MUT-077), none indeterminate (T5-MUT-078), and no supported same-failure finding (T5-MUT-079). Each caught 1 case.
- Survived: non-empty id (T5-MUT-069), durable (T5-MUT-070), different subject (T5-MUT-071), original durable (T5-MUT-072), same role (T5-MUT-073), shared delivery subject (T5-MUT-074), admitted after the assessment (T5-MUT-076), the same-failure equality clause (T5-MUT-080), and the empty-failure clause (T5-MUT-081).

### Currency, raw paths, replay, and retry

- Current assessments: latest wins (T5-MUT-092) caught 1 case. The tip check (T5-MUT-090), exact receipt set (T5-MUT-091), non-supported entry (T5-MUT-093), and subject scope (T5-MUT-094) survived. Closes, current key (T5-MUT-066) caught 1 case, by a `TypeError` only. Closes, latest assessment (T5-MUT-067) caught 1 case.
- Raw disposition refusal: T5-MUT-033 caught 2 cases. Raw approval refusal: T5-MUT-030 survived (two sufficient mechanisms). Unpaired approval: T5-MUT-031 caught 1 case.
- Replay: the transition re-check (T5-MUT-056) caught 4 cases. The replay rule flag (T5-MUT-057) caught 2. The live-path flag (T5-MUT-058) caught 49.
- Retry: transaction-id reuse (T5-MUT-051) caught 2 cases, and idempotent recognition (T5-MUT-052) caught 1. Disposition id in frame (T5-MUT-053), disposition body (T5-MUT-054), and approval body (T5-MUT-055) survived. All three are reachable.
- Post-allow pairing (T5-MUT-050) caught 3 cases. The port wraps store refusals (T5-MUT-022) caught 32 cases.

### Readiness

- Caught: the obligation block (T5-MUT-100, 1 case), only blocking decisions clear eligibility (T5-MUT-101, 6), the open-findings block for an optional role (T5-MUT-102, 1), the recompute flip (T5-MUT-103, 5), the open-findings re-verification (T5-MUT-105, 6), the recompute tip gate (T5-MUT-111, 5), the material-finding listing (T5-MUT-112, 8), a current accept-risk closes (T5-MUT-068, 5), and repair-request never closes (T5-MUT-082, 3).
- Accept-risk keeps the contradicting receipts: T5-MUT-045 caught 10 cases, by unexpected refusal only.
- Survived: the obligation-loop re-verification (T5-MUT-104), the recompute skipping non-supported assessments (T5-MUT-106), the material filter (T5-MUT-107), the supported filter (T5-MUT-108), the disposition subject scope (T5-MUT-109), and the assessment subject scope (T5-MUT-110).

## UNCAUGHT GUARD

All 37 surviving mutations are below. Each has code, but no target case fails when only that guard is removed. Where a probe is cited, `probe/probe3.py <scenario>` printed one result on the baseline and a different one under that single mutation alone. Each probe used the suite's own fixtures.

### (i) Reachable but untested: 20 guards

Each line gives the single input that would catch the mutation, then the probe result (baseline → mutated).

- **T5-MUT-016** (port: the assessment exists). Send a disposition with `assessment_id="assessment-missing"` through the port and assert `denial_code == "denied-disposition-no-assessment"`. S016: refused → `AttributeError`.
- **T5-MUT-018** (port: disposition subject equals assessment subject). Send `_disposition(subject)` with `review_subject_fingerprint="other-subject-fp"` and assert `"denied-disposition-subject-mismatch"`. S018: refused → **admitted**.
- **T5-MUT-020** (port: the finding is in the source report). Send a disposition with `finding_id="finding-missing"` and assert `"denied-disposition-no-finding"`. S020: refused → `AttributeError`.
- **T5-MUT-041** (store Rule 5: non-empty replacement id). Send a fixed-by with no `replacement_report_id` key; the schema allows this. Assert `"denied-disposition-missing-replacement"`. S041: that code → `denied-disposition-replacement-not-durable`.
- **T5-MUT-053** (retry: the disposition id is in the committed frame). Commit `disp-1` under `tx-A` and `disp-2` under `tx-B`. Retry `tx-A` with `disp-2`'s exact body and assert `"denied-duplicate-transaction-id"`. S053: refused → `tx-A` returned as an idempotent retry.
- **T5-MUT-054** (retry: same disposition body). Retry `tx-A` with the same `disposition_id` but `lineage.source_event_id="event-changed"`, and assert `"denied-duplicate-transaction-id"`. S054: refused → accepted as idempotent.
- **T5-MUT-055** (retry: same in-frame approval body). Retry `tx-A` with the same disposition and an approval with the same id but a changed `timestamp`. Assert `"denied-duplicate-transaction-id"`. S055: refused → accepted as idempotent.
- **T5-MUT-065** (closes: the assessment exists). On an empty store, append an approved accept-risk with `assessment_id="assessment-missing"` straight to the store with `append_semantic_records(..., lifecycle={"kind": "finding-disposition", ...})`. The store admits it. Then assert `disposition_closes(...) is False`. S065: False → `AttributeError`.
- **T5-MUT-073** (closes: replacement has the same role). Make a fixed-by whose clean replacement report has `role="security-reviewer"`, then assert `disposition_closes is False`. S073: False → True.
- **T5-MUT-074** (closes: shared delivery subject). Use a replacement subject with `delivery_subject_ref.subject_id="delivery-subject-other"`, then assert closes is False. S074: False → True.
- **T5-MUT-076** (closes: replacement admitted after the assessment). Persist the replacement report before the original report and assessment, then dispose fixed-by and assert closes is False. S076: False → True.
- **T5-MUT-080** (closes: only the same `actual_failure` blocks). Give the replacement report one material finding with `actual_failure="a different failure"` and assess it supported. Assert closes is True. S080: True → False.
- **T5-MUT-090** (current assessments: only the current tip counts). Persist `report-t5`, assess its finding `unsupported-opinion`, then persist `report-t5-v2` (sequence 2). Assert `("report-t5", "finding-t5") not in store.current_finding_assessments(fp)`. S090: absent → present. Supported entries are also guarded by T5-MUT-091, because a new tip must supersede the old receipts. That is why `T5-DIAG-10` was needed in the target test.
- **T5-MUT-091** (current assessments: exact active receipt set). After an accept-risk closes, apply a `source-invalidation` lifecycle with `_replacement_subject()` for `report-t5`/`finding-t5`, then assert `disposition_closes is False`. Probe P4 (`probe/probe2.py` under T5-MUT-091): False → True.
- **T5-MUT-094** (current assessments: subject scope). After the standard setup, call `review_readiness` for `_replacement_subject()` with its own policy fingerprint and assert `open_findings == []`. S094: `[]` → `["finding-t5"]`.
- **T5-MUT-104** (obligation recompute re-verifies each disposition). After a repair-request is admitted, assert `review_readiness(...)["obligations"][0]["decision"] == "open-supported-material-finding"`. S104: that value → `satisfied-findings`.
- **T5-MUT-106** (recompute skips non-supported assessments). Use a report with two material findings: one supported and disposed accept-risk, and one assessed `unsupported-opinion`. Assert the obligation decision is `satisfied-findings` and `acceptance_eligible` is True. S106: `(satisfied-findings, True)` → `(open-supported-material-finding, False)`.
- **T5-MUT-107** (open findings: material only). Persist a report whose only finding has `material: False`, assess it supported, and assert `open_findings == []`. S107: `[]` → `["finding-t5"]`.
- **T5-MUT-108** (open findings: supported only). Assess the material finding `unsupported-opinion` and assert `open_findings == []`. S108: `[]` → `["finding-t5"]`.
- **T5-MUT-038B** (the Rule 4 fallback applies only on fingerprint equality). This one can be reached, but on the baseline it produces the wrong outcome. A test that sends the standard accept-risk with approval `manifest_ref="wrong"` and `spec_policy_fingerprint="wrong"` and `current_subject=_replacement_subject()`, and asserts `"denied-disposition-subject-mismatch"`, **fails on the current baseline**. It would pass under T5-MUT-038B. S038B: admitted → refused. This is a runtime defect, not a test gap.

### (ii) Two sufficient mechanisms: 4 guards

- **T5-MUT-030**, the raw-path approval refusal. The unpaired-approval refusal (T5-MUT-031) returns the same code. `T5-DIAG-3` catches `test_raw_approval_write_refused_and_store_reopens`.
- **T5-MUT-060**, the closes subject check. Current-assessment subject scoping (T5-MUT-094) also returns no entry for the other subject. `T5-DIAG-9` catches `test_disposition_closes_false_for_wrong_subject`.
- **T5-MUT-109**, the readiness disposition subject filter. `disposition_closes` re-checks the subject (T5-MUT-060), so another subject's disposition never closes.
- **T5-MUT-110**, the readiness assessment subject filter. The store admits an assessment whose fingerprint differs from its report's subject. In a probe (S110) with such an assessment, readiness was identical with the filter removed: `(finding-assessment-required, False)` both ways. The downstream selection removes it again.

### (ii) Unreachable by construction (dead or defence-in-depth): 13 guards

- **T5-MUT-036**, store Rule 2. The approval is looked up by `authority_ref`, both in-frame (`approval_id == authority_ref`) and durable (keyed by `approval_id`). A found approval always matches. This is dead code.
- **T5-MUT-019** (port: the source report exists) and **T5-MUT-072** (closes: the original report exists). Every assessment path, lifecycle and raw (`_validate_review_transition`) alike, refuses an assessment whose report and finding are not durable. Records are append-only. `current_finding_assessments` also skips a missing report before T5-MUT-072 is reached.
- **T5-MUT-061, -063, -064, -123, -133**: in closes, the approval exists, and its scope, identity, G1, and G2 are re-checked. A disposition becomes durable only after these same rules pass against the approval named by its `authority_ref`, on the write path and again on replay. Both records are immutable, so the closes copies cannot see a violation. They are defence-in-depth.
- **T5-MUT-069, -070, -071**: in closes, the fixed-by replacement id is non-empty, the replacement is durable, and its subject differs. Store Rule 5 enforces all three at write and replay, on immutable records.
- **T5-MUT-081**, the empty-original-failure clause. The finding schema requires a non-empty `actual_failure`, and the current entry always names a finding that exists in the report.
- **T5-MUT-093**, the non-supported entry needs no active receipts. A non-supported assessment frame must supersede every derived receipt for its source (`unsupported assessment must supersede derived receipts`). New receipts for that source arrive only with a later supported assessment, which then becomes the latest.

## Absent guards

- **G3 in `disposition_closes`.** The brief names G3 for closes, but `disposition_closes` never reads `replacement_report_id` for accept-risk or repair-request, so no mutation can exist. It would be defence-in-depth only, because G3 refuses that input on both the write path (T5-MUT-141) and replay (T5-MUT-142).
- The three guards that were absent in the first pass (G1, G2, G3) now exist, and the write and replay copies of each are caught.

## NOT PROVEN

- `test_raw_approval_write_refused_and_store_reopens` survives T5-MUT-030 and T5-MUT-031 alike. Shape: **two sufficient mechanisms.** The raw-path approval refusal and the unpaired-approval refusal both return `denied-approval-authority-required`. Only compound `T5-DIAG-3` catches it. One way to make it catchable: send a raw batch that pairs an approval with a disposition. T5-MUT-030 is then the only refusal that names approvals; T5-MUT-033 would refuse with a different code. Probe `probe/probe4.py`: `denied-approval-authority-required` on the baseline → `denied-disposition-authority-required` under T5-MUT-030.

## Proven, with a caveat

- `test_disposition_closes_false_for_wrong_subject` is proven only through its True precondition (T5-MUT-068 and the write-path mutations). Its False assertion is pinned only by compound `T5-DIAG-9`.
- `test_disposition_closes_false_after_source_report_superseded`: its False assertion fails under T5-MUT-066 only because `entry["assessment"]` on `None` raises a `TypeError`. It is semantically pinned only by compound `T5-DIAG-10`.
- `test_g1_replay_refuses`, `test_g2_replay_refuses`, and `test_g3_replay_refuses` assert only that `EvidenceStoreError` is raised, not which rule refused. The replay-only mutations T5-MUT-122, -132, and -142 each catch exactly their own case, so each case is pinned to its guard today.
- `test_accept_risk_closes_review_and_contradiction_preserved`: as in the first pass, T5-MUT-045 catches it only by unexpected refusal, before its receipt-count and `contradicted` assertions run. Readiness mutations prove it (T5-MUT-068, -101, -103, -111).
- T5-MUT-001 catches success-path cases only because the review grant has no `evidence` root. Its catches on the negative cases are the ones that bear on scope selection.

## Runtime findings

Each finding below came from a probe on the frozen baseline (`$HOME/.slice2-scratch/t5-mut2/probe/`). None is a test gap alone, and each needs a decision by the spec owner.

1. **Rule 4 bypass (regression).** The removed port rule 4 compared the approval with `current_subject` on every call. The store now compares only against a durable `review-subject.v1` or a `lifecycle_review_subject` whose fingerprint equals the disposition's (the T5-MUT-038B condition). No part of the port or the store requires `current_subject` to match the disposition. Probe `probe.py` sent the wrong `manifest_ref` and policy with `current_subject=_replacement_subject()`. The disposition was **admitted**, `disposition_closes` returned True, and the review was acceptance-eligible.
2. **Eligibility is port-only.** Assessment exists, supported, subject match, finding in report, and material all live only in `_review_disposition._validate_disposition_eligibility`. The store does not own them. A review-grant holder calling `append_semantic_records` with the finding-disposition lifecycle got an accept-risk admitted with no assessment at all (probe P2). `disposition_closes` returns False for it, so readiness is unaffected. Still, the brief's "all semantic rules single-owner in `_evidence_store.py`" does not hold for eligibility.
3. **An unreferenced approval rides along.** The frame always includes `lifecycle["approval_record"]` when its id is new, even when the disposition's `authority_ref` names a different, already-durable approval. Rules 1, 3, G1, G2, and 4 then run only against the referenced approval. In probe P3, approval `approval-x` had `decision_scope: "spec-policy"`, `decision: "superseded"`, and `predecessor_id: "approval-t5"`. It was admitted, and the earlier accept-risk stopped closing.
4. **An assessment's fingerprint is not bound to its report's subject.** Probe S110 admitted an assessment of `report-t5` with `review_subject_fingerprint="review-subject-fp-other"`.

## Restored baseline

Both runtime hashes equal the frozen baseline after the last run (table under Scope and method). Each suite was run once, one at a time, on the restored baseline with `python3 -m pytest packs/core/tests/skills/work-loop/<suite> -q -p no:cacheprovider`:

| Suite | Result | Time |
| --- | --- | ---: |
| `test_review_disposition.py` | 78 passed | 2.44 s |
| `test_review_persistence.py` | 33 passed | 3.72 s |
| `test_review_bridge.py` | 50 passed | 1.37 s |
| `test_evidence_store.py` | 110 passed | 1.86 s |
