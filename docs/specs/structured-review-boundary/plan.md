# Plan: Structured review boundary

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** [`work-loop-review-disposition.md`](../../architecture/work-loop-review-disposition.md), [`acceptance-centered-work-loop.md`](../../architecture/acceptance-centered-work-loop.md), [`work-loop-acceptance-evidence.md`](../../architecture/work-loop-acceptance-evidence.md), [`work-loop-authority-migration.md`](../../architecture/work-loop-authority-migration.md), [`work-loop-execution-supervisor.md`](../../architecture/work-loop-execution-supervisor.md), the parent [`acceptance-centered-work-loop` brief](../../product/briefs/acceptance-centered-work-loop.md), the amended and approved Slice 1 spec and code-mode plan at `fd70edd51f7b45c4d0714223c07371798cca3391`, Slice 1's architecture and release closure at `cc4b6eb20e2fce7c58dac8958de27eb6c8a4e146`, and current work-loop policy and review scripts; Slice 1's contract, service, architecture, and release outputs exist, but Slice 2 execution remains gated until Slice 1's post-gates hardening and review freeze the final approved shape

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. The active legacy `approve-plan` authority continues to pin
> `spec.md` and `plan.md` in substance through Slice 2. Slice 1's shadow
> `initial-plan-review.v1` authorizes terminal intent but grants no authority to
> task content; only Slice 4 removes the legacy lock and introduces mutable task
> reprojection.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are
> working material before approval, while approval hashes the whole plan.

## Approach

Add the review boundary as callable services behind the current work-loop
engine before changing review authority. Establish the versioned contracts and
pure truth-table policies first, then persist current reports, assess findings,
record dispositions, and place the compatibility adapter across the existing
review path; conformance and parity tests keep the old path authoritative until
the new facts are complete and current, without changing the legacy plan lock,
task/cohort writers, procedure authority, or runtime provider selection.

## Constraints

- The approved Slice 1 spec and code-mode plan are the authoring and execution
  predecessor. Their contract inventory and semantics supply acceptance
  authority, the reviewed-execution envelope, protected-mutation
  classification, delivery subject, evidence transaction, verdict, and shared
  content-safety interfaces. Their canonical schemas and callable ports now
  exist and conform to the approved inventory, so T1 can resolve imports
  against them. Slice 2 execution still waits for Slice 1 closeout because its
  post-gates security hardening and review remain in flight. Mutable task
  reprojection and removal of the legacy plan lock are excluded because Slice
  4 owns them.
- The parent brief passed its Ready gate at
  `sha256-bytes-v1:8e2cf33151320b16cf8a12bf852531f262e57b5470dc8105ed121087b0347410`
  and is now `Executing` because Slice 1 moved to implementation. The
  architecture set is reviewed at
  `sha256-set-v1:0ca1b837a37254fdf6279e18f4ed01c6ff96ea8fd1d207b8c780e6aa4d994d02`,
  the first-three slice cut is confirmed, and Slice 1's spec and plan are
  approved.
- The parent brief's Architecture coverage table is the sole cross-document
  mapping for the ten architecture owners. Slice 2 cites that map and updates
  only its review-owned durable surfaces instead of copying the matrix here.
- Existing review authority remains active during compatible reads and shadow
  writes. A code deployment cannot move authority by implication.
- Existing legacy plan-lock, task/cohort, and procedure authorities remain
  active throughout Slice 2, including after any authorized review-only
  cutover. Slice 2 does not project mutable tasks or reinterpret
  `initial-plan-review.v1` as task approval.
- Pi is an optional external compatibility target owned by Slice 6. Slice 2
  neither imports, bundles, installs, selects, nor tests through Pi, and Pi
  presence cannot gate its review closure, cutover, or reversal.
- The current work-loop facade, repository test framework, shared confinement,
  and shared content-safety primitives are reused without a new dependency or
  top-level package. Core runtime modules remain self-contained standard-library
  scripts and import only sibling modules in the `work-loop` skill; build and
  test tooling cannot become a runtime dependency.
- `contracts/delivery/` remains the only delivery-schema source. Review schemas
  are test-time contracts: Core runtime scripts validate the same behavior in
  code and neither copy nor load those schemas at runtime.
- Slice 1 T9b reconciled its owned architecture pages with the implemented
  script seam and no-copy contract. The still-Draft review-disposition and
  execution-supervisor pages retain package-owned review-module and
  embedded-schema examples for later slices. Slice 2 T1 resolves its own
  review-module placement against the approved Core constraints, and T7 makes
  the review-owned architecture current; neither task rewrites later
  supervisor ownership. If a self-contained sibling service cannot satisfy the
  review contract without an `agentbundle` import or runtime schema copy,
  implementation stops for a plan amendment.
- The implemented Slice 1 service seam is grounded in sibling modules under
  `packs/core/.apm/skills/work-loop/scripts/`: `_acceptance.py`,
  `_policy_import.py`, `_subject_source.py`, `_subject_projection.py`,
  `_evidence_store.py`, `_content_safety.py`, `_security_events.py`,
  `_security_capability.py`, `_confined_mutation.py`, `_process_safety.py`,
  `_containment.py`, `_effect_broker.py`, and `_compat_facade.py`. Slice 2
  reuses those modules without a runtime import from `agentbundle`. Its own
  review-module decomposition remains T1 implementation discovery and is made
  durable by T7; a conflicting final owner or unusable shared seam requires a
  plan amendment before execution.
- The Slice 2 approval record remains repository-durable at this spec directory
  once approved. Its legacy plan digest is active lock provenance through Slice
  2; a Slice 1 `initial-plan-review.v1` copy of that digest is baseline audit
  evidence only. After closeout, authoritative schemas, architecture pages,
  tests, and release history own current review-boundary truth.

## Construction tests

**Integration tests:** T6 owns the canonical definitions of VI-1012 and
VI-1013; this summary adds no second statement of either obligation.

**Manual verification:** none

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility / review contract files resolved against the approved Slice 1 imports | T1 | VI-1001–VI-1003 schema, no-copy, and traceability results | Contract files are authoritative, linked from the spec, have no copies, and are covered by compatibility tests |
| Current architecture / review-disposition and parent architecture pages | T7 | VI-1016 durable-output trace | Pages name the shipped owner, compatibility state, and remaining cutover work |
| Maintainer procedure / canonical work-loop policy and review references | T6, T7 | VI-1012, VI-1014–VI-1019 integration, authority-isolation, self-containment, policy, pack, and durable-output checks | Published guidance contains only the opaque review boundary and preserves every authority outside Slice 2 |
| Release history / `docs/product/changelog.md` | T7 | VI-1016 durable-output trace | Release entry identifies the shipped boundary and verification result |

## Design (LLD)

### Design decisions

Owned by: T1, T2, T3, T4, T5, T6, T7

- Keep selection, report transport, failure assessment, and disposition as
  separate ports. Combining them would make reviewer invocation state part of
  delivery policy. Traces to: AC-0001–AC-0011.
- Store semantic reports and dispositions, but derive current obligation and
  readiness views. Attempts, retries, and raw reviewer sessions remain outside
  delivery authority. Traces to: AC-0005, AC-0009, AC-0010, AC-0014, AC-0015.
- Use the exact approved Slice 1 acceptance and security ports instead of local
  copies. Consume its reviewed-envelope and protected-mutation result as
  external authority facts; never turn either into a review-local planning
  decision. Traces to: AC-0008, AC-0012, AC-0013.

### Data & schema

Owned by: T1, T3, T4

- The interface inventory includes review subject, obligation, report, finding,
  assessment, and disposition record families authored by this slice. Their
  exact files, shared identity fields, and imports are resolved in T1 against
  the approved Slice 1 shared-contract inventory rather than frozen
  provisionally here. Traces to: AC-0002–AC-0009.
- Report identity has one safe current lineage tip per role and subject. Derived
  assessment views can be deleted and rebuilt from Slice 1's semantic evidence
  transactions. Traces to: AC-0005–AC-0009.
- Review identity excludes the plan digest and task-projection revision. Those
  values remain execution provenance, so a plan-only change cannot stale an
  otherwise current report; a changed acceptance subject or review-policy
  fingerprint can. Traces to: AC-0002, AC-0005, AC-0013.

### Interfaces & contracts

Owned by: T1, T2, T4, T5

- The reviewer port accepts a selected obligation and current review subject
  and returns a versioned structured report. It does not expose prompt, model,
  tool, retry, or session controls. Traces to: AC-0001, AC-0004, AC-0010.
- The Slice 1 evidence bridge is the only path by which a supported review
  failure affects criterion evidence; dispositions cannot write a supported
  acceptance verdict. Traces to: AC-0008, AC-0009, AC-0014, AC-0015.
- Canonical review schemas use JSON Schema 2020-12 under the semantic
  `contracts/delivery/` family selected by Slice 1 and remain test-time
  contracts with no runtime copies. Shared imports and callable in-code
  validators are grounded in the canonical Slice 1 schemas and sibling service
  modules; T1 owns only the review-schema resolution and registry links.

### Component / module decomposition

Owned by: T2, T3, T4, T5, T6

- Pure review-subject projection and obligation selection consume canonical
  subject and repository policy facts. Traces to: AC-0002, AC-0003.
- Content validation, schema validation, and the report store admit one inert
  report transaction or none. Traces to: AC-0004, AC-0005, AC-0012.
- The finding evaluator applies mechanical predicates and delegates only an
  indeterminate reachability decision to a named authority. Traces to: AC-0006,
  AC-0007.
- The disposition port records authorized resolution without redefining finding
  validity or acceptance support. Traces to: AC-0007–AC-0009.
- The compatibility adapter translates current reviewer artifacts into the same
  ports before acknowledging the legacy result. Traces to: AC-0011.

### State & control flow

Owned by: T2, T3, T4, T5

- Selection is recomputed from the current subject and policy. Report tips,
  assessments, and dispositions are current only when their bound identities
  still match; a changed acceptance subject or review-policy input reopens the
  applicable obligation or finding, while plan-only and task-projection
  revisions do not.
  Traces to: AC-0002, AC-0003, AC-0005, AC-0008, AC-0009.
- The invoker owns attempts only. Durable state begins after whole-report
  content and schema validation. Traces to: AC-0004, AC-0010, AC-0012.

### Behavior & rules

Owned by: T2, T4, T5

- The spec's Obligation and Finding truth tables are the behavior owners. Code
  and fixtures consume those tables without adding a reviewer-specific branch.
  Traces to: AC-0003, AC-0006–AC-0009.

### Failure, edge cases & resilience

Owned by: T3, T4, T6

- Missing, stale, malformed, forked, unsafe, unknown-major, and indeterminate
  inputs fail closed at the affected obligation. A failed compatibility
  projection remains unacknowledged so recovery can retry from the same source
  fact. Traces to: AC-0003–AC-0005, AC-0007, AC-0011, AC-0012.
- A crash cannot expose a report or assessment without its required Slice 1
  evidence delta. Recovery replays from durable semantic identities, not from
  reviewer sessions. Traces to: AC-0008, AC-0011, AC-0014, AC-0015.

### Quality attributes (NFRs)

Owned by: T2, T4, T6

- Runtime neutrality is demonstrated by the synthetic reviewer and the
  current-engine/synthetic-adapter truth-table suites. Determinism is measured
  by byte-identical normalized decisions for the same canonical inputs. Traces
  to: AC-0001–AC-0003, AC-0006, AC-0011, AC-0016.

### Dependencies & integration

Owned by: T1, T6, T7

- Slice 1 supplies acceptance authority, the reviewed envelope,
  protected-mutation classification, canonical subject, evidence, verdict,
  content-safety, confinement, and capability contracts through the grounded
  sibling service seam named in Constraints. The current work-loop engine is
  the first caller; Slice 4 later introduces mutable task projection and
  procedure ownership without changing review meaning. Pi remains outside Core
  as an optional later consumer of the neutral runtime contracts. Traces to:
  AC-0001, AC-0008, AC-0009, AC-0011–AC-0016.

## Tasks

### T1: Resolve and author the review contracts

- **Depends on:** none
- **Spec behavior:** Versioned report and record conformance; TDD.
- **Touches:** approved Slice 1 contract inventory and the confirmed review
  contract destination; spec/contract traceability.
- **Verification mode:** TDD
- **Tests:**
  - **VI-1001 (AC-0004):** schema corpus accepts one complete current report,
    rejects a separate fixture for each missing or malformed required field,
    and the delivery-contract scan finds no schema copy outside
    `contracts/delivery/`.
  - **VI-1002 (AC-0004, AC-0005):** version and lineage corpus rejects unknown majors,
    duplicate sequences, and forks while retaining one current safe tip.
  - **VI-1003 (AC-0012):** shared content-safety corpus accepts inert bounded prose and
    rejects each protected, oversized, or executable/authority-shaped report as
    one transaction.
  - **Stub:** `no stub (implementation-discovered)` — discovery predicate: T1
    must resolve the exact review-record families, schema identities and
    references, registry keys, and callable validator entry points against the
    implemented Slice 1 seam before an importable review contract surface
    exists; constraint: no provisional schema path, invented symbol, or copied
    validator; required outcome: one executable assertion per
    AC-0004/AC-0005/AC-0012 contract surface; verification mode: TDD; proof
    obligation: the first T1 change records a compilable red assertion before
    implementing its review contract.
- **Grounding:** `contracts/delivery/` and the Slice 1 sibling services provide
  the reusable schema, content-safety, and transaction boundaries; constraint —
  no copied identity or validator; required outcome — one authoritative schema
  per record family with no schema copy or runtime schema load; kill condition —
  Slice 1 closeout removes, materially changes, or leaves ambiguous a required
  predecessor contract.
- **Done when:** VI-1001–VI-1003 pass and the interface-compatibility durable output has a
  resolved destination and backward link.

### T2: Project review subjects and select obligations

- **Depends on:** T1
- **Spec behavior:** Deterministic selection and obligation closure; TDD.
- **Touches:** canonical Core work-loop policy and the reusable service seam
  discovered from Slice 1.
- **Verification mode:** TDD
- **Tests:**
  - **VI-1004 (AC-0002):** current-engine/synthetic-adapter fixture compares the
    normalized ordered obligation set for identical subject and policy inputs
    while independently varying plan and task-projection provenance.
  - **VI-1005 (AC-0003):** table-driven suite exercises every Obligation truth-table row
    and one mutation for each deciding input column.
  - **Stub:** `no stub (implementation-discovered)` — discovery predicate: T1
    identifies the callable policy seam and its contract types; constraint: the
    test calls the reusable service rather than the current engine parser;
    required outcome: one red table assertion over the selected obligation
    result; verification mode: TDD; proof obligation: the first T2 change
    records and earns that red before selection logic moves.
- **Grounding:** current role selection is owned by the work-loop skill; exact
  extraction symbols are implementation-discovered after T1. Stop if selection
  requires reviewer internals or stored workflow state.
- **Done when:** VI-1004–VI-1005 pass through the current-engine caller without changing
  the public work-loop invocation.

### T3: Validate and persist current reviewer reports

- **Depends on:** T1, T2
- **Spec behavior:** Structured report validity, current identity, and safe
  refusal; TDD.
- **Touches:** review validator/store service and current review-artifact adapter.
- **Verification mode:** TDD
- **Tests:**
  - **VI-1006 (AC-0004, AC-0005):** atomic persistence and rehydration suite proves one
    current report or an unsatisfied obligation after malformed, stale, forked,
    duplicate, and crash fixtures; a plan-only or task-projection revision
    retains the same current tip.
  - **VI-1007 (AC-0012):** persistence spy proves a refused report writes no semantic
    review record.
  - **Stub:** `no stub (implementation-discovered)` — discovery predicate: T1
    identifies Slice 1's atomic transaction/store port; constraint: no raw
    reviewer log or test-only store may stand in for it; required outcome: one
    red atomic-persistence assertion for AC-0004/AC-0005/AC-0012; verification mode: TDD;
    proof obligation: the first T3 change records and earns that red before the
    report store is implemented.
- **Grounding:** reuse the transaction and confined-write boundary imported by
  T1; stop if the only available store makes raw reviewer output authoritative.
- **Done when:** VI-1006–VI-1007 pass and report rehydration depends only on validated
  semantic records.

### T4: Assess actual failures

- **Depends on:** T1, T3
- **Spec behavior:** Reachable actual-failure classification and evidence-bridge
  lifecycle; TDD.
- **Touches:** finding evaluator, independent-assessment port, and Slice 1
  evidence bridge.
- **Verification mode:** TDD
- **Tests:**
  - **VI-1008 (AC-0006, AC-0007):** table-driven suite exercises every Finding truth-table
    row, including a supported path with controlled evidence for every edge.
  - **VI-1009 (AC-0007, AC-0008, AC-0014, AC-0015):** transaction suite proves supported
    assessments atomically create the required deterministic review-failure
    receipt set; report replacement or invalidation and supported-assessment
    replacement atomically supersede every derived receipt, including
    supported-to-unsupported and supported-to-indeterminate outcomes; those
    outcomes also remove or refuse current disposition eligibility.
  - **Stub:** `no stub (implementation-discovered)` — discovery predicate: T1
    exposes the approved evidence transaction and supersession call surface;
    constraint: assessment and receipt delta share that atomic boundary;
    required outcome: one red finding-assessment assertion over a supported and
    an unsupported fixture; verification mode: TDD; proof obligation: the first
    T4 change records and earns that red before evaluator implementation.
- **Grounding:** the approved Slice 1 evidence transaction and supersession
  contracts are mandatory inputs; stop if assessment and evidence cannot commit
  atomically.
- **Done when:** VI-1008–VI-1009 pass and the assessment view rebuilds from authoritative
  Slice 1 transactions.

### T5: Record dispositions and derive review closure

- **Depends on:** T2, T4
- **Spec behavior:** Disposition semantics and mandatory-obligation closure; TDD.
- **Touches:** disposition port and review-readiness query.
- **Verification mode:** TDD
- **Tests:**
  - **VI-1010 (AC-0008):** disposition table covers repair-request, fixed-by with fresh
    replacement report, and accept-risk without acceptance-support mutation.
  - **VI-1011 (AC-0009):** readiness matrix refuses every combination with an
    unsatisfied mandatory obligation or open supported material finding.
  - **Stub:** `no stub (implementation-discovered)` — discovery predicate: T1
    and T4 expose the approved decision-authority and current-assessment types;
    constraint: a disposition cannot write assessment validity or acceptance
    support; required outcome: one red disposition/readiness assertion covering
    an open repair request and an authorized accept-risk; verification mode:
    TDD; proof obligation: the first T5 change records and earns that red before
    disposition logic is implemented.
- **Grounding:** decision authority rules come from current repository policy;
  stop if a disposition can rewrite assessment validity or Slice 1 support.
- **Done when:** VI-1010–VI-1011 pass and deleting derived readiness state does not
  change the recomputed result.

### T6: Integrate the compatibility boundary

- **Depends on:** T3, T4, T5
- **Spec behavior:** Synthetic reviewer integration and legacy parity;
  non-review authority isolation; runtime self-containment; goal-based
  integration checks.
- **Touches:** current review-artifact, loop-engine, and loop-cohort seams plus
  the bundled service entry point discovered after Slice 1.
- **Verification mode:** goal-based check
- **Tests:**
  - **VI-1012 (AC-0001):** synthetic reviewer conformance fixture reaches review-clear
    through only the published reviewer port and policy registration.
  - **VI-1013 (AC-0011):** table-driven integration test consumes the spec's closed
    Compatibility corpus and compares each required structured result and
    acknowledgement decision with the current path.
  - **VI-1018 (AC-0013):** authority-isolation fixture compares legacy
    `approve-plan`, task/cohort writer, and procedure-authority decisions before
    and after Slice 2 wiring, proves `initial-plan-review.v1` is never consumed
    as task approval, and proves no Slice 2 caller can request or acknowledge a
    mutable-task projection.
  - **VI-1019 (AC-0016):** clean-environment integration runs the synthetic
    reviewer and closed Compatibility corpus after proving `agentbundle` and
    other repository packages are unavailable; a static import check permits
    only the standard library or sibling `work-loop` modules, and a runtime
    filesystem spy observes zero reads under `contracts/delivery/` while
    leaving build and test tooling free to validate the canonical schemas.
- **Grounding:** discovery predicate — locate the active approval, reviewer
  transition, finding-assessment, task/cohort-writer, and procedure-authority
  owners in `packs/core/.apm/skills/work-loop/scripts/review-artifact.py`,
  `loop-engine.py`, and `loop-cohort.py`; required outcome — one generic review
  seam that preserves every non-review authority; stop if the seam is absent or
  integration requires a reviewer-role branch in a shared policy path.
- **Done when:** VI-1012, VI-1013, VI-1018, and VI-1019 pass with the old
  authorities enabled and the new records reconstruct the same admitted review
  results from a self-contained Core runtime.

### T7: Remove reviewer mechanics from policy and refresh durable outputs

- **Depends on:** T6
- **Spec behavior:** Reviewer opacity, non-review authority isolation, and
  current maintainer truth; goal-based source and documentation checks.
- **Touches:** canonical work-loop skill source, owned review references,
  architecture pages, generated projections, and `docs/product/changelog.md`.
- **Verification mode:** goal-based check
- **Tests:**
  - **VI-1017 (AC-0010, AC-0011, AC-0013):** authority-cutover check requires a
    repository-durable approval receipt that names the retiring and successor
    review authorities, cites passing VI-1013 parity evidence, accepts tested
    reversal evidence, and authorizes policy cleanup before any current-review
    mechanic is removed; it grants no plan, task, cohort, procedure, or runtime
    provider authority.
  - **VI-1014 (AC-0010):** bounded source check fails on a reviewer-role condition or
    any prompt, tool, model, retry, session, or reviewer-workflow field in the
    delivery-policy surface.
  - **VI-1015 (AC-0001, AC-0010, AC-0013):** pack and projection tests prove
    the public invocation and non-review authority surfaces are unchanged and
    generated copies match their source.
  - **VI-1016 (AC-0001–AC-0016):** durable-output review traces the shipped contracts,
    architecture, maintainer procedure, and release entry to their owning tests.
- **Grounding:** edit the canonical pack source and regenerate projections per
  repository guidance; do not hand-edit generated copies or remove the active
  legacy plan-lock and task/cohort paths.
- **Done when:** VI-1014–VI-1017 pass, VI-1018 and VI-1019 still pass after
  policy cleanup, the authority-cutover receipt remains current for the shipped
  review-policy and contract fingerprints and parity evidence, and every
  Durable-output map row meets its closeout evidence condition.

## Rollout

- **Delivery:** compatible readers and shadow writers land first while the
  current review path remains authoritative; role-by-role authority changes
  only after parity and reversal evidence is accepted. Every plan, task/cohort,
  and procedure authority remains unchanged.
- **Infrastructure:** none beyond repository-local contract, evidence, review,
  and disposition records supplied by this migration.
- **External-system integration:** none; reviewer implementations remain opaque
  adapters selected by repository policy. Core has no Pi integration or
  dependency in this slice.
- **Deployment sequencing:** start only after Slice 1 closeout freezes the
  implemented contract and service seam while the legacy plan lock remains
  active; land T1–T5 services; run T6 dual-path parity, authority-isolation, and
  crash recovery; record the approved review-path switch and accepted reversal
  evidence in VI-1017; then perform T7 review-policy cleanup and durable-output
  refresh.

## Risks

- Slice 1 implementation may diverge from its approved inventory or semantics.
  T1 refuses the mismatch until Slice 1 is corrected or its approved contract
  receives the required amendment and fresh review.
- A compatibility adapter may become a second authority. Dual writes remain
  non-authoritative until one acknowledged cutover selects the reader and writer
  together.
- A schema may duplicate a predecessor-owned identity or safety rule. T1 imports
  and references predecessor definitions; schema review rejects copied fields
  that have an existing owner.
- Actual-failure assessment may become a renamed general adjudicator. VI-1008 keeps
  the decision to one reachability question and sends indeterminate cases to a
  named authority without adding workflow state.
- Accept-risk may hide contradictory acceptance evidence. VI-1009 and VI-1010 prove the
  evidence and review decisions remain separate.

## Changelog

<!-- Approval entries only:
- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->
- 2026-10-04: spec approved by owner
- 2026-10-04: plan approved by owner
