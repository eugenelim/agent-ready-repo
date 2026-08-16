# RFC-0077: Project knowledge lifecycle

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-02
- **Date closed:** 2026-08-13
- **Decision weight:** heavy — this proposal governs persistent agent-authored
  evidence across privacy, provenance, prompt-injection, filesystem, migration,
  and retrieval boundaries
- **Related:**
  - [`docs/architecture/knowledge-capture.md`](../architecture/knowledge-capture.md)
  - [`docs/product/research/agent-memory-lifecycle-methodology.md`](../product/research/agent-memory-lifecycle-methodology.md)
  - [`docs/knowledge/README.md`](../knowledge/README.md)
  - [RFC-0025](0025-work-loop-light-mode-and-risk-based-escalation.md)

---

## Reviewer brief

- **Decision:** Establish a portable lifecycle for capturing, distilling,
  retrieving, refreshing, routing, and retiring project knowledge.
- **Recommended outcome:** Accept a repo-scoped file-first baseline: free-form
  scratch is triaged at semantic workflow gates, `project-knowledge --capture`
  persists admitted observations through one typed event contract, and
  `project-knowledge --distill` later reconciles them into canonical topic JSON.
- **Change if accepted:** The current flat JSONL corpus migrates to per-topic
  canonical JSON with a deterministic body-free topic map. Typed observation
  events use classification/month JSONL journals. Core exposes capture,
  distillation, and enquiry as progressive modes of one `project-knowledge`
  skill, and explicit task-scoped enquiry is the only ordinary read path.
- **Affected surface:** Core knowledge contracts and progressive skill,
  observation and topic writers, work-loop capture integration, adopter
  knowledge files, migration, and later opt-in integrations with other packs.
- **Stakes:** Persistent prose can carry private data, false claims, and prompt
  injection into later sessions. A mandatory out-of-repository candidate store
  would also fail in managed environments that expose no durable writable user
  directory or memory service.
- **Review focus:** Whether persisted observations remain isolated from
  enquiry and authority; whether the single-writer, disposition, topic, and
  retrieval boundaries fail closed; and whether the first slice remains
  portable across tiny repositories, monorepos, and restricted environments.
- **Not in scope:** Transcript mining, automatic startup priming, workflow-owned
  candidate files, an external capture service, SQLite or another database,
  embeddings, the already-shipped closeout-question enhancement, or a
  multi-project bank.

## The ask

**Recommendation (Bottom Line Up Front, or BLUF):** Govern project memory as
`scratch → triage → capture → observation event → distil → topic → enquire →
refresh, route, or retire`. Scratch stays free-form and disposable. Captured
observations are durable, untrusted evidence awaiting disposition; only
reconciled topic JSON is eligible for enquiry as shared project knowledge.

**Situation:** The current work-loop asks what would have made completed work
materially better and appends selected patterns, gotchas, and antipatterns to
`docs/knowledge/patterns.jsonl`. Its writer validates, locks, lints, and
atomically replaces the file. Normal session start does not load the corpus.

**Complication:** The JSONL file is simultaneously the capture destination,
living knowledge, and lookup surface. It has no stable topic identity,
occurrence model, contradiction state, or source-relative freshness. A
previous draft treated capture and promoted knowledge as one store; another
placed candidates outside the repository, which assumes a writable durable
user location or service. Neither gives multiple workflows one safe contract,
one writer, and a repository-visible handoff boundary.

**Question:** How can the core pack improve capture and retrieval without
requiring memory infrastructure that some adopters cannot run or access?

**Answer:** Keep capture synchronous and make distillation separately
invocable. At a meaningful workflow gate, the agent reviews only explicit
scratch, discards noise, routes authoritative content, and submits reusable
residue to `project-knowledge --capture`. Its sole writer validates and appends
a typed event to the classification/month journal. At a workflow terminal gate
or explicit later run, `--distill` records a disposition and, when warranted,
reconciles the observation into a topic. A Git commit makes both journals and
the coherent topic/map snapshot durable; `--enquire` reads only eligible topics
from a committed snapshot and returns untrusted evidence.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | What does RFC-0077 govern? | The complete project-memory lifecycle | Capture, storage, retrieval, freshness, authority, and retirement form one safety chain. | This review | Confirmed |
| D2 | What is persisted? | Admitted observation events, their dispositions, canonical topics, and the body-free topic map | Repository-scoped journals survive normal Git handoff; enquiry still excludes unpromoted evidence. | This review | Confirmed |
| D3 | How do workflows capture? | Submit the published `CapturedObservation` contract to `project-knowledge --capture`; never write files directly | One public contract and one writer prevent format drift and competing ingestion paths. | This review | Confirmed |
| D4 | When does capture run? | At semantic completion gates over explicit scratch | RFC, ADR, spec, plan, verified-slice, review, and closeout boundaries can end a session; mechanical gates should not trigger repeated retrospection. | This review | Confirmed |
| D5 | What is the durable unit? | One stable topic with a current synthesis and provenance-bearing occurrences | Repeated observations are evidence about an evolving subject, not independent current truths. | This review | Confirmed |
| D6 | How are topics stored and published? | One pretty-printed JSON file per topic plus a deterministic body-free topic map; one Git commit publishes the coherent set | The current state remains directly reviewable, and Git already provides the multi-file snapshot boundary. | This review | Confirmed |
| D7 | How is the capability packaged and retrieved? | One progressive `project-knowledge` skill with separate `--capture`, `--distill`, and `--enquire` modes | Progressive disclosure preserves authority boundaries without making producer skills own storage mechanics. | This review | Confirmed |
| D8 | What happens when knowledge becomes authoritative elsewhere? | Route the owning change normally, then narrow or retire the topic with a pointer | Topics must not duplicate architecture, decisions, specifications, scoped agent task maps, verification tools, code, tests, CI, skills, or guides. | This review | Confirmed |
| D9 | How are richer memory backends handled? | Separate, optional governance after the portable baseline | Deferred capture requires an approved durable sink and changes privacy, availability, and operational boundaries. | Later RFC | Confirmed |

### Approval and publication gates

Accepting this RFC approves the lifecycle direction, not implementation or any
topic content. Before implementation starts, the two follow-on ADRs must be
accepted and the foundation spec and plan must be approved. The implementation,
legacy migration output, and activating v1 topic map then pass the repository's
normal PR/maintainer review and publish together in the commit that lands that
change. After activation, an unambiguous topic edit needs no additional
knowledge-specific prompt, but it remains an ordinary repository change subject
to that adopter's branch, commit, and review policy. Knowledge tooling neither
creates nor bypasses publication authority; a direct commit is sufficient only
where the repository already permits direct commits for comparable changes.

## Problem and goals

### Problem

Repository work produces reusable lessons at many decision points. Today only
work-loop closeout has a defined route into project knowledge, and every
accepted lesson becomes another independent row. Broadening automatic capture
before defining topic acceptance and retrieval would make the unsafe surface
larger.

Persisting admitted observations creates a second lifecycle, but avoiding it
loses useful evidence whenever distillation cannot finish in the originating
session or worktree. A user-directory queue fails when the agent cannot write
outside approved workspace roots. A service can solve that later, but it is an
additional runtime capability rather than a portable property of an in-process
skill. The repository is the only durable shared boundary the baseline can
reliably use.

The useful cut is therefore scratch versus captured evidence versus reconciled
knowledge. Scratch may still be lost before a semantic gate. After triage,
`--capture` records a bounded typed observation in the repository. That event
remains non-queryable until `--distill` gives it a terminal disposition and, if
appropriate, promotes its reusable residue into a topic.

### Goals

1. Let workflow-owned scratch remain free-form while giving every producer one
   published capture contract and one deterministic writer.
2. Run bounded retrospection at semantic gates without mining transcripts or
   replaying complete session history.
3. Make topic identity, occurrences, reconciliation, lifecycle, provenance,
   and source-relative freshness enforceable.
4. Separate classification/month observation journals from per-topic canonical
   JSON and its deterministic rebuildable topic map.
5. Retrieve task-relevant active topics only through explicit enquiry whose
   output is untrusted evidence.
6. Contain prompt injection, privacy leakage, project bleed, self-confirming
   claims, and authority amplification across write and read paths.
7. Intentionally retire knowledge that has been embodied in a stronger
   repository source of truth.
8. Keep the core pack stdlib-only and functional without a daemon, database,
   writable home directory, or network access.

### Non-goals

- Archiving conversations or deriving memory by mining transcripts.
- Guaranteeing recovery of scratch lost before a semantic gate.
- Persisting rejected scratch or raw quarantine bodies.
- Automatic session-start, resume, fork, or compaction-time topic loading.
- Automatically changing architecture, ADRs, specs, code, tests, CI, skills,
  conventions, or guides from a topic.
- Adding SQLite, another database, embeddings, a service, or a new dependency.
- Reworking the broad closeout question shipped in core 2.5.9.
- Defining an eventual multi-project bank.

## Authority and routing

Persistence never raises authority. A topic remains evidence below the
artifact authorized to define the concern and below runtime instructions or
permissions.

| Surface | Lifetime | Authority |
| --- | --- | --- |
| Conversation and tool output | Current run | Untrusted data |
| Free-form scratch | Current workflow or session | Working continuity only |
| Captured observation event | Cross-session until retention | Repository-published untrusted evidence; never an enquiry source |
| Active topic in the committed topic map | Cross-session, living | Repository-published untrusted evidence |
| Code, tests, ADRs, conventions, skills, architecture, specs, and guides | Their governed lifecycle | Canonical for their declared concern |
| System, developer, user, and runtime permission controls | Current execution | Instruction and authorization authority |

Arrival channel does not determine destination:

| Knowledge shape | Governing destination | Topic treatment |
| --- | --- | --- |
| User outcome, required behavior, or feature constraint | Brief or spec | Do not duplicate the normative contract |
| Supporting evidence for a proposed feature or decision | The owning RFC's `NNNN-notes/`, spec's `notes/`, or cited product research | Preserve only independently reusable practice residue |
| Current solution structure or subsystem behavior | Architecture documentation | Topic may point to it, then narrow or retire |
| Decision and rationale | ADR | Topic does not restate the decision |
| Short repository navigation or task map | Nearest scoped canonical agent-instruction file | Name where to start, generated outputs, and verification; never edit an IDE projection directly |
| Repeating procedure | Skill or convention, according to repository source-of-truth rules | Keep procedural authority out of topics and agent navigation maps |
| Enforceable invariant or verification oracle | Code, test, lint, CI, contract probe, or diagnostic tool | Prefer the narrowest effective executable control |
| User-facing operation | Guide | Topic does not become shadow usage documentation |
| Reusable practice lesson not owned above | Project topic | Retain as repository-published untrusted evidence |

## Capture and gate-time triage

### Scratch

Scratch is intentionally free-form. It can contain fragments, one-line review
notes, failed assumptions, or reminders. Workflows should capture enough to
recover four things later: the lesson, the conditions under which it applies,
the repository evidence, and the future question it might answer. Scratch has
no schema and is never an enquiry input.

Agents review scratch rather than transcripts. A gate retrospective must not
reconstruct observations from arbitrary messages or tool output after the
fact.

Scratch should also preserve a friction signal when the agent spent several
failed or redirected attempts locating the owning source, distinguishing source
from generated output, or discovering the right verification route. One
verified high-cost episode or repeated independent occurrences in the same
scope can justify a `CQ-ROUTE` suggestion even when the lesson is already known
by the end of the task.

A failed mechanical gate does not distil itself. The workflow may add explicit
scratch describing a missing oracle, false signal, expensive manual check, or
verification tool that existed but was not discoverable. The next semantic gate
triages those notes with `CQ-VERIFY`: wire an existing check into the loop,
propose scoped work to build or improve the check, or discard the note. Backlog
belongs in the repository's work tracker or a spec, not in standing agent
instructions.

### Semantic gates

Triage runs when work reaches a stable meaning boundary:

- RFC completion or approval;
- ADR acceptance;
- spec approval;
- plan approval;
- completion of a verified implementation slice;
- completion of review; and
- work-loop closeout, explicit handoff, or a known pre-compaction boundary.

Lint, typecheck, individual test, and other mechanical gates do not trigger
triage. Reconsidering the same unstable note after every command would create
duplicate work and unnecessary model context.

At each semantic gate, the owning workflow:

1. reads only scratch accumulated since its previous semantic gate;
2. discards observations disproved, task-local, obvious, vague, unsafe, or
   already fully represented by the artifact just completed;
3. routes normative or authoritative content to its owning artifact;
4. asks which future competency question the residue would answer; and
5. shapes each retained lesson into a `CapturedObservation` and invokes
   `project-knowledge --capture`; and
6. includes any observation-journal edit in the next verification, review, and
   commit barrier rather than appending after a supposedly final review.

At a workflow terminal gate, the caller attempts
`project-knowledge --distill` for the gate's capture receipts. Irreducible
judgment remains explicitly `pending`, is reported with its receipt, and does
not block unrelated workflow completion. A core maintainer can later run
`project-knowledge --distill --pending` over bounded cursor-paged partitions by
project scope. Capture never claims that distillation completed merely because
the originating session ended.

The pending-drain request uses selection mode `direct-maintainer-pending`, one
resolved scope, an optional versioned cursor, and fixed page ceilings. Workflow
handoffs may use only `workflow-receipts` with receipt IDs returned at their
gate and cannot select the pending corpus. The drain receipt reports mode,
scope, partitions inspected, cursor, pending/processed/unresolved counts, and
bounded diagnostics. This is interface separation and auditability, not an
authentication claim.

No separate per-observation approval prompt is required after the workflow has
performed gate triage. The event remains non-queryable and appears in the
ordinary repository diff. Privacy uncertainty or invalid provenance refuses
capture without storing the body. A later material contradiction or ambiguous
topic mutation leaves topics unchanged and is surfaced by distillation.

### CapturedObservation contract

`CapturedObservation` is the published strict-JSON request contract for
`project-knowledge --capture`. Successful capture wraps it in an immutable
`observation.captured` event. The minimum request carries:

- schema version; the producer fields below; the strict contract carries no
  storage identity chosen by the producer;
- concise lesson and practice kind (`pattern`, `gotcha`, or `antipattern`);
- applicable repository or subproject scope;
- one or more competency-question facets;
- destination hint for canonical routing;
- normalized repository-relative provenance and an evidence digest when
  available; these remain occurrence evidence fields, while durable occurrence
  identity is the `mutation_id` derived by the guarded mutation protocol;
- source-relative freshness anchor; and
- producer workflow and semantic-gate kind; and
- observation time as an RFC 3339 UTC instant; and
- semantic privacy attestation; and
- optional bounded friction evidence: failed or redirected attempt count and
  the stable route that would have prevented the investigation.

The originating workflow performs editorial triage. The capture mode validates
and records; it does not decide topic membership. The distillation mode performs
semantic reconciliation. One private deterministic writer validates
mode-specific mutations, confines paths, enforces limits, serializes writes,
and returns typed receipts. A script must not invent a lesson, decide a
contradiction, or silently overwrite a synthesis.

After all strict syntax, schema, provenance, and privacy admission checks pass,
core derives `capture_id` as
`kco-YYYYMM-<64 lowercase hex>`, where the month comes from observation time and
the suffix is SHA-256 over the canonical UTF-8/JCS producer request. The ID is
absent from its own preimage. Producer workflows never choose storage identity.

Digest fields use a versioned preimage contract. A committed repository source
uses its Git blob identity, including the repository's declared object format.
Other file evidence uses `sha256-bytes-v1`: lowercase SHA-256 over the exact
file bytes plus a separately recorded byte length. Text is never decoded,
normalized, or re-serialized before hashing. Unknown algorithms, ambiguous
normalization, length mismatch, and missing digests for consequential claims
fail closed.

After deriving the partition, capture checks for an existing identity first.
An exact replay returns its receipt regardless of age. Only a new capture must
be no more than seven days before writer UTC time, no more than five minutes in
the future, and not before the repository's v1 activation commit. This window
accommodates a long workflow without letting request-controlled dates exhaust
arbitrary month partitions. General historical import is out of scope and
requires separate governance; the v1 migration handles only the existing
legacy corpus.

### Observation journals and dispositions

Observation storage is partitioned by the captured practice classification and
UTC observation month from that immutable validated request field:

```text
docs/knowledge/observations/<pattern|gotcha|antipattern>/YYYY-MM.jsonl
```

The partitions bound append conflicts without assigning file ownership to a
workflow. Producer workflow and semantic gate are fields, never routing paths.
Each non-empty line is a versioned event. Slice 1 supports
`observation.captured` and `observation.dispositioned`. A capture is `pending`
until the latter references it and records at most one terminal result:
`promoted | duplicate | routed | rejected | superseded`. Promotion names the
topic occurrence created or updated. Rejection records a bounded reason code,
not rejected source material.

Capture identity is the core-derived `capture_id`; partition is not part of it.
An exact canonical request deterministically resolves to the same month, ID,
partition, event, and receipt even across writer-time month boundaries. Any
changed kind, observation time, or content is a distinct observation rather
than identity reuse and is reconciled by distillation. SHA-256 collision
resistance avoids an unbounded global scan or committed identity index.
Observation journals are never read by ordinary enquiry. Closed partitions are
retained in Slice 1; later whole-partition deletion or compaction requires a
reviewed retention rule and terminal disposition for every captured event.

The v1 ceilings are 32 MiB and 50,000 events per partition, 240 retained
partitions and 512 MiB across journals, and six explicitly selected partitions,
10,000 events, or 16 MiB per pending-selection page, whichever is reached
first. Exceeding a write ceiling refuses capture as `journal_capacity`.
`--distill --pending` pages deterministically with a versioned opaque cursor.
The cursor advances only between complete partition windows. It binds the
scope/filter, ordered retained-partition names, exact content digests of the
immediately preceding inspected partitions, and next partition offset. The
selector reads and reconciles a whole partition before emitting any of its
pending captures. A single partition over the page event or byte ceiling
refuses without partial output. Any append, disposition, or journal
reconciliation that changes a bound partition returns `cursor_stale`; the
maintainer restarts from the first page. No cursor silently skips a pre-existing
pending event.

Branch reconciliation is deterministic. A private merge helper consumes the
three Git stage blobs for one conflicted confined partition, parses each with
the strict decoder, collapses byte-identical event replays, and groups events by
`capture_id`. Different capture bodies for one ID, a disposition without its
capture, different terminal dispositions, or a capture whose body-derived
kind/month does not match the conflicted partition refuse the merge. Valid output
sorts by capture ID, with capture before disposition. Normal append order is
not semantic authority.

## Topics, occurrences, and lifecycle

A topic is one narrow, independently verifiable practice lesson with stable
identity. An occurrence is one attributable observation supporting or
challenging that topic.

Each topic records:

- immutable stable key and human-readable title;
- current observation-shaped synthesis;
- one or more structural scopes and competency-question facets;
- lifecycle and freshness state;
- zero or one owning canonical source;
- supporting sources and integrity digests where available;
- provenance-bearing occurrences that link back to captured or migrated
  observation identities; and
- retirement or supersession references where applicable.

When distillation closes an observation, it records exactly one terminal
disposition. `duplicate`, `routed`, `rejected`, and `superseded` close it
without creating a new current claim. `promoted` names the one topic occurrence
created or updated and may create a topic, attach evidence, revise synthesis,
mark contradiction, narrow after partial absorption, or retire. A proposed
split or other irreducible multi-topic judgment remains pending and is surfaced
without a terminal semantic guess.

The minimal lifecycle is:

- `active` — eligible for ordinary enquiry only when referenced by the
  committed topic map;
- `needs_review` — conflicting, unverifiable, privacy-uncertain, or stale;
  excluded from ordinary enquiry; and
- `retired` — no longer applicable or fully embodied elsewhere; retained for
  history and diagnostics but excluded from ordinary enquiry.

Freshness is source-relative, not age-relative. A topic needs review when a
digest-bearing source changes or disappears, current repository evidence
contradicts it, a canonical artifact supersedes it, or a human-set verification
deadline passes. Age alone neither proves freshness nor retires knowledge.

Retirement is intentional and destination-relative. An accepted ADR can absorb
a decision; current architecture can absorb verified current structure; an
accepted spec can absorb a normative requirement but not an unshipped behavior;
and code, tests, CI, skills, conventions, or guides must be present and effective
for the topic's scope. Draft or future intent can trigger routing or
`needs_review`, not retirement. Partial absorption narrows the topic to the
remaining independently useful residue.

A recurring or high-friction workflow lesson may route to a short task map in
the nearest scoped canonical agent-instruction file. The map names what to read
or change first, which outputs are generated, and how to verify the work. The
repository decides whether that source is `AGENTS.md`, `AGENTS.local.md`, or
another canonical instruction surface and projects platform-specific files from
it where required. Distillation only suggests the destination; it does not edit
standing instructions. Once the instruction is effective, or a test/lint/CI
control enforces the lesson, the topic narrows or retires.

Verification gaps follow the same lifecycle. If a suitable oracle exists but is
missed, the owning instruction or work-loop gate should name it. If the oracle
is absent or unreliable, normal work intake creates a scoped test, lint, CI,
contract probe, or diagnostic-tool change. The topic remains active as evidence
until the control is effective, then retires as `enforced` with the control as
its successor.

## Canonical files and migration

```text
docs/knowledge/
├── README.md
├── patterns.jsonl          # legacy curated corpus during migration
├── observations/
│   ├── pattern/YYYY-MM.jsonl
│   ├── gotcha/YYYY-MM.jsonl
│   └── antipattern/YYYY-MM.jsonl
├── topics/
│   └── <namespace>/
│       └── <stable-topic-key>.json
└── topics.index.json       # deterministic body-free topic map / commit manifest
```

Observation journals are append-oriented event evidence. The writer implements
append as a locked read-validate-write to a same-directory temporary file and
atomic replacement, so a rejected or partial line is never exposed. Partition
names derive only from validated kind and the immutable RFC 3339 UTC
observation time in the request, never writer wall-clock time or a
caller-supplied path. Journals are durable only after the repository's normal
commit boundary and are never a topic lookup surface.

Topic files are pretty-printed UTF-8 strict JSON. They hold reconciled current
state, so JSON is preferable to an append-only format: enquiry can read one
coherent object, lifecycle changes do not require event replay, and Git review
shows the resulting topic. Occurrences preserve evidence history without
adopting event sourcing.

`topics.index.json` is a portable topic map containing no bodies. It names the
published topic paths, stable identities, Git blob identities, routing headers,
and schema version. A builder deterministically produces its prospective bytes
from valid working-tree topics. Once the topic files and map land in one Git
commit, that commit is the single publication point: ordinary enquiry reads the
map and topic blobs from the same committed tree and ignores working-tree
edits. Topic files remain the semantic source of truth; a map mismatch is an
integrity failure, not permission to improvise. Optional richer local search
indexes are disposable, gitignored, and never canonical or committed.

The existing `patterns.jsonl` contains curated durable observations, not raw
scratch. Migration accounts for every non-empty row as exactly
`active_import`, `needs_review_import`, or `refused`; unknown dispositions fail
closed and the three counts must equal the input row count. Privacy-refused rows
persist no new body. Migration then:

1. validate the complete source before writing with the strict UTF-8 JSON
   decoder used by new contracts, rejecting duplicate keys, non-finite numbers,
   non-object rows, unsafe Unicode, and malformed lines with redacted
   path/line-only diagnostics;
2. preserve every `active_import` or `needs_review_import` legacy identifier
   and source as exactly one occurrence; a `refused` row contributes only to
   redacted accounting and persists no occurrence or body;
3. group records into proposed narrow topics and surface ambiguous merges;
4. stage a complete topic tree and deterministic index while JSONL remains
   canonical;
5. review accounting and topic diffs through the normal repository workflow;
6. publish the complete topic tree and map in one normal Git commit, which is
   the per-repository activation point; and
7. freeze the old JSONL file as migration evidence or remove it in a later
   reviewed cleanup after count-preserving verification.

The first slice introduces observation journals only as part of the activated
v1 layout. A repository with only legacy JSONL keeps the legacy append path. A
staged but uncommitted v1 map blocks both writers so a workflow cannot choose
between layouts. Ordinary enquiry continues from the last valid committed v1
snapshot when one exists and is unavailable in a legacy-only repository. Once
`HEAD` contains a valid v1 map, new work-loop observations use `--capture`, and
the legacy `patterns.jsonl` becomes read-only migration evidence.
Before the first v1 observation is persisted, the activation commit may be
reverted to the legacy-only state. After that boundary, the portable core
refuses automatic reverse migration: recovery is a reviewed forward change that
preserves v1 journals and topics and keeps legacy append disabled. Checking out
pre-v1 tooling cannot be made safe by code that is no longer present and is not
a supported rollback path.

## Progressive skill and authority boundaries

Core exposes one `project-knowledge` skill whose first action selects exactly
one progressive mode. Mode instructions and scripts are loaded only after that
selection:

- `--capture` accepts one `CapturedObservation`, appends one validated capture
  event, and returns a `CaptureReceipt`. It cannot read or write topics.
- `--distill` reads bounded pending observations, topics, and named sources;
  it records a disposition and may apply one validated topic mutation. It
  cannot retrieve evidence for an unrelated task.
- `--enquire` reads eligible committed topics and returns bounded evidence. It
  cannot read observation journals or invoke any writer.

The skill declares the informational boundary union
`[filesystem_read_untrusted, filesystem_write]` because catalogue metadata is
not a runtime permission grant and has no per-mode form. Least privilege is
enforced by dispatch and disjoint callable helpers, with construction tests
that reject cross-mode reads and writes. The union never authorizes enquiry to
reach journals or a writer.

Producer workflows own scratch, triage, and gate timing. They discover the
core skill through the normal adapter skill catalogue and invoke `--capture`
through an agent-mediated handoff. A pack may declare that seam through
`[[pack.integrations]]`; the metadata does not dispatch, auto-install core, or
grant write authority. If capture is optional and core is unavailable, the
workflow reports a named skip and does not invent another store. Workflows
never locate or call writer scripts directly.

`project-knowledge --distill` may read bounded captured events, the body-free
working-tree map, a bounded set of candidate topics, and named repository
sources. Only the private guarded writer appends the disposition, applies a
validated single-topic mutation, and rebuilds the prospective map. Split and
other multi-topic semantic changes are surfaced as a proposed normal repository
edit in Slice 1 rather than partially applied by the writer.

`project-knowledge --enquire` requires a concrete task summary, structural scope, and
competency question. In ordinary mode it resolves the checked-out worktree's
`HEAD` once, records that immutable commit and tree identity, and reads
`topics.index.json` plus selected topic blobs only from that tree. Agent or skill
callers cannot supply another revision. Arbitrary historical or alternate-tree
lookup is a separate explicit human diagnostic mode and never feeds ordinary
agent context. Enquiry compares the map's path and blob-identity set with that
tree without opening every body, then applies
hard project, scope, lifecycle, privacy, and freshness filters before ranking.
It opens only selected bodies and returns a bounded evidence envelope containing
topic identity, provenance, freshness, limitations, and source pointers. Before
returning a selected topic, it compares its source-relative anchors with the
current confined worktree sources; an uncommitted source change can therefore
suppress stale committed knowledge without making an uncommitted topic
queryable.
The complete body-free map has its own 32 MiB routing-read ceiling. The separate
1 MiB enquiry body-read ceiling applies only after routing and covers at most 12
selected topic bodies; a maximum conforming map therefore remains queryable.

The versioned contract `knowledge-competency-questions-v1` defines when project
memory helps agentic development:

| ID | Question |
| --- | --- |
| `CQ-ORIENT` | What repository-specific constraints or conventions affect this task? |
| `CQ-DESIGN` | What prior lessons should shape this design or tradeoff? |
| `CQ-CHANGE` | What couplings, invariants, and failure modes matter before changing this scope? |
| `CQ-DIAGNOSE` | What previous symptoms, causes, and failed approaches resemble this problem? |
| `CQ-REVIEW` | What recurring risks should this review inspect? |
| `CQ-VERIFY` | What evidence proves the change correct, and where is the current verification path insufficient? |
| `CQ-OPERATE` | What build, release, recovery, or operational lessons apply? |
| `CQ-ROUTE` | Which stronger repository artifact or narrowly scoped agent task map should own this knowledge? |
| `CQ-RETIRE` | Has a stronger artifact fully absorbed the topic, and what residue remains? |

Humans may enquire directly with a stable ID or free-form question. Selected
skills use only known v1 IDs, declare a decision moment and query/refinement
budget, and make the invocation visible. Every call returns an `EnquiryReceipt`
containing retrieval-time facts: question, topic IDs, verified sources, budget,
resolved commit/tree identities, abstention, and caller workflow. Whether the
evidence changed the approach is post-use information; Slice 1 gives enquiry no
feedback write path. The caller may record that result in explicit scratch for
later semantic-gate triage. Session start, status, capture, credential, and
authorization surfaces never enquire automatically.

Retrieved text is evidence, not instruction. It cannot change permissions,
select tools, approve actions, override higher-priority instructions, or write
back to memory. Consequential enquiry requires a resolvable digest-bearing
owning source and verifies it before returning the claim; otherwise it abstains.

Structural scope uses a platform-neutral serialized path: NFC-normalized,
repository-relative components separated by `/`, with `.` denoting project
root. This is an interchange form, not a POSIX-host assumption. Windows `\`
input is normalized; drive, UNC, device, reserved-name, case-alias,
trailing-dot/space, and reparse-point behavior is handled using native path
semantics. Matching compares resolved path components, never raw string
prefixes. A topic matches when one of its declared scopes is the same as or an
ancestor of the requested task scope. A root request is an explicit
whole-project query and remains subject to normal result budgets; unresolved,
absolute, traversing, symlink/reparse-escaped, or cross-project scope fails
closed.

## Security, privacy, and recovery

Every persisted and displayed field is untrusted input. The writer fails closed
on invalid Unicode, control or invisible payloads, malformed strict JSON,
unknown schema or lifecycle values, path escape, symlink redirection, oversized
input, missing project scope, missing provenance, privacy-policy failure, and
stale preconditions. The resolved `docs/knowledge` root itself must remain under
the resolved worktree root; confining only relative to a redirected knowledge
directory is insufficient.

Known secrets, personal information, private locators, account identifiers,
organization hostnames, and instruction-like source passages are not persisted.
The agent records a paraphrased, minimized practice observation with a
repository-relative source pointer and supplies a semantic privacy attestation.
The deterministic boundary independently rejects known secret patterns, email
addresses, absolute or user-specific paths, private locators, and
account/person/private identifier-shaped values in content/provenance fields,
plus unsafe Unicode and source passages. Typed identity fields allow only
validated Git commit/tree/blob and contract/capture/mutation/topic IDs; prose gains no
allowance by resembling one. An attestation is not a bypass: if either layer is
uncertain or refuses, no new body is written. This is the
portable minimum; an available sanctioned scanner may add evidence but is not
silently assumed.

Capture, topic mutation, and enquiry enforce:

- repository and subproject confinement before relevance ranking;
- fixed v1 resource ceilings for files, bytes, occurrences, opened bodies,
  output, retries, and elapsed work;
- one worktree-local knowledge mutation lock implemented with cross-platform
  exclusive lockfile creation, bounded wait, token-and-file-identity ownership,
  conservative stale reclaim, and lost-lock detection;
- same-directory temporary writes and atomic replacement for every journal,
  topic, and map file;
- stale-precondition checks before applying a synthesis change;
- no network or arbitrary-command authority in knowledge scripts;
- bounded, delimited evidence output; and
- no self-reingestion of model output as independent evidence.

Failures return a strict redacted `KnowledgeDiagnostic`, not raw exceptions.
Its allowlisted fields are version, reason code, safe persisted capture or mutation ID, confined
relative path/line where relevant, retryability, and recovery action. Privacy,
parsing, confinement, lock, capacity, cursor, replay, postimage, map, and
activation failures have explicit codes. Bodies, excerpts, absolute paths,
exception strings, and secret-shaped values are forbidden.
Pre-admission parsing, schema, provenance, privacy, unsafe-Unicode, and size
failures never return a request-derived ID or content digest. Only an exact
replay of an already admitted persisted capture or a post-admission recovery
failure may expose its persisted `capture_id`.

The lock begins before the deterministic read whose result controls a write and
ends after postimage verification. Agent reasoning never runs while it is held.
On acquisition, the writer re-reads all declared preconditions and refuses a
stale proposal. A malformed, foreign, symlinked, or non-regular lock is never
reclaimed automatically. Releasing a lock removes only the file whose identity
and random ownership token still match this hold.

The working tree may contain a coherent proposal or an interrupted,
non-queryable edit. Ordinary enquiry reads the last committed topic/map
snapshot, so a topic and its map become visible together and a crash cannot
publish a partial corpus. Capture is one atomic journal replacement.
Distillation applies idempotent ordered postimages: topic first, complete map
second, terminal disposition last. The writer derives an immutable
`mutation_id` as lowercase SHA-256 over canonical UTF-8/JCS bytes of
`mutation-id-v1`, capture identity, target topic key, and the proposed semantic
mutation fields, excluding every derived ID and digest. The occurrence stores
that ID alongside its ordinary evidence digest, never a proposal/postimage
digest. The writer then hashes the complete strict-JSON topic postimage
containing the ID. The canonical proposal stores the expected topic preimage
and postimage digests, and its `proposal_digest` is SHA-256 over canonical
UTF-8/JCS bytes with only `proposal_digest` omitted. The graph is acyclic and
has no random replay input. After interruption, an invocation without the
canonical proposal refuses as `replay_required`; exact replay of the same
semantic proposal deterministically reconstructs the mutation ID and
re-validates capture and preconditions. It creates a missing map or appends the
matching disposition only when the current topic is the exact expected
postimage; otherwise it refuses. A `promoted` disposition is invalid unless its
exact topic postimage, occurrence, and matching map already exist.
The lock coordinates only writers in that
worktree; Git merge and normal review resolve cross-worktree or cross-branch
contention. Git history, captured events, dispositions, and topic occurrences
provide recovery for published state. The legacy JSONL file remains untouched
until migration accounting and the resulting topic diff have been reviewed.

Every topic mutation rebuilds the shared map, so unrelated branches can
conflict on that derived file. A map-only conflict is never hand-merged: discard
it and deterministically rebuild from the already merged topic tree. Resolve any
same-topic conflict semantically first, then rebuild. This keeps the map hot but
mechanical without adding shards or another dependency.

## Rollout

### Slice 1 — Project knowledge foundation

The smallest sound slice includes:

1. a published strict `CapturedObservation` JSON Schema plus versioned event,
   disposition, topic, occurrence, mutation, map, and enquiry contracts;
2. the progressive `project-knowledge` skill with separately loaded
   `--capture`, `--distill`, and `--enquire` modes;
3. classification/month observation journals, capture receipts, terminal
   dispositions, one private cross-platform writer, and idempotent replay;
4. per-topic canonical JSON, deterministic topic-map rebuild, and committed Git
   snapshot publication semantics;
5. count-preserving migration from the current curated JSONL corpus;
6. explicit bounded enquiry with competency questions and abstention;
7. work-loop cutover from its private JSONL writer to semantic-gate
   `--capture`, plus one bounded terminal `--distill` handoff, without changing
   the shipped closeout question;
8. recurrence/high-friction routing to scoped agent task maps or verification
   tooling work intake; and
9. adopter documentation, tests, migration checks, and security evaluations.

The slice does not integrate additional skills automatically. Maintainers can
invoke capture or distillation explicitly until each originating workflow
receives a separately reviewed handoff integration.

### Integration slices — semantic gates in other workflows

After the foundation proves safe, update selected authoring, research, review,
and operational skills. Each integration owns its free-form scratch and gate
timing, constructs the shared observation request, and hands it to `--capture`.
It may request a bounded terminal distillation pass over its returned capture
IDs. It does not read topics unless it separately declares an enquiry question
and read boundary.

### Optional external capture backend

The repo-scoped journal survives normal commit and handoff but cannot preserve
scratch before a semantic gate or an uncommitted capture after a worktree is
discarded. An external backend may address that gap only through separate
governance of project identity, privacy, deletion, availability, and
reconciliation with the repository journal. Core does not probe or write user
directories implicitly and never claims external durability when the capability
is absent.

### Separate RFC — Multi-project bank

A bank changes tenancy, audience, privacy, ownership, and deletion semantics.
Only reviewed, sanitized topics may be explicitly exported. A receiving project
treats imported material as untrusted evidence and adopts it through its own
distillation boundary. No bank content inherits authority from its source
project.

## Options considered

### Capture continuity

| Option | Consequence | Decision |
| --- | --- | --- |
| Keep only free-form scratch and current JSONL append | Minimal change, but no topic model or safe enquiry | Reject |
| Give each workflow its own candidate file | Avoids a shared append target but creates competing formats, retention rules, and ingestion paths | Reject |
| Require a user-directory queue or memory service | Enables asynchronous distillation but fails in restricted environments and adds infrastructure | Reject as baseline |
| Persist one event file per observation | Simple concurrency, but file and Git-history volume scale with events | Reject |
| Append typed events to classification/month journals through one writer | Portable repository handoff with bounded hot files; adds explicit disposition and retention duties | Adopt |

### Canonical topic format

| Option | Consequence | Decision |
| --- | --- | --- |
| One shared JSONL file | Easy append, but remains a hot file and mixes independent topics | Reject |
| One JSONL event stream per topic | Preserves immutable events, but requires replay, compaction, and a materialized current view | Reject for now |
| One JSON object per topic | Direct current-state reads and review; occurrences retain evidence history | Adopt |
| SQLite or another database | Stronger queries and transactions, but adds runtime and portability cost before demonstrated need | Defer |

### Retrieval

| Option | Consequence | Decision |
| --- | --- | --- |
| Load all knowledge at startup | Maximum standing influence, token cost, and poisoning blast radius | Reject |
| Let every skill search implicitly | Hidden cost and authority flow | Reject |
| Explicit competency-question enquiry | Bounded and auditable, with clear abstention | Adopt |

## Risks and what would make this wrong

1. **Pre-gate scratch can still disappear.** An abrupt session end before
   capture loses the note. Revisit an external backend only when a supported
   durable capability exists and measured loss justifies its added boundary.
2. **Semantic gates become ceremony.** Too many prompts create duplicates and
   token cost. Integrations must target stable meaning boundaries, read only
   new explicit scratch, and do nothing when no lesson qualifies.
3. **Captured observations become a retained attack surface.** Strict privacy
   checks run before append, journals are excluded from enquiry, dispositions
   are bounded, and closed-partition retention remains explicit rather than
   silently indefinite.
4. **Automatic topic writes overreach.** Agent reconciliation can be wrong.
   Strict validation, source pointers, stale-precondition checks, committed-only
   enquiry, ordinary Git policy, and judgment-case refusal limit the blast
   radius.
5. **Topics duplicate stronger artifacts.** The corpus can become shadow
   architecture or specifications. Destination routing and intentional
   retirement are required lifecycle operations, not editorial suggestions.
6. **The committed topic map drifts.** Topic files remain semantically
   authoritative; full lint rejects mismatch, while enquiry compares the map's
   complete path/blob set to the committed Git tree and verifies selected bodies.
7. **Per-topic files still conflict on popular subjects.** A conflict on one
   topic is meaningful semantic contention. Split only when the claim is
   independently verifiable, not merely to avoid Git conflicts.
8. **Enquiry amplifies stored instructions.** Evidence is delimited,
   non-authoritative, bounded, and verified against current sources before
   consequential use.
9. **Instructions become a knowledge backlog.** Routing thresholds create a
   suggestion only. Missing tooling goes through work intake; scoped agent
   instructions state durable routes, not future work.

Revisit the file-first decision if measured corpus size, enquiry latency, or
write contention violates published budgets, or if supported environments
provide a portable durable state service with an enforceable privacy contract.

## Evidence and prior art

### Repository evidence

- The existing writer resolves and confines the repository root, validates
  fields, locks the read-modify-write sequence, lints before and after, and
  atomically replaces `patterns.jsonl`. This demonstrates that deterministic
  file safety is already an established core pattern.
- The current work-loop writes only after a closeout worth-keeping judgment and
  deliberately avoids normal session-start replay. The new design preserves
  both editorial selection and explicit retrieval.
- The research synthesis in
  [`agent-memory-lifecycle-methodology.md`](../product/research/agent-memory-lifecycle-methodology.md)
  supports staged consolidation, stable topics with occurrences,
  source-relative freshness, namespace-first retrieval, and no authority
  amplification.
- This managed workspace exposes repository and approved temporary writes but
  not a general durable user-state write capability. That supports a
  repo-scoped capture journal while falsifying an external spool as a universal
  baseline.

### External prior art

- [OpenAI Agents SDK memory](https://openai.github.io/openai-agents-python/sandbox/memory/)
  separates working history from generated durable memory and supports a
  two-phase generation flow. The relevant lesson is staged formation, not a
  requirement to adopt its backend.
- [LangGraph memory](https://docs.langchain.com/oss/python/langgraph/memory)
  distinguishes thread-scoped checkpoints from cross-thread stores and
  separates memory formation from retrieval.
- [OWASP prompt-injection guidance](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
  treats retrieved and externally supplied text as an instruction-confusion
  boundary. Persisted topics therefore remain delimited evidence.
- [JSON Lines](https://jsonlines.org/) remains appropriate for the current
  legacy record stream and possible future event transport, but it does not by
  itself provide reconciled current-topic semantics.
- [OASIS topic-oriented maps](https://docs.oasis-open.org/dita/v1.0/archspec/maps.html)
  separate reusable single-subject topic units from maps that select, organize,
  and provide context for them.
- [ISO Topic Maps](https://isotopicmaps.org/sam/sam-model/) separates subject
  identity from occurrences and defines identity-driven merging, supporting the
  stable-topic/occurrence model without requiring its full graph machinery.
- [Git's data model](https://git-scm.com/docs/user-manual) publishes one tree
  snapshot per commit. [Lucene commit points](https://lucene.apache.org/core/10_0_0/core/org/apache/lucene/index/IndexCommit.html)
  similarly make new content visible only after a small manifest is committed.
  Together they support a committed topic map as the publication boundary
  instead of a custom multi-file filesystem transaction.

### De-risk result

The riskiest assumption was that safe cross-workflow capture required an
external durable path. It failed against the active enterprise permission
model: no such path or memory API is universally available, while the repository
is writable and reviewable. The foundation therefore uses synchronous capture
into repo-scoped classification/month journals and lets distillation run either
at the workflow terminal gate or later. External pre-gate durability remains an
optional capability.

## Open questions

1. **Which non-work-loop skills integrate first?** Recommended default:
   authoring skills with explicit approval gates, followed by review and
   research workflows. Owner: core maintainer. Decide by: integration-slice
   planning.
2. **What deterministic lexical routing is sufficient for large monorepos?**
   Recommended default: scoped index fields and bounded keyword matching until
   measurement proves otherwise. Owner: foundation implementer. Decide by:
   implementation review.
3. **When should closed observation partitions compact or expire?** Recommended
   default: retain them unchanged in Slice 1; propose whole-partition retention
   only after every capture has a terminal disposition and measured repository
   growth justifies the loss of checkout-local history. Owner: core maintainer.
   Decide by: before any automatic retention behavior.

## Follow-on artifacts

1. ADR: canonical project knowledge uses per-topic JSON with a deterministic
   body-free topic map published in the same Git snapshot; JSONL is
   legacy/interchange rather than current topic state.
2. ADR: one progressive `project-knowledge` skill separates capture,
   distillation, and enquiry authority; captured observations persist in
   classification/month event journals and only topics are queryable.
3. [`docs/specs/project-knowledge-foundation/`](../specs/project-knowledge-foundation/)
   — Slice 1 implementation contract and plan.
4. Later specs for individual skill integrations at their semantic gates.
5. A separate RFC for any external capture backend or
   multi-project bank.
