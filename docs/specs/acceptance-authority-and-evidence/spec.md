# Spec: Acceptance authority and evidence

- **Status:** Implementing
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0005, ADR-0061, ADR-0125
- **Brief:** brief:acceptance-centered-work-loop
- **Discovery:** none
- **Contract:** `contracts/delivery/` (planned canonical delivery-contract bundle)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Protected semantic-policy contract.** `Contract`, `Scope and Non-goals`,
> `Durable Outputs`, `Agent Rules`, `Testing Strategy`, `Acceptance Criteria`,
> `Terminal Intent`, and `Accepted Risk` are approval-bound or explicitly
> review-authorized. A change follows its owning amendment, review, or risk
> decision. `Outcome`, `What Changes`, `Follow-ons`, and `Assumptions` are
> working material that may be corrected without changing accepted authority.

## Outcome

Platform Core maintainers can call versioned acceptance services that reconstruct scope and completion from approved criteria and admissible evidence while the current work-loop engine remains authoritative. Success is parity with current approved records, legacy delivery subjects, and verdicts, plus fail-closed recovery, confinement, capability, control-plane, and content-safety conformance across supported adapters.

## What Changes

- Accepted property, approval, evidence, security, and content-safety contracts gain one canonical source under `contracts/delivery/`.
- A pure reviewed-execution-envelope projector fingerprints current references to separately owned approvals for criteria and evidence policy, scope/non-goals, authority/security decisions, public contracts, durable outputs, and accepted risk without granting any of that authority itself.
- The current approved spec/plan pair imports atomically as one authoritative spec-policy decision plus one non-authoritative initial-plan review record bound to the derived envelope and authorized terminal intent; its plan digest is audit evidence, not a continuing task lock.
- Legacy worktree state projects to a runtime-neutral delivery subject without admitting ambient files or delivery-control records.
- Evidence enters through checksummed transactions and produces a derived criterion-level acceptance verdict.
- Filesystem, process, capability, containment, audit, and control-plane denial become shared infrastructure primitives.
- The current work-loop engine can call the new services in shadow mode without transferring procedure or completion authority.

## Scope and Non-goals

This slice owns the canonical delivery contracts, pure reviewed-envelope
projection, policy-only approval import, initial plan-review record,
protected-change classification, legacy subject projection, acceptance
evaluation and evidence storage, shared security and content-safety primitives,
and compatibility calls needed to prove parity.

It does not implement mutable task reprojection or cancellation, transfer
current engine or cohort authority, enable a target authority cutover, add
parallel execution or protected-ref product authority, start a later delivery
slice, or introduce an external service, database, or mandatory runtime.
Operational task reprojection and cancellation belong to Slice 4.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | The slice introduces portable delivery records consumed by package and pack code. | `contracts/delivery/`, `contracts/README.md`, `contracts/REGISTRY.md` | `agentbundle` contract maintainers | Schema validation, source-to-projection parity, compatibility fixtures, and backward spec pointers | Every shipped record has one canonical schema, registered ownership, and matching declared projections. |
| Current architecture | The callable service boundary changes the system's current component and authority map. | `ARCHITECTURE.md`, `docs/architecture/loop-infrastructure.md`, `docs/architecture/loop-contract.md`, `docs/architecture/acceptance-centered-work-loop.md`, `docs/architecture/work-loop-authority-migration.md`, `docs/architecture/work-loop-acceptance-evidence.md`, `docs/architecture/runtime-security-primitives.md`, and `docs/architecture/delivery-content-safety.md` | Platform Core | Architecture review plus links to contracts, implementation, and conformance suites | The documents describe the callable shadow services, retain the current engine's authority, and preserve the reversal and governance gates. |
| Authority migration | The implementation must not imply that code deployment supersedes accepted workflow decisions. | `docs/architecture/work-loop-authority-migration.md` | Architecture-governance owner | Missing-governance refusal and reverse-reader tests | No existing authority is retired, and every future cutover still requires its named accepted governance record. |
| Maintainer procedure | Maintainers need one current route to parity, recovery, and reversal checks; adopters receive no new invocation in this slice. | `docs/architecture/loop-infrastructure.md` and implementation-owned test commands | Core and `agentbundle` maintainers | Commands exercise import, rehydration, reversal, and cross-adapter conformance | A maintainer can run the documented checks without reading this frozen delivery record. |
| Release history | Package, Core pack, and architect pack behavior changes ship through their existing release owners; the architect pack releases because it carries a byte-identical `file_safety.py` copy. | `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/pyproject.toml`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `packs/architect/pack.toml`, `packs/architect/.claude-plugin/plugin.json`, and `docs/product/changelog.md` | Package, Core pack, and architect pack release maintainers | Version-parity checks, build-self output, package tests, pack evals, and an outcome-led changelog entry | Released package and pack versions contain matching contracts and implementations, and the changelog names the maintainer-visible result. |

## Agent Rules

The three-tier guard keeps implementation inside this slice.

### Always do

- Keep the current engine, cohort state, and approved digest pins authoritative while the new services run in shadow or compatibility mode.
- Reuse the repository's canonical contract hashing and `agentbundle.catalogue_tooling.file_safety` controls instead of duplicating either algorithm.
- Put portable record fields and identities in `contracts/delivery/`; keep policy in the Core skill and reusable security mechanics in package infrastructure.
- Derive the reviewed execution envelope only from current references to each owning approval; treat its fingerprint as a summary for comparison, never as a new grant of authority.
- Fail closed before any semantic append, process launch, filesystem mutation, or control-plane effect whose identity, authority, bounds, or content policy is uncertain.
- Preserve accepted criteria, approvals, evidence, and integrated history across cache deletion, restart, and reversal.
- Classify task, sequence, decomposition, test-shape, and local-method changes as outside approval authority while the reviewed envelope and terminal intent remain unchanged, without implementing the Slice 4 task projector.

### Ask first

- Change legacy canonicalization, approved-subject scope, or the meaning of an imported current record.
- Change accepted criteria or evidence policy, scope or non-goals, an authority or security boundary, a public contract, a durable output, or accepted risk; route the change through its owning amendment or risk decision before execution.
- Change terminal intent; obtain a fresh initial plan review for the new intent before a later-slice task projector may resume.
- Widen a capability's actions, roots, product reads, network access, child-process authority, resource limits, or containment trust class.
- Add a delivery record, writer, or content profile not owned by the architecture contract set.
- Select a cutover, retire an existing writer or reader, or treat a target record as authoritative; that also requires the named accepted governance record.

### Never do

- Store a task, phase, cohort, gate, retry, journal, or cached verdict as authority for accepted scope or completion.
- Introduce another workflow engine, transfer procedure ownership, enable protected-ref product authority, or enable new parallel execution in this slice.
- Publish only one side of the imported spec-policy approval and initial-plan review pair, or expose part of an evidence transaction.
- Treat an initial plan review, plan digest, task projection, task sequence, decomposition, or local method as acceptance authority or as a reason to require later plan approval.
- Let a reviewed-envelope fingerprint replace, merge, or widen the separate approvals it references.
- Let an untrusted adapter or worker write `.git`, protected integration refs, delivery-control records, approvals, evidence, reports, or dispositions directly.
- Persist rejected credential or personal-data bytes, excerpts, or content-derived hashes, or treat stored free text as instructions, tool calls, approvals, paths, or authority.

## Testing Strategy

- **Pure deterministic logic (AC-0003, AC-0007, AC-0009, AC-0010, AC-0014, AC-0015, AC-0018)** uses TDD because property projection, satisfaction, freshness, capability intersection, content-safety decisions, and the fixed evaluator benchmark each have a compact input/output oracle.
- **Transactional and operating-system integration (AC-0001, AC-0002, AC-0008, AC-0011, AC-0012, AC-0017, AC-0019, AC-0020, AC-0021)** uses TDD through integration tests because canonicalization, approval import, evidence transactions, reverse reading, authorized semantic append, security auditing, file mutation, process control, restart recovery, and cold rehydration cross storage or host boundaries.
- **Pure authority classification (AC-0004)** uses TDD because the Slice 1 boundary is a deterministic decision over the reviewed envelope, terminal intent, and proposed change; it does not execute, cancel, or persist Slice 4 task projections.
- **Cross-boundary conformance (AC-0005, AC-0006, AC-0013, AC-0016)** uses goal-based end-to-end suites because unit tests cannot prove legacy subject parity, current-engine authority preservation, adapter refusal, or control-plane forgery resistance across compatibility boundaries.
- **Release and projection closure** uses goal-based package, Core pack, schema, build, and status gates. This slice has no visual or manual-QA behavior.

## Acceptance Criteria

- [ ] **AC-0001.** For every mechanically projectable approved artifact in the frozen legacy corpus, the importer computes the same canonical spec and plan digests as the current approval implementation; the corpus includes status-token, checkbox, line-ending, and trailing-space normalization cases.
- [ ] **AC-0002.** Given a matching current approval pin and one unambiguous current reviewed-envelope fingerprint, one import exposes exactly one spec-policy approval and one `initial-plan-review.v1` record bound to that envelope and the authorized terminal intent; the imported plan digest is audit provenance only, and injected interruption at every append boundary, a digest or envelope mismatch, an ambiguous criterion, missing authority, or either invalid record exposes neither.
- [ ] **AC-0003.** `reviewed-execution-envelope.v1` deterministically fingerprints ordered current references to the separately owned approvals for criteria and evidence policy, scope and non-goals, authority and security decisions, public contracts, durable outputs, and accepted risk; a missing, ambiguous, stale, or conflicting reference refuses derivation, and the envelope grants, replaces, or widens none of the referenced authority.
- [ ] **AC-0004.** The initial plan review records that strategy, safety constraints, dependencies, and scope alignment were reviewed against one AC-0003 envelope and explicitly authorizes terminal intent, without giving tasks, sequence, decomposition, test shape, or local methods continuing authority; the classifier marks changes limited to those non-authoritative fields as not requiring human approval while envelope and intent stay fixed, marks a changed envelope or intent as requiring its owner plus fresh initial review, and performs no task reprojection, cancellation, or dispatch.
- [ ] **AC-0005.** For the same acknowledged product tree, the legacy subject provider and the runtime-neutral projector emit identical canonical manifests, product fingerprints, exclusions, spec identity, and plan provenance.
- [ ] **AC-0006.** An ambient, ignored, excluded, unreadable, link-like, non-regular, out-of-root, or unacknowledged added path cannot enter a delivery subject; an unresolved bound or source drift emits no partial subject.
- [ ] **AC-0007.** The same approved properties and admissible evidence produce the same `unapproved`, `contradicted`, `supported`, or `insufficient` verdict under the sequential reference runtime and every adapter declared supported; deleting task, phase, cohort, gate, retry, cached-verdict, or mechanical-journal state cannot change that verdict.
- [ ] **AC-0008.** A checksummed semantic evidence transaction exposes all ordered embedded records or none; restart truncates only an incomplete final frame, rejects checksum or reference corruption, rebuilds disposable indexes, and reproduces the pre-interruption verdict from the complete prefix.
- [ ] **AC-0009.** Exact-subject evidence becomes stale when its acceptance fingerprint changes; path-set evidence remains current only while every declared claim, policy, producer, complete-read, command, toolchain, configuration, environment, byte, and lineage fingerprint matches, and a missing or incomplete attestor falls back to exact-subject freshness.
- [ ] **AC-0010.** Every child capability is the intersection of its parent grant and the requested operation; omitted network and child-process fields deny all, and an unsupported containment or read-coverage claim refuses before launch or effect.
- [ ] **AC-0011.** Every file read or mutation derived from input stays within its declared canonical root and refuses absolute or traversing paths, links, reparse points, non-regular or multiply linked files, identity changes, and exceeded bounds; a refused or interrupted mutation leaves the prior file intact and records no success.
- [ ] **AC-0012.** Every managed process uses an identity-pinned absolute executable, fixed argument vector, confined working directory, allowlisted environment, explicit bounded stdin, full process-tree timeout, bounded output, and redaction; any validation or runtime breach terminates the tree and records no durable success or unredacted output.
- [ ] **AC-0013.** Untrusted executable or adapter code runs only under verified host containment and cannot directly write Git metadata, protected refs, product state outside its grant, or any delivery-control path; the cross-adapter forgery corpus observes zero bypass writes.
- [ ] **AC-0014.** Every durable semantic writer and replay boundary introduced by this slice, including `initial-plan-review.v1`, appears in the [`delivery-content-safety.md` §4](../../architecture/delivery-content-safety.md#4-contracts-and-invariants) profile matrix before use; each uses its assigned named profile and returns the same decision for the shared credential, personal-data, encoding, executable-structure, and size corpus, while a missing or unknown profile refuses append and replay without persisting payload bytes.
- [ ] **AC-0015.** A rejected credential or personal datum leaves no persisted payload, excerpt, or content-derived hash, while accepted free text remains typed inert data that cannot request tools, grant authority, alter procedure, or supply an executable path.
- [ ] **AC-0016.** The current engine can call the new services without changing its public invocation, transition authority, cohort writer, legacy plan pin, or completion decision; target records remain non-authoritative until a separately accepted governance record permits a cutover, and the target never reinterprets that legacy pin as continuing plan authority.
- [ ] **AC-0017.** During dual-read, the reverse reader reconstructs the original legacy approved spec/plan pair; after cutover, an authority-switch decision may snapshot the current within-envelope plan solely for legacy compatibility, without deleting newer semantic facts or granting the snapshot target authority, and any lossy or boundary-crossing projection refuses.
- [ ] **AC-0018.** On the CI reference worker, evaluating exactly 1,000 approved criteria against 100,000 admitted evidence records completes at p95 within 2 seconds, measured from evaluator invocation to complete verdict return by the committed benchmark harness.
- [ ] **AC-0019.** On the CI reference worker, cold rehydration of exactly 1,000 approved criteria and 100,000 admitted evidence records completes within 10 seconds, measured from a fresh process start to complete verdict return by the committed benchmark harness.
- [ ] **AC-0020.** Before any approval, initial-plan review, evidence receipt, evidence supersession, or security event becomes durably visible, the append boundary verifies the named writer or producer against its capability and record scope; missing, expired, mismatched, or out-of-scope authority exposes no partial record, and retry cannot weaken that refusal.
- [ ] **AC-0021.** When the audit sink is available, every security-sensitive allow and policy denial emits a durable security event with a stable reason code and redacted, non-payload metadata before success or refusal is acknowledged; when the sink is unavailable, the operation fails closed with a stable redacted denial code, no effect success, no protected request, content, credential, or personal datum persistence, and no claim that a security event was durably stored.

## Follow-ons

none — the parent brief owns later delivery slices, and this spec does not create or start them.

## Terminal Intent

`code` — after approval, implement the Slice 1 boundary in Scope and
Non-goals until every Acceptance Criterion is satisfied.

## Accepted Risk

none

## Assumptions

none
