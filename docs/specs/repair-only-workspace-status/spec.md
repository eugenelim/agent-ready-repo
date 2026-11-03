# Spec: Dispatch reads only headers, and workspace-status keeps only the repair

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-11-02 by eugenelim, spec and plan at `63ed6819e`, after four spec-mode shaping and adversarial review rounds and two security spec-stage rounds, each adjudicated (three adjudications were invalid; one was re-run), with the round-4 repairs accepted unreviewed; records under `.context/reviews/c2bc3c0b-0c0c-44a9-9a99-0028fa5e7927/`. Amended 2026-11-02 under controlled amendment after T9: the Engine-pinning tests term adds `test_dispatch_outside_a_skills_directory` and the Migration forms term adds `repair-plan` given `--yes`, `--operation-id` or `--confirmation-file`, after two amendment review rounds (each adjudicated); re-approved 2026-11-02 by eugenelim at `e90919690`; records under the same directory, `5-*` and `6-*`.
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
- **Readiness bridge.** `navigate-intents`'s pinned finding table, and the parity tests that pin it, copy `work-loop`'s table instead of the engine's.
- **`workspace-status`.** Its CLI keeps `repair-plan` and `repair-apply`. These go:
  - the `status`, `reconcile`, `explain` and `selected-membership` subcommands;
  - `prune` and `retirement-candidates`;
  - the migration forms of `repair-plan` and `repair-apply`, and `repair-rollback`;
  - the prune and retirement modules, the `workspace.toml` template, the `explain` and `reconcile` references, and every engine function the repair does not reach.

  The repair keeps its existing loads of `work-intake`'s `refresh.py` and `close-work`'s `cooling.py`.
- **`[authorization.migration]`.** No code reads it. These are deleted: the four `contracts/jsonschema/work-intake-migration-*.schema.json` files, `contracts/jsonschema/spec-retirement-candidates.schema.json`, their `contracts/README.md` rows, and `work-intake`'s `migration-read-only-plan` routing case with its four `evals/files/routing/migration-*` fixtures and its evaluator path.
- **Work-intake.** `refresh.py` and its packaged copy validate a normalized intake with their own code, and load no `workspace-status` file. The router's status route and its routing-matrix cases name `navigate-intents`.
- **MCP.** `agentbundle`'s `workspace_status()` tool builds `ready`, `active`, `blocked` and `canonical` from a packaged copy of dispatch, keeping the base slug guard and spec filter. Items carry no `ini_slug`, and `shaping` is empty. A non-FSM item's branch is `<type>/<slug>`, from a dispatched item `type:slug`; the legacy `ini_slug/type:slug` form still derives its three-part branch. The `_data/` copies follow: dispatch and the readiness module are added; the engine and prune copies are dropped.
- **Text.** These say where status, queue and repair now live:
  - `workspace-status`'s SKILL.md and `references/mutate.md`;
  - `work-loop`'s SKILL.md (Step 0's orientation and shaping-item guard);
  - `work-intake`'s SKILL.md status route;
  - `navigate-intents`'s SKILL.md queue redirect;
  - `close-work`'s SKILL.md;
  - `new-spec`'s `references/spec-and-plan-contract.md`;
  - the `work-loop`, `workspace-status` and `work-intake` evals;
  - the MCP server's instructions, the `workspace_status` tool description and both `git_branch` descriptions;
  - `packages/agentbundle/README-pypi.md`'s `workspace_status` row and `WORKSPACE_MCP_DISPATCHED_ITEM` text.
- **Tests outside the two skills.** Each suite that loads an engine function this spec deletes, or runs a retired subcommand, either reaches the surviving code with its assertions unchanged, or loses the cases that pinned only the retired behavior. The plan names each suite and its fate.
- **Repository tools.** `tools/compare-registry.py` is deleted. The tools that load a `workspace-status` script either run against what remains or are deleted with their tests.
- **Governance and records.**
  - an RFC-0106 errata entry, and a pointer erratum on RFC-0083;
  - the brief: its Spec map, its after-cutover list, and its `navigate-intents` non-goal, which admits the queue redirect and the finding-table re-point;
  - the retirement record's § Equivalence rows, the evidence of earlier rows whose only cited suite this spec deletes, and a § Compatibility closure entry;
  - the inventory;
  - this spec's ledger.
- **Release.** `core` at the next patch, `agentbundle` at its next minor, and one changelog fragment.
- **Unchanged:**
  - every `repair-plan` and `repair-apply` result, apart from the migration forms;
  - `workspace.toml` itself, which 9G deletes;
  - `guides/`, `docs/guides/`, `packs/core/JOURNEY.md`, `web/`, the seeds and the upgrade-notes draft, which 9F moves or publishes;
  - `packs/core/pack.toml`'s first-value check, `packs/core/README.md`, `DESIGN.md` and `docs/`, and every other pack's skills and manifest, which 9F moves;
  - `.workspace-prune-protected.toml`, apart from the lines this spec's new roster tests need; 9G retires the file;
  - every Shipped spec's body.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: dispatch output | Applicable: `work-loop`, the readiness bridge and the MCP tool parse it | `work-loop` SKILL.md Step 0; the `dispatch.py` module docstring | Platform Core maintainer | AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0027, AC-0030, AC-0031 pass | Docstring and SKILL.md name `--captured` and `unmigrated_workspace` |
| Interface compatibility: the `workspace-status` CLI | Applicable: adopters run the repair | `workspace-status` SKILL.md and `references/mutate.md` | Platform Core maintainer | AC-0008, AC-0009, AC-0010, AC-0011 pass | The mode table lists only the two repair rows |
| Interface compatibility: the MCP tool | Applicable: control planes poll `workspace_status()` and set the dispatched item | the tool description, the server instructions and both `git_branch` descriptions in `packages/agentbundle/agentbundle/workspace_mcp.py`; `packages/agentbundle/README-pypi.md` | Platform Core maintainer | AC-0014, AC-0015, AC-0028, AC-0032 pass | None of them names `ini_slug` as a `workspace_status()` field |
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
- Keep the base assertions of every suite AC-0002, AC-0011 and AC-0016 name, apart from the ones those criteria name as changing; change only how a suite reaches the code it tests.
- Add, re-own or remove a file's inventory row in the same change that adds, re-scopes or deletes the file.

### Ask first

- The wording of both errata entries, the brief text and the § Compatibility closure entry. The owner approves each before it is committed.
- Deleting a file, test or tool that What Changes and the plan do not name.
- Any edit to a file outside the surfaces What Changes and the plan name.

### Never do

- Change a `repair-plan` or `repair-apply` result, other than retiring the migration forms, or remove a repair operation type.
- Add a load, from any skill's script, of a file in another skill's directory. Copy the file into the skill instead, with a byte pin.
- Edit `workspace.toml`, the seeds, `guides/`, `docs/guides/`, `packs/core/JOURNEY.md`, `web/` or the upgrade-notes draft.
- Change `navigate-intents` beyond its finding-table copy, the parity tests that pin it, and the queue redirect in its SKILL.md.
- Add a dependency, a skill, a top-level directory, or a finding code other than `unmigrated_workspace`.

## Testing Strategy

- **Headers-only dispatch (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0027, AC-0030, AC-0031): TDD.** The base dispatch suites are the oracle: their assertions stay, apart from the cases AC-0002 names, and new cases cover the refusal, the isolation, the load failures, the dispatch after a repair and `--captured`.
- **Dispatch equivalence (AC-0007): manual QA.** A replay runs the base and the new dispatch over each repository the suites plant and over this repository, and records the counts in the ledger.
- **The CLI and the engine (AC-0008, AC-0009, AC-0010, AC-0011, AC-0012): TDD.** The base repair suites are the oracle, with argument-vector cases for each retired subcommand and a static reachability check over the scripts.
- **Copies and the bridge (AC-0013, AC-0017): goal-based.** Byte pins, and the parity tests re-pointed to `work-loop`'s table.
- **MCP and work-intake (AC-0014, AC-0015, AC-0016, AC-0028, AC-0029, AC-0032): TDD.** The package's MCP suites with planted repositories and dispatched items, a pin over the MCP texts and the README, the `work-intake` suites unchanged, and the router's status case.
- **Text, records and release (AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026): goal-based.** A roster check over the lists AC-0018 states, the inventory and record check, `lint-brief-coverage.py`, `tools/check-core-release.py` and the changelog checks.

## Acceptance Criteria

**Terms**

- **Base.** Commit `ab4e4b71c`.
- **Base dispatch.** `packs/core/.apm/skills/work-loop/scripts/dispatch.py` and the skill tree it loads, both at the base.
- **Entry.** An element of an array that `workspace.toml` holds under any top-level key other than `authorization`.
- **Entry-free repository.** One with no `workspace.toml`, or with a `workspace.toml` that is a readable regular file the base dispatch accepts and that holds no entry.
- **Dispatch suites.** `packs/core/tests/skills/work-loop/test_dispatch.py`, `test_header_derived_dispatch_replay.py` and `test_work_intake_dispatch.py`.
- **Engine-pinning tests.** `test_missing_engine`, `test_engine_symlinked_out_of_the_tree`, `test_engine_import_raises`, `test_engine_without_the_entry_point`, `test_engine_name_that_is_not_callable`, `test_selector_rule_matches_workspace_status` and `test_dispatch_outside_a_skills_directory`, all in `test_dispatch.py`.
- **Retired subcommands.** `status`, `reconcile`, `explain`, `selected-membership`, `prune`, `retirement-candidates` and `repair-rollback`.
- **Migration forms.** `repair-plan` given `--migration-selection`, `--yes`, `--operation-id` or `--confirmation-file`, and `repair-apply` given `--migration-selection`, `--operation-id` or `--confirmation-file`.
- **Retired tokens.** `workspace-status status`, `workspace-status reconcile`, `workspace-status explain`, `selected-membership`, `retirement-candidates`, `repair-rollback`, `--migration-selection` and `prune --select`.

**Dispatch**

- [ ] **AC-0001.** `dispatch.py` run from a skill tree holding only the `work-loop` skill directory prints, for each repository the dispatch suites plant, the same output as when it runs from the full `core` skill tree.
- [ ] **AC-0002.** Every dispatch-suite test at the base whose planted repository is entry-free, other than the engine-pinning tests, passes against the new dispatch with its assertions unchanged. The selector test asserts, for each of its base inputs, the canonical path the base selector returns or its refusal, as literal expectations.
- [ ] **AC-0027.** When `_header_readiness.py` or `file_safety.py` in dispatch's directory is missing, is a symbolic link resolving outside that directory, fails to import, or lacks a name dispatch calls from it, dispatch exits 2 with nothing on standard output, and standard error starts `engine_unavailable: <that file name>`.
- [ ] **AC-0031.** When `cooling.py` or `close_work.py` in dispatch's directory is missing, is a symbolic link resolving outside that directory, fails to import, or lacks a name the readiness module calls from it, dispatch on a repository with a `docs/lifecycle/` directory prints the base `cooling_state_unavailable` finding and treats no artifact as cooled, and no file outside that directory executes.
- [ ] **AC-0003.** For a repository whose `workspace.toml` holds at least one entry, argless dispatch, `--start` and `--resume` each print `decision.action` `refuse`, empty `ready`, `active` and `blocked`, and exactly one finding: code `unmigrated_workspace`, path `workspace.toml`, whatever the specs' headers say.
- [ ] **AC-0004.** A `workspace.toml` that the base dispatch refuses as `invalid_workspace` is refused the same way, with the same output.
- [ ] **AC-0005.** With `--captured`, dispatch's output adds one key, `captured`, equal to what the base `workspace-status` `_captured_projection` returns for the same repository, recorded as literal expectations, with or without `workspace.toml`. Without the flag, the output has exactly the keys the base dispatch prints.
- [ ] **AC-0006.** Every finding dispatch prints has a code in `work-loop`'s finding table and that table's next action. Each code in the table other than `unmigrated_workspace` carries its base engine text, and each code in the table appears in at least one dispatch-suite assertion.
- [ ] **AC-0007.** The ledger holds a replay of the base and the new dispatch over each entry-free repository the dispatch suites plant and over this repository. It covers argless runs and `--start` and `--resume` of each listed spec, with a count of runs compared and a count of differing outputs, which is 0.

**workspace-status**

- [ ] **AC-0008.** `workspace_status.py` with a first argument of `repair-plan` or `repair-apply`, outside the migration forms, prints the same standard output, writes the same files and exits with the same code as at the base. Any other first argument, or none, exits 2 with nothing on standard output. For each retired subcommand, standard error starts `retired_subcommand: <name>`.
- [ ] **AC-0009.** Each migration form exits 2 with nothing on standard output and writes no file.
- [ ] **AC-0010.** No file under `packs/core/.apm/skills/` or `packages/agentbundle/agentbundle/` reads an `[authorization.migration]` table or `.workspace-migrations.json`.
- [ ] **AC-0011.** These suites pass with their base assertions unchanged:
  - `test_captured_entry_drop.py`, `test_captured_item_files_repair.py` and `test_depends_on_headers_repair.py`;
  - `test_refresh_policy_move.py`, `test_spec_registration_stop_repair.py` and `test_tracker_entry_drop.py`;
  - every other test under `packs/core/tests/skills/workspace-status/` at the base that runs only `repair-plan` or `repair-apply`.

  Two kinds of assertion are exempt. An assertion about dispatch output in the dispatch-comparison tests AC-0030 names is replaced by AC-0030. A test in `test_spec_registration_stop_repair.py` that reaches its entry through a migration form plants that entry directly, as the literal the migration produced, and keeps its other assertions.
- [ ] **AC-0030.** Each dispatch-comparison test runs dispatch after each `repair-apply --yes` it runs. Exactly one of these holds for each run, taken in this order:
  1. when AC-0004 applies, dispatch prints the AC-0004 refusal;
  2. otherwise, while the applied `workspace.toml` still holds an entry, it prints the AC-0003 refusal;
  3. otherwise, it prints output byte-identical to dispatch on the same tree with `workspace.toml` removed.

  The dispatch-comparison tests are:
  - `test_dispatch_output_is_identical_across_apply` in `test_captured_entry_drop.py`;
  - `test_dispatch_output_is_byte_identical_before_and_after_apply` and `test_dispatch_output_is_identical_across_a_held_entrys_second_run` in `test_spec_registration_stop_repair.py`;
  - every test in `test_tracker_entry_drop.py` that ran dispatch at the base.
- [ ] **AC-0012.** Every top-level function and class in `workspace_status.py` and `workspace_status_engine.py` is reached from `workspace_status.py`'s `main` by the static closure. That closure follows each reference by name or attribute to a top-level name of either file, and treats each name `_bind_engine` binds as a reference to the engine name it binds. The skill's `scripts/` directory holds no prune or retirement module.

**Copies, work-intake and MCP**

- [ ] **AC-0013.** `work-loop/scripts/cooling.py` and `work-loop/scripts/close_work.py` are byte-identical to their `close-work` sources. The readiness module's source-authority parser accepts and refuses each source-authority record in the repository's fixtures and docs exactly as `work-intake`'s `parse_source_authority` does, with the same parsed fields.
- [ ] **AC-0014.** The MCP `workspace_status()` result's `canonical` is the argless output of `agentbundle`'s packaged dispatch for the repository, and `shaping` is `[]`. Its `ready`, `active` and `blocked` hold one item per item of that output, in its order, apart from the items the base tool's slug guard, spec filter and pack-presence filter skip. Each item carries the item's `path`, `slug` and `findings` and the tool's other base fields, apart from `ini_slug`, which no item carries.
- [ ] **AC-0015.** The MCP tool loads dispatch only from `agentbundle`'s `_data/`, and returns that result with `workspace.toml` absent.
- [ ] **AC-0028.** A `WORKSPACE_MCP_DISPATCHED_ITEM` value is three-part when a `/` precedes its first `:`, and two-part otherwise. For a two-part `<type>:<slug>`, the expected branch is `<type>/<slug>`, and `git_commit`'s scope equals the base scope for `<ini>/<type>:<slug>` with a safe `<ini>`. A three-part value behaves as at the base. Any of these values gets the base malformed-item handling: no expected branch, no `git_commit` scope, and git writes blocked.
  - one that does not split into a type and a slug;
  - one whose slug fails the base slug guard;
  - one whose type the lifecycle manifest does not know.
- [ ] **AC-0032.** Rule 5 of the server instructions and both `git_branch` descriptions each name `<type>/<slug>` as the branch, and none of them names a three-part `<ini_slug>/<type>/<slug>` branch. `README-pypi.md`'s `WORKSPACE_MCP_DISPATCHED_ITEM` text names `type:slug` as the form to set, and marks any three-part `ini_slug/type:slug` it names as legacy. None of the server instructions, the `workspace_status` tool description, the two `git_branch` descriptions, `README-pypi.md`'s `workspace_status` row or that `WORKSPACE_MCP_DISPATCHED_ITEM` text names `ini_slug` as a `workspace_status()` field. None of them describes `shaping` as anything but an empty list.
- [ ] **AC-0016.** `work-intake`'s `refresh.py` and `_data/work_intake_refresh.py` load no file from the `workspace-status` directory or a `workspace_status*` module. `packs/core/tests/skills/work-intake/test_work_intake.py` and `tests/roster/test_tracker_intake_adapters.py` pass with their base assertions unchanged.
- [ ] **AC-0029.** `work-intake`'s router routes a status request to `navigate-intents`, and the routing matrix's status cases expect `navigate-intents`.
- [ ] **AC-0017.** `navigate-intents`'s pinned finding table equals `work-loop`'s finding table, and the parity tests that compared it with the engine's table compare it with `work-loop`'s.

**Text**

- [ ] **AC-0018.** A roster check holds each of these. It collapses runs of whitespace inside each Markdown file and inside each string value of each JSON file before matching.
  - None of the retired tokens appears in `workspace-status`'s SKILL.md or `references/mutate.md`, in the SKILL.md of `work-loop`, `work-intake`, `navigate-intents`, `close-work`, `intake-intent` or `author-delivery-brief`, in `new-spec`'s `references/spec-and-plan-contract.md`, or in any string value of a JSON file under `packs/core/.apm/skills/*/evals/`.
  - `workspace-status`'s SKILL.md `description` contains none of `orient`, `what's ready`, `session start`, `show the queue` and `prune`.
  - `work-loop`'s SKILL.md contains `dispatch.py --captured`, and `work-intake`'s SKILL.md contains `` Route status directly to `navigate-intents` ``.

**Records and governance**

- [ ] **AC-0019.** RFC-0106 § Errata holds one owner-approved entry, dated in this delivery, that names:
  - the retired subcommands and the migration forms;
  - `[authorization.migration]` and the five deleted schemas;
  - the MCP tool's removed `ini_slug`, its empty `shaping`, its `canonical` object replaced by the dispatch output, and its two-part branch;
  - dispatch's `unmigrated_workspace` refusal.
- [ ] **AC-0020.** RFC-0083 § Errata holds one owner-approved entry that points to the AC-0019 entry for the retired migration contracts.
- [ ] **AC-0021.** `retirement-record.md` § Equivalence holds one row at slice `9` for each of these, each citing the AC-0019 entry:
  - `the workspace-status orientation run`, `the delivery-artifact prune`, `the retirement-candidates report`, `the legacy migration apply and rollback`, `the MCP queue's initiative slug and shaping list` and `the MCP canonical reconciliation object`, each an `accepted removal`;
  - `dispatch over unmigrated registry entries`, an `intended change`;
  - `dispatch from headers alone`, `reproduced`.

  Every earlier row cites at least one tracked file that exists after this change, and the record check passes.
- [ ] **AC-0022.** `retirement-record.md` § Compatibility closure holds an entry that links `../repair-only-workspace-status/spec.md` and names `unmigrated_workspace`, `[authorization.migration]` and the AC-0007 counts.
- [ ] **AC-0023.** `inventory.toml` holds a `docs/specs/repair-only-workspace-status/*` `contract` row at owner `9`, holds no row for a file this spec deletes, and passes the inventory check.
- [ ] **AC-0024.** The brief's Spec map lists `repair-only-workspace-status`. Its after-cutover list names that spec beside the engine-rules move and the `workspace-status` shrink. Its `navigate-intents` non-goal admits the queue redirect and pinning the finding table and its parity tests against `work-loop`'s table. `lint-brief-coverage.py` passes.
- [ ] **AC-0025.** `notes/verification-ledger.md` records each of these, with the SHA-256 of the file approved where one is approved:
  - eugenelim's approval of both errata entries, the brief text and the closure entry;
  - eugenelim's agreement, as owner of the readiness hand-over, to the finding-table re-point.

**Release**

- [ ] **AC-0026.** `tools/check-core-release.py --base` passes against the merge base with freshly fetched `origin/main`. `agentbundle`'s `version.py` and `pyproject.toml` carry the next minor above the version on freshly fetched `origin/main`. One `docs/product/changelog.d/` fragment names both packages at their new versions, and names `unmigrated_workspace`, `repair-plan`, the `repair-rollback` removal and the dropped `ini_slug`.

## Terminal Intent

`code` — move dispatch onto headers alone, shrink `workspace-status` to the repair, retire `[authorization.migration]`, and release `core` and `agentbundle`.

## Follow-ons

- eugenelim: 9F — publish the upgrade notes, adding the retired subcommands, migration tooling and MCP fields. Move the seeds, guides, `JOURNEY.md`, `web/` pages, `packs/core/pack.toml`'s first-value check, `packs/core/README.md`, `DESIGN.md` and `docs/index.md`, and the other packs' skills and manifests that still route to a retired subcommand: `desk-research-project-status`, `experience-status`, `run-okr-cascade`'s cross-pack routing, `new-rfc` and `packs/repo-governance/pack.toml`.
- eugenelim, as `navigate-intents` owner: the readiness bridge maps a dispatch refusal with `unmigrated_workspace` to `wrong_schema`, because the code is not in `intent_readiness.py`'s `_WORKSPACE_FAILURE_CODES`; mapping it to `bad_workspace` is outside this spec's `navigate-intents` boundary (owner decision, 2026-11-02).
- eugenelim: 9G — retire `.workspace-prune-protected.toml` and its `tests/AGENTS.md` rule with the closure checklist, since nothing reads it once `prune` is gone.

## Assumptions

- Product: adopters with an unfinished `.workspace-migrations.json` operation are invisible from here. After the upgrade they cannot roll it back, and 9F's upgrade notes are the only notice.
- Product: external control planes that read `ini_slug` from `workspace_status()`, or set a three-part dispatched item, are invisible from here. The changelog fragment names the change; the legacy dispatched-item form keeps working.
