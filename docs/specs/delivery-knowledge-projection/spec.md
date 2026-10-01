# Spec: Delivery knowledge projection

- **Status:** Draft
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** brief:acceptance-centered-work-loop
- **Discovery:** none
- **Contract:** `contracts/delivery/` (accepted Slice 1 canonical delivery-contract bundle)
- **Shape:** integration

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

Platform Core and project-knowledge maintainers receive reproducible knowledge candidates derived from durable delivery facts without making knowledge availability part of delivery. Success means pull scanning converges after lost notifications, invalid committed knowledge stays unusable, and delivery owns no knowledge lifecycle state.

## What Changes

- A read-only delivery fact feed exposes eligible committed evidence and review facts through the contract namespace accepted by Slice 1.
- A pure projector derives bounded, attributed knowledge observations or no observation from those facts.
- Reviewed-envelope, initial-plan-review, plan, task-projection, and mutation-classification inputs remain delivery authority or procedure inputs rather than reusable knowledge candidates.
- Project-knowledge pulls, checkpoints, deduplicates, admits, stores, retains, and revokes projected observations.
- Project-knowledge revalidates records read from Git and quarantines invalid committed records before enquiry or distillation.
- Delivery may send a best-effort notification after a fact commit without awaiting or recording acknowledgement.
- Reusable capture gates leave delivery, while explicit close-time `work-item` capture remains a deliberate bounded fact.

## Scope and Non-goals

This slice owns `delivery-fact-feed.v1`, `knowledge-observation.v1`, the pure
projection policy over eligible Slice 1 evidence and current Slice 2 review
facts, optional post-commit notification, project-knowledge pull collection,
committed-store read quarantine, and removal of reusable capture gates after
parity. It retains the existing explicit close-time `work-item` producer path.

It does not change acceptance or review authority, treat reviewed-envelope or
initial-plan-review data as knowledge, remove the current plan lock, reproject
mutable tasks, transfer procedure ownership, add Pi or another runtime
dependency, start Slice 4, or make knowledge tooling part of readiness.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | The feed, projection, and committed-record validation cross delivery and project-knowledge boundaries. | `contracts/delivery/`, `contracts/README.md`, and `contracts/REGISTRY.md`; Slice 3 record files follow the accepted Slice 1 inventory and the accepted Slice 2 review surface. | Core and project-knowledge contract maintainers | Schema validation, compatibility fixtures, and spec-to-contract traceability | Every exposed record has one canonical schema and matching producer and consumer validation. |
| Current architecture | The ownership boundary between delivery and knowledge changes. | `docs/architecture/acceptance-centered-work-loop.md`, `docs/architecture/work-loop-knowledge-handoff.md`, and the baseline `docs/architecture/knowledge-capture.md` | Platform Core and project-knowledge maintainers | Architecture review and links to contracts, implementation, committed-store read-validation and quarantine behavior, and conformance suites | The current architecture and baseline knowledge-capture page name the stateless delivery projection, independent knowledge lifecycle, committed-store read validation and quarantine, and retained explicit `work-item` seam without relying on this frozen spec. |
| Maintainer procedure | Maintainers need current pull-scan, quarantine, disabled-provider, and retained-work-item checks. | `packs/core/seeds/docs/knowledge/README.md` and the established work-loop/close-work maintainer guidance selected during implementation | Core and project-knowledge maintainers | Documented commands exercise rescan, quarantine, unavailable tooling, and explicit work-item capture | A maintainer can run the supported checks without reading this delivery record. |
| Release history | Core pack and package behavior changes ship through their existing release owners. | `packs/core/pack.toml`, package version surfaces selected by the accepted implementation boundary, and `docs/product/changelog.md` | Core pack and package release maintainers | Version parity, build output, targeted suites, and an outcome-led changelog entry | Released artifacts contain matching contracts and behavior, and the changelog names the maintainer-visible result. |

## Agent Rules

### Always do

- Before approval, retain the exact accepted Slice 1 revision, cite the exact accepted Slice 2 revision, and bind eligible source facts, acceptance and review currentness, identity and version inputs, ordering, content-policy application, and the retained `work-item` producer contract by reference to those accepted owners.
- Use Slice 1 acceptance authority to admit durable semantic evidence, and use Slice 2 currentness and acknowledgement rules to admit review facts; treat the reviewed envelope, initial plan review, and mutation classification only as authority or procedure controls, never as knowledge candidates.
- Derive every observation from an eligible durable fact with complete source provenance and deterministic identity.
- Apply the accepted content-safety and contract validation boundaries before an observation or committed knowledge record becomes usable.
- Keep pull scanning authoritative for discovery; treat notification as a latency optimization that may be dropped.
- Preserve explicit close-time `work-item` capture as a separate deliberate path with its existing bounds and validation.
- Keep knowledge-owned cursors, retries, deduplication, admission, storage, retention, quarantine, and revocation outside delivery readiness.
- Keep the current engine and legacy plan lock authoritative; only Slice 4 may introduce mutable task reprojection and remove that lock through its accepted cutover.

### Ask first

- Add an eligible source-fact kind, observation kind, or projection-policy version.
- Change the accepted Slice 1 or Slice 2 contract fields, identity, freshness, report, assessment, or disposition semantics.
- Change project-knowledge admission, retention, revocation, or storage ownership.
- Change when closeout creates an explicit `work-item` or what that record may contain.

### Never do

- Add a delivery-owned knowledge queue, cursor, retry, acknowledgement, skip log, admission record, retention record, revocation record, or capture gate.
- Make notification, scanning, admission, enquiry, distillation, or any knowledge-tool result a prerequisite for spec, plan, review, acceptance, readiness, or closeout.
- Treat a projected observation as accepted knowledge, product truth, a requirement, a decision, evidence, review disposition, or delivery authority.
- Project `reviewed-execution-envelope.v1`, `initial-plan-review.v1`, plan text, task projections, or mutation-classification results as reusable observations.
- Infer close-time `work-item` records from reusable observations or silently convert blocked delivery residue into knowledge.
- Import, bundle, install, or select Pi, or make Pi compatibility a prerequisite for this slice or any later Core cutover.
- Start Slice 4, move orchestration authority, or alter the predecessor-owned acceptance and review contracts in this slice.

## Testing Strategy

- Fact-feed snapshot semantics, projection eligibility, deterministic identity, and pure replay use **TDD** because each has a compact input/output invariant.
- Pull rescan, duplicate scans, committed-store quarantine, source supersession, and retained `work-item` capture use **TDD through integration tests** because their observable result crosses delivery and project-knowledge boundaries.
- Lost notification, absent or failing knowledge tooling, cache deletion, and readiness isolation use a **goal-based check through end-to-end conformance fixtures** because a unit test cannot prove that delivery completion is unchanged.
- Removal of delivery-owned lifecycle state and release closure use **goal-based checks** over source ownership, contract parity, package builds, and status gates. This slice has no visual or manual-QA behavior.

## Acceptance Criteria

- [ ] **AC-0001:** A complete pull scan enumerates every eligible committed delivery fact in stable contract-defined order from one reproducible snapshot, or refuses without returning a partial snapshot when that snapshot cannot be reproduced.
- [ ] **AC-0002:** Replaying the same eligible durable facts under the same projection and content-policy versions yields byte-identical observation identities and payloads, while an ineligible or refused fact yields no observation and no delivery record; reviewed-envelope, initial-plan-review, plan, task-projection, and mutation-classification inputs are ineligible.
- [ ] **AC-0003:** After every best-effort notification for an eligible fact is dropped, a later pull scan presents the same projected observations to project-knowledge as a scan performed with notifications delivered.
- [ ] **AC-0004:** Repeated and overlapping scans may repeat the same deterministic observation, but create no delivery-owned cursor, deduplication, acknowledgement, retry, skip, admission, or retention state.
- [ ] **AC-0005:** When Git introduces a malformed, unsafe, unknown-version, or policy-invalid committed knowledge record outside intake, enquiry and distillation exclude it and report a bounded knowledge-owned quarantine reason without mutating the committed record.
- [ ] **AC-0006:** A deliberate close-time `work-item` request that satisfies the existing work-loop producer contract remains observable through project-knowledge capture, while reusable delivery facts never infer or synthesize a `work-item`.
- [ ] **AC-0007:** For identical delivery facts, absent, disabled, unavailable, timing-out, refusing, or failing knowledge tooling produces the same spec, plan, review, acceptance, readiness, and closeout decisions as successful knowledge tooling.
- [ ] **AC-0008:** Excluding the deliberate close-time `work-item` producer path covered by AC-0006, a source and durable-state inventory after migration finds no delivery-owned knowledge queue, cursor, retry, acknowledgement, skip log, reusable knowledge capture gate, admission record, retention record, revocation record, or knowledge-specific readiness transition.
- [ ] **AC-0009:** A committed current `knowledge-captured-observation.v2` record with a valid schema, content-policy version, provenance, and inert-data decision remains usable by enquiry and distillation after read validation and produces no quarantine entry.
- [ ] **AC-0010:** Repeated scans, restart and rescan, and source supersession, revocation, or deletion converge to one current project-knowledge admission or retention decision per source identity plus projection and content-policy version, with no duplicate usable record and no derived record remaining usable after its source ceases to be current unless project-knowledge explicitly re-admits it from current provenance.

## Follow-ons

none — the parent brief owns later delivery slices, and this spec does not create or start them.

## Terminal Intent

`spec-plan` — stop after the spec and initial plan review are accepted. This
slice creates no repository implementation or test artifact and dispatches no
implementation task.

## Accepted Risk

none

## Assumptions

- Technical: the parent brief is Ready at `sha256-bytes-v1:8e2cf33151320b16cf8a12bf852531f262e57b5470dc8105ed121087b0347410`, its architecture set is reviewed at `sha256-set-v1:0ca1b837a37254fdf6279e18f4ed01c6ff96ea8fd1d207b8c780e6aa4d994d02`, and the first-three slice cut is confirmed. Slice 1 is Approved at spec `sha256-bytes-v1:a4d45422a5d8529c0352e231112955f5e50d49328543e354a201471b85991478` and plan `sha256-bytes-v1:b8aaadeca66402e0b2729f5a53f0f159e4fb2526dd20afea6d9b2e873296f03d`. The latest inspected Slice 2 spec `sha256-bytes-v1:aa624326320c0faccdd9ae639b9dd62368c10722443f81869175820c2b7da442` and plan `sha256-bytes-v1:062b99437fc3bcd46cf305555220bade0f0548ad3259682684ad6e5575459860` remain Draft/Drafting and are not authority; their accepted revisions, final review-record inventory, eligible record identities, and predecessor fingerprints remain approval blockers.
