# Plan: Acceptance authority and evidence

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/architecture/acceptance-centered-work-loop.md`, `docs/architecture/work-loop-authority-migration.md`, `docs/architecture/work-loop-acceptance-evidence.md`, `docs/architecture/runtime-security-primitives.md`, `docs/architecture/delivery-content-safety.md`; analogous implementations `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py` and `packs/core/.apm/skills/close-work/scripts/file_safety.py`; tests `packs/core/tests/skills/work-loop/test_loop_cohort.py` and `packages/agentbundle/tests/unit/test_catalogue_tooling_file_safety.py`. Deviation: the reviewed security design names `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py` as a source, while `packages/agentbundle/agentbundle/build/self_host.py` and `packs/AGENTS.local.md` identify it as a generated destination; this slice leaves `file_safety.py` and every copy unchanged and builds new confined-mutation primitives beside the `work-loop` skill's local copy (owner decision, 2026-10-01). Placement deviation: the Draft architecture names `packages/agentbundle/agentbundle/work_supervisor/` and `catalogue_tooling/` modules; this slice instead implements every service as a work-loop skill script, per the brief's script packaging pattern and its non-goal against a mandatory `agentbundle` runtime (owner decision, 2026-10-01). T9b updates those architecture pages to match.

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
- `contracts/delivery/` is the canonical schema source. No delivery schema is read at runtime: the standard-library scripts validate records in code, and the JSON Schemas are test-time contracts. So no schema copy ships in the Core pack, and the T1 suite asserts that no delivery schema copy exists outside `contracts/delivery/`.
- Runtime code uses the Python standard library. The existing test toolchain may validate JSON Schema; this slice adds no runtime dependency.
- Script code uses list-form process execution, explicit UTF-8, portable temporary paths, and platform-skipped link or execute-bit tests where the host cannot supply the capability.
- Every Slice 1 service is a self-contained standard-library module in `packs/core/.apm/skills/work-loop/scripts/`, beside `loop-engine.py` and `loop-cohort.py`, and reaches users through `make build-self` projections. No Slice 1 service code goes under `packages/agentbundle/`, and the skill gains no runtime dependency on `agentbundle` or any other package (owner decision, 2026-10-01). Security primitives import the skill's local byte-identical `file_safety.py` copy and leave it, and every other copy, unchanged.
- Core pack changes carry their version updates, evals, generated projections, and release record. No file under `packages/agentbundle/` changes in this slice, so no commit needs an `Engine-Change-RFC:` trailer; T9a confirms the package tree is unchanged against the base.
- The supported adapter set for this slice is the sequential reference runtime plus the Core compatibility adapter. The work-loop scripts declare that set in one place, and the conformance suites refuse to run against an empty or single-member declaration, so AC-0007 and AC-0013 always compare at least two adapters.
- "The CI reference worker" in AC-0018 and AC-0019 means a GitHub-hosted `ubuntu-latest` runner executing the existing dispatch-only `.github/workflows/test-corpus.yml`, whose `make test` shards already run the work-loop pack suite. The AC-0018 and AC-0019 benchmarks are pytest tests in that suite: each runs the committed harness, asserts its bound, and prints the measurement into the job log. No workflow changes. No pull request opens before this spec ships (owner decision); `test-corpus.yml` is already on the default branch, so T9a dispatches `gh workflow run test-corpus.yml --ref <branch>` after confirming with the owner. The committed harness fixes the timed-run count and warm-up policy.

## Construction tests

**Integration tests:**

- A frozen approved-artifact corpus drives legacy canonicalization, atomic import, reverse read, protected-change classification, legacy subject projection, verdict parity, and cache-deletion rehydration across the script services and the Core compatibility adapter.
- A shared adversarial corpus drives filesystem, process, capability, containment, control-plane forgery, content-safety, and inert-consumption conformance through every supported adapter.
- Crash injection covers every approval and evidence transaction boundary, then restarts from only durable bytes and compares the complete semantic record set and verdict.
- Cross-platform fixtures cover POSIX links, Windows reparse/junction behavior where available, process-tree termination, executable identity replacement, bounded output, and unsupported-capability refusal.

**Manual verification:** none. The slice exposes no UI or human-only judgment; all acceptance evidence comes from deterministic tests, conformance suites, benchmarks, and build gates.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Canonical delivery contracts and registry | T1, T9b | Schema, registry, and no-copy suites | `contracts/README.md` and `contracts/REGISTRY.md` name every shipped record and owner; no delivery schema copy exists outside `contracts/delivery/`. |
| Current architecture and authority migration | T8, T9b | Compatibility and missing-governance refusal suites | Architecture pages describe callable shadow services, current authority, reversal, and future cutover gates. |
| Maintainer parity, recovery, and reversal procedure | T5, T6, T7, T8, T9a, T9b | Import, restart, cache-deletion, reverse-read, and end-to-end commands | `docs/architecture/loop-infrastructure.md` names the commands and expected results without relying on this plan. |
| Core release history and versions | T9b | Pack tests, pack evals, build-self, version parity, and changelog lint | The Core version is released when required, and `docs/product/changelog.md` records the outcome. |

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

The work-loop skill scripts expose in-process Python ports (importable standard-library modules) for subject projection, reviewed-envelope derivation, spec-policy approval and initial-review import and lookup, protected-change classification, evidence append and replay, acceptance evaluation, capability issue/intersection, confined file and process operations, containment launch, effect brokering, auditing, and content-safety decisions. The exact Python symbols are implementation-discovered from the smallest cohesive set of script modules; the JSON contracts and tests define behavior before those symbols freeze. Traces to AC-0001 through AC-0017. Owned by T2-T8.

The Core compatibility adapter translates existing engine events and approved pins into typed calls, dual-emits old and new facts, and treats every target result as shadow data. It changes no public `work-loop` invocation. Traces to AC-0001, AC-0002, AC-0007, AC-0016, AC-0017. Owned by T5, T8.

### Component / module decomposition

Owned by: T1, T2, T3a, T3b, T3c, T4, T5, T6, T7, T8

- `contracts/delivery/` owns portable record shape and identity.
- Security primitive modules in `packs/core/.apm/skills/work-loop/scripts/` own reusable content-safety, capability, process, and audit mechanics. They build on the skill's local copy of the pack-owned `file_safety.py`, whose authoring source `packs/core/.apm/skills/close-work/scripts/file_safety.py` stays unchanged.
- Acceptance service modules in the same scripts directory own acceptance projection/evaluation, approvals, evidence, containment, brokering, and legacy compatibility services; they do not schedule work in this slice.
- The Core `work-loop` source owns delivery policy and the compatibility caller; generated adapter projections remain build outputs.
- Nothing in this slice imports from `agentbundle`.

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

Runtime code remains standard-library-only and integrates with Git through the existing acknowledged legacy result boundary. Test-only schema validation reuses the installed repository toolchain. Core pack source changes flow through the existing self-host projection, pack version, and release mechanisms; the scripts import nothing from `agentbundle`. Traces to AC-0001, AC-0005, AC-0016. Owned by T1, T8, T9b.

## Tasks

### T1: Canonical delivery schemas and ownership checks pass

**Depends on:** none

**Review shape:** DEEP — one review unit: the schema bundle and its registry and parity checks are understood and verified together; no split.

**Touches:** `contracts/delivery/**`, `contracts/README.md`, `contracts/REGISTRY.md`, schema and registry tests, and, per `tests/AGENTS.md`, a named roster step for the new `tests/roster/` file in `.github/workflows/build-check.yml` with its `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py`

**Tests:**

- Mode: TDD.
- AC-0001 through AC-0017, AC-0020, AC-0021: a contract suite validates every delivery schema against JSON Schema 2020-12, rejects unknown or incomplete authority-shaped records, verifies stable identity examples, and asserts that no copy of a delivery schema exists outside `contracts/delivery/`.
- AC-0001 through AC-0017, AC-0020, AC-0021: registry coverage compares the discovered canonical schema set with `contracts/README.md` and `contracts/REGISTRY.md` so an unregistered schema fails.
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

**Done when:** the T1 contract and registry suites, including the no-copy-outside-`contracts/delivery/` assertion, pass from canonical source bytes.

### T2: Content-safety decisions conform at every semantic boundary

**Depends on:** T1

**Review shape:** DEEP — one review unit; no split.

**Touches:** `docs/architecture/delivery-content-safety.md`, the work-loop script content-safety module, its tests, Core compatibility consumers

**Tests:**

- Mode: TDD through integration tests.
- Stub: `no stub (implementation-discovered)` — select the script callable only after the contract suite proves the policy, decision, and inert-data record shapes; the seam must accept a named profile and bytes and return a typed decision without persistence.
- AC-0014: discover every Slice 1 durable semantic writer and replay boundary, assert the architecture profile matrix covers the same set including `initial-plan-review.v1`, parameterize each boundary over the shared credential, personal-data, control-character, encoding, executable-structure, unknown-field, and edge-plus-one size corpus, and compare normalized decisions; a missing or unknown profile refuses append and replay without durable payload bytes.
- AC-0015: instrument persistence and diagnostics to prove rejected payload bytes, excerpts, and content-derived hashes are absent, then drive accepted adversarial prose through every consumer and assert that it cannot select tools, actions, paths, or authority.

**Done when:** the architecture profile matrix names every Slice 1 durable writer and replay boundary, including `initial-plan-review.v1`, and the T2 coverage, cross-boundary corpus, missing-profile refusals, and inert-consumer negatives pass before any semantic writer task begins.

### T3a: Capability, confined-file mutation, and security-event invariants pass

**Depends on:** T1, T2

**Review shape:** DEEP — one review unit; no split.

**Touches:** the work-loop script confined-mutation, capability, and security-event modules built on the skill's local `file_safety.py` copy (left unchanged), unit tests

**Tests:**

- Mode: TDD.
- Stub: `no stub (implementation-discovered)` — build on the local confinement copy without changing it, and choose the smallest work-loop script mutation, capability, and audit modules that avoid creating a second implementation of what `file_safety.py` already provides.
- AC-0010: property tests generate parent and requested grants and assert every child field is an intersection, with omitted network and child fields denying all.
- AC-0011: adversarial fixtures cover absolute and dot-segment paths, links, reparse points, multiple links, special files, identity replacement, bounds, interrupted staging, and atomic replacement while preserving the prior bytes on refusal.
- AC-0010, AC-0011, AC-0020, AC-0021: semantic-append and security-event tests assert named writer authority, stable reason codes, redacted metadata without request payloads, and durable audit before acknowledgment when the sink is available; when it is unavailable, tests require a stable redacted denial code, no effect success or protected-data persistence, and no durable-event claim.

**Done when:** the T3a capability, file-boundary, race, atomicity, and audit suites pass, and `file_safety.py` and every copy are byte-unchanged.

### T3b: Safe-process invariants pass across supported hosts

**Depends on:** T1, T3a

**Review shape:** DEEP — one review unit; no split.

**Touches:** the work-loop script process-safety module, unit tests, platform fixtures

**Tests:**

- Mode: TDD through operating-system integration tests.
- Stub: `no stub (implementation-discovered)` — choose the process callable after probing the existing repository process helpers; the contract fixes inputs and refusals, not a symbol or class hierarchy.
- AC-0012: fixtures vary executable identity, argv values, current directory, environment, stdin, timeout, output volume, encoding, child trees, and redaction matches; each invalid or breached case proves no durable success and no surviving child.
- AC-0021: with an available sink, every process allow and policy denial emits its redacted event before acknowledgment; an unavailable audit path launches no process, retains no protected input or output, returns a stable redacted denial code, and makes no durable-event claim.
- AC-0012: platform-capability fixtures skip only when the host cannot supply the asserted primitive and require the runtime capability declaration to refuse unsupported guarantees.

**Done when:** the T3b process contract, timeout, tree-kill, output-bound, redaction, and portability suites pass.

### T3c: Containment and effect-broker conformance deny control-plane forgery

**Depends on:** T3a, T3b

**Review shape:** DEEP — one review unit; no split.

**Touches:** the work-loop script containment and broker modules, adapter conformance fixtures, Core capability wiring

**Tests:**

- Mode: TDD through end-to-end security conformance.
- Stub: `no stub (implementation-discovered)` — select the launcher and broker ports only after each supported host reports which containment axes it can attest; no same-process wrapper may claim OS isolation.
- AC-0010: compare every launcher attestation with its grant and refuse any broader root, read mode, network, child, or resource allowance.
- AC-0013: run direct-syscall, Git metadata, protected-ref, delivery-control, broker-bypass, privilege-amplification, and unsupported-host fixtures through every adapter; the delivery-control fixtures read the set of `work-loop` skill copies from `contracts/adapter.toml` for the Core pack's declared surfaces, and attempt writes to the pack source, each such copy, and each runtime-read schema or policy file; all forgery writes remain absent.
- AC-0020, AC-0021: attempt broker and security-event appends with missing, expired, and mismatched producer capabilities and with unavailable audit storage; available-sink policy denials persist their redacted event before acknowledgment, while unavailable-sink attempts expose no partial record or effect, return a stable redacted denial code without a durable-event claim, and remain denied on retry.

**Done when:** the T3c containment, broker, delegation, and cross-adapter forgery suites pass with zero bypass effects.

### T4: Pure acceptance projection, freshness, and verdict suites pass

**Depends on:** T1, T2

**Review shape:** DEEP — one review unit; no split.

**Touches:** the work-loop script acceptance modules and benchmark harness, pure unit/property tests, the AC-0018 benchmark test in the work-loop pack suite, the acceptance schema-parity roster suite with its `build-check.yml` step and `STEP_DISPOSITION` entry

**Tests:**

- Mode: TDD.
- Stub: `no stub (implementation-discovered)` — derive the smallest pure projector/evaluator API from the canonical records; the seam must be importable without Git, filesystem mutation, engine, or adapter dependencies.
- AC-0003: property tests permute equivalent ordered approval references and assert one reviewed-envelope fingerprint, vary each protected source approval independently and assert the fingerprint changes, and refuse missing, ambiguous, stale, or conflicting references; the resulting record grants no operation by itself.
- AC-0004: property tests vary only working-plan, task-order, decomposition, test-shape, and local-method provenance and assert the classifier returns `no-approval-required` without writing task state while envelope and acceptance fingerprints stay unchanged; changing terminal intent invalidates the initial review.
- AC-0007: truth-table and permutation tests compare every verdict across equivalent normalized record sets and adapter labels, including empty mechanical state.
- AC-0009: mutation tests change each exact-subject and path-set freshness input independently, assert staleness at the first mismatch, and assert missing or incomplete read attestation selects exact-subject.
- AC-0018: a pytest test in the work-loop pack suite runs the committed harness (exactly 1,000 approved criteria and 100,000 admitted evidence records, a fixed timed-run count and warm-up policy), asserts p95 from call entry to full verdict return is within 2 seconds, and prints the measurement; it writes results only under a temporary path.

**Done when:** the T4 projector, truth-table, freshness, determinism, parity, and evaluator benchmark suites pass.

### T5: Policy import, reviewed envelope, initial plan review, change classification, and reverse-read suites pass

**Depends on:** T1, T2, T3a, T4

**Review shape:** DEEP — one review unit; no split.

**Touches:** the work-loop script approval/envelope/initial-review/import/change-classification/reverse-read modules, frozen legacy corpus, Core compatibility adapter, integration tests

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

**Touches:** the work-loop script subject-source and projection modules, Git/worktree fixtures, compatibility tests

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

**Touches:** the work-loop script evidence-store module, crash harness, index and benchmark tests, and the AC-0019 cold-rehydration benchmark test in the work-loop pack suite

**Tests:**

- Mode: TDD through append-log integration tests.
- Stub: `no stub (implementation-discovered)` — choose framing and append seams after T1 fixes transaction identity and checksum fields; use exclusive append/replace primitives rather than a database or new dependency.
- AC-0008: crash injection at every frame boundary proves all-or-none visibility, incomplete-final-frame truncation, corruption refusal, index deletion/rebuild, and verdict equivalence from the complete prefix.
- AC-0009: receipt and supersession fixtures prove stale or inadmissible records cannot support a property and contradiction is evaluated before support.
- AC-0020: receipt and supersession appends validate the named producer capability before staging durable bytes; missing, expired, mismatched, and out-of-scope authority plus retries expose no partial transaction.
- AC-0019: a pytest test in the work-loop pack suite starts a fresh process that deletes indexes, replays exactly 1,000 approved criteria and 100,000 admitted evidence records, and asserts complete verdict return within 10 seconds, printing the measurement.

**Done when:** the T7 atomicity, corruption, restart, index-rebuild, freshness, and cold-rehydration suites pass.

### T8: Current-engine compatibility calls preserve authority and public behavior

**Depends on:** T3c, T5, T6, T7

**Review shape:** DEEP — one review unit; no split.

**Touches:** Core work-loop source and scripts, the script compatibility facade, pack evals, engine/cohort regression tests

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
- AC-0001 through AC-0021: run the frozen import, subject, verdict, recovery, reversal, security, content-safety, authorized-append, audit-failure, and cross-adapter corpora against the projected Core pack (`make build-self` output).
- Clean-environment fence: run the projected work-loop scripts' compatibility path in an environment where `agentbundle` is not importable, after first proving it is not importable there, and assert the path completes. A static check asserts every runtime module in the projected `work-loop` skill imports only the Python standard library or its own sibling modules; an optional import inside an `ImportError` guard that falls back to standard-library behavior is allowed, as in the existing `lint-spec-status.py` `tomli` fallback. A diff against the base asserts no file under `packages/agentbundle/` changed.
- AC-0018, AC-0019: after owner confirmation, dispatch `gh workflow run test-corpus.yml --ref <branch>`; the evidence is the passing AC-0018 and AC-0019 benchmark tests in the shard that runs the work-loop pack suite, with their printed measurements and the run's head commit SHA.
- Real invocation: run the unchanged documented `work-loop` happy path through the compatibility caller and record the command, exit status, derived verdict, and confirmation that legacy authority made the decision.

**Done when:** the T9a conformance and repository gates pass, the retained benchmark run meets AC-0018 and AC-0019, and the real invocation preserves legacy authority.

### T9b: Durable documentation and release closure pass

**Depends on:** T9a

**Review shape:** DEEP — one review unit; its version and changelog edits are mechanical bookkeeping for the documented change; no split.

**Touches:** architecture pages, maintainer procedure, contract registry, Core versions and changelog, generated projections

**Tests:**

- Mode: goal-based check through repository gates.
- Stub: `no stub (goal-based check)`.
- Durable outputs: run Core pack tests, touched Core pack evals, source/projection parity, catalogue lint/verify, build-self zero-diff rerun, spec/brief/status lints, and documentation link checks.

**Done when:** the T9b repository gates pass, durable outputs describe current state, and release versions align.

## Rollout

- **Delivery:** contracts and readers land before writers. Each target writer runs behind the current compatibility path and produces shadow facts until parity and recovery evidence are clean. Initial review records its envelope and authorized terminal intent but creates no task projection; Slice 4 will own approval-free in-envelope reprojection. Rollback disables target calls and reads the retained legacy state; it does not delete new semantic facts.
- **Infrastructure:** no daemon, external service, database, queue, cloud resource, secret, or mandatory sandbox product is introduced. Untrusted execution activates only where the host supplies verified containment; otherwise it refuses.
- **External-system integration:** none. Git and the local operating system remain the only runtime integrations.
- **Deployment sequencing:** T1 contracts precede every reader; T2 and T3 security controls precede semantic writers and untrusted execution; T4 precedes stores; T5-T7 precede compatibility calls; T8 parity precedes documentation and release closure. No authority cutover occurs in this rollout, and no working-plan revision becomes an approval record.

## Risks

- A broad service layer could recreate the workflow engine under new names. Pure evaluators, typed ports, and the prohibition on stored phase/task completion keep procedure out of this slice.
- Canonicalization drift could make existing approved work unimportable. The frozen corpus compares current and target digests before any decision is published.
- Mutable planning could cross product or security intent unnoticed. Protected-boundary fixtures cover every AC-0003 field and terminal intent, return the owning amendment or review route, and prove that in-envelope task guidance is classified as outside approval authority without dispatching or mutating task state.
- The shared confinement helper could drift if Slice 1 edited it, because its package copies are generated. This slice leaves `file_safety.py` and every copy unchanged and builds new mutation primitives beside the local copy.
- Host-specific containment could be overstated. Capability declarations and attestations refuse guarantees a host cannot prove, and untrusted code has no same-process fallback.
- Content scanning cannot detect every natural-language instruction or personal identifier. Schema allowlists, producer classification, reject-unknown behavior, and inert consumption remain the hard boundary.
- Append-log volume could miss the latency targets. Derived indexes may optimize reads, but the cold benchmark deletes them and the evaluator never treats them as authority.
- Contract source and Core pack projections could ship at different revisions. T1/T9b parity gates, coupled versions, and the release record keep the bundle aligned.

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
- 2026-10-01: spec approved by owner (code-mode run, terminal intent `code`)
- 2026-10-01: plan approved by owner (code-mode run)
- 2026-10-01: controlled contract amendment from `CODE-IMPLEMENTATION`
  before any task completed. Owner decision: every Slice 1 service is a
  self-contained work-loop skill script, not code under
  `packages/agentbundle/`, per the brief's script packaging pattern and its
  non-goal against a mandatory `agentbundle` runtime. T0 and the draft
  RFC-0105 are dropped; generated-copy-only package commits use
  `Engine-Change-RFC: n/a — generated projection`. Spec Agent Rules and the
  Release history durable output changed to match. T9a adds a
  clean-environment fence. Spec and plan return to Draft/Drafting for fresh
  review and approval.
- 2026-10-01: round-6 review revisions. Owner decisions: T3a leaves
  `file_safety.py` and every copy unchanged and builds new confined-mutation
  primitives beside the work-loop skill's local copy, so no file under
  `packages/agentbundle/` changes and no `Engine-Change-RFC:` trailer is
  needed; AC-0013 names the work-loop skill's own runtime (pack source,
  generated copies, runtime-read schemas and policy) as delivery-control
  paths. Protected spec fields changed in this amendment overall: Agent
  Rules (two Always-do rules and one Never-do rule), AC-0013, Testing
  Strategy (release line), and Durable Outputs (Interface compatibility
  applicability; Release history narrowed to the Core pack, since no
  architect copy changes). T9a's fence now covers every non-standard-library
  import and the unchanged package tree.
- 2026-10-01: round-7 review revisions. Owner decisions: the Never-do
  rule and T9a check allow an `ImportError`-guarded optional import with a
  standard-library fallback; AC-0013's protected copies are every
  `work-loop` projection `contracts/adapter.toml` declares for the Core
  pack's surfaces; the Current architecture closeout adds that no listed
  page places a Slice 1 service under `packages/agentbundle/`; later-slice
  pages keep their placement until their own specs adopt this decision, and
  the brief is not edited here because sibling specs pin its byte revision. No delivery
  schema is read at runtime, so no schema copy ships in the Core pack.
- 2026-10-01: round-8 review revisions. The Never-do rule now names Python
  imports only (running `git` or reading the skill's own `assets/` is not an
  import); the Interface compatibility and Release history rows drop the
  projection clauses the no-runtime-schema decision removed; T1, T2, T3b,
  and the durable-output map drop leftover projection wording. Owner kept
  the round-7 AC-0013 set and import allowance unchanged.
- 2026-10-01: round-9 shaping correction: the Maintainer procedure owner
  is Core maintainers, since no Slice 1 command or service is
  `agentbundle`-owned.
- 2026-10-01: spec approved by owner (amended contract: work-loop skill scripts placement)
- 2026-10-01: plan approved by owner (amended contract)
- 2026-10-01: controlled contract amendment from `CODE-IMPLEMENTATION` with
  T1 and T2 completed. Owner decision: no pull request opens before this
  spec ships, so a new workflow could never reach `main` for T9a to
  dispatch. The benchmarks become a job in the existing dispatch-only
  `test-corpus.yml`, dispatched with `--ref` on this branch after owner
  confirmation; T4 adds a posture test for that workflow. T3a's work is
  committed and is re-accounted when its wave is rescheduled. Spec text is
  unchanged; both files return to Draft/Drafting for re-approval.
- 2026-10-01: round-11 review revisions. Owner decision: the benchmark job
  is a declared, separately pinned exception to `test-corpus-sharding`'s
  single-roster rule, recorded in an ADR in T4 with every claim site it
  touches. The posture test also fails on an added trigger, a job-level
  `permissions:` block, a non-`ubuntu-latest` runner, or a `secrets.`
  reference, and T9a runs the posture test and the workflow scanners on the
  exact dispatched commit first, since `ci-security.yml` needs a pull
  request.
- 2026-10-01: spec re-approved by owner after the benchmark-route amendment
- 2026-10-01: plan re-approved by owner (benchmark job as a declared test-corpus exception)
- 2026-10-01: controlled contract amendment with T1 and T2 completed.
  Owner decision after a local measurement (the AC-0018 harness takes 8.0 s
  for all 105 runs): the benchmarks are pytest tests in the work-loop pack
  suite that `make test` already runs, so `test-corpus.yml` shards measure
  them on `ubuntu-latest` with no workflow change. The benchmark job, its
  posture test, the single-roster exception, and its ADR are dropped. Spec
  text is unchanged; both files return to Draft/Drafting for re-approval.

<!-- Approval entries are added only at their human gates.

- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->
