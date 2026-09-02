# RFC-0096: Portable delivery-artifact lifecycle

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-23
- **Date closed:** 2026-08-23
- **Decision weight:** heavy
- **Related:** [RFC-0083](0083-work-intake-and-artifact-routing.md);
  [RFC-0093](0093-intent-scoped-completion.md);
  [RFC-0094](0094-direct-light-execution-without-durable-planning-artifacts.md);
  [ADR-0077](../adr/0077-feature-projection-and-tracker-authority.md);
  [ADR-0078](../adr/0078-standalone-intake-and-deterministic-workspace-index.md)

## Reviewer brief

- **Decision/outcome:** Accept role-based temporary specs/plans, portable
  resolution, extracted closeout, immediate disposal, and optional cooling.
- **Scope/stakes:** Seven waves affect handoff through status; deletion remains
  confirmed and fail-closed, with committed in-repository files version-recoverable.
- **Not in scope:** Implementing a wave, prescribing product-document information
  architecture, or imposing a path, format, tracker, or configuration file.

## The ask

Temporary does not mean uncommitted: specs/plans may remain through Paused or
Implementing; closeout later routes lasting information and ends authority.

| ID | Question | Decision |
| --- | --- | --- |
| D1 | Destinations? | Resolve repository evidence; ask on ambiguity or absence. |
| D2 | What survives? | Owned current truth, rationale, docs, interfaces, operations, and learning. |
| D3 | Who closes? | Future `close-work`, not `work-loop`. |
| D4 | Default? | Confirmed immediate disposal when no lasting fact or obligation remains. |
| D5 | Cooling? | Completion plus 30 calendar days; review never grants authority. |
| D6 | Workspace? | Active coordination/dependencies, not truth, history, or cooling. |

## 1. Problem and goals

Core currently treats one catalogue layout as canonical and preserves shipped
specs and plans as frozen history. That fails without shaping, with external
authority or custom layouts, or when nothing in an artifact should remain. It
also blurs shaped intent with current product truth and design with architecture.

The goals are to make core portable; find repository-owned and
external surfaces without relocation; support committed, queued, and
cross-session delivery; route lasting information before retirement; permit
immediate disposal, an exact 30-day cooling period, and exceptional retention;
and remove shipped artifacts from ordinary orientation. RFCs and architecture
decision records (ADRs) remain decision history outside this lifecycle.

Here, **core** is the core pack; **direct-light** is work without
a persisted spec/plan; **ordinary orientation** is context loaded by default at
session start; a **locator** identifies an artifact without assuming a path; and
a **completion receipt** is minimal evidence that a dependency's outcome landed.

This RFC does not require permanent feature documentation, define product-doc
content or navigation, govern other surfaces' retention, or require
`workspace.toml`, `agentbundle-layout.toml`, Markdown, or catalogue directories.

## 2. Semantic surface model

A semantic surface is a role, not a filename. Product shaping selects a bet and
may retain evidence under its own policy; a **delivery brief** coordinates slices;
a **delivery contract** (usually a spec) defines one outcome, while its plan is
mutable execution strategy.

Other roles are separate: **current product truth** states the promise and
boundaries; **user documentation** explains use; **product history** records
evolution when justified; **release history** records what shipped and when;
**current architecture** governs the system as it is; an **architecture design**
proposes change; **decision records** preserve why; **operations** owns runbooks;
**interface contracts** own compatibility; and **project knowledge** owns
reusable learning. Runtime and handoff state only coordinates execution.

Durable roles follow their own policies. Architecture design is not automatically
durable or subject to spec/plan cooling; its workflow updates current architecture
and decisions or dispositions the proposal.

“Feature document” is not a role: resolve it to product truth, user docs,
product/release history, interface reference, or delivery contract. A multi-role
artifact is distilled, retained by exception, or accepted by a durable owner as
`Reclassified`: delivery authority ends without deletion. This routing result is
not a seventh disposition. Coordination-only briefs follow delivery; product
evidence follows product policy.

## 3. Optional shaping and core-intake contract

`product-engineering` remains optional. Shaping may hand core the outcome,
boundaries and non-goals, assumptions and evidence, dependencies, source locator
and revision, authority, design context, and unresolved delivery questions.
This is a data contract, not a pack or format dependency.

Core does not repeat discovery because another source authored useful work. If
shaping is absent or declined, core classifies the request. External authority
stays external at a pinned revision; implementing contracts reject unattended
refresh. Later deltas are reviewed or become new intake.

## 4. Repository-surface resolution

Every requested surface uses one precedence order:

1. an explicit destination for this work;
2. declared repository policy or configuration;
3. an established in-repository convention;
4. an established external destination;
5. ambiguity, which requires confirmation;
6. absence, which produces an offer to select or create a destination.

Precedence chooses among policy-permitted destinations; an explicit destination
that violates mandatory repository policy is rejected, not treated as an override.

Root and scoped agent guidance route to owning sources, not a mandatory map.
Documented policy and enforced primitives establish conventions. Repetition is
inference until confirmed; one example is insufficient. Contradictions fail
closed. Structural discovery is bounded to one or two analogues and tests.

The resolver returns role; logical and physical locator; provenance and evidence
strength; availability, writability, and confinement; source and deletion
authority; revision or fingerprint; and confirmations. Local paths must
realpath-resolve inside the repository; external locators stay external.

Current configuration is insufficient as a universal registry. Wave 1 adds an
optional locator extension: workspace entries may
carry a surface role and non-path locator while retaining legacy `path` support,
and repository-specific configuration adapters may populate the same result.
No configuration file or global `[surfaces]` registry is required.

## 5. Closeout and disposition model

A spec-backed delivery contract declares expected durable outputs by semantic
role and resolved destination; the plan maps tasks and verification to them.
Direct-light carries the decision in session, but must finish or promote through
intake before pausing. Applicable durable outputs normally land with implementation;
external cadence may leave an owned follow-up, never unnamed residue.

The normalized lifecycle does not replace repository metadata:

| Lifecycle phase | This repository's projection |
| --- | --- |
| Drafting | spec `Draft`; plan `Drafting`; brief draft or not yet indexed |
| Ready | spec/plan `Approved`; build queue ready |
| Implementing | spec `Implementing`; plan `Executing`; work active |
| Paused | activity flag over Ready or Implementing; artifact status is unchanged |
| Closeout-pending | spec `Shipped`; plan `Done`; no closeout receipt yet |
| Post-closeout | `Cooling`, `Retained`, `Retired`, `Reclassified`, or `ExternalAdvisory` lifecycle record |

`close-work` verifies intent, outputs, obligations, and dependencies; routes
current facts, decisions, and learning to their owners; and dispositions the
rest rather than archiving whole artifacts. Abandoned or superseded work also
closes, but uses immediate, exceptional, or advisory—not post-ship—disposition.

Disposition is intent, not deletion permission. Source, write, and deletion
authority differ. Policy may select an eligible class, but every deletion needs
fresh authorized human confirmation bound to locator, fingerprint, disposition,
evidence, and authority; drift expires it.

| Disposition | Eligibility | Authority, action, and blocker |
| --- | --- | --- |
| `discard-local` | In-memory/tool-owned temporary state | Discard; file removal still needs confirmation. Persisted/lasting content blocks. |
| `delete-before-push` | Never sent remotely | Confirm removal before push; prior push forces reselection. |
| `delete-before-merge` | Removal change not yet integrated | Confirm removal before that change merges; prior delivery uses an ordinary follow-up deletion, never history rewriting. |
| `cool-30-days` | Delivered, closed, persistent record | Confirm enrollment; day 30 needs fresh human confirmation; uncertainty retains. |
| `retain-exception` | Longer obligation | Record reason, owner role, review date; do not delete. |
| `external-advisory` | No external deletion authority | Report only. With explicit authority, an adapter applies another disposition and still requires fresh confirmation. |

Immediate disposal is the default recommendation—not automatic action—when no
lasting fact or obligation remains. Committed deletion removes files from the
current tree through an ordinary change, never by rewriting Git history.

## 6. Thirty-day cooling and retention

**Intent completion** satisfies the outcome; the **delivery-completion event** is
selected merge/release/acceptance evidence; **closeout completion** settles
routing/disposition; initiative completion settles every child and residual.
Only delivered work cools. Policy selects the event; absent policy, `close-work`
asks and cannot enroll without an answer. Creation, Ready, edits, and session end
never start the clock.

`review_on` is exactly 30 calendar days after `completed_on` in the recorded
timezone. Late closeout preserves the selected event date, so an already-due
record is immediately reviewable without authorizing deletion.

Lifecycle state records ID, locators/fingerprints, disposition, completion
evidence/date, timezone, review date, source/write/delete authority facts, and
non-personal confirmation proof; exceptions add reason and owner role. It
excludes requirements, personal identities, and rationale.
Though temporary, it persists across sessions in a resolved tracker,
metadata, lifecycle store, or adjacent record. `workspace.toml` may point, never
own. Missing writable state fails closed; external claims are revalidated.

Identity uses logical IDs and content fingerprints, not commit topology, so
squash, merge, rebase, and shallow history remain workable. Renames update the
locator while retaining identity and prior aliases. Missing history, fingerprint
drift, unresolved references, or uncertain authority blocks deletion. Source
authority over an external spec never implies deletion authority; local plans
have independent dispositions.

Day-30 review rechecks completion, outputs, active use, obligations, identity,
and authority. Approval retires; refusal/uncertainty creates a reasoned, owned,
dated exception. Status or an external system signals due state; a human invokes
`close-work` retirement mode. The same mechanism signals exception review; its
owner may confirm immediate deletion, renew retention with a new date, choose
eligible cooling, or select advisory treatment. Day 30 never auto-deletes.

Immediately before mutation, deterministic helpers re-resolve and confine every
target, match its fingerprint, refuse escaping symlinks and implicit directory
deletion, and enumerate only explicitly confirmed regular files. Confirmation
expires on any mismatch.

## 7. Workflow ownership

- `product-engineering` optionally owns shaping and handoff.
- `work-intake` normalizes sources, resolves surfaces, and selects routing.
- `work-loop` implements, verifies, reviews, and returns completion evidence;
  `close-work` alone marks Closeout-pending and Post-closeout.
- future `close-work` owns closeout, initiative closure, disposition, cooling, and retirement.
- `workspace-status` projects state but never distils or deletes.
- project knowledge receives reusable learning through its own gate.
- deterministic helpers resolve, confine, fingerprint, date, and report eligibility; workflows own policy and confirmation.

`workspace.toml`, when present, projects two rooms. Intake places unresolved
outcomes in shaping; a selected bounded slice with a pinned delivery-source
locator graduates to build. Direct-light bypasses both rooms only for same-session
execution; queuing or pausing promotes it through intake. `work-loop` moves Ready
to Implementing. Pause is an overlay persisted in a resolved repository or
external coordination surface and restored on resume; if none is writable, the
workflow offers one and cannot silently claim resumability. Closeout removes the
live entry and keeps `{delivery_id, outcome, completion_event, evidence_ref}` only
while a live dependency cites it. Cooling stays outside ordinary orientation and
is retrieved only for explicit history, regression investigation, or retirement
review; status and default orientation must not load its contents.

When an initiative completes, closeout proves the accepted outcome, settles
remaining shaping and build entries, and removes or compacts the active section.
No permanent initiative shell or shipped-spec list remains by default. A
completion receipt remains only while live downstream work depends on it. Any
lasting initiative history resolves to an established roadmap, release, product,
governance, or external-tracker surface; absent one, the workflow offers a
choice rather than silently creating it.

Trackers normally own assignment, priority, schedule, status, discussion, and
cross-team coordination; repositories normally own code-coupled truth. Either
may own product or delivery facts when declared. Tracker writes need separate
adapter authority. Closed items are coordination history, not current truth.

## 8. Adopter portability and migration

The normalized roles, locator result, lifecycle record, and authority rules are
portable contracts rather than catalogue paths. Other agents, IDEs, trackers,
layouts, and spec formats can produce and consume them. Repositories without
durable adaptation use bounded discovery each time; repositories with good
routing reuse it. No suitable durable surface is created silently.

Migration is forward and fail-closed. Existing artifacts retain current treatment
until Wave 7 classifies them; legacy `path` remains valid. Nothing is bulk-deleted:
migration proves outputs, dependencies, authority, and disposition. Ambiguity
becomes an owned, dated `retain-exception`.

The representative cases resolve as follows: a shaped multi-slice outcome keeps
one handoff and several temporary contracts; a raw bounded request uses direct
light or a core-authored contract; an external spec stays external and pinned;
custom locations win through resolution; a user-facing feature updates user
docs without inventing architecture; a boundary change updates architecture and
an ADR without inventing product prose; paused work retains committed contracts
across sessions without starting cooling; and a spec containing lasting product
truth is distilled or reclassified before retirement.

## 9. Initiative waves

### Wave 1 — Shared semantic-surface resolver

Objective: semantic resolver and confinement helpers. Dependency: none.
Behavior: honor explicit, repository, custom, and external destinations.
Non-goals: lifecycle mutation or mandatory config. Evidence: locator/evidence
fixtures. Impact: additive contract and optional fields. Parallelism: none.

### Wave 2 — Product-engineering and core-intake integration

Objective: optional shaping handoff and content routing. Dependency: Wave 1.
Behavior: core reuses upstream/external work and works alone. Non-goals: shaping
retention and closeout. Evidence: intake fixtures with/without the pack. Impact:
prompt/template compatibility. Parallelism: Wave 3.

### Wave 3 — Architecture and ADR destination portability

Objective: portable design, architecture, and ADR surfaces. Dependency: Wave 1.
Behavior: adopter locations win; design stays distinct. Non-goals: method
redesign. Evidence: custom-location/boundary fixtures. Impact: prompt/guide
migration. Parallelism: Wave 2.

### Wave 4 — Close-work extraction and immediate disposition

Objective: `close-work`, output planning, initiative closure, and immediate
dispositions. Dependencies: Waves 1–3. Behavior: `work-loop` hands off evidence.
Non-goals: timed retirement/migration. Evidence: closeout and pause fixtures.
Impact: new workflow/doctrine. Parallelism: not Wave 5.

### Wave 5 — Thirty-day cooling and retirement engine

Objective: lifecycle adapters, dates, identity, exceptions, and retirement.
Dependency: Wave 4. Behavior: exactly 30 days; never auto-delete. Non-goals:
status/migration. Evidence: time, topology, external, and authority fixtures.
Impact: helper and persistent schema. Parallelism: not Waves 4 or 6.

### Wave 6 — Workspace-status projection and context exclusion

Objective: status projection and context exclusion. Dependencies: Waves 4–5.
Behavior: show closeout, due reviews, and exceptions. Non-goals:
distillation/deletion, and the dependency-scoped completion receipt, which
moves to Wave 7 — the lifecycle record carries no `outcome` field, so
projecting the four-field receipt needs a schema answer this wave does not
have. Evidence: authoritative projections never dispatch cooling work. Impact:
status compatibility. Parallelism: after Wave 5.

### Wave 7 — Historical migration and pruning

Objective: classify history, prune proven-eligible artifacts, and project the
dependency-scoped completion receipt from its coordination surface.
Dependencies: Waves 1–6. Behavior: reviewed plans, no bulk deletion, explicit
exceptions, and a four-field receipt once `outcome` has a source.
Non-goals: history rewrite/product-doc reorganization. Evidence: dry-run,
semantic samples, dependency proof, confirmations, orientation. Impact: large
separate release. Parallelism: none.

## 10. Risks and revisit conditions

The riskiest assumption—role plus locator covers custom and external repositories—
survived eight cases; Wave 1 fixtures are its falsification gate. Authority,
fingerprints, and confirmation mitigate deletion; receipts preserve dependencies.

Revisit if adopters cannot distinguish delivery from current truth, bounded
discovery needs mandatory config, product history is lost after clean closeout,
or cooling state fails across sessions. Until then ambiguity retains.

Rejected: permanent spec archives, deletion at every merge, `workspace.toml` as
lifecycle database, and more finish policy in `work-loop`; each breaks an
authority, obligation, portability, or ownership constraint.

Kubernetes ties feature documentation to release readiness, supporting output
planning
([documentation for a release](https://kubernetes.io/docs/contribute/new-content/new-features/)).
arc42 separates current architecture from rationale and excludes short-lived
information
([building blocks](https://docs.arc42.org/section-5/),
[decisions](https://docs.arc42.org/section-9/),
[short-lived information](https://docs.arc42.org/tips/5-24/)). NARA supports
event-based retention and authorized disposition; we borrow its control shape,
not federal obligations
([records scheduling](https://www.archives.gov/records-mgmt/scheduling/sch-records/)).

## Follow-on artifacts

Follow-on waves create artifacts; RFC-0096 remains
the blueprint, not a tracker.

## Errata

This RFC is Accepted: the body above is preserved as the original decision
record. Corrections are appended here, Approver-signed.

- **2026-08-27 (Approver: eugenelim) — Material post-seal contract amendment
  uses guarded baseline replacement.**

  RFC-0099 section 7 defines the material case: a spec or plan correction after
  sealing parks delivery, preserves and invalidates the old baseline, returns
  to spec-plan drafting, and requires full reapproval and resealing. This is
  not RFC-0096's ordinary normalized `Paused` state, whose artifact statuses
  remain unchanged. The ordinary `Paused` rule and governance-outside-rollup
  holding remain authoritative.

- **2026-09-01 (Approver: eugenelim) — Wave 7 ships as four owned slices.**

  RFC-0096 section 9 scoped Wave 7 as one release, but its objective names
  neither follow-on closed by this first slice. Wave 7a-i closes cooling scope
  through `cooling-scope-closure`; Wave 7a-ii projects the completion receipt;
  Wave 7b classifies history; and Wave 7c prunes proven-eligible artifacts. The
  still-open `rfc0096-wave7a-ii-completion-receipts` is owned by Wave 7a-ii,
  `rfc0096-wave7b-historical-classification` is owned by Wave 7b, and
  `rfc0096-wave7c-pruning` is owned by Wave 7c.

  The Wave 6 Follow-ons entries `cooling-closeout-eligibility` and
  `cooling-repair-migration-scope` are both closed by cooling-scope-closure.
  This closure also accepts the residual Wave 6 named: a lifecycle record that
  reads cleanly moves an initiative toward an affirmative closeout
  recommendation without being verified against its artifact.

  Wave 6's `cooling-brief-child-scope` entry misattributes its constraint to
  that spec's own AC46 pinned pair. The finding-code documentation gate is a
  superset check that admits any documented code, so a third code was always
  available; the real open question is attribution breadth. That follow-on
  stays open and is owned by Wave 7b.

  Wave 6 registered the receipt work as
  `wave6-dependency-scoped-completion-receipts`; it is registered here as
  rfc0096-wave7a-ii-completion-receipts.
