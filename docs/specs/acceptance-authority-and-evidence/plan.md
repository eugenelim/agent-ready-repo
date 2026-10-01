# Plan: Acceptance authority and evidence

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/architecture/acceptance-centered-work-loop.md`, `docs/architecture/work-loop-authority-migration.md`, `docs/architecture/work-loop-acceptance-evidence.md`, `docs/architecture/runtime-security-primitives.md`, `docs/architecture/delivery-content-safety.md`; analogous implementations `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py` and `packs/core/.apm/skills/close-work/scripts/file_safety.py`; tests `packs/core/tests/skills/work-loop/test_loop_cohort.py` and `packages/agentbundle/tests/unit/test_catalogue_tooling_file_safety.py`. Deviation: the reviewed security design names `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py` as a source, while `packages/agentbundle/agentbundle/build/self_host.py` and `packs/AGENTS.local.md` identify it as a generated destination; implementation edits the pack-owned source and regenerates the package copy.

> **Plan contract:** this is the current implementation strategy. Initial review
> checks strategy, safety constraints, dependencies, and scope alignment; it
> does not make the task list authoritative. After that review, tasks, sequence,
> decomposition, and local methods may be revised or regenerated without human
> approval while the derived reviewed-execution-envelope fingerprint and
> review-authorized terminal intent remain fixed. A protected source change
> follows its owning amendment or risk gate and then receives fresh initial
> review before a later-slice task projector may resume.
>
> **In force for this Slice 1 run:** that approval-free task revision is target
> behavior that Slice 4 delivers; it is not yet in force. The current engine runs
> this delivery, so any change to plan substance after `approve-plan` follows the
> current engine's re-plan and approval rule. Lifecycle bookkeeping (status
> tokens and checkboxes) is exempt, as the engine already normalizes it.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are
> working material before approval.

## Approach

Build the slice as dependency-ordered layers: canonical contracts first; shared content and security primitives second; pure acceptance logic third; approval, subject, and evidence persistence fourth; compatibility wiring and integrated conformance last. Each layer is additive and keeps the current engine authoritative, so it can land as an independently reviewable pull request and reverse by disabling the compatibility caller rather than deleting semantic facts.

The whole slice cannot be understood, verified, or reviewed as one unit, and its shape is **DEEP**, not mechanically uniform, so it splits. Each plan task is one review unit that can be understood, verified, and reviewed on its own; each leaves the repository working, and no layer begins before its contract and security dependencies are green.

## Constraints

- ADR-0061 and ADR-0125 keep the current engine and cohort writers authoritative. Slice 1 adds callable services but cannot transfer procedure ownership or widen the engine's effect registry.
- ADR-0005 keeps execution sequential by default and preserves its existing parallel-write gates. This slice adds no parallel admission or protected-ref product authority.
- [`work-loop-authority-migration.md`](../../architecture/work-loop-authority-migration.md) requires an accepted superseding governance record before any current authority is retired; implementation alone cannot satisfy that gate.
- `contracts/delivery/` is the canonical schema source. Package, pack, and generated copies are projections with explicit parity checks.
- Runtime code uses the Python standard library. The existing test toolchain may validate JSON Schema; this slice adds no runtime dependency.
- Package code uses list-form process execution, explicit UTF-8, portable temporary paths, and platform-skipped link or execute-bit tests where the host cannot supply the capability.
- Core pack and package changes carry their required version updates, evals, generated projections, release record, and `Engine-Change-RFC:` commit footer.
- No accepted RFC yet covers this engine change, and `packs/AGENTS.local.md` allows `n/a` only for non-engine changes. T0 obtains an accepted engine-scoped RFC before any task writes under `packages/agentbundle/`; every such commit cites it in its `Engine-Change-RFC:` trailer.
- The supported adapter set for this slice is the sequential reference runtime plus the Core compatibility adapter. The package declares that set in one place, and the conformance suites refuse to run against an empty or single-member declaration, so AC-0007 and AC-0013 always compare at least two adapters.
- "The CI reference worker" in AC-0018 and AC-0019 means a GitHub-hosted `ubuntu-latest` runner in a dispatch-only benchmark workflow. GitHub dispatches a `workflow_dispatch` workflow only once its file is on the default branch, so T4 adds the workflow `.github/workflows/benchmark-acceptance.yml` and it merges to `main` before T9a needs its evidence (owner decision); T7 extends it with the cold-rehydration benchmark, and T9a dispatches it with `--ref` on its own branch. The committed harness fixes the timed-run count and warm-up policy, and the workflow retains its output.

## Construction tests

**Integration tests:**

- A frozen approved-artifact corpus drives legacy canonicalization, atomic import, reverse read, protected-change classification, legacy subject projection, verdict parity, and cache-deletion rehydration across the package and Core compatibility adapter.
- A shared adversarial corpus drives filesystem, process, capability, containment, control-plane forgery, content-safety, and inert-consumption conformance through every supported adapter.
- Crash injection covers every approval and evidence transaction boundary, then restarts from only durable bytes and compares the complete semantic record set and verdict.
- Cross-platform fixtures cover POSIX links, Windows reparse/junction behavior where available, process-tree termination, executable identity replacement, bounded output, and unsupported-capability refusal.

**Manual verification:** none. The slice exposes no UI or human-only judgment; all acceptance evidence comes from deterministic tests, conformance suites, benchmarks, and build gates.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Canonical delivery contracts, registry, and declared projections | T1, T9b | Schema, registry, and source-to-projection parity suites | `contracts/README.md` and `contracts/REGISTRY.md` name every shipped record and owner; all projections match. |
| Current architecture and authority migration | T8, T9b | Compatibility and missing-governance refusal suites | Architecture pages describe callable shadow services, current authority, reversal, and future cutover gates. |
| Maintainer parity, recovery, and reversal procedure | T5, T6, T7, T8, T9a, T9b | Import, restart, cache-deletion, reverse-read, and end-to-end commands | `docs/architecture/loop-infrastructure.md` names the commands and expected results without relying on this plan. |
| Package, Core, and architect release history and versions | T9b | Package tests, pack evals, build-self, version parity, and changelog lint | Package, Core, and architect versions are released together when required, and `docs/product/changelog.md` records the outcome. |

## Design (LLD)

### Design decisions

Owned by: T1, T4, T5, T6, T7, T8

The service layer is a set of typed ports, pure projectors/evaluators, and append-only semantic stores rather than a second workflow engine. The current engine calls it through a compatibility adapter and remains the sole decision source until a later accepted governance record changes that authority. Traces to AC-0007, AC-0016, AC-0017. Owned by T4-T8.

The canonical delivery schemas live under `contracts/delivery/`, even though they are JSON-shaped, because the reviewed architecture assigns the bundle as one semantic interface family. `contracts/REGISTRY.md` supplies the backward pointer to this spec. Traces to AC-0001 through AC-0017. Owned by T1.

### Data & schema

Owned by: T1, T4, T5, T6, T7

The contract bundle defines `delivery-subject.v1`, `acceptance-property.v1`, `approval-record.v1`, `reviewed-execution-envelope.v1`, `initial-plan-review.v1`, `semantic-evidence-transaction.v1`, `evidence-receipt.v1`, `evidence-supersession.v1`, `acceptance-verdict.v1`, `security-capability.v1`, `confined-file.v1`, `safe-process.v1`, `containment-attestation.v1`, `security-event.v1`, `content-safety-policy.v1`, `content-safety-decision.v1`, and `untrusted-data.v1`. Each schema closes unknown authority-shaped fields, owns its identity fields, and declares compatibility and unknown-major refusal. Traces to AC-0001 through AC-0015, AC-0020, and AC-0021. Owned by T1.

Owning approvals, initial-plan reviews, evidence transactions, and security events are append-only facts with distinct authority. The reviewed execution envelope is a pure projection over ordered references to current approvals and grants nothing; the initial review binds one envelope fingerprint and terminal intent while never pinning later task text. Manifests, property projections, indexes, and verdicts are derived and disposable. Working-plan and future task-projection revisions are execution provenance, not approval records or acceptance inputs. Slice 1 defines that contract and its mutation classifier but does not create or update task projections. Traces to AC-0002 through AC-0009. Owned by T4-T7.

### Interfaces & contracts

Owned by: T2, T3a, T3b, T3c, T4, T5, T6, T7, T8

The package exposes in-process Python ports for subject projection, reviewed-envelope derivation, spec-policy approval and initial-review import and lookup, protected-change classification, evidence append and replay, acceptance evaluation, capability issue/intersection, confined file and process operations, containment launch, effect brokering, auditing, and content-safety decisions. The exact Python symbols are implementation-discovered from the smallest cohesive package boundary; the JSON contracts and tests define behavior before those symbols freeze. Traces to AC-0001 through AC-0017. Owned by T2-T8.

The Core compatibility adapter translates existing engine events and approved pins into typed calls, dual-emits old and new facts, and treats every target result as shadow data. It changes no public `work-loop` invocation. Traces to AC-0001, AC-0002, AC-0007, AC-0016, AC-0017. Owned by T5, T8.

### Component / module decomposition

Owned by: T1, T2, T3a, T3b, T3c, T4, T5, T6, T7, T8

- `contracts/delivery/` owns portable record shape and identity.
- `catalogue_tooling` owns reusable content, capability, filesystem, process, and audit primitives. The existing pack-owned `file_safety.py` remains the authoring source for its generated package projection.
- A new package-internal `work_supervisor` boundary owns acceptance projection/evaluation, approvals, evidence, containment, brokering, and legacy compatibility services; it does not schedule work in this slice.
- The Core `work-loop` source owns delivery policy and the compatibility caller; generated adapter projections remain build outputs.

Traces to AC-0001 through AC-0017. Owned by T1-T8.

### State & control flow

Owned by: T2, T3a, T3b, T3c, T4, T5, T6, T7, T8

Normal evaluation derives the current reviewed envelope from separately owned approvals, verifies that the initial review binds that fingerprint and terminal intent, projects the acknowledged legacy product subject and plan provenance, validates and appends evidence transactions, evaluates freshness and contradiction, then derives a verdict. The plan revision is provenance only; the caller receives a value, and no global phase, completion flag, plan approval, or task projection is written. Traces to AC-0003 through AC-0009. Owned by T4-T8.

Legacy import first reproduces both current digests, derives the current reviewed envelope, then publishes one authoritative spec-policy decision and one non-authoritative initial-plan review record bound to the envelope and terminal intent in one transaction. Restart either observes both records or recomputes both from the unchanged legacy pin. The Slice 1 classifier reports whether a proposed change stays outside protected authority or changes the envelope or intent; it creates no predecessor, task projection, cancellation, or dispatch record. Traces to AC-0001 through AC-0004, AC-0017. Owned by T5.

Security-sensitive semantic appends and effects validate the named writer or producer, intersect authority, verify containment where required, and, while the audit sink is available, durably emit a redacted event before acknowledging success or policy refusal. An unavailable sink fails closed with a stable redacted denial code, no effect success or protected-data persistence, and no durable-event claim. Any failed authority step leaves no semantic record or effect success. Traces to AC-0010 through AC-0015, AC-0020, and AC-0021. Owned by T2, T3a-T3c, T5, T7.

### Behavior & rules

Owned by: T2, T4, T5, T7

Accepted criteria and their approval-bound evidence policies are the only completion properties. The reviewed envelope fingerprints current approvals for scope/non-goals, authority and security decisions, public contracts, durable outputs, and accepted risk but grants none of them; terminal intent remains a separate initial-review authorization. Contradiction precedes support, a missing observation is insufficient, and in-envelope task, sequence, decomposition, test-shape, or method changes cannot change acceptance identity or require approval. Traces to AC-0003, AC-0004, AC-0007, AC-0009. Owned by T4, T5, T7.

Content decisions apply the architecture-owned profile matrix at the writer boundary. Rejected protected content leaves only a reason code without payload-derived material; accepted prose remains typed data at every consumer. Traces to AC-0014, AC-0015. Owned by T2.

### Failure, edge cases & resilience

Owned by: T2, T3a, T3b, T3c, T4, T5, T6, T7, T8

Unknown schema majors, missing or conflicting envelope references, ambiguous or expired writer authority, digest or envelope mismatch, partial transactions, a proposed change whose envelope fingerprint or terminal intent differs from the initial review, stale evidence, unreadable or drifting product state, unsupported containment, identity races, exceeded bounds, unavailable audit or security controls, and lossy reverse projection all refuse. The change classifier cannot dispatch or mutate tasks. Retries use stable record or operation identities and cannot turn a denial into an allow or publish a partial semantic record. Traces to AC-0002, AC-0004, AC-0006, AC-0008 through AC-0017, AC-0020, and AC-0021. Owned by T2-T8.

### Quality attributes (NFRs)

Owned by: T4, T7, T9a

Derived indexes may accelerate evaluation but deleting them must not change the verdict. The committed benchmark harness measures evaluator latency and cold rehydration on the CI reference worker against the fixed AC-0018 and AC-0019 corpus and clocks. Traces to AC-0007, AC-0008, AC-0018, AC-0019. Owned by T4, T7, T9a.

### Dependencies & integration

Owned by: T1, T8, T9b

Runtime code remains standard-library-only and integrates with Git through the existing acknowledged legacy result boundary. Test-only schema validation reuses the installed repository toolchain. Package and Core source changes flow through the existing self-host projection, package version, pack version, and release mechanisms. Traces to AC-0001, AC-0005, AC-0016. Owned by T1, T8, T9b.

## Tasks

### T0: An accepted engine-scoped RFC authorizes the package changes

**Depends on:** none

**Review shape:** DEEP — one governance review unit; no split.

**Touches:** `docs/rfc/` (one new RFC through the `new-rfc` skill), `docs/rfc/README.md` if it indexes RFCs

**Tests:**

- Mode: goal-based check.
- Stub: `no stub (goal-based check)`.
- The RFC proposes the Slice 1 engine change this spec and plan describe. It changes no Acceptance Criterion, scope, non-goal, or other protected field of this spec; a conflict routes back to this spec's owner.

**Done when:** the RFC records owner acceptance (`Status: Accepted`), and its number is the value every later `Engine-Change-RFC:` trailer cites.

### T1: Canonical delivery schemas and ownership checks pass

**Depends on:** T0

**Review shape:** DEEP — one review unit: the schema bundle and its registry and parity checks are understood and verified together; no split.

**Touches:** `contracts/delivery/**`, `contracts/README.md`, `contracts/REGISTRY.md`, package contract projections, schema and parity tests, and, per `tests/AGENTS.md`, a named roster step for the new `tests/roster/` file in `.github/workflows/build-check.yml` with its `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py`

**Tests:**

- Mode: TDD.
- AC-0001 through AC-0017, AC-0020, AC-0021: a contract suite validates every delivery schema against JSON Schema 2020-12, rejects unknown or incomplete authority-shaped records, verifies stable identity examples, and checks every declared package/pack projection against the canonical source.
- AC-0001 through AC-0017, AC-0020, AC-0021: registry coverage compares the discovered canonical schema set with `contracts/README.md`, `contracts/REGISTRY.md`, and the build manifest so an unregistered schema or undeclared copy fails.
- `test_delivery_contract_bundle_contains_valid_schemas` (AC-0003 — a missing or invalid bundle leaves the `reviewed-execution-envelope.v1` record that AC-0003 names undefined; it also guards the interface-compatibility durable output), `stub: true`; materialize at `tests/roster/test_delivery_contract_bundle.py` only after `CODE-IMPLEMENTATION`:

```python
# STUB: AC-0003 — canonical delivery contract bundle is present and schema-valid
import json
from pathlib import Path

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_delivery_contract_bundle_contains_valid_schemas() -> None:
    delivery_root = REPO_ROOT / "contracts" / "delivery"
    schemas = sorted(delivery_root.glob("*.schema.json"))
    assert schemas, "the canonical delivery contract bundle is missing"
    for schema_path in schemas:
        Draft202012Validator.check_schema(
            json.loads(schema_path.read_text(encoding="utf-8"))
        )
```

- PLAN handoff validation, re-run on 2026-10-01 for the revised stub against the pre-implementation tree from disposable scratch (stub at a scratch `tests/roster/` path, `contracts/` linked to the repository's, pytest started outside the repository): `python3 -m py_compile` passed; bounded `pytest -q` earned the intended red with one failure at `assert schemas` because the canonical `contracts/delivery/` bundle was not yet implemented. The validation created no repository test file; EXECUTE must materialize these exact fenced bytes before making the test green.

**Done when:** the T1 contract, registry, and projection suites pass from canonical source bytes.

### T2: Content-safety decisions conform at every semantic boundary

**Depends on:** T1

**Review shape:** DEEP — one review unit; no split.

**Touches:** `docs/architecture/delivery-content-safety.md`, package content-safety source, its tests, contract projections, Core compatibility consumers

**Tests:**

- Mode: TDD through integration tests.
- Stub: `no stub (implementation-discovered)` — select the package callable only after the contract suite proves the policy, decision, and inert-data record shapes; the seam must accept a named profile and bytes and return a typed decision without persistence.
- AC-0014: discover every Slice 1 durable semantic writer and replay boundary, assert the architecture profile matrix covers the same set including `initial-plan-review.v1`, parameterize each boundary over the shared credential, personal-data, control-character, encoding, executable-structure, unknown-field, and edge-plus-one size corpus, and compare normalized decisions; a missing or unknown profile refuses append and replay without durable payload bytes.
- AC-0015: instrument persistence and diagnostics to prove rejected payload bytes, excerpts, and content-derived hashes are absent, then drive accepted adversarial prose through every consumer and assert that it cannot select tools, actions, paths, or authority.

**Done when:** the architecture profile matrix names every Slice 1 durable writer and replay boundary, including `initial-plan-review.v1`, and the T2 coverage, cross-boundary corpus, missing-profile refusals, and inert-consumer negatives pass before any semantic writer task begins.

### T3a: Capability, confined-file mutation, and security-event invariants pass

**Depends on:** T1, T2

**Review shape:** DEEP — one review unit; the hand-maintained copies are byte-identical replicas checked by their pins, not separate review material; no split.

**Touches:** `packs/core/.apm/skills/close-work/scripts/file_safety.py`, generated package projection, the three hand-maintained byte-identical copies (`packs/core/.apm/skills/work-intake/scripts/file_safety.py`, `packs/core/.apm/skills/work-loop/scripts/file_safety.py`, `packs/architect/.apm/skills/architect-design/scripts/file_safety.py`) kept in sync with the source, capability and security-event source, unit and projection tests

**Tests:**

- Mode: TDD.
- Stub: `no stub (implementation-discovered)` — extend the pack-owned confinement source and choose the smallest package capability/audit modules whose public values can be mirrored without creating a second security implementation.
- AC-0010: property tests generate parent and requested grants and assert every child field is an intersection, with omitted network and child fields denying all.
- AC-0011: adversarial fixtures cover absolute and dot-segment paths, links, reparse points, multiple links, special files, identity replacement, bounds, interrupted staging, and atomic replacement while preserving the prior bytes on refusal.
- AC-0010, AC-0011, AC-0020, AC-0021: semantic-append and security-event tests assert named writer authority, stable reason codes, redacted metadata without request payloads, and durable audit before acknowledgment when the sink is available; when it is unavailable, tests require a stable redacted denial code, no effect success or protected-data persistence, and no durable-event claim.

**Done when:** the T3a capability, file-boundary, race, atomicity, audit, and source/projection parity suites pass, and every hand-maintained copy stays byte-identical to the source.

### T3b: Safe-process invariants pass across supported hosts

**Depends on:** T1, T3a

**Review shape:** DEEP — one review unit; no split.

**Touches:** package process-safety source, unit tests, platform fixtures, contract projections

**Tests:**

- Mode: TDD through operating-system integration tests.
- Stub: `no stub (implementation-discovered)` — choose the process callable after probing the existing package process helpers; the contract fixes inputs and refusals, not a symbol or class hierarchy.
- AC-0012: fixtures vary executable identity, argv values, current directory, environment, stdin, timeout, output volume, encoding, child trees, and redaction matches; each invalid or breached case proves no durable success and no surviving child.
- AC-0021: with an available sink, every process allow and policy denial emits its redacted event before acknowledgment; an unavailable audit path launches no process, retains no protected input or output, returns a stable redacted denial code, and makes no durable-event claim.
- AC-0012: platform-capability fixtures skip only when the host cannot supply the asserted primitive and require the runtime capability declaration to refuse unsupported guarantees.

**Done when:** the T3b process contract, timeout, tree-kill, output-bound, redaction, and portability suites pass.

### T3c: Containment and effect-broker conformance deny control-plane forgery

**Depends on:** T3a, T3b

**Review shape:** DEEP — one review unit; no split.

**Touches:** package containment and broker source, adapter conformance fixtures, Core capability wiring

**Tests:**

- Mode: TDD through end-to-end security conformance.
- Stub: `no stub (implementation-discovered)` — select the launcher and broker ports only after each supported host reports which containment axes it can attest; no same-process wrapper may claim OS isolation.
- AC-0010: compare every launcher attestation with its grant and refuse any broader root, read mode, network, child, or resource allowance.
- AC-0013: run direct-syscall, Git metadata, protected-ref, delivery-control, broker-bypass, privilege-amplification, and unsupported-host fixtures through every adapter; all forgery writes remain absent.
- AC-0020, AC-0021: attempt broker and security-event appends with missing, expired, and mismatched producer capabilities and with unavailable audit storage; available-sink policy denials persist their redacted event before acknowledgment, while unavailable-sink attempts expose no partial record or effect, return a stable redacted denial code without a durable-event claim, and remain denied on retry.

**Done when:** the T3c containment, broker, delegation, and cross-adapter forgery suites pass with zero bypass effects.

### T4: Pure acceptance projection, freshness, and verdict suites pass

**Depends on:** T1, T2

**Review shape:** DEEP — one review unit; the benchmark workflow is small, and its posture checks verify it alone; no split.

**Touches:** package acceptance source, pure unit/property tests, benchmark fixtures, `.github/workflows/benchmark-acceptance.yml`, the `WORKFLOWS` roster in `tools/check-zizmor-excessive-permissions.py`, a new posture test `tools/test-benchmark-acceptance-workflow.py` on `tools/posture_harness.py`, its gate-chain wiring in `tools/repo/build_gate_chain.py` with the matching `EXPECTED_SCRIPT_STEPS` pin in `tools/test_build_gate_chain.py`, the workflow's `WORKFLOW_SCOPE` classification in `tools/lint-ci-parity.py`, the workflow fleet table and §3.1 posture-test inventory in `docs/architecture/verification-graph.md`, and any other pin, roster, or inventory that registering a new workflow and gate-chain step obliges

**Tests:**

- Mode: TDD.
- Stub: `no stub (implementation-discovered)` — derive the smallest pure projector/evaluator API from the canonical records; the seam must be importable without Git, filesystem mutation, engine, or adapter dependencies.
- AC-0003: property tests permute equivalent ordered approval references and assert one reviewed-envelope fingerprint, vary each protected source approval independently and assert the fingerprint changes, and refuse missing, ambiguous, stale, or conflicting references; the resulting record grants no operation by itself.
- AC-0004: property tests vary only working-plan, task-order, decomposition, test-shape, and local-method provenance and assert the classifier returns `no-approval-required` without writing task state while envelope and acceptance fingerprints stay unchanged; changing terminal intent invalidates the initial review.
- AC-0007: truth-table and permutation tests compare every verdict across equivalent normalized record sets and adapter labels, including empty mechanical state.
- AC-0009: mutation tests change each exact-subject and path-set freshness input independently, assert staleness at the first mismatch, and assert missing or incomplete read attestation selects exact-subject.
- AC-0018: the committed benchmark measures p95 evaluator latency from call entry to full verdict return for the fixed corpus.
- Benchmark workflow posture, following `.github/workflows/test-corpus.yml`: no `inputs:`, top-level `permissions: contents: read`, `persist-credentials: false` on checkout, SHA-pinned `uses:`, per-run concurrency, a bounded `timeout-minutes`, and an uploaded artifact limited to the named benchmark result files plus the run's commit SHA. The workflow joins the `WORKFLOWS` roster in `tools/check-zizmor-excessive-permissions.py`. The posture test `tools/test-benchmark-acceptance-workflow.py` follows the repository's `tools/posture_harness.py` idiom (for example `tools/test-pack-evals-workflow.py`) and runs in the build gate chain; its mutation matrix fails when the `permissions:` floor, the `WORKFLOWS` roster entry, checkout `persist-credentials: false`, the absence of `inputs:`, the timeout, or the artifact path limit is removed. `tools/lint-ci-parity.py` classifies the new workflow in `WORKFLOW_SCOPE`.

**Done when:** the T4 projector, truth-table, freshness, determinism, and evaluator benchmark suites pass, the benchmark workflow posture checks pass, and the workflow is merged to `main` before T9a dispatches it.

### T5: Policy import, reviewed envelope, initial plan review, change classification, and reverse-read suites pass

**Depends on:** T1, T2, T3a, T4

**Review shape:** DEEP — one review unit; no split.

**Touches:** package approval/envelope/initial-review/import/change-classification/reverse-read source, frozen legacy corpus, Core compatibility adapter, integration tests

**Tests:**

- Mode: TDD through transaction and compatibility integration tests.
- Stub: `no stub (implementation-discovered)` — call the current canonicalizer through its owning module and select the approval, reviewed-envelope, initial-review, and change-classification ports only after the transaction owner is fixed by T1; do not copy normalization code.
- AC-0001: replay every frozen canonicalization fixture through current and target implementations and compare both artifact digests.
- AC-0002, AC-0014: derive the reviewed envelope, apply the named content-safety profiles, inject failure before, between, and after the spec-policy approval and envelope-bound initial-plan review, then restart and assert exactly zero or two visible records; malformed inputs, digest mismatch, envelope mismatch, wrong terminal intent, and a missing or unknown writer or replay profile publish zero.
- AC-0020: attempt both import appends with missing, expired, mismatched, and out-of-scope writer authority, including retry under the same record identity; every case exposes zero records.
- AC-0003, AC-0004: vary task order, decomposition, sequence, test shape, and local method independently and assert classification needs no approval while the envelope fingerprint and terminal intent remain fixed and no task, cancellation, or dispatch state is written; vary each protected approval reference or terminal intent and assert classification names the owning amendment, review, or risk route.
- AC-0017: during dual-read, reconstruct the original approved pair. Post-cutover behavior runs under a synthetic accepted authority-switch decision fixture, because this slice enables no real cutover: with the decision present, a within-envelope legacy compatibility snapshot is produced that grants no target authority and deletes no semantic facts; without it, the snapshot refuses; a lossy or boundary-crossing projection refuses.

**Done when:** the T5 canonicalization, envelope derivation, atomic import, initial-review, mutation-classification, protected-change refusal, restart, and reverse-reader suites pass without implementing Slice 4 task reprojection.

### T6: Legacy subject projection matches the acknowledged product boundary

**Depends on:** T1, T3a, T4

**Review shape:** DEEP — one review unit; no split.

**Touches:** package subject-source and projection source, Git/worktree fixtures, compatibility tests

**Tests:**

- Mode: TDD through Git integration tests.
- Stub: `no stub (implementation-discovered)` — locate the existing-engine acknowledged result boundary before choosing the provider seam; arbitrary dirty worktree state is not an input substitute.
- AC-0005: compare legacy and runtime-neutral canonical manifests, fingerprints, exclusions, spec identity, and plan provenance for the same acknowledged tree.
- AC-0006: mutate ignored, untracked, excluded, unreadable, link-like, non-regular, unacknowledged, and drifting paths one at a time and assert refusal or policy exclusion without a partial manifest.
- AC-0006: exercise the bound edge and edge-plus-one fixtures for every product traversal limit owned by [`work-loop-acceptance-evidence.md` §6](../../architecture/work-loop-acceptance-evidence.md#6-deployment-and-operations), plus the oversized-repository fixture specified in [§7](../../architecture/work-loop-acceptance-evidence.md#7-quality-scenarios-and-verification); the projector refuses before emitting a partial manifest and the plan does not duplicate the architecture-owned numeric values.

**Done when:** the T6 provider-parity and every subject-admission negative fixture pass.

### T7: Evidence transactions recover and rehydrate without cached authority

**Depends on:** T1, T2, T4, T6

**Review shape:** DEEP — one review unit; no split.

**Touches:** package evidence-store source, crash harness, index and benchmark tests, and the cold-rehydration job in `.github/workflows/benchmark-acceptance.yml` with any matching posture-test update

**Tests:**

- Mode: TDD through append-log integration tests.
- Stub: `no stub (implementation-discovered)` — choose framing and append seams after T1 fixes transaction identity and checksum fields; use exclusive append/replace primitives rather than a database or new dependency.
- AC-0008: crash injection at every frame boundary proves all-or-none visibility, incomplete-final-frame truncation, corruption refusal, index deletion/rebuild, and verdict equivalence from the complete prefix.
- AC-0009: receipt and supersession fixtures prove stale or inadmissible records cannot support a property and contradiction is evaluated before support.
- AC-0020: receipt and supersession appends validate the named producer capability before staging durable bytes; missing, expired, mismatched, and out-of-scope authority plus retries expose no partial transaction.
- AC-0019: a fresh-process benchmark deletes indexes, replays the fixed corpus, and measures through complete verdict return.

**Done when:** the T7 atomicity, corruption, restart, index-rebuild, freshness, and cold-rehydration suites pass.

### T8: Current-engine compatibility calls preserve authority and public behavior

**Depends on:** T3c, T5, T6, T7

**Review shape:** DEEP — one review unit; no split.

**Touches:** Core work-loop source and scripts, package compatibility facade, pack evals, engine/cohort regression tests

**Tests:**

- Mode: goal-based check through end-to-end compatibility suites.
- Stub: `no stub (goal-based check)`.
- AC-0007: dual-emitted legacy and target evidence over the frozen corpus yields identical verdicts after deleting target indexes and mechanical state.
- AC-0016: command, transition, legacy-plan-pin, cohort-writer, no-dispatch, and completion-decision fixtures compare before and after compatibility wiring; the target initial-review record remains non-authoritative for tasks, and Slice 1 creates no target task-projection record or plan approval.
- AC-0017: disabling target calls restores the legacy path, while a missing accepted governance fingerprint refuses every target-authority switch; downgrade approval authorizes the authority switch and compatibility snapshot, not the plan's task content.

**Done when:** the T8 compatibility, cache-deletion, public-command, authority, and reversal gates pass with no unexplained parity difference.

### T9a: Integrated conformance and benchmark evidence pass

**Depends on:** T1, T2, T3a, T3b, T3c, T4, T5, T6, T7, T8

**Review shape:** DEEP — one review unit of integrated evidence; no split.

**Touches:** cross-adapter conformance suites, benchmark harness extensions

**Tests:**

- Mode: goal-based check through repository gates and real compatibility invocations.
- Stub: `no stub (goal-based check)`.
- AC-0001 through AC-0021: run the frozen import, subject, verdict, recovery, reversal, security, content-safety, authorized-append, audit-failure, and cross-adapter corpora against the built package and projected Core pack.
- AC-0018, AC-0019: dispatch the benchmark workflow on GitHub-hosted `ubuntu-latest` with `--ref` on the T9a branch, and retain the measured p95 evaluation and cold-rehydration outputs with the run's commit SHA.
- Real invocation: run the unchanged documented `work-loop` happy path through the compatibility caller and record the command, exit status, derived verdict, and confirmation that legacy authority made the decision.

**Done when:** the T9a conformance and repository gates pass, the retained benchmark run meets AC-0018 and AC-0019, and the real invocation preserves legacy authority.

### T9b: Durable documentation and release closure pass

**Depends on:** T9a

**Review shape:** DEEP — one review unit; its version and changelog edits are mechanical bookkeeping for the documented change; no split.

**Touches:** architecture pages, maintainer procedure, contract registry, package/Core/architect versions and changelog, generated projections

**Tests:**

- Mode: goal-based check through repository gates.
- Stub: `no stub (goal-based check)`.
- Durable outputs: run package tests, touched Core pack evals, source/projection parity, catalogue lint/verify, build-self zero-diff rerun, spec/brief/status lints, and documentation link checks.

**Done when:** the T9b repository gates pass, durable outputs describe current state, and release versions align.

## Rollout

- **Delivery:** contracts and readers land before writers. Each target writer runs behind the current compatibility path and produces shadow facts until parity and recovery evidence are clean. Initial review records its envelope and authorized terminal intent but creates no task projection; Slice 4 will own approval-free in-envelope reprojection. Rollback disables target calls and reads the retained legacy state; it does not delete new semantic facts.
- **Infrastructure:** no daemon, external service, database, queue, cloud resource, secret, or mandatory sandbox product is introduced. Untrusted execution activates only where the host supplies verified containment; otherwise it refuses.
- **External-system integration:** none. Git and the local operating system remain the only runtime integrations.
- **Deployment sequencing:** the T0 RFC precedes every package change; T1 contracts precede every reader; T2 and T3 security controls precede semantic writers and untrusted execution; T4 precedes stores; T5-T7 precede compatibility calls; T8 parity precedes documentation and release closure. No authority cutover occurs in this rollout, and no working-plan revision becomes an approval record.

## Risks

- A broad service layer could recreate the workflow engine under new names. Pure evaluators, typed ports, and the prohibition on stored phase/task completion keep procedure out of this slice.
- Canonicalization drift could make existing approved work unimportable. The frozen corpus compares current and target digests before any decision is published.
- Mutable planning could cross product or security intent unnoticed. Protected-boundary fixtures cover every AC-0003 field and terminal intent, return the owning amendment or review route, and prove that in-envelope task guidance is classified as outside approval authority without dispatching or mutating task state.
- A generated security helper could be edited at the wrong layer and disappear on rebuild. T3a changes the pack-owned source and pins the generated package projection.
- Host-specific containment could be overstated. Capability declarations and attestations refuse guarantees a host cannot prove, and untrusted code has no same-process fallback.
- Content scanning cannot detect every natural-language instruction or personal identifier. Schema allowlists, producer classification, reject-unknown behavior, and inert consumption remain the hard boundary.
- Append-log volume could miss the latency targets. Derived indexes may optimize reads, but the cold benchmark deletes them and the evaluator never treats them as authority.
- Package and Core projections could ship at different revisions. T1/T9b parity gates, coupled versions, and the release record keep the bundle aligned.

## Changelog

- 2026-10-01: spec approved by owner
- 2026-10-01: plan approved by owner as the initial strategy, safety,
  dependency, scope-alignment, and terminal-intent review; tasks remain mutable
  inside that reviewed envelope.
- 2026-10-01: terminal intent amended from `spec-plan` to `code` on owner
  request to implement Slice 1. No other protected field changed. The spec
  `Brief:` pointer lost its stray backticks so workspace provenance resolves.
  The approvals above stay as history; this amendment needs fresh spec and
  plan review and fresh human approval of both.
- 2026-10-01: round-1 review revisions. Terminal intent now names the slice
  boundary, not task IDs. Added T0 (accepted engine-scoped RFC, owner
  decision), T5's T3a dependency, the in-force re-plan rule, the
  hand-maintained `file_safety.py` copies, the supported adapter set, the
  synthetic authority-switch fixture, the benchmark host (owner decision:
  dispatch-only `ubuntu-latest`), and a cwd-independent T1 stub. Owner
  approved adding the architect pack release files to the spec's Release
  history durable output, the only other protected-field change.
- 2026-10-01: round-2 review revisions. Owner decision: T4 adds the
  dispatch-only benchmark workflow and merges it to `main` before T9a
  dispatches it. T4 states and regression-checks the workflow's
  least-privilege posture. Every task declares its review shape, and T9
  splits into T9a (integrated evidence) and T9b (documentation and release
  closure). The T1 stub marker names AC-0003.
- 2026-10-01: round-3 review revisions. T4 names the benchmark workflow,
  its `posture_harness` posture test, gate-chain wiring, and `WORKFLOW_SCOPE`
  classification. T1 lists its roster step and parity disposition. T7 lists
  the cold-rehydration job it adds to the benchmark workflow.
- 2026-10-01: round-4 review revisions. T4 Touches adds the gate-chain
  step pin, the verification-graph workflow and posture-test inventory, and
  the general obligation to register a new workflow and gate-chain step
  completely.

<!-- Approval entries are added only at their human gates.

- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->
