# Spec: Header-derived dispatch and its replay

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-29 by eugenelim, spec and plan, after four spec-mode shaping and adversarial review rounds, each adjudicated, with the round-4 fixes accepted unreviewed; review records under `.context/reviews/header-derived-dispatch-spec-r1/` to `-r4/`. Re-approved 2026-10-29 by eugenelim after the pre-EXECUTE adversarial and secure-design reviews tightened confinement, the drop rule, named refusals and the engine load; records under `.context/reviews/ea6a3fd9-0b6d-4b55-841e-fc58e265b40c/`.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0106 (D1, header-derived readiness replaces dispatch and resume from spec entries, and the `unregistered_work` refusal is retired; D3, several ready specs are listed and the user is asked), RFC-0105 (D3, the behavioral-equivalence gate and accepted authority for each removal), ADR-0110 (a cooled child's parent scope is declared, and an undeclared one fails closed), RFC-0096 (§ 7, a cooled artifact's body is not loaded by orientation), RFC-0055 (errata entries on an Accepted RFC), ADR-0074 (standard-library skill scripts)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** spec:depends-on-headers, spec:registry-comparison, spec:next-item-suggestions-removal, spec:intent-brief-registration-stop
- **Contract:** `contracts/jsonschema/delivery-lifecycle-record.schema.json` gains an optional `parent` property within `delivery-lifecycle-record.v1`. The dispatch result is a skill-internal JSON output, read in `core` only.
- **Shape:** service

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

A read-only `work-loop` dispatch command decides which specs are ready and which are active. It reads each spec's own `Status:`, its sibling `plan.md`, its `Depends on:` targets, and a cooled spec's lifecycle record. From `workspace.toml` it drops only the repo-origin spec entries with empty `needs`, which are the entries the registration stop removes, and passes every other entry to the engine unchanged so it is judged as today. It never picks between several candidates. Success means a frozen-corpus replay of argless and named starts and resumes, in which every spec whose ready, active or dispatch result differs from `workspace-status`'s `canonical.ready` or `canonical.active` carries an accepted removal entry. That replay is the evidence the [spec registration stop](../../product/briefs/workspace-registry-retirement-delivery.md#delivery-slices) needs before any writer stops.

## What Changes

- **Dispatch command.** A new read-only `packs/core/.apm/skills/work-loop/scripts/dispatch.py` prints the ready, active and blocked specs, their findings, and one decision for an argless, named-start or named-resume invocation. It loads the `workspace-status` engine through a confined path and runs the engine's canonical reconciliation over a registry it builds in memory: the real registry without its repo-origin spec entries that have empty `needs`, plus one membership per remaining spec from its own headers. No engine file changes.
- **Cooling record.** The lifecycle record schema and `close-work`'s `cooling.py` gain an optional `parent` property. When `cooling.enrol` enrols a spec, it fills `parent` from the spec's `Brief:` header. `dispatch.py` reads a cooled spec's parent from that property.
- **Replay.** A replay suite and its frozen fixtures live under `packs/core/tests/skills/work-loop/`. A read-only `tools/replay-dispatch.py` lists live differences. The ledger at `docs/specs/header-derived-dispatch/notes/verification-ledger.md` holds the live run.
- **Records.** RFC-0106 § Errata gains an entry for each accepted removal the replay finds. The retirement record gains its slice-8 § Equivalence rows. The inventory and the brief's Spec map gain their rows.
- **Unchanged:**
  - `work-loop`'s SKILL.md, which still dispatches from `workspace-status`;
  - every writer of spec entries, and `close-work`'s spec moves;
  - every `workspace-status` file and output, including `unregistered_work`;
  - the `navigate-intents` readiness bridge;
  - ADR-0110, whose first revisit trigger this release's `enrol` change meets, and every contract except the RFC-0106 errata.

  The spec registration stop changes all of these in one release, gated on this spec's replay.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: the dispatch result and its decision | Applicable: `work-loop` and the readiness bridge read it in the stop's release | `dispatch.py`'s module docstring and `--help` | Platform Core maintainer | AC-0001 to AC-0012 pass | The docstring names each output key, each decision, and each exit code |
| Interface compatibility: the lifecycle record's `parent` | Applicable: a published schema that adopters' records follow | `contracts/jsonschema/delivery-lifecycle-record.schema.json`, `cooling.py`, `docs/lifecycle/README.md`, and `close-work`'s SKILL.md cooling-seam paragraph | Platform Core maintainer | AC-0013, AC-0014, AC-0015 and AC-0025 pass | Each names `parent`, its two value forms, and the absent case |
| Decision rationale: equivalence evidence and the authority for each removal | Applicable: RFC-0105 D3 gate 3, and FEAT-0034's second validation hook | `docs/specs/workspace-retirement/retirement-record.md` § Equivalence; `docs/rfc/0106-stop-registering-derivable-work.md` § Errata | Platform Core maintainer; eugenelim as RFC-0106 Approver | AC-0020 to AC-0022 pass | Each AC-0018 case has a row, and each removal row's authority is an owner-approved errata entry |
| Verification record: the live replay and the owner's approvals | Applicable: the hook's frozen corpus includes this repository | `docs/specs/header-derived-dispatch/notes/verification-ledger.md` | Platform Core maintainer | AC-0019 and AC-0022 pass | The ledger holds the run, its classification, and every approval |
| Current product truth: which consumers depend on the registry | Applicable: new files name `workspace.toml` | `docs/specs/workspace-retirement/inventory.toml` | Platform Core maintainer | AC-0023 and the inventory check pass | Each new file that names the registry has a row |
| Release history | Applicable: shipped `core` content changes, including `close-work`'s enrolment | a `docs/product/changelog.d/` fragment; `core`'s `pack.toml` and `.claude-plugin/plugin.json` at one new patch version | Platform Core maintainer | The changelog and version gates pass | The fragment names the dispatch command and the `parent` field |
| Delivery membership | Applicable: the brief's coverage map | The brief's Spec map row and this spec's `workspace.toml` entry | `author-delivery-brief` | `lint-brief-coverage.py` lists this spec under the brief | The coverage lint passes |

User documentation is not applicable: no user-facing dispatch behavior changes until the registration stop, which documents the new dispatch.

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Record every base outcome from a `git worktree` of commit `95a8cc985`, so its sibling modules are that commit's, and never re-record a frozen fixture.
- Classify every replay difference by case, spec path and field before writing its row, and stop for the owner on any difference that no accepted authority names.
- Regenerate the packaged and projected copies with `make build-self`, bump `core`'s version once, and carry the `Engine-Change-RFC: 0106` trailer on every commit that edits a file under `packages/agentbundle/`.

### Ask first

- The wording of each RFC-0106 § Errata entry AC-0022 needs. The owner approves each before it is committed.
- The live replay's classified difference list (AC-0019). The owner approves it in the ledger.
- Any new finding code, or any change to a finding code's meaning.

### Never do

- Change `work-loop`'s SKILL.md dispatch instructions, any spec-entry writer, `close-work`'s spec moves, any file under `packs/core/.apm/skills/workspace-status/`, or any `navigate-intents` file.
- Read a `workspace.toml` fact in `dispatch.py` other than to build the header registry and AC-0010's refusal, or open a cooled spec's body.
- Reimplement inside `dispatch.py` a rule that `workspace_status_engine.py` owns. The ready, active and blocked projection is `dispatch.py`'s own, and AC-0002 and AC-0003 state it.
- Add a dependency, a skill, a module boundary, or a top-level directory, or import across skills other than by loading a module by confined path.

## Testing Strategy

- **The dispatch result, the decision and the refusals (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012): TDD.** The command is a function of a planted repository tree, so one planted spec per rule turns its test red before the rule exists.
- **The lifecycle record field (AC-0013, AC-0014, AC-0015, AC-0025): TDD.** Each value form, and each refused one, is a validation result over a planted payload.
- **`workspace-status` unchanged (AC-0016, AC-0017): goal-based.** The frozen fixtures, the existing suites, and `git diff` over the skill directory.
- **The case replay (AC-0018): TDD with frozen fixtures.** Base outcomes are recorded once, and the suite fails on any difference that its classification table does not name.
- **The live replay (AC-0019): manual QA.** Both sides run over the same snapshot, and the owner judges the classified list. No rule written in advance can say which differences on real data are acceptable.
- **Records (AC-0020, AC-0021, AC-0022, AC-0023, AC-0024): goal-based.** The `workspace-retirement` check, the inventory check, the coverage lint, and a read of the ledger's approval records.

## Acceptance Criteria

Terms used below:

- **Base engine.** `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` and its sibling modules, at commit `95a8cc985`.
- **Base result.** The `canonical` object `workspace-status reconcile` prints at `95a8cc985` for a tree and its `workspace.toml`.
- **Dependency item**, **cooled**, and **canonical membership** have the meanings the [`depends-on-headers`](../depends-on-headers/spec.md) spec's Acceptance Criteria give them. **Child scope** has the meaning [ADR-0110](../../adr/0110-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md) gives it.
- **Spec file.** `docs/specs/<slug>/spec.md` under the root, for each entry `<slug>` of `docs/specs/` whose path `docs/specs/<slug>/spec.md` the engine's `_is_canonical_spec_artifact_path` accepts, where `docs/specs/<slug>` is a real directory and not a symbolic link, resolving inside the resolved `docs/specs/`, and `spec.md` is a regular file and not a symbolic link. An entry whose name that function refuses, such as `README.md`, is not read and gives no finding. Each accepted entry is checked on its own with work-loop's `file_safety.validate_confined_directory`, so a link-like or non-directory entry fails only itself. When `docs/` or `docs/specs/` is absent, meaning `lstat` finds no entry at that path, there are no spec files and no finding. When either has an entry but is not a real directory strictly inside the resolved `--root`, as `file_safety.validate_confined_directory` decides, or when a validated `docs/specs/` cannot be listed, there are no spec files, nothing under it is read, and `findings` holds one `invalid_artifact_path` finding with path `docs/specs`. A dangling symbolic link is not absent.
- **Status word** and **declared parent.** The `status` and `parent` that the engine's `_metadata_from_root` returns for a `kind = "spec"` entry at a spec file's path. They are read only for a spec file that no lifecycle record cools, and never for a cooled one.
- **Kept entry.** Every entry of the root's `workspace.toml` except a table whose `kind` is exactly `"spec"`, whose `source` is a table with `mode` exactly `"repo-origin"`, and whose `needs` is present as an array of length zero. A kept entry keeps its initiative, its initiative's fields, its collection and its own fields exactly as the file holds them.
- **Header registry.** The in-memory registry `dispatch.py` builds. It holds every kept entry, and one added initiative whose status is `active` under a slug no kept initiative uses. That added initiative holds only these memberships, each for a path that no kept entry names. A kept entry names a path when its `path` field equals it, or when the engine's `_legacy_canonical_alias` maps that kept entry onto it. Each membership has `kind = "spec"`, `source.mode = "repo-origin"` and `needs = []`:
  - one per spec file that no lifecycle record cools, whose status word is `Approved`, `Implementing` or `Shipped`. It sits in `work.queue`, `work.active` or `work.shipped` respectively, with its declared parent as `source.parent`;
  - one per spec locator a lifecycle record cools, in `work.shipped`. It carries the record's `parent` as `source.parent` when the record has one, and no `source.parent` otherwise.

  With no `workspace.toml`, there are no kept entries. The file is read once, through work-loop's `file_safety.read_confined_regular_file` with `max_bytes` of 8 MiB (8,388,608 bytes).
- **Header result.** The evaluations and findings of the loaded engine's `run_canonical_reconciliation` over the header registry, run with the root and the cooled set the engine resolves for the root, together with the cooling findings that resolution gives.
- **Dispatch result.** For a spec file: whether its path is in `ready`, whether it is in `active`, and the decision for each of four invocation shapes, which are argless start, argless resume, `--start` naming it, and `--resume` naming it. A decision is compared on its `action`, `path` and `candidates`.

**The dispatch result**

- [ ] **AC-0001.** `dispatch.py --root <root>` exits `0` and prints one JSON object. Its keys are `schema_version`, `ready`, `active`, `blocked`, `findings` and `decision`. Each `ready`, `active` and `blocked` item carries `path`, `slug`, `status` and `findings`. Each finding carries `code`, `path`, `dispatchable` and `next_action`. `decision` carries `action`, one of `start`, `resume`, `ask`, `none` and `refuse`; `path`, a spec path or `null`; `candidates`, a list that is empty unless `action` is `ask`; and `findings`, a list that is empty unless `action` is `refuse`, and otherwise holds the findings AC-0009 or AC-0010 names. Each list is sorted by `path`.
- [ ] **AC-0002.** Unless AC-0010 refuses the run, `ready` holds exactly the paths of the header result's evaluations whose kind is `spec`, whose collection is `work.queue`, and which are dispatchable. `active` holds exactly the paths of those whose kind is `spec`, whose collection is `work.active`, and which have no finding.
- [ ] **AC-0003.** `blocked` holds each header-result evaluation in `work.queue` or `work.active` whose path is in neither `ready` nor `active`, with that evaluation's findings. No other spec is in `blocked`.
- [ ] **AC-0004.** `findings` holds each header-result finding that belongs to no `blocked` item, including every `cooled_child_scope_unknown` and cooling-resolution finding, and each finding AC-0010 or AC-0011 adds. Output objects carry only the keys AC-0001 lists, so neither the added initiative nor any synthesized `summary` reaches the output.
- [ ] **AC-0005.** Except for an item whose path a kept entry names, no `ready`, `active` or `blocked` item's findings carry `unregistered_work`, `duplicate_membership`, `unsupported_legacy`, `configuration_mismatch`, `impossible_transition` or `provenance_mismatch`.
- [ ] **AC-0006.** For one tree, the output is byte-identical whatever entries its `workspace.toml` holds that are not kept entries, in whatever collections and order, including none. With a `workspace.toml` that holds only such entries, the output is byte-identical to the output with no `workspace.toml`. A spec entry whose `needs` is missing or not an array is a kept entry.
- [ ] **AC-0007.** A run writes nothing. The set of paths under the root, and each file's bytes and modification time, are the same afterwards.

**The decision**

- [ ] **AC-0008.** Unless AC-0010 refuses the run, with no selector:
  - exactly one `active` item gives `resume` with its path;
  - more than one gives `ask` with every `active` path as `candidates`;
  - no `active` item and exactly one `ready` item gives `start` with its path;
  - no `active` item and more than one `ready` item gives `ask` with every `ready` path as `candidates`;
  - otherwise the decision is `none`.

  For one tree, the decision is the same whatever the discovery order and modification times of the spec directories.
- [ ] **AC-0009.** `--start <spec>` gives `start` when the spec's path is in `ready`, and `--resume <spec>` gives `resume` when it is in `active`. Every other named invocation gives `refuse` with at least one finding, each with its `next_action`, chosen by the first rule that applies:
  1. AC-0010 refuses the run: that run's findings.
  2. The spec's path is in `blocked` with at least one finding: its `blocked` findings.
  3. A kept entry names the path: the findings the engine gives for that entry, from its header-result evaluation or, when it has none, from parsing it, such as `unsupported_legacy` or `invalid_entry`. When there are none, `impossible_transition`.
  4. A lifecycle record cools the spec: `impossible_transition`, decided from the record alone.
  5. The path names a `docs/specs/` entry that `_is_canonical_spec_artifact_path` accepts but that fails another spec-file condition: `invalid_artifact_path`.
  6. Nothing exists at the path: `missing_artifact`.
  7. AC-0011 gives the spec an `unreadable_artifact` finding: that finding.
  8. `--start` on a spec whose status word is `Implementing` or `Shipped`, or `--resume` on one whose status word is not `Implementing`: `impossible_transition`.
  9. Otherwise: `unapproved_spec`.

  A selector in no form the engine's spec selector accepts gives exit `2` and an `invalid_selector` message on standard error.

**The refusals**

- [ ] **AC-0010.** When the root's `workspace.toml` exists and is a symbolic link, not a regular file, a file with more than one link, larger than 8 MiB, unreadable, or not valid TOML, or when every `ini-NNN` slug is used by a kept initiative, `ready`, `active` and `blocked` are empty, the decision is `refuse`, and `findings` holds one `invalid_workspace` finding with path `workspace.toml` and its `next_action`.
- [ ] **AC-0011.** Each `docs/specs/` entry whose `docs/specs/<name>/spec.md` path `_is_canonical_spec_artifact_path` accepts, but which fails another spec-file condition, gives one `invalid_artifact_path` finding in `findings` with that path, and nothing else is read from it. Each spec file that no lifecycle record cools and no kept entry names, and that `_metadata_from_root` reports as not readable, gives one `unreadable_artifact` finding in `findings` with its path.
- [ ] **AC-0012.** `dispatch.py` resolves its own path and loads the engine from `workspace-status/scripts/workspace_status_engine.py` under the resolved skills directory that holds it, only when its own resolved parent is named `scripts`, that skills directory is named `skills`, and the engine path resolves to a regular file inside that skills directory. It loads the engine, and work-loop's `file_safety` beside `dispatch.py` under the same resolved-path and confinement rule, each under a unique module name without changing `sys.path`. When any of those conditions fails, either import raises, or a loaded module lacks a callable `dispatch.py` uses, it exits `2` with an `engine_unavailable` message on standard error and prints nothing on standard output.

**The lifecycle record**

- [ ] **AC-0013.** The schema's `properties` gains `parent`, whose value is the string `none` or one matching `^docs/product/briefs/[a-z0-9][a-z0-9-]{0,127}\.md$`. The schema stays `delivery-lifecycle-record.v1` and keeps `additionalProperties: false` and its `required` list. `cooling.py`'s `validate_payload` accepts exactly the payloads the schema accepts for `parent`: absent, or either form. It refuses any other value with the result code it gives any other invalid field.
- [ ] **AC-0014.** `cooling.enrol`, given a record whose `locator` is a spec file and which carries no `parent`, writes the record with `parent` taken from that spec's `Brief:` header, read before the spec cools:
  - `brief:<slug>`, or a repository path naming `docs/product/briefs/<slug>.md`, gives that path when it is a brief file, as ADR-0110's 2026-10-27 erratum defines one, and AC-0013's pattern accepts it;
  - a readable spec whose `Brief:` header is `none` or empty, or which has no `Brief:` header, gives `none`;
  - anything else gives no `parent`. This includes a missing, unreadable, non-regular or out-of-root spec file, and a value naming no brief file. Child scope then stays unknown, failing closed.

  A record whose `locator` is not a spec file is written as given.
- [ ] **AC-0015.** Every record payload that `tests/roster/test_thirty_day_cooling_and_retirement.py` and `tests/roster/test_cooling_scope_closure.py` build validates and verifies as it does at `95a8cc985`. The first file is unchanged. In the second, only `test_ac23_pinned_files_are_byte_unchanged` changes: it re-pins the digests of `cooling.py` and the schema under a dated comment that names this spec, and it keeps every other pin.
- [ ] **AC-0025.** A record that carries `parent` keeps it, with the same value, through `parse_record_bytes`, `load_record`, `canonical_bytes`, `record_rename`, `update_record`, `review`, `review_exception` and `reclassify_record`. Each of those accepts that record wherever it accepts the same record without `parent`.

**`workspace-status` unchanged**

- [ ] **AC-0016.** No file under `packs/core/.apm/skills/workspace-status/` changes, and these fixtures are byte-identical to their state at `95a8cc985`:
  - `packs/core/tests/skills/workspace-status/fixtures/depends-on-headers/expected.json`;
  - `packs/core/tests/skills/workspace-status/fixtures/depends-on-headers/expected-cooled-brief.json`;
  - `packs/core/tests/skills/workspace-status/fixtures/captured-item-files/expected.json`.
- [ ] **AC-0017.** Every `packs/core/tests/skills/workspace-status/` suite, `tools/test_workspace_status.py`, `tests/roster/test_thirty_day_cooling_and_retirement.py` and `tests/roster/test_cooling_scope_closure.py` pass.

**The replay**

- [ ] **AC-0018.** `packs/core/tests/skills/work-loop/test_header_derived_dispatch_replay.py` builds one repository per case. Each case's spec memberships are registered as the base engine needs them. The unregistered cases keep a `workspace.toml` that omits only that spec's entry. For every spec file in every case, the suite compares two things:
  - the base result's ready and active membership and the base decision for each invocation shape, frozen once in `packs/core/tests/skills/work-loop/fixtures/header-derived-dispatch/expected.json`;
  - `dispatch.py`'s dispatch result over the same tree.

  The base decision follows `work-loop`'s SKILL.md lines 168–195 at `95a8cc985`, every branch included. The suite holds a classification table keyed by case, spec path and field, giving the expected base and header values and either `reproduced` or `accepted removal` with an authority. Any difference that the table does not name with those exact values fails. The set of built cases equals the set of `expected.json` keys, and every table entry is used.

  The cases cover at least these groups:
  - **Dependencies:** each case of `test_depends_on_headers_equivalence.py`'s `CASES`, the cooled child with a declared parent, the cooled child with none, the cooled child whose record predates `parent`, and a named start and resume of a cooled spec.
  - **Registry-settled dependencies:** a defect settled by a `backlog.closed` membership, a target whose membership has findings, and a dependency whose kind differs from its target's membership.
  - **Fail-closed and provenance findings:** `provenance_mismatch`, `provenance_reference`, `invalid_source_authority`, `missing_plan`, `unreadable_artifact` for both a registered and an unregistered unreadable spec, `unapproved_spec`, `missing_artifact`, `invalid_artifact_path`, `impossible_transition`, `duplicate_membership`, `unsupported_legacy`, and `configuration_mismatch`.
  - **Status and registration:** a bare `**Status:**` spec, a symbolic-link `spec.md`, a symbolic-link spec directory aliasing another spec, a legacy `spec/<slug>` entry and a legacy `{slug = ...}` entry each aliasing an Approved spec, and a spec entry whose `needs` is not an array, with a named start of each asserting its finding code, a symbolic-link entry `docs/specs/linked` beside a ready spec, asserting its single `invalid_artifact_path` while the sibling stays in `ready`, a symbolic-link `docs/specs/README.md` that gives no finding, a provenance-valid tracker-origin spec the base dispatches, a provenance-invalid one, the unregistered Approved spec, the unregistered Implementing spec, and a spec under an inactive initiative.
  - **Selection and refusals:** several ready specs, several active specs, an unmigrated `needs` entry beside an otherwise-ready spec, an unmigrated captured-item entry beside an otherwise-ready spec, and a tracker-origin spec under an inactive initiative.
- [ ] **AC-0019.** The ledger holds one run of `tools/replay-dispatch.py` over a `git worktree` of `95a8cc985`. It records:
  - the base result's `canonical.ready` and `canonical.active`, and `dispatch.py`'s `ready` and `active`;
  - the `workspace.toml` SHA-256 and the number of lifecycle records;
  - every spec whose dispatch result differs, each assigned by hand to an AC-0018 case and class;
  - the owner's recorded approval of that list.

  When the snapshot holds a lifecycle record, the ledger also records a second run over a scratch copy in which each cooled spec entry's `source.parent` is copied into its record's `parent`.

**Governance and records**

- [ ] **AC-0020.** `docs/specs/workspace-retirement/retirement-record.md` § Equivalence holds one slice-8 row for each AC-0018 case. A row's Case cell is the case's name. Its Result is `accepted removal` when any of the case's classification entries is, and `reproduced` otherwise. An `accepted removal` row's Authority covers every removal entry in its case. Each row meets the row rules the [`workspace-retirement`](../workspace-retirement/spec.md) spec sets for § Equivalence.
- [ ] **AC-0021.** The rows for the unregistered Approved spec and the unregistered Implementing spec are `accepted removal`, with Authority RFC-0106 D1. The row for several ready specs is `accepted removal`, with Authority RFC-0106 D3.
- [ ] **AC-0022.** Each other `accepted removal` row's Authority is an RFC-0106 § Errata entry. That entry is dated on or after 2026-10-28 and names the row's case. For each such entry, the ledger holds its case, the owner's approval, and the approval date, which is no later than the date of the commit that adds the entry.
- [ ] **AC-0023.** Each file this change adds that names `workspace.toml`, `workspace-status` or `workspace_status` has a row in `docs/specs/workspace-retirement/inventory.toml`. This spec's directory has one `docs/specs/header-derived-dispatch/*` `contract` row at owner `8`, and the inventory check passes.
- [ ] **AC-0024.** The brief's Spec map holds `header-derived-dispatch`, and `lint-brief-coverage.py` passes.

## Follow-ons

- The spec registration stop, the next spec under the brief's slice 8, depends on this spec. Its scope:
  - switch `work-loop`'s argless and named dispatch to `dispatch.py`, with list-and-ask;
  - remove `unregistered_work`;
  - re-point the readiness bridge to `dispatch.py`'s output;
  - stop every spec-entry writer and `close-work`'s spec moves;
  - copy each cooled spec entry's `source.parent` into its record, then remove the repo-origin spec entries with a repair step, keeping tracker-origin spec entries until slice 9;
  - amend RFC-0064 D4 and its writer rows, `docs/product/AGENTS.md`'s coverage sentence, FEAT-0005, ADR-0110 (whose first revisit trigger this spec meets) and the other owner-8 contracts in that release.

  The registration stop runs only if AC-0019 is approved and `tools/compare-registry.py` finds no failing difference.
- The brief's slice 9 moves whatever engine rules `dispatch.py` still needs into `work-loop`, as it shrinks `workspace-status` to the repair. It also gives tracker-origin specs a header home and ends their registration.

## Assumptions

none
