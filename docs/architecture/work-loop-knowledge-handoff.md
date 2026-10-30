# Subsystem Design — Delivery-to-knowledge projection

**Decision sought:** Let delivery project attributed knowledge candidates from
facts it already owns, while project-knowledge owns every capture, admission,
storage, and enquiry concern and delivery owns no knowledge state.
**Author:** Platform Core
**Status:** Current
**Last updated:** 2026-10-29
**Reviewers:** Core and project-knowledge maintainers

Slice 3 of the [acceptance-centered work loop](acceptance-centered-work-loop.md)
ships this boundary beside the retained capture gates. A pull scan lists
`review-failure` receipts as unadmitted `gotcha` candidates, and a person or
agent keeps one by running the ordinary `--capture`. Nothing is queued,
acknowledged, deduplicated, or revoked by delivery.

## 1. Scope and Context

| In scope | Out of scope | Why |
| --- | --- | --- |
| A read-only feed of eligible facts in each spec's committed `delivery/evidence.jsonl` | Knowledge admission, distillation, taxonomy, and retention | Project knowledge owns its lifecycle |
| A pure projector from one eligible fact to one `knowledge-observation.v1` candidate or none | Any delivery-owned queue, cursor, retry, acknowledgement, skip log, admission record, or revocation record | Knowledge failure cannot become delivery state |
| A read-only candidate mode in project-knowledge that checks a feed page and stores nothing | Automatic capture of a candidate, a `lesson`, or a privacy attestation supplied on a person's behalf | A capture needs a human-written lesson and attestation |
| Per-record read quarantine on the read-only knowledge paths | Changing any writer, admission, retention, or storage rule | Writers keep refusing against an invalid record |
| The retained `spec-approved` and `plan-locked` capture gates and the close-time `work-item` path | Removing those gates | Slice 8 owns removal |

**Goals**

- Delivery behaves identically when knowledge tooling is absent or failing.
- Every candidate is reproducible from one durable `review-failure` receipt.
- No notification exists, so a dropped one cannot lose a fact: pull scanning is
  the only discovery path.

**Non-goals**

- Moving product truth, requirements, decisions, or knowledge admission into
  the work loop.
- Making any knowledge-tool result a prerequisite for spec, plan, review,
  acceptance, readiness, or closeout.

## 2. Structural Model

| Element | Type | Responsibility | State |
| --- | --- | --- | --- |
| Delivery fact feed (`delivery-fact-feed.py`, `_delivery_feed.py`) | Read-only command | Read each spec's committed `delivery/evidence.jsonl` through the work-loop confined file helpers and print one `delivery-fact-feed.v1` page of a reproducible snapshot | Stateless |
| Observation projector (`_knowledge_projection.py`) | Pure component | Map an eligible `review-failure` receipt to one `gotcha` candidate or none | Stateless |
| Candidate mode (`project_knowledge.py --candidates`) | Read-only project-knowledge mode | Validate one feed page, check each candidate, and print the survivors in an inert `knowledge-candidates.v1` frame | Stateless; writes no file |
| Capture (`project_knowledge.py --capture`) | Existing writer | Validate, identify, and journal a request a person or agent wrote | Knowledge store |
| Committed-record read validation (`knowledge_store.py`) | Project-knowledge boundary | Exclude an invalid committed record on the read-only paths and report a bounded reason | Per-read; no stored quarantine |

The feed and project-knowledge sit in separate skills and exchange only
`delivery-fact-feed.v1` data on standard input and output. Neither imports the
other, and neither imports `agentbundle`.

## 3. Runtime Model

**Normal sequence**

1. Every full-mode run's supervisor commits Slice 1 evidence frames, including
   Slice 2's `review-failure` receipts, to
   `docs/specs/<feature>/delivery/evidence.jsonl`. No setting turns this on,
   and light mode writes no log.
2. A maintainer runs `delivery-fact-feed.py` and pipes its page into
   `project_knowledge.py --candidates`.
3. The feed lists `docs/specs/` and reads each spec's `delivery/evidence.jsonl`
   that exists. It replays complete frames through the Slice 1 store's own
   `replay_admitted_frames` admission rules, without opening the store for
   writing, and cuts a torn final frame off the read bytes.
4. The projector turns each `review-failure` receipt that no supersession
   names into a candidate carrying the receipt's acceptance fingerprint and
   its source report's review-policy fingerprint. Every other receipt kind is
   ineligible.
5. Candidate mode strictly parses and schema-checks the whole page, then
   checks each candidate's text and paths with project-knowledge's own capture
   rules. It prints the survivors as unadmitted candidates with unverified
   provenance, and an omission code for each failure.
6. A person or agent who wants to keep a candidate writes the lesson, gives the
   privacy attestation, and runs the ordinary `--capture`.
7. Enquiry and the distillation pending page validate each committed record
   they read. They exclude an invalid one and still answer from the rest.

**Failure and recovery sequence**

1. Absent, disabled, unavailable, timing-out, or failing knowledge tooling
   changes no delivery decision; the supervisor never calls it.
2. A linked or oversized or
   checksum-invalid log, or a log whose read is refused becomes an unread
   source with a closed reason code and yields no candidate. A refused or
   link-like `docs/specs/` root refuses the whole scan.
3. A continuation whose snapshot can no longer be reproduced refuses with no
   page; the maintainer starts a new scan.
4. When Slice 2 supersedes a report or assessment, the next scan that reads
   its log presents no candidate for the receipt. A capture made earlier from
   that candidate is never edited, withdrawn, or dispositioned by a scan.

There is no notification. Pull scanning is the only discovery path, so a lost
signal, a restarted scan, and an overlapping scan need no recovery procedure:
each scan derives the same candidates from the same facts.

## 4. Contracts and Invariants

| Contract | Producer → consumer | Identity | Compatibility and change authority | Failure semantics | Invariant |
| --- | --- | --- | --- | --- | --- |
| [`delivery-fact-feed.v1`](../../contracts/delivery/delivery-fact-feed.v1.schema.json) | Feed → candidate mode | Snapshot digest, spec path, and Slice 1 receipt identity | Core and project-knowledge owners approve; unknown majors refuse | A corrupt, changing, or incomplete source is an unread source; a non-reproducible continuation refuses the scan | One snapshot lists every eligible committed fact in stable order, in pages of at most 1,000 facts and 1 MiB that never split an entry; a record or transaction id the identifier pattern cannot hold is shown as `digest-sha256:` plus the SHA-256 of its UTF-8 bytes, so it hides no other fact |
| [`knowledge-observation.v1`](../../contracts/delivery/knowledge-observation.v1.schema.json) | Projector → candidate mode | Spec directory, receipt identity, projection version, and content-policy version | Core and project-knowledge owners approve; unknown majors refuse | Ineligible, oversized, or content-refused input yields no observation and no record | A candidate is derived, inert, at most 4 KiB, with complete source provenance and no delivery authority |
| `knowledge-candidates.v1` (candidate-mode output frame) | Candidate mode → maintainer | Position in the page | Project-knowledge owners | A failing candidate is omitted with a closed code and no candidate text; a spec whose log the feed could not read appears as an `unread-source` element with its closed reason code and no content | The frame is distinct from enquiry's evidence frame and escapes every field |
| `knowledge-captured-observation.v2` read validation | Committed knowledge store → enquiry and the distillation pending page | Record location | Project-knowledge owners | An invalid, unsafe, or unknown-version record is excluded and reported by location and closed reason code | Git presence alone never makes a merged record eligible knowledge, and excluding a record never makes another more usable |

The feed's schemas live only under `contracts/delivery/`. Core runtime code
restates their rules in self-contained code, copies no schema, and opens
nothing under that directory at runtime.

Only a Slice 2 `review-failure` receipt is eligible. Adding a source kind, an
observation kind, or a projection-policy version needs owner approval and new
fixtures. Reviewed-envelope, initial-plan-review, plan, task-projection,
mutation-classification, and supervisor step records are never candidates.
A candidate is a past lesson, so a later change to the acceptance subject or
review policy does not hide it; the two fingerprints it carries show which
subject and policy it came from.

## 5. Data and State

| Element | State it owns | Lifecycle | Consistency requirement |
| --- | --- | --- | --- |
| Delivery fact feed | None; each page derives from the evidence logs, which the feed never writes, truncates, locks, or repairs | Recreated per scan | Stable order and bounded pages cover the named snapshot or the scan refuses |
| Observation projector | None | Re-run at any time | The same facts and policy versions give byte-identical identities and payloads |
| Candidate mode | None | One run | Writes no file; leaves the knowledge store byte-identical |
| Capture | Knowledge records | Existing project-knowledge lifecycle | Unchanged: privacy attestation, identity, time window |
| Read validation | A per-read quarantine list of at most 100 entries, then one counted overflow marker | Built and dropped within one read | Each entry is a bounded repository-relative locator plus a closed reason code, with no record bytes or content-derived hash |

Delivery owns no knowledge queue, cursor, retry, acknowledgement, skip log,
admission record, retention record, or revocation record, and no
knowledge-specific readiness transition. The knowledge store has no scan
cursor and no deduplication state: a repeated or overlapping scan may repeat a
candidate, and nothing records that it did.

## 6. Deployment and Operations

| Unit | Runs as | Scaling | Observability |
| --- | --- | --- | --- |
| Feed | `python <work-loop-dir>/scripts/delivery-fact-feed.py [--root <dir>] [--continuation <token>]` | One page per call; 256 MiB cap per log | Exit 0 with a page, or exit 2 with `delivery-fact-feed: refused: <code>` on stderr; an unexpected fault adds a `scan-failed: <stage>: <ExceptionClass>` line with no record content. A `snapshot-changed` refusal means restart from the first page with no token |
| Candidate mode | `python <project-knowledge-dir>/scripts/project_knowledge.py --candidates [--continue-from N]` | One page per call; at most 32 KiB of whole candidates per output | A frame with candidates, omission codes, and an optional continuation ordinal |
| Read quarantine | Part of `--enquire` and `--distill --pending` | At most 100 entries per read | A `quarantine` list and `knowledge-quarantine.v1` element on enquiry; the drain receipt's `diagnostics` on the pending page |

The maintainer commands are in the
[knowledge README](../../packs/core/seeds/docs/knowledge/README.md).

## 7. Quality Scenarios and Verification

| Stimulus | Mechanism and response | Target | Verification |
| --- | --- | --- | --- |
| Knowledge tooling is absent, disabled, unavailable, timing out, refusing, or failing | The supervisor never calls it, so every decision matches the absent run | Identical spec, plan, review, acceptance, readiness, and closeout decisions and files | `test_delivery_knowledge_isolation.py` |
| A spec has no `delivery/evidence.jsonl` | The feed lists no fact for it | Unchanged files, state, and decisions | `test_delivery_fact_feed.py` |
| A scan runs with no notification | Pull scanning presents every projected candidate | Zero dependency on a signal | `test_delivery_fact_feed.py`, `test_candidate_mode.py` |
| A scan repeats or overlaps | The same deterministic candidates return | Zero cursor, deduplication, or acknowledgement state; knowledge store byte-identical | `test_candidate_mode.py` |
| A log is linked, oversized, torn, or checksum-invalid | The log is an unread source or its torn frame is invisible | No fact from it; every log byte-identical | `test_delivery_fact_feed_confinement.py` |
| A receipt is superseded | The next scan presents no candidate for it | Zero stale candidates | `test_knowledge_projection.py`, `test_delivery_fact_feed.py` |
| A feed page or candidate is malformed or hostile | Whole-page refusal, or omission with a closed code | Zero candidate text outside the inert frame | `test_candidate_mode.py`, the differential corpus in `test_delivery_contract_bundle.py` |
| A merge introduces an invalid knowledge record | Enquiry and the pending page exclude it and report a location and code | Zero invalid records in an answer; committed bytes unchanged | `test_read_quarantine.py` |
| A writer meets an invalid record | Promotion, disposition, map rebuild, writer admission, and migration refuse the whole operation | Zero bytes changed | `test_quarantine_write_paths.py` |
| A close-time `work-item` or a producer capture at a retained gate | The existing path accepts or refuses it exactly as before | Zero change in acceptance, refusal, size, privacy, or provenance | `test_retained_capture_paths.py` |
| Core runs with `agentbundle` and the repository's other packages unavailable | Runtime modules import only the standard library or their own skill | Conformance corpus passes; zero opens under `contracts/delivery/` | `test_delivery_contract_bundle.py` |

## 8. Implementation Mapping

| Element | Source owner | Build unit | Verification |
| --- | --- | --- | --- |
| Read-only fact feed | `packs/core/.apm/skills/work-loop/scripts/delivery-fact-feed.py` and `_delivery_feed.py`, over the read-only `replay_admitted_frames` accessor in `_evidence_store.py` | Core pack, `work-loop` skill | `packs/core/tests/skills/work-loop/test_delivery_fact_feed.py` and `test_delivery_fact_feed_confinement.py` |
| Observation schema and projection policy | `contracts/delivery/knowledge-observation.v1.schema.json`; `_knowledge_projection.py` | Core pack, `work-loop` skill | `test_knowledge_projection.py`; schema parity in `tests/roster/test_delivery_contract_bundle.py` |
| Read-only candidate mode | `--candidates` in `packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py` | Core pack, `project-knowledge` skill | `packs/core/tests/skills/project-knowledge/test_candidate_mode.py` |
| Committed-record read validation | Read-only entry points in `knowledge_store.py` | Core pack, `project-knowledge` skill | `test_read_quarantine.py` and `test_quarantine_write_paths.py` |
| Readiness isolation | No production module; the supervisor never names knowledge tooling | Core pack, `work-loop` skill | `packs/core/tests/skills/work-loop/test_delivery_knowledge_isolation.py` |
| Retained capture gates | `project-knowledge --capture --producer-profile work-loop` at `spec-approved` and `plan-locked` | Core pack and `work-loop` | `test_retained_capture_paths.py` |
| Retained close-time `work-item` | Plain `project-knowledge --capture` with `semantic_gate.name: close-time`, `knowledge-captured-observation.v2`, and a per-item cold reasoning verdict, as in `packs/core/.apm/skills/work-loop/references/work-item-capture.md` | Core pack and `close-work` | `test_retained_capture_paths.py` and the existing `work-item` suites |

The close-time `work-item` path does not use `--producer-profile work-loop`.
The close first runs `--reasoning-payload` to get a correlation key, runs one
cold reasoning check, then runs `--capture` with `--reasoning-verdict` and
`--reasoning-correlation-key`. A projected candidate never creates a
`work-item`.

No `handoff_store.py`, knowledge skip store, delivery-side capture cursor,
notification port, or collector is built.

## 9. Decisions, Alternatives, and Risks

- **Decision:** Project candidates from existing facts; keep every capture,
  admission, and storage concern in the knowledge lifecycle. The owner chose
  candidates only on 2026-10-12 and shipping beside the current gates on
  2026-10-11 (see the
  [delivery knowledge projection owner decisions](../specs/delivery-knowledge-projection/notes/owner-decision-2026-10-11.md)).
- **Alternative:** Admit candidates automatically through a new capture
  contract version. **Rejected because:** a capture needs a human-written
  lesson and attestation, and its identity hashes `observed_at`, so a rescan
  on a later day would make a new record.
- **Alternative:** Persist a delivery-owned handoff queue and skip log.
  **Rejected because:** it recreates retry, retention, and recovery procedure
  inside work-loop.
- **Alternative:** Send a post-commit notification. **Rejected because:** pull
  scanning already recovers every case, so a signal adds a failure mode and
  no coverage.
- **Alternative:** Make writers tolerate invalid committed records.
  **Rejected because:** it changes storage and admission behavior, and a write
  would run against a reduced view.
- **Risk:** Evidence-log frame checksums are not keyed, so a contributor who
  commits a crafted `delivery/evidence.jsonl` can present invented
  candidates. **Mitigation:** candidates are marked as unverified local claims,
  stay in the inert frame, pass the persistable-text and path checks, and
  reach the store only through an ordinary `--capture`. Revisit at Slice 8.
- **Risk:** A genuine review finding can carry text that untrusted diff
  content steered. **Mitigation:** capture's privacy attestation and the
  evidence-only enquiry frame; this slice adds no stricter gate.
- **Risk:** One invalid committed record stops every promotion and terminal
  disposition, and one invalid topic or map entry stops every capture through
  writer admission, until a maintainer repairs or reverts it through Git.
  **Mitigation:** the read paths report its location and reason code.
- **Risk:** No candidate arrives without a person capturing it.
  **Mitigation:** accepted trade for an unchanged capture contract.

## 10. Rollout, Migration, and Reversal

Slice 3 ships the feed, projector, candidate mode, and read quarantine beside
the capture gates. The Core 4.0.0 cutover points the feed at committed
`delivery/evidence.jsonl`, so every full-mode run now writes delivery facts by
default. The `spec-approved` capture gate before the supervisor's `start` and
the `plan-locked` gate at `start` remain under those names. Slice 8 of the
[acceptance-centered work-loop brief](../product/briefs/acceptance-centered-work-loop.md)
removes them. Explicit close-time `work-item` capture stays for specific
blocked residue.

Rollback stops running the candidate mode and reverts the read-path change.
It restores no queue or delivery state because none exists, and no Slice 1 or
Slice 2 writer changed.

| Responsibility | Owner |
| --- | --- |
| Feed, projector, and candidate mode | Core maintainers |
| Capture, admission, retention, revocation, and read quarantine | Project-knowledge maintainers |
| Reusable capture-gate removal | Slice 8 |
| Rollback authorization | Project-knowledge maintainer after a projection or provenance failure |
