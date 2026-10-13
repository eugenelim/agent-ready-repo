# Spec: Delivery knowledge projection

- **Status:** Implementing
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** brief:acceptance-centered-work-loop
- **Discovery:** none
- **Contract:** `contracts/delivery/` (canonical delivery bundle; Slice 3 adds `delivery-fact-feed.v1` and `knowledge-observation.v1`)
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

Platform Core and project-knowledge maintainers get a proven boundary for
pulling reproducible knowledge candidates out of the evidence and review facts
that the Slice 1 and Slice 2 contracts define, without making knowledge tooling
part of delivery. Success means a pull scan finds every eligible fact with no
notification at all, an invalid knowledge record that arrives through Git is
excluded rather than breaking every read, and delivery owns no knowledge
lifecycle state. Candidates stay suggestions until a person or agent captures
one through the existing path. The current reusable capture gates keep
working unchanged beside the new path.

Today a production run writes only contentless `engine-transition` receipts,
and only with `WORK_LOOP_SHADOW_SERVICES=1`. No production path writes a
`review-failure` receipt yet, because Slice 2's review bridge is reached only
from tests until the FEAT-0036 cutover. This slice therefore proves the
boundary on contract fixtures; real yield arrives with those later cutovers.

## What Changes

- A read-only work-loop feed command reads each spec's Slice 1 evidence log
  through the skill's confined file helpers, without writing to it, and emits
  one reproducible `delivery-fact-feed.v1` snapshot of eligible facts in stable
  order. The page is machine input for the candidate mode; it marks every
  observation text field as untrusted data, and the maintainer procedure pipes
  it straight into the candidate mode rather than reading it.
- A pure projector in the same skill turns each eligible fact into one
  attributed `knowledge-observation.v1` candidate or none.
- Projection policy v1 has exactly one eligible source kind: a Slice 2
  `review-failure` receipt that no supersession in its log names, projected as
  a `gotcha` candidate. Every other Slice 1 receipt, including the
  `engine-transition` receipts production writes today, is ineligible. Once
  Slice 2 supersedes a receipt, the next scan that reads its log no longer
  presents its candidate. A candidate is a past lesson, not a claim about the
  current code, so a later change to the acceptance subject or review policy
  does not hide it; the candidate carries the receipt's acceptance fingerprint
  and its source report's review-policy fingerprint so the capturer can see
  which subject it came from.
- Reviewed-envelope, initial-plan-review, plan, task-projection, and
  mutation-classification records stay delivery authority or procedure input.
  They are never knowledge candidates.
- Project-knowledge gains a read-only candidate mode. It reads one feed page,
  validates the whole page, checks each candidate with its own text and path
  rules, and returns the checked candidates in a separate inert
  `knowledge-candidates.v1` frame, marked as unadmitted suggestions. It
  stores nothing. A person or agent turns a chosen candidate into an ordinary
  capture through the existing `--capture` path, writing the lesson and giving
  the privacy attestation there.
- Project-knowledge's read-only paths, enquiry and the distillation pending
  page, exclude an invalid committed record and report a bounded quarantine
  reason, instead of refusing the whole read as they do today. Every path that
  writes or checks store integrity still refuses the whole operation.
- Delivery sends no notification. Pull scanning is the only discovery path,
  which is the architecture's dropped-notification case made permanent.
- The `spec-approved` and `plan-locked` capture gates and the explicit
  close-time `work-item` capture path stay as they are.

## Scope and Non-goals

This slice owns `delivery-fact-feed.v1`, `knowledge-observation.v1`, their
canonical schemas, the read-only feed, the pure projection policy over eligible
Slice 1 evidence and current Slice 2 review facts, the read-only
project-knowledge candidate mode, and committed-record read quarantine. It
retains the existing reusable capture gates, the existing `--capture` path, and
the explicit close-time `work-item` capture path unchanged.

The feed reads only what Slice 1 writes today: the per-spec evidence log under
`<spec-dir>/.shadow-acceptance/`, which exists only when
`WORK_LOOP_SHADOW_SERVICES=1`. With the flag unset, the feed returns a complete
empty snapshot and every default run behaves as it does now.

It does not remove or change the reusable capture gates, make the evidence log
default-on, send a post-commit notification, change any Slice 1 or Slice 2
module beyond a read-only accessor, change acceptance or review authority,
write to a delivery evidence log, treat reviewed-envelope or initial-plan-review data as knowledge, remove
the current plan lock, reproject mutable tasks, transfer procedure ownership,
add Pi or another runtime dependency, add an `agentbundle` runtime dependency,
load delivery schemas at runtime, start Slice 4, or make knowledge tooling part
of readiness.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | The feed and observation records cross the delivery and project-knowledge boundary. | `contracts/delivery/delivery-fact-feed.v1.schema.json`, `contracts/delivery/knowledge-observation.v1.schema.json`, `contracts/README.md`, and the existing `contracts/REGISTRY.md` row for this spec | Core and project-knowledge contract maintainers | JSON Schema 2020-12 validation, an `x-spec` pointer on each schema, the delivery bundle inventory, a no-copy check, and producer-consumer fixtures | Each exposed record has one canonical schema under `contracts/delivery/`, producer and consumer validation agree, and no schema copy or runtime schema load exists. |
| Current architecture | The delivery-knowledge boundary changes, and the current pages misdescribe it. | `docs/architecture/work-loop-knowledge-handoff.md`, `docs/architecture/acceptance-centered-work-loop.md`, `docs/architecture/work-loop-authority-migration.md`, and `docs/architecture/knowledge-capture.md` | Platform Core and project-knowledge maintainers | Architecture text linked to contracts, implementation, and conformance suites | The pages name the shadow-scoped confined feed, the stateless projection, notification-free pull scanning, the read-only candidate mode with capture through the existing path, per-record read quarantine, the retained capture gates with their removal owned by Slice 8, and the actual close-time `work-item` command path, and none still describes a Slice 3 intake, deduplication, revocation, or knowledge-owned cursor. |
| Maintainer procedure | Maintainers need runnable pull-scan, candidate, quarantine, and disabled-tooling checks. | `packs/core/seeds/docs/knowledge/README.md` and `packs/core/.apm/skills/project-knowledge/SKILL.md` | Core and project-knowledge maintainers | Documented commands exercise a pull scan piped into the candidate mode, turning a candidate into a capture, quarantine output, and unavailable tooling | A maintainer can run the supported checks without reading this delivery record. |
| Release history | Core pack behavior changes ship through its existing release owner. | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, the `work-loop` and `project-knowledge` eval harnesses under `packs/core/.apm/skills/*/evals/`, and a product changelog fragment under `docs/product/changelog.d/` created with `tools/changelog.py new` | Core pack release maintainers | Version parity, build output, targeted suites, updated eval cases, and an outcome-led changelog entry | Released Core projections contain the matching behavior, canonical contracts stay unbundled, and the changelog names the maintainer-visible result. |

## Agent Rules

### Always do

- Bind eligible source facts, acceptance and review currentness, identity,
  ordering, and content-policy application to the shipped Slice 1 and Slice 2
  owners rather than restating their contracts.
- Admit Slice 1 evidence only from complete committed frames, and admit Slice 2
  review facts only through the supersession records Slice 2 writes when a
  report or assessment is replaced or a source is invalidated.
- Do not filter candidates on acceptance-subject or review-policy freshness.
  Those rules decide acceptance and review readiness, not whether a past review
  failure is a lesson worth suggesting; carry both fingerprints instead.
- Read delivery evidence logs without writing to them. Never truncate, lock for
  writing, repair, or append to a log from the feed.
- Read every evidence log only through the work-loop skill's own
  `file_safety.py` confined, no-follow, regular-file, bounded-read helpers.
- Derive every observation from an eligible durable fact, with complete source
  provenance and deterministic identity.
- Apply the existing `knowledge-observation` content-safety profile in
  `_content_safety.py` before an observation leaves delivery, and apply
  project-knowledge's own capture validation before a candidate or committed
  record becomes usable.
- Keep `contracts/delivery/` as the only delivery-schema source. Core runtime
  scripts validate the same behavior in self-contained code and neither copy nor
  load a delivery schema at runtime.
- Keep the feed and project-knowledge each inside its own skill. They exchange
  `delivery-fact-feed.v1` data, never Python imports across skills.
- Keep pull scanning the only discovery path.
- Keep the reusable capture gates and explicit close-time `work-item` capture
  working exactly as they do before this slice.
- Keep all knowledge-owned storage, admission, retention, quarantine
  reporting, and revocation inside project-knowledge, and leave every one of
  them unchanged except read-time quarantine.

### Ask first

- Add an eligible source-fact kind, an observation kind, or a
  projection-policy version.
- Add or change a method on a Slice 1 or Slice 2 module beyond a read-only
  accessor that leaves record content, identity, and write behavior unchanged.
- Change the shipped Slice 1 or Slice 2 contract fields, identity, freshness,
  report, assessment, or disposition semantics.
- Change project-knowledge admission, retention, revocation, or storage
  ownership.
- Change when closeout creates an explicit `work-item` or what that record may
  contain.

### Never do

- Add a delivery-owned knowledge queue, cursor, retry, acknowledgement, skip
  log, admission record, retention record, revocation record, or capture gate.
- Remove or alter the `spec-approved` or `plan-locked` capture gates, or make
  the evidence log or shadow services default-on.
- Write, admit, disposition, supersede, or withdraw any knowledge record from
  the feed, the projector, or the candidate mode.
- Supply a `lesson` or assert a `privacy_attestation` on a person's behalf.
- Make scanning, admission, enquiry, distillation, or any
  knowledge-tool result a prerequisite for spec, plan, review, acceptance,
  readiness, or closeout.
- Treat a projected observation as accepted knowledge, product truth, a
  requirement, a decision, evidence, review disposition, or delivery authority.
- Project `reviewed-execution-envelope.v1`, `initial-plan-review.v1`, plan text,
  task projections, or mutation-classification results as observations.
- Infer close-time `work-item` records from projected observations, or silently
  turn blocked delivery residue into knowledge.
- Import, bundle, install, or select Pi, or make Pi compatibility a
  prerequisite for this slice or any later Core cutover.
- Import `agentbundle` or another repository package from the feed, projector,
  candidate mode, or read-validation runtime; copy a delivery schema; or read a
  delivery schema at runtime.
- Start Slice 4, move orchestration authority, or alter the predecessor-owned
  acceptance and review contracts.

## Testing Strategy

- Feed snapshot semantics, read-only log access, complete-frame visibility,
  projection eligibility, deterministic identity, and pure replay use **TDD**,
  because each has a compact input-output invariant.
- Pull rescan, overlapping scans, candidate-mode page validation,
  committed-record quarantine, and source supersession use **TDD through integration tests**, because their result
  crosses the delivery and project-knowledge boundary.
- Notification-free discovery, absent or failing knowledge tooling, readiness
  isolation, and the retained capture paths use a **goal-based check through
  end-to-end conformance fixtures**, because they pin behavior that already
  holds and a unit test cannot show that delivery decisions are unchanged.
- Absence of delivery-owned lifecycle state, runtime self-containment, and
  release closure use **goal-based checks** over source inventory, contract
  no-copy parity, clean-environment runs, runtime file-open spies, and status
  gates. This slice has no visual or manual-QA behavior.

## Acceptance Criteria

- [ ] **AC-0001:** A complete pull scan enumerates every eligible committed delivery fact in stable contract-defined order from one reproducible snapshot, in pages of at most 1,000 facts and at most 1 MiB in which every observation free-text field is typed as untrusted data by the `delivery-fact-feed.v1` schema, each page ending before the entry that would exceed either bound so no entry is split or dropped, exposes no record from an incomplete or torn evidence frame, and leaves every evidence log byte-identical; when a continuation cannot reproduce its snapshot, the scan refuses without returning a partial result.
- [ ] **AC-0002:** Replaying the same eligible durable facts under the same projection and content-policy versions yields byte-identical observation identities and payloads of at most 4 KiB each, while an ineligible, oversized, or refused fact yields no observation and no delivery record; reviewed-envelope, initial-plan-review, plan, task-projection, mutation-classification, and superseded `review-failure` receipt inputs are ineligible, and every observation carries its source receipt's acceptance fingerprint and the review-policy fingerprint from the `lineage` of the review report that the receipt's supported assessment derives from.
- [ ] **AC-0003:** With no notification sent for any eligible fact, a later pull scan presents every projected observation that the same facts yield, so discovery never depends on a notification arriving.
- [ ] **AC-0004:** Repeated and overlapping scans may repeat the same deterministic observation, but create no delivery-owned or knowledge-owned cursor, deduplication, acknowledgement, retry, skip, admission, or retention state, and leave every file under the knowledge store byte-identical.
- [ ] **AC-0005:** When Git introduces a malformed, unsafe, unknown-version, or policy-invalid committed knowledge record outside intake, the read-only paths (enquiry through `--enquire` and the distillation pending page through `--distill --pending`) exclude that record, still return results from the remaining valid records, and leave the committed record unchanged; every path that writes, dispositions, promotes, rebuilds the topic map, admits a writer, or stages, activates, or reverses a migration still refuses the whole operation and changes no byte when any record it reads is invalid. Excluding a record never makes any other record more usable: a subject whose restricting, dispositioning, superseding, or revoking record is excluded is excluded too, and records left orphaned by an exclusion are excluded. Each quarantine entry carries only a record locator and a code from a closed knowledge-owned reason-code set, with no record bytes, excerpt, or content-derived hash. The locator is a validated, bounded, repository-relative path plus line number, escaped inside an inert frame; when the path fails validation, a non-content-derived ordinal replaces it. One read reports at most 100 quarantine entries, then a single counted overflow marker, and still returns the valid records.
- [ ] **AC-0006:** A deliberate close-time `work-item` capture that satisfies the existing contract in `packs/core/.apm/skills/work-loop/references/work-item-capture.md`, and a work-loop producer capture at the `spec-approved` or `plan-locked` gate, are each accepted and observable through project-knowledge exactly as before this slice, while projected observations never infer or synthesize a `work-item`.
- [ ] **AC-0007:** For identical delivery facts, absent, disabled, unavailable, timing-out, refusing, or failing knowledge tooling produces the same spec, plan, review, acceptance, readiness, and closeout decisions as successful knowledge tooling.
- [ ] **AC-0008:** A source and durable-state inventory after this slice finds no delivery-owned knowledge queue, cursor, retry, acknowledgement, skip log, admission record, retention record, revocation record, or knowledge-specific readiness transition, and no capture gate beyond the `spec-approved` and `plan-locked` gates and the close-time `work-item` path that existed before it.
- [ ] **AC-0009:** A committed current `knowledge-captured-observation.v2` record with a valid schema, content-policy version, provenance, and inert-data decision remains usable by enquiry and distillation after read validation and produces no quarantine entry.
- [ ] **AC-0010:** A source identity is the spec directory plus the Slice 1 receipt identity. Each scan presents exactly one candidate per current source identity plus projection and content-policy version. When a review report or supported assessment stops being current, the next scan that reads its log observes the Slice 2 receipt supersession and presents no candidate for it. A source whose log is absent, unread, refused, or disabled by the shadow flag, including on another clone or after a worktree is removed, yields no candidate. No scan outcome edits, withdraws, or dispositions a capture already made from an earlier candidate; that capture follows the store's existing lifecycle.
- [ ] **AC-0011:** The Core feed, projector, candidate mode, and committed-read validation pass their conformance corpus when `agentbundle` and other repository packages are unavailable; runtime modules import only the Python standard library or sibling modules in their own skill, open no file under `contracts/delivery/`, and the repository contains no delivery-schema copy outside that directory.
- [ ] **AC-0012:** With `WORK_LOOP_SHADOW_SERVICES` unset, a pull scan returns a complete, valid, empty snapshot, and a full work-loop run produces the same files, state, and decisions as it did before this slice.
- [ ] **AC-0013:** The feed reads each `docs/specs/<feature>/.shadow-acceptance/shadow-evidence.log` only through the work-loop `file_safety.py` confined, no-follow, single-link, regular-file read helpers rooted at the repository, with a 256 MiB cap per log matching the Slice 1 store bound, and only when its directory holds the writer's exact self-ignoring `.gitignore` marker; the marker read uses the same confined, no-follow, bounded helpers; a missing, refused, or different marker, a symlinked `.shadow-acceptance` directory, a symlink, non-regular, multiply linked, out-of-root, oversized, or checksum-invalid log is refused, reported in the snapshot as an unread source with a closed reason code, and contributes no facts or candidates. The listing of `docs/specs/` is confined to the repository and refuses the whole scan, explicitly and with a closed reason code, when the root is refused or any entry directly under it is link-like or unreadable; it never returns a complete snapshot in that case. With `WORK_LOOP_SHADOW_SERVICES` unset, the feed returns the AC-0012 empty snapshot without listing.
- [ ] **AC-0014:** The candidate mode reads one feed page from standard input up to the AC-0001 page byte bound and refuses the whole page, emitting nothing, unless it strictly parses as a schema-valid `delivery-fact-feed.v1` page. Every free-text field of each candidate must pass project-knowledge's `assert_persistable_text` and every path field its `assert_persistable_paths`, and no field may contain a line terminator (LF, CR, NEL, U+2028, U+2029) or a control, bidi, or zero-width character; a failing candidate is omitted with a closed reason code and no candidate text. The rest are returned only inside an inert `knowledge-candidates.v1` frame, distinct from enquiry's `knowledge-evidence.v1`, that marks each entry as an unadmitted candidate whose provenance is an unverified local claim, in renderer-owned positions that no field value can reproduce, and escapes every field, identifiers and provenance included, so no content can close or reopen the frame or forge a renderer line. One output holds at most 32 KiB of whole candidates and, when more remain, ends with an explicit continuation ordinal instead of truncating. The mode writes no file.

## Follow-ons

- Removing the reusable `spec-approved` and `plan-locked` capture gates belongs
  to the brief's Slice 8 `legacy-engine-cutover`, once delivery facts are
  written by default. The owner decision is
  [`notes/owner-decision-2026-10-11.md`](notes/owner-decision-2026-10-11.md).

## Terminal Intent

`code` — after approval, implement the Slice 3 boundary in Scope and
Non-goals through tasks T1-T4 until every Acceptance Criterion is satisfied.

## Accepted Risk

The first two risks below were accepted by the owner at spec approval on
2026-10-13; the store-wide write stop was accepted during the code-mode
amendment review on the same day, as recorded in
[`notes/owner-decision-2026-10-13.md`](notes/owner-decision-2026-10-13.md).

- **Unverified local provenance.** Evidence-log frame checksums are not keyed,
  so a contributor who force-adds a crafted `.shadow-acceptance/` log and marker
  to Git can make a pull scan present invented `review-failure` candidates.
  This slice does not detect Git-tracked logs. The residual is bounded because
  candidates are marked as unverified local claims, stay inside inert framing,
  pass the persistable-text and path checks, and reach the store only through
  an ordinary `--capture`. Owner: Platform Core. Revisit when Slice 8 makes
  delivery facts authoritative.
- **Steered review prose.** A genuine `review-failure` receipt can carry finding
  text that untrusted diff content steered, and natural-language instruction
  detection is incomplete. Candidate text reaches the store only through an
  ordinary `--capture`, whose privacy attestation is given by the person or
  agent making the capture under the existing capture contract, and enquiry
  replays stored knowledge inside its evidence-only frame. This slice adds no
  stricter capture gate. Owner: Platform Core.
- **Store-wide write stop.** One invalid committed observation record blocks
  every promotion and terminal disposition, plus captures into its partition.
  One invalid committed topic or topic-map entry blocks every write, captures
  included, through writer admission. Either stop lasts until a maintainer
  repairs or reverts the record through Git; the quarantine report on the
  read paths gives its location. This is today's behavior, kept so that no
  write runs against a reduced view. Owner: Platform Core.

## Assumptions

- Projected candidates only exist for specs run with
  `WORK_LOOP_SHADOW_SERVICES=1`, and no production path writes a projectable
  fact until the FEAT-0036 review cutover and Slice 8. This slice proves the
  boundary on fixtures, not the volume.
