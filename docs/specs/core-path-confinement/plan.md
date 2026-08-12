# Plan: core pack path confinement

- **Status:** Executing
- **Spec:** [`spec.md`](spec.md)
- **Mode:** full

## Delivery strategy

Work test-first in three bounded seams: repository-derived lint reads,
managed work-loop state reads, and knowledge-file locking. Keep helpers local
unless a second runtime caller demonstrably needs the exact same contract;
reuse `_statelock` where that contract already exists. Synchronize projections
and release metadata only after behavior is green.

## Tasks

### T1 — Pin repository-derived path escapes with red tests

- **Depends on:** none
- **Touches:** `packs/core/tests/skills/work-loop/test-lint-spec-status.py`, `packs/core/tests/skills/work-loop/test-lint-traceability.py`
- **Acceptance criteria:** AC1, AC2, AC6
- **Tests:** Add sentinel-bearing outside-root files plus traversal and symlink inputs. For traceability, instrument the directory boundary to prove an outside-resolving child is pruned before descent, cover circular resolution, and assert IDs come only from canonical confined paths. Assert the sentinel and outside existence cannot influence output; retain happy-path layout and contract coverage. These tests must fail against the current readers for the intended reason.
  - `test-lint-spec-status.py::case_workspace_symlink_outside_root_does_not_resolve_deferral` — `# STUB: AC1`; current reader resolves the external-only anchor.
  - `test-lint-spec-status.py::case_contract_registry_symlink_outside_root_does_not_supply_backref` — `# STUB: AC1`; current registry read accepts the external back-reference.
  - `test-lint-spec-status.py::case_reference_candidates_outside_root_do_not_resolve` — `# STUB: AC1`; current doc/code probes accept external files. `case_contract_file_symlink_outside_root_does_not_resolve` is the paired already-green control for the existing contract-file guard.
  - `test-lint-traceability.py::case_component_marker_symlink_outside_root_is_not_recognized` — `# STUB: AC2`; current existence probe recognizes the external marker.
  - `test-lint-traceability.py::{case_iter_dirs_prunes_unresolvable_children_before_descent,case_component_alias_uses_canonical_id}` — `# STUB: AC2`; exercise outside/circular pre-descent pruning and canonical IDs directly.
  - stub: true
- **Approach:** Extend the existing suites and their import helpers without adding a new harness.
- **Done when:** The pre-fix failures are recorded and each test names the unconfined probe or read it protects.

### T2 — Confine lint reads before probing

- **Depends on:** T1
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`, `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`
- **Acceptance criteria:** AC1, AC2
- **Tests:** Make T1's materialized stubs green; run existing lint-script suites to protect valid roots, configured layouts, contract warnings, and graph output.
  - stub: consumed from T1
- **Approach:** Reorder each candidate to resolve → contain → probe/read, use the returned canonical path, and fail closed without probing an outside target. Harden the recursive iterator itself by resolving and pruning child directories before `os.walk` descends, including circular-resolution failures.
- **Done when:** Every in-scope read/probe is visibly dominated by containment and no valid CLI output changes.

### T3 — Pin managed-state symlink reads with red tests

- **Depends on:** none
- **Touches:** `packs/core/tests/skills/work-loop/test-loop-engine.py`, `packs/core/tests/skills/work-loop/test-loop-cohort.py`
- **Acceptance criteria:** AC3, AC5, AC6
- **Tests:** Cover symlinked and non-regular state/pending files, an over-8-MiB file, and a sentinel external JSON target. Add a controlled replacement or monkeypatched filesystem-boundary case that changes file identity during the read and must be rejected. Cover dangling `events.jsonl` symlinks in initialization and append, asserting the external target is not created. Assert status and recovery never emit or act on the sentinel. Preserve ordinary status and recovery tests.
  - `test-loop-engine.py::{test_status_rejects_symlinked_engine_state,test_engine_state_reader_rejects_identity_change,test_engine_state_reader_rejects_over_limit_file,test_engine_state_reader_rejects_non_regular_path}` — `# STUB: AC3`; exercise the public sink plus descriptor identity, size, and type controls.
  - `test-loop-cohort.py::{test_status_rejects_symlinked_cohort_state,test_cohort_state_reader_rejects_identity_change,test_cohort_state_reader_rejects_over_limit_file,test_cohort_state_reader_rejects_non_regular_path}` — `# STUB: AC3`; same contract for cohort state.
  - `test-loop-engine.py::{test_recover_pending_rejects_symlink,test_recover_pending_rejects_symlinked_parent,test_recover_pending_rejects_non_regular_path,test_recover_pending_rejects_over_limit_file,test_recover_pending_rejects_identity_change}` — `# STUB: AC3`; exercise the actual recovery sink and assert no external sentinel is replayed or mutated through its target or parent.
  - `test-loop-engine.py::{test_init_rejects_dangling_event_log_symlink,test_append_rejects_dangling_event_log_symlink}` — `# STUB: AC3`; exercise both event-log creation paths and assert no external file is created.
  - `test-loop-engine.py::{test_init_rejects_non_regular_event_log,test_append_rejects_non_regular_event_log,test_append_rejects_event_log_identity_change}` — `# STUB: AC3`; cover shared event-log type and pre-write identity checks through both callers.
  - `test-loop-engine.py::test_init_creates_owner_only_event_log` — constructs an event log through the public init path and rejects any group/world permission bits.
  - stub: true
- **Approach:** Exercise public command functions or subprocess entry points so parsing-only tests cannot pass without reaching the sink.
- **Done when:** The current implementation fails the new boundary tests for the expected read path.

### T4 — Harden managed-state reads

- **Depends on:** T3
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`, `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`
- **Acceptance criteria:** AC3, AC5
- **Tests:** Make T3's materialized stubs green and run the complete engine/cohort suites, including normal recovery and status serialization.
  - stub: consumed from T3
- **Approach:** Add the smallest reusable file shapes already supported by each script: `lstat`, regular-file and size checks for reads, no-follow open where available, exclusive creation for a missing event log, and pre/post descriptor identity verification. Preserve schema parsing and diagnostics above that boundary.
- **Done when:** Managed state never follows a link, consumes an unverified path, or creates an event log through a link, and compatible regular files behave unchanged.

### T5 — Replace the weaker knowledge lock path

- **Depends on:** none
- **Touches:** `packs/core/tests/skills/work-loop/test-append-knowledge.py`, `packs/core/.apm/skills/work-loop/scripts/append-knowledge.py`
- **Acceptance criteria:** AC4, AC6
- **Tests:** Add hostile lock-type and stale-recovery regressions, then run append-knowledge and `_statelock` suites together.
  - `test-append-knowledge.py::test_stale_directory_lock_is_refused` — `# STUB: AC4`; the current custom lock reclaims the directory and exits zero.
  - `test-append-knowledge.py::test_recognized_stale_statelock_record_is_recovered` — `# STUB: AC4`; combines append-level stale-record recovery with a source-authority assertion that is red until `exclusive` comes from `_statelock.py`. Existing stale-race fixtures are migrated from the custom `abandoned` token to the recognized record format.
  - stub: true
- **Approach:** Load and use the shipped `_statelock` helper, translate its defined failures to the existing CLI diagnostic boundary, and remove the duplicated custom lock implementation. Only recognized regular records remain eligible for stale recovery; a directory, FIFO, device, or symlink is left untouched and refused.
- **Done when:** Append behavior has one lock authority and hostile lock paths fail closed.

### T6 — Synchronize, document, and verify the release

- **Depends on:** T2, T4, T5
- **Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`, `workspace.toml`, `docs/specs/pack-script-root-boundary-validation/spec.md`, generated core projections and marketplace aggregate
- **Acceptance criteria:** AC5, AC7, AC8, AC9
- **Tests:** Run projection drift/version checks, targeted pytest, pack conformance, lint, and `make build-check`; record exact environment-blocked gates until rerun in a writable environment.
  - stub: no stub (goal-based verification)
- **Approach:** Apply a patch version bump to both pack-owned version files, run the canonical projection build (which regenerates the marketplace aggregate), amend stale historical assumptions with an erratum, and keep downstream Snyk disposition operational rather than source-suppressive. The aggregate is generated and must not be edited as source.
- **Done when:** Source and projections agree, release surfaces name the fix, and the minimal writable-environment verification set passes.

## Review routing

- Spec stage: adversarial reviewer and security reviewer using the path/file
  checklist.
- Implementation stage: adversarial reviewer, security reviewer, then quality
  engineer after gates.
- Human gates: approve this spec, then approve this plan before implementation.
