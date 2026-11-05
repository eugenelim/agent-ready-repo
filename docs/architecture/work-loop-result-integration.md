# Subsystem Design — Product result integration

**Decision:** Every execution result passes through one crash-safe,
runtime-neutral integration boundary before it can change the canonical product
tree or support acceptance. The sequential boundary, a protected product ref,
ships; the parallel three-tree apply is Slice 7.
**Author(s):** Platform Core and `agentbundle` maintainers
**Status:** Partly implemented: § 1a ships; §§ 2–8 are the planned Slice 7 design
**Last updated:** 2026-11-05
**Reviewers:** Core pack and `agentbundle` maintainers

## 1. Scope and Context

| In scope | Out of scope | Why |
| --- | --- | --- |
| Validate and apply sequential or isolated result trees | Task scheduling | Scheduler decides when work runs; integration decides what enters the product |
| Conflict, cancellation, crash recovery, and canonical-tree ownership | Acceptance evaluation | Only integrated observations may reach the evidence port |
| Worktree materialization from the canonical tree | User-interface presentation | Files are a projection of the durable Git result |

**Goals**

- Parallel order cannot silently overwrite a sibling result.
- A crash exposes either the old or new canonical product tree, never a partial
  semantic tree.
- No evidence from an isolated result is admissible before integration.

**Non-goals**

- Automatically resolving semantic merge conflicts or choosing task priority.

## 1a. What ships and what Slice 7 adds

**Shipped: the sequential result boundary** ([ADR-0154](../adr/0154-work-loop-product-result-is-a-protected-ref.md)),
for full-mode `code` runs.

- Each run has its own product ref, `refs/agentbundle/delivery/<run-id>/<token>/product`. The
  supervisor moves `HEAD` and that ref together in one `git update-ref --stdin`
  transaction per step, so both name the same commit and `HEAD` stays on its branch.
- A result integrates only while the ref still names the commit its request was issued
  from. Otherwise `report` refuses `integration-conflict` and keeps the worker's files.
- The run store records the ref's name and value, and the trust rule and refusals are in the
  [execution-supervisor page](work-loop-execution-supervisor.md#product-ref). A reftable repository refuses `unsupported-ref-storage`.
- After a reset back to an earlier supervisor commit, the supervisor projects `HEAD` and the working tree forward through its
  own commits, or refuses `projection-blocked` when a file matches neither version.
- History the supervisor did not make enters the ref only through an owner-authorized
  `reanchor` step. An answer that would change a `delivery/` file refuses `adoption-refused`.
- Under `result_authority` `protected-product-ref` the delivery subject reads this ref.
  The execution-supervisor page's [Product ref](work-loop-execution-supervisor.md#product-ref)
  section owns the classification table, kill points, and decision.

**Planned, Slice 7:** the three-tree apply, `result-integration.v1` and
`integration-conflict.v1`, read and write sets, sibling cancellation, the Product addition
profile, path and byte caps, and the worktree materializer. Sections 2–8 below describe that
design and are **STATUS: PLANNED**. [ADR-0156](../adr/0156-work-loop-concurrency-needs-attested-read-coverage.md)
admits it, and the [`verified-infrastructure-parallelism`](../specs/verified-infrastructure-parallelism/spec.md)
spec owns its contract. Concurrent results use the run's existing product ref, not a second one.

**Known limit.** No shipped host can attest isolation or reads, so every adopter runs on the
sequential floor. The concurrent path is proven only against a test-only fixture launcher.

## 2. Structural Model

**STATUS: PLANNED (Slice 7).** Sections 2–8 describe the parallel design; § 1a is what ships.

| Element | Type | Responsibility | State |
| --- | --- | --- | --- |
| Result validator | Pure component | Validate subject, tree objects, authority, and change-set identity | Stateless |
| Change-set projector | Pure component | Derive normalized source-base-to-result changes | Stateless |
| Integration coordinator | Application service | Serialize compare-and-swap integration and notify the scheduler | In-flight lock |
| Canonical product ref | Durable semantic store | Point to the current immutable integration commit and product tree | Git commits and protected ref |
| Worktree materializer | Mechanical projector | Make repository files match the canonical product tree | Disposable checkout state |
| Conflict reporter | Port | Apply the shared [integration-diagnostic content profile](delivery-content-safety.md) to conflict paths and guidance | Result record |

The protected ref is the run's product ref (§ 1a). Each
successful operation creates a Git commit whose tree contains every product
path, whose parent is the prior canonical commit, and whose metadata carries
the stable integration operation key. The approval lineage retains the
starting commit or equivalent immutable tree manifest.

Task capabilities deny
direct `.git` and protected-ref writes; only the integration port holds them. The
shipped boundary detects a worker's change to the ref and refuses the result instead of
denying the write (§ 1a).

## 3. Runtime Model

**Normal sequence**

1. The supervisor spawns the owner-pinned launcher for each admitted attempt,
   verifies its `containment-attestation.v1` before releasing the worker, and
   reads `access-attestation.v1` from the same pipe when the worker ends. It
   computes the attempt's `execution-result.v1` from the attempt's own tree.
2. Before creating any Git object, the validator reconstructs the change set,
   applies the Product addition profile to every added path, and rejects
   ignored, denied, unprovenanced, mismatched, oversized, or unauthorized data.
3. Results integrate one at a time, in the order the sequential floor would
   have issued their tasks; a finished later result waits. Under the
   integration lock the coordinator reads the tip once and derives the paths
   changed since the result's source. Complete coverage means enforced
   allowlisting or tracing; a read or write that meets a changed path refuses
   and reprojects. Every other result requires exact source equality. Only
   then may the three-tree apply create objects.
4. A clean application writes an immutable tree and integration commit, then
   compare-and-swaps the protected ref from the observed target commit.
5. The coordinator emits `result-integration.v1` and materializes the
   worktree. Replay finds the landed operation by its commit trailer after a
   crash. Only the receipt admits observations. A result without a complete
   access attestation integrates only on exact source equality.

**Conflict and recovery sequence**

1. A content conflict, stale authority, or failed compare-and-swap leaves the
   canonical ref unchanged and emits a bounded conflict result.
2. The scheduler cancels overlapping siblings and reprojects the failed task
   from the new canonical tree. Non-overlapping siblings may continue.
3. A late result from a canceled attempt is never admitted. The task
   reprojects onto a fresh tree once the attempt's end is confirmed.
4. A crash before ref update leaves unreachable temporary objects. After ref
   update, retry finds the operation key, returns the same receipt, and re-emits
   sibling invalidation before new scheduling.
5. Partial worktree materialization is discarded and rebuilt from the
   canonical ref. It never changes acceptance or the next integration base.

## 4. Contracts and Invariants

| Contract | Producer → consumer | Identity | Compatibility and change authority | Failure semantics | Invariant |
| --- | --- | --- | --- | --- | --- |
| `execution-result.v1` | Runtime adapter → result validator | Subject, task-projection revision, task, attempt, operation, source/result trees, change digest | Canonical schema owns fields; readers deploy first; unknown majors refuse | Partial, superseded, unauthorized, or unverifiable results remain isolated | Unproven completeness requires serialization and exact source |
| `result-integration.v1` | Integration coordinator → scheduler, subject projector, and evidence port | Operation key, attempt-authority fingerprint, access-attestation line digest, source and observed target commits, result commit and tree, algorithm version | Core and `agentbundle` owners approve merge semantics; algorithm changes require a new major; unknown majors refuse | Canceled authority, stale reads/writes, conflict, CAS loss, or limits change no ref | In-lock intervening-change validation precedes object creation and CAS |
| `integration-conflict.v1` | Coordinator → scheduler and operator | Operation, attempt, target commit, bounded conflicting paths | Additive diagnostics are allowed; path disclosure follows repository classification | Conflict returns the task to projection and invalidates isolated observations | No partial application or silent overwrite |

The three-tree algorithm is a declared Git merge implementation and version,
not host-default behavior. The protected ref is the semantic commit point;
the index, temporary objects, locks, and checked-out files are mechanical.
Every evidence receipt cites a successful integration operation and result tree
unless its observation is explicitly pre-execution evidence.

## 5. Data and State

| Element | State it owns | Lifecycle | Consistency requirement |
| --- | --- | --- | --- |
| Canonical product ref | Integration commits and current ref | Initialized from approval base, advanced by CAS, retained in Git history | One current ref per delivery lineage |
| Integration coordinator | Lock and temporary index | Acquired, committed or discarded | Loss cannot create a semantic partial write |
| Worktree projection | Checked-out product files | Materialized, dirty, repaired | Never authoritative over the protected ref |
| Result and conflict records | Immutable operation outcome | Emitted, consumed, retained through closeout | Stable operation key deduplicates recovery |

## 6. Deployment and Operations

| Unit | Runs as | Scaling | Observability |
| --- | --- | --- | --- |
| Validator and coordinator | Local harness library | At most 100,000 changed paths or 10 GiB per result; refuse larger results | Operation, source, target, result, duration, refusal |
| Git object and ref store | Existing repository | One protected ref and commit chain per active delivery | Ref age, commit count, unreachable temporary bytes |
| Materializer | Workspace adapter | One projection per canonical-ref advance | Projection lag and repair count |

## 7. Quality Scenarios and Verification

| Stimulus | Mechanism and response | Target | Verification |
| --- | --- | --- | --- |
| Two siblings edit the same line | Versioned three-tree apply reports conflict and keeps the ref unchanged | Zero silent overwrites | Conflicting-parallel fixture |
| Two siblings edit independent paths | Serialized CAS integrations in sequential-floor order preserve both changes | Same final tree and verdict as the sequential run in every completion order | Permutation fixture |
| Process crashes at any integration boundary | Protected ref exposes old or new commit; operation-key replay converges | Zero partial semantic trees or duplicate commits | Crash injection before object write, before CAS, after CAS, and during materialization |
| Canceled sibling returns late | Attempt authority rejects its result and observations | Zero late-result tree or evidence admission | Cancellation-race fixture |
| B validates, then A commits and cancels B before B locks | In-lock authority revalidation refuses B | Zero canceled results pass the race window | Ordered cancellation-before-lock fixture |
| A changes input read by B while B writes another path | Read-set intersection cancels and reprojects B | Same result as serial A-then-B execution | Read-after-write fixture; unknown read set must serialize |
| B reads an undeclared path | Allowlist denies, tracer adds the read, or result becomes incomplete and exact-source only | Zero false-complete parallel results | Cross-adapter undeclared-read fixture |
| Crash follows A's CAS but precedes sibling cancellation | B's in-lock intervening-change check refuses; A replay re-emits cancellation | Zero stale sibling commits | Crash-after-CAS-before-cancellation read-after-write fixture |
| Result exceeds path or byte cap | Validator refuses before temporary apply | Refusal above 100,000 paths or 10 GiB | Bound-edge stress fixture |
| Worker attempts to update Git metadata or the protected ref | Capability and host containment deny the write | Zero bypassed integration commits | Cross-adapter ref-forgery fixture |
| Result contains ambient, ignored-secret, denied, or unprovenanced additions | Validator refuses before Git object creation | Zero manifest, object, commit, or ref writes | Addition-admission negative corpus |

## 8. Implementation Mapping

| Element | Source owner | Build unit | Verification |
| --- | --- | --- | --- |
| Validator, projector, and contracts | Proposed `work-loop/scripts/_supervisor_integration.py`; schemas in `contracts/delivery/` | Core pack | Schema-parity, authority, and change-set tests |
| Launcher boundary and admission | Proposed `work-loop/scripts/_supervisor_concurrency.py` | Core pack | Admission, attestation-defect, and fixture-launcher tests |
| Protected-ref coordinator | `work-loop/scripts/_supervisor_commit.py` | Core pack | CAS, merge, crash, and replay tests |
| Worktree materializer | The supervisor's existing projection of `HEAD` (§ 1a) | Core pack | Dirty and interrupted projection tests |
| Integration policy | `packs/core/.apm/skills/work-loop/` | Core pack | Conflict and cancellation skill evals |

## 9. Decisions, Alternatives, and Risks

- **Decision:** A protected Git ref, not a mutable worktree, is the semantic
  commit point.
- **Alternative:** Let parallel workers push directly into one worktree.
  **Rejected because:** file writes can interleave without one atomic result.
- **Alternative:** Require one branch per task and merge through host defaults.
  **Rejected because:** merge behavior and base selection then vary by runtime.
- **Risk:** A clean text merge is semantically wrong. **Mitigation:** integrated
  output still requires fresh evidence and review.
- **Risk:** Protected ref and worktree diverge at 3 a.m. **Mitigation:** ref wins;
  materialization is observable and repeatable.
- **Risk:** Large results exhaust temporary storage. **Mitigation:** path and
  byte caps refuse before apply, and unreachable objects are pruned by policy.

## 10. Rollout, Migration, and Reversal

**Current state.** `result_authority` is `protected-product-ref`: acceptance reads the product
ref, and both refs are written under either setting.

The full crash corpus runs under the
shipped authority and a named sample under the other, and a test fails on any second read of
the setting. Parallel-permutation and conflict-parity conditions belong to Slice 7's design above.

**Reversal.** This is the one place the route is stated.

- **Adopters:** reinstall the prior Core release for new runs. A run in flight finishes on
  the release that started it or starts again.
- **Maintainers who hold the pack source:** release a Core patch that sets `result_authority`
  back to `legacy-worktree`. Runs started after it read `HEAD`; a run in flight crosses
  through `regenerate` and runs its gates and reviews once more, because the subject's
  lineage changes. No product change is lost, since both refs carry the same commits.
- A lineage names the authority only, so a run taken back to an authority it already
  used can match evidence recorded in that stretch. One crossing always starts the evidence
  over.

| Responsibility | Owner |
| --- | --- |
| Integration contract and the authority setting | Core pack maintainers |
| Rollback authorization (the reversal patch or reinstall) | Core pack release maintainers |
| Parallel cutover and its contracts (Slice 7) | `agentbundle` maintainers |
