# Verification ledger: acceptance authority and evidence

Execution observations for the approved Slice 1 plan. This file is not
hash-pinned; it records how tasks are verified, not new obligations.

## Script-versus-schema parity (owner decision, 2026-10-01)

The canonical schemas in `contracts/delivery/` stay repository-only. Neither
`agentbundle` nor the Core pack ships them to adopters, and no work-loop script
reads them at runtime. Agents never write delivery records directly: trusted
work-loop scripts build every record from typed arguments, as `loop-engine`
already does for its state.

Every task that adds a module which builds or accepts a delivery record (T3a
through T7) therefore carries parity tests:

- each record the module emits validates against its canonical schema, using
  `jsonschema` at test time only; and
- the module's own validation refuses each schema-invalid case (an unknown
  authority-shaped field, a missing required field, an unknown
  `schema_version` major, an out-of-enum value) with a stable code.

The protected skill-copy set for AC-0013 is a constant in the scripts, with a
test pinning it to the work-loop projections `contracts/adapter.toml` declares
for the Core pack's surfaces. T9a's conformance run rolls these suites up as
the evidence for the Release history closeout: "Released pack versions contain
implementations that validate against the canonical contracts".

Shipping input schemas to the agent is deferred to the first slice that
accepts agent-written structured payloads.

## Benchmarks run inside the corpus (owner decision, 2026-10-01)

The AC-0018 harness takes 8.0 s for all 105 runs on a local M1 Max (p95 about
65 ms against the 2 s bound). The benchmarks are therefore ordinary pytest
tests in the work-loop pack suite, which `make test` already runs, so a
`test-corpus.yml` dispatch measures them on GitHub-hosted `ubuntu-latest` with
no workflow change. Each test asserts its bound, prints its measurement into
the job log, and writes results only under a temporary path. T9a records the
dispatched run's head commit SHA with the passing benchmark tests. The earlier
benchmark job, posture test, single-roster exception, and ADR draft were
dropped before commit.

T9a also confirms that `.github/workflows/test-corpus.yml` at the dispatched
run's head commit SHA is byte-identical to the default branch's copy. A
mismatch voids the benchmark evidence until the changed workflow passes the
CI security scanners. This replaces the round-12 scan-to-dispatch check and
carries a deferred round-13 security Nit.

T9a writes the dispatched run's ID, head commit SHA, the shard that ran the
work-loop pack suite, and the printed AC-0018 p95 and AC-0019 cold-rehydration
figures into this ledger, because the job log expires under the repository's
log-retention setting (deferred round-13 adversarial Nit).

Recorded evidence: `test-corpus.yml` run 37096863910, head commit
`d53bbc3af4ddfabc34a0e31a655cebe135764f3c`, completed 2026-10-03 on
`ubuntu-latest`. The workflow file at that commit is byte-identical to the
default branch's copy. Shard 2/4 ran the work-loop pack suite and passed:

- AC-0018: 1,000 criteria and 100,000 receipts, 5 warm-up and 100 timed runs,
  p95 88.4 ms and p50 76.5 ms against the 2,000 ms bound.
- AC-0019: 1,000 criteria, 100,000 receipts and 100,000 log frames rehydrated
  to 1,000 verdicts in 2.076 s against the 10 s bound.

## T9a acceptance evidence map

Each criterion maps to the suites that exercise it. Pack-behaviour suites live
in `packs/core/tests/skills/work-loop/`; repository-level suites live in `tests/roster/`. Every runtime module's
records are also pinned to their canonical schemas by the roster parity suites
(`test_delivery_contract_bundle.py`, `test_security_primitives_schema_parity.py`,
`test_acceptance_schema_parity.py`, `test_delivery_subject_parity.py`,
`test_containment_attestation_parity.py`, `test_evidence_store_schema_parity.py`).
`test_t9a_conformance_rollup.py` proves the projected `.claude/` and `.agents/`
copies are byte-identical to the pack source and importable.

| AC | Evidence |
| --- | --- |
| AC-0001 | `test_policy_import.py::TestCanonicalizationCorpus` |
| AC-0002 | `test_policy_import.py::TestAtomicImport` |
| AC-0003 | `test_acceptance.py::TestEnvelopeProjection`; `test_policy_import.py::TestChangeClassification` |
| AC-0004 | `test_acceptance.py::TestChangeClassifier`; `test_policy_import.py::TestChangeClassification` |
| AC-0005 | `test_subject_projection.py::TestProviderParityAC0005` |
| AC-0006 | `test_subject_projection.py::TestSubjectAdmissionNegativesAC0006`, `::TestTraversalLimitsAC0006` |
| AC-0007 | `test_acceptance.py::TestVerdictEvaluation`; `test_compat_facade.py::TestAC0007DualEmitCorpus` |
| AC-0008 | `test_evidence_store.py::TestAllOrNoneVisibility`, `::TestChecksumAndReferenceCorruption`, `::TestIndexDeleteAndRebuild` |
| AC-0009 | `test_acceptance.py::TestFreshnessEvaluation`; `test_evidence_store.py::TestFreshnessAndContradiction` |
| AC-0010 | `test_security_primitives.py::TestCapabilityIntersection`, `::TestCapabilityGrantLifecycle`; `test_containment_broker.py::TestAttestationWithinGrant` |
| AC-0011 | `test_security_primitives.py::TestConfinedMutationHappyPath`, `::TestConfinedMutationAdversarial`; `test_compat_facade.py::TestAC0011Confinement` |
| AC-0012 | `test_process_safety.py` (all classes) |
| AC-0013 | `test_containment_broker.py::TestDeliveryControlPathGuard`, `::TestForgeryFixturesPerAdapter`, `::TestDirectSyscallForgery`, `::TestProtectedRefForgery`, `::TestBrokerBypassForgery`, `::TestLaunchUntrusted`; `test_containment_attestation_parity.py` |
| AC-0014 | `test_content_safety.py`; `test_content_safety_boundary_matrix.py`; the content-profile refusals in `test_policy_import.py::TestAtomicImport` |
| AC-0015 | `test_content_safety.py` (no-payload and inert-data cases) |
| AC-0016 | `test_compat_facade.py::TestAC0016ShadowOff`, `::TestAC0016ShadowOn`; the engine and cohort suites (571 passed, 5 skipped); the T9a real invocation below |
| AC-0017 | `test_policy_import.py::TestReverseReader`; `test_compat_facade.py::TestAC0017Governance` |
| AC-0018 | `test_acceptance_benchmark.py` (asserts p95 within 2 s); binding run: the `test-corpus.yml` dispatch, pending owner confirmation |
| AC-0019 | `test_cold_rehydration_benchmark.py` (asserts within 10 s); binding run: the `test-corpus.yml` dispatch, pending owner confirmation |
| AC-0020 | `test_security_primitives.py::TestSecurityEventWriterAuthority`; `test_policy_import.py::TestWriterAuthorityRefusals`; `test_evidence_store.py::TestProducerCapabilityChecks`; `test_containment_broker.py::TestBrokerCapabilityFailures` |
| AC-0021 | `test_security_primitives.py::TestSecurityEvents`; `test_process_safety.py::TestAuditSinkUnavailable`, `::TestAuditEventOrder`; `test_evidence_store.py::TestAuditSinkBehavior` |

The clean-environment fence (`test_t9a_clean_env_fence.py`) evidences the
Never-do rule that no `work-loop` runtime module imports outside the standard
library and its siblings, and that the projected scripts run where `agentbundle`
is not importable. The other Never-do rule, no change under
`packages/agentbundle/`, is a fact about this slice rather than a lasting
repository rule, so it is checked once here instead of by a permanent test:
`git diff --name-only origin/main -- packages/agentbundle` listed 0 files at
branch head `6616ba4f7` on base `c586b26cf` (2026-10-02). T9b re-runs it before
closeout.

## T9a real invocation

Recorded 2026-10-02 using a throwaway spec in a temporary git repository.
Both runs used the pack source scripts at
`packs/core/.apm/skills/work-loop/scripts/` (byte-identical to the projected
copies at `.claude/skills/work-loop/scripts/`). Commands are shown with
positional arguments abbreviated as `<spec-dir>`; all resolved to absolute
paths in execution. All exits were 0.

### Run A: WORK_LOOP_SHADOW_SERVICES=1

```
WORK_LOOP_SHADOW_SERVICES=1 python loop-engine.py init <spec-dir> --mode code --json
  exit 0  → state=SPEC-PLAN-REVIEW, run_id=<run-id-A>

WORK_LOOP_SHADOW_SERVICES=1 python loop-cohort.py init <spec-dir> --run-id <run-id-A>
  exit 0

WORK_LOOP_SHADOW_SERVICES=1 python loop-engine.py transition <spec-dir> spec-ready
  exit 0  → state=SPEC-PLAN-REVIEW, last_event=spec-ready

WORK_LOOP_SHADOW_SERVICES=1 python loop-engine.py transition <spec-dir> reviewers-clean
  exit 0  → state=SPEC-HUMAN-GATE, last_event=reviewers-clean

WORK_LOOP_SHADOW_SERVICES=1 python loop-engine.py transition <spec-dir> spec-approved
  exit 0  → state=PLAN-HUMAN-GATE, last_event=spec-approved

[write plan.md to <spec-dir>]

WORK_LOOP_SHADOW_SERVICES=1 python loop-engine.py transition <spec-dir> plan-approved
  exit 0  → state=SPEC-PLAN-APPROVED, last_event=plan-approved

WORK_LOOP_SHADOW_SERVICES=1 python loop-cohort.py approve-plan <spec-dir> --expect-run-id <run-id-A>
  exit 0

WORK_LOOP_SHADOW_SERVICES=1 python loop-cohort.py schedule <spec-dir> --expect-run-id <run-id-A>
  exit 0

WORK_LOOP_SHADOW_SERVICES=1 python loop-engine.py transition <spec-dir> plan-locked
  exit 0  → state=CODE-IMPLEMENTATION, last_event=plan-locked, transition_sequence=5
```

Shadow evidence written to `<spec-dir>/.shadow-acceptance/`:

- `evidence.jsonl`: 5 records, all `authoritative: false`
  - events: `spec-ready`, `reviewers-clean`, `spec-approved`, `plan-approved`, `plan-locked`
- `policy-import.json`: `{"governance_required_for_authority_switch": true}`

### Run B: WORK_LOOP_SHADOW_SERVICES unset

Identical 9-command sequence with the env var unset. All exits 0.
Final state: `state=CODE-IMPLEMENTATION`, `last_event=plan-locked`,
`transition_sequence=5`.

No `.shadow-acceptance/` directory written.

### Comparison

The following `engine-state.json` fields are identical across both runs:
`feature`, `mode`, `state`, `last_event`, `transition_sequence`,
`schema_version`, `gate_question`, `last_event_context`.

Fields that differ: `run_id` (each run generates a fresh UUID) and
`last_transition_at` (wall-clock timestamps differ).

Legacy authority made every decision in both runs. The shadow facade
(Run A) emitted non-authoritative records for observability only and
did not alter any engine state or cohort state. The byte-identical
`engine-state.json` semantic fields confirm this.

## Pack eval harness

The `work-loop` skill is deliberately outside the Core pack's eval roster.
`packs/core/pack.toml` lines 49-50 record why: the skill is loaded broadly by
the plan, execute, and review discipline rather than by a narrow user prompt,
so no clean negative set can be written for it. The shadow services add no
prompt surface either; a maintainer opts in with `WORK_LOOP_SHADOW_SERVICES=1`.
Their behaviour is therefore covered by the pack and roster test suites listed
above, not by a new eval case.
