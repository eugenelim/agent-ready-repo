# Subsystem Design — Delivery-to-knowledge projection

**Decision sought:** Let delivery project attributed observations from facts it
already owns, while knowledge capture owns every cursor, retry, admission,
storage, and enquiry concern.
**Author:** Platform Core
**Status:** Draft
**Last updated:** 2026-10-01
**Reviewers:** Core and project-knowledge maintainers

## 1. Scope and Context

| In scope | Out of scope | Why |
| --- | --- | --- |
| Deterministic observation projection from durable delivery facts | Knowledge admission and distillation | Delivery cannot promote its observations to reusable truth |
| Provenance, subject, classification, and inert framing | Knowledge taxonomy and retention | Project knowledge owns its lifecycle |
| Optional notification after fact commit | Delivery-owned queue, cursor, retry, acknowledgement, or skip state | Knowledge failure cannot become delivery state |
| Migration of reusable pattern, gotcha, and antipattern capture | Close-time `work-item` capture | Specific blocked residue remains an explicit closeout record, not a reusable observation |

**Goals**

- Delivery behaves identically when knowledge tooling is absent or failing.
- Every observation is reproducible from a durable execution or review fact.
- Knowledge capture can retry, reject, or revoke without writing delivery state.

**Non-goals**

- Moving product truth, requirements, decisions, or knowledge admission into
  the work loop.

## 2. Structural Model

| Element | Type | Responsibility | State |
| --- | --- | --- | --- |
| Delivery fact feed | Read-only contract | Enumerate committed evidence and review facts as complete bounded snapshots | Stateless |
| Observation projector | Pure component | Map an eligible source fact to `knowledge-observation.v1` or no result | Stateless |
| Notification port | Optional adapter | Hint that a new projection is available | No durable delivery state |
| Knowledge collector | Project-knowledge adapter | Pull facts, checkpoint scans, deduplicate, and request admission | Knowledge-owned cursor |
| Knowledge intake | Existing subsystem | Validate usefulness, privacy, provenance, and scope | Admission and knowledge records |
| Committed-store reader | Project-knowledge boundary | Revalidate committed records that may have arrived outside intake | Knowledge-owned quarantine view |

The projector does not decide that an observation is reusable knowledge. It
adds no queue or shadow store: the durable source fact is the replay source.

## 3. Runtime Model

**Normal sequence**

1. Evidence or review commits a durable fact.
2. The projector verifies provenance, applies the shared
   [`content-safety-policy.v1`](delivery-content-safety.md), and deterministically
   returns one bounded observation or no result.
3. Work-loop may notify an installed listener after the fact commit. It neither
   waits for nor records delivery acknowledgement.
4. Independently, the knowledge collector scans source facts and runs the same
   projector. It owns its cursor, retries, deduplication, and admission calls.
5. Knowledge intake accepts, rejects, quarantines, or later revokes the
   observation without changing acceptance or delivery history.
6. Enquiry and distillation revalidate committed records before use. A record
   introduced by merge without a current valid schema, profile, and inert-data
   decision is excluded into a knowledge-owned quarantine view.

**Failure and recovery sequence**

1. A missing listener, dropped notification, or unavailable collector changes
   no delivery result.
2. Missing provenance or content refusal yields no observation and no skip
   record; the source fact remains authoritative.
3. Collector restart resumes from knowledge-owned state or safely rescans.
   Deterministic observation identity makes repeats idempotent.
4. Source correction, supersession, or deletion is re-evaluated by the
   knowledge lifecycle using the retained provenance.

Notification is only a latency optimization. Pull projection is the recovery
path, so delivery never owns backpressure, poison-message, or replay procedure.

## 4. Contracts and Invariants

| Contract | Producer → consumer | Identity | Compatibility and change authority | Failure semantics | Invariant |
| --- | --- | --- | --- | --- | --- |
| `delivery-fact-feed.v1` | Evidence transaction and reviewer-report stores → knowledge collector | Delivery lineage, snapshot fingerprint, source schema and fact ID | Core and project-knowledge owners approve eligible schemas and ordering; readers precede writers; unknown majors refuse | Unsafe, corrupt, changing, or incomplete snapshots refuse completion; bounded pages never silently truncate | One complete snapshot enumerates every eligible committed fact in stable schema-and-ID order and marks current, superseded, or revoked state |
| `knowledge-observation.v1` | Pure projector → optional listener and knowledge intake | Source fact ID, source schema, projection version, content-policy version | Core and project-knowledge owners approve; readers precede writers; unknown majors quarantine | Missing provenance, ineligible source, or content refusal returns no observation and writes nothing | Observation is derived, inert data with complete source provenance and no delivery authority |
| `knowledge-captured-observation.v2` read validation | Committed knowledge store → enquiry and distillation | Stored record ID, kind, schema and content-policy versions | Project-knowledge owners approve; current readers validate before use | Invalid, unsafe, or unknown records are excluded and reported without mutating the committed file | Git presence alone never makes a merged record eligible knowledge |

The feed returns at most 1,000 facts per page, one immutable snapshot
fingerprint, the last stable schema-and-ID key, and `complete`. A continuation
request names that fingerprint and last key; it is a stateless query, not a
delivery cursor. If the snapshot cannot be reproduced, the feed refuses and
the collector starts a new scan.

Superseded or revoked facts carry their status and successor reference. After
`complete`, the collector reconciles facts absent from the snapshot against its
own prior inventory, so deletion handling also remains knowledge-owned.

The contract carries the source reference, delivery subject and lineage,
observation type, bounded normalized content, producer, classification, and
effective time. It rejects raw transcripts, unbounded output,
producer-declared protected data, and scanner-covered matches. Unknown personal
data remains a residual risk handled by minimization, controlled references,
and intake revalidation.

Only source-fact schemas explicitly named by the projection policy are
eligible. Adding a source kind changes that policy and its fixtures; arbitrary
session prose can never become a projection input.

## 5. Data and State

| Element | State it owns | Lifecycle | Consistency requirement |
| --- | --- | --- | --- |
| Delivery fact feed | None; each snapshot is derived from existing evidence and review facts | Recreated for each scan | Stable ordering, bounded pages, and `complete` cover the named snapshot or refuse |
| Observation projector | None | Re-run at any time | Same source and policy produce the same identity and bytes |
| Notification port | Adapter-private transient handle | Sent or dropped | Loss changes only capture latency |
| Knowledge collector and intake | Cursor, dedupe, admission, retention, knowledge records | Existing project-knowledge lifecycle | No state is read by acceptance or readiness |
| Committed-store reader | Disposable quarantine view and reason codes | Rebuilt on store change or policy upgrade | Deleting the view re-runs validation; it grants no delivery authority |

Delivery owns no knowledge queue, skip log, admission record, or capture retry.

## 6. Deployment and Operations

| Unit | Runs as | Scaling | Observability |
| --- | --- | --- | --- |
| Observation projector | `work-supervisor.py knowledge project` or project-knowledge adapter | Bounded one fact at a time; collector batches externally | Projected, ineligible, refused counts |
| Optional listener | Installed runtime adapter | Best effort | Notification sent or dropped |
| Collector and intake | Existing project-knowledge lifecycle | Own batching, cursor, retention, and backpressure | Knowledge-owned lag and admission measures |

## 7. Quality Scenarios and Verification

| Stimulus | Mechanism and response | Target | Verification |
| --- | --- | --- | --- |
| Knowledge tooling is unavailable | Delivery commits its fact and stops knowledge work | Identical readiness and completion | Disabled-provider fixture |
| Notification is lost | Collector rescans and derives the same observation ID | Zero source-fact loss | Drop-and-rescan fixture |
| Collector scans a fact twice | Deterministic identity lets knowledge deduplicate | One admission decision per source and policy | Replay fixture |
| Source contains detected protected data | Projector returns no observation; intake revalidates | Zero scanner-corpus payloads enter knowledge | Privacy corpus |
| Delivery caches and journals are deleted | Projector reads durable semantic facts only | Identical projected observations | Rehydration fixture |
| Source is superseded or revoked | Provenance lets knowledge reconcile its derived record | Zero orphaned authoritative knowledge claims | Supersession and revocation fixture |
| A merge introduces an unvalidated knowledge record | Reader excludes it before enquiry or distillation and records a bounded quarantine reason | Zero invalid merged records enter an evidence response or topic mutation | Merge-bypass schema, privacy, instruction-shape, and unknown-policy corpus |
| Closeout captures a specific blocked item | Existing `work-item` producer profile validates and writes it outside observation projection | Zero work items inferred from reusable delivery facts | Existing reasoning-tier, schema, privacy, and closeout fixtures |

## 8. Implementation Mapping

| Element | Source owner | Build unit | Verification |
| --- | --- | --- | --- |
| Read-only fact feed | Proposed `contracts/delivery/delivery-fact-feed.v1` and `work_supervisor/knowledge_fact_feed.py` over committed evidence and review stores | Slice-3 supervisor service bundle | Snapshot, ordering, pagination, concurrent-change, supersession, deletion-reconciliation, and refusal tests |
| Observation schema and projection policy | `contracts/delivery/knowledge-observation.v1`; proposed `work_supervisor/knowledge_projection.py` | Slice-3 supervisor service bundle | Schema parity, determinism, provenance, and refusal tests |
| Optional notification adapter | Proposed supervisor notification port | Host adapter | Absence and drop tests |
| Pull collector and admission | Proposed pull mode and collector in `packs/core/.apm/skills/project-knowledge/` | Core pack | Rescan, dedupe, revocation, and unavailable-source tests |
| Committed-store read validation | Existing project-knowledge readers plus proposed quarantine projection | Core pack | Merge-bypass, exclusion, rebuild, and no-authority tests |
| Retained close-time work items | Existing `project-knowledge --capture --producer-profile work-loop` and `knowledge-captured-observation.v2` | Core pack and close-work | Existing work-item validation and closeout tests |

No `handoff_store.py`, knowledge skip store, or delivery-side capture cursor is
built.

## 9. Decisions, Alternatives, and Risks

- **Decision:** Project knowledge observations from existing facts; keep all
  capture state in the knowledge lifecycle.
- **Alternative:** Persist a delivery-owned handoff queue and skip log.
  **Rejected because:** it recreates retry, retention, and recovery procedure
  inside work-loop.
- **Alternative:** Keep capture gates after planning and execution. **Rejected
  because:** knowledge availability becomes a delivery dependency.
- **Alternative:** Depend on manual memory. **Rejected because:** provenance and
  reproducible source identity are lost.
- **Risk:** Source facts omit context useful to later work. **Mitigation:**
  improve the owning fact schema rather than create a second observation store.
- **Risk:** Projection creates noisy candidates. **Mitigation:** keep projection
  eligibility narrow; knowledge intake still owns usefulness and admission.
- **Risk:** Notification loss delays capture. **Mitigation:** pull scanning is
  authoritative for discovery.

## 10. Rollout, Migration, and Reversal

Slice 3 projects reusable pattern, gotcha, and antipattern facts while their
existing capture gates remain authoritative for comparison. Project-knowledge
then proves pull rescan, deduplication, privacy, merged-record quarantine, and
revocation without a listener.

After parity, remove only those reusable capture and distillation gates. Retain
explicit close-time `work-item` capture for specific blocked residue. Rollback
disables projection; it restores no queue or delivery state because none
exists.

| Responsibility | Owner |
| --- | --- |
| Projection contract and service | Core and `agentbundle` build maintainers |
| Collector, admission, retention, and revocation | Project-knowledge maintainers |
| Rollback authorization | Project-knowledge maintainer after projection or provenance failure |
