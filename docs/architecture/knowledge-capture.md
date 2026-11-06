# Knowledge capture

`project-knowledge` is a single skill with seven mutually exclusive modes. Four
carry the lifecycle: `--capture` records an observation, `--distill` folds
observations into topics, `--enquire` answers a question from committed topics,
and `--candidates` suggests what to capture without storing anything. Three
more move or validate state: `--migrate-legacy`, `--activate-staged`, and
`--reasoning-payload`.

Each mode has its own callable surface, so a mode that
reads cannot write. The store is plain files under `docs/knowledge/`, Git is its
publication and recovery path, and retrieved text is evidence, never
instruction.[^1]

## 1. Purpose and boundary

The skill captures reusable repository practice, distils it into file-backed
topics, and returns bounded evidence for an explicit question. It does not
replace canonical artifacts, keep arbitrary scratch, or give retrieved
knowledge authority. Enquiry cannot grant permission, approve a change, select a
tool, or override a canonical artifact, instruction, or runtime control.[^1]

## 2. Entrypoints

Each mode loads its own reference file and may call only the helpers named
here.[^2]

| Mode | Callable surface | Writes |
| --- | --- | --- |
| `--capture` | `capture_observation` | One pending observation |
| `--distill` | Bounded journal, topic, source, and guarded-mutation helpers | A disposition, and on a reviewed proposal a topic and the topic map |
| `--enquire` | Committed-topic, map, and current-source read helpers | Nothing |
| `--candidates` | None. Reads one `delivery-fact-feed.v1` page from standard input | Nothing |
| `--migrate-legacy`, `--activate-staged` | Migration staging and activation | A staged tree, then the live store |
| `--reasoning-payload` | Builds the cold-reasoning request for a `work-item` capture | Nothing |

`--candidates` prints checked suggestions in an inert `knowledge-candidates.v1`
frame, marked unadmitted with unverified provenance. A person or agent keeps one
by writing the lesson, giving the privacy attestation, and running the ordinary
`--capture`. Capture never reads the candidate frame.

`--producer-profile work-loop` is an additive producer seam on `--capture`. It
accepts only workflow semantic judgments, then builds the capture fields and the
fixed review enquiry envelope deterministically before normal validation. A full
raw request without the profile stays a supported path.[^3]

## 3. Owned state and write authority

Only `knowledge_store.py` writes the store.[^4]

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| Workflow scratch | Producer workflow context | Owning workflow | Its current workflow |
| Knowledge store | `docs/knowledge/` | `knowledge_store.py` | Project-knowledge modes, reviewers |
| Published knowledge | Committed Git tree | Normal Git commit workflow | `--enquire` |
| Store lock | Knowledge worktree | `knowledge_store.py` | Capture and distill |

The store holds `topics/`, `observations/`, `topics.index.json` (the topic map),
`patterns.jsonl`, and `README.md`.

## 4. Allowed edges

Capture records an observation and never reads or mutates topics. Distill reads
bounded observations and may write dispositions, topics, and the map.

Enquire
reads committed eligible topics and never reads journals or invokes a writer.
Knowledge code reads confined repository sources for provenance and freshness
and has no network, arbitrary-command, credential, or permission-management
authority.[^1][^5]

### 4a. Delivery feed and candidates

Delivery owns no knowledge state, and the two skills exchange only one page.
The work-loop skill's read-only `delivery-fact-feed.py` reads each spec's
committed `delivery/evidence.jsonl` through confined file helpers and prints a
`delivery-fact-feed.v1` page.

Its candidates come from unsuperseded
`review-failure` receipts, which the supervisor writes in every full-mode run, so
no setting turns the feed on. Scanning is pull-only: no notification, cursor,
deduplication, acknowledgement, retry, or admission state exists.[^6]

The `spec-approved` and `plan-locked` capture gates run under those names in
work-loop's full mode, and the close-time `work-item` capture is explicit.
**STATUS: PLANNED** — Slice 8 of the
[acceptance-centered work-loop brief](../product/briefs/acceptance-centered-work-loop.md)
removes the two gates. [work-loop-knowledge-handoff.md](work-loop-knowledge-handoff.md)
holds the full boundary.[^7]

## 5. Primary flows

1. A workflow submits explicit reusable residue to `--capture`, which returns an
   observation receipt.
2. `--distill` reconciles bounded observations, records a disposition, and may
   propose a topic and map mutation for review and commit.
3. `--enquire` resolves a question against the committed topic map and returns a
   bounded evidence receipt or abstains. A reply carries at most twelve topic
   bodies.[^8]
4. `--candidates` turns one feed page into unadmitted suggestions. A chosen
   suggestion re-enters at step 1 as an ordinary capture request.

## 6. Provenance for a multi-artifact terminal gate

A gate that closes over several artifacts supplies provenance in three separate
fields, because the observation contract names one artifact.[^9]

- The **primary owning artifact** is the observation's single
  `semantic_gate.artifact`. It answers which artifact the observation is about.
- The **companion-artifact set** in `provenance.sources` names every other
  artifact the gate closed over.
- The **freshness anchor** sits on the artifact whose content decides that the
  gate is satisfied. It answers what would have to change for the observation
  to go stale, and it need not be the primary artifact.

Reusing one artifact for both owner and anchor ties staleness to the wrong file.
Construction tests reference one canonical gate-to-artifact mapping, so a gate
whose artifact set changes updates one place.

## 7. The `work-item` record class

`--capture` accepts a fourth kind, `work-item`, at
`knowledge-captured-observation.v2`. The three older kinds (`pattern`, `gotcha`,
`antipattern`) carry generalisable practice.

`work-item` carries its
complement: a specific, currently blocked piece of leftover work that a
`work-loop` close declines rather than dispatches or discards. The writer emits
`v2` only, and a `v1` record is read under the `v1` rules its own
`contract_version` selects.[^10]

A `work_item` carries a `shape` (`defect`, `question`, or `decision`), each with
its own admission threshold, and a `blocker` naming why it is not done now
(`decision`, `instrument`, `elapsed-time`, or `dependency`). A `defect` may carry
`verification_route.command` as a bounded, read-only argv array.[^11] The argv
rules and their residuals are owned by
[security.md § 9](security.md#9-a-stored-work-item-command-carries-disclosed-unmitigated-residuals).
[`work-item-capture.md`](../guides/reference/work-item-capture.md) is the
adopter-facing reference.

**Validation is the reasoning tier only.** Every `work-item` capture needs a
cold reasoning verdict from a dispatch with no access to the originating
session, and a submission without a recognised verdict is never written.

The
close-time path is plain `--capture` with `semantic_gate.name: close-time`,
`--reasoning-verdict`, and `--reasoning-correlation-key`; the key comes from a
prior `--reasoning-payload` call. A projected candidate never creates a
`work-item`.[^12]

**STATUS: PLANNED** — the deterministic mechanical tier is a separate capability
([spec](../specs/work-item-mechanical-tier/spec.md), Draft). Until it lands, an
unavailable reasoning dispatch means no validation floor and no write. The gap
list is in
[security.md § 9](security.md#9-a-stored-work-item-command-carries-disclosed-unmitigated-residuals).

**A merge can bring in an unchecked record.** Write-time controls run once, at
`--capture`; which controls run there is recorded in
[security.md § 9](security.md#9-a-stored-work-item-command-carries-disclosed-unmitigated-residuals).

A merged or contributor-branch record may carry a record validated
elsewhere. Read-only paths revalidate committed records (§ 8a), but that checks
schema, version, content policy, and consistency, not the reasoning verdict, so a
merged `work-item` has the trust of any other merged file.

## 8. Failure and recovery

Invalid privacy, provenance, schema, path, or size input is refused before a body
is persisted, with redacted diagnostics. A lock loss, stale precondition,
malformed store, or inconsistent postimage stops mutation; the next writer
revalidates and completes only an idempotent missing step or refuses recovery.
Uncertain, stale, retired, malformed, or out-of-scope topics are excluded from
enquiry, and enquiry abstains when it cannot verify eligible evidence.[^13]

### 8a. Read validation of committed records

A record can reach Git outside capture, so `--enquire` and `--distill --pending`
validate each committed record they read. An invalid record is malformed, unsafe,
of an unknown version, policy-invalid, inconsistent, oversized, or orphaned. The
path excludes it, answers from the valid records, and leaves committed bytes
unchanged.[^14]

- **Exclusion is closed.** A subject whose restricting, dispositioning,
  superseding, or revoking record is excluded is excluded too, and orphans are
  excluded.
- **The report is bounded.** Each entry is a repository-relative locator (or a
  non-content-derived ordinal when the path fails validation) and a code from a
  closed set, with no record bytes, excerpt, or content-derived hash. One read
  lists at most 100 entries, then one counted overflow marker. Enquiry renders
  them in a `knowledge-quarantine.v1` element after the evidence element; the
  pending drain returns them as the receipt's `diagnostics`.
- **Writers refuse whole.** Capture, disposition, promotion, topic-map rebuild,
  writer admission, and migration staging or activation refuse the whole
  operation and change no byte when any record they read is invalid. One invalid
  observation blocks every promotion and terminal disposition plus captures into
  its partition. One invalid topic or map entry blocks every write through writer
  admission. Repairing or reverting the reported record through Git clears the
  stop.
- **Some refusals stay whole.** A missing, unparseable, wrong-version, or
  link-like topic map, and every capacity or budget refusal, refuse the whole
  read. A failure of the Git or operating-system read itself is never a record
  fault. A link-like or non-regular observation partition file is excluded as
  `unsafe` and never read.

## 8b. The promotion drain: reading a record to act on it

The promotion drain is the store's first read-and-act path. An operator
invokes it to hand a captured `work-item` to its owning route or to close
it. It reads the open `work-item` captures — those with no terminal
disposition — through the same confined read helpers every other read uses,
and per item assembles an offer: the record, the write-path prose controls
re-run over the schema-derived scanned field set (settling the § D10 prose
residual for everything the drain touches), the stored command's
pre-execution re-check through the write path's own validator, and the
command's run under the execution envelope. The envelope is the one place
a stored command executes: repository-confinement of every stored-path
member after symlink resolution, a neutralized environment with standard
input closed and `LC_ALL=C`, a 10-second wall-clock cap with process-group
t termination, a 64-KiB output cap, and `grep` pinned to `-F`. Output
crosses toward any durable sink only through the eight-pattern privacy
scan at that seam.

The terminal disposition is the sole commit point. A confirmed route runs
the work-intake transaction — the captured-item file under
`docs/product/captured/`, then the processor handoff — and only then writes
`routed`, and a route with no dispatch wired holds the item before any
transaction effect, so a route is never recorded as routed without its
handoff; a closure records `rejected` or `superseded` with its ground in
the reason code; a held item writes nothing and stays open. A crash ahead
of the disposition leaves the capture open, and re-running the drain
completes the sequence idempotently: the transaction's existing-artifact
path writes no second artifact and the store's identical-disposition no-op
writes no second terminal event. An unattended drain performs the
read-only half only and holds every item.

The implementation is in
`packs/core/.apm/skills/project-knowledge/scripts/promotion_drain.py`; the
operator procedure is `packs/core/.apm/skills/work-intake/SKILL.md` § 8.

## 9. Observability and evidence

Capture returns receipts. Distillation records dispositions and proposed store
changes. Enquiry returns selected topic identifiers, source pointers, limits,
abstention state, and quarantine entries.

Candidate mode returns the
`knowledge-candidates.v1` frame and writes nothing. The store, the committed
topic map, Git history, and redacted refusal diagnostics are the durable
evidence.

A capture diagnostic carries a `retryable` field, set on a timeout. Only the
two project-knowledge scripts mention it; no other skill under `packs/core/.apm/`
reads it.[^15]

## 10. Mechanical invariants

- `tools/lint-knowledge-surface-parity.py` stops silent drift among the
  duplicated knowledge-surface taxonomy copies used by architecture skills. The
  pre-PR catalogue check in the build gate chain runs it.[^16]
- Mode isolation, read quarantine, and write-path refusal are covered by the
  suites in `packs/core/tests/skills/project-knowledge/`.[^17]

No named command enforces the mode authority boundary beyond those suites.

## 11. Governing records

- [ADR-0081 — Canonical project knowledge uses per-topic JSON](../adr/0081-canonical-project-knowledge-uses-per-topic-json.md)
- [ADR-0082 — Project-knowledge modes separate authority](../adr/0082-project-knowledge-modes-separate-authority.md)
- [RFC-0077 — Distill knowledge](../rfc/0077-distill-knowledge.md)

## 12. Last verified against commit

`3fe5f2760`, whole page, against `packs/core/.apm/skills/project-knowledge/`,
`contracts/`, and the work-loop feed script.

[^1]: `packs/core/.apm/skills/project-knowledge/SKILL.md` (mode list and boundary text); [ADR-0082](../adr/0082-project-knowledge-modes-separate-authority.md).

[^2]: `SKILL.md` and `references/{capture,distill,enquire,candidate}-mode.md` in the same directory; mode flags in `scripts/project_knowledge.py` (`_run_main`).

[^3]: `scripts/project_knowledge.py` (`PRODUCER_WORKFLOW_VERSION`, `--producer-profile`); `packs/core/tests/skills/project-knowledge/test_work_loop_producer_profile.py`.

[^4]: `scripts/knowledge_store.py`; `docs/knowledge/` listing.

[^5]: `packs/core/tests/skills/project-knowledge/test_mode_isolation.py`.

[^6]: `packs/core/.apm/skills/work-loop/scripts/delivery-fact-feed.py`; `contracts/delivery/delivery-fact-feed.v1.schema.json`; `docs/specs/delivery-knowledge-projection/spec.md`.

[^7]: `packs/core/.apm/skills/work-loop/SKILL.md` (capture-gate steps); [work-loop-authority-migration.md](work-loop-authority-migration.md) (Slice 8 removal row).

[^8]: `scripts/project_knowledge.py` (`enquiry_bodies` in the budget table); `knowledge_store.py` (`budget_contract`).

[^9]: `contracts/delivery/knowledge-observation.v1.schema.json`; [work-loop-knowledge-handoff.md](work-loop-knowledge-handoff.md).

[^10]: `contracts/jsonschema/knowledge-captured-observation.schema.json` (`contract_version`); `docs/specs/work-item-capture/spec.md`.

[^11]: Schema enums for `shape` and `blocker`; `scripts/project_knowledge.py` (`_ARGV_ALLOWED_TOOLS`).

[^12]: `packs/core/.apm/skills/work-loop/references/work-item-capture.md`; `scripts/project_knowledge.py` (`--reasoning-payload`, `--reasoning-verdict`).

[^13]: `packs/core/tests/skills/project-knowledge/test_locking.py` and `test_observation_store.py`.

[^14]: `packs/core/tests/skills/project-knowledge/test_read_quarantine.py` and `test_quarantine_write_paths.py`; `docs/specs/delivery-knowledge-projection/spec.md`.

[^15]: `scripts/project_knowledge.py` (`retryable` in the diagnostic record); the open caller work is `docs/product/intents/project-knowledge-retryable-capture-handling.md`.

[^16]: `tools/lint-knowledge-surface-parity.py`; run by `tools/catalogue/pre_pr_catalogue.py`.

[^17]: `packs/core/tests/skills/project-knowledge/` (`test_mode_isolation.py`, `test_read_quarantine.py`, `test_quarantine_write_paths.py`).
