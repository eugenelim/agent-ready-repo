# Spec: Structured review boundary

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** brief:acceptance-centered-work-loop
- **Discovery:** none
- **Contract:** `contracts/delivery/` (canonical bundle; Slice 2 review schemas planned)
- **Shape:** service

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

Work-loop maintainers can add or replace a conforming reviewer without changing
delivery policy, while the loop consumes only selected obligations, current
typed reports, actual-failure assessments, and dispositions. The review boundary
is complete when every mandatory obligation has one deterministic result and no
reviewer prompt, tool, model, retry, session, or internal workflow state can
change delivery authority.

## What Changes

- Reviewer selection becomes a deterministic obligation set derived from the
  current review subject and repository policy.
- Reviewer output becomes a versioned structured report carrying its role,
  subject identity, terminal status, and findings.
- Finding validity becomes a current assessment of reachable actual failure;
  unsupported claims do not enter disposition.
- Finding resolution becomes a typed decision that is distinct from the
  acceptance evidence owned by
  [Slice 1](../acceptance-authority-and-evidence/spec.md).
- Existing reviewer outputs cross a compatibility boundary before the new
  review facts can affect delivery readiness.

## Scope and Non-goals

This slice owns review-subject projection, obligation selection, typed reports,
actual-failure assessment, dispositions, the review-to-evidence bridge, and the
compatibility path that preserves current review outcomes until an authorized
review cutover.

It consumes Slice 1's acceptance authority, reviewed-execution envelope,
protected-mutation classification, semantic evidence transaction, delivery
subject, and shared content-safety contracts without redefining them. It does
not introduce mutable task reprojection, remove the legacy plan lock, change
terminal intent, transfer procedure or cohort authority, or import, bundle,
install, or select Pi. It keeps the Core review path self-contained and does
not make `agentbundle` or another repository package a runtime dependency.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Review reports, findings, assessments, and dispositions cross a producer boundary | `contracts/delivery/`, `contracts/README.md`, and `contracts/REGISTRY.md`; review-boundary schemas are authored by this slice and import only the approved Slice 1 shared contracts | Delivery-contract maintainers | JSON Schema 2020-12 validation, a no-copy check, reader/writer compatibility, and synthetic-producer conformance | Every shipped record type has one authoritative schema under `contracts/delivery/`, registered ownership, no schema copy, and bidirectional spec traceability |
| Current architecture | The target review boundary becomes implemented architecture | [`docs/architecture/work-loop-review-disposition.md`](../../architecture/work-loop-review-disposition.md) and [`docs/architecture/acceptance-centered-work-loop.md`](../../architecture/acceptance-centered-work-loop.md) | Platform Core | Implementation mapping and parity evidence match the shipped boundary | Both pages describe the active owner, compatibility path, and remaining cutover state |
| Maintainer procedure | Work-loop policy consumes the new review facts | Canonical work-loop skill source and owned review references | Core pack maintainers | Pack tests and generated-projection checks | Published work-loop guidance contains no reviewer-specific procedure or retired authority |
| Release history | The shipped review boundary changes maintainer-visible behavior | `docs/product/changelog.md` | Release owner | Release entry links the shipped contract and verification | Closeout confirms the release record names the new boundary and its compatibility state |

## Agent Rules

### Always do

- Cite the approved Slice 1 contracts for acceptance identity, the reviewed
  execution envelope, protected-mutation classification, evidence, verdict,
  and shared content safety; do not restate them here.
- Bind obligations, reports, assessments, and dispositions to the current
  review subject and applicable policy identity.
- Keep plan and task-projection provenance outside review-subject identity;
  only a changed acceptance subject or review policy can stale review facts.
- Treat all reviewer-authored fields as untrusted input until the shared
  content-safety and schema-validation boundary accepts the complete report.

### Ask first

- Changing which roles are mandatory, optional, or eligible for an authorized
  waiver.
- Accepting risk for a supported material finding.
- Moving authority from the current review path or changing its reversal window.

### Never do

- Add reviewer-role branches, prompts, tools, model choices, retries, or session
  workflow to work-loop delivery policy.
- Remove the current plan lock, project mutable tasks, reinterpret
  `initial-plan-review.v1` as task approval, or take procedure authority from
  the current engine; Slice 4 owns those changes.
- Import, bundle, install, or select Pi in Core, or make Pi availability part
  of review selection, closure, cutover, or reversal.
- Import `agentbundle` from the Core review runtime or require another
  repository package for review selection, closure, cutover, or reversal.
- Copy a delivery schema outside `contracts/delivery/` or make the Core review
  runtime load a delivery schema instead of validating contract behavior in
  its self-contained code.
- Treat a stale, malformed, forked, missing, or `unable` report as satisfying a
  mandatory obligation.
- Turn opinion, duplication, stale evidence, or a failure already controlled on
  every reachable path into a supported finding.
- Recreate the current adjudicator or review workflow state machine under new
  record names.
- Introduce another top-level package or an external dependency for this slice.

## Testing Strategy

- **Obligation selection and closure (AC-0002, AC-0003, AC-0009):** TDD over the obligation truth table,
  because the same subject and policy must always return the same decision.
- **Report identity and refusal (AC-0004, AC-0005):** TDD over valid, stale, malformed, forked,
  missing, and unknown-version fixtures, because every case has a closed result.
- **Finding assessment and disposition (AC-0006, AC-0007, AC-0008, AC-0014, AC-0015):** TDD over the finding truth table and review-to-evidence bridge lifecycle,
  including positive reachable failures and the four non-blocking negative
  classes, because a wrong classification must make a fixture fail.
- **Reviewer opacity (AC-0001):** goal-based integration check with a synthetic reviewer,
  because success is visible only across selection, report persistence,
  assessment, and review closure.
- **Compatibility (AC-0011):** goal-based integration checks compare projected current
  review outcomes with the structured boundary, because the slice must not
  silently clean or split an acknowledged legacy result.
- **Authority isolation (AC-0013):** goal-based compatibility checks compare the
  active plan-lock, task/cohort, and procedure-authority decisions before and
  after review-boundary wiring, because Slice 2 may move review facts without
  introducing the Slice 4 execution cutover.
- **Policy leakage (AC-0010):** goal-based source check over the canonical work-loop
  policy surface, because reviewer-specific names and mechanics are forbidden
  there regardless of runtime behavior.
- **Report content safety (AC-0012):** TDD through the shared content-safety
  corpus, because an accepted inert report and each whole-report refusal need
  independent positive and negative fixtures.
- **Runtime self-containment (AC-0016):** goal-based clean-environment, import,
  and runtime-read checks over the projected Core review path, because package
  independence and the no-runtime-schema rule are visible only at the complete
  runtime boundary.

## Acceptance Criteria

### Obligation truth table

| Obligation | Current report | Finding state | Review decision |
| --- | --- | --- | --- |
| Mandatory | Valid terminal `clean` report | No findings | Obligation satisfied; no review block |
| Mandatory | Valid terminal `findings` report | Every finding has a current assessment and every supported material finding has a current closing disposition | Obligation satisfied; no review block |
| Mandatory | Valid terminal `findings` report | Any assessment is missing or indeterminate | Obligation unsatisfied; stop for assessment or owner direction |
| Mandatory | Valid terminal `findings` report | A supported material finding is unresolved or has only a repair request | Obligation satisfied; acceptance blocked by the open actual failure |
| Mandatory | Missing, stale, malformed, forked, unknown-major, or `unable` report | Any | Obligation unsatisfied; acceptance blocked |
| Optional | Missing or unusable report | Any | Optional obligation remains unsatisfied and does not block acceptance |
| Waived | Any | A current authorized waiver is bound to the same subject and policy | Obligation is not required and does not block acceptance |
| Waived | Any | Waiver is missing, stale, or unauthorized | The unwaived policy applies; a mandatory obligation remains blocking |

### Finding truth table

| Assessment | Required reason or evidence | Disposition effect |
| --- | --- | --- |
| Supported | Current rule and subject plus evidence for every edge from observation through reachable path to actual failure | A material finding blocks until `accept-risk` or `fixed-by` closes it |
| Unsupported: opinion | No falsifiable delivery failure | No disposition; non-blocking |
| Unsupported: duplicate | The same failure is already represented by a current finding on the same subject | No second disposition; non-blocking |
| Unsupported: stale | Report, rule, evidence, assessment, or subject identity is not current | No disposition; non-blocking |
| Unsupported: controlled elsewhere | Every cited path is already prevented by a current control | No disposition; non-blocking |
| Indeterminate | Available evidence cannot decide a required reachability edge | No disposition; obligation remains unsatisfied and stops for owner direction |

### Disposition truth table

| Disposition | Required current facts | Review and acceptance effect |
| --- | --- | --- |
| `repair-request` | Supported material finding, current subject, and authorized decision maker | Finding remains open; repair and a fresh report are required |
| `fixed-by` | Supported material finding plus a fresh replacement-subject report whose current assessment no longer leaves that failure open | Finding closes for review on the replacement subject |
| `fixed-by` | Replacement report is missing, stale, or bound to the old subject | Finding remains open |
| `accept-risk` | Supported material finding, current subject, evidence, and authorized decision maker | Finding closes for review; Slice 1's contradictory acceptance evidence remains unchanged |
| `accept-risk` | Authority, subject, or evidence is missing or stale | Finding remains open |

### Compatibility corpus

| Current review input | Required structured-boundary result | Acknowledgement rule |
| --- | --- | --- |
| Exact direct-clean report | Current `clean` report | Acknowledge only after both current and structured results exist |
| Conforming findings report with its paired assessment audit | Current `findings` report and current assessments | Acknowledge only after both current and structured results exist |
| Findings report without its required paired assessment audit | `indeterminate` | Do not close the obligation or acknowledge a clean result |
| Schema-invalid or unknown-major report | `unable` | Do not persist a semantic report, close the obligation, or acknowledge the source result |
| Report refused by the shared content-safety policy | `unable` | Do not persist a semantic report, close the obligation, or acknowledge the source result |
| Safe report whose legacy meaning cannot be mapped unambiguously | `indeterminate` | Persist only the validated indeterminate result; do not close the obligation or acknowledge the source result |
| One-sided current or structured write | Reconcile from the source event identity to the missing side | Do not acknowledge until both sides exist |
| Crash before acknowledgement | Replay produces the same paired facts without duplication | Acknowledge once after reconciliation completes |

- [ ] **AC-0001.** A synthetic reviewer that knows only the published reviewer
  contract can satisfy a selected obligation through the generic review
  boundary without a reviewer-specific work-loop change.
- [ ] **AC-0002.** For the same current review subject and policy identity,
  reviewer selection returns the same ordered mandatory, optional, and waived
  obligations through the current-engine compatibility caller and the
  runtime-neutral synthetic adapter corpus, across every plan-only or
  task-projection revision.
- [ ] **AC-0003.** Every row in the Obligation truth table returns its stated review
  decision, and a mutation of any row's report, finding, waiver, subject, or
  policy input returns the row selected by the mutated values.
- [ ] **AC-0004.** The structured-report conformance corpus accepts a current report
  carrying the required version, role, subject, terminal status, lineage, and
  finding fields and rejects each fixture that omits or malforms one required
  field.
- [ ] **AC-0005.** Current-report selection returns the unique safe lineage tip for
  a role and subject; a plan-only or task-projection revision leaves that tip
  current, while a stale acceptance subject, duplicate sequence, or fork leaves
  the obligation unsatisfied.
- [ ] **AC-0006.** Every row in the Finding truth table returns its stated
  assessment class, and the supported row becomes supported only when every
  required reachability edge has controlled evidence.
- [ ] **AC-0007.** Only a current supported material finding enters disposition;
  unsupported findings remain non-blocking and an indeterminate finding stops
  review without entering disposition.
- [ ] **AC-0008.** The disposition truth table treats `repair-request` as open,
  `fixed-by` as closed only when it names a fresh replacement-subject report,
  and `accept-risk` as review closure that does not convert contradictory
  acceptance evidence into support.
- [ ] **AC-0009.** The review result is acceptance-eligible only when every current
  mandatory obligation is satisfied and no supported material finding remains
  open.
- [ ] **AC-0010.** The canonical work-loop policy surface contains no reviewer-role
  condition and no field for prompts, tools, models, retries, sessions, or
  reviewer workflow state.
- [ ] **AC-0011.** Every row in the closed Compatibility corpus produces its
  required structured-boundary result and acknowledgement decision; no input
  class outside that table is admitted by the Slice 2 compatibility path.
- [ ] **AC-0012.** The shared content-safety corpus accepts inert bounded reviewer
  prose and rejects a complete report containing protected data, an oversized
  field, or authority-shaped executable content before any semantic review
  record is persisted.
- [ ] **AC-0013.** Slice 2 compatibility and review-cutover fixtures leave the
  active legacy plan lock, task/cohort writer, and procedure authority
  unchanged; no Slice 2 path treats `initial-plan-review.v1` as task approval
  or admits mutable task reprojection.
- [ ] **AC-0014.** A current supported finding assessment atomically emits one
  deterministic Slice 1 `review-failure` evidence receipt per affected
  criterion in the same semantic evidence transaction as the assessment; a
  crash exposes both the assessment and its complete receipt set or neither.
- [ ] **AC-0015.** When a source report or supported assessment ceases to be
  current, the review bridge atomically supersedes every receipt derived from
  that source, leaving no live `review-failure` receipt from a non-current
  report or assessment.
- [ ] **AC-0016.** The projected Core review path completes the synthetic
  reviewer and compatibility corpus when `agentbundle` and other repository
  packages are unavailable; its runtime modules import only the Python standard
  library or sibling `work-loop` modules, and the run opens no file under
  `contracts/delivery/`.

## Follow-ons

none

## Terminal Intent

`code` — after approval, implement only the Slice 2 review boundary and its
authorized review-path compatibility or cutover work.

## Accepted Risk

none

## Assumptions

none
