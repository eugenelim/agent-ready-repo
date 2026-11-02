# Plan: Dispatch reads only headers, and workspace-status keeps only the repair

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0106 D1, D3 and § Errata; RFC-0105 D3; RFC-0083 (the migration contracts); RFC-0078 (the MCP tool); RFC-0055; ADR-0074.
  - `packs/core/.apm/skills/work-loop/scripts/dispatch.py`: the engine names it loads (`_ENGINE_NAMES`, line 67), the workspace read (line 227), and the run (line 337).
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`: the code dispatch reaches at the base is `run_canonical_reconciliation` (line 4734), `evaluate_dispatch` (4583), `_dependency_is_satisfied` (3012), the header reader (3675-3881), the captured-item reader (3462-3563), `_metadata_from_root` (2377), `_resolve_cooled_state` (2273), and `_FINDING_NEXT_ACTIONS` (101).
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`: `_SUBCOMMANDS` (line 203), `main` (around 5840-6750), the migration section (4900-5800), and `_captured_projection`.
  - `packs/core/.apm/skills/work-intake/scripts/refresh.py`: `parse_source_authority` (line 556) and `_workspace_status_callable` (line 1779).
  - `packages/agentbundle/agentbundle/workspace_mcp.py`: `_canonical_status_projection` (line 1170), `_WorkspaceStatusTool` (1230), and the tool description (2346). `packages/agentbundle/agentbundle/build/self_host.py` `_runtime_projections` (line 94).
  - Precedent for a byte-pinned copy: `tests/roster/test_navigate_decisions_file_safety_mirror.py`. Precedent for the errata, ledger and closure entry: `docs/specs/last-registry-entries/`.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open.
> Execution observations belong in `notes/verification-ledger.md`.

## Approach

Dispatch moves first, because the shrink cannot delete engine code that dispatch still loads.

1. The governance texts land first, as controller commits: the errata entries and the brief amendment authorize every later edit to `navigate-intents` and every deletion.
2. The vendored copies land, then the readiness module and dispatch's re-point together, with the base dispatch suites as the oracle.
3. `--captured`, the MCP tool and work-intake each stop loading the engine.
4. Only then does `workspace-status` lose its retired subcommands, and the engine lose what the repair does not reach.
5. Text, tools and records follow, then the release.

The riskiest part is the port. About 2,000 lines of readiness rules leave the engine, and a mistake changes what an agent is told it may start. The replay (T4) is the check. It runs the base dispatch, extracted from the base commit, beside the new one on every entry-free planted repository and on this one.

A probe on 2026-11-02 sized the oracle. Of the 122 dispatch-suite tests at the base, 103 plant no `workspace.toml` entry. Six of those are the engine-pinning tests AC-0002 names, so 97 must pass unchanged. The other 19 plant entries that base dispatch dropped or judged, and are rewritten to expect `unmigrated_workspace`.

A second probe on 2026-11-02 traced the base dispatch over those suites. It executed 130 engine functions (about 3,160 lines), 18 `cooling.py` functions and the refresh source-authority parser. On this repository, its output was identical with and without `workspace.toml`.

## Constraints

- RFC-0106 § Errata and RFC-0083 § Errata: both entries are owner-approved before T6 deletes the migration tooling.
- The brief's `navigate-intents` non-goal: amended, owner-approved, before T2 or T8 edits `navigate-intents`.
- ADR-0074: skill scripts use the standard library only.
- `packs/AGENTS.md`: a pack-content change bumps `pack.toml` and `plugin.json` and updates the pack's eval harness. Shipped pack content cites no internal record.
- `packages/AGENTS.md`: an `agentbundle` change bumps `version.py` and `pyproject.toml`. Its tests read no repository path.
- The supervisor refuses any worker change under `docs/specs/repair-only-workspace-status/` or to a cited record: RFC-0105, RFC-0106, RFC-0083, RFC-0078, RFC-0055 and ADR-0074. The ledger, the replay record, the approvals and the errata are controller commits between attempts.
- The supervisor pins its own `work-loop` scripts and the installed `work-loop` skill. Every task that changes a `work-loop` source (T1, T2, T3, T8) reaches the installed copy only through the supervisor's `regenerate` request, and leaves `.claude/skills/work-loop/` and `.agents/skills/work-loop/` at their committed bytes. No mutation check may touch `packs/core/.apm/skills/work-loop/scripts/` while a supervisor integration suite runs.
- `tests/AGENTS.md` § Roster steps: a new roster test gets a named `build-check.yml` step, entries in `tools/lint-ci-parity.py`, and a `.workspace-prune-protected.toml` line for each `docs/specs/<slug>` literal.
- Before the PR: squash the branch and drop `docs/specs/repair-only-workspace-status/delivery/`, keeping the run history on an evidence branch.

## Construction tests

**Integration tests:** T4's replay spans T2 and T3.
**Manual verification:** T4, the replay.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Dispatch output | T1, T2, T3 | dispatch suites; isolation and copy pins | AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0013, AC-0027, AC-0030, AC-0031 checked |
| Dispatch equivalence | T4 | the replay record | AC-0007 checked |
| The `workspace-status` CLI | T6, T7 | repair suites; reachability check | AC-0008, AC-0009, AC-0010, AC-0011, AC-0012 checked |
| MCP tool and work-intake | T5 | `agentbundle` MCP suites; `work-intake` suites | AC-0014, AC-0015, AC-0016, AC-0028, AC-0029, AC-0032 checked |
| Readiness bridge | T2 | the parity tests | AC-0017 checked |
| Text | T8 | the roster check | AC-0018 checked |
| Repository tools | T9 | the kept tools' tests; no reference to a deleted tool | construction only |
| Decision rationale, records, brief | T10, T11 | roster check; inventory check; `lint-brief-coverage.py` | AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025 checked |
| Release history | T11 | `tools/check-core-release.py`; changelog checks | AC-0026 checked |

## Design (LLD)

### Design decisions

- **The readiness module is a port, not a copy.** It is `work-loop/scripts/_header_readiness.py`. It ports these engine rules, keeping each function's base name and semantics:
  - path predicates and confined artifact paths;
  - artifact metadata for specs, briefs, intents and captured items;
  - `Depends on:` and `Dependency receipts:` parsing and the resolution index;
  - the captured-item reader and listing;
  - dependency satisfaction, cycles and brief child-spec states;
  - lifecycle, collection and plan findings, and the dispatch evaluation;
  - the finding table.

  It drops workspace parsing, legacy entries and aliases, memberships, initiatives, repair and migration. The base builds a synthetic `header-derived` initiative and runs the whole reconciliation. The port evaluates the header-built queue, active and shipped spec lists directly, which is the same computation without the registry frame.

Owned by: T2

- **Dispatch reads `workspace.toml` only to refuse.** It reads the file through the existing confined read and `tomllib`, with the base 8 MiB cap. It refuses `invalid_workspace` where the base did. When any array under a top-level key other than `authorization` is non-empty, it returns the `unmigrated_workspace` refusal before evaluating anything. Readiness never depends on the file's content. The `authorization` exception keeps a leftover `[authorization.migration]` `approver_roles` array, or an unmoved refresh table, from refusing dispatch; refresh refuses on its own policy file.

Owned by: T2

- **Every load is a sibling load.** Nothing is loaded from outside dispatch's own resolved directory. The base engine's cross-skill `close-work/scripts/cooling.py` candidate is not ported, so the base layout check (`scripts/` under `skills/`) that guarded it goes too. The same files then run unchanged from `agentbundle`'s flat `_data/`.
  - `dispatch.py` loads `_header_readiness.py` and `file_safety.py` from `Path(__file__).parent`, through the base confined loader with its symlink and callable checks. A failure keeps the base `engine_unavailable: <file>` exit. The callable names are the ones dispatch calls from each file: `_SAFETY_NAMES` and `UnsafeContentError` for `file_safety.py`, and the readiness module's public entry points.
  - The cooling chain keeps the base behavior: it is resolved only when `docs/lifecycle/` exists, and a failure is the `cooling_state_unavailable` finding. The readiness module first loads `close_work.py` through the same confined loader and registers it as `sys.modules["cooling_close_work"]`, with the `__file__` that `cooling.py`'s `_close_work()` compares. It then loads `cooling.py` the same way. `cooling.py`'s own lazy, unconfined load therefore always finds the confined module, and a linked or missing file fails before anything runs.
  - `work-loop`'s `file_safety.py` is already byte-identical to `close-work`'s. The five engine-load tests break `_header_readiness.py` and `file_safety.py` in each AC-0027 condition. New cases break `cooling.py` and `close_work.py` in each AC-0031 condition, with a decoy outside the directory that records whether it ran.

Owned by: T1, T2

- **The selector test keeps its cases as literals.** `test_selector_rule_matches_workspace_status` compared dispatch's selector with `workspace_status.py`'s. It records, for each of its inputs, the canonical path the base selector returns or its refusal, as a literal table, so it still fails if dispatch's rule drifts from the base.

Owned by: T2

- **The source-authority parser is ported, with a parity pin.** `parse_source_authority` reaches 16 top-level names, about 343 lines, in a 2,171-line `refresh.py` that also holds network code. Only that closure moves into the readiness module. A roster test runs both parsers over every `toml source-authority` block in the repository and its fixtures, and compares accept or refuse and every parsed field.

Owned by: T2

- **`--captured` reuses the ported listing.** The flag adds `captured`, built as `workspace-status`'s `_captured_projection` builds it. Its oracle is that function's base result on each planted repository, recorded as literal JSON before T7 can delete it. Without the flag, the output keeps the readiness bridge's exact `_TOP_KEYS`, so `navigate-intents` needs no parser change.

Owned by: T3

- **The finding table is the codes dispatch can emit.** It is the base table minus the codes that only a registry entry can raise, plus `unmigrated_workspace`: "Run workspace-status repair-plan, then repair-apply, to move the remaining workspace.toml entries onto their artifacts." AC-0006's coverage clause removes any code no test reaches.

Owned by: T2

- **The MCP tool uses the packaged dispatch only.** `_data/` gains byte-identical `dispatch.py` and `_header_readiness.py`. The tool imports the packaged dispatch, never a repository or installed-skill copy, as it already does for `_content_safety.py`. It maps each dispatch item onto its base item shape without `ini_slug`, through the base slug guard, spec filter and pack-presence filter, and `canonical` becomes the dispatch output object. Nothing loads `_data/workspace_status_engine.py` or `_data/workspace_status_prune.py` any more, so both are dropped, with their `.gitattributes` lines and sibling-closure pins.

Owned by: T5

- **The dispatched item has two forms.** `_derive_expected_branch` and `_resolve_output_spec` share one parse. A `/` before the first `:` selects the three-part form, which keeps the base handling. Otherwise the value is two-part `type:slug`, giving branch `type/slug`, with the scope the base computes for that type and slug. Each component passes the base slug guard, and the type must be in the lifecycle manifest; any failure takes the base malformed-item path. Rule 5 of the server instructions, the `workspace_status` tool description, both `git_branch` descriptions and `README-pypi.md` name `<type>/<slug>`; the legacy form is accepted, not advertised.

Owned by: T5

- **Normalized-intake validation moves to `work-intake`.** `validate_normalized_intake` and its 25-name closure (about 389 lines) move into a `work-intake` script that `refresh.py` already loads as a sibling. The exact module is `implementation-discovered`: it is `intake_guard.py` unless its sibling-closure exemption forbids it. The router's status case returns the `navigate-intents` passthrough, and the `status-passthrough` literal in `test_registration_stop_routes.py` records it. The engine loses the function in T7, and `tools/work_intake_routing_evaluation.py` loads it from `work-intake`.

Owned by: T5

- **Retired subcommands fail loudly.** `main` maps each retired name to `retired_subcommand: <name>`, followed by its replacement: `work-loop` `dispatch.py` for `status`, `reconcile`, `explain` and `selected-membership`, and no replacement for `prune`, `retirement-candidates` and `repair-rollback`. It exits 2 before loading the engine. A bare invocation exits 2 with usage naming the two repair subcommands.

Owned by: T6

- **The engine keeps only what the repair reaches.** A pack test computes AC-0012's closure. Roots are `workspace_status.py`'s `main`. Edges are every `Name` and `Attribute` reference to a top-level name of either file, with each `_bind_engine` assignment mapping a module global to the engine name it binds. It fails on any top-level function or class outside the closure. Once `main` holds only the repair and refusal branches, that closure decides which engine code T7 deletes.

Owned by: T6, T7

- **Suites outside the two skills.** Their fates:
  - `packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py` and `tests/roster/test_status_projection_and_context_exclusion.py` lose the cases that call `project_closeout_status`, a status-only projection.
  - `packs/core/tests/skills/work-intake/test_work_intake.py` loads normalized-intake validation from `work-intake`, assertions unchanged. `packs/core/tests/pack/test_work_intake_surface.py` does the same, and loses its `migration-read-only-plan` row and `validate_migration_selection` cases.
  - The `migration-read-only-plan` routing case, its four `evals/files/routing/migration-*` fixtures, `tools/work_intake_routing_evaluation.py`'s `_evaluate_migration` path, and `tests/roster/test_work_intake_refresh_coordinator.py`'s `test_integrated_matrix_has_a_read_only_migration_planner_row` are deleted with the migration tooling.
  - The dispatch assertions in the repair suites are AC-0030's dispatch-comparison tests. Each asserts AC-0030 after the apply.
  - `test_spec_registration_stop_repair.py`'s `migrate_legacy_entry` helper plants the entry its migration produced as a literal, so `test_a_migrated_entry_is_planned_as_a_spec_entry_drop` and `test_a_migrated_entry_held_by_its_record_gets_the_type_6_manual_item` keep their assertions.
  - `packages/agentbundle/tests/integration/test_zipapp.py` loads the packaged dispatch in place of `_load_workspace_status_engine`.
  - `packs/core/tests/skills/work-loop/test_lint_spec_status_deferred.py`'s reader-parity table and `tools/test_pack_test_compatibility.py` keep the engine while the repair reaches the functions they load. Otherwise they retarget `_header_readiness`'s ported captured-item reader, assertions unchanged.
  - The `workspace-status` reader and equivalence suites keep every case whose engine function the repair still reaches. A case driving `status`, `explain` or `analyze_bounded` retargets dispatch or `_header_readiness` with its assertion unchanged where the behavior survives, and is deleted where it pinned only status output.

Owned by: T5, T6, T7

- **Earlier equivalence rows.** Each § Equivalence row whose cited evidence loses every tracked file gains, in the same change, the retargeted suite that now proves its behavior. No row's category or authority changes.

Owned by: T11

- **No sentence routes a status question to `workspace-status`.** The roster check that proves AC-0018 also carries a content pin, which is design and not contract. In the Markdown files AC-0018 lists, other than `workspace-status`'s own SKILL.md and `references/mutate.md`, no sentence names `workspace-status` together with any of `status`, `queue`, `orient`, `orientation`, `ready`, `next`, `eligibility`, `reconciliation` or `backlog`. Sentences are split on the raw text, at sentence ends, blank lines, headings and list-item starts, and whitespace is collapsed inside each sentence. The name matches only as the exact token `workspace-status`, bounded by characters other than a letter, digit, `-` or `_`. The listed words match whole and case-insensitively, and a listed word joined to another by `-` or `_` does not count. The pin skips JSON. The controller may narrow its word list when a repair sentence trips it.

Owned by: T8

- **Tools.** `tools/compare-registry.py` and `tools/test_compare_registry.py` are deleted, since every registration stop has run. `tools/replay-dispatch.py` and `tools/bench-workspace-status.py` stay if their tests pass against the shrunk engine, and are deleted with their tests otherwise. Either outcome is recorded in the ledger.

Owned by: T9

## Tasks

### T10: Governance before the edits

- **Depends on:** none
- **Verification mode:** goal-based
- **Touches:** controller commits only: `docs/rfc/0106-stop-registering-derivable-work.md`, `docs/rfc/0083-work-intake-and-artifact-routing.md`, `docs/product/briefs/workspace-registry-retirement-delivery.md`, `docs/specs/repair-only-workspace-status/notes/verification-ledger.md`
- **Tests:** for AC-0019, AC-0020, AC-0024, and AC-0025's errata, brief and hand-over records: the owner approves each text, and the ledger holds its SHA-256 and the hand-over owner's agreement. `lint-brief-coverage.py` passes.
- **Done when:** both errata entries and the brief text are committed with their approvals recorded.

### T1: Vendor `cooling.py` and `close_work.py` into `work-loop`

- **Depends on:** none
- **Verification mode:** goal-based
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/cooling.py`, `packs/core/.apm/skills/work-loop/scripts/close_work.py`, `tests/roster/test_work_loop_cooling_mirror.py`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`, `docs/specs/workspace-retirement/inventory.toml`
- **Tests:** for AC-0013: a roster byte pin of each copy against its `close-work` source, modeled on the `navigate-decisions` file-safety mirror test.
- **Done when:** the new roster test and `tools/lint-ci-parity.py` pass, and the supervisor's `regenerate` request has rebuilt the installed `work-loop` copy.

### T2: The header-readiness module, and dispatch on it

- **Depends on:** T1, T10
- **Verification mode:** TDD
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/_header_readiness.py`, `packs/core/.apm/skills/work-loop/scripts/dispatch.py`, the dispatch suites, `packs/core/tests/skills/work-loop/test_dispatch_isolation.py`, `tests/roster/test_header_readiness_source_authority_parity.py`, `packs/core/.apm/skills/navigate-intents/scripts/intent_readiness.py`, `packs/core/tests/skills/navigate-intents/test_export_readiness.py`, `tests/roster/test_spec_registration_stop.py`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`, `docs/specs/workspace-retirement/inventory.toml`, `.claude/skills/navigate-intents/**`, `.agents/skills/navigate-intents/**`
- **Tests:**
  - AC-0001: the isolation suite copies only `work-loop/` into a temporary `skills/` tree and compares output for each planted repository.
  - AC-0002: the 97 entry-free tests keep their assertions; only their fixture helpers change, if a helper loaded the engine. The selector test's literal table.
  - AC-0027: the five engine-load tests, rewritten, break `_header_readiness.py` and `file_safety.py` in each condition.
  - AC-0031: `cooling.py` and `close_work.py` broken in each condition, over a repository with `docs/lifecycle/`, each with an outside decoy that records whether it ran.
  - AC-0003: the 19 entry-planting tests become refusal cases. One case plants an entry in each of `[backlog]`, an initiative's `work`, `brief_queue` and `shaping_queue`, and a repo-origin spec entry with `needs = []`. One `[authorization.migration]` table alone does not refuse.
  - AC-0004: the base `invalid_workspace` cases are unchanged.
  - AC-0006: the coverage check over the finding table.
  - AC-0013: the parser parity pin.
  - AC-0017: both bridge parity tests point at `_header_readiness`'s table, and `_KNOWN_FINDINGS` equals it.
- **Done when:** the dispatch suites, the isolation and parity tests, `packs/core/tests/skills/navigate-intents/` and `tests/roster/test_spec_registration_stop.py` pass, and the supervisor's `regenerate` request has rebuilt the installed `work-loop` copy.

### T3: `--captured` and the shaping-item guard

- **Depends on:** T2
- **Verification mode:** TDD
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/dispatch.py`, `packs/core/tests/skills/work-loop/test_dispatch.py`, `packs/core/tests/skills/work-loop/fixtures/captured-projection/**`, `packs/core/.apm/skills/work-loop/SKILL.md`, `tools/test_workspace_status.py`, `tests/roster/test_workspace_status_projection.py`
- **Tests:** for AC-0005: planted captured items, one of each `Type:` route, a `signal`, an invalid item and an unreadable item, each with and without `workspace.toml`. The `captured` object is compared with the base `_captured_projection` output recorded as literal JSON fixtures. A run without the flag has the base key set. Step 0's guard text names `dispatch.py --captured`, and `_WORK_LOOP_CONTRACT_HASH` follows the new Step 0.
- **Done when:** the dispatch suites, `tools/test_workspace_status.py` and `tests/roster/test_workspace_status_projection.py` pass, and the supervisor's `regenerate` request has rebuilt the installed `work-loop` copy.

### T4: The dispatch replay

- **Depends on:** T2, T3
- **Verification mode:** manual QA
- **Touches:** `.context/` only; the controller copies the record into the ledger
- **Tests:** for AC-0007: extract `packs/core/.apm/skills/` at the base into a temporary tree. For each entry-free repository the dispatch suites plant, captured with the T2 probe's plugin, and for this repository, run both dispatches argless and with `--start` and `--resume` of each listed spec. Compare the standard output bytes and the exit codes, and record the run count and the difference count.
- **Done when:** the difference count is 0 and the controller has committed the record to the ledger.

### T5: The MCP tool and work-intake leave the engine

- **Depends on:** T2
- **Verification mode:** TDD
- **Touches:**
  - MCP and packaging: `packages/agentbundle/agentbundle/workspace_mcp.py`, `packages/agentbundle/README-pypi.md`, `packages/agentbundle/agentbundle/build/self_host.py`, `packages/agentbundle/agentbundle/_data/dispatch.py`, `packages/agentbundle/agentbundle/_data/_header_readiness.py`, `packages/agentbundle/agentbundle/_data/workspace_status_engine.py`, `packages/agentbundle/agentbundle/_data/workspace_status_prune.py`, `packages/agentbundle/agentbundle/_data/work_intake_refresh.py`, `.gitattributes`;
  - package tests: `packages/agentbundle/tests/**/test_workspace_mcp*.py`, `packages/agentbundle/tests/integration/test_build_check_drift_gates.py`, `packages/agentbundle/tests/integration/test_zipapp.py`, `tests/roster/test_packaged_runtime_closure.py`;
  - work-intake: `packs/core/.apm/skills/work-intake/scripts/refresh.py`, `intake_guard.py`, `intake_router.py`, `packs/core/.apm/skills/work-intake/evals/files/routing/matrix.json`, `packs/core/tests/skills/work-intake/test_work_intake.py`, `packs/core/tests/skills/work-intake/test_registration_stop_routes.py`, `packs/core/tests/pack/test_work_intake_surface.py`, `tools/work_intake_routing_evaluation.py`, `tests/roster/test_tracker_intake_adapters.py`, `.claude/skills/work-intake/**`, `.agents/skills/work-intake/**`;
  - `docs/specs/workspace-retirement/inventory.toml`.
- **Tests:**
  - AC-0014 and AC-0015: MCP cases over planted fixture repositories. These are entry-free, unmigrated, without `workspace.toml`, with a ready spec, with an active spec, and with a blocked non-spec path the filters skip. Each compares the tool's lists with the packaged dispatch's output and asserts no `ini_slug`.
  - AC-0028: dispatched-item cases for `type:slug`, `ini/type:slug`, `spec:a/b`, an unsafe slug and an unknown type in each form, each asserting the expected branch, the `git_commit` scope and whether git writes are blocked.
  - AC-0032: a pin over the server instructions, the tool description, both `git_branch` descriptions and `README-pypi.md`.
  - AC-0016: the two `work-intake` suites keep their assertions, and a pin shows `refresh.py` names no `workspace_status` module.
  - AC-0029: the router's status case, the matrix's status rows and the `status-passthrough` literal.
  - The sibling-closure pin, the drift gate and the zipapp test follow the new `_data/` set.
- **Done when:** `packages/agentbundle/tests/`, the `work-intake` suites, `tests/roster/test_packaged_runtime_closure.py` and `tests/roster/test_tracker_intake_adapters.py` pass.

### T6: `workspace-status` keeps only the repair

- **Depends on:** T2, T3, T5, T10
- **Verification mode:** TDD
- **Touches:**
  - scripts and skill files: `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`, the five `workspace_status_prune.py` and `workspace_status_retirement*.py` scripts, `packs/core/.apm/skills/workspace-status/assets/workspace.toml.template`, `references/explain.md` and `references/reconcile.md`;
  - deleted contracts and fixtures: `contracts/jsonschema/work-intake-migration-*.schema.json`, `contracts/jsonschema/spec-retirement-candidates.schema.json`, `contracts/README.md`, `packs/core/.apm/skills/work-intake/evals/files/routing/migration-*`, the `migration-read-only-plan` case in `matrix.json`, `tools/work_intake_routing_evaluation.py`, `tests/roster/test_work_intake_refresh_coordinator.py`, `packs/core/tests/pack/test_work_intake_surface.py`;
  - tests: `packs/core/tests/skills/workspace-status/**`, `packs/core/tests/skills/workspace-status/test_repair_only_reachability.py`, `packs/core/tests/skills/close-work/test_pause_receipts_and_initiative.py`, `tests/roster/test_status_projection_and_context_exclusion.py`, `tools/test_workspace_status_cli.py`, `tools/test_workspace_status.py`, `tests/roster/test_workspace_status_progressive_disclosure.py`, and the roster tests that drive a retired subcommand;
  - records and projections: `docs/specs/workspace-retirement/inventory.toml`, `.claude/skills/workspace-status/**`, `.agents/skills/workspace-status/**`.
- **Tests:**
  - AC-0008 and AC-0009: argument-vector cases for each retired subcommand, a bare call, and each migration form. These assert exit 2, empty standard output, the standard-error prefix, and an unchanged tree.
  - AC-0011: the listed repair suites keep their assertions, with the migration-form setup planted as a literal.
  - AC-0030: each dispatch-comparison test AC-0030 names asserts AC-0030 after the apply.
  - The migration, prune, retirement and status-output suites are deleted, each with its fixtures. Reader and equivalence cases follow the design's suite fates.
  - AC-0010: a grep pin over both trees.
  - `BACKEND_DIGESTS` and the mode-row check follow the new scripts.
- **Done when:** `packs/core/tests/skills/workspace-status/`, `packs/core/tests/skills/close-work/`, `tools/test_workspace_status_cli.py`, `tools/test_workspace_status.py`, `tools/test_local_ci_shared_test_deduplication.py` and every roster test the change touches pass.

### T7: The engine loses what the repair does not reach

- **Depends on:** T6
- **Verification mode:** TDD
- **Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`, `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`, `packs/core/tests/skills/workspace-status/**`, `packs/core/tests/skills/work-loop/test_lint_spec_status_deferred.py`, `tools/test_pack_test_compatibility.py`, `tests/roster/test_workspace_status_progressive_disclosure.py`, `.claude/skills/workspace-status/**`, `.agents/skills/workspace-status/**`
- **Tests:** for AC-0012: the reachability test turns green. For AC-0011: the repair suites still keep their assertions. A test that called a deleted engine function directly follows the design's suite fates.
- **Done when:** the reachability test, `packs/core/tests/skills/workspace-status/`, `packs/core/tests/skills/work-loop/test_lint_spec_status_deferred.py` and `tools/test_pack_test_compatibility.py` pass.

### T8: Skill text and evals

- **Depends on:** T3, T6
- **Verification mode:** goal-based
- **Touches:**
  - skill text: `packs/core/.apm/skills/workspace-status/SKILL.md` and `references/mutate.md`; `packs/core/.apm/skills/work-intake/SKILL.md`; `packs/core/.apm/skills/navigate-intents/SKILL.md`; `packs/core/.apm/skills/close-work/SKILL.md`; `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`;
  - evals: `packs/core/.apm/skills/work-loop/evals/evals.json`, `packs/core/.apm/skills/workspace-status/evals/evals.json`, `packs/core/.apm/skills/workspace-status/evals/eval_queries.json`, `packs/core/.apm/skills/work-intake/evals/evals.json`;
  - tests: `tests/roster/test_repair_only_workspace_status.py`, and the roster phrase-pin tests that pin removed text;
  - CI and projections: `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`, `.workspace-prune-protected.toml`, `.claude/skills/**`, `.agents/skills/**` other than `work-loop`.
- **Tests:** for AC-0018: the new roster check over AC-0018's lists, with the design's sentence content pin. Each phrase pin that pinned removed text pins the replacement text, or is deleted with the behavior it guarded. The eval schema suites pass.
- **Done when:** the new roster check, the touched roster tests, the eval suites and `tools/lint-ci-parity.py` pass, and the supervisor's `regenerate` request has rebuilt the installed `work-loop` copy.

### T9: Repository tools

- **Depends on:** T7
- **Verification mode:** goal-based
- **Touches:** `tools/compare-registry.py`, `tools/test_compare_registry.py`, `tools/replay-dispatch.py`, `tools/test_replay_dispatch.py`, `tools/bench-workspace-status.py`, `Makefile`, `tools/repo/build_gate_chain.py`, `tools/shard_test_roster.py`, `tools/lint-ci-parity.py`, `docs/specs/workspace-retirement/inventory.toml`
- **Tests:** each kept tool's test passes. Each deleted tool leaves no reference in the Makefile, the gate chain or the shard roster.
- **Done when:** `make lint-ruff lint-mypy`, `tools/lint-ci-parity.py` and the kept tools' tests pass.

### T11: Records and release

- **Depends on:** T4, T7, T8, T9, T10
- **Verification mode:** goal-based
- **Touches:** `docs/specs/workspace-retirement/retirement-record.md`, `docs/specs/workspace-retirement/inventory.toml`, `tests/roster/test_repair_only_workspace_status.py`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/pyproject.toml`, `docs/product/changelog.d/*`
- **Tests:**
  - AC-0021, AC-0022, AC-0023: the record and inventory checks, the earlier rows' evidence, and the roster check's closure-entry case.
  - AC-0025's closure-entry record: the ledger holds the owner's approval with the entry's SHA-256.
  - AC-0026: `tools/check-core-release.py --base "$(git merge-base HEAD origin/main)"` after `git fetch origin`, and the changelog checks.
  - Also: `make lint-ruff lint-mypy`, and the dispatched `test-roster.yml`, `test-corpus.yml` and `pack-javascript.yml` runs.
- **Done when:** the owner has approved the closure entry, the controller has recorded it, and each check passes.

## Rollout

- **Delivery:** one `core` release and one `agentbundle` release. An adopter whose `workspace.toml` still holds entries is refused by dispatch until they run `repair-plan` and `repair-apply --yes`.
- **Reversal:** revert the release. Every deleted file and function is in git history.

## Risks

- A readiness rule mis-ported only on a path no planted repository reaches would pass the suites and the replay. The trace's 130 executed functions bound what the oracle covers; anything else the engine held is registry-only by construction.
- A control plane that reads `ini_slug` from `workspace_status()` breaks on upgrade; one that sets the three-part dispatched item keeps working.

## Changelog

- 2026-11-02: spec approved by eugenelim at `63ed6819e`, after four spec-mode shaping and adversarial review rounds and two security spec-stage rounds, with the round-4 repairs accepted unreviewed.
- 2026-11-02: plan approved by eugenelim at `63ed6819e`.
