# T6 mutation evidence

Status: incomplete. 28 of the 34 cases in `test_review_compat.py` are proven by at least one counted single-property mutation. Six cases are NOT PROVEN, and none of them can be reached by a mutation of the two runtime files in scope. 76 counted single-property mutations ran: 35 caught at least one case and 41 survived every case. Four compound diagnostics (`T6-DIAG-1` to `T6-DIAG-4`) back the analysis only and do not count. Both runtime hashes matched the baseline after every run and every probe.

**Runtime defects found.** Probes on the baseline show six behaviours that break the spec's Compatibility corpus. The worst two are a clean report the legacy path would refuse, and an acknowledgement over a stored fact that disagrees. See [Runtime findings](#runtime-findings).

**Test defect found.** The VI-1019 file-open spy watches `packs/contracts/delivery/`, not the repository's `contracts/delivery/`. A runtime read of `contracts/delivery/review-report.v1.schema.json` passes the suite (T6-MUT-164). The same read aimed at `packs/contracts/delivery/` is caught (T6-MUT-164B).

## Scope and method

Targets: all 34 cases of `packs/core/tests/skills/work-loop/test_review_compat.py`, which are 25 single-case functions plus 9 corpus rows.

Each run used this command from the execution root: `python3 -m pytest packs/core/tests/skills/work-loop/test_review_compat.py -q -p no:cacheprovider --tb=long --junitxml=<scratch>`. Each mutation reports every case it catches.

A catch needs exit 1 and a runtime failure inside a test body. Four kinds count:

- **assertion:** an `assert` in the test body fails.
- **did-not-raise:** a `pytest.raises` block saw no raise. No case in this suite uses one.
- **test-body-raise:** the test body raises on the subject's output, such as a `KeyError` on a missing return field.
- **unexpected-raise:** the code under test raises while the failing test statement calls `reconcile_review_source_event`, `review_readiness`, or the loop-engine caller. A raise from a setup helper does not count.

The classifier reads the deepest traceback frame. A runtime `assert` (such as `_review_compat.py:715`) is therefore an unexpected-raise, not a test assertion. Collection, import, syntax, fixture-setup, and timeout failures do not count. Only one occurred, in a retired attempt (see [Retired attempt](#retired-attempt)).

Each mutation is one exact-string replacement in one runtime file. The helper is in `$HOME/.slice2-scratch/t6-mut/` and follows the T5 pass. It checks every replacement in memory before writing anything: the old string must occur exactly once, the new string must occur exactly once after replacement, and no string may be empty. Restoration is the inverse exact replacement, followed by a sha256 check of both files. Only `_review_compat.py` and the body of `project_compat_reconcile_review_source_event` in `loop-engine.py` were mutated. No test or other repository file was edited. No restoration incident occurred. Probes ran on the baseline or under one registered mutation through the same apply, restore, and hash-check helper (`probe_under.py`).

Baseline sha256, checked before the first run, after every run and probe, and at the end:

| File | sha256 |
| --- | --- |
| `_review_compat.py` | `672f027b70166330e669f72112df87e8e2f95c2ab7719c2eec0137f43a1c5c24` |
| `loop-engine.py` | `c2bf88cc8e962d0553bd65f580f260919a2e74e081dba1c131086472d7b4cfa1` |

### Retired attempt

The first T6-MUT-152 (`return dict(...` with no closing parenthesis) was a syntax error. It errored one case at fixture setup, and it made `test_vi1018_authority_isolation` skip because `loop-engine.py init` failed. It counted nothing and is excluded. The registered T6-MUT-152 is its replacement. The skip matters: that case skips instead of failing when the engine cannot start.

## Completed checks

| Mutation | Guarded behavior | Catching cases |
| --- | --- | ---: |
| T6-MUT-001 | closed form gate: a form outside the closed set returns unable | 0 |
| T6-MUT-002 | step-6 dispatch: an unknown form falls to unable (second form check) | 0 |
| T6-MUT-010 | content-safety refusal returns unable before any classification or write | 0 |
| T6-MUT-020 | direct-clean requires the legacy raw classification to be clean | 0 |
| T6-MUT-030 | structural-clean requires the legacy raw classification to be clean | 1 |
| T6-MUT-031 | structural-clean refuses a report carrying a '## Not checked' footer | 0 |
| T6-MUT-040 | findings form: grammar-invalid text maps to unable (not indeterminate) | 1 |
| T6-MUT-041 | findings form: grammar-valid findings without adjudication map to indeterminate | 1 |
| T6-MUT-050 | adjudicated: a missing adjudication text maps to indeterminate | 0 |
| T6-MUT-051 | adjudicated: a non-JSON raw report maps to indeterminate | 1 |
| T6-MUT-052 | adjudicated: an empty or non-list finding set maps to indeterminate | 0 |
| T6-MUT-053 | adjudicated: every finding must validate as finding.v1 | 0 |
| T6-MUT-054 | adjudicated: a non-JSON adjudication text maps to indeterminate | 0 |
| T6-MUT-055 | adjudicated: the audit must be a JSON object | 0 |
| T6-MUT-056 | adjudicated: audit ids match finding ids one-to-one (guard removed) | 1 |
| T6-MUT-057 | adjudicated: an audit id with no finding (extra audit entry) maps to indeterminate | 0 |
| T6-MUT-058 | adjudicated: each audit entry must be an object | 0 |
| T6-MUT-059 | adjudicated: decision is in the closed set {sustained, refuted} | 1 |
| T6-MUT-060 | adjudicated: the closed decision set contains refuted | 4 |
| T6-MUT-061 | adjudicated: authority_ref must be a non-empty string | 0 |
| T6-MUT-070 | sustained is assessed through the independent-authority judgment (supported) | 0 |
| T6-MUT-071 | sustained is NOT forced to unsupported-opinion (refuted branch only for refuted) | 1 |
| T6-MUT-072 | refuted maps to unsupported-opinion (not the sustained/supported branch) | 0 |
| T6-MUT-073 | refuted: controlled fact falsifiable-delivery-failure is False | 1 |
| T6-MUT-074 | sustained: the authority judgment requests supported | 1 |
| T6-MUT-075 | non-audited finding falls back to unsupported-opinion (audit-less branch) | 0 |
| T6-MUT-080 | legacy presence via last_review_record_operation_id | 0 |
| T6-MUT-081 | legacy presence via transition_history: the entry's transition_id must equal the source event id (match removed) | 5 |
| T6-MUT-082 | legacy presence via transition_history: only an entry with the same transition_id counts | 0 |
| T6-MUT-083 | transition_history: only reviewers-clean maps to a clean legacy outcome | 0 |
| T6-MUT-084 | transition_history: findings-remain maps to a findings legacy outcome | 1 |
| T6-MUT-085 | transition_history: reviewers-clean maps to a clean legacy outcome | 4 |
| T6-MUT-090 | agreement: legacy clean agrees only with a structured clean result | 0 |
| T6-MUT-091 | agreement: legacy findings agrees only with a structured findings result | 1 |
| T6-MUT-092 | agreement: legacy findings + structured findings acknowledges | 0 |
| T6-MUT-093 | divergent: disagreement sets divergent True | 1 |
| T6-MUT-094 | divergent is False when the legacy outcome is unknown (op id only) | 0 |
| T6-MUT-095 | acknowledgement requires the legacy side to be present | 2 |
| T6-MUT-096 | an absent legacy side short-circuits to not acknowledged / not divergent | 0 |
| T6-MUT-097 | unable is never acknowledged | 3 |
| T6-MUT-098 | agreement: indeterminate is never acknowledged against legacy clean | 0 |
| T6-MUT-100 | a classifier unable result returns before any persistence | 2 |
| T6-MUT-101 | structured_present on the unable path is False | 4 |
| T6-MUT-102 | a fresh event persists its report (write not skipped) | 6 |
| T6-MUT-103 | structured_present on the success path is True | 3 |
| T6-MUT-110 | replay: an existing report for the source event is not rewritten | 0 |
| T6-MUT-111 | idempotency lookup matches lineage.source_event_id | 0 |
| T6-MUT-112 | crash recovery: an existing report with missing assessments writes them | 1 |
| T6-MUT-113 | crash recovery runs for findings results with audit entries | 1 |
| T6-MUT-114 | crash recovery: already-assessed findings are excluded from missing_findings | 0 |
| T6-MUT-115 | assessment writer skips finding ids already persisted | 0 |
| T6-MUT-116 | existing assessment ids are scoped to this report_id | 0 |
| T6-MUT-117 | a fresh findings result writes its assessments in the same reconcile | 1 |
| T6-DIAG-1 | COMPOUND: missing_findings filter + skip_finding_ids filter | 0 |
| T6-DIAG-2 | COMPOUND: closed form gate + step-6 unknown-form fallback | 2 |
| T6-MUT-120 | deterministic report_id derived from source_event_id | 0 |
| T6-MUT-121 | deterministic report transaction id | 0 |
| T6-MUT-122 | deterministic assessment id | 0 |
| T6-MUT-123 | deterministic assessment transaction id | 0 |
| T6-MUT-124 | lineage carries the source_event_id (structured side identity) | 1 |
| T6-MUT-130 | the classifier temp directory is created under the store root | 0 |
| T6-MUT-131 | the classifier temp directory is removed after use | 0 |
| T6-MUT-132 | a store without a Path _root refuses with unable | 0 |
| T6-MUT-133 | a classifier I/O failure maps to error (then unable), not a raise | 0 |
| T6-MUT-140 | return carries divergent | 3 |
| T6-MUT-141 | return carries no field outside the closed six | 0 |
| T6-MUT-142 | return echoes source_event_id | 7 |
| T6-MUT-143 | return carries legacy_present from the legacy check | 2 |
| T6-MUT-150 | loop-engine exposes project_compat_reconcile_review_source_event | 1 |
| T6-MUT-151 | caller passes legacy_state through unchanged | 0 |
| T6-MUT-152 | caller passes source_event through unchanged | 0 |
| T6-MUT-160 | no reviewer role-name literal in shipped review modules | 1 |
| T6-MUT-161 | no initial-plan-review.v1 reference in Slice 2 review modules | 1 |
| T6-MUT-162 | no mutable-task projection API in Slice 2 review modules | 1 |
| T6-MUT-163 | no non-stdlib, non-sibling import (agentbundle in a function body) | 1 |
| T6-MUT-164 | the runtime opens no file under contracts/delivery/ | 0 |
| T6-MUT-164B | the runtime opens no file under the spy's resolved anchor (packs/contracts/delivery/) | 1 |
| T6-DIAG-3 | COMPOUND: missing_findings filter + skip_finding_ids filter + deterministic assessment transaction id | 1 |
| T6-DIAG-4 | COMPOUND: report-write skip on replay + idempotency lookup (store exact-retry dedupe left alone) | 2 |
| T6-MUT-032 | structural-clean: a footer-free clean report maps to clean (footer predicate not inverted) | 1 |

`T6-DIAG-1` to `T6-DIAG-4` are compound diagnostics. Each applies two or three counted mutations at once, so none counts toward proof.

## Mutation details

| Mutation | File | Exact mutation (`⏎` is a newline) | Observed failures (case @ test line, kind) | Restored |
| --- | --- | --- | --- | --- |
| T6-MUT-001 | `_review_compat.py` | `if form not in _CLOSED_FORMS:⏎ return _unable()` → `if False:⏎ return _unable()` | none (survived) | OK |
| T6-MUT-002 | `_review_compat.py` | `else:⏎ return _unable()⏎⏎ if result == "unable":` → `else:⏎ result, findings = "clean", []⏎⏎ if result == "unable":` | none (survived) | OK |
| T6-MUT-010 | `_review_compat.py` | `if not cs_decision.accepted:⏎ return _unable()` → `if False:⏎ return _unable()` | none (survived) | OK |
| T6-MUT-020 | `_review_compat.py` | `if result.get("classification") == "clean":⏎ return "clean", []` → `if True:⏎ return "clean", []` | none (survived) | OK |
| T6-MUT-030 | `_review_compat.py` | `if result.get("classification") != "clean":⏎ return "unable", []` → `if False:⏎ return "unable", []` | `c1_structural_clean_rejects_findings_text` @1606 (assertion) | OK |
| T6-MUT-031 | `_review_compat.py` | `if result.get("not_checked_present"):⏎ return "unable", []` → `if False:⏎ return "unable", []` | none (survived) | OK |
| T6-MUT-040 | `_review_compat.py` | `if result.get("classification") == "findings":⏎ # Grammar-valid` → `if True:⏎ # Grammar-valid` | `c5_grammar_invalid_findings_produces_unable` @2086 (assertion) | OK |
| T6-MUT-041 | `_review_compat.py` | `return "indeterminate", []⏎ # Grammar-invalid` → `return "unable", []⏎ # Grammar-invalid` | `corpus[findings-no-adjudication]` @742 (assertion) | OK |
| T6-MUT-050 | `_review_compat.py` | `if adjudication_text is None:⏎ return "indeterminate", [], []` → `if False:⏎ return "indeterminate", [], []` | none (survived) | OK |
| T6-MUT-051 | `_review_compat.py` | `raw_findings = json.loads(raw_report_text)⏎ except (json.JSONDecodeError, ValueError):⏎ return "indeterminate", [], []` → `raw_findings = json.loads(raw_report_text)⏎ except (json.JSONDecodeError, ValueError):⏎ raise` | `corpus[safe-unmappable]` @730 (unexpected-raise) | OK |
| T6-MUT-052 | `_review_compat.py` | `if not isinstance(raw_findings, list) or not raw_findings:` → `if False:` | none (survived) | OK |
| T6-MUT-053 | `_review_compat.py` | `ok, _code = contracts.validate_finding_dict(item)⏎ if not ok:` → `ok, _code = contracts.validate_finding_dict(item)⏎ if False:` | none (survived) | OK |
| T6-MUT-054 | `_review_compat.py` | `audit = json.loads(adjudication_text)⏎ except (json.JSONDecodeError, ValueError):⏎ return "indeterminate", [], []` → `audit = json.loads(adjudication_text)⏎ except (json.JSONDecodeError, ValueError):⏎ raise` | none (survived) | OK |
| T6-MUT-055 | `_review_compat.py` | `if not isinstance(audit, dict):⏎ return "indeterminate", [], []` → `if False:⏎ return "indeterminate", [], []` | none (survived) | OK |
| T6-MUT-056 | `_review_compat.py` | `if raw_ids != audit_ids:` → `if False:` | `c2_id_mismatch_produces_indeterminate` @1769 (unexpected-raise) | OK |
| T6-MUT-057 | `_review_compat.py` | `if raw_ids != audit_ids:` → `if raw_ids - audit_ids:` | none (survived) | OK |
| T6-MUT-058 | `_review_compat.py` | `if not isinstance(decision_entry, dict):⏎ return "indeterminate", [], []` → `if False:⏎ return "indeterminate", [], []` | none (survived) | OK |
| T6-MUT-059 | `_review_compat.py` | `if decision not in _CLOSED_AUDIT_DECISIONS:` → `if False:` | `c2_bad_decision_produces_indeterminate` @1827 (assertion) | OK |
| T6-MUT-060 | `_review_compat.py` | `_CLOSED_AUDIT_DECISIONS: frozenset[str] = frozenset({"sustained", "refuted"})` → `_CLOSED_AUDIT_DECISIONS: frozenset[str] = frozenset({"sustained"})` | `corpus[adjudicated-all-refuted]` @742 (assertion); `vi1019_self_containment` @1348 (assertion); `c2_all_refuted_produces_acceptance_eligible` @1743 (assertion); `c4_crash_recovery_writes_missing_assessments` @2012 (assertion) | OK |
| T6-MUT-061 | `_review_compat.py` | `if not isinstance(authority_ref, str) or not authority_ref:` → `if False:` | none (survived) | OK |
| T6-MUT-070 | `_review_compat.py` | `predicate_version=_COMPAT_PREDICATE_VERSION,⏎ independent_authority=independent_authority,⏎ )` → `predicate_version=_COMPAT_PREDICATE_VERSION,⏎ independent_authority=None,⏎ )` | none (survived) | OK |
| T6-MUT-071 | `_review_compat.py` | `if decision == "refuted":⏎ # Refuted findings` → `if True:⏎ # Refuted findings` | `c2_sustained_finding_produces_findings_result_not_eligible` @1700 (assertion) | OK |
| T6-MUT-072 | `_review_compat.py` | `if decision == "refuted":⏎ # Refuted findings` → `if False:⏎ # Refuted findings` | none (survived) | OK |
| T6-MUT-073 | `_review_compat.py` | `controlled_facts={"falsifiable-delivery-failure": False},⏎ controlled_edges={⏎ "rule-to-observation": None,⏎ "observation-to-reachable-path": None,⏎ "…` → `controlled_facts={"falsifiable-delivery-failure": True},⏎ controlled_edges={⏎ "rule-to-observation": None,⏎ "observation-to-reachable-path": None,⏎ "r…` | `c2_all_refuted_produces_acceptance_eligible` @1750 (assertion) | OK |
| T6-MUT-074 | `_review_compat.py` | `"requested_judgment": "supported",` → `"requested_judgment": "unsupported-opinion",` | `c2_sustained_finding_produces_findings_result_not_eligible` @1700 (assertion) | OK |
| T6-MUT-075 | `_review_compat.py` | `if audit_entry is None:⏎ # No audit entry` → `if False:⏎ # No audit entry` | none (survived) | OK |
| T6-MUT-080 | `_review_compat.py` | `if legacy_state.get("last_review_record_operation_id") == source_event_id:⏎ return True, None` → `if False:⏎ return True, None` | none (survived) | OK |
| T6-MUT-081 | `_review_compat.py` | `if isinstance(entry, dict) and entry.get("transition_id") == source_event_id:` → `if False:` | `corpus[direct-clean]` @745 (assertion); `corpus[one-sided-legacy-present]` @745 (assertion); `vi1013_crash_before_acknowledgement_is_idempotent` @843 (assertion); `c3_transition_history_clean_acknowledged` @1883 (assertion); `c3_transition_history_divergent` @1925 (assertion) | OK |
| T6-MUT-082 | `_review_compat.py` | `if isinstance(entry, dict) and entry.get("transition_id") == source_event_id:` → `if isinstance(entry, dict) and entry.get("transition_id") is not None:` | none (survived) | OK |
| T6-MUT-083 | `_review_compat.py` | `if event == _LEGACY_CLEAN_EVENT:` → `if event != _LEGACY_FINDINGS_EVENT:` | none (survived) | OK |
| T6-MUT-084 | `_review_compat.py` | `if event == _LEGACY_FINDINGS_EVENT:⏎ return True, "findings"` → `if False:⏎ return True, "findings"` | `c3_transition_history_divergent` @1925 (assertion) | OK |
| T6-MUT-085 | `_review_compat.py` | `if event == _LEGACY_CLEAN_EVENT:⏎ return True, "clean"` → `if False:⏎ return True, "clean"` | `corpus[direct-clean]` @745 (assertion); `corpus[one-sided-legacy-present]` @745 (assertion); `vi1013_crash_before_acknowledgement_is_idempotent` @843 (assertion); `c3_transition_history_clean_acknowledged` @1883 (assertion) | OK |
| T6-MUT-090 | `_review_compat.py` | `agrees = (legacy_event == "clean" and result == "clean") or (` → `agrees = (legacy_event == "clean") or (` | none (survived) | OK |
| T6-MUT-091 | `_review_compat.py` | `legacy_event == "findings" and result == "findings"⏎ )` → `legacy_event == "findings"⏎ )` | `c3_transition_history_divergent` @1922 (assertion) | OK |
| T6-MUT-092 | `_review_compat.py` | `legacy_event == "findings" and result == "findings"⏎ )` → `False⏎ )` | none (survived) | OK |
| T6-MUT-093 | `_review_compat.py` | `if agrees:⏎ return True, False⏎ return False, True` → `if agrees:⏎ return True, False⏎ return False, False` | `c3_transition_history_divergent` @1925 (assertion) | OK |
| T6-MUT-094 | `_review_compat.py` | `if legacy_event is None:⏎ # Legacy recorded but event unknown — cannot verify agreement.⏎ return False, False` → `if False:⏎ # Legacy recorded but event unknown — cannot verify agreement.⏎ return False, False` | none (survived) | OK |
| T6-MUT-095 | `_review_compat.py` | `if not legacy_present:⏎ return False, False` → `if not legacy_present:⏎ return result == "clean", False` | `corpus[one-sided-legacy-absent]` @745 (assertion); `vi1013_crash_before_acknowledgement_is_idempotent` @827 (assertion) | OK |
| T6-MUT-096 | `_review_compat.py` | `if not legacy_present:⏎ return False, False` → `if False:⏎ return False, False` | none (survived) | OK |
| T6-MUT-097 | `_review_compat.py` | `"structured_present": False,⏎ "acknowledged": False,` → `"structured_present": False,⏎ "acknowledged": True,` | `corpus[unknown-form]` @745 (assertion); `corpus[content-safety-refused]` @745 (assertion); `vi1013_out_of_corpus_input_refused` @786 (assertion) | OK |
| T6-MUT-098 | `_review_compat.py` | `agrees = (legacy_event == "clean" and result == "clean") or (` → `agrees = (legacy_event == "clean" and result in ("clean", "indeterminate")) or (` | none (survived) | OK |
| T6-MUT-100 | `_review_compat.py` | `if result == "unable":⏎ return _unable()` → `if False:⏎ return _unable()` | `c1_structural_clean_rejects_findings_text` @1609 (assertion); `c5_grammar_invalid_findings_produces_unable` @2089 (assertion) | OK |
| T6-MUT-101 | `_review_compat.py` | `"legacy_present": False,⏎ "structured_present": False,` → `"legacy_present": False,⏎ "structured_present": True,` | `corpus[unknown-form]` @751 (assertion); `corpus[content-safety-refused]` @751 (assertion); `c1_structural_clean_rejects_findings_text` @1609 (assertion); `c5_grammar_invalid_findings_produces_unable` @2089 (assertion) | OK |
| T6-MUT-102 | `_review_compat.py` | `if not already_structured:⏎ report = _build_compat_report(` → `if False:⏎ report = _build_compat_report(` | `corpus[adjudicated-all-refuted]` @730 (unexpected-raise); `corpus[adjudicated-sustained]` @730 (unexpected-raise); `vi1013_crash_before_acknowledgement_is_idempotent` @851 (assertion); `vi1019_self_containment` @1348 (assertion); `c2_sustained_finding_produces_findings_result_not_eligible` @1671 (unexpected-raise); `c2_all_refuted_produces_acceptance_eligible` @1723 (unexpected-raise) | OK |
| T6-MUT-103 | `_review_compat.py` | `"structured_present": structured_present,⏎ "acknowledged": acknowledged,` → `"structured_present": False,⏎ "acknowledged": acknowledged,` | `vi1013_crash_before_acknowledgement_is_idempotent` @826 (assertion); `c4_crash_recovery_writes_missing_assessments` @2013 (assertion); `c6_return_value_has_required_fields` @2134 (assertion) | OK |
| T6-MUT-110 | `_review_compat.py` | `if not already_structured:⏎ report = _build_compat_report(` → `if True:⏎ report = _build_compat_report(` | none (survived) | OK |
| T6-MUT-111 | `_review_compat.py` | `if record.get("lineage", {}).get("source_event_id") == source_event_id:⏎ return record⏎ return None` → `if False:⏎ return record⏎ return None` | none (survived) | OK |
| T6-MUT-112 | `_review_compat.py` | `if missing_findings:` → `if False:` | `c4_crash_recovery_writes_missing_assessments` @2018 (assertion) | OK |
| T6-MUT-113 | `_review_compat.py` | `if result == "findings" and findings and audit_entries:⏎ existing_assessment_ids` → `if False:⏎ existing_assessment_ids` | `c4_crash_recovery_writes_missing_assessments` @2018 (assertion) | OK |
| T6-MUT-114 | `_review_compat.py` | `if f["finding_id"] not in existing_assessment_ids⏎` → `if f["finding_id"] or existing_assessment_ids⏎` | none (survived) | OK |
| T6-MUT-115 | `_review_compat.py` | `if finding_id in skip_finding_ids:⏎ continue` → `if False:⏎ continue` | none (survived) | OK |
| T6-MUT-116 | `_review_compat.py` | `if r.get("report_id") == report_id⏎` → `if True⏎` | none (survived) | OK |
| T6-MUT-117 | `_review_compat.py` | `# Write assessments for findings from adjudicated form.⏎ if result == "findings" and findings and audit_entries:` → `# Write assessments for findings from adjudicated form.⏎ if False:` | `c2_all_refuted_produces_acceptance_eligible` @1750 (assertion) | OK |
| T6-DIAG-1 | `_review_compat.py` | compound of T6-MUT-114 + T6-MUT-115 | none (survived) | OK |
| T6-DIAG-2 | `_review_compat.py` | compound of T6-MUT-001 + T6-MUT-002 | `corpus[unknown-form]` @742 (assertion); `vi1013_out_of_corpus_input_refused` @785 (assertion) | OK |
| T6-MUT-120 | `_review_compat.py` | `"report_id": f"compat-report:{source_event_id}",` → `"report_id": f"compat-report:{source_event_id}:{os.urandom(4).hex()}",` | none (survived) | OK |
| T6-MUT-121 | `_review_compat.py` | `transaction_id=f"compat-tx:{source_event_id}:report",` → `transaction_id=f"compat-tx:{source_event_id}:report:{os.urandom(4).hex()}",` | none (survived) | OK |
| T6-MUT-122 | `_review_compat.py` | `assessment_id = f"compat-assessment:{source_event_id}:{finding_id}"` → `assessment_id = f"compat-assessment:{source_event_id}:{finding_id}:{os.urandom(4).hex()}"` | none (survived) | OK |
| T6-MUT-123 | `_review_compat.py` | `transaction_id=f"compat-tx:{source_event_id}:assess:{finding_id}",` → `transaction_id=f"compat-tx:{source_event_id}:assess:{finding_id}:{os.urandom(4).hex()}",` | none (survived) | OK |
| T6-MUT-124 | `_review_compat.py` | `"source_event_id": source_event_id,⏎ "producer": "compat-adapter",` → `"source_event_id": f"{source_event_id}:{os.urandom(4).hex()}",⏎ "producer": "compat-adapter",` | `vi1013_crash_before_acknowledgement_is_idempotent` @831 (unexpected-raise) | OK |
| T6-MUT-130 | `_review_compat.py` | `tmpdir = Path(tempfile.mkdtemp(dir=str(store_root)))` → `tmpdir = Path(tempfile.mkdtemp())` | none (survived) | OK |
| T6-MUT-131 | `_review_compat.py` | `shutil.rmtree(str(tmpdir), ignore_errors=True)` → `tmpdir.exists()` | none (survived) | OK |
| T6-MUT-132 | `_review_compat.py` | `if store_root is None or not isinstance(store_root, Path):⏎ return _unable()` → `if False:⏎ return _unable()` | none (survived) | OK |
| T6-MUT-133 | `_review_compat.py` | `except Exception: # noqa: BLE001⏎ return {"classification": "error", "_reason": "io-failure", "not_checked_present": False}` → `except Exception: # noqa: BLE001⏎ raise` | none (survived) | OK |
| T6-MUT-140 | `_review_compat.py` | `"acknowledged": acknowledged,⏎ "divergent": divergent,⏎ }` → `"acknowledged": acknowledged,⏎ }` | `c3_transition_history_clean_acknowledged` @1886 (test-body-raise); `c3_transition_history_divergent` @1925 (test-body-raise); `c6_return_value_has_required_fields` @2130 (assertion) | OK |
| T6-MUT-141 | `_review_compat.py` | `"acknowledged": acknowledged,⏎ "divergent": divergent,⏎ }` → `"acknowledged": acknowledged,⏎ "divergent": divergent,⏎ "legacy_event": legacy_event,⏎ }` | none (survived) | OK |
| T6-MUT-142 | `_review_compat.py` | `return {⏎ "source_event_id": source_event_id,⏎ "result": result,` → `return {⏎ "source_event_id": role,⏎ "result": result,` | `corpus[direct-clean]` @741 (assertion); `corpus[adjudicated-all-refuted]` @741 (assertion); `corpus[adjudicated-sustained]` @741 (assertion); `corpus[findings-no-adjudication]` @741 (assertion); `corpus[safe-unmappable]` @741 (assertion); `corpus[one-sided-legacy-present]` @741 (assertion); `corpus[one-sided-legacy-absent]` @741 (assertion) | OK |
| T6-MUT-143 | `_review_compat.py` | `"legacy_present": legacy_present,⏎ "structured_present": structured_present,` → `"legacy_present": False,⏎ "structured_present": structured_present,` | `c3_transition_history_clean_acknowledged` @1882 (assertion); `c3_transition_history_divergent` @1921 (assertion) | OK |
| T6-MUT-150 | `loop-engine.py` | `def project_compat_reconcile_review_source_event(⏎` → `def project_compat_reconcile_review_source_event_renamed(⏎` | `vi1013_loop_engine_caller_exists` @861 (assertion) | OK |
| T6-MUT-151 | `loop-engine.py` | `source_event,⏎ legacy_state=legacy_state,⏎ review_subject=review_subject,⏎ review_policy=review_policy,⏎ issuer=issuer,⏎ grant=grant,⏎ audit_sink=audi…` → `source_event,⏎ legacy_state={},⏎ review_subject=review_subject,⏎ review_policy=review_policy,⏎ issuer=issuer,⏎ grant=grant,⏎ audit_sink=audit_sink,⏎ )…` | none (survived) | OK |
| T6-MUT-152 | `loop-engine.py` | `return _review_compat().reconcile_review_source_event(⏎ store,⏎ source_event,⏎` → `return _review_compat().reconcile_review_source_event(⏎ store,⏎ {**source_event, "role": "caller-substituted-role"},⏎` | none (survived) | OK |
| T6-MUT-160 | `_review_compat.py` | `role: str = source_event["role"]` → `role: str = source_event.get("role") or "adversarial-reviewer"` | `vi1012_no_reviewer_role_literals_in_shipped_modules` @525 (assertion) | OK |
| T6-MUT-161 | `_review_compat.py` | `# Content-safety classification for legacy review text.` → `_TASK_APPROVAL_KIND: str = "initial-plan-review.v1"⏎⏎# Content-safety classification for legacy review text.` | `vi1018_initial_plan_review_not_consumed_as_task_approval` @1010 (assertion) | OK |
| T6-MUT-162 | `_review_compat.py` | `# ── Public entry point ────` → `def approve_task_projection() -> None:⏎ """Injected violation."""⏎ raise NotImplementedError⏎⏎⏎# ── Public entry point ────` | `vi1018_no_mutable_task_projection_api` @1042 (assertion) | OK |
| T6-MUT-163 | `_review_compat.py` | `global _content_safety_module⏎ if _content_safety_module is None:` → `global _content_safety_module⏎ if False:⏎ import agentbundle # noqa: F401⏎ if _content_safety_module is None:` | `vi1019_static_import_check` @1565 (assertion) | OK |
| T6-MUT-164 | `_review_compat.py` | `cs = _content_safety()⏎` → `cs = _content_safety()⏎ try:⏎ open(str(_SCRIPTS_DIR.parents[5] / "contracts" / "delivery" / "review-report.v1.schema.json"), "rb").close()⏎ except OSE…` | none (survived) | OK |
| T6-MUT-164B | `_review_compat.py` | `cs = _content_safety()⏎` → `cs = _content_safety()⏎ try:⏎ open(str(_SCRIPTS_DIR.parents[4] / "contracts" / "delivery" / "review-report.v1.schema.json"), "rb").close()⏎ except OSE…` | `vi1019_self_containment` @1348 (assertion) | OK |
| T6-DIAG-3 | `_review_compat.py` | compound of T6-MUT-114 + T6-MUT-115 + T6-MUT-123 | `c4_crash_recovery_writes_missing_assessments` @2023 (unexpected-raise) | OK |
| T6-DIAG-4 | `_review_compat.py` | compound of T6-MUT-111 + T6-MUT-121 | `vi1013_crash_before_acknowledgement_is_idempotent` @831 (unexpected-raise); `c4_crash_recovery_writes_missing_assessments` @1992 (unexpected-raise) | OK |
| T6-MUT-032 | `_review_compat.py` | `if result.get("not_checked_present"):⏎ return "unable", []` → `if not result.get("not_checked_present"):⏎ return "unable", []` | `c1_structural_clean_accepts_exact_clean_text` @1641 (assertion) | OK |

## Test-to-mutation map

| Case | Counted single mutations that red it |
| --- | --- |
| `vi1012_clean_report_reaches_acceptance_eligible` | **NOT PROVEN** |
| `vi1012_unsupported_findings_report_reaches_acceptance_eligible` | **NOT PROVEN** |
| `vi1012_no_reviewer_role_literals_in_shipped_modules` | T6-MUT-160 |
| `corpus[direct-clean]` | T6-MUT-081, T6-MUT-085, T6-MUT-142 |
| `corpus[adjudicated-all-refuted]` | T6-MUT-060, T6-MUT-102, T6-MUT-142 |
| `corpus[adjudicated-sustained]` | T6-MUT-102, T6-MUT-142 |
| `corpus[findings-no-adjudication]` | T6-MUT-041, T6-MUT-142 |
| `corpus[unknown-form]` | T6-MUT-097, T6-MUT-101 |
| `corpus[content-safety-refused]` | T6-MUT-097, T6-MUT-101 |
| `corpus[safe-unmappable]` | T6-MUT-051, T6-MUT-142 |
| `corpus[one-sided-legacy-present]` | T6-MUT-081, T6-MUT-085, T6-MUT-142 |
| `corpus[one-sided-legacy-absent]` | T6-MUT-095, T6-MUT-142 |
| `vi1013_out_of_corpus_input_refused` | T6-MUT-097 |
| `vi1013_crash_before_acknowledgement_is_idempotent` | T6-MUT-081, T6-MUT-085, T6-MUT-095, T6-MUT-102, T6-MUT-103, T6-MUT-124 |
| `vi1013_loop_engine_caller_exists` | T6-MUT-150 |
| `vi1018_authority_isolation` | **NOT PROVEN** |
| `vi1018_initial_plan_review_not_consumed_as_task_approval` | T6-MUT-161 |
| `vi1018_no_mutable_task_projection_api` | T6-MUT-162 |
| `vi1019_self_containment` | T6-MUT-060, T6-MUT-102, T6-MUT-164B |
| `vi1019_package_check_detects_violation` | **NOT PROVEN** |
| `vi1019_spy_detects_contracts_delivery_access` | **NOT PROVEN** |
| `vi1019_static_check_detects_agentbundle_import` | **NOT PROVEN** |
| `vi1019_static_import_check` | T6-MUT-163 |
| `c1_structural_clean_rejects_findings_text` | T6-MUT-030, T6-MUT-100, T6-MUT-101 |
| `c1_structural_clean_accepts_exact_clean_text` | T6-MUT-032 |
| `c2_sustained_finding_produces_findings_result_not_eligible` | T6-MUT-071, T6-MUT-074, T6-MUT-102 |
| `c2_all_refuted_produces_acceptance_eligible` | T6-MUT-060, T6-MUT-073, T6-MUT-102, T6-MUT-117 |
| `c2_id_mismatch_produces_indeterminate` | T6-MUT-056 |
| `c2_bad_decision_produces_indeterminate` | T6-MUT-059 |
| `c3_transition_history_clean_acknowledged` | T6-MUT-081, T6-MUT-085, T6-MUT-140, T6-MUT-143 |
| `c3_transition_history_divergent` | T6-MUT-081, T6-MUT-084, T6-MUT-091, T6-MUT-093, T6-MUT-140, T6-MUT-143 |
| `c4_crash_recovery_writes_missing_assessments` | T6-MUT-060, T6-MUT-103, T6-MUT-112, T6-MUT-113 |
| `c5_grammar_invalid_findings_produces_unable` | T6-MUT-040, T6-MUT-100, T6-MUT-101 |
| `c6_return_value_has_required_fields` | T6-MUT-103, T6-MUT-140 |

## NOT PROVEN

No mutation of `_review_compat.py` or the loop-engine caller can red these six cases.

- `test_vi1012_clean_report_reaches_acceptance_eligible` and `test_vi1012_unsupported_findings_report_reaches_acceptance_eligible`. Shape: **an unreachable path.** Both drive `_review_persistence`, `_review_assessment`, `_review_bridge`, and `_review_disposition` directly and never call the adapter. Their subject is out of the mutation scope, so they can be proven only by mutating those modules.
- `test_vi1018_authority_isolation`. Shape: **an unreachable path,** plus a tautology. The fixture never calls the adapter, though its docstring says it does. It captures `state.json` after `loop-cohort init`, runs `plan check-current`, and compares state, but no Slice 2 code runs in between. Its second assertion, `rc_check == check_result.get("plan_review_status") or True`, can never fail. It also calls `pytest.skip` when `init` fails, so a broken engine skips it. One input would make it catchable: call `project_compat_reconcile_review_source_event` against the spec directory's real `state.json` between the two captures. Then compare `approve-plan`, `schedule`, and `plan check-current` output before and after.
- `test_vi1019_package_check_detects_violation`. Shape: **an absence something else guarantees.** The script exits at check 1, before it loads any review module. The outcome depends only on the stub `agentbundle` on `PYTHONPATH`, never on runtime code. It proves the harness, not the runtime.
- `test_vi1019_static_check_detects_agentbundle_import`. Shape: **an absence something else guarantees.** It appends its own `import agentbundle` to a copy and scans the copy. Any runtime source that parses gives a non-empty hit list. Its hash check compares the file with itself. It proves the scanner, not the runtime.
- `test_vi1019_spy_detects_contracts_delivery_access`. Shape: **an absence something else guarantees.** The assertion is `"SPY_OPEN_COUNT=" in stdout or returncode != 0`. A clean run prints `SPY_OPEN_COUNT`, and any failure exits non-zero, so it passes for every runtime. Its closing hash check compares the file with itself. One input would make it catchable: assert `returncode == 1` and that stderr names the injected `.spy-probe` path. Today the injected copy cannot even find its own `contracts` directory from `tmp_path` and crashes on `/contracts/delivery/.spy-probe`. That crash would also satisfy the stricter assertion, so the injection must also target the spy's real anchor.

## Proven, with a caveat

- `test_vi1019_self_containment` catches only a read under `packs/contracts/delivery/` (T6-MUT-164B). It misses a read under the repository's `contracts/delivery/` (T6-MUT-164). That is the real schema directory, and the file exists there. The spy walks up from `SCRIPTS` to the first directory holding `contracts` or `packs`. That is `packs/`, because `packs/contracts` is the contracts pack. A baseline probe with a spy on `builtins.open` and `io.open` saw no `contracts/delivery` open across direct-clean, sustained adjudicated, findings, and structural-clean calls. Under T6-MUT-164 it saw the root-path reads. The baseline is therefore clean, but the suite cannot prove it.
- `corpus[content-safety-refused]` is proven only for acknowledgement and `structured_present` (T6-MUT-097 and T6-MUT-101). Its text `Clean \x01 has control character.` also fails the legacy grammar. So removing the content-safety guard (T6-MUT-010) still yields `unable` (**two sufficient mechanisms**).
- `corpus[unknown-form]` and `test_vi1013_out_of_corpus_input_refused` survive T6-MUT-001 and T6-MUT-002 alike. The form gate and the step-6 fallback both return `unable` (**two sufficient mechanisms**). Only compound `T6-DIAG-2` reds them.
- `corpus[safe-unmappable]` is labelled "non-JSON adjudication", but its raw report is not JSON, so it stops at the raw-report parse (T6-MUT-051). Changing the adjudication-parse failure into a raise (T6-MUT-054) survives (**a message from a different rule**).
- `corpus[adjudicated-sustained]` and `test_c2_sustained_finding_produces_findings_result_not_eligible` cannot tell `supported` from `indeterminate`. Both block readiness. T6-MUT-070 drops the independent authority, so the sustained finding becomes `indeterminate`, and every case still passes.
- `corpus[adjudicated-*]`, `findings-no-adjudication`, and `test_c4_*` use `_legacy_state_with_operation` or an empty state and assert only `acknowledged`. They never assert `legacy_present` or `divergent` for the operation-id-only state (T6-MUT-080 and T6-MUT-094 survive).
- `test_c2_id_mismatch_produces_indeterminate` is caught by T6-MUT-056 only through a `KeyError` raised in the adapter. The subset case (an extra audit id, T6-MUT-057) is not pinned.
- `test_c3_*` catch T6-MUT-140 through a `KeyError` in the test body, and `test_c6` catches it by assertion.

## Guard coverage

| Guard named in the brief | Mutations | Result |
| --- | --- | --- |
| Closed form gate | 001, 002 | Two sufficient mechanisms. Compound DIAG-2 caught. |
| Content-safety refusal → unable | 010 | Uncaught (i) |
| Direct-clean grammar requirement | 020 | Uncaught (i) |
| Structural-clean grammar | 030, 032 | Caught |
| Structural-clean footer predicate | 031 | Uncaught (i) |
| Trailing-whitespace predicate | none | Absent from `_review_compat.py` (see below) |
| Findings form: invalid → unable, valid → indeterminate | 040, 041 | Caught |
| Adjudicated one-to-one id matching | 056 caught; 057 | 057 uncaught (i) |
| Closed audit decision set | 059, 060 | Caught |
| Sustained → supported via independent authority | 070; 074 | 070 uncaught (i); 074 caught |
| Sustained is not forced unsupported | 071 | Caught |
| Refuted → unsupported-opinion | 072 uncaught; 073 caught | 072 uncaught (i) |
| Legacy presence via `last_review_record_operation_id` | 080 | Uncaught (i) |
| Legacy presence via `transition_history` with an allowed event | 081, 084, 085 caught; 082, 083 | 082, 083 uncaught (i) |
| Agreement check | 091 caught; 090, 092, 098 | 090, 092, 098 uncaught (i) |
| Divergent flag | 093 caught; 094 | 094 uncaught (i) |
| Acknowledged requires both sides | 095 caught; 096 | 096 is two sufficient mechanisms |
| Never acknowledged for indeterminate or unable | 097 caught; 098 | 098 uncaught (i) |
| `structured_present` reflects the store | 100, 101, 102, 103 | Caught. It is not derived from the store; see the findings. |
| Deterministic ids | 120 to 124 | 124 caught; 120 to 123 uncaught (i) |
| Crash recovery writes missing assessments | 112, 113, 117 | Caught |
| No duplicate records on replay | 110, 111, 114, 115, 116 | Masked by the store; DIAG-1, -3, -4 |
| Temp files only under the store root | 130, 131, 132, 133 | Uncaught (i) |
| Return field set | 140, 142, 143 caught; 141 | 141 uncaught (i) |
| Loop-engine caller delegates unchanged | 150 caught; 151, 152 | 151, 152 uncaught (i) |
| VI-1012 role-name literal | 160 | Caught |
| VI-1018 `initial-plan-review.v1` reference | 161 | Caught |
| VI-1018 mutable-task API | 162 | Caught |
| VI-1019 `import agentbundle` in a function body | 163 | Caught by `test_vi1019_static_import_check` |
| VI-1019 `contracts/delivery` read | 164B caught; 164 | 164 uncaught (test defect) |

**Trailing-whitespace predicate.** `_review_compat.py` has none. Structural-clean relies on `loop-cohort._classify_raw_report`, which compares each line exactly with the sentinel. That code is outside the mutation scope. A baseline probe of `Clean — ready to commit. ` (one trailing space) under structural-clean returns `unable`, which is correct.

## UNCAUGHT GUARD

Each entry names the single input that would catch it. It gives the baseline result, observed by probe, and the result under the mutation. "Wrong" means the mutated behaviour breaks the spec.

### (i) Reachable but untested: 33 mutations

| Mutation | Single catching input | Baseline | Under mutation |
| --- | --- | --- | --- |
| 010 content safety | direct-clean `Clean — ready to commit.⏎⏎## Not checked⏎- a\x01b` | `unable` | `clean`, persisted. Wrong. |
| 020 direct-clean grammar | direct-clean with `_FINDINGS_TEXT` | `unable` | `clean`, persisted. Wrong. |
| 031 structural footer | structural-clean `Clean — ready to commit.⏎⏎## Not checked⏎- not run` | `unable` | `clean`. Wrong: legacy routes footers to adjudication. |
| 050 adjudication None | adjudicated, valid finding JSON, `adjudication_text=None` | `indeterminate` | `TypeError` raised. Wrong. |
| 052 empty finding list | adjudicated `[]` with `{}` | `indeterminate` | `ReviewPersistenceRefused` raised. Wrong. |
| 053 finding.v1 validation | adjudicated finding missing `rule_ref` | `indeterminate` | `ReviewPersistenceRefused` raised. Wrong. |
| 054 non-JSON adjudication | adjudicated, valid finding JSON, adjudication `not json` | `indeterminate` | `JSONDecodeError` raised. Wrong. |
| 055 audit must be an object | adjudication `["f-probe"]` | `indeterminate` | `AttributeError` raised. Wrong. |
| 057 extra audit id | audit carries the finding's id plus `extra` | `indeterminate` | `findings`. Wrong: the audit is not one-to-one. |
| 058 audit entry must be an object | adjudication `{"f-probe": "refuted"}` | `indeterminate` | `AttributeError` raised. Wrong. |
| 061 non-empty authority_ref | refuted with `authority_ref: ""` | `indeterminate` | `findings`. Wrong. |
| 070 independent authority | sustained material finding; assert the stored assessment is `supported` | `supported` | `indeterminate`. Readiness is blocked either way. Wrong class. |
| 072 refuted → unsupported | refuted **material** finding, then `review_readiness` | eligible `True`, `unsupported-opinion` | eligible `False`, `supported`. Wrong. |
| 080 op-id presence | operation-id-only state; assert `legacy_present` | `True` | `False`. Wrong field; acknowledgement unchanged. |
| 082 transition id match | `reviewers-clean` history entry for another id, no op id | `legacy_present False`, ack `False` | `True`, ack `True`. Wrong. |
| 083 allowed event | same-id entry with event `approve-plan`, no op id | ack `False` | ack `True`. Wrong. |
| 090 clean agreement | `reviewers-clean` plus adjudicated `findings` | ack `False`, divergent `True` | ack `True`. Wrong. |
| 092 findings agreement | `findings-remain` plus adjudicated `findings` | ack `True` | ack `False`, divergent `True`. Wrong. |
| 094 unknown event is not divergent | operation-id-only state; assert `divergent` | `False` | `True`. Wrong. |
| 098 indeterminate never acknowledged | `reviewers-clean` plus findings form (`indeterminate`) | ack `False`, divergent `True` | ack `True`. Wrong. |
| 116 assessments scoped to report | event A fully reconciled with finding `f`; B's report pre-written with the same `f`; reconcile B | B's assessment written | B's assessment skipped. Wrong. |
| 120 report id | assert `report_id == "compat-report:<id>"` | deterministic | random suffix. Replay still dedupes by lineage. Wrong id only. |
| 121 report transaction id | assert the transaction id | deterministic | random. No visible effect in a probe. |
| 122 assessment id | assert `assessment_id` | deterministic | random suffix. Wrong id only. |
| 123 assessment transaction id | assert the transaction id | deterministic | random. No visible effect in a probe. |
| 130 temp dir under store root | spy `tempfile.mkdtemp`; assert `dir == store._root` | under root | `dir=None` (system temp). Wrong. |
| 131 temp dir removed | list the store root after a direct-clean call | `store.log` only | stray `tmp*` dir left. Wrong. |
| 132 store root required | store wrapper with no `_root`, adjudicated refuted | `unable`, 0 records | `findings`, 1 record. Wrong. |
| 133 I/O failure → unable | `_root` set to a missing directory, direct-clean | `unable` | `FileNotFoundError` raised. Wrong. |
| 141 closed return set | assert `set(result) == {six keys}` | six keys | adds `legacy_event`. Wrong; the C6 docstring says "exactly". |
| 151 caller passes `legacy_state` | the caller with a `reviewers-clean` state | ack `True` | ack `False`. Wrong. |
| 152 caller passes `source_event` | the caller, then read the stored report role | `legacy-reviewer` | `caller-substituted-role`. Wrong. |
| 164 `contracts/delivery` read | spy anchored at the repository root, not `packs/` | no read | reads `contracts/delivery/review-report.v1.schema.json`. Wrong. |

The four deterministic-id rows (120 to 123) are one guard, so these 33 mutations cover 30 guards.

### (ii) Two sufficient mechanisms or masked by the store: 7 mutations

- **001 and 002** (form gate and step-6 fallback). Each alone returns `unable` for an unknown form. Compound DIAG-2 catches 2 cases. Cutting one makes the other catchable.
- **096** (absent legacy short-circuit). When legacy is absent, `legacy_event` is always `None`, so the next check returns the same pair. No input separates them.
- **110 and 111** (replay rewrite and lineage lookup). On an exact replay, the store accepts the identical transaction as a retry, so nothing changes. DIAG-4 (111 plus a random report transaction id) catches 2 cases with `composed record ID already admitted`. A content-changing replay separates them: under 110 or 111 the replay in `replay-content-mismatch` raises `lifecycle request differs from committed transaction`. On the baseline it acknowledges (see the findings).
- **114 and 115** (the missing-findings filter and the skip set). Each alone filters, and the store's transaction retry masks both. DIAG-1 (114 plus 115) survives. DIAG-3 (plus a random assessment transaction id) catches `test_c4` with `composed record ID already admitted`.

### (ii) Unreachable by construction: 1 mutation

- **075** (the audit-less branch in `_write_compat_assessments`). `_classify_adjudicated` returns an audit entry for every finding, or none at all. Assessments run only when `audit_entries` is non-empty. The `audit_entry is None` branch is dead.

## Runtime findings

All are baseline probes (`probe/probe.py`) with hashes checked.

1. **Direct-clean accepts non-exact text and clears review.** The legacy `--direct-clean-file` requires the exact sentinel bytes. The adapter accepts any raw-classifier `clean`. `Clean — ready to commit.⏎` and `Clean — ready to commit.⏎⏎## Not checked⏎- authorization review not run` both return `clean`, persist a clean report, and make `review_readiness` acceptance-eligible. The second carries a disclosure footer that legacy routes to full adjudication. The spec row is "Exact direct-clean report".
2. **Replay acknowledges against a different stored fact.** Idempotency keys only on `source_event_id`. A first call with findings-form text stores an `indeterminate` report. A replay with the same id as direct-clean, plus a `reviewers-clean` legacy entry, returns `result: clean, acknowledged: True`. The store still holds only the `indeterminate` report, and readiness is not eligible. The acknowledgement attests to a result that was never persisted.
3. **The legacy payload digest is ignored.** `last_review_record_payload_digest` is never read. A state whose digest is `WRONG-DIGEST` still acknowledges. The T6 design called for presence "with matching payload digest".
4. **Schema-invalid adjudicated findings persist as `indeterminate`.** A finding with `schema_version: 2` (unknown major) or a missing required field returns `indeterminate` and stores `compat-report:e` with that status. The spec row "Schema-invalid or unknown-major report" requires `unable` and no persisted semantic report.
5. **The adjudication text gets no content safety, and a downstream refusal leaves a one-sided write.** Only `raw_report_text` is checked. With a sustained `authority_ref` shaped like a credential (`ghp_` plus 36 characters), the adapter writes the findings report and then raises `ReviewAssessmentRefused: … denied-content-safety-rejected-credential`. A replay raises the same way. The store keeps a findings report with zero assessments. Readiness stays non-eligible, so this fails closed. Still, the spec requires `unable` with nothing persisted, not a raise after a partial write. A refuted `authority_ref` holding `\x01` is accepted, but it is not persisted, because the refuted path does not use it.
6. **`structured_present` is not read from the store.** After a clean report is stored for id `e`, a replay of `e` with content-safety-refused text returns `structured_present: False`. The store still holds one record for `e`. `_unable()` hard-codes `False`, and the success path hard-codes `True`.

The baseline behaves correctly for every other probe input in the UNCAUGHT GUARD table.

## Restored baseline

Both hashes equal the baseline. `python3 -m pytest packs/core/tests/skills/work-loop/test_review_compat.py -q -p no:cacheprovider`: 34 passed in 3.18s.
