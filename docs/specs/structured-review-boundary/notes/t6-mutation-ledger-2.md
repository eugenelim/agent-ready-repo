# T6 mutation evidence, second pass

Status: incomplete. 61 of the 65 cases in `test_review_compat.py` are proven by at least one counted single-property mutation. Four cases are NOT PROVEN, and no mutation of the two runtime files in scope can red them. 105 counted single-property mutations ran: 76 caught at least one case and 29 survived every case. Four compound diagnostics (`T6-DIAG-1` to `T6-DIAG-4`) back the analysis only and do not count. Both runtime hashes matched the baseline after every run and every probe.

**First-pass defects.** Four of the six are fixed (1, 2, 3, 6). Two are partly fixed (4, 5). See [First-pass defects re-probed](#first-pass-defects-re-probed).

**New runtime defects.** Five. The worst is a one-sided write: a report is stored, then the adapter raises before any assessment. See [New runtime defects](#new-runtime-defects).

**The repaired defects are mostly unpinned.** No test reds when D2 is reverted (T6-MUT-200), when D1 is reverted to the pre-fix classifier (T6-MUT-021), when D4's unknown-major rule is reverted (T6-MUT-053B), when D5's adjudication refusal is removed (T6-MUT-011), or when D6 is reverted (T6-MUT-101). D3 is pinned by `test_d3_*`. D5's profile fix is pinned (T6-MUT-013).

## Scope and method

Targets: all 65 cases of `packs/core/tests/skills/work-loop/test_review_compat.py`. That is 54 single-case functions, 9 corpus rows, and 2 `test_d3` rows.

Each run used this command from the execution root: `python3 -m pytest packs/core/tests/skills/work-loop/test_review_compat.py -q -p no:cacheprovider --tb=long --junitxml=<scratch>`. Each mutation reports every case it catches.

A catch needs exit 1 and a runtime failure inside a test body. Four kinds count:

- **assertion:** an `assert` in the test body fails. This includes a subprocess check that fails its own assertion.
- **did-not-raise:** a `pytest.raises` block saw no raise. No case uses one.
- **test-body-raise:** the test body raises on the subject's output.
- **unexpected-raise:** the code under test raises while the failing test statement calls `reconcile_review_source_event`, `review_readiness`, or the loop-engine caller. A raise from a setup helper does not count.

Collection, import, syntax, fixture-setup, and timeout failures do not count. None occurred.

Each mutation is one exact-string replacement in one runtime file. `T6-MUT-154` is one logical edit (wrap the caller's return) split over two lines; it counts as one. The helpers are in `$HOME/.slice2-scratch/t6-mut2/` (`run.py`, `mutations.py`, `probe_under.py`, `probe/probe2.py`, `tables.py`), copied from the first pass with the new baseline hash. Every replacement is checked in memory before anything is written: the old string occurs exactly once, the new string occurs exactly once after replacement, no string is empty, and the result compiles. Restoration is the inverse exact replacement, then a sha256 check of both files. Only `_review_compat.py` and `project_compat_reconcile_review_source_event` in `loop-engine.py` were mutated. No test or other repository file was edited. No restoration incident occurred.

Baseline sha256, checked before the first run, after every run and probe, and at the end:

| File | sha256 |
| --- | --- |
| `_review_compat.py` | `d1bb92e80dae9bf757372d49bf5591d08ab202845bb90fa161d1b0b8e12a6bf5` |
| `loop-engine.py` | `c2bf88cc8e962d0553bd65f580f260919a2e74e081dba1c131086472d7b4cfa1` |

### Changes from the first pass

- Dropped: T6-MUT-075 (the dead audit-less branch was removed) and T6-MUT-164B (`packs/contracts/delivery/` does not exist, and the spy now anchors at the repository root).
- Re-targeted to the new code: 020 (byte equality), 093 (`if not agrees`), 097 and 101 (the `_unable()` closure).
- Added for the repairs: 011 to 013 (D5), 021 to 023 (D1), 033 (structural-clean predicate), 053B and 053C (D4), 101B and 104 (D6), 132B and 134 (temp/I-O), 141B (unable key set), 153 and 154 (caller), 165 and 166 (cohort-state writes), 190 to 196 (D3), 200 to 205 (D2).

## Completed checks

| Mutation | Guarded behavior | Catching cases |
| --- | --- | ---: |
| T6-MUT-001 | closed form gate: a form outside the closed set returns unable | 0 |
| T6-MUT-002 | step-5 dispatch: an unknown form falls to unable (second form check) | 0 |
| T6-DIAG-2 | COMPOUND: closed form gate + step-5 unknown-form fallback | 2 |
| T6-MUT-010 | content-safety refusal of the raw report returns unable before any write | 0 |
| T6-MUT-011 | D5: content-safety refusal of the adjudication text returns unable before any write | 0 |
| T6-MUT-012 | D5: adjudication text is content-checked at all (gate on presence not inverted) | 30 |
| T6-MUT-013 | D5: adjudication check uses the registered review-report profile (pre-fix profile) | 23 |
| T6-MUT-020 | D1: direct-clean refuses any text that is not the exact sentinel | 1 |
| T6-MUT-021 | D1: direct-clean uses byte equality, not the legacy raw classifier (pre-fix revert) | 0 |
| T6-MUT-022 | D1: direct-clean refuses the sentinel plus a trailing newline | 0 |
| T6-MUT-023 | D1: direct-clean compares against loop-cohort's CLEAN_SUBSTRING (not a prefix test) | 0 |
| T6-MUT-030 | structural-clean requires the legacy raw classification to be clean | 2 |
| T6-MUT-031 | structural-clean refuses a report carrying a '## Not checked' footer | 1 |
| T6-MUT-032 | structural-clean: a footer-free clean report maps to clean (footer predicate not inverted) | 2 |
| T6-MUT-033 | structural-clean uses the legacy raw classifier, not byte equality | 2 |
| T6-MUT-040 | findings form: grammar-invalid text maps to unable (not indeterminate) | 1 |
| T6-MUT-041 | findings form: grammar-valid findings without adjudication map to indeterminate | 2 |
| T6-MUT-050 | adjudicated: a missing adjudication text maps to indeterminate | 1 |
| T6-MUT-051 | adjudicated: a non-JSON raw report maps to indeterminate | 1 |
| T6-MUT-052 | adjudicated: an empty or non-list finding set maps to indeterminate | 1 |
| T6-MUT-053 | adjudicated: every finding must validate as finding.v1 | 1 |
| T6-MUT-053B | D4: an unknown-major finding maps to unable (pre-fix: indeterminate) | 0 |
| T6-MUT-053C | D4: a missing-field finding maps to indeterminate, not unable | 1 |
| T6-MUT-054 | adjudicated: a non-JSON adjudication text maps to indeterminate | 1 |
| T6-MUT-055 | adjudicated: the audit must be a JSON object | 1 |
| T6-MUT-056 | adjudicated: audit ids match finding ids one-to-one (guard removed) | 2 |
| T6-MUT-057 | adjudicated: an extra audit id maps to indeterminate (subset check only) | 1 |
| T6-MUT-058 | adjudicated: each audit entry must be an object | 1 |
| T6-MUT-059 | adjudicated: decision is in the closed set {sustained, refuted} | 1 |
| T6-MUT-060 | adjudicated: the closed decision set contains refuted | 9 |
| T6-MUT-061 | adjudicated: authority_ref must be a non-empty string | 1 |
| T6-MUT-070 | sustained is assessed through the independent-authority judgment (supported) | 1 |
| T6-MUT-071 | sustained is NOT forced to unsupported-opinion (refuted branch only for refuted) | 2 |
| T6-MUT-072 | refuted maps to unsupported-opinion (not the sustained/supported branch) | 1 |
| T6-MUT-073 | refuted: controlled fact falsifiable-delivery-failure is False | 2 |
| T6-MUT-074 | sustained: the authority judgment requests supported | 2 |
| T6-MUT-080 | legacy presence via last_review_record_operation_id | 1 |
| T6-MUT-081 | transition_history: match on transition_id removed | 11 |
| T6-MUT-082 | transition_history: only an entry with the same transition_id counts | 1 |
| T6-MUT-083 | transition_history: only reviewers-clean maps to a clean legacy outcome | 1 |
| T6-MUT-084 | transition_history: findings-remain maps to a findings legacy outcome | 2 |
| T6-MUT-085 | transition_history: reviewers-clean maps to a clean legacy outcome | 9 |
| T6-MUT-090 | agreement: legacy clean agrees only with a structured clean result | 2 |
| T6-MUT-091 | agreement: legacy findings agrees only with a structured findings result | 1 |
| T6-MUT-092 | agreement: legacy findings + structured findings acknowledges | 1 |
| T6-MUT-093 | divergent: event disagreement sets divergent True | 3 |
| T6-MUT-094 | divergent is False when the legacy outcome is unknown (op id only) | 1 |
| T6-MUT-095 | acknowledgement requires the legacy side to be present | 4 |
| T6-MUT-096 | an absent legacy side short-circuits to not acknowledged / not divergent | 0 |
| T6-MUT-097 | unable is never acknowledged | 3 |
| T6-MUT-098 | agreement: indeterminate is never acknowledged against legacy clean | 1 |
| T6-MUT-190 | D3: a clean digest mismatch blocks acknowledgement (pre-fix: digest ignored) | 2 |
| T6-MUT-191 | D3: a clean digest mismatch sets divergent True | 2 |
| T6-MUT-192 | D3: the digest is checked only when this source is the latest-recorded review | 0 |
| T6-MUT-193 | D3: the digest is checked only for a clean result (findings by event) | 1 |
| T6-MUT-194 | D3: the digest is computed over the request's form | 0 |
| T6-MUT-195 | D3: the digest is computed over the request's exact report bytes | 5 |
| T6-MUT-196 | D3: the latest-recorded predicate is not skipped (digest never checked) | 2 |
| T6-MUT-100 | a classifier unable result returns before any persistence | 4 |
| T6-MUT-101 | D6: structured_present on the unable path reads the store (pre-fix: hard-coded False) | 0 |
| T6-MUT-101B | structured_present on the unable path is not hard-coded True | 8 |
| T6-MUT-102 | a fresh event persists its report (write not skipped) | 14 |
| T6-MUT-103 | structured_present on the success path is True | 3 |
| T6-MUT-104 | D6/D2: the early store lookup sets already_structured from the store | 0 |
| T6-MUT-200 | D2: a stored status that differs from this request is refused (pre-fix: ignored) | 0 |
| T6-MUT-201 | D2: the conflict path reports the stored result, not the request's | 0 |
| T6-MUT-202 | D2: the conflict path never acknowledges | 0 |
| T6-MUT-203 | D2: the conflict path carries the denial code | 0 |
| T6-MUT-204 | D2: the conflict path reports structured_present True | 0 |
| T6-MUT-205 | D2: the conflict path reports legacy_present from the legacy check | 0 |
| T6-MUT-110 | replay: an existing report for the source event is not rewritten | 0 |
| T6-MUT-111 | idempotency lookup matches lineage.source_event_id | 0 |
| T6-MUT-112 | crash recovery: an existing report with missing assessments writes them | 2 |
| T6-MUT-113 | crash recovery runs for findings results with audit entries | 2 |
| T6-MUT-114 | crash recovery: already-assessed findings are excluded from missing_findings | 0 |
| T6-MUT-115 | assessment writer skips finding ids already persisted | 0 |
| T6-MUT-116 | existing assessment ids are scoped to this report_id | 1 |
| T6-MUT-117 | a fresh findings result writes its assessments in the same reconcile | 4 |
| T6-DIAG-1 | COMPOUND: missing_findings filter + skip_finding_ids filter | 0 |
| T6-DIAG-3 | COMPOUND: 114 + 115 + random assessment transaction id | 1 |
| T6-DIAG-4 | COMPOUND: idempotency lookup + random report transaction id | 3 |
| T6-MUT-120 | deterministic report_id derived from source_event_id | 1 |
| T6-MUT-121 | deterministic report transaction id | 0 |
| T6-MUT-122 | deterministic assessment id | 1 |
| T6-MUT-123 | deterministic assessment transaction id | 0 |
| T6-MUT-124 | lineage carries the source_event_id (structured side identity) | 1 |
| T6-MUT-130 | the classifier temp directory is created under the store root | 1 |
| T6-MUT-131 | the classifier temp directory is removed after use | 1 |
| T6-MUT-132 | a store without a Path _root refuses with unable | 1 |
| T6-MUT-132B | a store whose _root directory is missing refuses (missing-root refusal) | 0 |
| T6-MUT-133 | a classifier I/O failure maps to error (then unable), not a raise | 1 |
| T6-MUT-134 | a classifier I/O failure maps to a non-clean classification | 1 |
| T6-MUT-140 | return carries divergent | 10 |
| T6-MUT-141 | return carries no field outside the closed six (success path) | 1 |
| T6-MUT-141B | return carries no field outside the closed six (unable path) | 0 |
| T6-MUT-142 | return echoes source_event_id | 7 |
| T6-MUT-143 | return carries legacy_present from the legacy check | 3 |
| T6-MUT-150 | loop-engine exposes project_compat_reconcile_review_source_event | 4 |
| T6-MUT-151 | caller passes legacy_state through unchanged | 1 |
| T6-MUT-152 | caller passes source_event through unchanged | 1 |
| T6-MUT-153 | caller passes review_policy through unchanged | 0 |
| T6-MUT-154 | caller returns the adapter result unchanged (acknowledged forced False) | 1 |
| T6-MUT-160 | VI-1012: no reviewer role-name literal in shipped review modules | 1 |
| T6-MUT-161 | VI-1018: no initial-plan-review.v1 reference in Slice 2 review modules | 1 |
| T6-MUT-162 | VI-1018: no mutable-task projection API in Slice 2 review modules | 1 |
| T6-MUT-163 | VI-1019: no non-stdlib, non-sibling import (agentbundle in a function body) | 1 |
| T6-MUT-164 | VI-1019: the runtime opens no file under <repo>/contracts/delivery/ | 1 |
| T6-MUT-165 | VI-1018: the adapter never writes cohort state.json | 1 |
| T6-MUT-166 | VI-1018: the adapter never mutates the caller's legacy_state mapping | 0 |

`T6-DIAG-1` to `T6-DIAG-4` apply two or three counted mutations at once. None counts toward proof.

`T6-MUT-012` inverts the presence gate, so every call with `adjudication_text=None` raises `AttributeError`. `T6-MUT-013` restores the pre-fix unregistered profile, so every adjudicated call returns `unable`. Both are blunt. A case listed only under them is proven, but only for "the adapter runs".

## Mutation details

| Mutation | File | Exact mutation | Observed failures | Restored |
| --- | --- | --- | --- | --- |
| T6-MUT-001 | compat | `if form not in _CLOSED_FORMS:⏎ return _unable()` → `if False:⏎ return _unable()` | none (survived) | OK |
| T6-MUT-002 | compat | `else:⏎ return _unable()⏎⏎ if result == "unable":` → `else:⏎ result, findings = "clean", []⏎⏎ if result == "unable":` | none (survived) | OK |
| T6-DIAG-2 | compat | compound: T6-MUT-001 + T6-MUT-002 | `corpus[unknown-form]` (assertion); `vi1013_out_of_corpus_input_refused` (assertion) | OK |
| T6-MUT-010 | compat | `if not cs_decision.accepted:⏎ return _unable()` → `if False:⏎ return _unable()` | none (survived) | OK |
| T6-MUT-011 | compat | `if not adj_cs_decision.accepted:⏎ return _unable()` → `if False:⏎ return _unable()` | none (survived) | OK |
| T6-MUT-012 | compat | `if adjudication_text is not None:⏎ adj_cs_decision` → `if adjudication_text is None:⏎ adj_cs_decision` | `corpus[direct-clean]` (unexpected-raise); `corpus[findings-no-adjudication]` (unexpected-raise); `corpus[one-sided-legacy-present]` (unexpected-raise); `corpus[one-sided-legacy-absent]` (unexpected-raise); `vi1013_crash_before_acknowledgement_is_idempotent` (unexpected-raise); `vi1018_authority_isolation` (unexpected-raise); +24 more | OK |
| T6-MUT-013 | compat | `adj_cs_decision = cs.check_content_safety(⏎ "review-report",` → `adj_cs_decision = cs.check_content_safety(⏎ "review-adjudication",` | `corpus[adjudicated-all-refuted]` (assertion); `corpus[adjudicated-sustained]` (assertion); `corpus[safe-unmappable]` (assertion); `vi1019_self_containment` (assertion); `vi1019_spy_detects_contracts_delivery_access` (assertion); `c2_sustained_finding_produces_findings_result_not_eligible` (assertion); +17 more | OK |
| T6-MUT-020 | compat | `if raw_report_text.encode("utf-8") != sentinel:⏎ return "unable", []` → `if False:⏎ return "unable", []` | `t4_020_direct_clean_requires_sentinel_text` (assertion) | OK |
| T6-MUT-021 | compat | `if raw_report_text.encode("utf-8") != sentinel:` → `if _run_classify_raw_report(source_event_id, raw_report_text, store_root).get("classification") != "clean":` | none (survived) | OK |
| T6-MUT-022 | compat | `if raw_report_text.encode("utf-8") != sentinel:` → `if raw_report_text.rstrip("\n").encode("utf-8") != sentinel:` | none (survived) | OK |
| T6-MUT-023 | compat | `if raw_report_text.encode("utf-8") != sentinel:` → `if not raw_report_text.encode("utf-8").startswith(sentinel):` | none (survived) | OK |
| T6-MUT-030 | compat | `if result.get("classification") != "clean":⏎ return "unable", []` → `if False:⏎ return "unable", []` | `c1_structural_clean_rejects_findings_text` (assertion); `t4_133_classifier_io_failure_returns_unable` (assertion) | OK |
| T6-MUT-031 | compat | `if result.get("not_checked_present"):⏎ return "unable", []` → `if False:⏎ return "unable", []` | `t4_031_structural_clean_rejects_not_checked_footer` (assertion) | OK |
| T6-MUT-032 | compat | `if result.get("not_checked_present"):⏎ return "unable", []` → `if not result.get("not_checked_present"):⏎ return "unable", []` | `c1_structural_clean_accepts_exact_clean_text` (assertion); `t4_031_structural_clean_rejects_not_checked_footer` (assertion) | OK |
| T6-MUT-033 | compat | `result = _run_classify_raw_report(source_event_id, raw_report_text, store_root)⏎ if result.get("classification") != "clean":` → `result = {"classification": "clean" if raw_report_text == _cohort().CLEAN_SUBSTRING else "error"}⏎ if result.get("classification") != "clean…` | `t4_130_temp_dir_under_store_root` (assertion); `t4_133_classifier_io_failure_returns_unable` (assertion) | OK |
| T6-MUT-040 | compat | `if result.get("classification") == "findings":⏎ # Grammar-valid` → `if True:⏎ # Grammar-valid` | `c5_grammar_invalid_findings_produces_unable` (assertion) | OK |
| T6-MUT-041 | compat | `return "indeterminate", []⏎ # Grammar-invalid` → `return "unable", []⏎ # Grammar-invalid` | `corpus[findings-no-adjudication]` (assertion); `t4_098_indeterminate_never_acknowledged_against_legacy_clean` (assertion) | OK |
| T6-MUT-050 | compat | `if adjudication_text is None:⏎ return "indeterminate", [], []` → `if False:⏎ return "indeterminate", [], []` | `t4_050_adjudicated_none_adjudication_returns_indeterminate` (unexpected-raise) | OK |
| T6-MUT-051 | compat | `raw_findings = json.loads(raw_report_text)⏎ except (json.JSONDecodeError, ValueError):⏎ return "indeterminate", [], []` → `raw_findings = json.loads(raw_report_text)⏎ except (json.JSONDecodeError, ValueError):⏎ raise` | `corpus[safe-unmappable]` (unexpected-raise) | OK |
| T6-MUT-052 | compat | `if not isinstance(raw_findings, list) or not raw_findings:` → `if False:` | `t4_052_adjudicated_empty_finding_list_returns_indeterminate` (unexpected-raise) | OK |
| T6-MUT-053 | compat | `ok, code = contracts.validate_finding_dict(item)⏎ if not ok:` → `ok, code = contracts.validate_finding_dict(item)⏎ if False:` | `t4_053_invalid_finding_returns_indeterminate` (unexpected-raise) | OK |
| T6-MUT-053B | compat | `if code == "denied-unknown-schema-version":⏎ return "unable", [], []` → `if False:⏎ return "unable", [], []` | none (survived) | OK |
| T6-MUT-053C | compat | `return "unable", [], []⏎ return "indeterminate", [], []` → `return "unable", [], []⏎ return "unable", [], []` | `t4_053_invalid_finding_returns_indeterminate` (assertion) | OK |
| T6-MUT-054 | compat | `audit = json.loads(adjudication_text)⏎ except (json.JSONDecodeError, ValueError):⏎ return "indeterminate", [], []` → `audit = json.loads(adjudication_text)⏎ except (json.JSONDecodeError, ValueError):⏎ raise` | `t4_054_non_json_adjudication_returns_indeterminate` (unexpected-raise) | OK |
| T6-MUT-055 | compat | `if not isinstance(audit, dict):⏎ return "indeterminate", [], []` → `if False:⏎ return "indeterminate", [], []` | `t4_055_audit_not_dict_returns_indeterminate` (unexpected-raise) | OK |
| T6-MUT-056 | compat | `if raw_ids != audit_ids:` → `if False:` | `c2_id_mismatch_produces_indeterminate` (unexpected-raise); `t4_057_extra_audit_id_returns_indeterminate` (assertion) | OK |
| T6-MUT-057 | compat | `if raw_ids != audit_ids:` → `if raw_ids - audit_ids:` | `t4_057_extra_audit_id_returns_indeterminate` (assertion) | OK |
| T6-MUT-058 | compat | `if not isinstance(decision_entry, dict):⏎ return "indeterminate", [], []` → `if False:⏎ return "indeterminate", [], []` | `t4_058_audit_entry_not_dict_returns_indeterminate` (unexpected-raise) | OK |
| T6-MUT-059 | compat | `if decision not in _CLOSED_AUDIT_DECISIONS:` → `if False:` | `c2_bad_decision_produces_indeterminate` (assertion) | OK |
| T6-MUT-060 | compat | `_CLOSED_AUDIT_DECISIONS: frozenset[str] = frozenset({"sustained", "refuted"})` → `_CLOSED_AUDIT_DECISIONS: frozenset[str] = frozenset({"sustained"})` | `corpus[adjudicated-all-refuted]` (assertion); `vi1019_self_containment` (assertion); `vi1019_spy_detects_contracts_delivery_access` (assertion); `c2_all_refuted_produces_acceptance_eligible` (assertion); `c4_crash_recovery_writes_missing_assessments` (assertion); `t4_072_refuted_material_produces_unsupported_opinion_and_eligible` (assertion); +3 more | OK |
| T6-MUT-061 | compat | `if not isinstance(authority_ref, str) or not authority_ref:` → `if False:` | `t4_061_empty_authority_ref_returns_indeterminate` (assertion) | OK |
| T6-MUT-070 | compat | `predicate_version=_COMPAT_PREDICATE_VERSION,⏎ independent_authority=independent_authority,⏎ )` → `predicate_version=_COMPAT_PREDICATE_VERSION,⏎ independent_authority=None,⏎ )` | `t4_070_sustained_produces_supported_assessment` (assertion) | OK |
| T6-MUT-071 | compat | `if decision == "refuted":⏎ # Refuted findings` → `if True:⏎ # Refuted findings` | `c2_sustained_finding_produces_findings_result_not_eligible` (assertion); `t4_070_sustained_produces_supported_assessment` (assertion) | OK |
| T6-MUT-072 | compat | `if decision == "refuted":⏎ # Refuted findings` → `if False:⏎ # Refuted findings` | `t4_072_refuted_material_produces_unsupported_opinion_and_eligible` (assertion) | OK |
| T6-MUT-073 | compat | `controlled_facts={"falsifiable-delivery-failure": False},` → `controlled_facts={"falsifiable-delivery-failure": True},` | `c2_all_refuted_produces_acceptance_eligible` (assertion); `t4_072_refuted_material_produces_unsupported_opinion_and_eligible` (assertion) | OK |
| T6-MUT-074 | compat | `"requested_judgment": "supported",` → `"requested_judgment": "unsupported-opinion",` | `c2_sustained_finding_produces_findings_result_not_eligible` (assertion); `t4_070_sustained_produces_supported_assessment` (assertion) | OK |
| T6-MUT-080 | compat | `if legacy_state.get("last_review_record_operation_id") == source_event_id:⏎ return True, None` → `if False:⏎ return True, None` | `t4_080_operation_id_sets_legacy_present` (assertion) | OK |
| T6-MUT-081 | compat | `if isinstance(entry, dict) and entry.get("transition_id") == source_event_id:` → `if False:` | `corpus[direct-clean]` (assertion); `corpus[one-sided-legacy-present]` (assertion); `vi1013_crash_before_acknowledgement_is_idempotent` (assertion); `c3_transition_history_clean_acknowledged` (assertion); `c3_transition_history_divergent` (assertion); `t4_090_clean_legacy_with_findings_result_not_acknowledged` (assertion); +5 more | OK |
| T6-MUT-082 | compat | `if isinstance(entry, dict) and entry.get("transition_id") == source_event_id:` → `if isinstance(entry, dict) and entry.get("transition_id") is not None:` | `t4_082_different_transition_id_no_legacy_present` (assertion) | OK |
| T6-MUT-083 | compat | `if event == _LEGACY_CLEAN_EVENT:` → `if event != _LEGACY_FINDINGS_EVENT:` | `t4_083_unrecognised_event_no_legacy_present` (assertion) | OK |
| T6-MUT-084 | compat | `if event == _LEGACY_FINDINGS_EVENT:⏎ return True, "findings"` → `if False:⏎ return True, "findings"` | `c3_transition_history_divergent` (assertion); `t4_092_findings_legacy_with_findings_result_acknowledged` (assertion) | OK |
| T6-MUT-085 | compat | `if event == _LEGACY_CLEAN_EVENT:⏎ return True, "clean"` → `if False:⏎ return True, "clean"` | `corpus[direct-clean]` (assertion); `corpus[one-sided-legacy-present]` (assertion); `vi1013_crash_before_acknowledgement_is_idempotent` (assertion); `c3_transition_history_clean_acknowledged` (assertion); `t4_090_clean_legacy_with_findings_result_not_acknowledged` (assertion); `t4_098_indeterminate_never_acknowledged_against_legacy_clean` (assertion); +3 more | OK |
| T6-MUT-090 | compat | `agrees = (legacy_event == "clean" and result == "clean") or (` → `agrees = (legacy_event == "clean") or (` | `t4_090_clean_legacy_with_findings_result_not_acknowledged` (assertion); `t4_098_indeterminate_never_acknowledged_against_legacy_clean` (assertion) | OK |
| T6-MUT-091 | compat | `legacy_event == "findings" and result == "findings"⏎ )` → `legacy_event == "findings"⏎ )` | `c3_transition_history_divergent` (assertion) | OK |
| T6-MUT-092 | compat | `legacy_event == "findings" and result == "findings"⏎ )` → `False⏎ )` | `t4_092_findings_legacy_with_findings_result_acknowledged` (assertion) | OK |
| T6-MUT-093 | compat | `if not agrees:⏎ return False, True` → `if not agrees:⏎ return False, False` | `c3_transition_history_divergent` (assertion); `t4_090_clean_legacy_with_findings_result_not_acknowledged` (assertion); `t4_098_indeterminate_never_acknowledged_against_legacy_clean` (assertion) | OK |
| T6-MUT-094 | compat | `if legacy_event is None:⏎ # Legacy recorded but event unknown — cannot verify event agreement.⏎ return False, False` → `if False:⏎ # Legacy recorded but event unknown — cannot verify event agreement.⏎ return False, False` | `t4_094_op_id_only_state_is_not_divergent` (assertion) | OK |
| T6-MUT-095 | compat | `if not legacy_present:⏎ return False, False` → `if not legacy_present:⏎ return result == "clean", False` | `corpus[one-sided-legacy-absent]` (assertion); `vi1013_crash_before_acknowledgement_is_idempotent` (assertion); `t4_082_different_transition_id_no_legacy_present` (assertion); `t4_083_unrecognised_event_no_legacy_present` (assertion) | OK |
| T6-MUT-096 | compat | `if not legacy_present:⏎ return False, False` → `if False:⏎ return False, False` | none (survived) | OK |
| T6-MUT-097 | compat | `"structured_present": already_structured, # D6: reflects store state⏎ "acknowledged": False,` → `"structured_present": already_structured, # D6: reflects store state⏎ "acknowledged": True,` | `corpus[unknown-form]` (assertion); `corpus[content-safety-refused]` (assertion); `vi1013_out_of_corpus_input_refused` (assertion) | OK |
| T6-MUT-098 | compat | `agrees = (legacy_event == "clean" and result == "clean") or (` → `agrees = (legacy_event == "clean" and result in ("clean", "indeterminate")) or (` | `t4_098_indeterminate_never_acknowledged_against_legacy_clean` (assertion) | OK |
| T6-MUT-190 | compat | `if legacy_state.get("last_review_record_payload_digest") != expected:⏎ return False, True` → `if False:⏎ return False, True` | `d3_clean_digest_mismatch_is_divergent[unrelated-digest]` (assertion); `d3_clean_digest_mismatch_is_divergent[wrong-form-digest]` (assertion) | OK |
| T6-MUT-191 | compat | `if legacy_state.get("last_review_record_payload_digest") != expected:⏎ return False, True` → `if legacy_state.get("last_review_record_payload_digest") != expected:⏎ return False, False` | `d3_clean_digest_mismatch_is_divergent[unrelated-digest]` (assertion); `d3_clean_digest_mismatch_is_divergent[wrong-form-digest]` (assertion) | OK |
| T6-MUT-192 | compat | `and legacy_state.get("last_review_record_operation_id") == source_event_id⏎ ):` → `and True⏎ ):` | none (survived) | OK |
| T6-MUT-193 | compat | `result == "clean"⏎ and legacy_state.get("last_review_record_operation_id")` → `result in ("clean", "findings")⏎ and legacy_state.get("last_review_record_operation_id")` | `t4_092_findings_legacy_with_findings_result_acknowledged` (assertion) | OK |
| T6-MUT-194 | compat | `expected = _cohort()._review_payload_digest(⏎ form, hashlib` → `expected = _cohort()._review_payload_digest(⏎ "direct-clean", hashlib` | none (survived) | OK |
| T6-MUT-195 | compat | `form, hashlib.sha256(raw_report_text.encode("utf-8")).hexdigest()` → `form, hashlib.sha256(raw_report_text.strip().encode("utf-8") + b"\n").hexdigest()` | `corpus[direct-clean]` (assertion); `corpus[one-sided-legacy-present]` (assertion); `vi1013_crash_before_acknowledgement_is_idempotent` (assertion); `c3_transition_history_clean_acknowledged` (assertion); `t4_151_caller_passes_legacy_state` (assertion) | OK |
| T6-MUT-196 | compat | `and legacy_state.get("last_review_record_operation_id") == source_event_id⏎ ):` → `and False⏎ ):` | `d3_clean_digest_mismatch_is_divergent[unrelated-digest]` (assertion); `d3_clean_digest_mismatch_is_divergent[wrong-form-digest]` (assertion) | OK |
| T6-MUT-100 | compat | `if result == "unable":⏎ return _unable()` → `if False:⏎ return _unable()` | `c1_structural_clean_rejects_findings_text` (assertion); `c5_grammar_invalid_findings_produces_unable` (assertion); `t4_020_direct_clean_requires_sentinel_text` (assertion); `t4_031_structural_clean_rejects_not_checked_footer` (assertion) | OK |
| T6-MUT-101 | compat | `"structured_present": already_structured, # D6: reflects store state` → `"structured_present": False, # D6: reflects store state` | none (survived) | OK |
| T6-MUT-101B | compat | `"structured_present": already_structured, # D6: reflects store state` → `"structured_present": True, # D6: reflects store state` | `corpus[unknown-form]` (assertion); `corpus[content-safety-refused]` (assertion); `c1_structural_clean_rejects_findings_text` (assertion); `c5_grammar_invalid_findings_produces_unable` (assertion); `t4_010_content_safety_refusal_returns_unable` (assertion); `t4_020_direct_clean_requires_sentinel_text` (assertion); +2 more | OK |
| T6-MUT-102 | compat | `if not already_structured:⏎ report = _build_compat_report(` → `if False:⏎ report = _build_compat_report(` | `corpus[adjudicated-all-refuted]` (unexpected-raise); `corpus[adjudicated-sustained]` (unexpected-raise); `vi1013_crash_before_acknowledgement_is_idempotent` (assertion); `vi1019_self_containment` (assertion); `vi1019_spy_detects_contracts_delivery_access` (assertion); `c2_sustained_finding_produces_findings_result_not_eligible` (unexpected-raise); +8 more | OK |
| T6-MUT-103 | compat | `"structured_present": structured_present,⏎ "acknowledged": acknowledged,` → `"structured_present": False,⏎ "acknowledged": acknowledged,` | `vi1013_crash_before_acknowledgement_is_idempotent` (assertion); `c4_crash_recovery_writes_missing_assessments` (assertion); `c6_return_value_has_required_fields` (assertion) | OK |
| T6-MUT-104 | compat | `already_structured: bool = existing_report is not None` → `already_structured: bool = False` | none (survived) | OK |
| T6-MUT-200 | compat | `if stored_status != result:` → `if False:` | none (survived) | OK |
| T6-MUT-201 | compat | `"result": stored_status,` → `"result": result,` | none (survived) | OK |
| T6-MUT-202 | compat | `"structured_present": True,⏎ "acknowledged": False,⏎ "divergent": False,⏎ "_conflict"` → `"structured_present": True,⏎ "acknowledged": True,⏎ "divergent": False,⏎ "_conflict"` | none (survived) | OK |
| T6-MUT-203 | compat | `"_conflict": "denied-compat-source-event-conflict",⏎` → `"_conflict": "",⏎` | none (survived) | OK |
| T6-MUT-204 | compat | `"structured_present": True,⏎ "acknowledged": False,⏎ "divergent": False,⏎ "_conflict"` → `"structured_present": False,⏎ "acknowledged": False,⏎ "divergent": False,⏎ "_conflict"` | none (survived) | OK |
| T6-MUT-205 | compat | `"legacy_present": legacy_present,⏎ "structured_present": True,` → `"legacy_present": False,⏎ "structured_present": True,` | none (survived) | OK |
| T6-MUT-110 | compat | `if not already_structured:⏎ report = _build_compat_report(` → `if True:⏎ report = _build_compat_report(` | none (survived) | OK |
| T6-MUT-111 | compat | `if record.get("lineage", {}).get("source_event_id") == source_event_id:⏎ return record⏎ return None` → `if False:⏎ return record⏎ return None` | none (survived) | OK |
| T6-MUT-112 | compat | `if missing_findings:` → `if False:` | `c4_crash_recovery_writes_missing_assessments` (assertion); `t4_116_assessments_scoped_to_report` (assertion) | OK |
| T6-MUT-113 | compat | `if result == "findings" and findings and audit_entries:⏎ existing_assessment_ids` → `if False:⏎ existing_assessment_ids` | `c4_crash_recovery_writes_missing_assessments` (assertion); `t4_116_assessments_scoped_to_report` (assertion) | OK |
| T6-MUT-114 | compat | `if f["finding_id"] not in existing_assessment_ids⏎` → `if f["finding_id"] or existing_assessment_ids⏎` | none (survived) | OK |
| T6-MUT-115 | compat | `if finding_id in skip_finding_ids:⏎ continue` → `if False:⏎ continue` | none (survived) | OK |
| T6-MUT-116 | compat | `if r.get("report_id") == report_id⏎` → `if True⏎` | `t4_116_assessments_scoped_to_report` (assertion) | OK |
| T6-MUT-117 | compat | `# Write assessments for findings from adjudicated form.⏎ if result == "findings" and findings and audit_entries:` → `# Write assessments for findings from adjudicated form.⏎ if False:` | `c2_all_refuted_produces_acceptance_eligible` (assertion); `t4_070_sustained_produces_supported_assessment` (assertion); `t4_072_refuted_material_produces_unsupported_opinion_and_eligible` (assertion); `t4_120_123_deterministic_ids` (assertion) | OK |
| T6-DIAG-1 | compat | compound: T6-MUT-114 + T6-MUT-115 | none (survived) | OK |
| T6-DIAG-3 | compat | compound: T6-MUT-114 + T6-MUT-115 + T6-MUT-123 | `c4_crash_recovery_writes_missing_assessments` (unexpected-raise) | OK |
| T6-DIAG-4 | compat | compound: T6-MUT-111 + T6-MUT-121 | `vi1013_crash_before_acknowledgement_is_idempotent` (unexpected-raise); `c4_crash_recovery_writes_missing_assessments` (unexpected-raise); `t4_116_assessments_scoped_to_report` (unexpected-raise) | OK |
| T6-MUT-120 | compat | `"report_id": f"compat-report:{source_event_id}",` → `"report_id": f"compat-report:{source_event_id}:{os.urandom(4).hex()}",` | `t4_120_123_deterministic_ids` (assertion) | OK |
| T6-MUT-121 | compat | `transaction_id=f"compat-tx:{source_event_id}:report",` → `transaction_id=f"compat-tx:{source_event_id}:report:{os.urandom(4).hex()}",` | none (survived) | OK |
| T6-MUT-122 | compat | `assessment_id = f"compat-assessment:{source_event_id}:{finding_id}"` → `assessment_id = f"compat-assessment:{source_event_id}:{finding_id}:{os.urandom(4).hex()}"` | `t4_120_123_deterministic_ids` (assertion) | OK |
| T6-MUT-123 | compat | `transaction_id=f"compat-tx:{source_event_id}:assess:{finding_id}",` → `transaction_id=f"compat-tx:{source_event_id}:assess:{finding_id}:{os.urandom(4).hex()}",` | none (survived) | OK |
| T6-MUT-124 | compat | `"source_event_id": source_event_id,⏎ "producer": "compat-adapter",` → `"source_event_id": f"{source_event_id}:{os.urandom(4).hex()}",⏎ "producer": "compat-adapter",` | `vi1013_crash_before_acknowledgement_is_idempotent` (unexpected-raise) | OK |
| T6-MUT-130 | compat | `tmpdir = Path(tempfile.mkdtemp(dir=str(store_root)))` → `tmpdir = Path(tempfile.mkdtemp())` | `t4_130_temp_dir_under_store_root` (assertion) | OK |
| T6-MUT-131 | compat | `shutil.rmtree(str(tmpdir), ignore_errors=True)` → `tmpdir.exists()` | `t4_131_temp_dir_removed_after_classification` (assertion) | OK |
| T6-MUT-132 | compat | `if store_root is None or not isinstance(store_root, Path):⏎ return _unable()` → `if False:⏎ return _unable()` | `t4_132_store_without_root_returns_unable` (unexpected-raise) | OK |
| T6-MUT-132B | compat | `if store_root is None or not isinstance(store_root, Path):⏎ return _unable()` → `if store_root is None or not isinstance(store_root, Path) or not store_root.is_dir():⏎ return _unable()` | none (survived) | OK |
| T6-MUT-133 | compat | `except Exception: # noqa: BLE001⏎ return {"classification": "error", "_reason": "io-failure", "not_checked_present": False}` → `except Exception: # noqa: BLE001⏎ raise` | `t4_133_classifier_io_failure_returns_unable` (test-body-raise) | OK |
| T6-MUT-134 | compat | `return {"classification": "error", "_reason": "io-failure", "not_checked_present": False}` → `return {"classification": "clean", "_reason": "io-failure", "not_checked_present": False}` | `t4_133_classifier_io_failure_returns_unable` (assertion) | OK |
| T6-MUT-140 | compat | `"acknowledged": acknowledged,⏎ "divergent": divergent,⏎ }` → `"acknowledged": acknowledged,⏎ }` | `c3_transition_history_clean_acknowledged` (test-body-raise); `c3_transition_history_divergent` (test-body-raise); `c6_return_value_has_required_fields` (assertion); `t4_090_clean_legacy_with_findings_result_not_acknowledged` (test-body-raise); `t4_092_findings_legacy_with_findings_result_acknowledged` (test-body-raise); `t4_094_op_id_only_state_is_not_divergent` (test-body-raise); +4 more | OK |
| T6-MUT-141 | compat | `"acknowledged": acknowledged,⏎ "divergent": divergent,⏎ }` → `"acknowledged": acknowledged,⏎ "divergent": divergent,⏎ "legacy_event": legacy_event,⏎ }` | `t4_141_return_value_has_exactly_six_keys` (assertion) | OK |
| T6-MUT-141B | compat | `"acknowledged": False,⏎ "divergent": False,⏎ }` → `"acknowledged": False,⏎ "divergent": False,⏎ "_reason": "unable",⏎ }` | none (survived) | OK |
| T6-MUT-142 | compat | `return {⏎ "source_event_id": source_event_id,⏎ "result": result,` → `return {⏎ "source_event_id": role,⏎ "result": result,` | `corpus[direct-clean]` (assertion); `corpus[adjudicated-all-refuted]` (assertion); `corpus[adjudicated-sustained]` (assertion); `corpus[findings-no-adjudication]` (assertion); `corpus[safe-unmappable]` (assertion); `corpus[one-sided-legacy-present]` (assertion); +1 more | OK |
| T6-MUT-143 | compat | `"legacy_present": legacy_present,⏎ "structured_present": structured_present,` → `"legacy_present": False,⏎ "structured_present": structured_present,` | `c3_transition_history_clean_acknowledged` (assertion); `c3_transition_history_divergent` (assertion); `t4_080_operation_id_sets_legacy_present` (assertion) | OK |
| T6-MUT-150 | loop-engine | `def project_compat_reconcile_review_source_event(⏎` → `def project_compat_reconcile_review_source_event_renamed(⏎` | `vi1013_loop_engine_caller_exists` (assertion); `vi1018_authority_isolation` (test-body-raise); `t4_151_caller_passes_legacy_state` (test-body-raise); `t4_152_caller_passes_source_event` (test-body-raise) | OK |
| T6-MUT-151 | loop-engine | `source_event,⏎ legacy_state=legacy_state,⏎ review_subject=review_subject,⏎ review_policy=review_policy,⏎ issuer=issuer,⏎ grant=grant,⏎ audit…` → `source_event,⏎ legacy_state={},⏎ review_subject=review_subject,⏎ review_policy=review_policy,⏎ issuer=issuer,⏎ grant=grant,⏎ audit_sink=audi…` | `t4_151_caller_passes_legacy_state` (assertion) | OK |
| T6-MUT-152 | loop-engine | `return _review_compat().reconcile_review_source_event(⏎ store,⏎ source_event,⏎` → `return _review_compat().reconcile_review_source_event(⏎ store,⏎ {**source_event, "role": "caller-substituted-role"},⏎` | `t4_152_caller_passes_source_event` (assertion) | OK |
| T6-MUT-153 | loop-engine | `review_policy=review_policy,⏎ issuer=issuer,⏎ grant=grant,⏎ audit_sink=audit_sink,⏎ )⏎⏎⏎def _compat_facade` → `review_policy={},⏎ issuer=issuer,⏎ grant=grant,⏎ audit_sink=audit_sink,⏎ )⏎⏎⏎def _compat_facade` | none (survived) | OK |
| T6-MUT-154 | loop-engine | compound: open + close | `t4_151_caller_passes_legacy_state` (assertion) | OK |
| T6-MUT-160 | compat | `role: str = source_event["role"]` → `role: str = source_event.get("role") or "adversarial-reviewer"` | `vi1012_no_reviewer_role_literals_in_shipped_modules` (assertion) | OK |
| T6-MUT-161 | compat | `# Content-safety classification for legacy review text.` → `_TASK_APPROVAL_KIND: str = "initial-plan-review.v1"⏎⏎# Content-safety classification for legacy review text.` | `vi1018_initial_plan_review_not_consumed_as_task_approval` (assertion) | OK |
| T6-MUT-162 | compat | `# ── Public entry point ────` → `def approve_task_projection() -> None:⏎ """Injected violation."""⏎ raise NotImplementedError⏎⏎⏎# ── Public entry point ────` | `vi1018_no_mutable_task_projection_api` (assertion) | OK |
| T6-MUT-163 | compat | `global _content_safety_module⏎ if _content_safety_module is None:` → `global _content_safety_module⏎ if False:⏎ import agentbundle # noqa: F401⏎ if _content_safety_module is None:` | `vi1019_static_import_check` (assertion) | OK |
| T6-MUT-164 | compat | `cs = _content_safety()⏎` → `cs = _content_safety()⏎ try:⏎ open(str(_SCRIPTS_DIR.parents[5] / "contracts" / "delivery" / "review-report.v1.schema.json"), "rb").close()⏎ …` | `vi1019_self_containment` (assertion) | OK |
| T6-MUT-165 | compat | `cs = _content_safety()⏎` → `cs = _content_safety()⏎ _st = Path(str(getattr(store, "_root", "/nonexistent"))).parent / "repo" / "docs" / "specs" / "test-feature" / "stat…` | `vi1018_authority_isolation` (assertion) | OK |
| T6-MUT-166 | compat | `legacy_present, legacy_event = _determine_legacy_outcome(legacy_state, source_event_id)⏎` → `legacy_present, legacy_event = _determine_legacy_outcome(legacy_state, source_event_id)⏎ legacy_state["last_review_record_operation_id"] = s…` | none (survived) | OK |

## Test-to-mutation map

Mutation numbers drop the `T6-MUT-` prefix.

| Case | Caught by |
| --- | --- |
| `vi1012_clean_report_reaches_acceptance_eligible` | **NOT PROVEN** |
| `vi1012_unsupported_findings_report_reaches_acceptance_eligible` | **NOT PROVEN** |
| `vi1012_no_reviewer_role_literals_in_shipped_modules` | 160 |
| `corpus[direct-clean]` | 012, 081, 085, 195, 142 |
| `corpus[adjudicated-all-refuted]` | 013, 060, 102, 142 |
| `corpus[adjudicated-sustained]` | 013, 102, 142 |
| `corpus[findings-no-adjudication]` | 012, 041, 142 |
| `corpus[unknown-form]` | 097, 101B |
| `corpus[content-safety-refused]` | 097, 101B |
| `corpus[safe-unmappable]` | 013, 051, 142 |
| `corpus[one-sided-legacy-present]` | 012, 081, 085, 195, 142 |
| `corpus[one-sided-legacy-absent]` | 012, 095, 142 |
| `vi1013_out_of_corpus_input_refused` | 097 |
| `vi1013_crash_before_acknowledgement_is_idempotent` | 012, 081, 085, 095, 195, 102, 103, 124 |
| `vi1013_loop_engine_caller_exists` | 150 |
| `vi1018_authority_isolation` | 012, 150, 165 |
| `vi1018_initial_plan_review_not_consumed_as_task_approval` | 161 |
| `vi1018_no_mutable_task_projection_api` | 162 |
| `vi1019_self_containment` | 012, 013, 060, 102, 164 |
| `vi1019_package_check_detects_violation` | **NOT PROVEN** |
| `vi1019_spy_detects_contracts_delivery_access` | 012, 013, 060, 102 |
| `vi1019_static_check_detects_agentbundle_import` | **NOT PROVEN** |
| `vi1019_static_import_check` | 163 |
| `c1_structural_clean_rejects_findings_text` | 012, 030, 100, 101B |
| `c1_structural_clean_accepts_exact_clean_text` | 012, 032 |
| `c2_sustained_finding_produces_findings_result_not_eligible` | 013, 071, 074, 102 |
| `c2_all_refuted_produces_acceptance_eligible` | 013, 060, 073, 102, 117 |
| `c2_id_mismatch_produces_indeterminate` | 013, 056 |
| `c2_bad_decision_produces_indeterminate` | 013, 059 |
| `c3_transition_history_clean_acknowledged` | 012, 081, 085, 195, 140, 143 |
| `c3_transition_history_divergent` | 012, 081, 084, 091, 093, 140, 143 |
| `c4_crash_recovery_writes_missing_assessments` | 013, 060, 103, 112, 113 |
| `c5_grammar_invalid_findings_produces_unable` | 012, 040, 100, 101B |
| `c6_return_value_has_required_fields` | 012, 103, 140 |
| `t4_010_content_safety_refusal_returns_unable` | 101B |
| `t4_020_direct_clean_requires_sentinel_text` | 012, 020, 100, 101B |
| `t4_031_structural_clean_rejects_not_checked_footer` | 012, 031, 032, 100, 101B |
| `t4_050_adjudicated_none_adjudication_returns_indeterminate` | 012, 050 |
| `t4_052_adjudicated_empty_finding_list_returns_indeterminate` | 013, 052 |
| `t4_053_invalid_finding_returns_indeterminate` | 013, 053, 053C |
| `t4_054_non_json_adjudication_returns_indeterminate` | 013, 054 |
| `t4_055_audit_not_dict_returns_indeterminate` | 013, 055 |
| `t4_057_extra_audit_id_returns_indeterminate` | 013, 056, 057 |
| `t4_058_audit_entry_not_dict_returns_indeterminate` | 013, 058 |
| `t4_061_empty_authority_ref_returns_indeterminate` | 013, 061 |
| `t4_070_sustained_produces_supported_assessment` | 013, 070, 071, 074, 102, 117 |
| `t4_072_refuted_material_produces_unsupported_opinion_and_eligible` | 013, 060, 072, 073, 102, 117 |
| `t4_080_operation_id_sets_legacy_present` | 012, 080, 143 |
| `t4_082_different_transition_id_no_legacy_present` | 012, 082, 095 |
| `t4_083_unrecognised_event_no_legacy_present` | 012, 083, 095 |
| `t4_090_clean_legacy_with_findings_result_not_acknowledged` | 013, 081, 085, 090, 093, 102, 140 |
| `t4_092_findings_legacy_with_findings_result_acknowledged` | 013, 060, 081, 084, 092, 193, 102, 140 |
| `t4_094_op_id_only_state_is_not_divergent` | 012, 094, 140 |
| `t4_098_indeterminate_never_acknowledged_against_legacy_clean` | 012, 041, 081, 085, 090, 093, 098, 140 |
| `t4_116_assessments_scoped_to_report` | 013, 060, 102, 112, 113, 116 |
| `t4_120_123_deterministic_ids` | 013, 060, 102, 117, 120, 122 |
| `t4_130_temp_dir_under_store_root` | 012, 033, 130 |
| `t4_131_temp_dir_removed_after_classification` | 012, 131 |
| `t4_132_store_without_root_returns_unable` | 101B, 132 |
| `t4_133_classifier_io_failure_returns_unable` | 012, 030, 033, 133, 134 |
| `t4_141_return_value_has_exactly_six_keys` | 012, 140, 141 |
| `t4_151_caller_passes_legacy_state` | 012, 081, 085, 195, 150, 151, 154 |
| `t4_152_caller_passes_source_event` | 012, 102, 150, 152 |
| `d3_clean_digest_mismatch_is_divergent[unrelated-digest]` | 012, 081, 085, 190, 191, 196, 140 |
| `d3_clean_digest_mismatch_is_divergent[wrong-form-digest]` | 012, 081, 085, 190, 191, 196, 140 |

## NOT PROVEN

No mutation of `_review_compat.py` or the loop-engine caller can red these four cases.

- `test_vi1012_clean_report_reaches_acceptance_eligible` and `test_vi1012_unsupported_findings_report_reaches_acceptance_eligible`. Shape: **an unreachable path.** Both drive `_review_persistence`, `_review_assessment`, `_review_bridge`, and `_review_disposition` directly and never call the adapter. Their subject is outside the mutation scope. They can be proven only by mutating those modules.
- `test_vi1019_package_check_detects_violation`. Shape: **an absence something else guarantees.** The script exits at check 1, before it loads any review module. The outcome depends only on the stub `agentbundle` on `PYTHONPATH`. It proves the harness, not the runtime.
- `test_vi1019_static_check_detects_agentbundle_import`. Shape: **an absence something else guarantees.** It appends its own `import agentbundle` to a copy and scans the copy. Any runtime source that parses gives a hit. The T3 hash check now compares against a hash taken before injection, but the test never writes the original, so it cannot fail either. It proves the scanner, not the runtime.

## Proven, with a caveat

- `test_vi1019_spy_detects_contracts_delivery_access` is caught only when the injected script crashes before it prints `SPY_OPEN_COUNT` (012, 013, 060, 102). The real violation, T6-MUT-164, does not red it. Its count assertion (`int(count) > 0`) holds for every runtime that finishes, because module loads are opens. It never asserts exit 1 or that stderr names `.spy-probe-t1`. Its closing hash check still compares the file with itself. Shape: **a message from a different rule.** One input would make it catch the spy: assert `returncode == 1` and `".spy-probe-t1" in stderr`.
- `test_vi1019_self_containment` now catches a read of the real `<repo>/contracts/delivery/review-report.v1.schema.json` (T6-MUT-164). The first-pass test defect is fixed.
- `test_vi1018_authority_isolation` now calls the adapter and catches a write to its `state.json` (T6-MUT-165). It does not catch an in-place change to the caller's `legacy_state` mapping (T6-MUT-166), because it compares only the file. Step 3 still calls `pytest.skip` when `loop-cohort init` fails, so a broken cohort skips it.
- `test_t4_010_content_safety_refusal_returns_unable` and `corpus[content-safety-refused]` do not pin the content-safety guard (T6-MUT-010 survives). Shape: **two sufficient mechanisms.** The T4-010 text is direct-clean and fails D1 byte equality. The corpus text fails the structural grammar. Both are proven only for `structured_present` and acknowledgement (101B, 097).
- `test_t4_020_direct_clean_requires_sentinel_text` uses findings text, which also fails the pre-fix classifier. So reverting D1 to the classifier (T6-MUT-021) survives. Shape: **two sufficient mechanisms.** It pins only "some check exists" (T6-MUT-020).
- `test_t4_053_invalid_finding_returns_indeterminate` pins missing-field → `indeterminate` (053C). That conflicts with the spec row "Schema-invalid or unknown-major report → `unable`, do not persist". See defect 4.
- `test_d3_clean_digest_mismatch_is_divergent[wrong-form-digest]` uses only the direct-clean form. Hard-coding the digest form to `direct-clean` (T6-MUT-194) survives.
- `corpus[unknown-form]` and `test_vi1013_out_of_corpus_input_refused` survive 001 and 002 alone (**two sufficient mechanisms**). Only compound DIAG-2 reds them on result. They are proven by 097 and 101B.

## UNCAUGHT GUARD

Each entry names the single input that would catch it. It gives the baseline result and the result under the mutation, both observed by probe (`probe/probe2.py`, run on the baseline and through `probe_under.py`). "Wrong" means the mutated behaviour breaks the spec.

### (i) Reachable but untested: 19 mutations (18 guards, plus 132B)

| Mutation | Single catching input | Baseline | Under mutation |
| --- | --- | --- | --- |
| 010 raw content safety | findings form, `_FINDINGS_TEXT` plus a line `token ghp_` + 36×`A` | `unable`, 0 records | `indeterminate`, report persisted. Wrong. Same for an adjudicated finding whose `observation` holds the token. |
| 011 D5 adjudication refusal | adjudicated refuted finding, `authority_ref` = `ghp_` + 36×`A` | `unable`, 0 records | `findings`, report and assessment persisted. Wrong. |
| 021 D1 pre-fix classifier | direct-clean `Clean — ready to commit.⏎` | `unable`, 0 records | `clean`, persisted. Wrong. Same for the `## Not checked` footer text. |
| 022 D1 trailing newline | direct-clean `Clean — ready to commit.⏎` | `unable` | `clean`, persisted. Wrong. |
| 023 D1 prefix match | direct-clean `Clean — ready to commit. extra` | `unable` | `clean`, persisted. Wrong. |
| 053B D4 unknown major | adjudicated finding with `schema_version: 2` | `unable`, 0 records | `indeterminate`, `compat-report:e` persisted. Wrong. |
| 101 D6 unable path | store a clean report for `e`, then replay `e` as structural-clean `Clean \x01 bad` | `structured_present: True` | `False`. Wrong. |
| 104 D6/D2 early lookup | same replay as 101; or findings-form `e` then direct-clean `e` | `structured_present: True`; conflict result | `False`; the second call raises `EvidenceStoreRefused: lifecycle request differs from committed transaction`. Wrong. |
| 192 D3 latest-recorded predicate | `reviewers-clean` entry for `e`, `last_review_record_operation_id: "later"`, digest `WRONG` | ack `True` | ack `False`, divergent `True`. Wrong by the docstring rule. |
| 194 D3 digest form | structural-clean `Clean — ready to commit.` with the structural-clean digest | ack `True` | ack `False`, divergent `True`. Wrong. |
| 200 D2 conflict refusal | findings-form `e`, then direct-clean `e` with a matching `reviewers-clean` state | conflict, result `indeterminate`, ack `False` | result `clean`, ack `True`; store still holds only `indeterminate`. Wrong (first-pass defect 2 returns). |
| 201 D2 stored result | same as 200 | result `indeterminate` | result `clean`. Wrong. |
| 202 D2 never acknowledge | same as 200 | ack `False` | ack `True`. Wrong. |
| 203 D2 denial code | same as 200; assert `_conflict` | `denied-compat-source-event-conflict` | `""`. Wrong. |
| 204 D2 structured_present | same as 200 | `True` | `False`. Wrong. |
| 205 D2 legacy_present | same as 200 | `True` | `False`. Wrong. |
| 141B unable key set | unknown form; assert `set(result) ==` the six keys | six keys | adds `_reason`. Wrong. |
| 166 caller's legacy_state | pass a dict; compare it after the call | unchanged | `last_review_record_operation_id` overwritten. Wrong. |
| 132B missing root directory | a store whose `_root` names a missing directory, direct-clean | raises `EvidenceStoreError` | `unable`. This mutation adds a refusal; it exposes defect N5, not a missing test of an existing guard. |

### (ii) Two sufficient mechanisms or masked by the store: 9 mutations

- **001 and 002** (form gate and step-5 fallback). Each alone returns `unable` for an unknown form. DIAG-2 catches 2 cases.
- **096** (absent-legacy short-circuit). When legacy is absent, `legacy_event` is `None`, so the next check returns the same pair. No input separates them.
- **110 and 111** (replay rewrite and lineage lookup). An exact replay is an identical store transaction, which the store accepts as a retry. A differing replay now stops at the D2 check first. DIAG-4 (111 plus a random report transaction id) catches 3 cases with `composed record ID already admitted`.
- **114 and 115** (the missing-findings filter and the skip set). Each alone filters, and the store retry masks both. DIAG-1 survives. DIAG-3 (plus a random assessment transaction id) catches `test_c4`.
- **121 and 123** (deterministic transaction ids). With the report-id and skip guards in place, a replay writes nothing, so the transaction id is never reused. They matter only combined (DIAG-3, DIAG-4).

### (ii) Unreachable by construction: 1 mutation

- **153** (the caller drops `review_policy`). `_review_compat.py` never reads `review_policy`. It appears only in the signature and the call. No input can show the change.

## First-pass defects re-probed

All probes ran on the baseline with hashes checked.

1. **Direct-clean accepts non-exact text. Fixed.** `Clean — ready to commit.⏎`, the `## Not checked` footer text, and `Clean — ready to commit. extra` each return `unable` with 0 records.
2. **Replay acknowledges against a different stored fact. Fixed.** Findings-form `e`, then direct-clean `e` with a matching `reviewers-clean` state, returns `result: indeterminate` (the stored status), `acknowledged: False`, and `_conflict: denied-compat-source-event-conflict`. The store keeps one `indeterminate` report. Residuals are defects N1 and N4.
3. **The legacy payload digest is ignored. Fixed for the latest-recorded clean event.** `WRONG-DIGEST` gives ack `False`, divergent `True`. The correct digest acknowledges. A structural-clean report with a direct-clean digest gives ack `False`. An older clean event (not the latest operation id) acknowledges by event alone, which the docstring states is intended.
4. **Schema-invalid adjudicated findings persist as `indeterminate`. Partly fixed.** `schema_version: 2` now returns `unable` with 0 records. A finding missing `rule_ref`, or with `material: "yes"`, still returns `indeterminate` and stores `compat-report:e` with that status. The spec row "Schema-invalid or unknown-major report" requires `unable` and no persisted semantic report. `test_t4_053` asserts the contrary behaviour.
5. **Adjudication text gets no content safety; a downstream refusal leaves a one-sided write. Partly fixed.** A raw `ghp_` credential in `authority_ref` now returns `unable` with 0 records. Validation is still not complete before the first write. Two inputs store a `findings` report, then raise with 0 assessments:
   - sustained `authority_ref` `"a\x01b"`. `json.dumps` escapes it to `\u0001`, so it passes the text check. Then `ReviewAssessmentRefused: generated finding assessment is invalid: denied-content-safety-rejected-encoding`.
   - two findings with the same `finding_id`. Then `ReviewAssessmentRefused: finding must be embedded in the current report`.
   Readiness stays non-eligible, so both fail closed. The spec still requires `unable` with nothing persisted.
6. **`structured_present` is not read from the store. Fixed.** After a clean report for `e`, replays of `e` that end `unable` (content-safety refused, unknown form, non-exact direct-clean) return `structured_present: True`.

## New runtime defects

- **N1. The conflict return has seven keys.** The D2 path adds `_conflict` to the six closed fields. The C6 and T4-141 docstrings say "exactly" six. No test covers the conflict path.
- **N2. Partial write, then raise.** See defect 5. The escaped control character and the duplicate finding id both store a report with no assessments and raise instead of returning `unable`.
- **N3. A JSON-escaped control character bypasses raw content safety.** An adjudicated finding with `observation` `"bad\x01obs"` is checked as escaped JSON text and passes. Finding validation then fails, and the adapter stores `compat-report:e` as `indeterminate` with no findings. The spec row "Report refused by the shared content-safety policy" requires `unable` and no persisted report. A literal credential is caught, because it survives JSON escaping.
- **N4. A same-status replay with a different finding set raises.** Adjudicated `e` with finding `f-probe` (refuted), then adjudicated `e` with finding `f-two` (sustained). Both are `findings`, so D2 does not fire. Crash recovery tries to assess `f-two` against the stored report and raises `ReviewAssessmentRefused: finding must be embedded in the current report`. Nothing new is written. The D2 rule compares only `terminal_status`, so a differing request with the same status is not refused as a conflict.
- **N5. A missing root directory raises on direct-clean.** With `_root` naming a missing directory, structural-clean returns `unable` (I/O mapped to error), but direct-clean no longer uses a temp file. It reaches the store write and raises `EvidenceStoreError: advisory lock path is outside root`. The guard checks only that `_root` is a `Path`.

## Restored baseline

Both hashes equal the baseline. `python3 -m pytest packs/core/tests/skills/work-loop/test_review_compat.py -q -p no:cacheprovider`: 65 passed in 3.60s.
