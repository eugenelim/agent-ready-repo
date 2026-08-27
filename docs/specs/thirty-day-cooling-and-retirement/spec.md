# Spec: Thirty-day cooling and retirement

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096 §6 and §9; `close-work-extraction-and-immediate-disposition` (Shipped, live dependency); `semantic-surface-resolver` (Shipped)
- **Brief:** none
- **Discovery:** none
- **Contract:** [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer enrols one delivered, closed delivery artifact into a thirty-day
cooling period, and thirty days later a human invokes `close-work` to review it.
Wave 5 computes `review_on` as exactly thirty calendar days after the selected
delivery-completion event in the recorded timezone, persists a bounded lifecycle
record next to the artifact it governs, answers whether that record is due, and
verifies the artifact's identity from its logical ID and content fingerprint
rather than from commit topology. Day-30 review rechecks completion, outputs,
active use, obligations, identity, and authority; approval retires the record and
refusal or uncertainty creates a reasoned, owned, dated exception. Being due
authorizes nothing: day 30 never auto-deletes, and an approved deletion runs
through Wave 4's unchanged preview, confirmation, and effect seams. Wave 5 adds
no scheduler, daemon, or background job; no second resolver or fingerprint
helper; and no dependency. Workspace-status projection, ordinary-context
exclusion, historical migration, and pruning remain absent.

## Durable Outputs

| Semantic role | Applicability and resolved destination | Owner and closeout evidence |
| --- | --- | --- |
| `decision-record` | Applicable: [`docs/rfc/0096-portable-delivery-artifact-lifecycle.md`](../../rfc/0096-portable-delivery-artifact-lifecycle.md) at `6e984d67b583b36798efddbb2717ce5784572a49` | The accepted RFC owns cooling policy and rationale; Wave 5 adds no ADR. Closeout verifies the pin. |
| `interface-contract` | Applicable, new exact target: [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json) | Owns the persistent record's field set and the excluded fields. Closeout verifies the shipped writer and reader validate against it. |
| `current-architecture` | Applicable: [`docs/architecture/work-intake-and-artifact-routing.md`](../../architecture/work-intake-and-artifact-routing.md) | Owns where cooling state lives, who may write it, and the Wave 6/7 boundary. Closeout requires a whole-surface read against shipped behaviour. |
| `user-documentation` (how-to) | Applicable: [`guides/core/how-to/close-and-disposition-work.md`](../../../guides/core/how-to/close-and-disposition-work.md) | Owns the maintainer's enrol, check-due, and day-30 review task. Closeout verifies the `cool-30-days` row no longer claims classification only. |
| `user-documentation` (reference) | Applicable: [`guides/core/reference/work-intake-routing-and-lifecycle.md`](../../../guides/core/reference/work-intake-routing-and-lifecycle.md) | Owns the public disposition-result table and the remaining Wave 6/7 boundary. Closeout verifies the table header and the `cool-30-days` row. |
| `user-documentation` (workspace reference) | Applicable: [`guides/core/reference/workspace-toml-schema.md`](../../../guides/core/reference/workspace-toml-schema.md) | Owns the statement that `workspace.toml` points at cooling state and never owns it. Closeout verifies no cooling schema entered the file. |
| `user-documentation` (navigation) | Applicable: [`packs/core/README.md`](../../../packs/core/README.md) | Owns terse discovery of the cooling capability. Closeout verifies navigation without copied implementation detail. |
| `release-history` | Applicable: [`docs/product/changelog.md`](../../product/changelog.md) | Owns the shipped Core capability after the pack version settles. Closeout verifies the topmost dated `[core]` heading equals `packs/core/pack.toml`. |
| `project-knowledge` | Conditional and intentionally unresolved until implementation produces reusable learning: route through the existing `project-knowledge --capture` gate | No placeholder is created. Closeout requires either an explicit `not applicable—no reusable learning` finding or an accepted gate receipt. |

### Capability and delivery evidence

Implementation, tests, and gate results are the capability-proof layer, not a
semantic durable-output role. This Wave 5 delivery is a live dependency for
RFC-0096 Wave 6 and Wave 7: its spec and plan stay available until those waves
settle. Wave 4's spec and plan remain a live dependency of this wave and are not
disposed of here.

## Boundaries

### Always do

- Compute `review_on` from calendar dates in the recorded IANA timezone, never
  from an elapsed-hours interval.
- Take the current instant as an explicit timezone-aware argument at every seam
  that needs it. No Wave 5 module reads the system clock.
- Establish artifact identity from the logical delivery ID and the content
  fingerprint produced by the blessed
  `file_safety.sha256_confined_regular_file` helper.
- Resolve the lifecycle-record surface through the shipped Wave 1 resolver
  before reading or writing it, and fail closed when it is absent, unconfined,
  or not writable.
- Treat every persisted record, external claim, and model-proposed locator,
  date, timezone, authority fact, or confirmation as bounded untrusted data and
  revalidate it at the deterministic seam that acts on it.
- Keep source, write, and deletion authority independent, and refuse when any is
  unknown or contradictory.
- Route an approved deletion through Wave 4's existing `preview_deletion`,
  `confirm_deletion`, and `apply_confirmed_deletion` seams unchanged.

### Ask first

- Ask before changing the record's field set, the excluded-field rule, the
  resolved record destination, or the selected delivery-completion event.
- Ask before accepting a retained exception's reason, owner role, and review
  date, or renewing one.
- Ask before adding a second lifecycle adapter, a dependency, a configuration
  file, a registry, or a top-level directory.

### Never do

- Never auto-delete on day 30, on elapsed time, on a status change, on session
  end, or after a passing review.
- Never treat a due record as deletion permission, and never let a prior review
  substitute for fresh confirmation.
- Never add a scheduler, daemon, cron entry, background job, or wake-up hook.
- Never derive identity, dueness, or eligibility from commit topology, branch
  shape, reflog, or history depth.
- Never persist requirements, personal identity, or rationale in the lifecycle
  record.
- Never let `workspace.toml` own cooling state; it may hold a pointer only.
- Never add a second semantic-surface resolver, a second fingerprint helper, a
  weaker path check, or a new runtime dependency.
- Never implement workspace-status projection, ordinary-context exclusion,
  historical migration, or pruning.

## Testing Strategy

- **Date and dueness arithmetic: TDD.** The clock is an injected argument, so
  DST transitions, a reader in a different timezone, a leap day, late closeout,
  and days 29/30/31 are ordinary table cases over pure functions.
- **Record schema and refusals: TDD.** A closed field set, strict parse, and
  each fail-closed refusal are compressible rules with stable codes.
- **Identity across history shapes: goal-based fixtures over real Git.** Temporary
  repositories perform a squash merge, a merge commit, a rebase, and a
  `--depth=1` shallow clone of the same logical artifact; a fifth fixture deletes
  `.git` entirely. Git is never mocked, because a fixture cannot testify about
  the thing it mocks.
- **Persistence and confinement: TDD with real filesystem fixtures.** Confined
  temporary repositories exercise the resolved destination, an unwritable
  surface, an escaping symlink, and a cross-session reload.
- **Review outcomes: TDD.** Approval, refusal, and each uncertain recheck are a
  finite decision table with stable result codes and an asserted empty mutation
  trace.
- **Doctrine and boundary agreement: goal-based checks.** The five updated
  pointers, the amended Wave 4 roster boundary test, catalogue lint and verify,
  self-host regeneration, and the site and link gates prove the source doctrine
  and every projection agree.

## Acceptance Criteria

- [ ] **AC1 — `review_on` is thirty calendar days.** For a record whose
  `completed_on` is a date in a recorded IANA timezone, `review_on` equals that
  date plus thirty calendar days.
- [ ] **AC2 — A DST transition does not move `review_on`.** A `completed_on`
  whose thirty-day window contains a spring-forward or fall-back transition in
  the recorded zone yields the same `review_on` as one that contains neither.
- [ ] **AC3 — Dueness is evaluated in the recorded zone.** Two readers whose
  local zones differ from the recorded zone and from each other receive the same
  dueness answer for the same record and the same instant.
- [ ] **AC4 — A leap day counts as one calendar day.** A window spanning 29
  February yields `review_on` thirty calendar days after `completed_on`.
- [ ] **AC5 — Day 29 is not due; days 30 and 31 are.** Dueness flips at local
  midnight on `review_on` in the recorded zone.
- [ ] **AC6 — Late closeout preserves the event date.** Enrolling with a
  `completed_on` already more than thirty days in the past yields a record that
  is immediately due.
- [ ] **AC7 — Due grants no permission.** A due record returns no deletion
  permission and an empty mutation trace.
- [ ] **AC8 — The clock is injected.** Every seam that needs the current instant
  accepts it as a timezone-aware argument; a naive argument refuses, and no Wave
  5 module reads the system clock.
- [ ] **AC9 — Only delivered work enrols.** Enrolment refuses work that is not
  delivered, not closed, or has no persistent record.
- [ ] **AC10 — Enrolment needs a selected completion event.** Absent a policy
  selection, enrolment refuses with a stable code rather than choosing an event.
- [ ] **AC11 — Only the completion event starts the clock.** Creation, reaching
  Ready, editing an artifact, and ending a session each refuse to enrol.
- [ ] **AC12 — The record carries exactly the §6 field set.** It holds ID,
  locator and aliases, fingerprint, disposition, completion evidence and date,
  timezone, review date, independent source/write/delete authority facts, and
  non-personal confirmation proof; an exception adds reason and owner role. Any
  other key refuses the write.
- [ ] **AC13 — Requirements, identity, and rationale are excluded.** A write
  carrying requirement text, personal identity, or rationale refuses with zero
  effects.
- [ ] **AC14 — Missing writable state fails closed.** An absent, unconfined, or
  read-only resolved destination refuses enrolment and review rather than
  degrading to memory.
- [ ] **AC15 — External claims are revalidated.** A completion date, timezone,
  fingerprint, or authority fact arriving from outside the repository is
  re-derived or re-checked at the seam before it is persisted or acted on.
- [ ] **AC16 — Identity survives every history shape.** The same logical
  artifact verifies after a squash merge, a merge commit, a rebase, and a
  `--depth=1` shallow clone, and verifies with `.git` removed entirely.
- [ ] **AC17 — A rename updates the locator and keeps prior aliases.** After a
  rename the record's locator is the new path and the previous locator is
  retained as an alias.
- [ ] **AC18 — Four conditions block deletion.** Missing history, fingerprint
  drift, an unresolved reference, and uncertain authority each block deletion
  with a distinct stable code.
- [ ] **AC19 — Source authority never implies deletion authority.** A record
  whose source authority covers an external spec and whose deletion authority is
  absent blocks deletion.
- [ ] **AC20 — Day-30 review rechecks six things.** Review requires an explicit
  answer for completion, outputs, active use, obligations, identity, and
  authority; a missing answer refuses.
- [ ] **AC21 — Approval retires.** A review whose six answers all approve returns
  a `Retired` result.
- [ ] **AC22 — Refusal or uncertainty creates an exception.** Either outcome
  returns a `retain-exception` record carrying a bounded reason, an owner role,
  and a human-supplied review date.
- [ ] **AC23 — Day 30 never deletes.** No Wave 5 seam removes a file; an approved
  deletion is performed only by Wave 4's unchanged `preview_deletion`,
  `confirm_deletion`, and `apply_confirmed_deletion`.
- [ ] **AC24 — The record persists across sessions.** A record written in one
  process is loaded byte-equivalently in another, and `workspace.toml` gains no
  cooling schema.
- [ ] **AC25 — One adapter, no new machinery.** Wave 5 adds no second resolver,
  no second fingerprint helper, no scheduler or background job, and no runtime
  dependency; the shipped Wave 1 resolver and `file_safety` module are unchanged.
- [ ] **AC26 — The five current-behaviour pointers now state Wave 5.** The
  how-to, the lifecycle reference table header and `cool-30-days` row, the
  workspace schema reference, and the pack README no longer say cooling stops at
  classification.
- [ ] **AC27 — The Wave 6 and Wave 7 boundaries remain provable.** The amended
  Wave 4 roster boundary test still fails if a changed doctrine surface claims
  workspace-status projection, ordinary-context exclusion, migration, or pruning.

## Assumptions

- Technical: the lifecycle record resolves to `docs/specs/<slug>/lifecycle.json`
  as the RFC §6 "adjacent record"; this repository has no pre-existing writable
  surface that owns delivery-lifecycle state, so §4 rung 6 applies. (source: user
  confirmation 2026-08-27)
- Technical: `runtime-coordination` is the applicable existing resolver role, so
  `surface_resolver.py` and its published contract are unchanged and their pinned
  digests hold. (source: `packs/core/.apm/skills/work-intake/scripts/surface_resolver.py`)
- Technical: `datetime`, `date`, `timedelta`, and `zoneinfo` are stdlib on the
  supported Python floor; none of `dateutil`, `pendulum`, `arrow`, or `pytz` is
  installed or needed. (source: repository dependency check 2026-08-27)
- Technical: Wave 4's `preview_deletion` / `confirm_deletion` /
  `apply_confirmed_deletion` seams already implement confirmed deletion, so
  Wave 5 adds no deletion path. (source: `packs/core/.apm/skills/close-work/scripts/close_work.py`)
- Technical: the project-knowledge store is not extended, because it owns
  reusable learning and its capture contract cannot carry a locator, fingerprint,
  or authority record that excludes rationale. (source: `packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py`)
- Product: Wave 5 covers dates, identity, persistence, exceptions, and
  retirement; workspace-status projection and context exclusion are Wave 6, and
  migration and pruning are Wave 7. (source: RFC-0096 §9)
- Process: Wave 5 depends on Wave 4 only and runs alone; Wave 4's spec and plan
  are retained as a live dependency. (source: RFC-0096 §9; user instruction
  2026-08-27)

## Changelog

- 2026-08-27: Opened.
