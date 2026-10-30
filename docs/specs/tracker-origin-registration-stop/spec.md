# Spec: Tracker-origin work stops being registered

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0106 (D1, a type's registration stops once every responsibility its entries carry has a replacement, and the contracts requiring it change in that release), RFC-0105 (D3, the retirement gates and the one retirement record), RFC-0083 (work intake, the source-authority record, and refresh), RFC-0055 (errata entries on an Accepted RFC), ADR-0074 (standard-library skill scripts)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** spec:spec-registration-stop
- **Contract:** `contracts/jsonschema/source-authority.schema.json`
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.

## Outcome

A maintainer or agent who takes in, refreshes, or closes a tracker-origin intent, brief or spec edits only that artifact, whose `source-authority` record names its tracker profile, and never adds, moves or removes a `workspace.toml` entry for it. Success is that refresh resolves the profile from the artifact alone, keeps every authority check it makes today, and leaves `workspace.toml` byte-identical, and that an adopter moves each existing tracker-origin entry's profile onto its artifact with one repair run, apart from an entry the repair cannot match to its artifact, which it names.

## What Changes

- **Profile home.** The `source-authority` record gains an optional `tracker_profile` table with `id` and `version` — `contracts/jsonschema/source-authority.schema.json`, `work-intake`'s `scripts/refresh.py` parser and renderer, and `intake-intent`'s renderer, which writes it for a tracker-origin intent.
- **Record writer for briefs and specs.** `work-intake`'s intake transaction renders a first record from the intake's declared source with `scripts/refresh.py`'s renderer, writes it into a tracker-origin brief or spec in place of the registration stage, and checks it before dispatch; `author-delivery-brief` and `new-spec` keep a record they find.
- **Refresh.** `scripts/refresh.py` takes the tracker profile from the artifact's record, refuses an artifact whose record has none, binds the comparison's profile and kind to the artifact at commit, and no longer finds, checks or rewrites a `workspace.toml` entry. It still reads the global `[authorization.refresh]` policy and binds the `workspace.toml` digest.
- **Router.** `work-intake`'s router gives a tracker-origin signal the same route as a repo-origin one: no membership. The unused `workspace_source_record` helper goes.
- **Repair.** A `workspace-status` step, `tracker-entry-drop`, copies each tracker-origin entry's profile into its artifact's record and removes the entry, or names the entry it cannot match or must hold.
- **Writers.** `work-intake`, `author-delivery-brief`, `intake-intent` and `close-work` stop telling anyone to add or move a tracker-origin entry; the routing matrices in `core`, `atlassian`, `github` and `linear` expect no membership, and the `github` and `linear` journeys stop calling the artifact registered.
- **Guides.** The schema guide, the intake guides, the two-room explanation, the Atlassian guides and the work-intake architecture page stop saying tracker-origin work is registered.
- **Governance.** § Errata on RFC-0106 and RFC-0083.
- **Records.** The retirement record's tracker rows and § Compatibility closure, the inventory, the brief's Spec map and slice 9 text, and this spec's ledger.
- **Unchanged:**
  - `work-loop`, `dispatch.py`, and every file under `packs/core/.apm/skills/work-loop/`;
  - the global `[authorization.refresh]` and `[authorization.migration]` tables and every reader of them;
  - the engine's readiness rules, finding table (including the `cooled_child_scope_unknown` next action), and the `tracker_profile` field it validates on an entry, which the repair reads;
  - the brief-intake adapters' code, which already pass the profile to `work-intake`;
  - the repo-origin repair steps and every Shipped spec's body.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: the source-authority record | Applicable: every tracker-origin artifact carries it, and adopters' tools parse it | `contracts/jsonschema/source-authority.schema.json`; `work-intake`'s `references/` and SKILL.md § Refresh | Platform Core maintainer | AC-0001, AC-0002 and AC-0003 pass | The schema and the parser accept the same `tracker_profile` shapes |
| Interface compatibility: which entries the registry holds, and the repair that removes the rest | Applicable: adopters' writers and the repair share the schema | `guides/core/reference/workspace-toml-schema.md`, `packs/core/.apm/skills/workspace-status/SKILL.md` and `references/mutate.md` | Platform Core maintainer | AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0017 and AC-0018 pass | Each names `tracker-entry-drop` |
| User documentation: intake and refresh of tracker work | Applicable: adopters follow the guides by hand | the guides AC-0018 lists | Platform Core maintainer | AC-0018 passes; the rewritten paragraphs are checked in review | No listed page says tracker-origin work is registered |
| Current architecture | Applicable: the work-intake architecture page states registry write authority | `docs/architecture/work-intake-and-artifact-routing.md` | Platform Core maintainer | AC-0018 passes | The page names the record as the profile's home |
| Decision rationale | Applicable: RFC-0106 D1 requires the contract change in the stop's release | RFC-0106 and RFC-0083 § Errata | eugenelim, Approver | AC-0019 and AC-0020 pass | Each entry carries owner-approved wording |
| Retirement evidence | Applicable: RFC-0105 D3 gate 4 | `docs/specs/workspace-retirement/retirement-record.md` § Disposition and § Compatibility closure; `inventory.toml` | Platform Core maintainer | AC-0021 and AC-0022 pass | The closure entry names this spec, the repair and the run |
| Delivery membership and remainder | Applicable: the brief's coverage map and slice 9 cut | `docs/product/briefs/workspace-registry-retirement-delivery.md` | eugenelim, brief owner | AC-0023 passes; `lint-brief-coverage.py` lists this spec | The brief names the post-#1651 remainder |
| Verification record | Applicable: approvals and the repair run on this repository | `docs/specs/tracker-origin-registration-stop/notes/verification-ledger.md` | Platform Core maintainer | AC-0020 and AC-0024 pass | The ledger holds each approval and the run |
| Release history | Applicable: `core`, `atlassian`, `github` and `linear` content changes | one `docs/product/changelog.d/` fragment; each pack's `pack.toml` and `.claude-plugin/plugin.json` at one new patch version | Platform Core maintainer | The changelog and version gates pass | The fragment names the stop and `tracker-entry-drop` |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.
A syscall, flag, helper name, or exact write order is mechanism that belongs in
the plan's `## Design (LLD)`, not here.

### Always do

- Take a tracker profile only from the intake's declared profile, from the existing entry's `tracker_profile`, or from the owner's explicit answer when asked for it; never from tracker content, labels, prose or the artifact's body outside its `source-authority` record.
- Regenerate the packaged and projected copies with `make build-self`, bump `core`, `atlassian`, `github` and `linear` once each, and carry the `Engine-Change-RFC: 0106` trailer on every commit that edits a file under `packages/agentbundle/`.
- Run the `work-loop` dispatch, refresh coordinator and repair suites that exist at the base after each task, and keep them passing without editing a `work-loop` file.

### Ask first

- The wording of each errata entry and of the brief's slice 9 amendment. The owner approves each before it is committed.
- Any edit to `Makefile`, a file under `.github/workflows/`, a `contracts/jsonschema/` file other than `source-authority.schema.json`, or `.workspace-prune-protected.toml`, each of which open PR #1651 also changes.

### Never do

- Edit any file under `packs/core/.apm/skills/work-loop/` or its projections, or change `dispatch.py`'s output or decision rules.
- Remove or weaken a refresh check other than the per-entry lookup, entry validation and entry revision write: the workspace digest binding, the policy read, the binding of the comparison's profile and kind to stored state, and the authority, lifecycle, approver, field and receipt checks stay.
- Move, rename or stop reading `[authorization.refresh]` or `[authorization.migration]`.
- Remove, move or rewrite a `workspace.toml` entry by hand; the repair alone removes tracker-origin entries.
- Add a dependency, a skill, a module, a finding code or a top-level directory, or any reader of the old `workspace.toml` shape outside the repair and the readers that exist at the base.

## Testing Strategy

- **Record shape and first record (AC-0001, AC-0002, AC-0003, AC-0025, AC-0029): TDD.** The schema and the parser each red on a planted record with the new table before the change; malformed tables are refusal cases.
- **Refresh (AC-0004, AC-0005, AC-0006, AC-0007, AC-0026 and AC-0008): TDD, exercised by the refresh coordinator's integration suite and the front-door suites.** Each refusal and the entry-free commit is a coordinator call over a planted repository; the existing refusal cases that do not name the entry run unchanged.
- **Router and matrices (AC-0009, AC-0016): TDD and goal-based.** `route_intake` is pure, so each tracker-origin route reds against the repo-origin route; each matrix's comparison suite passes.
- **Repair (AC-0010, AC-0030, AC-0011, AC-0027, AC-0012, AC-0013, AC-0014 and AC-0015): TDD.** Each rule is a `repair-plan` or `repair-apply` result over a planted `workspace.toml` and artifact, one planted entry per case.
- **Writer, guide and record text (AC-0017, AC-0028, AC-0018, AC-0021, AC-0022, AC-0023): goal-based.** A roster check over closed lists of files and phrases, each phrase that must be absent checked present at the base, the inventory check and the brief coverage lint.
- **Governance (AC-0019, AC-0020): goal-based.** The roster check reads each errata entry and the ledger's approval rows.
- **This repository (AC-0024): manual QA.** One repair run over real data, recorded in the ledger.

## Acceptance Criteria

Terms used below.

- **Base.** Commit `e8679a9a3`.
- **Record.** The one closed ```` ```toml source-authority ```` block of an artifact, as `scripts/refresh.py`'s parser reads it at the base.
- **Profile table.** A record's `tracker_profile` table: exactly the keys `id` and `version`, each a non-empty string holding no carriage return or line feed, `id` at most 200 characters and `version` at most 100, the length bounds the engine applies to an entry's `tracker_profile` at the base.
- **Tracker-origin entry.** An element of the first list the engine's `_extract_canonical_memberships` returns, as at the base, whose `source` is a table with `mode` exactly `"tracker-origin"`.
- **Entry-level finding.** A `reconcile` finding whose code is one of `invalid_entry`, `duplicate_membership`, `impossible_transition`, `provenance_mismatch`, `cooled_child_scope_unknown` or `refresh_conflict` and whose path is the entry's `path`.
- **Declared parent.** For a cooled tracker-origin `kind = "spec"` entry whose raw `source.parent` key is present: `none` when its value is `none` or an empty string; otherwise the path `_resolved_provenance_parent(source.parent, require_local_brief=True)` returns as at the base, when that path is a brief file and matches `^docs/product/briefs/[a-z0-9][a-z0-9-]{0,127}\.md$`. An absent key, or any other value, declares no parent. An entry is cooled when its collection and index are among the positions the engine's `cooled_work_entry_paths`, as at the base, returns for its initiative, the set `spec-entry-drop` reads.
- **Held entry.** A cooled tracker-origin `kind = "spec"` entry that has a declared parent and whose lifecycle record carries no `parent`.
- **Matched entry.** A tracker-origin entry, not a held entry, that meets each of these conditions; each is named by the reason a manual item gives when it fails:
  - `path-missing`: the entry has a `path`;
  - `artifact-missing`: that path names a confined regular file;
  - `record-missing-or-invalid`: the file holds exactly one record that parses;
  - `ref-mismatch`: the record's `source_ref` equals the entry's `source.ref`;
  - `entry-profile-invalid`: the entry's `tracker_profile` is a profile table;
  - `profile-mismatch`: the record's profile table is absent or equal to the entry's `tracker_profile`;
  - `needs-present`: the entry's `needs` is empty;
  - `other-write-pending`: no other operation of the same plan writes that file;
  - `entry-finding`: `reconcile` reports no entry-level finding for it.

**The record**

- [ ] **AC-0001.** `contracts/jsonschema/source-authority.schema.json` accepts every record its tests accept at the base, accepts each of those records with a profile table added, and rejects a record whose `tracker_profile` misses `id` or `version`, carries another key, holds a non-string or empty value, holds a value with a carriage return or line feed, or exceeds either length bound.
- [ ] **AC-0002.** `scripts/refresh.py`'s parser accepts and its renderer writes the same records the schema accepts in AC-0001, a parse then render then parse returns an equal record, and the parser refuses each record the schema rejects there with `invalid_source_authority`.
- [ ] **AC-0003.** `intake-intent`'s renderer writes, for a tracker-origin intake whose source carries a tracker profile, a record whose profile table equals that profile, and writes no record for a repo-origin intake, as at the base.
- [ ] **AC-0025.** `scripts/refresh.py` renders, from a tracker-origin source's locator, revision and declared profile, a record that its parser accepts with `source_ref`, `source_revision` and profile table equal to those values and an empty `[owned_fields]`, and refuses, with no output, a source that is not tracker-origin, carries no profile, or whose values its renderer refuses.

**Refresh**

- [ ] **AC-0004.** For an artifact whose record has no profile table, refresh returns `refresh-unavailable` with zero effects before any acquisition and the next action `add-record-tracker-profile`.
- [ ] **AC-0005.** Refresh resolves the processor registration from the record's profile table, and returns `refresh-unavailable` with zero effects when a request names a different profile `id` or `version`.
- [ ] **AC-0006.** `coordinate_local_refresh` commits a local refresh for an artifact that no `workspace.toml` entry names, and `workspace.toml`'s bytes are the same afterwards.
- [ ] **AC-0007.** `coordinate_local_refresh` refuses with `invalid_local_update`, changing no file, when the proposed `workspace.toml` bytes differ from the current ones, or when the proposed record's profile table differs from the current record's.
- [ ] **AC-0026.** `coordinate_local_refresh` refuses with `invalid_local_update`, changing no file, when the current record read from disk has no profile table, when that table's `id` or `version` differs from the comparison's `profile_id` or `profile_version`, or when the comparison's `artifact_kind` differs from the artifact's kind, read from its first line that starts `# ` after an optional leading front-matter block that opens and closes with a `---` line: `spec` when that line starts `# Spec:`, `brief` when it starts `# Brief:`, and `intent` otherwise.
- [ ] **AC-0008.** Every refresh coordinator test at the base that does not construct, alter or assert on a `workspace.toml` entry passes unchanged, including the workspace digest and the missing or substituted policy cases.

**The router**

- [ ] **AC-0009.** For each signal whose `authority_mode` is `tracker-origin`, `route_intake` returns a `Route` whose fields other than `authority_mode` equal those it returns for the same signal with `authority_mode` `repo-origin`, and no file under `packs/core/.apm/skills/work-intake/scripts/` defines `workspace_source_record`.

**The repair**

- [ ] **AC-0010.** `workspace-status repair-plan` holds one `tracker-entry-drop` operation for each matched entry, naming its initiative key (empty for a top-level collection), collection, index, `path`, `kind`, registry fingerprint, and the profile it writes, or none when the record already holds an equal profile table.
- [ ] **AC-0030.** `repair-plan` holds no `queue-to-shipped` or `queue-remove` operation for a matched entry, and holds the operations it holds at the base for every other entry.
- [ ] **AC-0011.** For each tracker-origin entry that is not a matched entry and not a held entry, `repair-plan` holds no `tracker-entry-drop` operation and one manual item naming the entry's `path`, or its locator when it has no `path`, and the reason of the first matched-entry condition it fails.
- [ ] **AC-0027.** For each held entry, `repair-plan` holds no `tracker-entry-drop` operation and one manual item naming the entry's `path`, its lifecycle record's path, and the `parent` value to add to that record; once the record carries `parent`, the next `repair-plan` treats the entry as any other tracker-origin entry.
- [ ] **AC-0012.** `repair-apply --yes` adds the planned profile table to the record of each applied operation, after which the artifact holds exactly one record, which the parser accepts and which equals the record before the write with that table added, and every byte outside the record is unchanged; and it removes the entry in the same atomic, comment-preserving `workspace.toml` write under the writer lock as its other applied operations.
- [ ] **AC-0013.** `repair-apply --yes` refuses an operation, leaving its entry and artifact unchanged, when the entry the registry read under the lock holds at the planned locator, re-derived from that read, is not a matched entry with the planned `path`, `kind`, fingerprint and profile, or is a held entry, or when the artifact's bytes differ from those the plan read.
- [ ] **AC-0014.** On a registry where every planned operation applies, a following `repair-plan` holds no `tracker-entry-drop` operation, and refresh on each migrated artifact resolves the entry's former profile.
- [ ] **AC-0015.** The repair suites at the base for `needs-to-header`, `captured-to-file`, `intent-brief-drop` and `spec-entry-drop` pass unchanged, and the stdout of `dispatch.py --root <tree>` is byte-identical immediately before and after `repair-apply --yes` on each planted tree of this spec's repair suite, which plants at least one matched entry of each kind `intent`, `brief` and `spec` in a collection that agrees with its artifact's status, an Archived tracker-origin spec's matched entry in `work.queue`, one held entry before and after its record gains `parent`, and one unmatched entry for each manual-item reason.

**Writers and matrices**

- [ ] **AC-0016.** Each tracker-origin case of `packs/core/.apm/skills/work-intake/evals/files/routing/matrix.json` and of the `jira-brief-intake`, `jira-align-brief-intake`, `github-brief-intake` and `linear-brief-intake` intake matrices expects AC-0009's route, every other case is byte-identical to the base, and each matrix's comparison suite passes.
- [ ] **AC-0017.** Read with each run of whitespace as one space, none of these files holds the phrase listed for it:
  - `packs/core/.apm/skills/work-intake/SKILL.md`: `is registered as before, because refresh checks its tracker profile through the entry alone`, `register a tracker-origin intent as a Draft`, `resolve the existing entry and its exact tracker profile`, `register a tracker-origin artifact in`, `(a tracker-origin intent is registered)`, or `In each registered case the artifact comes first`;
  - `packs/core/.apm/skills/author-delivery-brief/SKILL.md`: `add its one schema-valid Draft entry`, `move the complete structured brief entry`, `tracker-origin brief's workspace entry`, `Only a tracker-origin brief's entry moves`, or `its existing structured workspace entry`;
  - `packs/core/.apm/skills/close-work/SKILL.md`: `for a tracker-origin brief it also moves`;
  - `packs/core/.apm/skills/intake-intent/SKILL.md`: `let the calling intake workflow add its one non-dispatchable`;
  - `packs/github/JOURNEY.md` and `packs/linear/JOURNEY.md`: `registered tracker-origin artifact`.
- [ ] **AC-0028.** Read with each run of whitespace as one space, each of these files holds each phrase listed for it:
  - `packs/core/.apm/skills/work-intake/SKILL.md`: `tracker_profile`, `never infer a processor from the artifact kind, tracker content, labels, or prose`, and, in one paragraph, `add-record-tracker-profile`, `tracker-entry-drop`, and `ask the owner for the profile`;
  - `packs/core/.apm/skills/author-delivery-brief/SKILL.md` and `packs/core/.apm/skills/new-spec/SKILL.md`: `keep an existing source-authority block byte for byte`;
  - `packs/core/.apm/skills/workspace-status/SKILL.md`, `packs/core/.apm/skills/workspace-status/references/mutate.md` and `guides/core/reference/workspace-toml-schema.md`: `tracker-entry-drop`;
  - `docs/architecture/work-intake-and-artifact-routing.md`: `tracker_profile`.
- [ ] **AC-0029.** `run_intake_transaction`, given a tracker-origin source, commits only when the artifact it materialized then holds exactly one record whose `source_ref`, `source_revision` and profile table equal that source's locator, revision and declared profile; otherwise, including when the materializer wrote a record of its own or AC-0025 refuses the source, it ends with `rolled_back` or `reconciliation_required`, leaves no new artifact, and starts no dispatch.

**Guides**

- [ ] **AC-0018.** Read with each run of whitespace as one space, none of these files holds the phrase listed for it, and the schema guide's section rule reads the file's raw lines, a heading being a line that starts `#` outside a fenced code block:
  - `guides/core/reference/workspace-toml-schema.md`: `tracker-origin intent and brief entries stay`, `A tracker-origin spec keeps its entry`, `For a tracker-origin brief entry`, or `tracker-origin entry moves to the matching collection`, and each line of it that holds `mode = "tracker-origin"` lies in a section, between two headings, that holds `tracker-entry-drop`;
  - `guides/core/how-to/intake-an-external-brief.md`: `keeps a registry entry`, `Brief file created and registered in`, or `If registration fails`;
  - `guides/core/reference/work-intake-routing-and-lifecycle.md`: `Only a spec or a tracker-origin intent or brief is registered`, `register it only when it is a spec or a tracker-origin`, or `A tracker-origin brief's entry sits in the collection that matches its status`;
  - `guides/_shared/reference/work-intake-routing-and-lifecycle.md`: `` `work.queue` for a tracker-origin one ``, `` `brief_queue.draft` for a tracker-origin one ``, `repository backlog for a tracker-origin one`, or `A spec, and a tracker-origin intent or brief, is registered`;
  - `guides/catalogue-curation/tutorials/your-first-skill.md`: `registers a tracker-origin item`;
  - `guides/_shared/how-to/use-work-intake.md`: `A spec or a tracker-origin item also gets a non-dispatchable entry` or `is registered as tracker-origin`;
  - `guides/core/how-to/capture-work.md`: `A spec or a tracker-origin item also gets a non-dispatchable entry`;
  - `guides/core/how-to/start-or-remember-work.md`: `unless it is tracker-origin`;
  - `guides/core/explanation/two-room-model.md`: `only a spec or a tracker-origin item is also registered`, `a tracker-origin one is registered in`, or `a tracker-origin entry moves to`;
  - `guides/product-engineering/how-to/hand-an-intent-to-build.md`: `a spec or a tracker-origin artifact is also registered`;
  - `guides/atlassian/how-the-atlassian-pack-works.md`: `For registered tracker-origin work`;
  - `guides/atlassian/work-with-jira.md`: `created and registered a tracker-origin`;
  - `docs/architecture/work-intake-and-artifact-routing.md`: `a tracker-origin brief's entry carries the same state`, `for a tracker-origin brief, its entry`, `mirrored by structured workspace source fields`, or `Refresh processors receive an existing registered artifact`.

**Governance**

- [ ] **AC-0019.** Each of these § Errata sections holds an entry dated on or after 2026-10-30 that links RFC-0106 and holds each literal listed for it:
  - `docs/rfc/0106-stop-registering-derivable-work.md`: `tracker-entry-drop`, `tracker_profile`, and `source-authority`;
  - `docs/rfc/0083-work-intake-and-artifact-routing.md`: `tracker_profile` and `refresh`.
- [ ] **AC-0020.** `docs/specs/tracker-origin-registration-stop/notes/verification-ledger.md` holds one row for each entry AC-0019 lists and for the brief amendment AC-0023 names, naming its target file and the owner's approval with an ISO 8601 timestamp to the minute with its UTC offset, which is earlier than the author date (`git log --format=%aI`) of the commit that adds that text.

**Records**

- [ ] **AC-0021.** In `docs/specs/workspace-retirement/retirement-record.md`, the § Disposition rows `source.tracker_profile`, `source.tracker_profile.id` and `source.tracker_profile.version` name the record's `tracker_profile` table as their Home; no § Disposition row holds `tracker-origin spec entries, and their writers, stay until slice 9` or `tracker-origin intent and brief entries stay until slice 9`; and § Compatibility closure holds an entry that links this spec and names `tracker-entry-drop` and the ledger's repair run.
- [ ] **AC-0022.** `docs/specs/workspace-retirement/inventory.toml` holds one `docs/specs/tracker-origin-registration-stop/*` `contract` row at `owner = 9`, a row for each file this spec adds or changes that names `workspace.toml`, `workspace-status` or `workspace_status` outside an inventoried directory, and no row for a file this spec leaves without such a name; and the inventory check passes.
- [ ] **AC-0023.** `docs/product/briefs/workspace-registry-retirement-delivery.md`'s Spec map holds `tracker-origin-registration-stop`, its slice 9 text holds owner-approved wording that names, as work after the execution-supervisor cutover, moving the engine rules `dispatch.py` needs into `work-loop`, shrinking `workspace-status` to the repair, removing the legacy registry entries with the spec-status lint's deferral anchors, a home for `[authorization.refresh]` and `[authorization.migration]`, the deletion of `workspace.toml`, and the certification, and `lint-brief-coverage.py` passes on it.

**This repository**

- [ ] **AC-0024.** The ledger holds the `repair-plan` output on this repository at this branch, with its count of `tracker-entry-drop` operations and tracker-origin manual items, each `0`.

## Follow-ons

- eugenelim: the brief's slice 9 text (AC-0023) — the work after the execution-supervisor cutover, including a home for the two `[authorization.*]` tables, which the retirement record's § Disposition does not yet cover.

## Assumptions

- Product: adopters with tracker-origin entries are invisible from here — whether any entry fails the matched-entry test in practice is ungrounded, and the manual item is the only notice.
