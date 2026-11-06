# Subsystem Design — Product result integration

**Decision:** Every execution result passes through one crash-safe,
runtime-neutral integration boundary before it can change the canonical product
tree or support acceptance. The sequential boundary, a protected product ref,
ships, and so does the concurrent path: a pinned three-way apply that lands results
in the sequential order. That path is off by default and no shipped host can run it
(§ 1a, *Known limit*).
**Author(s):** Platform Core and `agentbundle` maintainers
**Status:** Implemented, except the Product addition profile, which is planned
**Last updated:** 2026-11-06
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

## 1a. What ships and what stays planned

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

**Shipped: the concurrent path** ([ADR-0156](../adr/0156-work-loop-concurrency-needs-attested-read-coverage.md);
the [`verified-infrastructure-parallelism`](../specs/verified-infrastructure-parallelism/spec.md)
spec owns its contract). It runs only when `supervisor-policy.json` sets `concurrency` to
`enforced-allowlist` or `complete-trace`; the shipped value is `sequential`. Concurrent results
use the run's existing product ref, not a second one.

- A `run-concurrent` request names up to `max_concurrent_attempts` tasks whose declared read
  and write sets do not meet. Each attempt runs in its own directory outside Git, with its own
  pinned launcher, and its attested read and write sets decide what its result may land on.
- Ingestion turns an attempt directory into a Git tree under path-count and byte caps (100,000
  paths, 10 GiB) and checks names and link targets before any object exists.
- A finished result is held, recorded by its tree and the digest of its access line, until the
  tasks before it have landed. Results land one at a time under one `integration.lock`, in the
  order the sequential floor would have issued the tasks, whatever order they finished in.
- The three-tree apply is `git merge-tree --write-tree` with its merge base pinned to the
  result's source commit. A refusal writes `integration-conflict.v1`, leaves both refs alone,
  and projects the task again from the new tip. A landing writes `result-integration.v1`.
- A failure cancels only the running siblings whose sets meet the failed task's. The task is
  projected again up to `reprojection_bound` times and then runs on the floor.
- Every verb that integrates (`run-concurrent`, `report` for a floor result, and `next`) lands
  each held result that is next, and a killed run converges on the next verb.
- The supervisor's own projection of `HEAD` is the worktree materializer: after each landing
  it brings the working tree and index to the product ref before any floor request issues.

**Planned:** the Product addition profile, which would classify every added path of a result
before a Git object exists. Ingestion today applies the floor's ignore rules and the closed
name, link, special-file, and cap checks, and no more.

**Known limit.** No shipped host can attest isolation or reads, so every adopter runs on the
sequential floor. The concurrent path is proven only against a test-only fixture launcher,
which enforces nothing; the permutation and conflict corpus drives it, and it is never
installed.

## 2. Structural Model

Sections 2–8 describe the concurrent path as built. The Product addition profile is the one
planned element (§ 1a).

| Element | Type | Responsibility | State |
| --- | --- | --- | --- |
| Result validator | Pure component (`ingest_attempt_directory`) | Ingest an attempt directory into a tree, under caps and link rules | Stateless |
| Change-set projector | Pure component | Derive normalized source-base-to-result changes | Stateless |
| Integration coordinator | Application service | Hold results, then serialize compare-and-swap integration in floor order | `integration.lock`, `held/` |
| Canonical product ref | Durable semantic store | Point to the current immutable integration commit and product tree | Git commits and protected ref |
| Worktree materializer | Mechanical projector (the supervisor's projection of `HEAD`) | Make repository files match the canonical product tree | Disposable checkout state |
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
   writes the attempt's `execution-result.v1` itself, carrying the tree it ingested
   and the digest of the access line.
2. Before creating any Git object, ingestion walks the attempt directory without
   following links and refuses a path or byte count over the caps, a special file,
   a hard link, a Git control name, an unsafe link target, and a protected path.
   The Product addition profile (planned) does not yet classify added paths.
3. A finished result is held. Results integrate one at a time, in the order the
   sequential floor would have issued their tasks; a finished later result waits.
   Under `integration.lock` the coordinator reads the tip once. A result whose
   source commit is the tip lands as it is. Any other result needs a complete
   access attestation (enforced allowlisting or tracing) and is refused as
   `incomplete-attestation` without one. Every attested read and write is checked
   against the paths changed from the source to the tip, both ends of a rename and
   each parent directory included; a meeting is refused as `meets`. Only then may
   the three-tree apply create objects.
4. A clean application writes an immutable tree and an integration commit that
   carries the attempt's trailer, then compare-and-swaps `HEAD` and the product ref
   together from the observed tip. A ref that moved first is `cas-lost`.
5. The coordinator records `result-integration.v1` and brings the working tree and
   index to the product ref. Replay finds the landed operation by its commit
   trailer after a crash.

**Conflict and recovery sequence**

1. A content conflict, a `merge.*` setting or merge attribute, an attested read
   or write that meets a change, a changed link target, stale authority, or a
   failed compare-and-swap leaves both refs unchanged and writes a bounded
   `integration-conflict.v1`.
2. The scheduler projects the failed task again from the new tip and cancels only
   running siblings whose declared sets meet its own. Other siblings continue.
3. A cancelled attempt's launcher gets `abort` and its process group is ended and
   confirmed within 10 seconds; its late result is never admitted. An end that
   cannot be confirmed sends the task to the floor and leaves the attempt directory
   behind. A task projected again counts toward `reprojection_bound`, and at the
   bound it runs on the floor.
4. A crash before the ref update leaves unreachable temporary objects. After it,
   the next supervisor verb finds the operation's commit trailer and records the
   landing without a second commit. A held result that survives a crash stays held.
5. Partial worktree materialization is discarded and rebuilt from the canonical
   ref. It never changes acceptance or the next integration base.
6. A controller replan or stub-fence revision is admitted only while no attempt is
   open. It discards every held result, and each task is projected again without
   counting toward the bound.

## 4. Contracts and Invariants

| Contract | Producer → consumer | Identity | Compatibility and change authority | Failure semantics | Invariant |
| --- | --- | --- | --- | --- | --- |
| `execution-result.v1` | Runtime adapter, or the supervisor for a concurrent attempt → result validator | Request, run, kind; for a concurrent attempt the ingested result tree and the access line's sha256 | Canonical schema owns fields; readers deploy first; unknown majors refuse | Partial, superseded, unauthorized, or unverifiable results remain isolated | Unproven completeness requires serialization and exact source |
| `result-integration.v1` | Integration coordinator → scheduler, subject projector, and evidence port | Operation key, attempt-authority fingerprint, access-attestation line digest, source and observed target commits, result commit and tree, algorithm version | Core and `agentbundle` owners approve merge semantics; algorithm changes require a new major; unknown majors refuse | Canceled authority, stale reads/writes, conflict, CAS loss, or limits change no ref | In-lock intervening-change validation precedes object creation and CAS |
| `integration-conflict.v1` | Coordinator → scheduler and operator | Operation, attempt, source and observed target commits, reason, at most 1,000 conflicting repository paths with the total count and a truncation flag | Additive diagnostics are allowed; path disclosure follows repository classification | Conflict returns the task to projection and invalidates isolated observations | No partial application or silent overwrite |

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
| Result and conflict records | Immutable operation outcome in the run store (`integrations/`, `conflicts/`) | Emitted, consumed, retained through closeout | Stable operation key deduplicates recovery |
| Held results | A record in `held/` and a ref `refs/agentbundle/delivery/<run>/<token>/held/<attempt>` naming the tree | Written when an attempt finishes, removed when it lands, is refused, or is discarded | Part of every later attempt's manifest, so a worker's change to either is `attempt-residue` |

## 6. Deployment and Operations

| Unit | Runs as | Scaling | Observability |
| --- | --- | --- | --- |
| Validator and coordinator | Local harness library | At most 100,000 paths or 10 GiB per result; refuse larger results. A conflict record lists at most 1,000 paths of at most 1,024 bytes each | Operation, source, target, result, duration, refusal |
| Git object and ref store | Existing repository | One protected ref and commit chain per active delivery | Ref age, commit count, unreachable temporary bytes |
| Materializer | Workspace adapter | One projection per canonical-ref advance | Projection lag and repair count |

## 7. Quality Scenarios and Verification

| Stimulus | Mechanism and response | Target | Verification |
| --- | --- | --- | --- |
| Two siblings edit the same line | Versioned three-tree apply reports conflict and keeps the ref unchanged | Zero silent overwrites | Conflict schedule in the permutation corpus |
| Two siblings edit independent paths | Serialized CAS integrations in sequential-floor order preserve both changes | Same final tree and verdict as the sequential run in every completion order | Permutation corpus: three completion orders per concurrent mode |
| Process crashes at any integration boundary | Protected ref exposes old or new commit; operation-key replay converges | Zero partial semantic trees or duplicate commits | Kill-point suite at each integration write |
| Canceled sibling returns late | Attempt authority rejects its result and observations | Zero late-result tree or evidence admission | Failure-handling suite |
| B validates, then A commits before B locks | In-lock intervening-change check against the one tip read refuses B when its sets meet A's changes | Zero stale results pass the race window | Ref-move suite in the integration tests |
| A changes input read by B while B writes another path | Read-set intersection refuses and reprojects B | Same result as serial A-then-B execution | Read-after-write schedule in the permutation corpus, and its must-red mutant |
| B reads an undeclared path | Allowlist denies, tracer adds the read, or result becomes incomplete and exact-source only | Zero false-complete parallel results | Access-attestation suite |
| Crash follows A's CAS but precedes its integration record | The next verb finds A's commit trailer and records the landing; B's in-lock intervening-change check refuses | Zero stale sibling or duplicate commits | Kill-point suite after the compare-and-swap |
| Result exceeds path or byte cap | Validator refuses before temporary apply | Refusal above 100,000 paths or 10 GiB | Ingestion cap tests |
| Worker attempts to update Git metadata or the protected ref | Capability and host containment deny the write | Zero bypassed integration commits | Attempt-residue suite |
| Result contains ambient, ignored-secret, denied, or unprovenanced additions | Validator refuses before Git object creation | Zero manifest, object, commit, or ref writes | Planned with the Product addition profile |

## 8. Implementation Mapping

| Element | Source owner | Build unit | Verification |
| --- | --- | --- | --- |
| Held results, ordered integration, and the apply | `work-loop/scripts/_supervisor_integration.py`; schemas in `contracts/delivery/` | Core pack | Integration, schema-parity, and record suites |
| Admission, attempt directories, and ingestion | `work-loop/scripts/_supervisor_concurrency.py` and `_confined_entries.py` | Core pack | Admission and ingestion tests |
| Launcher boundary and attestation checks | `work-loop/scripts/_supervisor_launcher.py` | Core pack | Launcher tests against the fixture launcher |
| The `run-concurrent` verb, cancellation, and recovery | `work-loop/scripts/_supervisor_concurrent.py` | Core pack | Failure-handling and kill-point tests |
| Protected-ref coordinator | `work-loop/scripts/_supervisor_commit.py` | Core pack | CAS, merge, crash, and replay tests |
| Worktree materializer | The supervisor's existing projection of `HEAD` (§ 1a) | Core pack | Dirty and interrupted projection tests |
| Permutation and conflict corpus | `packs/core/tests/skills/work-loop/permutation_corpus.py` | Core pack tests | Permutation suite and `tests/roster/test_concurrency_records.py` |
| Integration policy | `packs/core/.apm/skills/work-loop/` | Core pack | Skill evals |

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
the setting. The permutation and conflict corpus runs four schedules under each concurrent mode
in every completion order and compares each run's product tree and criterion outcomes with the
sequential run's.

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
| The concurrent path and its contracts | Core pack and `agentbundle` maintainers |
