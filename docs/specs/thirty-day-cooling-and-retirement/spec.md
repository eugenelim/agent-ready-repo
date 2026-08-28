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
record in a resolved, confirmed destination, answers whether that record is due,
and verifies the artifact's identity from its logical ID and content fingerprint
rather than from commit topology. Day-30 review rechecks completion, outputs,
active use, obligations, identity, and authority; approval retires the record,
refusal or uncertainty creates a reasoned, owned, dated exception, and that
exception is itself reviewable. Being due authorizes nothing: day 30 never
auto-deletes, and an approved deletion runs through Wave 4's unchanged preview,
confirmation, and effect seams. Wave 5 adds no scheduler, daemon, or background
job; no second resolver or fingerprint helper; and no dependency.
Workspace-status projection, ordinary-context exclusion, historical migration,
and pruning remain absent.

## Durable Outputs

| Semantic role | Applicability and resolved destination | Owner and closeout evidence |
| --- | --- | --- |
| `decision-record` | Applicable: [`docs/rfc/0096-portable-delivery-artifact-lifecycle.md`](../../rfc/0096-portable-delivery-artifact-lifecycle.md) at `6e984d67b583b36798efddbb2717ce5784572a49` | The accepted RFC owns cooling policy and rationale; Wave 5 adds no ADR. Closeout verifies the pin. |
| `interface-contract` | Applicable, new exact target: [`contracts/jsonschema/delivery-lifecycle-record.schema.json`](../../../contracts/jsonschema/delivery-lifecycle-record.schema.json) | Owns the persistent record's field set, its bounds at every level, and the excluded fields. Closeout verifies the shipped writer and reader validate against it and that it carries `x-spec`. |
| `runtime-coordination` | Applicable, new exact target: `docs/lifecycle/` with its `README.md` | Owns the destination this repository resolves for cooling records. Closeout verifies the directory is the confirmed candidate and that no other writer touches it. |
| `current-architecture` | Applicable: [`docs/architecture/work-intake-and-artifact-routing.md`](../../architecture/work-intake-and-artifact-routing.md) | Owns where cooling state lives, who may write it, and the Wave 6/7 boundary. Closeout requires a whole-surface read against shipped behaviour, including its "Last verified surface" section. |
| `user-documentation` (how-to) | Applicable: [`guides/core/how-to/close-and-disposition-work.md`](../../../guides/core/how-to/close-and-disposition-work.md) | Owns the maintainer's enrol, check-due, and day-30 review task. Closeout verifies the `cool-30-days` row no longer claims classification only. |
| `user-documentation` (reference) | Applicable: [`guides/core/reference/work-intake-routing-and-lifecycle.md`](../../../guides/core/reference/work-intake-routing-and-lifecycle.md) | Owns the public disposition-result table and the remaining Wave 6/7 boundary. Closeout verifies the table header and the `cool-30-days` row. |
| `user-documentation` (workspace reference) | Applicable: [`guides/core/reference/workspace-toml-schema.md`](../../../guides/core/reference/workspace-toml-schema.md) | Owns the statement that `workspace.toml` points at cooling state and never owns it. Closeout verifies no cooling schema entered the file. |
| `user-documentation` (navigation) | Applicable: [`packs/core/README.md`](../../../packs/core/README.md) | Owns terse discovery of the cooling capability. Closeout verifies navigation without copied implementation detail. |
| `user-documentation` (workflow instructions) | Applicable: [`packs/core/.apm/skills/close-work/SKILL.md`](../../../packs/core/.apm/skills/close-work/SKILL.md) | Owns what the agent is actually instructed to do at runtime. Closeout verifies the disposition row, the deterministic-seam sentence, and the timer prohibition all describe shipped behaviour. |
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
- Resolve the lifecycle-record destination through the shipped Wave 1 resolver
  from a supplied, confirmed candidate, and fail closed when it is absent,
  unconfined, or not writable.
- Re-resolve and confine the record's path immediately before every write, and
  establish writability from a filesystem fact rather than from a declared
  candidate attribute.
- Treat every persisted record, external claim, and model-proposed locator,
  date, timezone, authority fact, or confirmation as bounded untrusted data and
  revalidate it at the deterministic seam that acts on it.
- Keep source, write, and deletion authority independent, and refuse when any is
  unknown or contradictory.
- Draw every persisted vocabulary token from a published set: RFC §5 disposition
  intents and `close_work.POST_CLOSEOUT_RESULTS`.
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
- Never create the lifecycle destination implicitly; absence is an offer to
  select or create, which a human accepts.
- Never add a second semantic-surface resolver, a second fingerprint helper, a
  weaker path check, or a new runtime dependency.
- Never implement workspace-status projection, ordinary-context exclusion,
  historical migration, or pruning.

## Testing Strategy

- **Date and dueness arithmetic: TDD.** The clock is an injected argument, so
  DST transitions, a reader in a different timezone, a leap day, late closeout,
  and days 29/30/31 are ordinary table cases over pure functions.
- **Record schema and refusals: TDD.** A closed field set bounded at every
  object level, strict parse, and each fail-closed refusal are compressible
  rules with stable codes.
- **Write-seam safety: TDD with real filesystem fixtures.** Confined temporary
  repositories exercise a swapped parent, an escaping symlink, a non-regular
  target, a real permission-denied destination, and an absent surface.
- **Identity across history shapes: goal-based fixtures over real Git.** Temporary
  repositories perform a squash merge, a merge commit, a rebase, and a
  `--depth=1` shallow clone of the same logical artifact; a fifth fixture deletes
  `.git` entirely. The record is written *before* each topology operation and
  verified *after* it, so a topology-derived implementation cannot self-verify.
  Git is never mocked, because a fixture cannot testify about the thing it mocks.
- **Review outcomes: TDD.** Approval, refusal, each uncertain recheck, and each
  exception-review outcome are a finite decision table with stable result codes
  and an asserted empty mutation trace.
- **Doctrine and boundary agreement: goal-based checks.** The five updated
  pointers, the shipped skill's own instructions, the amended Wave 4 roster
  boundary test, catalogue lint and verify, self-host regeneration, and the site
  and link gates prove the source doctrine and every projection agree.

**Stub coverage.** TDD-mode ACs are stubbed in `plan.md`'s per-task `Tests:`
subsections. Covered by a compiled red stub: AC1–AC33. `no stub (mode)`: AC34–AC37
(Task 5, goal-based and manual QA). Uncovered: none.

## Acceptance Criteria

### Dates and dueness

- [ ] **AC1 — `review_on` is thirty calendar days.** For a record whose
  `completed_on` is a date in a recorded IANA timezone, `review_on` equals that
  date plus thirty calendar days.
- [ ] **AC2 — The arithmetic is calendar-based, not interval-based.** A
  `completed_on` whose window contains a DST transition in the recorded zone
  still yields `review_on == completed_on + 30 calendar days`, the same offset
  as a window containing no transition.
- [ ] **AC3 — Dueness is evaluated in the recorded zone.** Readers whose local
  zones differ from the recorded zone and from each other receive the same
  dueness answer for the same record and the same instant.
- [ ] **AC4 — Day 29 is not due; days 30 and 31 are.** Dueness flips at local
  midnight on `review_on` in the recorded zone.
- [ ] **AC5 — Late closeout preserves the event date.** Enrolling with a
  `completed_on` already more than thirty days in the past yields a record that
  is immediately due and whose persisted `completed_on` equals the supplied
  event date rather than the enrolment day.
- [ ] **AC6 — Due grants no permission.** A due record returns no deletion
  permission and an empty mutation trace.
- [ ] **AC7 — The clock is injected.** Every seam that needs the current instant
  accepts it as a timezone-aware argument; a naive argument refuses, and no Wave
  5 module reads the system clock.

### The record

- [ ] **AC8 — The record's keys are exactly what the contract declares.** At
  every object level, the published schema is the enumeration; any key it does
  not declare refuses the write.
- [ ] **AC9 — Exclusion is structural, not detected.** `confirmation_proof` is
  an opaque digest, every evidence reference is a bounded non-personal
  reference, and `owner_role` is a pattern-constrained role, so requirements,
  personal identity, and rationale cannot be expressed rather than being
  screened for.
- [ ] **AC10 — The record has one canonical serialization.** Re-serializing a
  loaded record is byte-identical, and a non-finite numeric value refuses with
  `record-invalid`.
- [ ] **AC11 — Oversized and over-nested input refuses.** A record exceeding the
  byte ceiling or the nesting bound refuses with `record-invalid` rather than
  raising.

### Enrolment and persistence

- [ ] **AC12 — Only delivered work enrols.** Enrolment refuses work that is not
  delivered, not closed, or has no persistent record.
- [ ] **AC13 — Enrolment needs a selected completion event.** Absent a policy
  selection, enrolment refuses with a stable code rather than choosing an event.
- [ ] **AC14 — Only the completion event starts the clock.** Creation, reaching
  Ready, editing an artifact, and ending a session each refuse to enrol.
- [ ] **AC15 — Enrolment needs a confirmed candidate destination.** The resolver
  performs no discovery, so enrolment refuses unless the caller supplies a
  candidate carrying its evidence and a completed `destination-selection`
  confirmation.
- [ ] **AC16 — The destination must already exist; the record need not.** An
  absent record file is the normal pre-enrolment state, while an absent,
  unresolvable, unconfined, or read-only destination refuses with
  `lifecycle-state-unwritable`. Enrolment never creates the destination.
- [ ] **AC17 — Writability is a filesystem fact.** The read-only refusal is
  established at the write seam, not from a candidate's declared `writability`
  attribute, so a candidate that declares itself writable over a genuinely
  read-only destination still refuses.
- [ ] **AC18 — The write seam re-confines immediately before mutation.** A
  parent swapped for a symlink, an escaping destination, or a non-regular target
  detected at that point refuses with `unsafe-target` and zero effects.
- [ ] **AC19 — Every record mutation is authorized before it happens.** A
  record-mutating seam validates a write-scoped authority binding first, and
  refuses with `authority-uncertain` and an empty mutation trace when it is
  absent, uncertain, or names a different action or resource.
- [ ] **AC20 — A record loaded from disk is revalidated in full.** Every field,
  not only externally originating claims, is re-checked at the seam that acts on
  it.
- [ ] **AC21 — Stored state must be internally consistent.** `review_on` is
  re-derived from `completed_on` and `timezone` on load, and a disposition may
  move only forward; a mismatch or a backward move refuses with `record-invalid`.
- [ ] **AC22 — The record persists across sessions.** A record written in one
  process is loaded field-equivalently in another.
- [ ] **AC23 — `workspace.toml` gains no cooling schema.** It may carry a
  pointer to the lifecycle destination and nothing else.

### Identity

- [ ] **AC24 — Identity survives every history shape.** The same logical
  artifact verifies after a squash merge, a merge commit, a rebase, and a
  `--depth=1` shallow clone, and verifies with `.git` removed entirely.
- [ ] **AC25 — A rename updates the locator and keeps prior aliases.** After a
  rename the record's locator is the new path and the previous locator is
  retained as an alias.
- [ ] **AC26 — Four conditions block deletion.** Missing history, fingerprint
  drift, an unresolved reference, and uncertain authority each block deletion
  with a distinct stable code.
- [ ] **AC27 — Source authority never implies deletion authority.** A record
  whose source authority covers an external spec and whose deletion authority is
  absent blocks deletion.

### Day-30 review

- [ ] **AC28 — Day-30 review rechecks six things.** Review requires an explicit
  answer for completion, outputs, active use, obligations, identity, and
  authority; a missing answer refuses.
- [ ] **AC29 — The six answers must be human-attested.** An answer or exception
  envelope carrying only model-proposed input refuses with `review-incomplete`.
- [ ] **AC30 — Approval retires.** A review whose six answers all approve
  returns a `Retired` post-closeout result.
- [ ] **AC31 — Refusal or uncertainty creates an exception.** Either outcome
  returns a `retain-exception` record carrying a bounded reason, an owner role,
  and a human-supplied review date.
- [ ] **AC32 — An exception is itself reviewable.** Exception review offers its
  owner exactly four outcomes: confirm immediate deletion, renew retention with
  a new date, choose eligible cooling, or select advisory treatment.
- [ ] **AC33 — Day 30 never deletes.** No Wave 5 seam removes a file; an
  approved deletion is performed only by Wave 4's unchanged `preview_deletion`,
  `confirm_deletion`, and `apply_confirmed_deletion`.

### Boundaries and surfaces

- [ ] **AC34 — The reused primitives are byte-unchanged.** `surface_resolver.py`
  and `file_safety.py` end this wave with their pinned digests intact.
- [ ] **AC35 — No runtime dependency is added.** Every date, timezone, hashing,
  and serialization operation uses the standard library.
- [ ] **AC36 — The instructional surfaces state shipped behaviour.** The how-to,
  the lifecycle reference table header and `cool-30-days` row, the workspace
  schema reference, the pack README, and `close-work/SKILL.md`'s disposition
  row, deterministic-seam sentence, and timer prohibition no longer say cooling
  stops at classification.
- [ ] **AC37 — The Wave 6 and Wave 7 boundary survives.** The doctrine
  corpus still states, unweakened, that workspace-status projection,
  ordinary-context exclusion, migration, and pruning are not implemented, and
  the amended Wave 4 roster test still fails if that statement is removed or
  weakened.

## Assumptions

- Technical: the lifecycle record resolves to `docs/lifecycle/<delivery-id>.json`.
  The first destination chosen, `docs/specs/<slug>/lifecycle.json`, was withdrawn
  because `docs/CONVENTIONS.md` freezes a shipped spec directory as a unit and
  only shipped work cools. (source: owner decisions 2026-08-27; `docs/CONVENTIONS.md`
  § "A spec directory freezes as a unit"; `tests/roster/test_direct_light_documentation_boundary.py`)
- Technical: `runtime-coordination` is the applicable existing resolver role, so
  `surface_resolver.py` and its published contract are unchanged and their pinned
  digests hold. (source: `packs/core/.apm/skills/work-intake/scripts/surface_resolver.py`)
- Technical: the resolver never scans a repository, so the caller supplies the
  candidate destination and its confirmation. (source: `surface_resolver.py`
  module docstring)
- Technical: `datetime`, `date`, `timedelta`, and `zoneinfo` are stdlib on the
  `>=3.11` floor both packages declare; none of `dateutil`, `pendulum`, `arrow`,
  or `pytz` is declared by any manifest here, and none is needed. Some are
  present transitively in the developer interpreter, which is not a licence to
  import them. (source: `pyproject.toml`, `packages/*/pyproject.toml`,
  `tools/requirements.txt`, checked 2026-08-27)
- Technical: there is no blessed confined *writer* — `file_safety.py` is
  read-only — so the write seam reuses Wave 4's existing validated-parent walk
  rather than adding a second confinement implementation. (source:
  `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py`;
  `packs/core/.apm/skills/close-work/scripts/close_work.py`)
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
- 2026-08-27: Pre-EXECUTE adversarial and secure-design review; 27 sustained
  findings applied. Destination re-decided to `docs/lifecycle/<delivery-id>.json`
  after the frozen-spec-directory conflict surfaced. Added criteria for the
  candidate destination, write-seam confinement, write authorization, on-load
  revalidation and forward-only disposition, structural exclusion, canonical
  serialization, input bounds, human attestation, and exception review. Cut the
  leap-day criterion to a plan table case; merged the two write-surface criteria.
