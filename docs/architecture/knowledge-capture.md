# Knowledge capture

## 1. Purpose and boundary

`project-knowledge` captures reusable repository practice, distils it into
file-backed knowledge, and returns bounded evidence for an explicit question.
It does not replace canonical artifacts, preserve arbitrary scratch, or grant
authority to retrieved knowledge.

Enquiry reads committed active topics as bounded untrusted evidence. It cannot
grant permission, approve a change, select a tool, or override a canonical
artifact, instruction, or runtime control.

## 2. Entrypoints

- `project-knowledge --capture` loads `references/capture-mode.md` and may
  call only `capture_observation`.
- `project-knowledge --distill` loads `references/distill-mode.md` and may
  call its bounded journal, topic, source, and guarded-mutation helpers.
- `project-knowledge --enquire` loads `references/enquire-mode.md` and may
  call only committed-topic, map, and current-source read helpers.
- `project-knowledge --candidates` loads `references/candidate-mode.md`, reads
  one `delivery-fact-feed.v1` page from standard input, and calls no store
  helper. It prints checked suggestions in an inert `knowledge-candidates.v1`
  frame, marked unadmitted with unverified provenance, and writes no file. A
  person or agent keeps a candidate by writing the lesson, giving the privacy
  attestation, and running the ordinary `--capture`; capture never reads the
  candidate frame.

`--producer-profile work-loop` is an additive producer seam. It accepts only
workflow semantic judgments, then constructs deterministic capture fields and
the fixed review enquiry envelope before normal validation. A full raw request
without the profile remains a supported public path.

## 3. Owned state and write authority

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| Workflow scratch | Producer workflow context | Owning workflow | Its current workflow |
| Knowledge store | `docs/knowledge/` | `packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py` | Project-knowledge modes and reviewers |
| Published knowledge | Committed Git tree | Normal Git commit workflow | `--enquire` |
| Store lock | Knowledge worktree | `knowledge_store.py` | Capture and distill operations |

The store contains `topics/`, `observations/`, `topics.index.json`,
`patterns.jsonl`, and `README.md`.

## 4. Dependencies and allowed edges

Producer workflows may submit a strict observation through `--capture`. Capture
records an observation and does not read or mutate topics. Distill reads bounded
observations and may write dispositions, topics, and the topic map. Enquire reads
committed eligible topics and never reads journals or invokes a writer.

Knowledge code may read confined repository sources for provenance and freshness.
It has no network, arbitrary-command, credential, or permission-management
authority. Canonical artifacts retain authority for their concerns.

## 4a. Delivery feed and candidates

Delivery owns no knowledge state. The work-loop skill's read-only
`delivery-fact-feed.py` reads each spec's shadow evidence log through its
confined file helpers, only when `WORK_LOOP_SHADOW_SERVICES=1` has made the
writer produce one, and prints a `delivery-fact-feed.v1` page whose candidates
come from unsuperseded `review-failure` receipts. Pull scanning is the only
discovery path: no notification is sent, and the scan keeps no cursor,
deduplication, acknowledgement, retry, or admission state. The two skills
exchange only that page; neither imports the other. The retained
`spec-approved` and `plan-locked` producer capture gates and the close-time
`work-item` capture work as before, and the gates' removal is owned by Slice 8
`legacy-engine-cutover`. The full boundary is in
[work-loop-knowledge-handoff.md](work-loop-knowledge-handoff.md); the
contracts are
[`delivery-fact-feed.v1`](../../contracts/delivery/delivery-fact-feed.v1.schema.json)
and
[`knowledge-observation.v1`](../../contracts/delivery/knowledge-observation.v1.schema.json).

## 5. Primary flows

1. A workflow submits explicit reusable residue to `--capture`, which records
   an observation receipt.
2. `--distill` reconciles bounded observations, records a disposition, and may
   propose a topic and map mutation for review and commit.
3. `--enquire` resolves a task question against the committed topic map and
   returns a bounded evidence receipt or abstains.
4. `--candidates` turns one feed page into unadmitted suggestions. A chosen
   suggestion re-enters at step 1 as an ordinary capture request.

## 6. Provenance for a multi-artifact terminal gate

The capture contract names one artifact per observation, while several terminal
gates close over more than one. A gate in that shape supplies deterministic
provenance through three separate fields rather than by choosing one artifact
and dropping the rest:

- a **named primary owning artifact**, which is the observation's single
  `semantic_gate.artifact`;
- an explicit **companion-artifact provenance set**, carried in
  `provenance.sources`, naming every other artifact the gate closed over; and
- a **freshness anchor on the artifact that closes the gate**, which is not
  necessarily the primary owning artifact — it is whichever artifact's content
  determines that the gate is satisfied.

Separating the anchor from the owner matters because the two answer different
questions. The owner answers "which artifact is this observation about"; the
anchor answers "what content would have to change for this observation to go
stale". A gate that reuses one artifact for both silently ties staleness to the
wrong file.

Construction tests reference one canonical gate-to-artifact mapping. Restating
the path rules per test duplicates a fact that has no owner, and the copies
drift at the first gate whose artifact set changes.

## 7. The `work-item` record class

`--capture` accepts a fourth kind, `work-item`, at
`knowledge-captured-observation.v2`
(`contracts/jsonschema/knowledge-captured-observation.schema.json`). Where
the three older kinds (`pattern`, `gotcha`, `antipattern`) carry
generalisable practice, `work-item` carries its complement: a specific,
non-generalisable, currently-blocked piece of leftover work — the record a
`work-loop` close writes for an item it declines rather than dispatches or
discards. `docs/guides/reference/work-item-capture.md` is the adopter-facing
reference for writing one; this section is the architectural summary.

A `work_item` object carries a `shape` — `defect`, `question`, or
`decision` — each with its own admission threshold, and a `blocker` naming
why it is not done now (`decision`, `instrument`, `elapsed-time`,
`dependency`). A `defect` may carry `verification_route.command` as a
bounded, read-only argv array: a four-tool allowlist (`cat`, `wc`, `grep`,
`ls`), no options, a positive character class, and a repository-path rule
over § D6's stored-path set, which also takes in `verification_route.path`
and leaves out `grep`'s pattern. Those rules confine that set to the
repository; they do not decide whether a file in it is sensitive. `v1` stays a read-only
legacy version; the writer emits `v2` only, and a v1 record is still read
under the v1 rules its own `contract_version` selects.

**Validation as delivered: the reasoning tier only.** Every `work-item`
capture is gated on a per-item cold reasoning check — a dispatch with no
access to the originating session — and a submission with no recognized
verdict from that check is never written, whatever the reason the verdict
is missing (unreachable, unconfigured, malformed, mismatched, or stale on a
corrected re-submission). There is no second, deterministic tier in this
delivery: the reasoning check is the whole of validation. The **mechanical
tier is not built.** It is a separate, not-yet-landed capability —
`docs/specs/work-item-mechanical-tier/spec.md` — and until it lands, an
unavailable reasoning dispatch is an unavailable validation floor, full
stop. `docs/architecture/security.md` § Work-item capture — the gap list is
the single home for what that leaves open.

**The unchecked merge path.** The write-time controls above — the argv
rules, the privacy scan, the instruction-shape refusal, the reasoning
check — run once, at `--capture`. A record can also enter the committed
store by a path other than that API: a merge, or a contributor branch,
carrying a record validated elsewhere or not at all. The read-only paths
now revalidate the committed records they read (see § 8a), but that
validation checks schema, version, content policy, and consistency, not the
reasoning verdict a `work-item` needed at capture, so a merged record still
sits on the same trust footing as any other file the merge brought in.

The close-time `work-item` command path is plain `--capture` (no
`--producer-profile`), with `semantic_gate.name: close-time` and a per-item
cold reasoning verdict passed as `--reasoning-verdict` and
`--reasoning-correlation-key`; the key comes from a prior `--reasoning-payload`
call. `packs/core/.apm/skills/work-loop/references/work-item-capture.md` owns
the steps. A projected candidate never creates a `work-item`.

## 8. Failure and recovery behavior

Invalid privacy, provenance, schema, path, or size input is refused before a
body is persisted. Refusals use redacted diagnostics.

A lock loss, stale precondition, malformed store, or inconsistent postimage
stops mutation. The next writer revalidates state and completes only an
idempotent missing step or refuses recovery.

Uncertain, stale, retired, malformed, or out-of-scope topics are excluded from
ordinary enquiry. Enquiry abstains when it cannot verify eligible evidence.

## 8a. Read validation of committed records

A record can reach Git outside capture, so the two read-only paths,
`--enquire` and `--distill --pending`, validate each committed record they
read. An invalid record is one that is malformed, unsafe, of an unknown version,
policy-invalid, inconsistent, oversized, or orphaned. The path excludes it
on its own, still answers from the valid records, and leaves the committed
bytes unchanged.

- **Closed exclusion.** Excluding a record never makes another more usable. A
  subject whose restricting, dispositioning, superseding, or revoking record is
  excluded is excluded too, and records left orphaned are excluded.
- **Bounded report.** Each entry is a repository-relative locator (or a
  non-content-derived ordinal when the path fails validation) and a code from a
  closed set, with no record bytes, excerpt, or content-derived hash. One read
  lists at most 100 entries, then one counted overflow marker. Enquiry
  renders them in a separate `knowledge-quarantine.v1` element after the
  evidence element; the pending drain returns them as the receipt's
  `diagnostics`.
- **Writers refuse whole.** Capture, disposition, promotion, topic-map
  rebuild, writer admission, and migration staging or activation still
  refuse the whole operation and change no byte when any record they read
  is invalid, so no write runs against a reduced view. One invalid
  observation record blocks every promotion and terminal disposition, plus
  captures into its partition. One invalid topic or topic-map entry blocks
  every write, captures included, through writer admission. Either stop lasts
  until a maintainer repairs or reverts the record through Git; the
  quarantine report gives its location.
- **Whole refusals that remain.** A missing, unparseable, or link-like topic
  map, and every capacity or budget refusal, still refuse the whole read. A
  map that names the wrong version counts as unparseable: no valid record set
  exists to answer from. A failure of the Git or operating-system read itself
  (a non-zero exit, a spawn or temporary-file error, a failed size probe) is
  never a record fault; it refuses the whole read rather than hiding the topic
  it touched. A link-like or non-regular observation partition file is not a
  whole refusal on the pending page: it is excluded as `unsafe` and never read.
  A read of one topic by name that fails because its own entry was excluded
  reports that entry's closed reason code and locator, and no content.

The implementation is in `knowledge_store.py`; the suites are
`packs/core/tests/skills/project-knowledge/test_read_quarantine.py` and
`test_quarantine_write_paths.py`.

## 9. Observability and evidence

Capture returns receipts. Distillation records dispositions and proposed store
changes. Enquiry returns selected topic identifiers, source pointers, limits,
abstention state, and any quarantine entries. Candidate mode returns the
`knowledge-candidates.v1` frame and writes nothing.

The store, committed topic map, Git history, and redacted refusal diagnostics
provide the durable evidence trail.

## 10. Mechanical invariants

- `tools/lint-knowledge-surface-parity.py` prevents silent drift among the
  duplicated knowledge-surface taxonomy copies used by architecture skills.

The mode authority boundary is documented here. This page does not claim a
named command enforces it.

## 11. Relevant ADRs

- [ADR-0081 — Canonical project knowledge uses per-topic JSON](../adr/0081-canonical-project-knowledge-uses-per-topic-json.md)
- [ADR-0082 — Project-knowledge modes separate authority](../adr/0082-project-knowledge-modes-separate-authority.md)

## 12. Last verified against commit

`615b68d8c` for sections 1-6 and 8-11. Section 7 (`work-item`) added by
`docs/specs/work-item-capture/spec.md`, current on this pack's landed T1-T7.
The candidate mode, § 4a, and § 8a were added by
`docs/specs/delivery-knowledge-projection/spec.md` and match its T1-T3 code.
