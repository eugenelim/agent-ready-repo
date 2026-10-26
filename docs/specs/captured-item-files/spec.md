# Spec: Captured items in their own files

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-26 by eugenelim, spec and plan, after spec-stage shaping, adversarial, and security reviews over seven rounds ending clean; review records under `.context/reviews/captured-item-files-spec-20261026T0431/`. Re-approved 2026-10-26 by eugenelim after controlled amendment 1 (`notes/verification-ledger.md` § Amendment 1: AC-0037's Case-cell rule), clean on adversarial review of the amendment apart from one deferred nit. Re-approved 2026-10-26 by eugenelim after controlled amendment 2 (`notes/verification-ledger.md` § Amendment 2: AC-0021's fail-closed refusals; T9 added), clean on adversarial review of the amendment; records under `.context/reviews/captured-item-files-amendment2/`.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0106 (D3, a captured item's own file with `Status:`, `Kind:`, and `Type:` lines and the migration's kind assignment; D1, the shaping-item guard's replacement and the rule that a writer stops only with its contract), RFC-0105 (D3, the behavioral-equivalence gate), RFC-0103 (D1, the typed `Parent intent:` reference), ADR-0053 (D9, OKR gaps routed to `frame-situation` by their `strategy` type), ADR-0074 (standard-library skill scripts)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Contract:** none — the captured-item file grammar is contracted by the criteria below; `contracts/jsonschema/workspace-entry.schema.json` keeps its shape, because the repair reads the registry through it.
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
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer or agent who records work for later — a defect, a design question, an OKR gap — finds it as one file, `docs/product/captured/<slug>.md`, whose own `Status:`, `Kind:`, and `Type:` lines say what it is, and `work-loop` routes a supplied slug whose file carries a `Type:` line to its shaping skill. Success is that every captured item in this repository's registry gets such a file in one confirmed repair run, with an item-for-item comparison showing none was lost, and that a registry entry still pointing a captured item anywhere else is refused and pointed at the repair.

## What Changes

- The captured-item file grammar — one file per item in `docs/product/captured/`, carrying `Status:`, `Kind:`, and optional `Type:`, `Resolution:`, `Parent intent:`, and `Detail:` lines, beside slice 2's `Depends on:` and `Dependency receipts:`.
- Its reader, a `captured` section of `workspace-status status` listing every file in that directory, and the lifecycle checks that read a registered item's status from its file — `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` and `workspace_status.py`, with their packaged copies.
- The `unmigrated_captured_item` refusal and the `invalid_captured_item` finding — the same engine.
- The shaping-item guard, matching a captured-item file's `Type:` line instead of registry entries — the engine's guard helper and `packs/core/.apm/skills/work-loop/SKILL.md` Step 0.
- A `captured-to-file` operation in `repair-plan` and `repair-apply` — `workspace_status.py`. It writes records and `workspace.toml` and never writes a file a registry entry points at.
- The migration of this repository's 77 captured items: 77 files under `docs/product/captured/`, 51 registry `path` values re-pointed to them, and one design note's `Depends on:` line copied into its record, then removed from the note by hand.
- The writers and suggesters that name a captured item's path: `work-intake`'s remember route; `run-okr-cascade` and its cross-pack routing reference, jointly with the `product-strategy` pack; `frame-situation` and `diverge-solutions` in `product-engineering`, with their examples; `work-loop`'s pre-flight failure capture; and the architect guide `establish-reference-architecture.md`. Each keeps registering.
- Unchanged: the 26 legacy slug-only entries keep `unsupported_legacy` until the brief's slice 9 removes them, and their records are found by slug. The legacy `--migration-selection` route keeps its target collections; a captured item it registers outside the directory is refused like any other and moved by the repair. `lint-spec-status.py`'s deferral anchors keep resolving, because the repair refuses a slug that would change one.
- The captured-item equivalence rows — `docs/specs/workspace-retirement/retirement-record.md` § Equivalence, with an `intended change` result admitted by a controlled amendment of the `workspace-retirement` spec.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: the captured-item file grammar | Applicable: a new published file shape that writers and the reader share | `packs/core/.apm/skills/work-intake/SKILL.md` § Terse workspace capture, and `guides/core/reference/workspace-toml-schema.md` § Defects | Platform Core maintainer | Both name the directory, the six fields, and their values; AC-0038 passes | Both surfaces match AC-0001 |
| User documentation: how an adopter moves captured items | Applicable: adopters upgrade by running the repair | `packs/core/.apm/skills/workspace-status/references/mutate.md` § Repair subcommands, and `guides/core/how-to/start-or-remember-work.md` | Platform Core maintainer | `captured-to-file` and its confirmation are described | The text names the command, its confirmation, and its item comparison |
| Maintainer procedure: the shaping-item guard | Applicable: `work-loop`'s Step 0 instruction changes | `packs/core/.apm/skills/work-loop/SKILL.md` Step 0 | Platform Core maintainer | AC-0040 passes | The guard paragraph names `captured.items` and no registry collection |
| Cross-pack contract: OKR gaps as captured items | Applicable: `run-okr-cascade` writes the file | `packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md` and `references/cross-pack-routing.md` | Platform Core maintainer with the `product-strategy` pack owner | AC-0038 and AC-0039 pass | The gap file carries `Kind: intent` and `Type: strategy` |
| Decision rationale: equivalence evidence | Applicable: RFC-0105 D3 gate 3 | `docs/specs/workspace-retirement/retirement-record.md` § Equivalence | Platform Core maintainer | The amended `workspace-retirement` check passes | Every case in AC-0037 has a row |
| Release history | Applicable: shipped `core`, `product-strategy`, and `product-engineering` content changes | a `docs/product/changelog.d/` fragment; each changed pack's `pack.toml` and `.claude-plugin/plugin.json` at one new patch version | Platform Core maintainer | The changelog gate passes | The fragment names the repair and the refusal |
| Delivery membership | Applicable: the brief's coverage map | The brief's Spec map and this spec's `workspace.toml` entry | `author-delivery-brief` | `lint-brief-coverage.py` lists this spec under the brief | The coverage lint passes |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Open every captured-item file, source file, and directory listing through confinement checks that refuse what AC-0004, AC-0041, and AC-0021's source bullet refuse, write every record as AC-0027 and AC-0046 require, and never open a cooled artifact's body.
- Keep each dependency satisfaction rule as it is, apart from AC-0013's refusal; AC-0009, AC-0010, AC-0042, and AC-0045 state the kept rules for captured items.
- Regenerate the packaged copies with `make build-self`, bump each changed pack's version, and carry the `Engine-Change-RFC: 0106` trailer on every commit that edits an engine source.
- Run the repair on this repository only as `repair-plan`, then the owner's confirmation of that exact plan, then `repair-apply`.

### Ask first

- Running `repair-apply` against this repository. The owner confirms the exact plan file, including every slug, kind, and record text it holds.
- Adding a finding code other than `unmigrated_captured_item` and `invalid_captured_item`.
- Editing a `retirement-record.md` Disposition row other than the Home cells of `entry.kind`, `entry.slug`, `entry.intent`, and `entry.type`.
- Any change to `frame-situation`, `diverge-solutions`, `run-okr-cascade`, or `establish-reference-architecture.md` beyond the captured-item path and file their output names.

### Never do

- Stop any registration writer, or amend ADR-0053 D9, RFC-0063, or `work-intake`'s registration rule. The follow-on spec does that, after the brief's slice 5 ships.
- Let the reconciliation, the `captured` listing, or the shaping-item guard open the file at an unmigrated captured membership's path.
- Change `navigate-intents`, except to add this spec's two finding codes to the readiness bridge's pinned copy of the `workspace-status` finding table, which that bridge's parity test requires.
- Add a dependency, a skill, a module outside the two `workspace-status` scripts and their packaged copies, or a top-level directory. `tomlkit` stays confined to `repair-apply`, as `packs/core/AGENTS.md` declares.
- Let a `captured-to-file` operation write any file other than `workspace.toml`, the writer lock, the plan file, and its record. Edit no source file by hand, except removing from this repository's one design note the dependency lines the repair copied into its record, after `repair-apply`.
- Edit `workspace.toml` beyond the repair's `path` rewrites, its header comment on where a captured item's entry points, adding and moving this spec's own entry, and the parent brief's entry moved together with its `Status:` line.

## Testing Strategy

- **Reader, listing, and confinement (AC-0001, AC-0002, AC-0003, AC-0004, AC-0041, AC-0005, AC-0006): TDD.** Each is a rule over one file's preamble or one directory listing, so a fixture with one planted case reds each test before the rule exists.
- **Lifecycle, satisfaction, and refusal (AC-0007, AC-0008, AC-0009, AC-0010, AC-0042, AC-0011, AC-0012, AC-0013, AC-0045): TDD, paired fixtures.** Each case is written once in today's shape and once migrated; the outcome of today's shape is recorded from the engine at commit `ce30822a0` as a frozen expectation.
- **Guard (AC-0014, AC-0015): TDD.** One planted file per case.
- **Repair (AC-0016, AC-0043, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0024, AC-0025, AC-0026, AC-0027, AC-0046, AC-0047, AC-0028, AC-0030, AC-0031, AC-0032): TDD over fixture repositories**, including an interrupted apply and a rerun.
- **This repository's migration (AC-0033, AC-0034, AC-0035, AC-0036): goal-based.** The repair runs here once, and the `status` output and spec-status lint of the tree it read are compared with the tree it left.
- **Equivalence record (AC-0037): goal-based.** The amended `workspace-retirement` check runs against this repository.
- **Writer and guard instructions (AC-0038, AC-0044, AC-0039, AC-0040): goal-based.** A roster check over a closed list of files and phrases.

## Acceptance Criteria

Terms used below. Preamble, field value, live intent, canonical membership, captured-item reference, and typed reference are as the [`depends-on-headers`](../depends-on-headers/spec.md) spec's Acceptance Criteria define them.

- **Captured-item directory.** `docs/product/captured/`.
- **Captured-item file.** A directory entry directly in the captured-item directory whose name matches `^[a-z0-9][a-z0-9-]*\.md$`. Its **slug** is its name without `.md`. Every other entry in the directory is ignored.
- **Captured membership.** A canonical membership whose path is a captured-item reference. It is **migrated** when its path names a captured-item file, and **unmigrated** otherwise.
- **Legacy captured entry.** A registry entry in `backlog.open`, `backlog.closed`, `shaping_queue.backlog`, or `shaping_queue.active` that is a table with a string `slug` key, no `path` key, and a `kind` that is absent or `defect`. A slug-only table with another `kind` is a legacy artifact alias and keeps `unsupported_legacy`.
- **Shaping types.** `shape`, `research`, `strategy`, `design`, and `signal`. Each **routes to** `intent`, `desk-research-project-start`, `frame-situation`, `experience-status`, and `(signal — no action)`, in turn.
- **Captured item at migration.** Each captured membership and each legacy captured entry in the registry the repair reads.
- **Cooled.** In the cooled set the engine reads from the repository's lifecycle records, never from the registry.
- **Base slug.** For a legacy captured entry, its `slug`. For an unmigrated membership, its source file's name without its last extension, lowercased, with each run of characters outside `[a-z0-9]` replaced by one `-` and leading and trailing `-` removed. For a migrated membership, both its file's slug and the base slug its record's `Detail:` path would give as a source.
- **Confined file.** A path with no symbolic link in any segment that names a regular file inside the repository with exactly one link, and whose identity is the same when it is opened as when it was checked.
- **Echo rule.** In a finding, and in `repair-plan` or `repair-apply` output, each value is judged on its own against its position's grammar: a path against the captured-item reference grammar, a slug against the captured-item file name grammar, `Status:`, `Kind:`, `Type:`, and `Resolution:` against their value sets, `Parent intent:` against the typed-reference grammar, an unread path in the finding of AC-0021's last two bullets against the repository-path grammar of one or more `/`-separated segments, each matching `[A-Za-z0-9._-]+` and none `.` or `..`, a dependency item against the typed-reference or captured-item reference grammar, a receipt token against the token rules the `depends-on-headers` spec's AC-0004 sets for its position, a SHA-256 or registry fingerprint against `^[0-9a-f]{64}$`, a collection against the collection names, and an entry position against a non-negative integer; a header edge is judged part by part as its waiting path, item, and receipt. A value appears verbatim only when it matches, has at most 200 characters, and holds no control character; otherwise it appears as an empty string. A record's full text and a summary are free text: they appear whole, as JSON strings in which every control character and every non-ASCII character is escaped.

Each criterion from AC-0001 to AC-0032, from AC-0041 to AC-0043, and from AC-0045 to AC-0047 is a rule the engine or the repair enforces. Given an input that breaks one about a single file or entry, the result names that file's path or that entry's slug under the echo rule.

**Reader and listing**

- [x] **AC-0001.** A captured-item file is valid when its preamble holds each of these fields at most once, `Status:` and `Kind:` exactly once, and no field value outside its set:
  - `Status:` is `Open` or `Closed`;
  - `Kind:` is `defect`, `design`, `research`, or `intent`;
  - `Type:` is a shaping type;
  - `Resolution:` is `fixed`, `declined`, or `superseded`, and is present exactly when `Kind:` is `defect` and `Status:` is `Closed`;
  - `Parent intent:` is a typed reference whose kind is `intent`, `outcome`, `opportunity`, or `capability`;
  - `Detail:` is a captured-item reference.

  Otherwise it gives an `invalid_captured_item` finding naming its path and the first failing field, in the order listed.
- [x] **AC-0002.** `workspace-status status` output holds a `captured` object with `items` and `findings`. `items` holds one entry per captured-item file, sorted by path. A valid, non-cooled file's entry holds its `path`, `slug`, `status`, and `kind`, and its `type`, `routes_to`, `resolution`, `parent_intent`, and `detail` or `null`. Every other entry holds its `path`, its `slug`, and exactly one of `cooled: true`, `invalid: true`, or `unreadable: true`. `findings` holds every `invalid_captured_item` and `unreadable_artifact` finding the listing gives.
- [x] **AC-0003.** When the captured-item directory is absent, `items` and `findings` are empty.
- [x] **AC-0004.** When any segment of the captured-item directory's path is a symbolic link, the directory resolves outside the repository, or it cannot be listed, `items` is empty and `findings` holds one `unreadable_artifact` finding naming the directory.
- [x] **AC-0041.** A captured-item file that is not a confined file, or that cannot be read, is listed with `unreadable: true` and an `unreadable_artifact` finding naming it, and none of its content is used.
- [x] **AC-0005.** A cooled captured-item file is listed without any part of it being opened.
- [x] **AC-0006.** The `captured` object is the same for any two registries over the same tree, whatever entries either holds.

**Lifecycle, satisfaction, and the refusal**

- [x] **AC-0007.** A migrated captured membership gets the existing `impossible_transition` finding when its file's `Kind:` differs from the membership's `kind`; when its file's `Status:` is `Closed` in `backlog.open`, `shaping_queue.backlog`, or `shaping_queue.active`; or when its file's `Status:` is `Open` in `backlog.closed`.
- [x] **AC-0008.** A migrated captured membership whose file is invalid or unreadable gets that file's `invalid_captured_item` or `unreadable_artifact` finding and no other lifecycle finding.
- [x] **AC-0009.** A dependency on a non-cooled migrated captured membership of kind `defect` is satisfied exactly when the membership is in `backlog.closed` and its file is valid, `Closed`, and `Resolution: fixed`.
- [x] **AC-0010.** A dependency on a non-cooled migrated captured membership of any other kind is not satisfied.
- [x] **AC-0042.** A dependency on a cooled migrated captured membership is satisfied, without any part of its file being opened, exactly when its kind is not `defect` or it is a `defect` whose membership is in `backlog.closed`.
- [x] **AC-0011.** A non-cooled unmigrated captured membership gets an `unmigrated_captured_item` finding naming its path, whose next action names `workspace-status repair-plan`. A cooled unmigrated captured membership gets no such finding.
- [x] **AC-0012.** The reconciliation opens no part of the file at an unmigrated captured membership's path: not for its lifecycle, its provenance, its routing identity, or its `Depends on:` header.
- [x] **AC-0013.** A dependency item that names a non-cooled unmigrated captured membership's path gives `unsatisfied_dependency` and is not satisfied.
- [x] **AC-0045.** A dependency item that names a cooled unmigrated captured membership's path gives the result it gives at commit `ce30822a0`, without any part of that file being opened.

**The shaping-item guard**

- [x] **AC-0014.** The shaping-item guard, given a slug, returns the skill the `Type:` value routes to when `docs/product/captured/<slug>.md` is a valid, non-cooled captured-item file with a `Type:` line. It returns no match, reading no registry entry, when that file is valid without a `Type:` line, cooled, or absent, and when the slug is outside the captured-item file name grammar, in which case it opens no file.
- [x] **AC-0015.** The shaping-item guard refuses, with that file's `invalid_captured_item` or `unreadable_artifact` finding, when `docs/product/captured/<slug>.md` is invalid or unreadable.

**The repair**

- [x] **AC-0016.** `repair-plan` emits one `captured-to-file` operation for each non-cooled unmigrated captured membership and for each legacy captured entry whose slug names no captured-item file, unless AC-0021 or AC-0022 refuses it. It emits no operation and no finding for a cooled unmigrated captured membership.
- [x] **AC-0043.** `repair-plan` reports a manual finding naming a legacy captured entry and its record path, and emits no operation for it, when its slug names a captured-item file that is unreadable or whose bytes differ from the record AC-0019 and AC-0020 derive for it.
- [x] **AC-0017.** Each `captured-to-file` operation names its record path, the record's full text, and its entry's collection and position; a membership's operation also names its source path, the source file's SHA-256, its registry fingerprint, and the `Depends on:` and `Dependency receipts:` items it copies.
- [x] **AC-0018.** A record's slug is its entry's base slug. When an unmigrated membership's base slug is empty or equals a base slug of any other captured item at migration, it is prefixed with `<d>-`, where `<d>` is the name of the directory above `notes/` when the source's parent directory is `notes/`, and the source's parent directory otherwise.
- [x] **AC-0019.** The record holds, in this order: a `# ` title of its slug with each `-` as a space and the first letter capitalized; `Status:` `Open`, or `Closed` for an entry in `backlog.closed`; `Kind:`; `Type:` when the entry is a legacy captured entry whose `type` is a shaping type; `Resolution:` copied from the source file when the status is `Closed`; `Parent intent:` when the entry carries an `intent` path; `Detail:` naming the source path for a membership; copies of the source's `Depends on:` and `Dependency receipts:` lines; and then, when the entry has a `summary`, a `## Summary` heading followed by the summary.
- [x] **AC-0020.** The record's `Kind:` is the entry's `kind`. For a legacy captured entry with no `kind` it is `defect` when the entry has no `type`, `intent` for `shape` or `strategy`, `research` for `research`, and `design` for `design`. The `Parent intent:` value is the typed reference, by intent kind and `Slug:`, of the live intent at the entry's `intent` path.
- [x] **AC-0021.** `repair-plan` reports a manual finding naming the entry, and emits no operation for it, for each of these:
  - a source file that is missing, unreadable, outside the repository, or not a confined file;
  - a source path that more than one canonical membership names, or that a dependency item of another canonical membership names;
  - a membership whose `kind` is not `defect`, `design`, `research`, or `intent`;
  - a membership whose registry entry still carries a non-empty typed `needs` array;
  - a source file whose own `Status:` breaks its collection's rule: a `defect` that is `Closed` in `backlog.open`; another kind whose status is not `Draft` in `backlog.open`; a status in `shaping_queue.backlog` or `shaping_queue.active` that is terminal for its kind, which is `Accepted` or `Fulfilled` for `intent`, `Complete` for `research`, and `Approved` for `design`; or a `defect` in `backlog.closed` that is not `Closed` with a `Resolution:` of `fixed`, `declined`, or `superseded`;
  - a slug still outside the captured-item file name grammar, or still equal to another captured item's slug, after AC-0018;
  - a slug that differs from the file stem of the source path when a spec's `(deferred: <anchor>)` marker names that stem;
  - a membership whose record path already holds a file whose bytes differ from the planned record, which AC-0043 covers for a legacy captured entry;
  - a legacy captured entry with no `kind` whose `type` is `signal` or outside the shaping types;
  - an `intent` path that is not a live intent;
  - a `summary` holding a control character other than a line feed;
  - a planned record that the reader would not read back as valid with exactly the field values AC-0019 and AC-0020 derive;
  - a membership whose slug differs from its source file's stem, when any spec's `(deferred: <anchor>)` markers cannot be read: a `docs/specs/<d>/spec.md` that is cooled, unreadable, or not a confined file, or a `docs/specs/` that exists but cannot be listed;
  - a membership, when the file of another non-cooled canonical membership is present but unreadable or not a confined file; a missing or cooled membership's file names nothing.

  The finding for either of the last two bullets names each path that could not be read.
- [x] **AC-0022.** When the canonical findings hold `invalid_workspace` or `configuration_mismatch`, `repair-plan` emits no `captured-to-file` operation and no AC-0021 or AC-0043 finding.
- [x] **AC-0024.** `repair-apply`, given a confirmed plan, writes each operation's record, and then sets each migrated membership's `path` to its record path in one `workspace.toml` write.
- [x] **AC-0025.** For its `captured-to-file` operations, `repair-apply` changes no byte of `workspace.toml` outside the `path` values they set, and writes no file other than `workspace.toml`, the writer lock, and the records they name. A `needs-to-header` operation in the same plan writes what the `depends-on-headers` spec allows it.
- [x] **AC-0026.** Under the shared writer lock, `repair-apply` refuses an operation, changing nothing for it, when its record path, source path, slug, entry, record text, or copied items differ from the values re-derived from the current registry and files; when the source file's SHA-256 or the registry fingerprint no longer matches the plan; or when the membership is now cooled or the cooled state cannot be read.
- [x] **AC-0027.** `repair-apply` creates a record only by an exclusive create that follows no link and fails when any entry exists at the record path.
- [x] **AC-0046.** `repair-apply` creates a record only at a record path with no symbolic link in any segment, inside a `docs/product/captured/` that is a directory inside the repository when checked after any directory creation. Otherwise it refuses the operation, changing nothing for it.
- [x] **AC-0047.** A record path that already holds a confined file with exactly the planned bytes is left as it is. Any other entry at the record path, including one the exclusive create finds, refuses the operation, changing nothing for it.
- [x] **AC-0028.** After an interrupted `repair-apply`, a rerun of `repair-plan` and `repair-apply` finishes the migration with the same records. A record the interruption left with fewer than its planned bytes gives AC-0021's differing-bytes finding for a membership, or AC-0043's finding for a legacy captured entry, each naming the record path, and the rerun finishes once that file is removed.
- [x] **AC-0030.** `repair-apply` reports the captured items at migration it read, each as its slug, `kind`, and source path or `null`; each record it wrote or kept, read back as its slug and every field AC-0019 writes; and the header edges of every copied line as read from the source and as read back from the record, each keyed by its record path.
- [x] **AC-0031.** `repair-apply` exits non-zero when any record reads back with a field value that differs from its planned value, or when the header edges read from a source differ from those read back from its record.
- [x] **AC-0032.** Every value `repair-plan` and `repair-apply` print follows the echo rule. The plan file holds every value unredacted, it is the surface the owner confirms, and AC-0031's comparisons use the unredacted values.

**This repository**

- [x] **AC-0033.** On this repository at the implementing pull request's head commit, every captured item at migration has a valid captured-item file.
- [x] **AC-0034.** On this repository at the implementing pull request's head commit, every captured membership is migrated and the `captured` object holds no finding.
- [x] **AC-0035.** On this repository, `workspace-status status` over the tree after `repair-apply` reports the same `canonical.ready`, `canonical.active`, and `canonical.blocked` paths, and the same canonical findings by code, as the engine at commit `ce30822a0` reports over the tree the repair read, with each finding on a migrated membership's old path appearing on its new one.
- [x] **AC-0036.** On this repository, every `(deferred: <anchor>)` marker that `lint-spec-status.py` resolves over the tree the repair read also resolves over the tree it left.
- [x] **AC-0037.** `docs/specs/workspace-retirement/retirement-record.md` § Equivalence holds one row for each of these cases, its Case cell being the case's name up to the first colon outside a code span, under the criteria the amended `workspace-retirement` spec states for that section:
  - the captured-item file migration;
  - the captured-item lifecycle status;
  - the captured-item dependency;
  - the unmigrated captured-item refusal;
  - the deferral anchor;
  - entries that carry no `kind`: the kind assigned to a slug-only entry, as an intended change;
  - a captured-item file that carries a `Type:` line: the shaping-item guard's match, as an intended change;
  - matches nothing else: the shaping-item guard no longer matching a registry entry, as an intended change.

**Writer and guard instructions**

- [x] **AC-0038.** Each of these files names `docs/product/captured/`, and no fenced `toml` block in it holds a `path` value other than one under `docs/product/captured/`, a `docs/specs/<d>/spec.md` path, or a path under `docs/product/briefs/` or `docs/product/intents/`:
  - `packs/core/.apm/skills/work-intake/SKILL.md`;
  - `packs/core/.apm/skills/work-loop/SKILL.md`;
  - `packs/core/.apm/skills/work-loop/references/pre-flight-failures.md`;
  - `packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md`;
  - `packs/product-strategy/.apm/skills/run-okr-cascade/references/cross-pack-routing.md`;
  - `packs/product-engineering/.apm/skills/frame-situation/SKILL.md`;
  - `packs/product-engineering/.apm/skills/frame-situation/examples/signal-to-finding.md`;
  - `packs/product-engineering/.apm/skills/diverge-solutions/SKILL.md`;
  - `packs/product-engineering/.apm/skills/diverge-solutions/examples/opportunity-to-options.md`;
  - `guides/architect/how-to/establish-reference-architecture.md`;
  - `guides/core/reference/workspace-toml-schema.md`.
- [x] **AC-0044.** No fenced `toml` block or inline code span in a file AC-0038 lists holds a table with a `slug` key and no `path` key.
- [x] **AC-0039.** `packs/product-strategy/.apm/skills/run-okr-cascade/SKILL.md` names `Kind: intent` and `Type: strategy` for each gap file.
- [x] **AC-0040.** In `packs/core/.apm/skills/work-loop/SKILL.md`, the paragraph beginning `Then apply the **Shaping-item guard**` names `captured.items`, `routes_to`, `invalid`, and `unreadable`, and does not name `[shaping_queue]` or `[backlog].open`.

## Follow-ons

- The brief's slice 3, continued as the `captured-item-registration-stop` spec once slice 5 ships: amend ADR-0053 D9, RFC-0063, and `work-intake`'s registration rule; stop every captured-item registration writer; and give a captured item of any kind a finding-free closed state that settles a dependency through its own `Status:` and `Resolution:` when it has no membership.
- The owners of the `entry.needs (string form)` and `entry.source (string form)` Disposition rows: the legacy strings on the 26 slug-only entries stay in the registry, and the records this repair writes carry neither. Until then, a legacy entry's record that its owner later closes or extends differs from what AC-0019 and AC-0020 derive, and `repair-plan` reports it on each run; that repeat is accepted.

## Assumptions

none
