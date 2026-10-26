# Plan: Captured items in their own files

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0106 D1 and D3; RFC-0105 D3; RFC-0103 D1; ADR-0053 D9; ADR-0074.
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`: `_parse_preamble_fields`, `_iter_preamble_lines`, `_artifact_metadata`, `_append_lifecycle_findings`, `_dependency_is_satisfied`, `_resolve_header_item`, `build_resolution_index`, `_confined_artifact_path`, `check_shaping_guard`, and `run_canonical_reconciliation`.
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`: the `needs-to-header` plan-and-apply pair (`_build_repair_plan_json`, `_validate_needs_operation`, `_apply_needs_operations`), the analogous operation this repair follows, and `confine_migration_path` with `_migration_file_bytes` for every write.
  - `packs/core/tests/skills/workspace-status/test_depends_on_headers_reader.py`, `test_depends_on_headers_equivalence.py`, and `test_depends_on_headers_repair.py`: the fixture style and the frozen-expectation pattern.
  - `packs/core/.apm/skills/work-intake/scripts/intake_transaction.py`: the shared writer lock `.workspace-repair.lock`.
  - `docs/specs/workspace-retirement/`: the record this slice amends.

## Approach

Freeze first. T1 records, from the engine at commit `ce30822a0`, the outcome of each captured-item case written in today's shape, so the lifecycle and satisfaction rules are compared with a recording rather than with a reading of the code. The reader and the `captured` listing come next, then the switch that reads a registered item's status from its file and refuses the old shape, then the guard. The repair follows, and runs on this repository only after it passes on fixtures and only on a plan the owner has confirmed. The writer text changes land before the migration, so no shipped instruction writes an entry the switch refuses. The riskiest part is the switch: every suite that plants a captured membership outside `docs/product/captured/` starts seeing `unmigrated_captured_item`, about 27 sites across 11 files.

## Constraints

- Standard library only in the engine (ADR-0074). `tomlkit` stays inside `repair-apply`, under the Tier 1 declaration in `packs/core/AGENTS.md`.
- Every read of a captured-item file or a source file goes through the engine's identity-checked reader, `confine_migration_path` with `_migration_file_bytes`, which refuses a link in any segment, requires a regular singly linked file, opens with `O_NOFOLLOW`, and checks identity before and after. The directory listing checks every segment of `docs/product/captured` the same way. `_confined_artifact_path` and `_confined_briefs_path` follow links and are not used for these reads. A record is created with `O_CREAT | O_EXCL | O_NOFOLLOW`. A cooled artifact's body is never opened.
- `make build-self` reprojects the engine and `workspace_status.py` into `packages/agentbundle/agentbundle/_data/`. Packaged copies are never hand-edited.
- An engine-source commit carries `Engine-Change-RFC: 0106`, as `tools/lint-catalogue-curation-guard.py` enforces.
- `core`, `product-strategy`, `product-engineering`, and `architect` each take one patch bump in `pack.toml` and `.claude-plugin/plugin.json`, and each changed skill's eval harness gains or updates a case (`packs/AGENTS.md`).
- Shipped pack text states its rules directly and cites no internal record (`packs/AGENTS.md`).
- The captured-item directory is pinned at `docs/product/captured/`, as `intents/` and `briefs/` are pinned, and is not read from `agentbundle-layout.toml`.
- A change to `run-okr-cascade` is owned jointly with the `product-strategy` pack. That pack has no scoped `AGENTS.md`, so `packs/AGENTS.md` and the root file govern it; T6 rechecks for one before editing.

## Construction tests

- **Live comparison (T7):** `workspace-status status` is captured over the tree the repair reads, with the engine at `ce30822a0` from a `git worktree` under `.context/`, and again after it with this slice's engine. A scratch script applies AC-0035's and AC-0036's comparisons, mapping each migrated old path to its new one, and records the result in `notes/verification-ledger.md`.
- **Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| File grammar surfaces | T6 | `work-intake` SKILL.md and the schema guide name the directory and the fields | AC-0038 passes |
| Adopter repair documentation | T5, T6 | `mutate.md` and `start-or-remember-work.md` describe `captured-to-file` | The text names the command, its confirmation, and its comparison |
| Shaping-item guard | T4 | `work-loop` SKILL.md Step 0 | AC-0040 passes |
| OKR gap contract | T6 | `run-okr-cascade` SKILL.md and `cross-pack-routing.md` | AC-0038 and AC-0039 pass |
| Equivalence record | T8 | `retirement-record.md` § Equivalence rows | The amended `workspace-retirement` check passes |
| Release history | T7 | A changelog fragment and the four version bumps | The changelog gate passes |
| Delivery membership | T7 | The Spec map row and the `workspace.toml` entry | `lint-brief-coverage.py` passes |

## Design (LLD)

### Data & schema

Owned by: T2, T5

```markdown
# Workspace mcp brief queue exposure

- **Status:** Open
- **Kind:** defect
- **Detail:** docs/specs/workspace-mcp/notes/workspace-mcp-brief-queue-exposure.md

## Summary

<the registry entry's summary>
```

- A record written by the repair carries only the fields AC-0019 lists, with the source's dependency lines copied, not moved: the repair never writes a source file, so an interruption can never leave an edge in neither place. The summary sits under its own `## Summary` heading, so it is outside the preamble and can never add or replace a field. A writer may add body sections; the reader reads the preamble only.
- A field appears once. `_parse_preamble_fields` keeps the first value, so the grammar check counts field lines itself through `_iter_preamble_lines`.
- `Detail:` is a pointer to context the item does not own. The reconciliation never reads it; the planner uses it only to compute a migrated membership's second base slug. After migration the source's copied dependency lines are inert, because the source is no longer any membership's path; `mutate.md` tells an adopter they may delete them.

### Interfaces & contracts

Owned by: T2, T4, T5

- `status` gains a top-level `captured` object: `{"items": [...], "findings": [...]}`. It is built from the directory listing and the cooled set only, never from the parsed registry, and it is emitted even when `canonical_failed` holds. `reconcile` and the MCP status tool carry the same object.
- `check_shaping_guard(root, slug, cooled)` replaces the registry form. It returns the routed skill, a refusal carrying the file's finding, or `None`. `work-loop` applies the same rule by matching the slug in `captured.items`: `routes_to` routes, `invalid` or `unreadable` stops, anything else continues. No new subcommand is needed.
- `repair-plan` adds operations of type `captured-to-file` to `automatic_operations`, each carrying `operation_type`, `record_path`, `record_text`, `entry_locator` (collection and entry index), and, for a membership, `source_path`, `source_sha256`, `registry_fingerprint`, `depends_on_items`, and `receipt_items`, or, for a legacy captured entry, `slug`. `_VALID_OPERATION_TYPES` admits it; plan building, `_validate_plan_structure`, and `_apply_operations` dispatch on it as they do for `needs-to-header`. A membership whose entry still carries typed `needs` gets a `needs-to-header` operation and an AC-0021 manual finding in the same plan, so the edges reach the source's header first and a later run copies them.
- `repair-apply` returns `captured_before`, `captured_after`, `header_edges_before`, `header_edges_after`, and `captured_equal`, and exits 1 when `captured_equal` is false.

### Behavior & rules

Owned by: T3

- **Lifecycle reads the record.** For a migrated captured membership, `_artifact_metadata` reads the record, and `_append_lifecycle_findings` applies AC-0007's `Open`/`Closed` rule in place of today's `Draft` rule for non-defect kinds in `backlog.open` and the per-kind terminal set in the shaping queues. A defect's `backlog.closed` rule, `Closed` with `fixed`, `declined`, or `superseded`, is unchanged.
- **Satisfaction is unchanged.** `_TERMINAL_STATUS_BY_KIND`, the defect branch of `_dependency_is_satisfied`, and its cooled branch stay as they are. A non-cooled non-defect captured item never satisfies a dependency, exactly as today, where a non-terminal status blocks and a terminal one is a lifecycle finding that structurally blocks the path. A cooled one is satisfied without a read, as today.
- **The refusal skips three read sites, and only those.** The retirement-candidate scan in `workspace_status_retirement_candidates.py` reads tracked text files for citations, not for a captured item's status or kind, and is unchanged.
- **Read sites.** An unmigrated captured membership is skipped by `_artifact_metadata`, by the identity pass in `canonical_repository_identity` (which calls `_metadata_from_root`), and by `_header_edges_by_path`. Each dependency on its path reports `unsatisfied_dependency` with reason `captured item unmigrated`.
- **Legacy entries.** Legacy captured entries keep `unsupported_legacy`. The registry is not rewritten for them; their record is found by slug.
- **Slugs are fixed by the whole set.** The planner computes every captured item at migration's base slugs in one pass before it emits any operation, and prefixes an unmigrated membership's slug when its base slug collides with any other base slug. A migrated membership contributes its record's slug and its `Detail:` source's base slug, so a membership refused after its twin migrated still collides on the rerun and keeps its prefix.
- **Status conflicts are read from the source.** The planner reads the source's own `Status:` and applies AC-0021's collection rules to it, which are the rules the engine at `ce30822a0` applied, because the switched engine no longer reads an unmigrated file and so reports no such finding itself.

### Failure, edge cases & resilience

Owned by: T5

- Apply order is the records first, then one atomic `workspace.toml` write. An interrupted run leaves records whose bytes the rerun re-derives exactly, because no source has changed; it keeps them and finishes. A record path occupied by anything else refuses its operation.
- A record path whose parent directory is absent is created through the same segment check, re-checked after creation, so a symlinked `docs/product/` or `docs/product/captured/` refuses the operation.
- The writer lock is the shared `.workspace-repair.lock` the intake transaction uses, taken before any precondition check. Agent writers that create records without the lock are caught by the exclusive create, which refuses rather than overwrites.

### Dependencies & integration

Owned by: T2

- The listing and record reads use the engine's identity-checked reader. The blessed `agentbundle.catalogue_tooling.file_safety` helpers live in the `agentbundle` package, which a standalone skill script cannot import (ADR-0074), and `confine_migration_path` with `_migration_file_bytes` is the engine's stdlib equivalent of `read_confined_regular_file`.

## Tasks

### T1: Frozen expectations for the captured-item cases

**Depends on:** none

**Mode:** TDD

**Tests:**
- Criteria: AC-0007, AC-0009, AC-0010, AC-0042.
- `packs/core/tests/skills/workspace-status/test_captured_item_files_equivalence.py` builds one `tmp_path` repository per case in today's shape: a defect note with no status, and one `Closed`, in `backlog.open`; a design note `Draft`, and one `Approved`, in `backlog.open` and in `shaping_queue.backlog`; a closed defect with each resolution, and a defect note `Open`, in `backlog.closed`; a spec depending on the `Draft` design note, on the `Approved` one, and on each closed defect; and a spec depending on a cooled defect with and without a `backlog.closed` membership and on a cooled design note.
- A recorder behind `--record-expectations` writes `fixtures/captured-item-files/expected.json` from the engine at `ce30822a0`, run from a `git worktree` of that commit, holding each case's finding codes and paths and `dispatch_by_path` dispatchability. It is committed on its own.
- Without the flag, the test asserts the old shape still reproduces `expected.json` on the unchanged engine.

**Done when:** `expected.json` is committed from the unchanged engine, and the old-shape test passes.

### T2: The captured-item reader and listing

**Depends on:** T1

**Mode:** TDD

**Tests:**
- Criteria: AC-0001, AC-0002, AC-0003, AC-0004, AC-0041, AC-0005, AC-0006.
- `test_captured_item_files_reader.py` plants one case per AC-0001 rule: each field missing, repeated, and out of set; `Resolution:` on an open defect and missing on a closed one; a `Parent intent:` that is a `spec:` reference; a `Detail:` with a `..` segment; a field hidden in a comment or a fence, which does not count; a field line under `## Summary`, which does not count; and a valid record with every optional field.
- Listing cases: an absent directory; a `README.md` and a `Bad_Name.md`, both ignored; a cooled file made unreadable, listed as cooled with no read; a symlinked `docs/product/captured` and a symlinked `docs/product`; a symlinked entry, a hard-linked entry, a directory named like a record, and an entry swapped for a link between its check and its open, each `unreadable: true`; an invalid entry, `invalid: true`; and the same tree under two different registries, giving equal `captured` objects.

**Done when:** each reader test reds before its rule exists and passes after.

### T3: The switch, the refusal, and satisfaction

**Depends on:** T2

**Mode:** TDD

**Tests:**
- Criteria: AC-0007, AC-0008, AC-0009, AC-0010, AC-0042, AC-0011, AC-0012, AC-0013.
- `test_captured_item_files_equivalence.py` adds the migrated form of each T1 case whose old shape has no lifecycle finding: the record in `docs/product/captured/` with `Open` for open-collection items and `Closed` with the same resolution for closed defects. Each asserts T1's finding codes and dispatchability, including the three cooled cases, with the record made unreadable to show it is not opened. AC-0007's three conflict cases, a `Closed` record in `backlog.open` and in `shaping_queue.backlog` and an `Open` record in `backlog.closed`, each assert `impossible_transition`, matching the T1 finding for the same conflict in today's shape.
- Each old-shape T1 case becomes an `unmigrated_captured_item` assertion with its next action, and a cooled one asserts the hand-written-record next action. A spy over the engine's file opens asserts that no reconciliation opens the unmigrated path, across `_artifact_metadata`, `canonical_repository_identity`, and `_header_edges_by_path`; a planted `Depends on:` line on the unmigrated file contributes no edge. A spec depending on an unmigrated path asserts `unsatisfied_dependency`.
- A membership-kind mismatch, an invalid record, and an unreadable record in `backlog.open` each assert their one finding.
- `navigate-intents`' `_KNOWN_FINDINGS` in `intent_readiness.py` gains `unmigrated_captured_item` and `invalid_captured_item` with the engine's sentences, and `test_readiness_vocabulary_matches_workspace_status` passes.
- The suites the survey found move their captured memberships into `docs/product/captured/` with a record: `tools/test_workspace_status_cli.py`, `tools/test_workspace_status.py`, `packages/agentbundle/tests/test_workspace_mcp_tools.py`, `packs/core/tests/skills/workspace-status/`, `packs/core/tests/skills/work-loop/test_lint_spec_status_deferred.py`, `packs/core/tests/pack/fixtures/work-intake-contracts/`, and the roster suites `test_dependency_scoped_completion_receipts.py`, `test_status_projection_and_context_exclusion.py`, and `test_two_sided_prune_closure_invariant.py`. The eval fixtures `workspace-status/evals/files/target/` and `cooled-path-collision/` move the same way. An assertion that pins the old reading becomes an `unmigrated_captured_item` assertion. The suites and the skills' eval suites pass.

**Done when:** the equivalence suite and every migrated suite pass.

### T4: The shaping-item guard

**Depends on:** T2

**Mode:** TDD

**Tests:**
- Criteria: AC-0014, AC-0015, AC-0040.
- `test_captured_item_files_reader.py` asserts the guard for each shaping type; for a record with no `Type:`; for an invalid and an unreadable record, each refusing; for a cooled record; for a missing file; for `../x` and `Bad_Name`, with a spy asserting no open; and for a registry holding a typed `shaping_queue` entry with the same slug and no record, which does not match.
- `tools/test_workspace_status.py`'s guard cases move to the file form.
- The `work-loop` SKILL.md guard paragraph is rewritten. `tests/roster/test_captured_item_files_instructions.py` asserts AC-0040. The work-loop eval case for the guard moves to a captured-item file.

**Done when:** the guard tests and the instruction test pass.

### T5: The repair

**Depends on:** T3

**Mode:** TDD

**Tests:**
- Criteria: AC-0016, AC-0043, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0030, AC-0031, AC-0032.
- `test_captured_item_files_repair.py` runs `repair-plan` and `repair-apply` over fixture repositories. It asserts:
  - the operation fields, with `repair-plan` leaving every byte outside its plan file unchanged;
  - the slug rule over `verification-ledger.md` twice, `follow-ons.md` three times, `manifest.example.yaml`, a stem that is all punctuation, and a membership whose stem equals a legacy entry's slug;
  - the same slugs on a rerun after the legacy record exists, and after one of two colliding memberships migrated and the other was refused;
  - the record text for a file-backed defect, a design note carrying `Depends on:`, a legacy entry with `intent` and `summary`, a legacy entry with `type = "shape"` and no `kind`, and a closed defect with its `Resolution:`;
  - a summary holding `\n- **Type:** strategy` lines, which stay under `## Summary` and do not route the guard, and a summary holding an escape character, which is a manual finding;
  - one manual finding per AC-0021 case, including an `Approved` design note in `backlog.open` and in `shaping_queue.backlog` and a membership with typed `needs`, whose plan also holds its `needs-to-header` operation;
  - an AC-0043 finding for a legacy `type = "shape"` entry whose slug names a record with no `Type:`;
  - a `canonical_failed` workspace yielding no operation and no finding;
  - a byte comparison of `workspace.toml` outside the changed `path` values, and every source file byte-identical after apply;
  - each AC-0026 refusal: an edited `source_path` with a matching SHA-256, an edited `record_path`, an edited `slug`, an edited `entry_locator`, and an edited `record_text`, each with `plan_id` recomputed; a changed source; a changed registry; and a membership cooled after planning;
  - each AC-0027 refusal: a record path created as a file with other bytes after planning, a hard-linked record holding the planned bytes, a symlinked `docs/product`, and a symlinked record directory;
  - an interrupted apply after the first record write, followed by a clean rerun that writes the same records;
  - `captured_equal` false when a record is edited by hand after the write, and the copied edges keyed by record path on both sides;
  - an oversized slug and a source path with a control character, each echoed as an empty string while the plan file holds it whole, and a record text printed as one escaped JSON string.

**Done when:** the repair tests pass.

### T6: Writers, suggesters, and guides

**Depends on:** T3

**Mode:** goal-based

**Tests:**
- Criteria: AC-0038, AC-0044, AC-0039.
- `tests/roster/test_captured_item_files_instructions.py` asserts AC-0038's closed file list, its directory phrase, and its `toml` path rule, AC-0044's slug-only rule, and AC-0039's two lines.
- `work-intake` SKILL.md's remember route and Terse workspace capture name the record and its fields; `references/lifecycle-index.md` follows. `run-okr-cascade` writes each gap as a record with `Kind: intent` and `Type: strategy` and registers that path. `frame-situation` and `diverge-solutions` suggest registering through `work-intake`, which writes the record with `Detail:` naming the shaping artifact, and their examples follow. `work-loop`'s pre-flight failure capture writes a record and registers its path. The architect guide's design-record entry points at a record. Each changed skill's eval cases follow.
- `mutate.md`, `workspace-status` SKILL.md, `guides/core/reference/workspace-toml-schema.md`, and `guides/core/how-to/start-or-remember-work.md` describe the file, the refusal, and the repair. The anchor hash in `tools/test_workspace_status.py` is updated in the same commit as any SKILL.md §1 to §5 text.
- `test_workspace_retirement_inventory.py` passes, with one `docs/specs/captured-item-files/*` contract row at owner 3.

**Done when:** the instruction test, the anchor test, the eval suites, and the inventory test pass.

### T7: The migration of this repository

**Depends on:** T4, T5, T6

**Mode:** goal-based

**Tests:**
- Criteria: AC-0033, AC-0034, AC-0035, AC-0036.
- Capture `status` and the resolved deferral anchors of `lint-spec-status.py` with the engine at `ce30822a0` as the construction test says. Run `repair-plan`, and ask the owner to confirm the exact plan, including all 77 slugs and the 26 assigned kinds (spec Ask-first). Run `repair-apply`, and record `captured_equal`, the edge sets, and the AC-0035 and AC-0036 comparisons in `notes/verification-ledger.md`.
- Remove the copied `Depends on:` line from `docs/product/design/portfolio-outcome-entry-surfaces.md` by hand, and update `workspace.toml`'s header comment on where a captured item's entry points.
- `make build-self`, the four version bumps, and the changelog fragment. This spec's `workspace.toml` entry and Spec map row are added at approval, before any capture, so both trees hold them. `lint-brief-coverage.py` passes.

**Done when:** `captured_equal` is true, the AC-0035 and AC-0036 comparisons pass, and the ledger records them.

### T8: The equivalence record and the retirement amendment

**Depends on:** T7

**Mode:** goal-based

**Tests:**
- Criteria: AC-0037.
- Amend `docs/specs/workspace-retirement/spec.md` and `plan.md` through the work-loop controlled-amendment path, with the owner's re-approval: its Equivalence Result rule admits `intended change`, and its Authority rule requires an `intended change` row's Authority to meet the same link and section-text rules as an `accepted removal` row, with Case text in place of Fact text. Its check-passes criterion reopens. Extend `test_workspace_retirement_inventory.py` with one planted-violation fixture per changed rule.
- Write the seven Equivalence rows. The three intended-change rows link RFC-0106 D3 and D1, whose section text holds their Case text. Correct the Home cells of `entry.kind`, `entry.slug`, `entry.intent`, and `entry.type` to name `docs/product/captured/<slug>.md` and its fields.

**Done when:** the amended check passes against this repository.

## Rollout

- **Delivery:** one pull request. The reader, the refusal, the repair, the writers, and this repository's migration ship together, so no captured item is refused on a tree that has not been migrated.
- **Adopters:** after upgrading `core`, a captured item registered outside `docs/product/captured/` is reported with `unmigrated_captured_item`, which names `repair-plan`. One confirmed `repair-apply` moves them all. A captured item is never dispatchable, so the refusal stops no build work.
- **Reversal:** revert the pull request. The migration is tracked-file edits, so the revert restores the registry paths and the design note's dependency line and removes the records together.

## Risks

- **The PE suggestions now name a record a user may not create.** `frame-situation` and `diverge-solutions` route registration through `work-intake`, which writes the record; a hand-added entry pointing at the shaping artifact is refused and names the repair, which writes it.
- **Fingerprints move.** Every migrated membership's routing identity changes once. A stale plan file or cached identity is refused by its fingerprint.
- **Assigned slugs read oddly for shared files.** `agentbundle`, `loop-cohort`, and `manifest-example` name a defect by the file it was filed against. The owner sees every slug in the plan, and a later rename is a hand edit of one file and one `path`.

## Changelog
