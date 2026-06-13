# Plan: gemini-full-parity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

A new `gemini` adapter that mirrors the `copilot-full-parity` / `cursor-full-parity`
shape: a contract block drives projection, a new projection-mode module handles the
one tool-specific serialisation (TOML commands), and the adapter module ties it
together — all in **one PR, one contract bump (`v0.12 → v0.13`)**. The Cursor
adapter (RFC-0026) merged at v0.11 (#273) and `copilot-skills-and-web` then merged
at v0.12 (#272), so this stacks on the post-copilot main, reusing Cursor's
proven scope-agnostic-emission + install-time prefix-rewrite pattern and following its
exact hand-maintained-site touch-list (see Dependencies & integration). Order of
operations: lock the contract
surface first (T1), then the command-mode module it references (T2), then the
adapter module (T3), then the `.gemini/settings.json` single-merge + user-scope
rewrite (T4), then opt every pack in (T5), then tests + CI wiring (T6), then the
docs/distribution-only surface (T7). The **riskiest part** is the
`.gemini/settings.json` merge carrying **two** managed keys (`hooks` + `context`)
without clobbering adopter content — and the fail-closed command transform, which
must error rather than emit a broken command.

## Constraints

- **RFC-0027 / ADR-0016** — the seven decisions: full-parity projection, keep+map
  `tools:`, tier-preserving model map, new `gemini-command-toml` mode, `AGENTS.md`
  `context.fileName` bridge, zero-drop hook-event map, distribution-only.
- **RFC-0026 / ADR-0015 (Cursor)** — **merged** at v0.11 (#273); `copilot-skills-and-web`
  then merged at **v0.12** (#272, no ADR/RFC number); this stacks on the post-copilot
  main at **v0.13** (ADR-0016) and reuses Cursor's emission + prefix-rewrite pattern +
  its hand-maintained-site touch-list. Numbers are now pinned.
- **`copilot-full-parity` / RFC-0024 / ADR-0013** — the pattern mirrored:
  projection-mode modules under `build/projections/`, the explicit alias table
  that fails the build on an unmapped name, dual-copy contract, atomic bump.
- **RFC-0011** — `allowed-adapters`; opted into all packs here.
- **RFC-0004 / ADR-0004 / ADR-0002 / RFC-0005** — atomicity, per-adapter
  projection, scope dimension, `merge-json`/user-scope-hook precedent.

## Construction tests

Per-task tests live under **Tasks**. Cross-cutting:

**Integration tests:**
- Full projection of a representative pack (skills + agents + commands + hook
  bodies + wiring) to `.gemini/*` at repo scope, and the same to `~/.gemini/*` at
  user scope (T3 + T4).
- `.gemini/settings.json` merge against a pre-populated file with a foreign key:
  both managed keys (`hooks`, `context`) land, foreign key survives (T4).

**Manual verification:** none beyond per-task + CI gates (`make build-check`,
`make build-self`).

## Design (LLD)

Stack: Python; the `agentbundle` build package (no `docs/architecture/reference.md`
present — stack detected from the repo). Adapters are contract-driven projection
modules; the contract is `_data/adapter.toml` + `_data/adapter.schema.json`,
byte-mirrored to `docs/contracts/`.

### Design decisions
- **Reuse, don't invent.** Exactly one new projection mode (`gemini-command-toml`)
  and one static `context` emission; everything else reuses existing modes
  (`direct-directory`, `direct-file`) and a bespoke settings-merge helper.
  Rejected: a bespoke agent-projection mode (Copilot's `copilot-agent-md`) —
  Gemini agents are Markdown + frontmatter like Kiro-IDE, so `direct-file` + a
  `frontmatter-mapping` suffices. *Traces to: AC2, AC4 · adapter.toml.*
- **Cursor hook-body model (changed 2026-06-11).** `hook-body` → `.gemini/hooks/`
  (not the legacy `tools/hooks/`), so it is fenced by the single `.gemini/` prefix
  at **both** scopes and the settings command is rewritten `tools/hooks/`→
  `.gemini/hooks/` (the `cursor.py` `_rewrite_hook_body_path` precedent). Rejected:
  `tools/hooks/` at repo + a claude-code-style scope-conditional `target.user`
  table + the v0.3 user-scope-hooks machinery — heavier, and it would leave the
  hook body outside `~/.gemini/` at user scope (the original AC2/AC10 contradiction
  the reviewer flagged). The Cursor model makes **every** target land under
  `.gemini/` at both scopes, which is what lets `core` (a hook-shipping pack)
  install at user scope. *Traces to: AC2, AC3, AC9, AC10.*
- **Single settings merge via a bespoke helper.** `hooks` wiring **and** the static
  `context` bridge write to the **same** `.gemini/settings.json` in one managed-merge.
  The generic `merge-json` module carries exactly one primitive-driven `managed-key`
  and cannot emit a primitive-less static value, so the `gemini` adapter owns a
  `_project_settings_json` helper (the `cursor.py` `_project_hooks_json` shape),
  run as a post-pass over all packs. It builds `hooks` from the `hook-wiring`
  source (event-mapped, command path-rewritten) and `context = {"fileName":
  <list>}` where `<list>` is read from a new contract field `context-filenames`
  on the gemini hook-wiring rule. **Single-writer (cursor model):** the file is
  written **only when the pack ships hook-wiring** — repo-scope install writes
  merge-json targets whole-file (no install-time JSON merge; `install.py:858-886`)
  and the adapter renders to an isolated tempdir, so emitting a settings.json for
  every pack would *overwrite*/clobber another pack's hooks. The `context` bridge
  rides in the hook-wiring write; `core` ships both wiring and `AGENTS.md` (seed),
  so the bridge lands when the file it points at exists. Rejected: emit context
  for every pack (clobbers under whole-file overwrite); a second static-file
  emitter for `context` (two writers to one file); a `merge_json.py` change to
  carry a static key (couples a shared module to one adapter); making install.py
  merge-json-aware at repo scope (large change to shared machinery, out of scope).
  *Traces to: AC8.*
- **Fail-closed commands.** Translate single-injection; **raise** on anything
  `{{args}}` can't express. Rejected: log-and-degrade (emits a broken command).
  *Traces to: AC7.*

### Interfaces & contracts
- `[adapter.gemini]` block: 5 `projection` rows (skill/agent/hook-body/hook-wiring/
  command) + a `[adapter.gemini.projections.kiro-ide-hook] mode = "dropped"` table
  entry (Kiro-only; the Cursor/kiro-ide/kiro-cli precedent — so gemini adds **6**
  primitive×adapter pairs, total `38→44`), `[adapter.gemini.scope]` (allowed-prefixes
  `[".gemini/", ".agentbundle/"]` identical at both scopes), `frontmatter-mapping =
  "gemini-agent-frontmatter"`, the hook-event map, and `context-filenames =
  ["AGENTS.md", "GEMINI.md"]` on the hook-wiring rule (drives the `context` bridge).
  The hook-event map is keyed on the **Claude-Code PascalCase source events** the
  shipped wiring uses (`SessionStart`, `UserPromptSubmit`, `PreToolUse`,
  `PostToolUse`, `Stop`, `SessionEnd`) — **not** the lowercase Kiro
  `agent-event-vocabulary` — mirroring `copilot-hooks-json`'s `_EVENT_MAP`, but
  **fail-closed** on an unmapped event (the copilot precedent, *unlike* cursor's
  fail-open drop-with-log).
- `gemini-agent-frontmatter`: `name`/`description` passthrough; `tools` `values`
  map (`normalize = "to-list"`, de-duplicating collided targets like `Edit`+
  `MultiEdit`→single `replace`); `model` `values` map; absent `model` → omitted.
- `gemini-command-toml` admitted to the `mode` enum at every enumerating site in
  `adapter.schema.json`.
- All edits dual-copied to `docs/contracts/`; `test_contract_files_byte_identical`
  is the guard. *Traces to: AC2, AC4, AC5, AC6, AC9, AC13 · adapter.toml/schema.*

### Dependencies & integration
**Hand-maintained sites beyond the contract** — the exact touch-list Cursor's
#273 worked, confirmed against its diff (a new adapter needs *all* of these, or a
CI-only-root test red-fails):
- `build/adapters/__init__.py` — **both** registries (callable + module-keyed) gain `gemini`.
- `build/adapters/gemini.py` — the new module (mirror `cursor.py`).
- `commands/install.py` — adapter dispatch branch in **both** `_render_for_repo_scope`
  and `_render_for_user_scope` + the `gemini-command-toml` mode dispatch. Like Cursor,
  `.gemini/` is identical at both scopes, so **no gemini-specific prefix rewrite** and
  **no `scope.py` edit** (the `contract_version_at_least` helper already exists on main);
  generic user-rooting lands the `.gemini/…` relpaths under `~`.
- `build/tests/test_contract.py` — `ALL_ADAPTERS` set (+`gemini`) + pair-count
  (`38→44`) + version (`0.13`) + the docstring prose (`:5` "× N adapters" / `:150`
  per-adapter math) updated to match.
- `tests/unit/test_install_argparse_adapter_flag.py` — shipped-adapter tuple (`gemini`
  sorts after `cursor`, before `kiro`).
- `tests/unit/test_contract_v0_3_schema.py` — version/enum assertion.
- `tests/integration/test_multi_pack_install.py` — adapter tuple (auto-derived) + a
  `_skill_path` branch (`.gemini/skills/<n>/SKILL.md`) + the
  `_ADAPTERS_WHERE_GOV_ORPHAN_SCAN_FIRES` set (+`gemini` — gemini's skill dir-shape
  matches cursor/claude/kiro/codex, so the per-pack scanner fires).
- `build/tests/test_adapter_kiro_ide.py` + `test_adapter_cursor.py` — per-adapter
  contract-version pins (`"0.12"` → `"0.13"`).
- `.github/workflows/build-check.yml` — CI wiring (the new `test_adapter_gemini.py`
  step; **`build-check.yml` only**, per the Cursor precedent — the Windows workflow
  runs no `test_adapter_*` suite).
- `adapter.schema.json` — `gemini-command-toml` mode enum (Gemini-specific; Cursor needed none).
- `packs/*/pack.toml` `allowed-adapters` gains `gemini` (7 explicit-list packs; the
  4 list-less packs admit it by default at both scopes); a coverage test resolves
  `--adapter gemini` for all 11 packs × {repo, user}. The marketplace aggregation
  (`make build-self`) and drift gate (`make build-check`) stay green. *Traces to:
  AC1, AC4, AC10, AC11, AC13.*

### Failure, edge cases & resilience
- Unmapped tool → build-time **log**, dropped from the list (no silent omit).
- Command needing positional/multi-injection args → build **error** (fail-closed).
- Pre-populated `.gemini/settings.json` with foreign keys → managed-key merge
  preserves them.
- Unrecognised source hook event (not in the map) → build **error** (fail-closed,
  the `copilot-hooks-json` precedent), never a silent drop. A source `matcher`
  (regex on `BeforeTool`/`AfterTool`) passes through unchanged. *Traces to: AC5, AC7, AC8, AC9.*

## Tasks

### T1: Contract block + schema mode enum + version bump (dual-copied)

**Depends on:** none

**Tests:**
- `test_contract` validates the new `[adapter.gemini]` block (projections, scope, frontmatter-mapping, hook-event map). [AC2, AC3, AC5, AC6, AC9]
- `gemini-command-toml` present in the `mode` enum at every enumerating site. [AC4]
- `test_contract_files_byte_identical` green (`_data/*` ↔ `docs/contracts/*`). [AC13]
- All `test_contract*.py` version assertions updated to the new version and green; no lexical version-compare regression. [AC13]

**Approach:**
- Add `[adapter.gemini]` to `packages/agentbundle/agentbundle/_data/adapter.toml`: 5 projection rows (skill→`.gemini/skills/`, agent→`.gemini/agents/` + `gemini-agent-frontmatter`, hook-body→`.gemini/hooks/`, hook-wiring→`merge-json` `.gemini/settings.json` managed-key `hooks` + `hook-event-map` + `context-filenames`, command→`gemini-command-toml` `.gemini/commands/`), a `[adapter.gemini.projections.kiro-ide-hook] mode = "dropped"` table entry, `[adapter.gemini.scope]` (`allowed-prefixes` `[".gemini/", ".agentbundle/"]` both scopes), `gemini-agent-frontmatter` (`tools` + `model` `values` maps), the hook-event map.
- Add `gemini-command-toml` to the `mode` enum at every site in `_data/adapter.schema.json` (4 sites).
- Dual-copy both to `docs/contracts/adapter.toml` + `docs/contracts/adapter.schema.json`.
- Bump the contract version **v0.12 → v0.13** (main is at v0.12 post-copilot-skills-and-web); sweep `test_contract.py` (`ALL_ADAPTERS` +`gemini`, pair-count `38→44`, mode-enum +`gemini-command-toml`, version, **and the docstring prose** at `:5`/`:150`), `test_contract_v07.py`/`test_contract_v08.py` (numeric `>=` compares — safe, no edit), `tests/unit/test_contract_v0_3_schema.py`, the per-adapter version pins in `build/tests/test_adapter_kiro_ide.py` + `test_adapter_cursor.py` (both `assertEqual(version, "0.12")`), and any cohort/adapter-support version pin.

**Touches:** packages/agentbundle/agentbundle/_data/adapter.toml, packages/agentbundle/agentbundle/_data/adapter.schema.json, docs/contracts/adapter.toml, docs/contracts/adapter.schema.json, packages/agentbundle/agentbundle/build/tests/test_contract*.py

**Done when:** `python -m pytest packages/agentbundle/agentbundle/build/tests/test_contract*.py` is green and the new block validates.

### T2: `gemini-command-toml` projection-mode module (fail-closed)

**Depends on:** T1

**Tests (TDD):**
- Single-injection command: `$ARGUMENTS`→`{{args}}`, body→TOML `prompt`, frontmatter `description`→TOML `description`. [AC7]
- Subdir namespacing: `git/commit.md` → `.gemini/commands/git/commit.toml`. [AC7]
- **Error path:** a command body using positional `$1`/`$2` or multiple distinct injections **raises a build error** (no file emitted). [AC7]
- A command with no `description` frontmatter omits the key (Gemini generates one). [AC7]

**Approach:**
- New module `packages/agentbundle/agentbundle/build/projections/gemini_command_toml.py` mirroring the `codex-agent-toml` module shape; emit valid TOML (multi-line `prompt`).
- Dispatch the mode **inside `gemini.py`'s `_project_single`** (the `codex.py:149 elif mode == "codex-agent-toml"` precedent — modes are consumed by the adapter, **not** centrally in `install.py`; install.py dispatches by adapter name only, wired in T4). So this task touches only the new module; the gemini.py `elif` arm lands with T3.

**Touches:** packages/agentbundle/agentbundle/build/projections/gemini_command_toml.py

**Done when:** the TDD suite (happy + error paths) is green.

### T3: `gemini` adapter module + registry

**Depends on:** T1, T2

**Tests (integration + TDD):**
- Adapter projects each primitive to its contract target at repo scope (skill→`.gemini/skills/<n>/`, agent→`.gemini/agents/<n>.md`, hook-body→`.gemini/hooks/`, command→`.gemini/commands/<n>.toml`). [AC2]
- `gemini-agent-frontmatter`: `tools` name-mapped (`Read→read_file` … `LS→list_directory`); an unmapped tool dropped **with a log**. [AC5]
- `model` tier-mapped (`opus→gemini-2.5-pro`/`sonnet→gemini-2.5-flash`/`haiku→gemini-2.5-flash-lite`); absent `model`→omitted. [AC6]

**Approach:**
- `packages/agentbundle/agentbundle/build/adapters/gemini.py` driven by the contract block; register in `adapters/__init__.py` `registry`.

**Touches:** packages/agentbundle/agentbundle/build/adapters/gemini.py, packages/agentbundle/agentbundle/build/adapters/__init__.py

**Done when:** the adapter projects all five primitives correctly and the frontmatter mapping tests are green.

### T4: `.gemini/settings.json` single managed-merge (hooks + context) + user-scope dispatch

**Depends on:** T1, T3

**Tests (integration):**
- Hook-wiring + `context.fileName = ["AGENTS.md", "GEMINI.md"]` land in **one** `.gemini/settings.json` (managed keys `hooks` + `context`). [AC8]
- A pack with **no** hook-wiring writes **no** `.gemini/settings.json` (the cursor single-writer model — repo-scope install overwrites merge targets whole-file, so a per-pack settings.json would clobber another pack's hooks); the `context` bridge rides in the hook-wiring write (core ships both). [AC8]
- Merge against a **pre-populated** `settings.json` with a foreign top-level key: foreign key survives; both managed keys present. [AC8]
- Hook-event map applied from the PascalCase source keys (`SessionStart→SessionStart`, `UserPromptSubmit→BeforeAgent`, `PreToolUse→BeforeTool`, `PostToolUse→AfterTool`, `Stop→AfterAgent`, `SessionEnd→SessionEnd`); the shipped `session-start.toml` wiring (`[[hooks.SessionStart]]`) lands correctly with its command path-rewritten `tools/hooks/`→`.gemini/hooks/`; an unrecognised event **fails the build**; a `matcher` passes through. [AC9]
- `--scope user`: every target (incl. hook bodies at `.gemini/hooks/`) lands under `~/.gemini/` via the generic user-rooting (no gemini-specific home logic). [AC10]

**Approach:**
- Add a bespoke `_project_settings_json` helper in `gemini.py` (the `cursor.py` `_project_hooks_json` shape) run as a post-pass over all packs: build `hooks` from `hook-wiring` source (event-mapped fail-closed, command path-rewritten `tools/hooks/`→`.gemini/hooks/`) + static `context` from the rule's `context-filenames`; read-merge-write `.gemini/settings.json` preserving foreign keys; emit `context` unconditionally.
- Add the `gemini` dispatch branch to **both** `_render_for_repo_scope` and `_render_for_user_scope` in `commands/install.py` (no prefix-rewrite — `.gemini/` is identical at both scopes, the Cursor pattern).

**Touches:** packages/agentbundle/agentbundle/build/adapters/gemini.py, packages/agentbundle/agentbundle/commands/install.py

**Done when:** the merge + user-scope integration tests are green, including the foreign-key-survival and no-wiring-still-emits-context cases.

### T5: Opt `gemini` into `allowed-adapters` across all packs

**Depends on:** T1

**Tests (goal-based):**
- `gemini` present in the `allowed-adapters` list of the 7 packs that declare one. [AC11]
- **Coverage test:** `_resolve_target_adapter(adapter="gemini", scope=s, allowed_adapters=<pack's list-or-None>)` for **all 11 packs × {repo, user}** returns `"gemini"` (none refused). [AC11]
- `make build-check` green — no marketplace-aggregation or drift-gate regression. [AC11]

**Approach:**
- Append `"gemini"` to the 7 packs that declare an explicit `allowed-adapters` list (`architect`, `atlassian`, `contracts`, `converters`, `credential-brokers`, `figma`, `research`) — required at **both** scopes: a list-declaring pack refuses an unlisted `--adapter` even at repo scope (`install.py:2737-2762`), and at user scope every listed adapter must be user-scope-capable (`install.py:2720-2734`; `gemini` qualifies via its `[scope].user`).
- **Leave the 4 line-less packs untouched** (`core`, `governance-extras`, `monorepo-extras`, `user-guide-diataxis`): a list-less pack admits *any shipped adapter* at repo scope and *any user-scope-capable adapter* at user scope, so they already admit `gemini` at both scopes once it ships — adding an explicit list would **narrow** them (regression for every other adapter). Confirmed against `install.py:2737-2762` + `:2744-2752`.
- Bump pack versions only where the marketplace/drift gate requires it (per the non-projected-pack-bump-drifts-marketplace learning; mind `test_shipped_pack_manifests.py`'s per-pack version pins — `core`=0.12, others=0.8); run `make build-self` then `make build-check`.

**Touches:** packs/architect/pack.toml, packs/atlassian/pack.toml, packs/contracts/pack.toml, packs/converters/pack.toml, packs/credential-brokers/pack.toml, packs/figma/pack.toml, packs/research/pack.toml, marketplace.json

**Done when:** the 7 explicit-list packs list `gemini`, the coverage test confirms all 11 packs admit `gemini` at both scopes, and `make build-check` is green.

### T6: `test_adapter_gemini.py` + CI wiring + shipped-agent tool coverage

**Depends on:** T2, T3, T4

**Tests:**
- New `build/tests/test_adapter_gemini.py` consolidating the projection, frontmatter-mapping, command-transform, and settings-merge assertions. [AC14]
- Shipped-agent tool coverage: scan shipped agent frontmatter; assert every declared tool is in the `gemini-agent-frontmatter` `values` map (an unmapped tool surfaces, not silently drops). [AC5]
- Update every shipped-adapter/version-pinned assertion that red-fails on the bump [AC13]: `tests/unit/test_install_argparse_adapter_flag.py` (shipped tuple; `gemini` sorts after `cursor`, before `kiro`), `tests/unit/test_contract_v0_3_schema.py`, `build/tests/test_contract.py` (`ALL_ADAPTERS` + pair-count `38→44` + mode-enum + version + the `:5`/`:150` docstring prose), `tests/integration/test_multi_pack_install.py` (adapter tuple auto-derived + a `_skill_path` branch → `.gemini/skills/<n>/SKILL.md` + add `gemini` to `_ADAPTERS_WHERE_GOV_ORPHAN_SCAN_FIRES`), and the per-adapter version pins in `build/tests/test_adapter_kiro_ide.py` + `test_adapter_cursor.py` (both `assertEqual(version, "0.12")` → `"0.13"`).

**Approach:**
- Author `test_adapter_gemini.py` (mirror `test_adapter_cursor.py`); add it as an explicit `python -m pytest …test_adapter_gemini.py` step to `.github/workflows/build-check.yml` only — matching Cursor's #273, which wired `test_adapter_cursor.py` into `build-check.yml` alone; the Windows workflow runs no `test_adapter_*` suite.
- Run the **full** `pytest packages/agentbundle/` by hand to catch the CI-only-root assertions (`tests/unit/`, `tests/integration/`) and the adapter-test version pins the local gate skips.

**Touches:** packages/agentbundle/agentbundle/build/tests/test_adapter_gemini.py, packages/agentbundle/tests/unit/test_install_argparse_adapter_flag.py, packages/agentbundle/tests/unit/test_contract_v0_3_schema.py, packages/agentbundle/agentbundle/build/tests/test_contract.py, packages/agentbundle/agentbundle/build/tests/test_adapter_kiro_ide.py, packages/agentbundle/agentbundle/build/tests/test_adapter_cursor.py, packages/agentbundle/tests/integration/test_multi_pack_install.py, .github/workflows/build-check.yml

**Done when:** `test_adapter_gemini.py` is green locally, every shipped-adapter/version-pinned assertion above is updated and green under the full `pytest packages/agentbundle/`, and the new test is wired into `build-check.yml`.

### T7: Support-matrix correction + AGENTS.md reader line + distribution-only proof

**Depends on:** T3

**Tests (goal-based):**
- `docs/guides/_shared/reference/adapter-support.md` Gemini row corrected from "Universal layer" to its true tier (skill/subagent/command/hook native). [AC15]
- `gemini` **absent** from `SELF_HOST_ADAPTERS`; `make build-self` produces **no** `.gemini/` tree in this repo. [AC12]

**Approach:**
- Edit `docs/guides/_shared/reference/adapter-support.md` (repo-owned / `EXCLUDED_PATTERNS` — direct edit).
- Refine the Gemini CLI reader line in **root `AGENTS.md` directly** (line 4 already names Gemini CLI; reword to reflect native projection) **and** keep `packs/core/seeds/AGENTS.md:4` in sync. `AGENTS.md` is in `EXCLUDED_PATTERNS` and `_compose_agents_md` returns `None` when the on-disk file exists, so it is **not** projected — editing the root directly is correct and is *not* reverted by `build-self` (the `work-loop-light-mode` precedent: "root `AGENTS.md` is Manual — edited directly with its seed synced").
- Assert distribution-only: grep `SELF_HOST_ADAPTERS` excludes `gemini`; `make build-self` then `git status` shows no `.gemini/`.

**Touches:** docs/guides/_shared/reference/adapter-support.md, AGENTS.md, packs/core/seeds/AGENTS.md

**Done when:** the matrix reads correctly, the reader line is updated in both root and seed, and `make build-self` writes no `.gemini/` tree.

## Rollout

- **Delivery:** additive — a new adapter + an all-packs `allowed-adapters` opt-in. No migration of existing state; a Gemini adopter installs fresh. Reversible (remove the block + adapter + pack lines). Irreversible: none.
- **Infrastructure:** none.
- **External-system integration:** targets Gemini CLI's documented `.gemini/*` layout; no live service dependency.
- **Deployment sequencing:** Cursor (RFC-0026) merged at v0.11; `copilot-skills-and-web` then merged at v0.12; this stacks on the post-copilot main at v0.13 with the emission pattern + hand-maintained-site list settled. Done — the rebase onto the post-copilot main has been performed.

## Risks

- **Contract-bump test traps** — a version bump trips lexical version-compare bugs and stale assertions in CI-ungated test roots (incl. the shipped-adapter-tuple pin `tests/unit/test_install_argparse_adapter_flag.py`, which `gemini` reorders); run the **full** `pytest packages/agentbundle/` by hand on the bump, not just `build-check`.
- **Marketplace drift from the packs edit** — touching `pack.toml` files can drift `marketplace.json`; `build-check` red-fails until `build-self` is run. Bump only where the gate requires.
- **Rebase against merged Cursor + copilot-skills-and-web — resolved.** Cursor merged first at v0.11; `copilot-skills-and-web` (#272) then merged at v0.12; this branch was rebased onto the post-copilot main on 2026-06-11, the version pinned to **v0.13**, and the hand-maintained-site list reconciled (copilot's skill flip to `direct-directory` `.github/skills/` changes no gemini-side site). A *further* rebase before this PR merges must re-confirm no fourth adapter/contract bump landed in between (re-pin if so).

## Changelog

- 2026-06-11: initial plan (drafted after RFC-0027 Accepted + ADR-0016; built on the Cursor-lands-first coordination assumption).
- 2026-06-11: rebased after the Cursor adapter merged (#273, v0.11). Pinned contract bump to **v0.12** and ADR to **0016** (Cursor took 0015); un-hedged the now-real ADR-0015 references; expanded the hand-maintained-site list (T6 + Dependencies & integration) to match Cursor's actual diff — `test_multi_pack_install.py`, `test_contract_v0_3_schema.py`, both `__init__` registries; confirmed **no `scope.py` edit** needed (Cursor's `contract_version_at_least` helper is on main); spec → Approved.
- 2026-06-12: **EXECUTE-discovered correction — `.gemini/settings.json` is single-writer (cursor model).** Repo-scope install writes merge-json targets whole-file (no install-time JSON merge; `install.py:858-886`) and adapters render to an isolated tempdir, so emitting a settings.json for *every* pack (the "context even without wiring" refinement) **clobbers** another pack's hooks on multi-pack install — surfaced by `test_multi_pack_install`'s `[gemini]` orphan-clobber cases. Fix: write `.gemini/settings.json` only when the pack ships hook-wiring (exactly as `.cursor/hooks.json` / `.claude/settings.local.json`), carrying `hooks` + the `context` bridge in that one write; `core` ships both the wiring and `AGENTS.md` (seed), so the bridge lands when its target exists. AC8 + design decision + the relevant tests updated; reverted the now-unneeded `_SHARED_MERGE_TARGETS` test concession (gov-extras no longer writes the merge target).
- 2026-06-11: pre-EXECUTE adversarial review + user directive ("all packs get gemini at repo **and** user scope"). **(a)** `hook-body` moved `tools/hooks/`→`.gemini/hooks/` (the Cursor model) so every target is under `.gemini/` at both scopes — resolves the AC2/AC10 contradiction the reviewer flagged **and** lets `core` (a hook-shipping pack) install at user scope; settings command path-rewritten `tools/hooks/`→`.gemini/hooks/`. **(b)** Context-bridge mechanism made concrete: a bespoke `gemini.py` `_project_settings_json` post-pass writes `hooks`+`context` in one merge; `context.fileName` sourced from a new contract field `context-filenames`; emitted even when no pack ships wiring. **(c)** `kiro-ide-hook` declared `dropped` (table form) → pair-count pinned **44**; `ALL_ADAPTERS` + docstring prose updated. **(d)** AC11 extended to all-11-packs × both-scopes with a coverage test; `allowed-prefixes` `[".gemini/", ".agentbundle/"]` identical at both scopes. **(e)** `to-list` de-dup noted (Edit+MultiEdit→single replace); five non-shipped event mappings marked unit-table-verified.
- 2026-06-11: re-pinned after `copilot-skills-and-web` (#272) merged at **v0.12** on top of Cursor (per user direction). Contract bump moved **v0.12 → v0.13**; per-adapter version pins now read `"0.12"`; ADR-0016 / RFC-0027 unchanged (copilot-skills-and-web took no ADR/RFC number). Verified copilot's `skill` flip to `direct-directory` `.github/skills/` and `copilot-instruction` retirement touch no gemini-side site; pair count base re-confirmed at 38 (copilot's flip kept its pair count). Verified AC11 against `install.py:2737` — a pack with an explicit `allowed-adapters` list refuses an unlisted `--adapter` even at repo scope, so the 7 listed packs genuinely need `gemini` appended.
