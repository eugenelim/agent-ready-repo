# Subsystem Design — Work-loop authority migration

**Decision sought:** Move delivery authority from the current FSM, cohort,
approval pin, and parallelism decisions only through explicit compatibility and
governance cutovers; no implementation slice supersedes an accepted record by
implication.
**Author:** Platform Core
**Status:** Draft
**Last updated:** 2026-10-01
**Reviewers:** Core, `agentbundle`, and architecture-governance maintainers

## 1. Scope and Context

| In scope | Out of scope | Why |
| --- | --- | --- |
| Current and target authority for each work-loop concern | Rewriting frozen ADR bodies | A new accepted record, not implementation, changes authority |
| Compatibility, cutover, reversal, and baseline-document updates | Child contract fields | The owning subsystem designs define their schemas |
| Required superseding governance decisions | Assigning an RFC or ADR number | The repository decision workflow owns identifiers |

The current engine and cohort are not merely code to replace. Their transition
tables, writer rules, approval pins, and accepted decisions are authority until
a named gate and an accepted superseding record move that authority.

## 2. Authority and Records Migration

| Current authority | Target authority | Compatibility owner | Cutover and reversal | Required governance record |
| --- | --- | --- | --- | --- |
| `loop-engine.py` transition table and `engine-state.json` completion phase | Approved criteria, `semantic-evidence-transaction.v1`, review facts, and derived `acceptance-verdict.v1` | Slice-1 evaluator adapter dual-reads old events and new facts | Slice 1 requires unexplained-verdict parity and cache-deletion rehydration; reversal selects the old verdict path without deleting new facts | Accepted work-loop authority record explicitly replaces phase state as completion authority and requires updates to `ARCHITECTURE.md` and `loop-infrastructure.md` |
| ADR-0125 D1–D3 registered engine effects and `loop-cohort.py` as `state.json` writer of record | Supervisor scheduler, task projection, and repairable mechanical journal | Slice-4 legacy result and cohort adapters | Slice 4 requires command, schedule, backward-edge, and acknowledged-result parity; reversal relaunches the old engine and cohort writers | The same or a linked accepted record supersedes ADR-0125 D1–D3 and updates `loop-infrastructure.md` |
| Current whole-artifact `approve-plan` pin for canonical spec and plan digests | One spec-policy `approval-record.v1` plus one `initial-plan-review.v1` carrying terminal intent; the imported plan digest proves the reviewed baseline but grants no continuing authority to its task list | Slice-1 importer and slice-4 task projector/reverse reader | Both records become visible atomically or neither does; later in-envelope task changes need no approval; changing terminal intent requires explicit authorization; reversal requires an explicit downgrade approval for the current plan snapshot because the old engine still requires a lock | Work-loop authority record replaces whole-plan locking with initial review plus mutable task projection; [acceptance and evidence](work-loop-acceptance-evidence.md) owns canonicalization and protected-boundary parity |
| ADR-0061 D5 prohibition on parallel-wave orchestration and its deferred modes | Supervisor scheduling with sequential floor and capability-based parallel admission | Slice-7 scheduler and provider conformance suite | No concurrent dispatch before the superseding record is accepted; reversal selects sequential mode | Accepted record explicitly supersedes ADR-0061 D5 and names the newly admitted runtime modes |
| ADR-0005 D3 safe-category membership and D4 post-write `git merge-tree` file-disjointness gate | Enforced read allowlisting or complete tracing before admission, plus protected-ref integration and permutation proof | Slice-7 scheduler, security capability, and result-integration ports | Missing proof serializes; any parity failure disables parallel admission without changing semantic facts | Parallelism record explicitly supersedes ADR-0005 D3–D4 while preserving fail-closed admission and merge-conflict handling |
| `loop-parallelism.md` §§3–4 serialize-only prediction and planned `wave-decision` contract | Task-contract isolation hints plus the supervisor's non-authoritative scheduler decision | Slice-4 compatibility projector; slice-7 scheduler afterward | Prediction remains advisory and cannot grant parallel writes; optional Pi compatibility is not a prerequisite; slice 7 retires it only after conformance and governance gates pass | Parallelism record accepts, replaces, or retires the planned contract and records the reserved owner decision |
| `project-knowledge --producer-profile work-loop` reusable capture gates and close-time `work-item` seam | Stateless observation projection for reusable evidence/review facts; retained explicit `work-item` capture for specific blocked residue | Slice-3 projector and project-knowledge intake | Projection can be disabled without affecting delivery; retained work-item capture keeps its own validation and closeout owner | Baseline `knowledge-capture.md` is updated at slice 3; no ADR supersession is required unless its ownership changes |

“Required governance record” is a cutover prerequisite, not a placeholder
decision. The accepted artifact receives its identifier through `new-rfc` or
`new-adr`, cites the rows it supersedes, and names the first release allowed to
switch each writer. Until then, the current record remains authoritative even
when shadow services exist.

## 3. Data Transition Inventory

| Old artifact and schema | New artifact and schema | Trigger and dual rule | Partial residue and recovery | Rollback inside dual-read window | Cutover proof |
| --- | --- | --- | --- | --- | --- |
| `engine-state.json` schema v1 | Derived `acceptance-verdict.v1` | Every old transition also evaluates a shadow verdict; old writer remains authoritative | New semantic records remain valid; recomputation resumes from their fingerprints | Select old engine and ignore the shadow verdict | Zero unexplained verdict differences plus cache-deletion rehydration |
| `state.json` cohort schema v2 | Mutable `task-contract.v1` projections plus `mechanical-journal.v1` | The reviewed baseline first projects tasks; later working-plan or task changes inside the protected envelope reproject without approval while cohort mutation remains authoritative | Projections and journal may be discarded and rebuilt; semantic records deduplicate by identity | Delete new mechanical state and continue from cohort v2 | Schedule parity, task replacement, protected-boundary refusal, crash recovery, and delete-journal fixtures pass |
| Mutable worktree result | Protected product ref plus `result-integration.v1` | Each completed old-engine task snapshots and shadow-integrates its result | Temporary objects and partial checkout are discarded; protected ref remains old or new | Restore old worktree authority from the matching integration commit | Sequential, permutation, conflict, and crash parity pass |
| Canonical approved spec digest plus canonical approved plan digest | One spec-policy `approval-record.v1` plus one `initial-plan-review.v1` baseline record | Import both from the same current `approve-plan` pin after exact canonicalization parity; publish atomically; later plan/task revisions are Git and projection provenance, not approvals | Ambiguous criteria, digest mismatch, or either missing record publishes neither; retry recomputes both | During dual-read, restore the original approved pair; after cutover, downgrade requires explicit approval of the current plan snapshot and refuses a lossy projection | Every imported criterion maps to the approved spec digest; the initial review maps to the legacy plan digest; in-envelope task changes reproject without approval; status and checkbox normalization corpus passes |
| `.loop-run/events.jsonl` schema v1 plus `notes/verification-ledger.md` observations | `evidence-receipt.v1` and `evidence-supersession.v1` | Each verification observation emits old and new forms with one producer event ID | One-sided records reconcile by event ID; duplicates collapse by receipt identity | Ignore new receipts and continue the old gate path | Truth-table corpus and cross-adapter evidence parity pass |
| Raw reviewer output, `review-verdict.v1`, classifiers, and paired audits | `review-report.v1`, `finding-assessment.v1`, and `finding-disposition.v1` | Existing review adapters validate and write both forms before acknowledging | A validated new report remains but is ignored until its old counterpart reconciles | Read preserved raw and old verdict data through the old review path | Reviewer transport, reachability, privacy, and replacement-subject fixtures pass |
| Manual unknown-effect decisions in engine events | `effect-resolution.v1` | Each new manual decision dual-writes a stable operation-key record; unresolved historical effects stay blocked | A durable resolution remains valid if journal state is lost | Old engine consumes its event while the compatibility adapter reads the resolution | Three outcome fixtures pass after journal deletion |
| Reusable in-loop pattern, gotcha, and antipattern capture gates | Derived `knowledge-observation.v1`; no delivery-side store | Project eligible durable facts while old capture remains authoritative | Notifications may drop; project-knowledge pull rescans by stable source identity | Disable projection and retain old reusable-capture path | Drop-and-rescan, privacy, dedupe, quarantine, and revocation fixtures pass |
| Close-time `work-item` through `--producer-profile work-loop` | Retained explicit `work-item` capture contract | Closeout submits specific blocked residue through existing validation; projection never substitutes for it | Unavailable or refused capture leaves no record and cannot change delivery readiness | Keep the current producer seam | Existing reasoning-tier, schema, privacy, and closeout fixtures pass |

## 4. Runtime and Failure Model

**Normal sequence**

1. A slice deploys compatible readers and shadow writers while the current
   authority remains the sole decision source.
2. Parity and recovery fixtures bind old and new results to the same subject.
3. The required governance record is accepted before the cutover lease opens.
4. One cutover changes the reader and writer together and records the release,
   source and target fingerprints, reverse reader, and authority.
5. Baseline architecture documents are updated in that same reviewed change.

After target authority is active, replanning inside the reviewed envelope is
not a writer cutover. The supervisor records a new task projection, cancels
unintegrated attempts, and preserves integrated facts. A change to criteria or
evidence policy, scope or non-goals, security or authority, public contracts,
durable outputs, accepted risk, or review-authorized terminal intent is
protected and refuses until its owner acts.

**Failure and reversal sequence**

1. Missing governance, partial import, stale parity, an active run, or an
   unavailable reverse reader refuses cutover.
2. A crash before the authority receipt leaves the old owner active; a crash
   after it recovers from the receipt and refuses a second switch.
3. Reversal acquires the same lease, proves the retained reader and artifact
   provenance, and switches authority without deleting newer semantic facts.
4. A lossy reverse projection refuses and requires forward repair.

## 5. Invariants

| Invariant | Enforcement |
| --- | --- |
| An accepted record is never superseded by code deployment alone | Cutover checks the named governance artifact and superseded decision IDs |
| One concern has one active writer | Cutover lease and compare-and-swap authority receipt switch reader and writer together |
| Shadow data cannot grant authority | Compatibility readers mark it non-authoritative until the cutover receipt exists |
| Reversal preserves semantic history | Reverse readers project older forms without deleting criteria, approvals, evidence, reports, or dispositions |
| Initial review cannot become a permanent task lock | The initial record proves one review gate; later in-envelope task projections need no approval and cannot change protected semantic inputs |
| Parallelism cannot arrive early | Scheduler exposes sequential capability until both governance and proof gates pass |

## 6. Build and Documentation Mapping

| Cutover | Sources that must change together | Verification |
| --- | --- | --- |
| Slice 1 acceptance authority and initial plan review | `ARCHITECTURE.md`, `loop-infrastructure.md`, `loop-contract.md`, approval/review schemas, evaluator and importer | Digest canonicalization, atomic import, initial-review semantics, verdict parity, cache deletion, reverse read |
| Slice 3 knowledge separation | `knowledge-capture.md`, project-knowledge producer profile and intake, projection contracts | Reusable-observation parity, retained work-item capture, unavailable intake, merged-record quarantine |
| Slice 4 procedure authority and mutable task projection | `ARCHITECTURE.md`, `loop-infrastructure.md`, supervisor facade, task projector, legacy result/cohort adapters | Command, schedule, task replacement, protected-boundary refusal, backward-edge, crash, and reversal parity |
| Slice 7 parallel admission | `ARCHITECTURE.md`, `loop-parallelism.md`, superseding ADR/RFC, scheduler, security and integration ports | Governance refusal, read-proof enforcement, permutation equivalence, sequential fallback |
| Slice 8 removal | All reverse readers and release manifests plus retired engine/cohort sources | Full reversal rehearsal followed by engine-removal rehearsal |

Frozen ADR bodies remain unchanged. A superseding record and permitted errata
carry the relationship; current architecture pages are updated only after the
new record is accepted.

## 7. Quality Scenarios

| Stimulus | Response | Target | Verification |
| --- | --- | --- | --- |
| Cutover runs without its superseding record | Refuse before changing a reader or writer | Zero implied supersessions | Missing-governance fixture per governed row |
| One side of the legacy spec-approval/initial-review import fails | Publish neither record | Zero partially initialized deliveries | Crash, malformed-spec-policy, and malformed-plan corpus |
| A working plan reorders, splits, or replaces tasks inside the reviewed envelope | Reproject without approval and cancel only unintegrated predecessor attempts | Zero approval prompts and zero lost integrated facts | Reorder, split, replacement, cancellation, and evidence-preservation corpus |
| A replan changes a protected semantic boundary or terminal intent | Refuse dispatch and name the owning amendment or review route | Zero protected changes execute as ordinary replans | Criterion, evidence-policy, scope/non-goal, authority/security, public-contract, durable-output, accepted-risk, and terminal-intent mutation corpus |
| Parallel provider is installed before slice 7 governance | Advertise or select sequential capability only | Zero concurrent dispatches | Pre-governance provider fixture |
| Reversal follows newer semantic writes | Reverse reader preserves facts it cannot represent and refuses lossy authority switch | Zero deleted semantic facts | Forward-write then reversal rehearsal |

## 8. Risks and Ownership

- **Risk:** Governance lands after implementation and shadow paths become a de
  facto authority. **Mitigation:** conformance keeps all target decisions
  non-authoritative until the governance fingerprint is present.
- **Risk:** Baseline pages and accepted records disagree after cutover.
  **Mitigation:** their updates share the cutover change and release manifest.
- **Risk:** A rollback reader is retained but no longer executable.
  **Mitigation:** every release rehearses the retained reader before removal.

| Responsibility | Owner |
| --- | --- |
| Superseding work-loop authority record | Architecture-governance owner |
| Slice cutover and reverse-reader implementation | Core and `agentbundle` maintainers |
| Parallelism supersession and safety proof | Architecture-governance, security, and Core maintainers |
| Release authorization and reversal | `agentbundle` release maintainer on call |
