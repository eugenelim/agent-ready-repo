# Plan: dropped-primitives-coverage

- **Spec:** [`spec.md`](spec.md)
- **Status:** Shipped (2026-05-26)

> **Plan contract:** this is the implementation strategy. Unlike the spec, this document is allowed to change as you learn. When it changes substantially (a different approach, not just a re-ordering), note why in the changelog at the bottom.

## Approach

Single-PR implementation that lands the contract bump (v0.7 → v0.8) + schema enum extension, the shared `merge-json` projection helper, the new `codex-agent-toml` projection helper, the build-pipeline codex.py wiring (the sole projection-mode dispatcher), the eight packs' contract version bump, the dropped-primitives warning rail, the sibling-spec amendment, and the test surface in one merge per RFC-0004 atomicity. Order of operations: (1) contract data edits + schema-enum extension — *the floor* (T1); (2) shared `merge-json` helper lifted from claude-code-private into `build/projections/merge_json.py` (T2); (3) shared `codex-agent-toml` serialiser at `build/projections/codex_agent_toml.py` (T3); (4) build-pipeline codex.py wiring — codex's per-adapter handler dispatches the new modes to the shared helpers (T4 — the **only** dispatcher; install routes through this via `render.py` → `build.main.run_recipe`); (5) install-handler runtime-accessor pin — verify codex's extended `allowed-prefixes` flow through the runtime accessors (T5, no new dispatcher code); (6) warning-rail helpers + install handler hook (T6); (7) eight packs bump to v0.8 (T7); (8) integration tests across the install handler routing through the build pipeline (T8); (9) sibling-spec amendment + ROADMAP (T9); (10) gates (T10). Tests-first per task per `work-loop` discipline. Task graph: T2 and T3 are independent siblings (both `Depends on: none`) consumable from T4; the rest is sequential because the contract is the shared substrate.

## Constraints

- **Constrained by:** RFC-0009 (codex `direct-directory` projection at `.agents/skills/` — the existing codex projection this spec extends); RFC-0005 (`merge-json` mode + `managed-key` — reused for codex hooks.json); RFC-0012 (per-adapter projection at repo scope — the warning's hook point is in the install handler block this RFC shaped); ADR-0002 (per-pack default-plus-allowance — atomicity precedent).
- **Single PR per RFC-0004 atomicity.** Partial landings risk (a) the contract claims `.codex/agents/` projection but no code writes there, (b) the schema accepts the new mode but the projection-dispatch doesn't dispatch to it, (c) eight packs declare v0.8 but the resolver can't see the new projections.
- **No new third-party Python dependency.** stdlib (`tomllib` for reads; hand-rolled TOML emit reusing `config.py`'s `_emit_basic_string` helper for writes) plus existing `jsonschema`.
- **Warning wording fixed by spec AC10**; tests assert exact strings.
- **Refuse-on-drop is out of scope** — this spec ships a warning, not a refusal. A future RFC can add `--accept-degraded` if telemetry shows the warning is missed.

## Construction tests

Most construction tests live under **Tasks** below (per-task `Tests:`).

**Cross-cutting tests** (span more than one task):

- **End-to-end install integration suite** at `packages/agentbundle/tests/integration/test_install_dropped_primitives_warning.py`. Installs `core` against each of the four shipped adapters at repo scope and asserts (a) the codex projection now lands `.codex/agents/<agent>.toml` + `.codex/hooks.json` (the contract-bump verification), (b) the warning rail fires for codex/kiro/copilot with the correct per-adapter type list, (c) the warning rail stays silent for claude-code. This *is* T8; cross-referenced here for the cross-cutting view. Covers spec AC18; prerequisites span T1-T7.
- **`pre-pr.py` end-to-end** — `python3 tools/hooks/pre-pr.py` exits 0 on the final tree. Covers spec AC21; spans every task.
- **`make build-self FORCE=1` clean** after the final commit. Covers spec AC20; spans T7 (the eight pack bumps).

## Tasks

Order matters — listed in the order they should be done. The graph is **mostly sequential** because the contract is the shared substrate, but T2 (merge-json lift) and T3 (codex-agent-toml serialiser) are independent siblings (both declaring `Depends on: none`) that T4 + T5 consume. The warning rail (T6) depends only on T1's contract data. T7's pack bumps wait until both T4 and T5 land so a clean reinstall of a v0.8 pack via codex actually projects under the new contract.

### T1: Contract bump v0.7 → v0.8 plus codex projection entries plus new frontmatter mapping (atomic edit)

**Depends on:** none

**Spec mapping:** AC1, AC2, AC3, AC4, AC5. Mode: goal-based check (contract is data; test is `tomllib.loads` + assertion).

**Atomicity requirement:** the version bump AND the two codex projection edits AND the `allowed-prefixes` extension AND the new frontmatter-mapping table land in a **single commit**. Splitting leaves intermediate snapshots (e.g., `version = "0.8"` with codex projection still saying `dropped`) that break every downstream test.

**Tests:**
- `packages/agentbundle/agentbundle/build/tests/test_contract_v08.py::test_contract_version_is_08` — load `_data/adapter.toml`, assert `tomllib.loads(...)["contract"]["version"] == "0.8"`.
- `test_contract_v08.py::test_codex_agent_projection` — find `[[adapter.codex.projection]]` with `primitive = "agent"`; assert `mode == "codex-agent-toml"`, `target-path == ".codex/agents/"`, `frontmatter-mapping == "codex-agent-frontmatter-v0.8"`.
- `test_contract_v08.py::test_codex_hook_wiring_projection` — assert `mode == "merge-json"`, `target-path == ".codex/hooks.json"`, `managed-key == "hooks"`.
- `test_contract_v08.py::test_codex_command_still_dropped` — assert `mode == "dropped"` (the command entry is preserved).
- `test_contract_v08.py::test_codex_allowed_prefixes_includes_codex_dir` — assert `".codex/"` in `allowed-prefixes.repo` and `.user`.
- `test_contract_v08.py::test_codex_frontmatter_mapping_table` — load `[frontmatter-mapping."codex-agent-frontmatter-v0.8"]`; assert `name` and `description` mapping entries present; assert NO `body` sub-table (the body-to-`developer_instructions` is a mode-level convention per AC4, not a rename rule).
- `test_contract_v08.py::test_schema_admits_codex_agent_toml_mode_at_every_dropped_site` — load `adapter.schema.json`; walk the JSON tree and find every `enum` array that contains the string `"dropped"`; assert every such enum also contains `"codex-agent-toml"`. The test discovers the sites dynamically so a future schema edit that adds a fifth enum site doesn't silently drift this AC.
- `test_contract_v08.py::test_schema_loads_v08_contract` — load `adapter.schema.json` via `jsonschema` and validate the v0.8 `adapter.toml` against it; assert no validation errors. This is the load-bearing schema-integration test. Implicit pin: codex's `agent` entry now uses `codex-agent-toml` and codex's `hook-wiring` entry now uses `merge-json` — both must be admitted at the codex array site (the schema's projection-mode enum is global across adapters, so `merge-json` already validates there).
- `test_contract_v08.py::test_claude_code_and_kiro_unchanged` — property invariants: claude-code projects all 5 primitives; kiro projects 4 of 5 with `command: dropped`; copilot's 3 dropped entries unchanged.

**Approach:**
- Edit `packages/agentbundle/agentbundle/_data/adapter.toml`:
  - Bump `[contract] version` `"0.7"` → `"0.8"`.
  - Replace the codex `[[adapter.codex.projection]]` entries for `agent` and `hook-wiring` per AC2.
  - Extend `[adapter.codex.scope].allowed-prefixes.repo` and `.user` with `".codex/"` per AC3.
  - Add `[frontmatter-mapping."codex-agent-frontmatter-v0.8"]` table per AC4. Per-key sub-tables declared explicitly: `[frontmatter-mapping."codex-agent-frontmatter-v0.8".name]` with `rename = "name"`; `[frontmatter-mapping."codex-agent-frontmatter-v0.8".description]` with `rename = "description"`. The shape follows the existing per-key sub-table convention (the kiro-agent-frontmatter-v0.9 mapping at `adapter.toml:321+` ships `description` / `tools` / `model` sub-tables — codex's `name` sub-table is new and per-mapping; don't copy kiro's keyset verbatim). **No `body` sub-table** — the markdown body lands in `developer_instructions` via mode-level convention in the `codex-agent-toml` projection mode itself (T3), not via a rename rule.
  - Update the header comment to name this spec alongside existing RFC pointers.
  - **All edits in one commit.**
- Edit `packages/agentbundle/agentbundle/_data/adapter.schema.json`:
  - Extend the projection-mode `enum` to admit `"codex-agent-toml"` at **every site that currently enumerates `"dropped"`**. Discover the sites with `grep -n '"dropped"' adapter.schema.json` (today: four sites — two for the top-level array-form `[[adapter.<name>.projection]]` shapes and two for the scope-conditional `[adapter.<name>.projections.<primitive>]` shapes; future schema edits may change the count). Each enum site that admits the current modes (`direct-directory` / `direct-file` / `merge-json` / `user-merge-json` / `merge-into-agent-json` / `instruction-file` / `managed-block-inline` / `degraded-info-log` / `dropped`) gets `codex-agent-toml` added. Without the extension at every site, schema-validated contract loads reject v0.8 on first run.
- Mirror the edited `_data/adapter.toml` into `docs/contracts/adapter.toml` (existing convention enforced by `test_contract.py::test_contract_files_byte_identical`).
- Run `make build-self FORCE=1` to propagate any projected `adapter.toml` copies.

**Done when:** the contract tests pass, the schema-load test in `test_contract.py` exits 0 (the schema enum extension is the load-bearing piece), and `make build-self FORCE=1` produces a clean working tree.

---

### T2: Lift `merge-json` projection helper to a shared module

**Depends on:** none

**Spec mapping:** AC7 (the spec acknowledgment that the helper is shared, not codex-private). Mode: TDD (the existing claude-code merge-json tests are the safety net; the lift is a refactor — tests stay green before and after; public surface unchanged).

**Tests:**

The existing claude-code merge-json tests at `packages/agentbundle/agentbundle/build/tests/test_adapter_claude_code.py` (search for `merge_json` / `hook-wiring`) stay green before and after. Plus:

- `packages/agentbundle/agentbundle/build/tests/test_projections_merge_json.py` (new module) — focused unit tests on the lifted helper: empty source returns no-op; merging into existing JSON preserves non-managed-key entries; multiple TOML source files merge in deterministic (sorted) order; output is `json.dumps(..., indent=2, sort_keys=True) + "\n"` per the pre-lift behaviour.

**Approach:**

- The `packages/agentbundle/agentbundle/build/projections/` package already exists with five sibling modules (`__init__.py`, `direct_directory.py`, `hook_id.py`, `kiro_ide_hook.py`, `merge_into_agent_json.py`, `user_merge_json.py`). Add the helper alongside these as a sixth sibling — no namespace-anchor creation needed.
- Lift the `_project_merge_json` function (currently defined inside `packages/agentbundle/agentbundle/build/adapters/claude_code.py` and dispatched at the `mode == "merge-json"` branch in `_project_for_codex`-style dispatch) into `packages/agentbundle/agentbundle/build/projections/merge_json.py` as a public function `project_merge_json` (signature unchanged). Reference the symbol name and the dispatcher case rather than line numbers — line numbers drift with neighbour edits per the project convention.
- `claude_code.py` imports the function from the new location and removes the local definition. The existing `mode == "merge-json"` dispatcher branch now calls the imported function.
- Re-run the existing claude-code merge-json tests AND the security tests (`packages/agentbundle/agentbundle/build/tests/test_security.py` exercises the public `project` entry-point which transitively calls the lifted helper); they must stay green byte-identically.

**Done when:** the new module test passes; existing claude-code merge-json tests stay green; `test_security.py` exits 0; `grep -rn "_project_merge_json" packages/agentbundle/agentbundle/build/adapters/` shows the function is no longer defined inside `claude_code.py`; `make build-self FORCE=1 && git status --short` is empty (the dist projection copy at `build/lib/agentbundle/build/adapters/claude_code.py` regenerates cleanly without orphan content).

---

### T3: `codex-agent-toml` projection helper — markdown → TOML serialiser

**Depends on:** none

**Spec mapping:** AC6, AC16. Mode: TDD (pure conversion logic).

**Tests:**

New module `packages/agentbundle/tests/unit/test_codex_agent_toml.py`:

- `test_trivial_round_trip` — input `---\nname: foo\ndescription: bar\n---\nBody content.` produces TOML where `tomllib.loads(output)["name"] == "foo"`, `["description"] == "bar"`, `["developer_instructions"]` contains `"Body content."`.
- `test_multiline_body_preserved` — body with newlines and special characters (quotes, backslashes) round-trips through TOML's basic-multi-line string (`"""..."""`) without corruption. Pin: input body containing `"hello"` produces TOML where `tomllib.loads(output)["developer_instructions"]` equals the input body byte-for-byte.
- `test_unmapped_fields_dropped` — input with `tools: [foo, bar]` produces TOML without a `tools` field (codex agent format has no slot). Assert `"tools" not in tomllib.loads(output)`.
- `test_frontmatter_rename_applied` — if the frontmatter-mapping renames a field (e.g., `summary` → `description`), the rename is applied; output has the renamed key.
- `test_empty_body_emits_empty_developer_instructions` — input with frontmatter only and no body produces `developer_instructions = ""` (empty string, not missing).
- `test_markdown_body_lands_in_developer_instructions` — the codex-agent-toml mode unconditionally writes the markdown body to the TOML `developer_instructions` field; this is a mode-level convention, not a frontmatter-mapping rename (the body isn't a frontmatter key). Pin: input body produces `tomllib.loads(output)["developer_instructions"] == <body>`.
- `test_developer_instructions_not_in_frontmatter_mapping` — assert the contract's `[frontmatter-mapping."codex-agent-frontmatter-v0.8"]` sub-table does NOT contain a `body` or `developer_instructions` rename entry; the body-to-`developer_instructions` is a mode convention per spec AC4.

**Approach:**

- Add the serialiser at `packages/agentbundle/agentbundle/build/projections/codex_agent_toml.py` as a public function `project_codex_agent_toml(source_dir, output_root, rule, frontmatter_mappings)` returning `None` and writing TOML files to `output_root / rule["target-path"] / <agent-name>.toml`.
- Implementation: enumerate `<source_dir>/*.md` files (sorted); for each, parse YAML frontmatter using the existing parser (reuse `agentbundle.config._parse_frontmatter` or the equivalent in render.py — implementer verifies); split markdown body; apply the frontmatter-mapping rename rules (including the `body` sentinel that captures the markdown body); emit TOML using either an in-module emitter or by extending `agentbundle.config._emit_basic_string` to handle multi-line basic strings.
- TOML emission shape: each output field is emitted as `<key> = <value>` where strings use basic-string quoting; multi-line bodies use `"""..."""` triple-quote with embedded backslash-escapes for any literal `"""` inside the body.
- The helper takes `frontmatter_mappings` (the contract's `[frontmatter-mapping]` sub-table for the named mapping) as an explicit argument so it doesn't reach into the global contract — this keeps the function pure and unit-testable without a full contract fixture.

**Done when:** all six unit tests pass; the function is consumable from both the build pipeline (T4) and the install handler (T5) without further wiring.

---

### T4: Build-pipeline codex.py wiring — dispatch the new modes

**Depends on:** T1, T2, T3

**Spec mapping:** AC2 (the contract claim must match runtime), AC7 (codex `merge-json` reuses the shared helper). Mode: TDD (integration — `make build` against fixture packs).

**Tests:**

Extend `packages/agentbundle/agentbundle/build/tests/test_adapter_codex.py` (existing module):

- `test_codex_agent_projects_via_codex_agent_toml_mode` — fixture pack with one agent; run codex projection; assert `<output>/.codex/agents/<agent>.toml` exists and parses as TOML with the expected `name`, `description`, `developer_instructions` keys.
- `test_codex_hook_wiring_projects_via_merge_json` — fixture pack with one hook-wiring TOML; run codex projection; assert `<output>/.codex/hooks.json` is valid JSON with the `hooks` key containing the merged entries.
- `test_codex_command_still_dropped_at_build_time` — fixture pack with one command; run codex projection; assert NO `command`-shaped output anywhere in `<output>/.codex/` (the contract's `dropped` mode means `_iter_primitives` skips the type).
- Existing tests `test_agent_hook_wiring_command_dropped`, `test_hook_body_extensions_preserved`, `test_every_shipped_skill_projects_with_equal_bytes` are updated/replaced to assert the new v0.8 shape rather than the v0.7 `dropped` shape. The deletion + replacement of `test_agent_hook_wiring_command_dropped` is **deliberate spec-driven inversion** — its v0.7 assertion is the inverse of what the v0.8 contract (AC2) now claims; this is not a regression hiding behind a test deletion. Rename the replacement to `test_only_command_dropped_post_v08` so a future grep for the old name surfaces the intentional drift via the rename history rather than appearing to be missing.

**Approach:**

- In `packages/agentbundle/agentbundle/build/adapters/codex.py`, extend the dispatcher around line 143 (`raise ValueError(f"codex: unhandled mode {mode!r} for {primitive_name}")`):
  ```python
  elif mode == "merge-json":
      from agentbundle.build.projections.merge_json import project_merge_json
      for source_dir in source_dirs:
          project_merge_json(source_dir, output_root, rule)
  elif mode == "codex-agent-toml":
      from agentbundle.build.projections.codex_agent_toml import project_codex_agent_toml
      mapping_name = rule["frontmatter-mapping"]
      mapping = contract["frontmatter-mapping"][mapping_name]
      for source_dir in source_dirs:
          project_codex_agent_toml(source_dir, output_root, rule, mapping)
  else:
      raise ValueError(...)
  ```
- Update `_iter_primitives` if needed (the existing implementation skips primitives where `mode == "dropped"`; the new modes are non-dropped and pass through).

**Done when:** the three new tests pass; the existing tests in `test_adapter_codex.py` are updated to match v0.8; `pytest agentbundle/build/tests/test_adapter_codex.py` exits 0.

---

### T5: Install-handler runtime accessors — verify contract data flows through

**Depends on:** T1, T4

**Spec mapping:** AC7's runtime-accessor surface. Mode: TDD (unit tests on the accessors; the actual install-side projection is the build pipeline T4 wires — confirmed via `packages/agentbundle/agentbundle/render.py` which imports `run_recipe` from `agentbundle.build.main` and routes through `build/adapters/codex.py`; there is **no independent install-handler projection-mode dispatcher** to update).

**Tests:**

New module `packages/agentbundle/tests/unit/test_codex_projection_modes.py`:

- `test_codex_allowed_prefixes_includes_codex_dir_repo` — the install handler's `_adapter_allowed_prefixes_repo("codex")` returns a list containing `".codex/"` (verifies T1's contract data flows through the runtime accessor).
- `test_codex_allowed_prefixes_includes_codex_dir_user` — same for `_adapter_allowed_prefixes_user("codex")`.
- `test_path_jail_rejects_write_outside_codex_prefix` — `safety.write_jailed(root, "other-dir/foo", b"x")` with codex's resolved prefix list raises `safety.PathJailError`; positive control writes under `.codex/agents/foo.toml` succeed.
- `test_render_pack_routes_codex_agent_to_build_pipeline` — invoke `render.render_pack(pack_dir, contract=...)` for a fixture pack with one agent under codex; assert the resulting output contains `.codex/agents/<name>.toml`. This is integration-shape but lives in the unit-test module because it verifies the install handler's wrapping correctly threads through T4's dispatch.

**Approach:**

- No new dispatcher code is needed (round-2 review caught this — `render.py` is a thin wrapper over `agentbundle.build.main.run_recipe` → `build/adapters/codex.py`, where T4's wiring lives).
- The only install-side changes are runtime-accessor assertions: confirm `_adapter_allowed_prefixes_repo("codex")` and `_adapter_allowed_prefixes_user("codex")` read the extended prefix lists from the T1 contract bump. These accessors are data-driven (existing implementation reads from the contract per pack), so the T1 edit should flow through without code change — but the tests pin this at runtime so a regression that hardcodes a prefix list anywhere downstream is caught.

**Done when:** the four tests pass; `pytest packages/agentbundle/tests/unit/test_codex_projection_modes.py` exits 0; `grep -rn "codex.*allowed-prefixes\|allowed-prefixes.*codex" packages/agentbundle/agentbundle/` shows no hardcoded prefix-list-for-codex (everything is contract-derived); the path-jail accepts `.codex/agents/<name>.toml` and `.codex/hooks.json` writes at both scopes (no `safety.PathJailError` thrown for in-prefix paths).

---

### T6: Dropped-primitives warning rail — helpers + install handler emit

**Depends on:** T1

**Spec mapping:** AC8, AC9, AC10, AC11, AC17. Mode: TDD (helpers are pure; the install-handler hook is integration-shape but pins via stderr capture).

**Tests:**

New module `packages/agentbundle/tests/unit/test_install_dropped_primitives_warning.py`:

- `test_enumerate_dropped_primitives_codex_against_core` — `_enumerate_dropped_primitives(packs_dir / "core", "codex")` post-bump returns `{"command": N}` (where N = number of commands in `core`'s `.apm/commands/`). Agent + hook-wiring no longer appear because they project natively post-T1.
- `test_enumerate_dropped_primitives_copilot_against_core` — returns `{"agent": N, "command": M, "hook-wiring": P}` with the right counts (all three drop types fire).
- `test_enumerate_dropped_primitives_kiro_against_core` — returns `{"command": N}` only (kiro drops just `command`).
- `test_enumerate_dropped_primitives_claude_code_returns_empty` — claude-code has no `dropped` modes; returns `{}` regardless of pack content.
- `test_enumerate_dropped_primitives_skills_only_pack_returns_empty` — pack with only `.apm/skills/` against copilot returns `{}` (no drop-eligible types present in the pack).
- `test_enumerate_compatible_primitives_codex_post_bump` — returns `["skill", "agent", "hook-body", "hook-wiring"]` (the non-dropped types for codex post-T1, filtered to types the pack ships).
- `test_warning_text_one_type_singular_N1` — one-type drop with N=1 produces `warning: pack core ships 1 command that codex projects as 'dropped'; ...`. Singular form, no `s`.
- `test_warning_text_one_type_plural` — one-type drop with N>1 produces `... ships 3 commands that codex projects as 'dropped'; ...`. Plural form, no comma, no "and".
- `test_warning_text_two_type` — two-type drop produces `... ships 2 agents and 3 commands that copilot projects as 'dropped'; ...` (`"X and Y"` shape).
- `test_warning_text_three_type_serial_comma` — three-type drop produces serial-comma form `... ships 2 agents, 3 commands, and 1 hook-wiring that copilot projects as 'dropped'; ...`. Singular for the N=1 entry; serial-comma + final "and" overall.
- `test_warning_text_zero_count_elision` — counts `{"agent": 0, "command": 3, "hook-wiring": 0}` produces the one-type line, not a three-type line with two zeros.
- `test_short_circuit_single_scope_repeat` — call install handler twice for same `(root, pack, adapter, scope)` in same Python process; second call emits no warning.
- `test_short_circuit_dual_scope_independent` — dual-scope install where repo and user have different resolved adapters; assert one warning per scope; assert each scope is independently silenceable on repeat (silencing repo doesn't silence user).
- `test_dual_scope_same_adapter_both_scopes_fires_twice` — dual-scope install where repo and user resolve to the same adapter with the same dropped types; assert two warnings fire (one per scope) per AC10's "same wording, both fire" pin. Failure of this test signals an over-eager dedup that breaks the per-scope contract.
- `test_warning_silent_for_claude_code` — install `core` via claude-code; assert no warning stderr.

**Approach:**

- Add module-level state at `packages/agentbundle/agentbundle/commands/install.py`:
  ```python
  _DROPPED_WARNING_SEEN: set[tuple[str, str, str, str]] = set()
  ```
  Plus a `_clear_dropped_warning_seen()` test helper alongside `_clear_inband_detection_seen()` (the PR #141 precedent).
- Add `_enumerate_dropped_primitives(pack_dir, adapter)` helper: load the adapter contract via the existing `_contract_data()` (or equivalent — implementer verifies the function name); collect `primitive` field values from entries where `mode == "dropped"`; for each, count files in `<pack_dir>/.apm/<primitive-type-dirname>/` where dirname is the plural form (skills/agents/hooks/hook-wiring/commands). Return `{type: count}` dict with non-zero entries only.
- Add `_enumerate_compatible_primitives(pack_dir, adapter)` helper: similar walk but for `mode != "dropped"`, filtered to types the pack actually ships.
- Add `_format_dropped_warning(pack_name, adapter, dropped_counts, compatible_types) -> str` formatter producing the AC10 pinned wording.
- Hook the warning into the install handler at the **pre-write barrier point**: after Step 5's `scopes_to_install` is finalised, each scope's target adapter is resolved (`repo_target_adapter` and/or `user_target_adapter` depending on which scopes are in the plan), AND Step 5's per-scope plan-list (`plans`) is built (loop at install.py around line 463). Before Step 6's pre-flight rails fire and before Step 9's writes. (Name the symbolic Step boundary in code comments, not line numbers — line numbers drift with neighbour edits.)
- **Dual-scope handling.** For each scope in `scopes_to_install`, evaluate the warning condition with that scope's resolved adapter. Two scopes → at most two warnings (one per scope) — each silenceable independently via the four-tuple `(root, pack_name, adapter, scope)` short-circuit key.
- Short-circuit via `_DROPPED_WARNING_SEEN: set[tuple[str, str, str, str]]` on repeat calls within the same process. Test helper `_clear_dropped_warning_seen()` exposed alongside the PR #141 precedent `_clear_inband_detection_seen()`.

**Done when:** all 12 unit tests in the new module pass; existing tests in the install handler stay green.

---

### T7: Eight packs bump to v0.8

**Depends on:** T1, T4, T5, T6

**Spec mapping:** AC12. Mode: goal-based check (TOML edit per pack).

**Tests:**

New module `packages/agentbundle/agentbundle/build/tests/test_shipped_packs_v08_declarations.py`:

- For each of the eight pack names: load `packs/<pack>/pack.toml`, assert `[pack.adapter-contract] version == "0.8"`.
- `make build-self FORCE=1` is a noop on the eight packs' projections after the bump.

**Approach:**

- For each pack in `(atlassian, figma, converters, contracts, core, governance-extras, user-guide-diataxis, monorepo-extras)`, edit `packs/<pack>/pack.toml`: bump `[pack.adapter-contract] version = "0.7"` → `"0.8"`. No other field changes.
- Run `make build-self FORCE=1` and verify `git status --short` is clean modulo the eight `pack.toml` edits.

**Done when:** the eight-pack test passes; `make build-self FORCE=1` produces a clean working tree.

---

### T8: End-to-end install integration tests

**Depends on:** T4, T5, T6, T7

Folds in former-T5's integration assertions (install handler routing through the build pipeline correctly projects codex agents + hook-wiring at the new targets), now that T5 collapsed to runtime-accessor checks only.

**Spec mapping:** AC18. Mode: TDD (integration; install handler as black box).

**Tests:**

New module `packages/agentbundle/tests/integration/test_install_dropped_primitives_warning.py`. Per shipped adapter against the real `core` pack:

- **Codex projection end-to-end.** `agentbundle install --pack core --scope repo --adapter codex <repo>`; assert `<repo>/.codex/agents/<agent>.toml` exists for each agent in `core/.apm/agents/`; assert `<repo>/.codex/hooks.json` exists with merged entries; assert `<repo>/.agents/skills/<skill>/SKILL.md` exists (RFC-0009 path unchanged); assert stderr contains the warning for `command(s)` only (agent / hook-wiring no longer dropped post-bump).
- **Copilot warning end-to-end.** Install `core` via `--adapter copilot --scope repo`; assert rc 0; assert stderr names all three counts (`agent(s)`, `command(s)`, `hook-wiring(s)`); assert skills + hook-bodies land at copilot's targets.
- **Kiro warning end-to-end.** Install `core` via `--adapter kiro --scope repo`; assert stderr names `command(s)` only.
- **Claude-code silence end-to-end.** Install `core` via `--adapter claude-code --scope repo`; assert stderr has no warning line (claude-code projects everything).
- **Skills-only pack silence.** Install `governance-extras` (skills-only) via `--adapter copilot --scope repo`; assert no warning (pack doesn't ship drop-eligible types).

**Approach:**

- Reuse the existing integration-test fixture pattern (`tmp_path` + monkeypatched `HOME` + `<repo>` argument) from PR #141's `test_install_repo_scope_per_adapter.py`.
- Each case asserts on-disk projection AND stderr content; both are observable outcomes of the install.

**Done when:** every case passes; `pytest packages/agentbundle/tests/integration/` exits 0.

---

### T9: Sibling-spec amendment + ROADMAP

**Depends on:** T1, T7

**Spec mapping:** AC14, AC15. Mode: manual QA + goal-based grep.

**Tests:**

- Goal-based grep: `docs/specs/distribution-adapters/spec.md` Changelog gains a v0.7 → v0.8 entry naming the codex projection additions and the new `codex-agent-toml` mode.
- Goal-based grep: `docs/backlog.md` contains a `dropped-primitives-coverage` section.

**Approach:**

- Edit `docs/specs/distribution-adapters/spec.md`: append a Changelog entry naming this spec's contract bump and the new mode.
- Edit `docs/backlog.md`: add a `dropped-primitives-coverage` heading section mirroring the layout of the existing `repo-scope-per-adapter-projection` section.

**Done when:** the two grep cases pass; manual read confirms each commitment landed.

---

### T10: Gates pass — final sweep

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T9

**Spec mapping:** AC19, AC20, AC21, AC22. Mode: goal-based check (gates).

**Tests:**

- `pytest packages/agentbundle/` exits 0.
- `make build-self FORCE=1 && git status --short` shows no changes.
- `python3 tools/hooks/pre-pr.py` exits 0.
- CI replication of `build-check` linux + windows, `pytest` windows, `docs` lint suite — verified post-push on the PR.

**Approach:**

- Sweep for any test that touched the v0.7 pack contract version, the codex projection entries, or the `_data/adapter.toml` shape. Update each to match v0.8 expectations.
- Run the full local gate suite. Resolve any drift.
- Commit; push; verify CI green.

**Done when:** all four local gates pass; CI on the open PR is green.

## Rollout

This spec ships behind no flag. The contract bump v0.7 → v0.8 is the gate: any v0.8 pack at codex routes through the new `.codex/agents/` and `.codex/hooks.json` projections; any pack at `< v0.8` continues through the legacy codex path (agents + hook-wiring drop silently per the prior contract; the warning rail fires for them via the dynamic trigger). **Adopter-facing behaviour change:** post-merge, a codex adopter installing any of the eight shipped packs at repo scope gets agents + hook-wiring projected natively where they used to be silently dropped; the warning rail visibly names what's still dropped (codex `command`, kiro `command`, copilot's three) on every other adapter/pack combination.

**Reversible.** If a regression surfaces post-merge, revert the implementation PR (the contract bump reverts to v0.7; codex projection entries revert to `dropped`; the eight packs' contract version reverts). No data migration; no persistent state change.

## Risks

- **`codex-agent-toml` serialiser correctness.** Pure conversion logic but the TOML multi-line basic-string emission has edge cases (embedded triple-quotes, leading/trailing whitespace). **Mitigation:** unit tests in T2 cover the load-bearing cases; integration test in T6 round-trips through `tomllib.loads` to catch any malformed output.
- **Codex hooks.json schema drift.** OpenAI may evolve the hooks.json shape after this spec ships; our `merge-json` mode merges into the `hooks` key without validating sub-shapes. **Mitigation:** spec documents the assumed shape (`event → matcher group → handlers`) and cites the upstream docs URL with the 2026-05-26 fetch date. A future contract bump can pin a hook-wiring schema if OpenAI breaks the current shape.
- **Eight packs bumping in one PR.** Per RFC-0012 precedent — risk is a typo in one of the eight breaks `agentbundle validate` for that pack. **Mitigation:** T5's per-pack test loads each `pack.toml` via `tomllib.loads` and asserts the bumped version; `make build-self FORCE=1` is the second belt.
- **Warning noise.** If too many adopters install `core` via codex/kiro/copilot, the warning may become learned-ignored. **Mitigation:** the warning fires once per `(root, pack, adapter, scope)` per session via short-circuit. If telemetry later shows the warning is ignored, a future RFC can add `--accept-degraded` to silence + a confirmation gate (Option 2 from the design discussion).
- **Codex `command` drop is residual and may not have a clean fix.** The OpenAI deprecation of custom-prompts in favour of skills means commands can't migrate trivially. **Mitigation:** the warning rail makes this visible; pack authors can choose to omit commands from codex-targeted packs or accept the drop.
- **v0.7→v0.8 codex re-projection requires a documented manual migration.** Adopters who installed a multi-primitive pack via `--adapter codex` in the v0.7 window have a state row + skills + hook-bodies on disk but no `.codex/agents/` or `.codex/hooks.json` (those types were `dropped`). Running `agentbundle install` again hits Step 4a's `already installed; use 'upgrade'` refusal; `--force` does NOT auto-detect this case (AC24(b) shape-mismatch fires on dist-tree files only); `agentbundle upgrade` at repo scope uses the dist-tree renderer per RFC-0012's Ask-first surface, so it doesn't re-project under the new contract either. **Mitigation:** the explicit two-step path is the documented migration (`agentbundle uninstall --pack <pack> --scope repo .` then `agentbundle install --pack <pack> --scope repo --adapter codex .`). Auto-detection of this case is named as a follow-on; getting `--force` semantics wrong here would strand adopters with partial installs.

## Changelog

- 2026-05-26 — Initial Drafting. Spec follows from the warning-rail design discussion 2026-05-26; broader scope (codex contract bump + warning rail across three adapters) per adopter direction. Originally eight tasks; re-planned twice. **Round-1 re-plan** (post-T1-EXECUTE-attempt): the build pipeline (`make build`) has its own per-adapter codex.py module with hardcoded `direct-directory` / `direct-file` mode handlers — the spec's "no code change beyond the contract entry" claim for codex hook-wiring was wrong. Restructured: split the projection helpers (`merge-json`, `codex-agent-toml`) into shared modules under `build/projections/` (T2 + T3); wire the build-pipeline `codex.py` (T4) to dispatch the new modes via the shared helpers. **Round-2 re-plan** (post-pre-EXECUTE review of round-1 amendment): the install handler routes through `render.py` → `agentbundle.build.main.run_recipe` → `build/adapters/codex.py` — there is **no independent install-side projection-mode dispatcher**. The originally-proposed T5 ("install-handler render.py wiring") was phantom dispatch against a non-existent surface; collapsed T5 into runtime-accessor checks only (verify `_adapter_allowed_prefixes_*` flow through the contract data; the actual codex projection at install time *is* T4's build-pipeline dispatcher). T1 also extended to bump `adapter.schema.json`'s mode-enum to admit `codex-agent-toml` (without it, schema-validated contract loads reject v0.8 on first run). Final shape: 10 tasks; T2/T3 independent siblings; T4 is the sole dispatcher; T5 is runtime-accessor pin only; the rest sequential. Plan re-reviewed pre-EXECUTE per work-loop discipline.
- 2026-05-26 — **Round-3 re-plan** (post-pre-EXECUTE adversarial review at EXECUTE entry). Three blockers fixed without restructuring tasks: (a) spec § Always do at line 30 acknowledged that `packages/agentbundle/agentbundle/build/projections/` already exists with five sibling modules — T2 adds a sixth, not creates the package; plan T2 Approach updated to drop conditional `__init__.py` creation; (b) spec § Always do at line 31 collapsed to single-location serialiser (build-pipeline dispatcher only) matching round-2's conclusion that no install-side dispatcher exists; (c) AC10 and plan T6 Approach corrected the "Step 6 plan loop" reference — the plan-loop is in Step 5 of `install.py` (line 463), Step 6 is the kiro-only user-scope pre-flight rail. The pre-write barrier is "after Step 5's plans list built, before Step 6's pre-flight and Step 9's writes." Concern 4 also addressed: T1 test list explicitly notes that the schema's projection-mode enum is global across adapters, so `merge-json` already validates at the codex site without a per-site enum edit.
