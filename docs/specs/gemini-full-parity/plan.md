# Plan: gemini-full-parity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

A new `gemini` adapter that mirrors the `copilot-full-parity` / `cursor-full-parity`
shape: a contract block drives projection, a new projection-mode module handles the
one tool-specific serialisation (TOML commands), and the adapter module ties it
together — all in **one PR, one contract bump (`v0.11 → v0.12`)**. The Cursor
adapter (RFC-0026) is **already merged** at v0.11 (#273), so this stacks on its
proven scope-agnostic-emission + install-time prefix-rewrite pattern and follows its
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
- **RFC-0026 / ADR-0015 (Cursor)** — **merged** at v0.11 (#273); this stacks on it
  at **v0.12** (ADR-0016) and reuses its emission + prefix-rewrite pattern + its
  hand-maintained-site touch-list. Numbers are now pinned.
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
  (`direct-directory`, `direct-file`, `merge-json`). Rejected: a bespoke
  agent-projection mode (Copilot's `copilot-agent-md`) — Gemini agents are
  Markdown + frontmatter like Kiro-IDE, so `direct-file` + a `frontmatter-mapping`
  suffices. *Traces to: AC2, AC4 · adapter.toml.*
- **Single settings merge.** `hooks` wiring and the `context` bridge write to the
  **same** `.gemini/settings.json` in one managed-merge, not two passes — avoids a
  read-modify-write race and a double-rewrite. Rejected: a separate static-file
  emitter for `context` (two writers to one file). *Traces to: AC8 · user
  confirmation.*
- **Fail-closed commands.** Translate single-injection; **raise** on anything
  `{{args}}` can't express. Rejected: log-and-degrade (emits a broken command).
  *Traces to: AC7.*

### Interfaces & contracts
- `[adapter.gemini]` block: `projection` rows per primitive, `[adapter.gemini.scope]`,
  `frontmatter-mapping = "gemini-agent-frontmatter"`, and the hook-event map keyed on
  the **Claude-Code PascalCase source events** the shipped wiring uses (`SessionStart`,
  `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `SessionEnd`) — **not** the
  lowercase Kiro `agent-event-vocabulary` — mirroring `copilot-hooks-json`'s `_EVENT_MAP`.
- `gemini-agent-frontmatter`: `name`/`description` passthrough; `tools` `values`
  map (`normalize = "to-list"`); `model` `values` map; absent `model` → omitted.
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
- `commands/install.py` — adapter dispatch + the `gemini-command-toml` mode + the
  user-scope prefix rewrite for `~/.gemini/`. The existing rewrite seam covers it;
  the `contract_version_at_least` helper Cursor added to `scope.py` already exists
  on main, so **no `scope.py` edit** is needed here.
- `build/tests/test_contract.py` — `ALL_ADAPTERS` + pair-count + version assertions.
- `tests/unit/test_install_argparse_adapter_flag.py` — shipped-adapter tuple.
- `tests/unit/test_contract_v0_3_schema.py` — version/enum assertion.
- `tests/integration/test_multi_pack_install.py` — adapter tuple + a `_skill_path`
  branch (`.gemini/skills/<n>/SKILL.md`) + the gov-orphan-scan adapter set.
- `build/tests/test_adapter_kiro_ide.py` + `test_adapter_cursor.py` — per-adapter
  contract-version pins (`"0.11"` → `"0.12"`).
- `.github/workflows/build-check.yml` — CI wiring (the new `test_adapter_gemini.py`
  step; **`build-check.yml` only**, per the Cursor precedent — the Windows workflow
  runs no `test_adapter_*` suite).
- `adapter.schema.json` — `gemini-command-toml` mode enum (Gemini-specific; Cursor needed none).
- `packs/*/pack.toml` `allowed-adapters` gains `gemini` (7 explicit-list packs); the
  marketplace aggregation (`make build-self`) and drift gate (`make build-check`)
  stay green. *Traces to: AC1, AC4, AC10, AC11, AC13.*

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
- Add `[adapter.gemini]` to `packages/agentbundle/agentbundle/_data/adapter.toml`: projection rows (skill/agent/hook-body/hook-wiring/command), `[adapter.gemini.scope]`, `gemini-agent-frontmatter` (`tools` + `model` `values` maps), the hook-event map.
- Add `gemini-command-toml` to the `mode` enum at every site in `_data/adapter.schema.json`.
- Dual-copy both to `docs/contracts/adapter.toml` + `docs/contracts/adapter.schema.json`.
- Bump the contract version **v0.11 → v0.12** (main is at v0.11 post-Cursor); sweep `test_contract.py`/`test_contract_v07.py`/`test_contract_v08.py`/`tests/unit/test_contract_v0_3_schema.py`, the per-adapter version pins in `build/tests/test_adapter_kiro_ide.py` + `test_adapter_cursor.py` (both `assertEqual(version, "0.11")`), and any cohort/adapter-support version pin.

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
- Register the mode in the `commands/install.py` dispatch.

**Touches:** packages/agentbundle/agentbundle/build/projections/gemini_command_toml.py, packages/agentbundle/agentbundle/commands/install.py

**Done when:** the TDD suite (happy + error paths) is green.

### T3: `gemini` adapter module + registry

**Depends on:** T1, T2

**Tests (integration + TDD):**
- Adapter projects each primitive to its contract target at repo scope (skill→`.gemini/skills/<n>/`, agent→`.gemini/agents/<n>.md`, hook-body→`tools/hooks/`, command→`.gemini/commands/<n>.toml`). [AC2]
- `gemini-agent-frontmatter`: `tools` name-mapped (`Read→read_file` … `LS→list_directory`); an unmapped tool dropped **with a log**. [AC5]
- `model` tier-mapped (`opus→gemini-2.5-pro`/`sonnet→gemini-2.5-flash`/`haiku→gemini-2.5-flash-lite`); absent `model`→omitted. [AC6]

**Approach:**
- `packages/agentbundle/agentbundle/build/adapters/gemini.py` driven by the contract block; register in `adapters/__init__.py` `registry`.

**Touches:** packages/agentbundle/agentbundle/build/adapters/gemini.py, packages/agentbundle/agentbundle/build/adapters/__init__.py

**Done when:** the adapter projects all five primitives correctly and the frontmatter mapping tests are green.

### T4: `.gemini/settings.json` single managed-merge (hooks + context) + user-scope rewrite

**Depends on:** T1, T3

**Tests (integration):**
- Hook-wiring + `context.fileName = ["AGENTS.md", "GEMINI.md"]` land in **one** `.gemini/settings.json` (managed keys `hooks` + `context`). [AC8]
- Merge against a **pre-populated** `settings.json` with a foreign top-level key: foreign key survives; both managed keys present. [AC8]
- Hook-event map applied from the PascalCase source keys (`SessionStart→SessionStart`, `UserPromptSubmit→BeforeAgent`, `PreToolUse→BeforeTool`, `PostToolUse→AfterTool`, `Stop→AfterAgent`, `SessionEnd→SessionEnd`); the shipped `session-start.toml` wiring (`[[hooks.SessionStart]]`) lands correctly; an unrecognised event fails the build; a `matcher` passes through. [AC9]
- `--scope user`: every target lands under `~/.gemini/` via the existing prefix rewrite (no gemini-specific home logic). [AC10]

**Approach:**
- Emit the `hooks` wiring via `merge-json` (managed-key `hooks`) and the static `context` fragment into the **same** file in a single managed-merge.
- Confirm `commands/install.py` user-scope-prefix-rewrite covers `.gemini/` → `~/.gemini/`.

**Touches:** packages/agentbundle/agentbundle/build/adapters/gemini.py, packages/agentbundle/agentbundle/commands/install.py

**Done when:** the merge + user-scope integration tests are green, including the foreign-key-survival case.

### T5: Opt `gemini` into `allowed-adapters` across all packs

**Depends on:** T1

**Tests (goal-based):**
- `gemini` present in the `allowed-adapters` list of the 7 packs that declare one; `gemini` admissible for all 11 packs (the 4 line-less packs admit it by default at repo scope). [AC11]
- `make build-check` green — no marketplace-aggregation or drift-gate regression. [AC11]

**Approach:**
- Append `"gemini"` to the 7 packs that declare an explicit `allowed-adapters` list (`architect`, `atlassian`, `contracts`, `converters`, `credential-brokers`, `figma`, `research`).
- **Leave the 4 line-less packs untouched** (`core`, `governance-extras`, `monorepo-extras`, `user-guide-diataxis`): at repo scope `install.py` admits *any shipped adapter* for a pack with no list, so they already admit `gemini` once it ships — adding an explicit list would **narrow** them (regression for every other adapter). Confirmed against `install.py:2682-2698` ("Repo scope: any shipped adapter is admissible").
- Bump pack versions only where the marketplace/drift gate requires it (per the non-projected-pack-bump-drifts-marketplace learning); run `make build-self` then `make build-check`.

**Touches:** packs/architect/pack.toml, packs/atlassian/pack.toml, packs/contracts/pack.toml, packs/converters/pack.toml, packs/credential-brokers/pack.toml, packs/figma/pack.toml, packs/research/pack.toml, marketplace.json

**Done when:** the 7 explicit-list packs list `gemini`, all 11 packs admit it, and `make build-check` is green.

### T6: `test_adapter_gemini.py` + CI wiring + shipped-agent tool coverage

**Depends on:** T2, T3, T4

**Tests:**
- New `build/tests/test_adapter_gemini.py` consolidating the projection, frontmatter-mapping, command-transform, and settings-merge assertions. [AC14]
- Shipped-agent tool coverage: scan shipped agent frontmatter; assert every declared tool is in the `gemini-agent-frontmatter` `values` map (an unmapped tool surfaces, not silently drops). [AC5]
- Update every shipped-adapter/version-pinned assertion that red-fails on the bump [AC13]: `tests/unit/test_install_argparse_adapter_flag.py` (shipped tuple; `gemini` sorts before `kiro`), `tests/unit/test_contract_v0_3_schema.py`, `build/tests/test_contract.py` (`ALL_ADAPTERS` + pair-count + version), `tests/integration/test_multi_pack_install.py` (adapter tuple + a `_skill_path` branch → `.gemini/skills/<n>/SKILL.md`; check the gov-orphan-scan adapter set), and the per-adapter version pins in `build/tests/test_adapter_kiro_ide.py` + `test_adapter_cursor.py` (both `assertEqual(version, "0.11")` → `"0.12"`).

**Approach:**
- Author `test_adapter_gemini.py` (mirror `test_adapter_cursor.py`); add it as an explicit `python -m pytest …test_adapter_gemini.py` step to `.github/workflows/build-check.yml` only — matching Cursor's #273, which wired `test_adapter_cursor.py` into `build-check.yml` alone; the Windows workflow runs no `test_adapter_*` suite.
- Run the **full** `pytest packages/agentbundle/` by hand to catch the CI-only-root assertions (`tests/unit/`, `tests/integration/`) and the adapter-test version pins the local gate skips.

**Touches:** packages/agentbundle/agentbundle/build/tests/test_adapter_gemini.py, packages/agentbundle/tests/unit/test_install_argparse_adapter_flag.py, packages/agentbundle/tests/unit/test_contract_v0_3_schema.py, packages/agentbundle/agentbundle/build/tests/test_contract.py, packages/agentbundle/agentbundle/build/tests/test_adapter_kiro_ide.py, packages/agentbundle/agentbundle/build/tests/test_adapter_cursor.py, packages/agentbundle/tests/integration/test_multi_pack_install.py, .github/workflows/build-check.yml

**Done when:** `test_adapter_gemini.py` is green locally, every shipped-adapter/version-pinned assertion above is updated and green under the full `pytest packages/agentbundle/`, and the new test is wired into `build-check.yml`.

### T7: Support-matrix correction + AGENTS.md reader line + distribution-only proof

**Depends on:** T3

**Tests (goal-based):**
- `docs/guides/reference/adapter-support.md` Gemini row corrected from "Universal layer" to its true tier (skill/subagent/command/hook native). [AC15]
- `gemini` **absent** from `SELF_HOST_ADAPTERS`; `make build-self` produces **no** `.gemini/` tree in this repo. [AC12]

**Approach:**
- Edit `docs/guides/reference/adapter-support.md` (repo-owned / `EXCLUDED_PATTERNS` — direct edit).
- Refine the Gemini CLI reader line in **root `AGENTS.md` directly** (line 4 already names Gemini CLI; reword to reflect native projection) **and** keep `packs/core/seeds/AGENTS.md:4` in sync. `AGENTS.md` is in `EXCLUDED_PATTERNS` and `_compose_agents_md` returns `None` when the on-disk file exists, so it is **not** projected — editing the root directly is correct and is *not* reverted by `build-self` (the `work-loop-light-mode` precedent: "root `AGENTS.md` is Manual — edited directly with its seed synced").
- Assert distribution-only: grep `SELF_HOST_ADAPTERS` excludes `gemini`; `make build-self` then `git status` shows no `.gemini/`.

**Touches:** docs/guides/reference/adapter-support.md, AGENTS.md, packs/core/seeds/AGENTS.md

**Done when:** the matrix reads correctly, the reader line is updated in both root and seed, and `make build-self` writes no `.gemini/` tree.

## Rollout

- **Delivery:** additive — a new adapter + an all-packs `allowed-adapters` opt-in. No migration of existing state; a Gemini adopter installs fresh. Reversible (remove the block + adapter + pack lines). Irreversible: none.
- **Infrastructure:** none.
- **External-system integration:** targets Gemini CLI's documented `.gemini/*` layout; no live service dependency.
- **Deployment sequencing:** the Cursor adapter (RFC-0026) is **merged** at v0.11; this stacks on it at v0.12 with the emission pattern + hand-maintained-site list settled. Done — the rebase that pinned the numbers has been performed.

## Risks

- **Contract-bump test traps** — a version bump trips lexical version-compare bugs and stale assertions in CI-ungated test roots (incl. the shipped-adapter-tuple pin `tests/unit/test_install_argparse_adapter_flag.py`, which `gemini` reorders); run the **full** `pytest packages/agentbundle/` by hand on the bump, not just `build-check`.
- **Marketplace drift from the packs edit** — touching `pack.toml` files can drift `marketplace.json`; `build-check` red-fails until `build-self` is run. Bump only where the gate requires.
- **Rebase against merged Cursor — resolved.** Cursor merged first at v0.11; this branch was rebased on 2026-06-11, the version pinned to v0.12, and the hand-maintained-site list reconciled against Cursor's actual diff. A *future* rebase before this PR merges must re-confirm no third adapter landed in between (re-pin if so).

## Changelog

- 2026-06-11: initial plan (drafted after RFC-0027 Accepted + ADR-0016; built on the Cursor-lands-first coordination assumption).
- 2026-06-11: rebased after the Cursor adapter merged (#273, v0.11). Pinned contract bump to **v0.12** and ADR to **0016** (Cursor took 0015); un-hedged the now-real ADR-0015 references; expanded the hand-maintained-site list (T6 + Dependencies & integration) to match Cursor's actual diff — `test_multi_pack_install.py`, `test_contract_v0_3_schema.py`, both `__init__` registries; confirmed **no `scope.py` edit** needed (Cursor's `contract_version_at_least` helper is on main); spec → Approved.
