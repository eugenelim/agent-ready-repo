# Plan: Structured review boundary

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** [`work-loop-review-disposition.md`](../../architecture/work-loop-review-disposition.md), [`acceptance-centered-work-loop.md`](../../architecture/acceptance-centered-work-loop.md), [`work-loop-acceptance-evidence.md`](../../architecture/work-loop-acceptance-evidence.md), [`work-loop-authority-migration.md`](../../architecture/work-loop-authority-migration.md), [`work-loop-execution-supervisor.md`](../../architecture/work-loop-execution-supervisor.md), the parent [`acceptance-centered-work-loop` brief](../../product/briefs/acceptance-centered-work-loop.md), shipped Slice 1 at squash commit `9d39eae8b` (PR #1515), its [verification ledger](../acceptance-authority-and-evidence/notes/verification-ledger.md), and current work-loop policy and review scripts

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
  against them. Slice 1 is shipped at `9d39eae8b`; its final security hardening
  and review evidence are recorded in its verification ledger. Mutable task
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
- Existing legacy plan-lock, task/cohort, review, and procedure authorities
  remain active throughout Slice 2. The review-authority cutover is the
  separate [follow-on](../../product/intents/FEAT-0036-review-authority-cutover.md).
  Slice 2 does not project mutable tasks or reinterpret
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

**Shipped-predecessor reconciliation:** the [interface check](notes/slice-1-reconciliation.md)
records the exact Slice 1 append/replay, validator, content-safety, audit, and
shadow interfaces at `9d39eae8b`. T1, T3, T4, and T6 below consume that check.
This task regeneration changes no accepted criterion, schema, authority, scope,
durable output, or accepted risk. Pre-EXECUTE reviews and both human gates run
again because the prior ignored engine/cohort state is absent.

**Integration tests:** T6 owns the canonical definitions of VI-1012 and
VI-1013; this summary adds no second statement of either obligation.

**Manual verification:** none

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility / review contract files resolved against the approved Slice 1 imports | T1 | VI-1001–VI-1003 schema, no-copy, and traceability results | Contract files are authoritative, linked from the spec, have no copies, and are covered by compatibility tests |
| Current architecture / review-disposition and parent architecture pages | T7 | VI-1016 durable-output trace | Pages name the shipped owner, compatibility state, and remaining cutover work |
| Maintainer procedure / canonical work-loop policy and review references | T6, T7 | VI-1012, VI-1014–VI-1016, VI-1018, VI-1019, and VI-1020 integration, authority-isolation, self-containment, policy, pack, and durable-output checks | Published guidance gains no reviewer-specific procedure, retires no current review authority, and its projections match source |
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
- **Shipped seam:** use the owning sibling validators; no shared
  `_schema_validation.py` exists. Review schemas reference the approved
  delivery-subject and other shared schema properties rather than copying
  them. Register a closed review-owned writer/replay map before use, preserving
  `SLICE_1_WRITER_BOUNDARIES` and its existing profile assignments. Enforce
  individual report free-text bounds as well as the shared whole-record bound.
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
- **Shipped seam:** extend `EvidenceStore` with a backward-compatible batch
  transaction port and a closed, code-owned set of review-record validators
  and replay indexers. Existing receipt/supersession calls, schemas, frames,
  denial codes, authority checks, and recovery behavior remain compatible.
  Unknown record kinds refuse; callers cannot supply arbitrary validators.
  Admit every embedded record through its registered content profile and
  validator on append and replay. This implements the existing semantic
  transaction contract rather than adding a second authoritative journal.
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
- **Shipped seam:** use T3's batch port for the assessment and the complete
  deterministic criterion receipt set in one frame; use the same port for
  source replacement and the complete supersession delta. Rebuild assessment
  views from those frames. Do not encode assessments in receipt identifiers
  or producer strings and do not substitute two separately committed logs.
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
    Regression and mutation checks cover existing single-record callers,
    whole-frame recovery, duplicate/first-wins replay, concurrent appends,
    authority on retry, stable denial mapping, and a post-allow denial with the
    same operation ID. Rehydration must recover the assessment and its entire
    receipt set, not merely references to separately committed records.
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
- **Shipped authority seam:** before any disposition becomes visible, validate
  the named decision maker against current policy, subject, finding, and
  capability record scope through the approved Slice 1 authority ports. Store
  the durable security allow event before the ledger effect. Missing,
  unauthorized, stale, or out-of-scope authority and an unavailable audit sink
  refuse with stable codes and expose no semantic disposition. A refusal after
  an allow stores a denial with the same operation ID.
- **Verification mode:** TDD
- **Tests:**
  - **VI-1010 (AC-0008):** disposition table covers repair-request, fixed-by with fresh
    replacement report, and accept-risk without acceptance-support mutation.
    Negative fixtures cover missing, unauthorized, stale, and out-of-scope
    decision authority; audit-unavailable fixtures prove no ledger effect;
    post-allow failure fixtures prove same-operation audit pairing. These checks
    apply to every disposition kind, including replacement-subject fixed-by.
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
  change the recomputed result; every disposition write proves authority and
  audit-before-effect or returns its stable refusal without visibility.

### T6: Integrate the compatibility boundary

- **Depends on:** T3, T4, T5
- **Spec behavior:** Synthetic reviewer integration and legacy parity;
  non-review authority isolation; runtime self-containment; goal-based
  integration checks.
- **Touches:** current review-artifact, loop-engine, and loop-cohort seams plus
  the bundled service entry point discovered after Slice 1.
- **Shipped seam:** preserve Slice 1's opt-in post-legacy-commit shadow calls
  and redacted divergence behavior. A separate explicit review compatibility
  adapter owns source-event reconciliation and acknowledges only after both
  current and structured review facts exist. A shadow observation alone is
  never that acknowledgement or a review-authority cutover.
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

### T7: Refresh durable outputs for the shipped boundary

- **Depends on:** T6
- **Spec behavior:** Reviewer opacity of the shipped boundary, review and
  non-review authority isolation, and current maintainer truth; goal-based source and
  documentation checks.
- **Touches:** review-owned architecture pages, `contracts/README.md` and
  `contracts/REGISTRY.md`, generated projections, `packs/core/pack.toml`,
  `packs/core/.claude-plugin/plugin.json`, the Core work-loop eval harness at
  `packs/core/.apm/skills/work-loop/evals/evals.json`, and
  `docs/product/changelog.md`.
- **Verification mode:** goal-based check
- **Tests:**
  - **VI-1014 (AC-0010):** bounded source check fails on a reviewer-role
    condition, or a prompt, tool, model, retry, session, or reviewer-workflow
    field, in the structured review-boundary runtime modules or the
    review-policy data shape, and fails when this change adds such a condition
    or field to the canonical work-loop skill or its owned references.
  - **VI-1015 (AC-0001, AC-0010, AC-0013):** pack and projection tests prove
    the public invocation and non-review authority surfaces are unchanged and
    generated copies match their source.
  - **VI-1020 (AC-0013):** review-authority isolation fixture drives the legacy
    review gate in a fake Git root under `tmp_path` through the real engine and
    cohort scripts: raw classification, adjudication inspection, review
    recording, and the `reviewers-clean` and `findings-remain` transitions. It
    proves their decisions and resulting state, normalized for run IDs and
    timestamps, are identical with and without the compatibility adapter having
    reconciled the same review events.
  - **VI-1016 (AC-0001–AC-0016):** durable-output review traces the shipped contracts,
    architecture, maintainer procedure, and release entry to their owning tests.
    Release checks prove matching Core pack/plugin versions above main's
    current version, the eval-harness update, and a free-standing changelog
    entry. Record the Highlights decision in the same step: outcome-led bullets
    when consumer capability changes, otherwise a none-verdict with its reason
    in the completion/PR-description evidence. No PR or external action is
    authorized by these local release checks.
- **Grounding:** edit the canonical pack source and regenerate projections per
  repository guidance; do not hand-edit generated copies, change the current
  review procedure, or remove the active legacy plan-lock, review, and
  task/cohort paths.
- **Done when:** VI-1014–VI-1016 and VI-1020 pass, VI-1018 and VI-1019 still pass, and every
  Durable-output map row meets its closeout evidence condition; paired Core
  versions, eval coverage, release entry, and Highlights decision are verified.

## Rollout

- **Delivery:** compatible readers, the compatibility adapter, and shadow
  writers land while the current review path remains authoritative. Moving
  review authority belongs to the review-authority cutover follow-on. Every
  plan, task/cohort, review, and procedure authority remains unchanged.
- **Infrastructure:** none beyond repository-local contract, evidence, review,
  and disposition records supplied by this migration.
- **External-system integration:** none; reviewer implementations remain opaque
  adapters selected by repository policy. Core has no Pi integration or
  dependency in this slice.
- **Deployment sequencing:** start only after Slice 1 closeout freezes the
  implemented contract and service seam while the legacy plan lock remains
  active; land T1–T5 services; run T6 dual-path parity, authority-isolation, and
  crash recovery; then perform the T7 durable-output refresh.

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
- 2026-10-07: spec approved by owner
- 2026-10-07: plan approved by owner
- 2026-10-10: spec approved by owner
- 2026-10-10: plan approved by owner
