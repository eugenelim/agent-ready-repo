# Spec: Project knowledge foundation

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0077, ADR-0081, and ADR-0082 (Accepted)
- **Brief:** none
- **Discovery:** none
- **Contract:** `contracts/jsonschema/knowledge-captured-observation.schema.json` plus versioned core topic, disposition, map, and enquiry contracts
- **Shape:** mixed

> **Spec contract:** this document defines what “done” means. The implementing
> change must match it or update it through the same review workflow.

## Objective

Any integrated workflow can triage free-form scratch at a semantic gate and
submit one worthwhile lesson to `project-knowledge --capture` through a shared,
published contract. One private writer persists the admitted observation in a
repo-scoped classification/month journal. At a terminal gate or in a later
explicit run, `project-knowledge --distill` records a terminal disposition and
may reconcile the observation into stable per-topic JSON. Humans and declared
skills can use `project-knowledge --enquire` to retrieve only committed active
topics as bounded untrusted evidence.

The foundation works with repository filesystem access alone. It requires no
writable user directory, database, daemon, network service, embedding model,
or automatic session memory.

## Boundaries

### Always do

- Keep scratch free-form and workflow-owned; persist only observations that
  pass gate-time triage and the capture contract.
- Keep captured-observation journals durable but non-queryable. A captured
  event is explicitly pending until distillation gives it at most one terminal
  disposition.
- Treat topic files as semantically canonical and the committed body-free topic
  map as their deterministic rebuildable publication manifest.
- Route normative content to its owning repository artifact; retain only
  independently reusable practice residue as topics.
- Treat every captured, persisted, or retrieved body as untrusted data below
  governed artifacts, user intent, and runtime permissions.
- Treat the working tree as the authoring surface and one committed Git
  topic/map snapshot as the only ordinary enquiry surface.
- Author shipped behavior in `packs/core` and regenerate projections through
  existing build routes.

### Ask first

- Reopen or materially amend RFC-0077, ADR-0081, ADR-0082, this spec, or this
  plan after approval.
- Resolve material contradiction, insufficient provenance, privacy uncertainty,
  over-broad topic split, ambiguous routing, or ambiguous retirement.
- Turn a routing suggestion into agent instructions, a workflow gate, or a
  verification-tool change through that artifact's normal workflow.
- Change a versioned contract, resource limit, lifecycle/disposition vocabulary,
  migration accounting rule, or retention behavior.

### Never do

- Mine transcripts or arbitrary tool history to reconstruct observations.
- Query observation journals, scratch, legacy JSONL, `needs_review`, retired,
  malformed, privacy-refused, or out-of-project records as ordinary knowledge.
- Persist rejected raw bodies or quarantine content that the baseline cannot
  protect and delete.
- Let producer workflows choose journal paths, invoke private writer scripts,
  or create fallback stores.
- Load knowledge automatically at session start, resume, fork, or compaction.
- Add SQLite, embeddings, a service, or another runtime dependency.
- Let retrieved content grant authority, widen permissions, select tools,
  approve changes, or write itself back as evidence.
- Edit adapter-specific instruction projections directly or use `AGENTS.md` as
  a backlog.
- Change the broad closeout question shipped in core 2.5.9.

## Testing strategy

- **Contracts:** table-driven TDD for strict JSON, Unicode, duplicate keys,
  non-finite numbers, provenance, privacy attestations, and resource limits.
- **Capture:** construction tests for classification/month routing,
  idempotency, terminal disposition, and enquiry exclusion.
- **Filesystem safety:** Linux, macOS, and native-Windows fixtures for
  confinement, path aliases, exclusive locks, stale ownership, interruption,
  ordered-write recovery and atomic replacement.
- **Distillation:** behavioral tests that reject, route, deduplicate, promote,
  reconcile, narrow, surface, and retire without letting scripts make semantic
  judgments.
- **Migration:** disposable-repository tests for complete accounting,
  deterministic output, activation, rollback, and provenance preservation.
- **Enquiry:** scope, freshness, abstention, injection containment, immutable
  Git snapshot, and output-budget tests driven by competency questions.
- **Integration:** construction tests for progressive mode isolation and a
  work-loop-to-core handoff through normal skill discovery.
- **Delivery:** catalogue lint/verify, projection drift, knowledge lint, build
  gates, and one end-to-end adopter journey.

## Acceptance Criteria

- [x] **AC1.** `contracts/jsonschema/knowledge-captured-observation.schema.json`
  publishes the strict, versioned producer contract. It carries no
  producer-chosen storage identity. It requires concise lesson,
  `pattern | gotcha | antipattern`
  kind, structural project scope, one or more competency-question facets,
  destination hint, producer workflow, semantic gate, normalized confined
  provenance, source-relative freshness anchor, observation time, and semantic
  privacy attestation. It optionally records bounded friction evidence and a
  stable verification/navigation route. Unknown fields, duplicate keys,
  non-finite values, invalid Unicode/control content, absent provenance, and
  oversized fields fail closed. A producer-supplied `capture_id` is an unknown
  field and therefore fails closed.
  The published schema is bundled byte-identically with the catalogue engine
  under the existing `contracts/` authority rule.
  After all strict syntax, schema, provenance, and privacy admission checks
  pass, core derives `capture_id` as
  `kco-YYYYMM-<64 lowercase hex>` from observation month and SHA-256 over the
  canonical UTF-8/JCS producer request, with the ID absent from its own
  preimage. Fixed vectors prove cross-platform derivation.

- [x] **AC2.** Successful `--capture` wraps the validated request in an
  immutable `observation.captured` event and appends it only to
  `docs/knowledge/observations/<kind>/YYYY-MM.jsonl`, where kind and UTC month
  are derived from the request kind and immutable RFC 3339 UTC observation
  time, never writer wall-clock time or a caller-supplied path. Producer
  workflow is provenance, never file ownership. Capture returns a receipt that
  identifies the event and partition. Normal capture refuses observation times
  more than seven days before writer UTC time, more than five minutes in the
  future, or before the repository's v1 activation commit only after checking
  for an existing identity. An aged exact replay returns its existing receipt;
  an aged new capture refuses. General historical import is out of scope; AC20
  migrates only the existing legacy corpus.

- [x] **AC3.** Capture identity is core-derived `capture_id`; partition is not
  part of identity. An exact canonical request deterministically derives the
  same month, ID, partition, event, and receipt, including across a writer-time
  month boundary. A changed request is a distinct observation to reconcile, not
  identity reuse. No committed observation index is
  required. Pending selection scans only bounded named partitions; an optional
  lookup accelerator is disposable, gitignored, and rebuildable from journals.

- [x] **AC4.** Every captured event is explicitly `pending` and non-queryable
  until distillation processes it. A processed capture receives at most one
  terminal `observation.dispositioned` event with disposition `promoted |
  duplicate | routed | rejected | superseded`. A disposition references the capture,
  records a bounded reason code, and names the resulting topic occurrence or
  canonical destination when applicable. A rejection never duplicates the raw
  body. Unknown or conflicting terminal dispositions fail closed. Terminal
  workflows attempt distillation for their receipts; unresolved judgment stays
  enumerable through bounded cursor-paged `--distill --pending` runs owned by
  core maintainers. A workflow request uses selection mode `workflow-receipts`
  and only receipt IDs returned at its gate. Direct maintenance uses
  `direct-maintainer-pending`, one resolved scope, optional versioned cursor,
  and fixed page ceilings. The typed drain receipt reports mode, scope,
  partitions inspected, cursor, pending/processed/unresolved counts, and
  bounded diagnostics; the separation is not an authentication claim.

- [x] **AC5.** A strict versioned topic contract requires immutable path-safe
  topic key, title, one observation-shaped current synthesis, structural scopes,
  competency facets, exact audience `project`, lifecycle, freshness, zero or
  one owning source, supporting sources, and provenance-bearing occurrences.
  Unknown fields and states fail closed.

- [x] **AC6.** Each promoted occurrence references its captured observation or
  legacy identity and records producer, semantic gate, normalized source and
  optional evidence digest when available, scope, observation time, and reviewed disposition
  without a transcript, private locator, or source instruction.

- [x] **AC7.** Topic lifecycle is exactly `active | needs_review | retired`.
  Only active privacy-approved topics referenced by the committed topic map are
  eligible for ordinary enquiry. Missing, unknown, contradictory,
  source-unavailable, or superseded state fails closed.

- [x] **AC8.** Freshness becomes review-required when a digest-bearing source
  is missing or changed, current evidence contradicts the synthesis, a stronger
  artifact supersedes it, or a human-set verification deadline passes. Age
  alone neither proves freshness nor retires a topic.

- [x] **AC9.** Retirement requires `canonicalized | enforced | obsolete |
  merged | invalidated`. Canonicalized, enforced, or merged retirement records
  confined successor references and verifies full claim coverage plus
  destination effectiveness for the same scope. A spec can absorb a normative
  requirement but not unshipped behavior. Partial absorption narrows the topic
  and leaves the remainder active.

- [x] **AC10.** Canonical reconciled storage is one pretty-printed UTF-8 JSON
  file per stable topic under `docs/knowledge/topics/`. There is no canonical
  topic JSONL stream, topic event replay, revision counter duplicating Git, or
  committed database.

- [x] **AC11.** `topics.index.json` contains no topic or occurrence bodies and
  is byte-deterministically rebuilt from valid topic headers. It records schema
  version, stable identity, path, routing headers, and expected Git blob
  identity. Topic files remain semantic authority; mismatch is an integrity
  failure. Richer local indexes are disposable, gitignored, and uncommitted.

- [x] **AC12.** Every knowledge read/write resolves the worktree and knowledge
  roots, proves containment using native path components, and rejects symlink
  or reparse-point escape, directory cycles, identity aliases, non-regular
  files, and I/O uncertainty. Stored scopes serialize as NFC-normalized
  repository-relative `/`-separated components, with `.` for root; drive, UNC,
  device, absolute, dot-segment, reserved-name, and trailing-dot/space aliases
  fail closed. Linux, macOS, and native-Windows fixtures prove equivalent
  serialization and matching.

- [x] **AC13.** One coarse worktree-local knowledge mutation lock covers all
  journal, topic, and map writes. It uses cross-platform exclusive file
  creation, bounded wait, random token plus file identity, conservative stale
  reclaim, and lost-lock detection. Malformed, foreign, symlinked, or
  non-regular locks are not reclaimed automatically, and release removes only
  the still-owned lock.

- [x] **AC14.** The writer acquires the lock before the deterministic re-read
  that controls a write, validates preconditions, writes same-directory
  temporary postimages, atomically replaces declared files, and verifies the
  result before release. Capture replaces one journal atomically. Distillation
  applies idempotent postimages in the exact order topic, complete map, terminal
  disposition. The writer derives an immutable `mutation_id` as lowercase
  SHA-256 over canonical UTF-8/JCS bytes of `mutation-id-v1`, capture identity,
  target topic key, and semantic mutation fields, excluding all derived IDs and
  digests. The occurrence stores that ID plus its ordinary evidence digest when
  available,
  but no proposal/postimage digest. The writer hashes the complete topic
  postimage containing the ID. The proposal stores
  expected topic pre/postimage digests; its own digest is lowercase SHA-256 over
  canonical UTF-8/JCS bytes with only the self-digest field omitted. The
  occurrence stores no proposal or postimage digest. There is no random replay
  input. Recovery without the canonical proposal returns `replay_required`;
  exact proposal replay deterministically reconstructs the ID,
  revalidates all digests, rebuilds a missing map or appends a disposition only
  when the current topic is the exact postimage, and otherwise refuses. A
  `promoted` disposition is invalid unless its exact topic occurrence and
  matching map already exist. Fault injection covers every
  replace boundary. Failures cannot alter the committed enquiry snapshot. Git
  merge/review handles cross-worktree contention.

- [x] **AC15.** `project-knowledge --distill` reads bounded pending captures,
  the body-free map, a bounded set of topics, and explicitly named confined
  sources. It proposes one terminal disposition and at most one topic mutation.
  A split or other irreducible multi-topic judgment is surfaced as a normal
  repository proposal with no guarded semantic guess.

- [x] **AC16.** Agent reasoning owns classification, reconciliation, synthesis,
  routing, and retirement. Deterministic code owns parsing, validation,
  confinement, privacy checks, idempotency, locking, atomic writes, recovery,
  and map rebuild. Code cannot invent a lesson, resolve a contradiction, choose
  an owning artifact, or retire a topic.

- [x] **AC17.** Unambiguous valid writes may update the working tree without a
  separate per-observation approval prompt and return through normal workflow
  verification/review. Privacy uncertainty, insufficient provenance, material
  contradiction, ambiguous routing, or stale preconditions leave semantic
  files unchanged and return a bounded reason. Only one committed coherent
  topic/map snapshot is queryable.

- [x] **AC18.** Before capture persists any body, semantic attestation and
  deterministic checks refuse known secrets, personal data, account/private
  identifiers, private URLs, organization hostnames, user-specific paths,
  unsafe Unicode, and instruction-shaped source passages. Typed identity fields
  allow only validated Git and contract identities. Optional scanner absence is
  not claimed as coverage; uncertainty refuses the body, diagnostics reveal no
  rejected content, and the baseline stores no raw quarantine.

- [x] **AC19.** Fixed v1 budgets cap a capture event at 16 KiB; a journal
  partition at 32 MiB and 50,000 events; retained journals at 240 partitions
  and 512 MiB; one pending-selection page at six partitions, 10,000 events, or
  16 MiB; one topic at 128 KiB; occurrences at 256 per topic; the topic corpus
  at 50,000 files and 512 MiB; the map and its enquiry routing read at 50,000
  entries and 32 MiB; one enquiry's selected-topic body reads at 12 bodies and
  1 MiB; and one envelope at 32 KiB. Paging is
  deterministic across complete partition windows. The versioned opaque cursor
  binds the scope/filter, ordered retained-partition names, exact content
  digests of the immediately preceding inspected partitions, and next partition
  offset. The selector emits no pending capture from a partition before reading
  and reconciling that whole partition. A single partition over the page event
  or byte ceiling refuses without partial output. Any bound-partition append,
  disposition, or reconciliation returns `cursor_stale`; restart from page one
  cannot silently skip a pre-existing pending capture. A full journal refuses
  capture with `journal_capacity`.
  Each script stops after 30 seconds and performs no
  automatic retry. Exhaustion returns no partial success. Limit changes require
  contract review rather than environment overrides.

- [x] **AC20.** Migration validates all current
  `docs/knowledge/patterns.jsonl` rows with the same strict UTF-8 JSON decoder
  as new contracts, rejecting duplicate keys, non-finite numbers, non-object
  rows, unsafe Unicode, and malformed lines before classification. Failure
  emits only redacted path/line diagnostics and no staged postimage. Each valid
  row is assigned exactly
  `active_import | needs_review_import | refused`. Counts equal input rows;
  each `active_import` or `needs_review_import` legacy identity/source becomes
  exactly one occurrence, ambiguous grouping is surfaced, refused rows persist
  no occurrence or new body, and source is unchanged on any
  validation, privacy, accounting, or interruption failure.

- [x] **AC21.** Migration stages a complete v1 topic tree and map, verifies
  deterministic accounting, and publishes them in one normal
  Git commit. Legacy-only `HEAD` keeps the old append path and has no ordinary
  enquiry. A staged/uncommitted v1 map blocks both old and new writers. A valid
  v1 map and matching topic blobs in `HEAD` activate the new capture path and
  make legacy JSONL read-only. Rollback never silently activates dual writers.
  Before any v1 observation is persisted, reverting the activation commit may
  restore the legacy-only path. Afterwards automatic reverse migration refuses
  without changing files; supported recovery is a reviewed forward change that
  preserves v1 journals/topics and keeps legacy append disabled. Pre-v1 tooling
  is outside this runtime guarantee.

- [x] **AC22.** Work-loop owns scratch and triage. At review, verified-slice,
  handoff, and closeout semantic gates it considers only new explicit scratch,
  routes/discards first, and hands each admitted contract to
  `project-knowledge --capture` through normal skill discovery. At a terminal
  gate it attempts `--distill` for the gate's capture receipts; unresolved
  judgment remains pending and is surfaced. A later explicit maintainer run may
  process bounded cursor-paged pending captures. Journal/topic/map changes
  return through verification, review, and commit. The existing closeout
  question remains byte-pinned.

- [x] **AC23.** `knowledge-competency-questions-v1` is exactly `CQ-ORIENT |
  CQ-DESIGN | CQ-CHANGE | CQ-DIAGNOSE | CQ-REVIEW | CQ-VERIFY | CQ-OPERATE |
  CQ-ROUTE | CQ-RETIRE`. `--enquire` requires a bounded task summary, resolved
  project/subproject scope, a free-form direct-human question or one known ID
  for skill use, and `routine | consequential` risk. Unknown skill IDs fail and
  absent/unknown risk defaults to consequential.

- [x] **AC24.** Ordinary enquiry resolves checked-out `HEAD` once, records its
  immutable commit/tree IDs, and reads map/topic blobs only from that tree.
  Callers cannot select another revision. It verifies the map's complete
  path/blob set before ranking, applies project, scope, lifecycle, privacy, and
  freshness filters, opens only bounded selected bodies, and compares their
  anchors with current confined sources. Enquiry never falls back to working
  tree topics, scratch, observation journals, or legacy JSONL.

- [x] **AC25.** The bounded delimited evidence envelope names topic identity,
  synthesis, scope, freshness, provenance, limitations, and source pointers and
  labels content as evidence, not instruction. Consequential enquiry verifies a
  digest-bearing owning source or abstains. `EnquiryReceipt` records only the
  question, selected topics, verified sources, budget, immutable corpus IDs,
  abstention, and caller. Enquiry has no feedback mutation path.

- [x] **AC26.** One discoverable `project-knowledge` skill selects exactly one
  progressive mode. `--capture` can call only `capture_observation`, cannot
  read topics, and rejects every other helper
  surface; `--distill`
  can read bounded journals/topics/sources and call the
  guarded writer; `--enquire` can read only committed topic/map/source data and
  cannot read journals or invoke a writer. Each mode loads only its own
  instructions and helper surface. Construction tests reject cross-mode calls.

- [x] **AC27.** `project-knowledge/SKILL.md` declares the exact informational
  union `metadata.boundaries: [filesystem_read_untrusted, filesystem_write]`.
  Because boundary metadata is not a runtime grant, mode isolation is enforced
  by dispatch and callable surfaces, not by treating the union as permission.
  Catalogue/schema tests preserve the metadata in every adapter projection.

- [x] **AC28.** A producer workflow discovers `project-knowledge` through its
  adapter's normal skill catalogue, submits the public contract in an
  agent-mediated handoff, and never imports or locates the private writer.
  Optional `[[pack.integrations]] kind = "handoff"` metadata may declare the
  seam but neither dispatches nor grants authority. If core is absent, the
  workflow reports one named skip and creates no fallback store. No workflow
  owns separate journal files.

- [x] **AC29.** Knowledge code has no network, arbitrary-command, credential,
  authorization, or permission-management capability. Retrieved or
  model-produced text cannot grant authority, select tools, approve mutations,
  widen scope, or write itself back as evidence.

- [x] **AC30.** The committed implementation contains no proper name or vendor
  identifier copied from the private comparison material supplied in the
  originating session, database dependency, embedding code, automatic
  loader, multi-project bank, new top-level directory, or separately
  discoverable capture/distil/enquire skills. Manual QA compares changed bytes
  with the private session value and records only pass/fail, never the value, in
  `docs/specs/project-knowledge-foundation/notes/manual-qa.md`.

- [x] **AC31.** At least two independent occurrences in one scope, or one
  verified observation with at least three failed/redirected attempts, can
  produce a bounded `CQ-ROUTE` suggestion—not an automatic edit—to the nearest
  canonical scoped agent-instruction file for a hard-to-discover existing
  route, or normal work intake for a missing verification oracle. A suggested
  task map names the authoritative start, generated outputs, and verification.
  Projections are not edited directly; effective enforcement permits retirement
  as `enforced`.

- [x] **AC32.** A map-only merge conflict is discarded and deterministically
  rebuilt from the merged topic tree. Same-topic conflicts require semantic
  resolution first. A two-worktree fixture proves distinct-topic changes
  rebuild to one byte-identical complete map; no hand-merged map is accepted.
  Conflicted journals use a private three-stage merge helper: exact event
  replays collapse, a capture body that does not hash to its `capture_id` refuses,
  body-derived kind/month must match the conflicted partition path,
  capture precedes at most one terminal disposition, conflicting dispositions
  refuse, and valid output is sorted by capture ID with capture first. Two-worktree tests
  cover distinct captures, exact replay, identity-integrity failure,
  wrong-partition events, and disposition collision.

- [x] **AC33.** Closed observation partitions remain unchanged in Slice 1.
  There is no automatic per-event deletion or compaction. A later reviewed
  retention rule may delete or compact only whole partitions after all captures
  have terminal dispositions, with explicit acknowledgement that Git history
  remains and checkout-local history is reduced.

- [x] **AC34.** End-to-end verification in a disposable repository demonstrates
  migration; gate-time scratch triage; published-contract capture; idempotent
  journal append; terminal disposition; topic creation and reconciliation; map
  rebuild; committed-only competency enquiry; source-drift suppression;
  retirement after a stronger artifact; interruption recovery; and proof that
  journals, working-tree-only topics, and rejected bodies are not retrieved.

- [x] **AC35.** The core release updates version authorities, changelog,
  progressive-skill roster, `[pack.evals]`, activation and near-miss evals,
  mode-specific behavior checks, LLM-judge coverage for distillation/enquiry,
  generated projections, and projection-drift checks required by
  `packs/AGENTS.md`.

- [x] **AC36.** Every evidence/freshness digest is a strict versioned object. A
  committed repository blob records kind `git-blob-v1`, the repository's
  allowlisted `sha1 | sha256` object format, and lowercase object ID. Other file
  evidence records kind `sha256-bytes-v1`, lowercase SHA-256 over exact bytes,
  and byte length. Hashing performs no text decoding, Unicode normalization,
  newline conversion, or re-serialization. Unknown algorithms, malformed IDs,
  ambiguous normalization, length mismatch, digest mismatch, and a missing
  digest for a consequential claim fail closed with diagnostics that reveal no
  source content.
  Fixed-byte vectors prove mutation-ID, topic-postimage, and proposal-digest
  construction is non-circular and byte-identical on Linux, macOS, and native
  Windows.

- [x] **AC37.** Every refusal or recoverable inconsistency returns a strict
  redacted `KnowledgeDiagnostic` with version, allowlisted reason code,
  persisted capture or mutation ID when safe, confined relative path and line when relevant,
  `retryable` boolean, and allowlisted recovery action. Codes include privacy,
  provenance, strict parsing, confinement, lock contention/loss,
  `journal_capacity`, `cursor_stale`, `replay_required`, postimage mismatch,
  map mismatch, and staged dual-writer activation. Unknown codes fail closed.
  The envelope never includes an observation/topic body, source excerpt,
  absolute path, exception string, or secret-shaped value.
  Pre-admission parsing, schema, provenance, privacy, unsafe-Unicode, and size
  failures never include a request-derived ID or content digest. Only an exact
  replay of an already admitted capture or a post-admission recovery failure
  may include its persisted `capture_id`.

## Assumptions

- Ordinary repository diffs remain the human review boundary for unambiguous
  journal and topic mutations.
- Git history plus observation events and topic occurrences are sufficient
  audit and recovery for Slice 1.
- Deterministic scoped lexical routing is adequate until measurement shows
  otherwise.
- Losing pre-gate or uncommitted scratch is preferable to silently writing it
  into an unapproved user-scope store.
