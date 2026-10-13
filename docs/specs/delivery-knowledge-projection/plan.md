# Plan: Delivery knowledge projection

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing
- **Repository anchors:** `docs/product/briefs/acceptance-centered-work-loop.md` at `sha256-bytes-v1:5b4cc8d489a256eda3f5edbb0e51de07ccd35dcfa6bd0f38964286ca563f8910`, which carries the 2026-10-11 owner decision; the reviewed architecture set at `sha256-set-v1:0ca1b837a37254fdf6279e18f4ed01c6ff96ea8fd1d207b8c780e6aa4d994d02`, as since amended by the Slice 2 release; Slice 1 shipped at `9d39eae8b` (Core shadow services) and Slice 2 shipped at `bfe30052c` (Core 3.0.5). Direct owners: `docs/architecture/work-loop-knowledge-handoff.md`, `docs/architecture/work-loop-acceptance-evidence.md`, `docs/architecture/work-loop-review-disposition.md`, and `docs/architecture/knowledge-capture.md`. Analogous self-contained script seams: Slice 2's `_review_*.py` modules under `packs/core/.apm/skills/work-loop/scripts/`, with their no-runtime-schema-read spy in `packs/core/tests/skills/work-loop/test_review_compat.py` and schema parity in `tests/roster/`. Knowledge lifecycle code: `packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py` and `knowledge_store.py`, constructed through `packs/core/tests/skills/project-knowledge/`. Uncertainty: no reproducible snapshot reader exists over the evidence log, so T1 builds one.

> **Plan contract:** this is the implementation strategy. The current legacy
> whole-plan lock remains authoritative for Slice 3 until Slice 4 removes it
> through its accepted cutover. `initial-plan-review.v1` authorizes terminal
> intent and never grants task-content authority, but it does not enable mutable
> task reprojection in this slice. Substantive plan changes follow the current
> approval path while that lock remains active.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are
> working material before approval, while approval hashes the whole plan.

## Approach

Build a confined read-only feed and a pure projector in the work-loop skill over
the evidence log format that Slices 1 and 2 define, then teach project-knowledge
to pull that feed's output and to exclude invalid committed records one at a
time without ever raising another record's usability. Author the two new
schemas only under `contracts/delivery/`; runtime code validates the same rules
in self-contained standard-library code. Send no notification, change no Slice
1 or Slice 2 writer, and pin the reusable capture gates and the close-time
`work-item` path as unchanged. Production runs write no projectable fact yet,
so every behavioral proof runs on contract fixtures.

**Declined addition:** the optional post-commit notification. Rung 1 of `Cut
before adding`: no listener exists, pull scanning already satisfies discovery,
and the hint would have changed the Slice 1 `_compat_facade.py` writer.

## Constraints

- Slices 1 and 2 have shipped. Their contracts and modules are cited, not
  restated, and Slice 3 changes none of their record content, identity, or
  write behavior.
- The only production evidence log is
  `<spec-dir>/.shadow-acceptance/shadow-evidence.log`, written by
  `_compat_facade.py` only when `WORK_LOOP_SHADOW_SERVICES=1`, which also writes
  a self-ignoring `.gitignore` beside it. The feed reads those logs in place and
  inherits that scope. Each log is local to one worktree while the knowledge
  store is shared through Git, so a missing log is never evidence that a source
  stopped being current.
- In production today that log holds only contentless `engine-transition`
  receipts. Slice 2's `review-failure` receipts are written only when
  `project_compat_reconcile_review_source_event` (`loop-engine.py`) runs, and
  only tests call it until the FEAT-0036 cutover. T1-T3 therefore prove every
  behavior on contract fixtures built with the shipped writers.
- The feed reads through `read_confined_regular_file` in the work-loop
  `file_safety.py`, with `max_bytes` equal to the store's
  `_EVIDENCE_LOG_MAX_BYTES` (256 MiB), as the store's own open path does.
- `EvidenceStore.open()` in `_evidence_store.py` truncates a torn final frame,
  so the feed cannot use it as-is. The feed reads log bytes directly or through
  a new read-only accessor, which is the one predecessor-module change this plan
  admits without asking first.
- Slice 2 owns `review-failure` receipt creation and supersession, which the
  evidence store composes atomically (`_build_bridge_receipt`,
  `_build_bridge_supersession`, `_validate_review_transition`). The feed reads
  active and superseded state from the log; it never decides review
  currentness itself.
- `_content_safety.py` already registers a `knowledge-observation` profile with
  a 64 KiB cap. The projector uses it rather than adding a profile.
- Work-loop and project-knowledge are separate skills. The feed is a command
  whose output project-knowledge reads; neither imports the other.
- Project-knowledge today refuses a whole read on one malformed committed
  record (`_validated_event_lines` and `_validate_event` in `knowledge_store.py`;
  `map_mismatch` on enquiry). T2 changes that to per-record exclusion with a
  bounded reason on the read-only entry points only. Those are the
  enquire-mode helpers `enquire` (the `--enquire` route), `read_committed_topic`,
  and `read_freshness_source`, which read the committed topic map and topic
  blobs, and the `--distill --pending` page (`distill_pending` over
  `pending_page`), which reads observation partitions. A lookup whose named
  topic is itself excluded still refuses. Likewise the pending page's
  `workflow-receipts` mode, which the work-loop `plan-locked` terminal
  distillation uses, keeps its `replay_required` whole refusal when any
  selected capture is excluded or hidden, so a gate's drain never reports
  fewer captures than it named. `select_pending`, which shares the pending
  page's `_load_pending_partition_window` loader but has no production caller,
  keeps whole refusal, so exclusion is applied in `pending_page` rather than
  in that shared loader, and the refusal pinned in
  `packs/core/tests/skills/project-knowledge/test_observation_store.py` stays
  unchanged. Every other caller of the shared
  readers (`_read_events`, `_bounded_topic_records`, `_read_committed_topic_map`,
  `_verify_committed_topic_headers`) keeps today's whole-operation refusal when
  any observation, topic, or map record it reads is invalid. That set includes
  `--capture` and the work-loop producer gates, `_find_capture` over every
  partition, `distill_capture`, the terminal-disposition write, the promotion
  mutation in `distill_observation`, `rebuild_topic_map`,
  `recover_guarded_mutation`, `_verify_promoted_state`,
  `current_tree_snapshot`, `committed_knowledge_snapshot`, the committed-map
  coherence check behind writer admission (`_committed_v1_map_is_coherent`,
  `_assert_v1_writer_allowed`, `_coherent_worktree_map`), and migration
  staging, activation, reversal, and `legacy_append`. So no write can drop a
  quarantined line or map entry, miss an excluded terminal disposition, or
  pass an integrity or admission check against a reduced view; the
  store-wide write stop this keeps is a spec Accepted Risk.
- The close-time `work-item` path uses plain `--capture` with a cold reasoning
  verdict and `semantic_gate.name: close-time`, per
  `packs/core/.apm/skills/work-loop/references/work-item-capture.md`. It does
  not use `--producer-profile work-loop`, and close-work has no knowledge
  capture of its own.
- The current engine and legacy plan lock stay authoritative. This slice
  neither starts Slice 4 nor moves procedure, result, acceptance, or review
  authority.
- Pi is an optional external Slice 6 target. This slice imports, bundles,
  installs, and selects no Pi component.
- Pre-review disconfirming probe: `rg -n -i "knowledge.{0,24}(queue|cursor|retry|acknowledg|skip|admission|retention|revocation)|capture.{0,16}gate" packs/core/.apm/skills/work-loop packs/core/.apm/skills/close-work` finds the two work-loop producer gates (`_WORK_LOOP_CAPTURE_GATES` in `project_knowledge.py`, `SKILL.md` "Project-knowledge integration") and no delivery-owned lifecycle store, so no store migration is planned.
- The spec and plan are repository-durable at the locators above. Accepted
  contracts, current architecture, maintainer guidance, tests, and release
  history become the post-closeout evidence owners; the spec directory freezes
  after shipment.

## Construction tests

**Integration tests:** One shared conformance matrix feeds evidence and review
fixtures through these paths: no notification, candidate page refused, repeated scan, overlapping scan,
cache deleted, torn final frame, changed snapshot, report replacement,
assessment replacement, receipt superseded, log absent, log removed after a
capture, refused log (symlink, non-regular, multiply linked, oversized,
checksum-invalid), shadow flag unset, valid committed record, invalid merged
record, excluded disposition record, unavailable tooling, packages unavailable,
runtime schema read, and both retained capture paths. It compares observation
identity and bytes, presented candidates, knowledge-store bytes,
quarantine output, delivery decisions, evidence-log bytes, runtime file opens,
and delivery-owned state against AC-0001 through AC-0014.

**Manual verification:** none — every accepted behavior has a deterministic
contract, state, or decision oracle.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility | T1, T2, T4 | Schemas, inventory, no-copy, and feed parity from T1; consumer validation from T2; traceability from T4 | Canonical schemas, README rows, the registry row, and runtime behavior agree at release, with no schema copy or runtime schema read. |
| Current architecture | T4 | Architecture text tied to the conformance matrix | The four pages name the shadow-scoped feed, the read-only candidate mode, per-record quarantine, retained gates with Slice 8 removal, and the actual close-time `work-item` path. |
| Maintainer procedure | T2, T4 | Documented commands pass on pull, quarantine, and disabled-tooling fixtures | Maintainer guidance runs the supported checks without this plan. |
| Release history | T4 | Build, version-parity, clean-environment, targeted-suite, and changelog checks | Released Core projections and the changelog describe the shipped boundary. |

## Design (LLD)

### Design decisions

The evidence log is the replay source. The feed snapshots it read-only, the
projector returns one deterministic observation or none and writes nothing, and
pull scanning is the only discovery path. Neither the feed nor the candidate
mode holds lifecycle state or writes the knowledge store; a person or agent
admits knowledge through the existing `--capture` path. Traces to AC-0002
through AC-0004, AC-0007, AC-0008, AC-0010, AC-0012, and AC-0014. Owned by: T1-T3.

### Interfaces & contracts

The feed is a work-loop script command. It scans `docs/specs/*/` in path order,
reads each `.shadow-acceptance/shadow-evidence.log` (AC-0013), and admits
exactly the frames the store's replay (`_index_frames` in `_evidence_store.py`)
admits: a frame reusing a seen transaction, receipt, or supersession identity
is skipped so the first wins, and a checksum, reference, or
`_validate_review_transition` failure makes the whole log an unread source. The
only difference is that a torn final frame is left unrepaired and invisible.
It emits a `delivery-fact-feed.v1` page. Each entry
carries the source fact's spec path, transaction and record identity, and
predecessor version, plus its `knowledge-observation.v1` projection or an
explicit `none` with a bounded reason. When the first page is produced, the
snapshot token fixes the whole source set: the `docs/specs/` listing plus every
log's byte length and prefix digest. A continuation re-enumerates and refuses
on any difference, including an append to a not-yet-read log or an added or
removed spec directory, instead of mixing snapshots. A page holds at most
1,000 entries and 1 MiB, and each observation at most 4 KiB, so the largest
page the feed can emit is the largest page the candidate mode accepts; the
`delivery-fact-feed.v1` schema states both numbers once. Projection policy v1
admits one source kind, a current Slice 2 `review-failure` receipt, projected
as a `gotcha` observation whose text comes only from the typed review-report
and finding records in the same log, after the `knowledge-observation`
content-safety profile. A receipt is eligible only when no supersession in the
log names it; Slice 2 writes that supersession atomically whenever a report or
assessment is replaced or a source invalidated (`_validate_review_transition`
in `_evidence_store.py`). No current-fingerprint authority exists in shadow
mode, so the feed does not judge subject or policy freshness; each observation
carries the receipt's acceptance fingerprint and the review-policy fingerprint
from the `lineage` of the source review report, reached through the supported
assessment that derived the receipt (`_find_receipt_source` in
`_evidence_store.py`).
The feed command writes the page to standard output. Project-knowledge gains
one candidate mode that reads that page from standard input (AC-0014), checks
each candidate's text and path fields with `assert_persistable_text` and
`assert_persistable_paths`, and renders the survivors in a new
`knowledge-candidates.v1` frame. That frame reuses the escaping rule of
`_render_envelope` in `knowledge_store.py` but is a separate element, refuses
any field holding a line terminator or control, bidi, or zero-width character,
carries the unadmitted and unverified-provenance labels as attributes of each
entry element rather than as text lines, and pages whole
candidates within a 32 KiB output budget with a continuation ordinal. It writes
nothing. Turning a
candidate into knowledge is an ordinary `--capture` by a person or agent, who
writes the lesson and the privacy attestation; that path, its identity rule,
and its time window stay unchanged. Traces to AC-0001, AC-0002, AC-0004,
AC-0005, AC-0006, AC-0010, AC-0011, and AC-0014. Owned by: T1-T2.

### Failure, edge cases & resilience

A torn final frame is invisible, not repaired. A refused log (AC-0013) or a
checksum-invalid frame makes that log an unread source in the snapshot with a
closed reason code. A changed prefix refuses the continuation. An absent log,
including every log when the shadow flag is unset, contributes nothing. None of
these touches the knowledge store. Unsafe or unknown committed knowledge records
are excluded per record with a locator and closed reason code only. The
exclusion closes over dependents in the store's real record kinds: a capture
whose `observation.dispositioned` event (`promoted`, `duplicate`, `routed`,
`rejected`, or `superseded`) is excluded is excluded too rather than reverting
to pending, and a disposition whose capture is excluded is excluded. A
disposition is written into its capture's own partition, so while a partition
holds an invalid line whose target capture cannot be identified from validated
fields, the pending page shows no capture from that partition unless validated
data proves the line did not close it. That closure applies on the pending
page, the only read-only path that reads observations. For AC-0005, a record is orphaned when its only purpose is to
act on or point at another record, such as a disposition or a map entry. A
topic is a self-contained distilled record that `validate_topic` checks on its
own, and its `occurrences` are provenance, so excluding a capture orphans no
topic. Enquiry reads no observation journal, so its closure stays in the
topic layer: an invalid topic is not rendered, and a `topics.index.json`
entry that is invalid or points at an excluded topic is excluded instead of
failing the whole enquiry with `map_mismatch`. A missing, unparseable, or
link-like map file still refuses the whole enquiry, because no valid record
set exists. Quarantine output never enters the `knowledge-evidence.v1` element,
which stays byte-identical. On `--enquire`, the rendered text gains a separate
`<knowledge-quarantine version="knowledge-quarantine.v1">` element after the
evidence element, present only when an entry exists, holding each entry's
escaped locator or ordinal and reason code as attributes, and the CLI result
gains a top-level `quarantine` list carrying the same entries; the
`knowledge-enquiry-receipt.v1` receipt is unchanged. On `--distill --pending`,
the entries fill the drain receipt's existing `diagnostics` list. Both carry
the counted overflow marker after 100 entries. For AC-0005, a locator is
valid only when it is a repository-relative path under `docs/knowledge/` that
passes `assert_persistable_paths` and holds no line terminator (LF, CR, NEL,
U+2028, U+2029) or control, bidi, or zero-width character, the same limits
AC-0014 sets for candidate fields; any other locator is replaced by its
non-content-derived ordinal. Repeated
scans present the same candidates and store nothing. Traces to AC-0001, AC-0003 through AC-0007, AC-0010, AC-0012, and
AC-0013. Owned by: T1-T3.

### Dependencies & integration

Slice 1 supplies the evidence log format, frame checksum, receipt and
supersession records, content-safety profiles, and the effect and audit
boundary. Slice 2 supplies `review-failure` receipts and their supersession
inside the same log. Project-knowledge remains the capture, storage, enquiry,
distillation, and lifecycle owner. The reusable capture gates and the
close-time `work-item` path stay as they are; Slice 8 owns gate removal. No
Slice 3 runtime imports `agentbundle`, another repository package, or a
contract schema. Traces to AC-0001 through AC-0014. Owned by: T1-T4.

## Tasks

### T1: The read-only feed and pure projector satisfy snapshot and replay conformance

**Depends on:** none

**Touches:** `contracts/delivery/delivery-fact-feed.v1.schema.json`, `contracts/delivery/knowledge-observation.v1.schema.json`, `contracts/README.md`, `tests/roster/test_delivery_contract_bundle.py` (`_EXPECTED_SCHEMA_NAMES` pins the bundle inventory), a new schema parity suite under `tests/roster/`, new self-contained feed and projector modules under `packs/core/.apm/skills/work-loop/scripts/`, an optional read-only accessor in `_evidence_store.py`, `packs/core/.apm/skills/work-loop/evals/`, their generated skill projections, and tests under `packs/core/tests/skills/work-loop/`

**Verification mode:** TDD through contract and integration tests

**Tests:**
- A contract suite drives fixture evidence logs, built with the shipped Slice 1 and Slice 2 writers, through complete, paged past 1,000 facts, changed-prefix, torn-final-frame, checksum-invalid, absent-log, report-replacement, assessment-replacement, receipt-supersession, subject-changed but unsuperseded receipt (still eligible, fingerprints carried), oversized projection, page byte-bound boundary, reused-identity frame, append to a not-yet-read log and added or removed spec directory between pages, unknown-version, ineligible-source, and content-refusal cases. It compares the feed with AC-0001, AC-0002, AC-0010, and AC-0012, and compares every log's bytes before and after. The negative corpus includes `engine-transition` and other non-review receipts, reviewed-envelope and initial-plan-review records, plus plan, task-projection, mutation-classification, and superseded `review-failure` receipt inputs.
- A confinement suite presents a symlinked, FIFO, hard-linked, out-of-root, over-cap, and marker-missing log, a symlinked marker, and a symlinked `.shadow-acceptance` directory, and compares the unread-source entry, its reason code, and the absent facts and candidates with AC-0013. Separately, a symlinked or unreadable entry directly under `docs/specs/` and a refused root check the explicit whole-scan refusal, and a shadow-flag-unset run checks the empty snapshot without listing.
- A table-driven projector suite replays source fixtures and compares canonical observation identity and bytes across fresh processes, policy-version changes, supersession, and refusal against AC-0002 and AC-0004.
- Roster parity checks validate the two new schemas with `jsonschema` at test time, require their `x-spec` pointer to this spec, check that the feed schema types every observation free-text field as untrusted data and that an emitted page carries that typing, update the bundle inventory, and reject any delivery-schema copy outside `contracts/delivery/`.

**PLAN TDD disposition:** `no stub (implementation-discovered)`. **Discovery predicate:** the feed and projector modules do not exist yet, and their callable names and the choice between direct log reads and a read-only store accessor are set when implementation inspects `_evidence_store.py` frame parsing. **Constraint:** the first test may read but not alter, copy, or replace a predecessor contract, may not write to an evidence log, and cannot make Core load a schema at runtime. **Required outcome:** a contract test fails on a torn final frame or a superseded `review-failure` receipt before the feed makes both invisible. **Verification mode:** TDD through contract and integration tests. **Proof obligation:** this spec's `notes/verification-ledger.md` records the chosen seams and the first behavioral red result mapped to AC-0001, AC-0002, or AC-0010 before implementation turns it green.

**Grounding:** Read frames with the same canonical-JSON checksum rule as `_compute_frame_checksum` in `_evidence_store.py`, and take supersession from the log's own supersession records. Stop if the feed cannot tell a superseded `review-failure` receipt from an unsuperseded one using only the log's own supersession records, or if a read-only snapshot needs any write to the log; ask the owner rather than amending a predecessor.

**Done when:** the contract, replay, refusal, byte-identity, confinement, and parity tests pass, the work-loop eval harness covers the feed command, and the interface-compatibility evidence exists.

### T2: Project-knowledge gains a read-only candidate mode and per-record quarantine

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py`, `packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py`, `packs/core/.apm/skills/project-knowledge/SKILL.md` and its mode references, `packs/core/.apm/skills/project-knowledge/evals/`, generated skill projections, and `packs/core/tests/skills/project-knowledge/`

**Verification mode:** TDD through integration tests

**Tests:**
- Candidate-mode fixtures send no notification, restart, rescan overlapping pages, replay replaced reports, replaced assessments, and superseded receipts, and rescan with a log removed or refused. They compare the presented candidates, one per current source identity, with AC-0003 and AC-0010, and compare every knowledge-store file and all delivery-owned state before and after with AC-0004.
- Page fixtures feed malformed, duplicate-key, oversized, schema-invalid, and privacy-failing pages and candidates, with one fixture per candidate text and path field, and compare whole-page refusal, closed reason codes with no candidate text, and zero writes with AC-0014. A deeply nested page within the byte bound is refused the same way, with a closed reason code, no output, and no traceback.
- Framing fixtures render candidates containing frame-closing tags, markup, control text, and a line terminator followed by a forged `provenance:` or admitted-marker line in every field, and a candidate set larger than 32 KiB, and check the `knowledge-candidates.v1` element and unadmitted marker, full escaping, whole-candidate paging with a continuation ordinal, and no truncation, per AC-0014.
- A capture fixture turns one presented candidate into an ordinary `--capture` with a written lesson and attestation, then rescans after the source is superseded, and checks that the capture follows the store's existing lifecycle untouched, per AC-0010.
- A positive committed-read fixture passes a current valid `knowledge-captured-observation.v2` record through the `--distill --pending` page and a promotion, then enquires over the topic that promotion produced, and compares the usable results and empty quarantine output with AC-0009.
- A differential corpus holds one valid feed page plus one violation per constraint in the `delivery-fact-feed.v1` schema. Every page runs through `jsonschema` and through the candidate-mode validator, and the two must agree on accept or refuse; no constraint the consumer must enforce relies on annotation-only `format`.
- Write-path fixtures commit an invalid line beside valid captures and a terminal disposition, then run `--capture`, a work-loop producer capture, and a disposition into that partition. A second set commits an invalid topic and, separately, an invalid map entry beside valid ones, then runs a promotion, a map rebuild, a capture (writer admission), and legacy-migration staging and activation. Each operation refuses as it does before this slice, and every partition file, topic file, and `topics.index.json` stays byte-identical, per AC-0005 and AC-0006.
- Merge-bypass fixtures commit malformed, unsafe, unknown-version, and policy-invalid records, and a partition file with a hostile name, beside valid ones, then run `--enquire` and the `--distill --pending` page. They compare per-record exclusion, results from the valid records, and byte-identical committed files with AC-0005, and check that each quarantine entry holds only an escaped, validated locator or an ordinal and a closed reason code, and appears only in the `knowledge-quarantine.v1` element and top-level `quarantine` list on enquiry or the `diagnostics` list on the pending page, never inside `knowledge-evidence.v1`. A further fixture commits more than 100 invalid records and checks the counted overflow marker and that valid results still return.
- Dependency fixtures corrupt an `observation.dispositioned` line for each terminal disposition, and separately corrupt a capture that a disposition points at. Two more fixtures place an unparseable line and a disposition line with an invalid `capture_id` beside a closed capture, and check that the capture is not shown as pending. A `workflow-receipts` fixture selects a valid capture in a partition that also holds such a line and checks the `replay_required` refusal. They check that the capture is excluded rather than reverting to pending and that the orphaned disposition is excluded, per AC-0005.
- Hostile-locator fixtures commit an invalid topic file and an invalid `topics.index.json` entry whose names each hold frame-closing markup, an attribute-breaking quote, a line terminator followed by a forged line, and a bidi or zero-width character. They check that each appears in the `knowledge-quarantine.v1` attributes only as a fully escaped valid locator or an ordinal, that nothing closes, reopens, or adds lines to that element or `knowledge-evidence.v1`, and that the evidence element is byte-identical to a run without the invalid records.
- Topic fixtures corrupt a topic, corrupt a `topics.index.json` entry, and leave a map entry pointing at an excluded topic. They check that the invalid topic and each dependent map entry are excluded, that a topic whose `occurrences` name a capture excluded on the pending page still renders on enquiry with no journal opened, that enquiry still renders the valid topics, and that no excluded record's text appears, per AC-0005.

**PLAN TDD disposition:** `no stub (implementation-discovered)`. **Discovery predicate:** T1 has fixed the feed page and observation contract, and implementation inspection has chosen where in `project_knowledge.py` the candidate mode sits and which read paths in `knowledge_store.py` move from whole-read refusal to per-record exclusion. **Constraint:** the first test uses the existing knowledge store, adds no delivery-owned state, and never mutates an invalid committed record. **Required outcome:** an integration test fails because the candidate mode does not yet present a fixture's current candidate or because one invalid committed record refuses the whole read, then passes through the candidate mode or per-record exclusion. **Verification mode:** TDD through integration tests. **Proof obligation:** this spec's `notes/verification-ledger.md` records the chosen seams and the first behavioral red result mapped to AC-0010 or AC-0005 before implementation turns it green.

**Grounding:** Extend the existing validation in `_validate_event` and `validate_topic` rather than adding a second store or validator. Confine per-record exclusion to the read-only entry points named in Constraints; every writer and integrity check listed there keeps whole-operation refusal on any invalid observation, topic, or map record it reads. Revise the existing whole-enquiry refusal tests in `packs/core/tests/skills/project-knowledge/test_enquiry.py` for a corrupt map entry or an unsafe topic to the per-record contract, and keep the missing, unparseable, and symlinked map-file cases as whole refusals. Stop if per-record exclusion on enquiry would need a new observation-journal read. Keep `--capture`, its write-time refusals, `derive_capture_id`, its time window, and the `knowledge-evidence.v1` enquiry frame unchanged; the candidate mode calls `assert_persistable_text` and `assert_persistable_paths` directly and reuses the envelope's escaping rule for its own frame. Stop if the candidate mode needs to write any file, or if safe exclusion cannot be decided without changing a committed record's bytes.

**Done when:** the candidate, page, differential-corpus, framing, capture, write-path, quarantine, dependency, and topic tests pass, the eval harness covers the candidate mode and quarantine output, and the project-knowledge skill documents the candidate command and the capture step after it.

### T3: Delivery decisions ignore knowledge tooling and both retained capture paths are unchanged

**Depends on:** T1, T2

**Touches:** end-to-end conformance fixtures under `packs/core/tests/skills/work-loop/` and `packs/core/tests/skills/project-knowledge/`; no production module

**Verification mode:** goal-based check through end-to-end conformance fixtures

**Tests:**
- One delivery fixture runs a full work-loop pass with knowledge tooling absent, disabled, unavailable, timing out, refusing, and failing, and with the shadow flag set and unset. It compares spec, plan, review, acceptance, readiness, and closeout decisions, plus the files and state a pre-slice run produces, with AC-0007 and AC-0012.
- A state inventory after every path compares delivery-owned files and records against the forbidden lifecycle-state set in AC-0004 and AC-0008.
- Regression fixtures submit a deliberate close-time `work-item`, an inferred `work-item`, and `spec-approved` and `plan-locked` producer captures, and compare acceptance, refusal, size, privacy, provenance, and observability with the pre-slice behavior and AC-0006.

**Grounding:** These fixtures pin behavior that already holds, so no red phase exists; each fixture must fail when its compared decision or capture result is deliberately changed. Stop if preserving either capture path needs a change to readiness or to a Slice 1 or Slice 2 module.

**Done when:** the disabled-tooling, shadow-unset, inventory, and capture-path fixtures pass and no delivery-owned knowledge lifecycle state exists.

### T4: Cross-boundary conformance and durable outputs close the slice

**Depends on:** T1-T3

**Touches:** cross-boundary conformance fixtures, `docs/architecture/work-loop-knowledge-handoff.md`, `docs/architecture/acceptance-centered-work-loop.md`, `docs/architecture/work-loop-authority-migration.md`, `docs/architecture/knowledge-capture.md`, `packs/core/seeds/docs/knowledge/README.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, and a product changelog fragment under `docs/product/changelog.d/` created with `tools/changelog.py new`

**Verification mode:** goal-based check through integration, build, and documentation gates

**Tests:**
- The shared matrix in `## Construction tests` runs AC-0001 through AC-0014; this task adds no second case inventory.
- Core pack build and parity checks compare canonical contracts, generated skill projections, and runtime behavior. Clean-environment and file-open spy fixtures prove AC-0011 without bundling schemas.
- Documentation and status checks verify the four architecture pages, including the correction of the handoff page's §8 `work-item` command and §10 gate removal and the authority-migration page's Slice 3 owner, proof, and `work-item` rows, `knowledge-capture.md`'s read-validation account, the maintainer commands, release versions, changelog, contract traceability, and spec and plan lifecycle state.

**Grounding:** Use the repository's targeted Core pack suites, `make build-self`, `make bootstrap-sites`, the roster contract suites, and `lint-spec-status.py`. Stop if any output needs a runtime repository package, a schema copy or runtime schema load, Slice 4 work, or a change to predecessor authority.

**Done when:** the matrix and repository gates pass, the architecture pages match the shipped boundary, and every durable-output row has closeout evidence.

## Rollout

- **Delivery:** Land behind the current engine and legacy plan lock, beside the
  unchanged capture gates. The feed only sees specs run with
  `WORK_LOOP_SHADOW_SERVICES=1`. Rollback stops running the candidate mode and
  reverts the read-path change; no delivery state needs migration because none
  exists, and no Slice 1 or Slice 2 writer changed.
- **Infrastructure:** none — local canonical contracts, self-contained Core pack
  code, and the existing Git-backed knowledge store.
- **External-system integration:** none.
- **Deployment sequencing:** T1 feed and projector, T2 candidate mode and
  quarantine, T3 readiness-isolation and retained-path proof, then T4 durable outputs
  and release.

## Risks

- Per-record exclusion weakens today's fail-closed read. A record excluded in
  error hides knowledge silently. T2 reports every exclusion with a bounded
  reason, and the positive AC-0009 fixture guards against over-exclusion.
- A projection that carries too much review content may leak protected data or
  instructions into an agent's context. The `knowledge-observation`
  content-safety profile runs before emission, the feed page marks its text as
  untrusted data, the candidate mode reruns the persistable-text and path
  checks and keeps output inside inert framing, and capture goes through the
  unchanged `--capture` validation.
- A read-only feed racing a live append could see a partial frame. Frame
  checksums and the prefix-digest snapshot token make that frame invisible and
  refuse a mismatched continuation.
- Frame checksums are not keyed, so a force-added Git-tracked log can present
  invented candidates. The spec records this under Accepted Risk; the
  unverified-provenance marker and ordinary capture validation bound it.
- Genuine review prose can be steered by untrusted diff content. The spec records
  this under Accepted Risk; capture stays the ordinary `--capture` path.
- A per-worktree log can vanish while a capture made from its candidate lives on
  in Git. Slice 3 never withdraws a capture, so that capture follows the store's
  ordinary lifecycle like any hand-written one.
- Candidates-only collection means no knowledge arrives without a person or
  agent capturing it. That is the owner's chosen trade: no automatic admission
  in exchange for an unchanged capture contract.
- Removing nothing still risks changing the gates by accident. T3's capture-path
  fixtures pin both retained paths.
- A copied or runtime-loaded schema could couple Core to a repository checkout.
  T1 and T4 require one canonical schema set, a no-copy scan, clean-environment
  runs, and zero runtime opens under `contracts/delivery/`.

## Changelog

<!-- Approval entries only:
- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->
- 2026-10-13: spec approved by eugenelim (spec-plan run)
- 2026-10-13: plan approved by eugenelim (spec-plan run)
- 2026-10-13: spec approved by eugenelim (code-mode run, terminal intent `code`)
- 2026-10-13: plan approved by eugenelim (code-mode run)
