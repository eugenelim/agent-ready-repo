# Spec: Dispatch reads only headers, and workspace-status keeps only the repair

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105 (D3, the retirement gates and the one retirement record), RFC-0106 (D1, a registration's readers go when its replacement ships; D3, list-and-ask; § Errata, each removal's authority), RFC-0083 (the work-intake migration contracts this spec retires), RFC-0078 (the `workspace_status()` MCP tool), RFC-0055 (errata entries on an Accepted RFC), ADR-0074 (standard-library skill scripts)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** spec:last-registry-entries
- **Contract:** none
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

A maintainer or agent learns what is ready, active or blocked from `work-loop`'s dispatch, which reads only each artifact's own headers and runs with no other skill installed, and an adopter still holding registry entries is refused with a pointer to the repair instead of getting a silent answer. Success is that dispatch's answer on every entry-free repository is byte-identical to what it was, and `workspace-status` answers only `repair-plan` and `repair-apply`.

## What Changes

- **Dispatch.** `work-loop`'s `scripts/dispatch.py` decides from a new header-readiness module in the same directory and loads no `workspace-status`, `close-work` or `work-intake` file. It refuses with `unmigrated_workspace` while `workspace.toml` still holds an entry. With `--captured` it also prints the captured-item listing that the shaping-item guard reads.
- **Vendored copies.** `close-work`'s `cooling.py` and `close_work.py` gain byte-identical copies in `work-loop/scripts/`. The source-authority parser is ported into the readiness module.
- **Readiness bridge.** `navigate-intents`'s pinned finding table copies `work-loop`'s table instead of the engine's.
- **`workspace-status`.** Its CLI keeps `repair-plan` and `repair-apply`. These go:
  - the `status`, `reconcile`, `explain` and `selected-membership` subcommands;
  - `prune` and `retirement-candidates`;
  - the migration forms of `repair-plan` and `repair-apply`, and `repair-rollback`;
  - the prune and retirement modules, the `workspace.toml` template, the `explain` and `reconcile` references, and every engine function the repair does not reach.
- **`[authorization.migration]`.** No code reads it. These are deleted: the four `contracts/jsonschema/work-intake-migration-*.schema.json` files, `contracts/jsonschema/spec-retirement-candidates.schema.json`, their `contracts/README.md` rows, and the migration eval fixture.
- **Refresh.** `work-intake`'s `refresh.py` and its packaged copy validate a normalized intake with their own code, and load no `workspace-status` file.
- **MCP.** `agentbundle`'s `workspace_status()` tool builds `ready`, `active`, `blocked` and `canonical` from a packaged copy of dispatch. Items carry no `ini_slug`, and `shaping` is empty. The `_data/` copies follow: dispatch and the readiness module are added; the engine and prune copies are dropped.
- **Text.** These say where status, queue and repair now live:
  - `workspace-status`'s SKILL.md and `references/mutate.md`;
  - `work-loop`'s SKILL.md (Step 0's orientation and shaping-item guard);
  - `work-intake`'s SKILL.md status route;
  - `navigate-intents`'s SKILL.md queue redirect;
  - `close-work`'s SKILL.md;
  - the `work-loop`, `workspace-status` and `work-intake` evals.
- **Repository tools.** `tools/compare-registry.py` is deleted. The tools that load a `workspace-status` script either run against what remains or are deleted with their tests.
- **Governance and records.**
  - an RFC-0106 errata entry, and a pointer erratum on RFC-0083;
  - the brief: its Spec map, its after-cutover list, and its `navigate-intents` non-goal, which admits the queue redirect;
  - the retirement record's § Equivalence rows and a § Compatibility closure entry;
  - the inventory;
  - this spec's ledger.
- **Release.** `core` at the next patch, `agentbundle` at its next minor, and one changelog fragment.
- **Unchanged:**
  - every `repair-plan` and `repair-apply` result;
  - `workspace.toml` itself, which 9G deletes;
  - `guides/`, `docs/guides/`, `packs/core/JOURNEY.md`, `web/`, the seeds and the upgrade-notes draft, which 9F moves or publishes;
  - `.workspace-prune-protected.toml`;
  - every Shipped spec's body.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: dispatch output | Applicable: `work-loop`, the readiness bridge and the MCP tool parse it | `work-loop` SKILL.md Step 0; the `dispatch.py` module docstring | Platform Core maintainer | AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007 pass | Docstring and SKILL.md name `--captured` and `unmigrated_workspace` |
| Interface compatibility: the `workspace-status` CLI | Applicable: adopters run the repair | `workspace-status` SKILL.md and `references/mutate.md` | Platform Core maintainer | AC-0008, AC-0009, AC-0010, AC-0011 pass | The mode table lists only the two repair rows |
| Interface compatibility: the MCP tool | Applicable: control planes poll `workspace_status()` | the tool description in `packages/agentbundle/agentbundle/workspace_mcp.py` | Platform Core maintainer | AC-0014, AC-0015 pass | The description names no `ini_slug` |
| Decision rationale | Applicable: modes, migration tooling and MCP fields are removed | RFC-0106 § Errata; RFC-0083 § Errata | eugenelim, Approver | AC-0019, AC-0020 pass | Each entry carries owner-approved wording |
| Retirement evidence | Applicable: RFC-0105 D3 gates 3 and 4 | `retirement-record.md` § Equivalence and § Compatibility closure; `inventory.toml` | Platform Core maintainer | AC-0021, AC-0022, AC-0023 pass | The closure entry names this spec and the replay |
| Delivery membership | Applicable: the after-cutover list and a non-goal change | `docs/product/briefs/workspace-registry-retirement-delivery.md` | eugenelim, brief owner | AC-0024 passes | The brief names `repair-only-workspace-status` |
| Verification record | Applicable: approvals and the dispatch replay | `docs/specs/repair-only-workspace-status/notes/verification-ledger.md` | Platform Core maintainer | AC-0007, AC-0025 pass | The ledger holds each approval and the replay |
| Release history | Applicable: `core` and `agentbundle` change | one `docs/product/changelog.d/` fragment; `packs/core/pack.toml`, `.claude-plugin/plugin.json`; `packages/agentbundle/agentbundle/version.py`, `pyproject.toml` | Platform Core maintainer | AC-0026 passes | The fragment names both packages |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.
A syscall, flag, helper name, or exact write order is mechanism that belongs in
the plan's `## Design (LLD)`, not here.

### Always do

- Regenerate the projected and packaged copies with `make build-self`, bump `core` and `agentbundle` once each, and carry `Engine-Change-RFC: 0106` on every commit that edits a file under `packages/agentbundle/`.
- Keep the base assertions of every suite AC-0002 and AC-0011 name; change only how a suite reaches the code it tests.
- Add, re-own or remove a file's inventory row in the same change that adds, re-scopes or deletes the file.

### Ask first

- The wording of both errata entries, the brief text and the § Compatibility closure entry. The owner approves each before it is committed.
- Deleting a file, test or tool that What Changes does not name.
- Any edit to a file outside the surfaces What Changes names.

### Never do

- Change a `repair-plan` or `repair-apply` result, or remove a repair operation type.
- Load, from any skill's script, a file in another skill's directory. Copy it into the skill instead, with a byte pin.
- Edit `workspace.toml`, the seeds, `guides/`, `docs/guides/`, `packs/core/JOURNEY.md`, `web/` or the upgrade-notes draft.
- Change `navigate-intents` beyond its finding-table copy, the parity tests that pin it, and the queue redirect in its SKILL.md.
- Add a dependency, a skill, a top-level directory, or a finding code other than `unmigrated_workspace`.

## Testing Strategy

- **Headers-only dispatch (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006): TDD.** The base dispatch suites are the oracle: their assertions stay, and new cases cover the refusal, the isolation and `--captured`.
- **Dispatch equivalence (AC-0007): manual QA.** A replay runs the base and the new dispatch over each repository the suites plant and over this repository, and records the counts in the ledger.
- **The CLI and the engine (AC-0008, AC-0009, AC-0010, AC-0011, AC-0012): TDD.** The base repair suites are the oracle, with argument-vector cases for each retired subcommand and a static reachability check over the scripts.
- **Copies and the bridge (AC-0013, AC-0017): goal-based.** Byte pins, and the parity tests re-pointed to `work-loop`'s table.
- **MCP and refresh (AC-0014, AC-0015, AC-0016): TDD.** The package's MCP suites with a planted repository, and the `work-intake` normalized-intake suites unchanged.
- **Text, records and release (AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026): goal-based.** A roster check over closed file and phrase lists, the inventory and record check, `lint-brief-coverage.py`, `tools/check-core-release.py` and the changelog checks.

## Acceptance Criteria

**Terms**

- **Base.** Commit `5fe7ca91f`.
- **Base dispatch.** `packs/core/.apm/skills/work-loop/scripts/dispatch.py` and the skill tree it loads, both at the base.
- **Entry.** An element of an array that `workspace.toml` holds under any top-level key other than `authorization`.
- **Entry-free repository.** One with no `workspace.toml`, or with a `workspace.toml` that is a readable regular file the base dispatch accepts and that holds no entry.
- **Dispatch suites.** `packs/core/tests/skills/work-loop/test_dispatch.py`, `test_header_derived_dispatch_replay.py` and `test_work_intake_dispatch.py`.
- **Retired subcommands.** `status`, `reconcile`, `explain`, `selected-membership`, `prune`, `retirement-candidates` and `repair-rollback`.

**Dispatch**

- [ ] **AC-0001.** `dispatch.py` run from a skill tree holding only the `work-loop` skill directory prints, for each repository the dispatch suites plant, the same output as when it runs from the full `core` skill tree.
- [ ] **AC-0002.** Every dispatch-suite test at the base whose planted repository is entry-free passes against the new dispatch with its assertions unchanged.
- [ ] **AC-0003.** For a repository whose `workspace.toml` holds at least one entry, argless dispatch, `--start` and `--resume` each print `decision.action` `refuse`, empty `ready`, `active` and `blocked`, and exactly one finding: code `unmigrated_workspace`, path `workspace.toml`, whatever the specs' headers say.
- [ ] **AC-0004.** A `workspace.toml` that the base dispatch refuses as `invalid_workspace` is refused the same way, with the same output.
- [ ] **AC-0005.** With `--captured`, dispatch's output adds one key, `captured`, equal to the `captured` object that the base `workspace-status status` prints for the same repository; without the flag, the output has exactly the keys the base dispatch prints.
- [ ] **AC-0006.** Every finding dispatch prints has a code in `work-loop`'s finding table and that table's next action. Each code in the table other than `unmigrated_workspace` carries its base engine text, and each code in the table appears in at least one dispatch-suite assertion.
- [ ] **AC-0007.** The ledger holds a replay of the base and the new dispatch over each entry-free repository the dispatch suites plant and over this repository. It covers argless runs and `--start` and `--resume` of each listed spec, with a count of runs compared and a count of differing outputs, which is 0.

**workspace-status**

- [ ] **AC-0008.** `workspace_status.py` with a first argument of `repair-plan` or `repair-apply` behaves as at the base. Any other first argument, or none, exits 2 with nothing on standard output. For each retired subcommand, standard error starts `retired_subcommand: <name>`.
- [ ] **AC-0009.** `repair-plan` given `--migration-selection`, and `repair-apply` given `--migration-selection`, `--operation-id` or `--confirmation-file`, each exits 2 with nothing on standard output and writes no file.
- [ ] **AC-0010.** No file under `packs/core/.apm/skills/` or `packages/agentbundle/agentbundle/` reads an `[authorization.migration]` table or `.workspace-migrations.json`.
- [ ] **AC-0011.** These suites pass with their base assertions unchanged:
  - `test_captured_entry_drop.py`, `test_captured_item_files_repair.py` and `test_depends_on_headers_repair.py`;
  - `test_refresh_policy_move.py`, `test_spec_registration_stop_repair.py` and `test_tracker_entry_drop.py`;
  - every other test under `packs/core/tests/skills/workspace-status/` at the base that runs only `repair-plan` or `repair-apply`.
- [ ] **AC-0012.** Every top-level function and class in `workspace_status.py` and `workspace_status_engine.py` is reached by the static call graph from the `repair-plan` and `repair-apply` entry points. The skill's `scripts/` directory holds no prune or retirement module.

**Copies, refresh and MCP**

- [ ] **AC-0013.** `work-loop/scripts/cooling.py` and `work-loop/scripts/close_work.py` are byte-identical to their `close-work` sources. The readiness module's source-authority parser accepts and refuses each source-authority record in the repository's fixtures and docs exactly as `work-intake`'s `parse_source_authority` does, with the same parsed fields.
- [ ] **AC-0014.** The MCP `workspace_status()` result's `canonical` is the argless output of `agentbundle`'s packaged dispatch for the repository, and `shaping` is `[]`. Its `ready`, `active` and `blocked` hold one item per item of that output, in its order. Each item carries the item's `path`, `slug` and `findings` and the tool's other base fields, apart from `ini_slug`, which no item carries.
- [ ] **AC-0015.** The MCP tool loads dispatch only from `agentbundle`'s `_data/`, and returns that result with `workspace.toml` absent.
- [ ] **AC-0016.** `work-intake`'s `refresh.py` and `_data/work_intake_refresh.py` load no file from the `workspace-status` directory or a `workspace_status*` module. The `work-intake` normalized-intake suites pass with their base assertions unchanged.
- [ ] **AC-0017.** `navigate-intents`'s pinned finding table equals `work-loop`'s finding table, and the parity tests that compared it with the engine's table compare it with `work-loop`'s.

**Text**

- [ ] **AC-0018.** A roster check holds each of these, over closed file and phrase lists:
  - `workspace-status`'s SKILL.md mode table lists only `repair-plan` and `repair-apply`, and its `description` claims no orientation, queue or prune trigger;
  - `work-loop`'s SKILL.md shaping-item guard reads `captured.items` from `dispatch.py --captured`, and Step 0 names no `["ini-NNN"]` orientation field;
  - `work-intake`'s SKILL.md routes status to `navigate-intents` `outstanding` and `work-loop`'s dispatch;
  - `navigate-intents`'s and `close-work`'s SKILL.md route no queue or status question to `workspace-status`;
  - no eval under `packs/core/.apm/skills/` routes a retired subcommand.

**Records and governance**

- [ ] **AC-0019.** RFC-0106 § Errata holds one owner-approved entry, dated in this delivery, that names:
  - the retired subcommands and the migration forms;
  - `[authorization.migration]` and the five deleted schemas;
  - the MCP tool's removed `ini_slug` and empty `shaping`;
  - dispatch's `unmigrated_workspace` refusal.
- [ ] **AC-0020.** RFC-0083 § Errata holds one owner-approved entry that points to the AC-0019 entry for the retired migration contracts.
- [ ] **AC-0021.** `retirement-record.md` § Equivalence holds one row at slice `9` for each of these, each citing the AC-0019 entry:
  - `the workspace-status orientation run`, `the delivery-artifact prune`, `the retirement-candidates report`, `the legacy migration apply and rollback` and `the MCP queue's initiative slug and shaping list`, each an `accepted removal`;
  - `dispatch over unmigrated registry entries`, an `intended change`;
  - `dispatch from headers alone`, `reproduced`.

  The record check passes.
- [ ] **AC-0022.** `retirement-record.md` § Compatibility closure holds an entry that links `../repair-only-workspace-status/spec.md` and names `unmigrated_workspace`, `[authorization.migration]` and the AC-0007 counts.
- [ ] **AC-0023.** `inventory.toml` holds a `docs/specs/repair-only-workspace-status/*` `contract` row at owner `9`, holds no row for a file this spec deletes, and passes the inventory check.
- [ ] **AC-0024.** The brief's Spec map lists `repair-only-workspace-status`. Its after-cutover list names that spec beside the engine-rules move and the `workspace-status` shrink. Its `navigate-intents` non-goal admits the queue redirect. `lint-brief-coverage.py` passes.
- [ ] **AC-0025.** `notes/verification-ledger.md` records eugenelim's approval of both errata entries, the brief text and the closure entry, each with the SHA-256 of the file approved.

**Release**

- [ ] **AC-0026.** `tools/check-core-release.py --base` passes against the merge base with freshly fetched `origin/main`. `agentbundle`'s `version.py` and `pyproject.toml` carry its next minor version. One `docs/product/changelog.d/` fragment names both packages at their new versions and names `unmigrated_workspace` and `repair-plan`.

## Terminal Intent

`code` — move dispatch onto headers alone, shrink `workspace-status` to the repair, retire `[authorization.migration]`, and release `core` and `agentbundle`.

## Follow-ons

- eugenelim: 9F — publish the upgrade notes, adding the retired subcommands, migration tooling and MCP fields, and move the seeds, guides, `JOURNEY.md` and `web/` pages that still route to a retired subcommand.
- eugenelim: 9G — retire `.workspace-prune-protected.toml` and its `tests/AGENTS.md` rule with the closure checklist, since nothing reads it once `prune` is gone.

## Assumptions

- Product: adopters with an unfinished `.workspace-migrations.json` operation are invisible from here. After the upgrade they cannot roll it back, and 9F's upgrade notes are the only notice.
- Product: external pollers of the MCP `workspace_status()` tool that read `ini_slug` are invisible from here. The changelog fragment is their notice.
