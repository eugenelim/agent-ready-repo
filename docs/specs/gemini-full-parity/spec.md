# Spec: gemini-full-parity

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0027](../../rfc/0027-gemini-cli-full-parity-adapter.md) (the decision: add a full-parity `gemini` distribution adapter projecting all primitives to `.gemini/*` + `~/.gemini/*`; keep+map agent `tools:`; tier-preserving model map; new `gemini-command-toml` mode; `AGENTS.md` `context.fileName` bridge; zero-drop hook-event map; distribution-only); [ADR-0016](../../adr/0016-gemini-cli-full-parity-adapter.md) (the recorded decision); [RFC-0026](../../rfc/0026-cursor-full-parity-adapter.md) + [ADR-0015](../../adr/0015-cursor-full-parity-distribution-adapter.md) (the Cursor full-parity adapter — **merged** at contract **v0.11** (#273); the `copilot-skills-and-web` skill-flip then **merged** at **v0.12** (#272); this stacks on both at **v0.13**, reusing Cursor's now-proven scope-agnostic-emission + prefix-rewrite pattern and its hand-maintained-site touch-list); [RFC-0024](../../rfc/0024-copilot-subagent-projection.md) + [ADR-0013](../../adr/0013-copilot-full-parity-user-scope-adapter.md) + [`copilot-full-parity`](../copilot-full-parity/spec.md) (the full-parity adapter pattern this mirrors — new projection-mode modules under `build/projections/`, the explicit tool-alias table that **fails the build** on an unmapped name, the dual-copy contract invariant, the atomic contract+pack bump); [RFC-0011](../../rfc/0011-pack-allowed-adapters.md) (`allowed-adapters` — edited across **all** packs); [RFC-0005](../../rfc/0005-user-scope-hook-support.md) (`merge-json` / user-scope-hook precedent for the `.gemini/settings.json` merge); [RFC-0004](../../rfc/0004-install-scope-per-pack.md) (one-PR-one-contract-bump atomicity; install-scope dimension); [ADR-0004](../../adr/0004-repo-scope-per-adapter-projection.md) (per-adapter projection model); [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md) (per-pack scope default + allowance). Modifies [`packages/agentbundle/agentbundle/_data/adapter.toml`](../../../packages/agentbundle/agentbundle/_data/adapter.toml) (new `[adapter.gemini]` block + `gemini-agent-frontmatter` + hook-event map; contract version bump) and [`packages/agentbundle/agentbundle/_data/adapter.schema.json`](../../../packages/agentbundle/agentbundle/_data/adapter.schema.json) (`gemini-command-toml` admitted to the `mode` enum at every site) — **both dual-copy** into [`docs/contracts/adapter.toml`](../../contracts/adapter.toml) + [`docs/contracts/adapter.schema.json`](../../contracts/adapter.schema.json) (byte-identical, per `test_contract_files_byte_identical`); a new projection-mode module under `packages/agentbundle/agentbundle/build/projections/`; the dispatch + user-scope-prefix-rewrite in `packages/agentbundle/agentbundle/commands/install.py`; the new adapter `packages/agentbundle/agentbundle/build/adapters/gemini.py` + its registry entry in `adapters/__init__.py`; `allowed-adapters` across the **7 list-declaring** packs (`packs/*/pack.toml`; the 4 list-less packs are left untouched per AC11); and the support matrix [`docs/guides/_shared/reference/adapter-support.md`](../../guides/_shared/reference/adapter-support.md) + root [`AGENTS.md`](../../../AGENTS.md) reader line.
- **Contract:** none <!-- no REST/event/RPC interface surface; the adapter contract (`adapter.toml`) is internal build-pipeline data, named in Constrained by above -->
- **Shape:** integration <!-- wiring the adapter/contract to an external tool's (Gemini CLI's) native surfaces; pulls dependencies & integration + interfaces & contracts + failure & resilience into the plan's LLD -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Scope: one PR, one contract bump (`v0.12 → v0.13`).** The contract block +
> version bump, the new `gemini-command-toml` mode, the `gemini-agent-frontmatter`
> mapping, the scope table, the `AGENTS.md` bridge, the packs `allowed-adapters`
> edit, the support-matrix correction, and the adapter module all land in a
> **single PR** per the RFC-0004 atomicity precedent inherited from
> `copilot-full-parity`. Splitting risks the contract claiming `.gemini/*`
> projection with no implementation that writes there.

> **Coordination (numbers now pinned).** The Cursor adapter (RFC-0026 / ADR-0015)
> **merged** at contract **v0.11** (#273) on 2026-06-11; the `copilot-skills-and-web`
> skill-flip then **merged** at **v0.12** (#272). This work therefore stacks on
> the post-copilot main: contract **v0.12 → v0.13**, **ADR-0016** (Cursor took 0015;
> `copilot-skills-and-web` took no ADR/RFC number). The Cursor
> implementation is the worked precedent for every hand-maintained site this spec
> touches (`__init__.py` two registries, `install.py` dispatch + prefix rewrite,
> `test_contract.py`, `test_install_argparse_adapter_flag.py`,
> `test_multi_pack_install.py`, `test_contract_v0_3_schema.py`, CI wiring).

## Objective

Make the `gemini` adapter project **every primitive Gemini CLI now supports** —
`skill`, `agent`, `hook-body`, `hook-wiring`, `command` — to Gemini CLI's native
`.gemini/*` (repo) and `~/.gemini/*` (user) discovery layout, and bridge the
canonical `AGENTS.md` into Gemini's context discovery so the universal layer is
honoured rather than silently dropped. Today Gemini CLI is classified as a
"Universal layer / `AGENTS.md` reader only" adapter and has **no adapter at all**
— and because Gemini does not read `AGENTS.md` by default and does not cross-read
`.claude/`/`.codex/`, a Gemini adopter currently gets **nothing**. This spec
closes that gap with full fidelity: the agent `tools:` allowlist is **kept and
name-mapped** (Gemini has a real per-agent allowlist), and a **tier-preserving**
model map is applied.

**For the Gemini adopter installing a pack at repo scope:**
`agentbundle install --pack core --scope repo --adapter gemini .` today refuses or
no-ops (no `gemini` adapter exists). After this spec the same command lands the
pack's skills at `.gemini/skills/<name>/`, its subagents at
`.gemini/agents/<name>.md` (markdown body → system prompt, `tools:`/`model:`
name-mapped via the new `gemini-agent-frontmatter` mapping), its commands at
`.gemini/commands/<name>.toml` (markdown body → TOML `prompt` via the new
`gemini-command-toml` mode), its hook bodies under `.gemini/hooks/` with the wiring
merged into `.gemini/settings.json` (`hooks` key, command path-rewritten
`tools/hooks/`→`.gemini/hooks/`), and a managed `context.fileName`
entry in that **same** `.gemini/settings.json` so the root `AGENTS.md` is read. At
`--scope user` the identical tree lands under `~/.gemini/` via the generic
user-rooting of the same `.gemini/…` relpaths (no gemini-specific prefix rewrite,
the Cursor pattern). No supported primitive is dropped; an unmappable tool name is
logged and a command that needs more than single-argument injection **fails the
build** rather than emitting a silently-degraded command.

## Boundaries

### Always do

- **Dual-copy every contract edit** — `_data/adapter.toml` and `_data/adapter.schema.json` edits are mirrored byte-for-byte into `docs/contracts/` (guarded by `test_contract_files_byte_identical`).
- **Map agent tool/model names via the explicit `values` tables** in the contract (the `codex-agent-frontmatter` pattern); an **unmapped tool name is dropped with a build-time log line**, never silently omitted.
- **Merge — never overwrite — `.gemini/settings.json`**: write only the managed `hooks` and `context` keys; preserve any adopter-authored keys.
- **Sweep every shipped-adapter/version-pinned test on the bump** — `test_contract.py`/`test_contract_v07.py`/`test_contract_v08.py`/`tests/unit/test_contract_v0_3_schema.py`, the shipped-adapter-tuple pin `tests/unit/test_install_argparse_adapter_flag.py`, `tests/integration/test_multi_pack_install.py`, the per-adapter version pins in `build/tests/test_adapter_kiro_ide.py` + `test_adapter_cursor.py`, and any cohort/adapter-support version pin; watch lexical version-compare traps. Run the **full** `pytest packages/agentbundle/` by hand (CI-only roots are not in `make build-check`).
- **Add the new `test_adapter_gemini.py` path to CI explicitly** (`make build-check` runs no pytest; CI wires each path by hand).

### Ask first

- **Pinning the concrete contract version number and ADR number** — these are resolved at the pre-merge rebase against the merged Cursor adapter, not chosen now.
- **Changing the model alias targets** away from the stable 2.5 line (`opus→gemini-2.5-pro` / `sonnet→gemini-2.5-flash` / `haiku→gemini-2.5-flash-lite`), e.g. to the `gemini-3-*-preview` line.
- **Adding any projection mode or contract construct beyond** the one new `gemini-command-toml` mode and the static `context`-bridge emission named in RFC-0027.

### Never do

- **Add `gemini` to `SELF_HOST_ADAPTERS`** — this repo does not self-host onto Gemini (distribution-only; `SELF_HOST_ADAPTERS` stays `("claude-code", "codex")`). *(Structural.)*
- **Introduce a new top-level dependency, package, or module boundary** beyond `build/adapters/gemini.py`, the one new `build/projections/` mode module, and the `[adapter.gemini]` contract block. *(Structural.)*
- **Whole-file overwrite an adopter's `.gemini/settings.json`** or any adopter-authored `.gemini/*` content.
- **Silently drop a Gemini-supported primitive, an unmappable tool, or a non-single-injection command** — drop-with-log for tools, **fail-closed (build error)** for commands; never a silent degrade.

## Testing Strategy

- **Agent frontmatter mapping** (tool-name `values` map + tier-preserving model `values` map + unmapped-tool log): **TDD** — a compressible invariant (input agent frontmatter → exact output frontmatter), unit-level over the mapping function.
- **Command `gemini-command-toml` transform + fail-closed rule**: **TDD** — the happy path (`$ARGUMENTS`→`{{args}}`, body→`prompt`, description→`description`, subdir→`:` namespacing) **and** the error path (a command needing positional `$1`/multiple-injection raises a build error), unit-level.
- **Hook-wiring + `context` bridge single-merge into `.gemini/settings.json`**: **goal-based**, exercised by an **integration** test that merges against a **pre-populated** `settings.json` carrying a foreign key and asserts the foreign key survives and both managed keys land.
- **Hook-event mapping** (PascalCase source `SessionStart→SessionStart`, `UserPromptSubmit→BeforeAgent`, `PreToolUse→BeforeTool`, `PostToolUse→AfterTool`, `Stop→AfterAgent`, `SessionEnd→SessionEnd`): **TDD** — source-event→Gemini-event table, unit-level, with a fail-closed assertion on an unrecognised event and a matcher-passthrough assertion. The five non-shipped mappings are unit-table-verified only; the `SessionStart` round-trip is the single integration-verified path (it is the only shipped wiring).
- **Skill / hook-body projection** (`.gemini/skills/`, `.gemini/hooks/`) **+ contract pair-count**: **goal-based** — an **integration** test over the adapter's projection (skill→`.gemini/skills/<n>/`, hook-body→`.gemini/hooks/`), and `test_contract.py`'s pair-count pinned to **44** (gemini adds 5 standard + 1 `kiro-ide-hook` dropped table entry = 6; the `ALL_ADAPTERS` set and the "standard pairs" docstring prose are updated to match).
- **Contract byte-identical + version-compare**: **goal-based** — `test_contract_files_byte_identical` and the swept `test_contract*.py` green.
- **All-packs `allowed-adapters`, both scopes + no marketplace/build drift**: **goal-based** — `gemini` in the 7 list-declaring packs' `allowed-adapters`; a coverage test resolves `--adapter gemini` for all 11 packs × {repo, user} with none refused; `make build-check` green (drift gate, marketplace aggregation).
- **Shipped-agent tool coverage**: **goal-based** — a test scanning shipped agent frontmatter asserts every declared tool is in the mapping (so an unmapped tool would surface, not silently drop).

## Acceptance Criteria

- [x] **AC1.** A `gemini` adapter module exists at `packages/agentbundle/agentbundle/build/adapters/gemini.py` and is registered in `adapters/__init__.py` (`registry` map).
- [x] **AC2.** `[adapter.gemini]` in `_data/adapter.toml` projects `skill` → `direct-directory` `.gemini/skills/<name>/`, `agent` → `direct-file` + `gemini-agent-frontmatter` `.gemini/agents/<name>.md`, `hook-body` → `direct-file` `.gemini/hooks/` (the Cursor model — under `.gemini/` so it is fenced by the same prefix at **both** scopes, not the legacy `tools/hooks/` repo-only path), `hook-wiring` → `merge-json` (managed-key `hooks`) `.gemini/settings.json`, `command` → `gemini-command-toml` `.gemini/commands/<name>.toml`. `kiro-ide-hook` is declared `dropped` in the table form (Kiro-only; mirrors the Cursor/kiro-ide/kiro-cli precedent) — so the contract adds **6** (primitive × gemini) pairs.
- [x] **AC3.** `[adapter.gemini.scope]` declares `repo = "."`, `user = "~"`, and `allowed-prefixes` **identical at both scopes** — `[".gemini/", ".agentbundle/"]` (the Cursor pattern: every projected target is under `.gemini/`, so the user-scope home is the generic user-rooting of the same repo-relpath with no gemini-specific prefix rewrite). No `tools/hooks/` prefix — gemini's hook bodies land under `.gemini/hooks/`.
- [x] **AC4.** `gemini-command-toml` is added to the `mode` enum at **every** enumerating site in `_data/adapter.schema.json` and its `docs/contracts/` mirror.
- [x] **AC5.** `gemini-agent-frontmatter` maps `tools` via `values` (`Read→read_file`, `Grep→grep_search`, `Glob→glob`, `Edit→replace`, `MultiEdit→replace`, `Write→write_file`, `Bash→run_shell_command`, `WebFetch→web_fetch`, `WebSearch→google_web_search`, `LS→list_directory`) with `normalize = "to-list"`; an unmapped tool is dropped with a build-time log line. (`MultiEdit` is mapped for parity with the `codex`/`claude`/`kiro` maps, which all cover it.) The `to-list` mapping **de-duplicates collided targets** (an agent declaring both `Edit` and `MultiEdit` yields a single `replace`, not two) — the `codex-agent-toml` `_apply_mapping` `if translated not in mapped` precedent. An agent whose declared tools **all** drop emits **no** `tools` key (not `tools: []`, which Gemini could read as "no tools permitted") — matching the `model`-absent → omitted precedent.
- [x] **AC6.** `gemini-agent-frontmatter` maps `model` via `values` (`opus→gemini-2.5-pro`, `sonnet→gemini-2.5-flash`, `haiku→gemini-2.5-flash-lite`); a source agent that omits `model` produces no `model` field in the output. (Verify `gemini-2.5-flash-lite` against the live CLI model list at implementation time per RFC-0027 § Evidence — it is confirmed on the API models page but not yet the CLI model-selection page.)
- [x] **AC7.** The `command` projection translates a single-injection command (`$ARGUMENTS`→`{{args}}`, body→`prompt`, description→`description`, subdir `/`→`:`) and **raises a build error** for any command requiring positional (`$1`/`$2`) or multi-injection arguments `{{args}}` cannot express. (The positional guard matches `$<digit>` body-wide — fail-closed, so a literal dollar-amount in prose/code also refuses the build; an injection-context-aware parser is a follow-on, `docs/backlog.md` § `gemini-full-parity`. No shipped command contains a `$<digit>`.)
- [x] **AC8.** Hook-wiring **and** the `AGENTS.md` `context.fileName = ["AGENTS.md", "GEMINI.md"]` bridge land in a **single** managed-merge into `.gemini/settings.json` (managed keys `hooks` + `context`); a pre-existing foreign key in that file survives the merge. **Mechanism (resolves the "no driving primitive" gap):** the `gemini` adapter owns a bespoke settings-merge helper (the `cursor.py` `_project_hooks_json` shape — *not* the generic `merge-json` module, which carries one primitive-driven key), invoked once per projection as a post-pass over all packs. It builds the `hooks` map from the `hook-wiring` source (the rule's `managed-key`) **and** a static `context` map whose `fileName` list is read from a new contract field `context-filenames = ["AGENTS.md", "GEMINI.md"]` on the `gemini` hook-wiring projection rule (data in the contract, not a literal in code; schema-safe — array-item rules carry no `additionalProperties:false`, the same place `hook-event-map` lives). The helper reads any existing `settings.json`, sets only `hooks` + `context`, preserves every other top-level key, and writes **once**. **Single-writer (the cursor model):** the file is written **only when the pack ships hook-wiring** — repo-scope install writes merge-json targets **whole-file** (no install-time JSON merge) and the adapter renders into an isolated tempdir, so a settings.json emitted for *every* pack would **overwrite** (clobber) another pack's hooks. Gating on hook-wiring presence keeps `.gemini/settings.json` single-writer per install root, exactly as `.cursor/hooks.json` and `.claude/settings.local.json` are. The `context` bridge rides in that same write; in the catalogue the base `core` pack ships **both** the session-start wiring **and** `AGENTS.md` (as a seed), so the bridge lands precisely when the `AGENTS.md` it points at exists. **Documented boundary:** an adopter who installs *only* a non-`core` pack with `--adapter gemini` (no `core`, hence no shipped hook-wiring) gets no `.gemini/settings.json` — so if they have an `AGENTS.md` of their *own*, it is not bridged. This is a known limitation of the single-writer model under repo-scope whole-file overwrite; the clean fix (write `context` whenever an `AGENTS.md` exists at the install root, independent of wiring) needs install-time merge-json and is a follow-on (`docs/backlog.md` § `gemini-full-parity`). In practice every catalogue adopter installs `core`, so the bridge lands. This is the **only** non-`gemini-command-toml` contract construct, and it is the "static `context`-bridge emission" the Ask-first boundary admits.
- [x] **AC9.** The hook-event map is keyed on the **Claude-Code source event names** the shipped hook-wiring actually uses (PascalCase, e.g. `[[hooks.SessionStart]]`) — mirroring the `copilot-hooks-json` `_EVENT_MAP` precedent — mapping `SessionStart→SessionStart`, `SessionEnd→SessionEnd`, `UserPromptSubmit→BeforeAgent`, `PreToolUse→BeforeTool`, `PostToolUse→AfterTool`, `Stop→AfterAgent`. The map lives in the contract, drops no event, and **fails the build** (not silently) on an unrecognised source event. A source hook `matcher` (Gemini supports a regex matcher on `BeforeTool`/`AfterTool`) is passed through unchanged; no shipped wiring sets one today. The carried command's legacy `tools/hooks/` hook-body prefix is **rewritten to `.gemini/hooks/`** (where `hook-body` direct-file lands it per AC2), the `cursor.py` `_rewrite_hook_body_path` precedent — so the emitted command references the script where it actually lands at both scopes. Only the shipped `SessionStart` round-trip is integration-verified (it is the only shipped wiring); the other five mappings are verified by unit table-assertion.
- [x] **AC10.** At `--scope user`, **every** target lands under `~/.gemini/` (skills, agents, commands, `settings.json`, **and** hook bodies — all under `.gemini/` per AC2/AC3) via the generic user-rooting of the adapter's scope-agnostic `.gemini/…` repo-relpaths (no `gemini`-specific home-path logic, no prefix rewrite — the Cursor pattern). This holds for every pack, including `core` (which ships a hook body + wiring): the body lands at `~/.gemini/hooks/`, fenced by `allowed-prefixes.user`.
- [x] **AC11.** **Every pack admits `gemini` at both repo and user scope.** `gemini` is appended to the `allowed-adapters` list of the **7 packs that declare one** (`architect`, `atlassian`, `contracts`, `converters`, `credential-brokers`, `figma`, `research`) — required because `install.py:2737-2762` refuses an unlisted `--adapter` for a list-declaring pack even at repo scope, and the user-scope subcheck (`install.py:2720-2734`) requires every listed adapter to be user-scope-capable (`gemini` is, via AC3's `[scope].user`). The **4 line-less packs** (`core`, `governance-extras`, `monorepo-extras`, `user-guide-diataxis`) are left **untouched** — a list-less pack admits *any* shipped (repo) / user-scope-capable (user) adapter, so they already admit `gemini` at both scopes; adding an explicit list would *narrow* them (a regression for every other adapter). A goal-based coverage test resolves `--adapter gemini` for **all 11 packs × {repo, user}** and asserts none is refused. After the edit `make build-check` is green (no marketplace/drift regression).
- [x] **AC12.** `gemini` is **not** in `SELF_HOST_ADAPTERS`; `make build-self` projects no `.gemini/` tree into this repo.
- [x] **AC13.** `_data/adapter.toml` + `_data/adapter.schema.json` are byte-identical to their `docs/contracts/` mirrors (`test_contract_files_byte_identical` green); the contract version is bumped **v0.12 → v0.13**; and every shipped-adapter/version-pinned assertion is updated and green — `test_contract.py` (`ALL_ADAPTERS` + pair-count + version), `tests/unit/test_install_argparse_adapter_flag.py` (shipped-adapter tuple; `gemini` sorts before `kiro`), `tests/unit/test_contract_v0_3_schema.py`, `tests/integration/test_multi_pack_install.py` (adapter tuple + a `_skill_path` branch returning `.gemini/skills/<n>/SKILL.md`), **and the per-adapter contract-version pins in `build/tests/test_adapter_kiro_ide.py` + `build/tests/test_adapter_cursor.py`** (both currently `assertEqual(version, "0.12")`). All are CI-only roots not in `make build-check`.
- [x] **AC14.** `test_adapter_gemini.py` exists under `build/tests/` and is wired into `.github/workflows/build-check.yml` as an explicit pytest path (matching how Cursor's #273 wired `test_adapter_cursor.py` — `build-check.yml` only; the Windows workflow runs no `test_adapter_*` suite).
- [x] **AC15.** The support matrix `docs/guides/_shared/reference/adapter-support.md` gains a **dedicated Gemini CLI row** at its true tier (skill/subagent/command/hook native — like the Cursor row), and Gemini is **removed** from the "Any `AGENTS.md` reader" example (it is no longer universal-layer-only). The root `AGENTS.md` Gemini reader line reflects native projection (edited directly — `AGENTS.md` is `EXCLUDED_PATTERNS`, not projected — with the `packs/core/seeds/AGENTS.md` copy kept in sync).

## Assumptions

- Technical: adapters are Python modules under `packages/agentbundle/agentbundle/build/adapters/`, registered in `adapters/__init__.py` (`registry` map). (source: `packages/agentbundle/agentbundle/build/adapters/__init__.py:39`)
- Technical: the contract is `_data/adapter.toml` + `_data/adapter.schema.json`, byte-mirrored into `docs/contracts/` (`test_contract_files_byte_identical`). (source: `docs/specs/copilot-full-parity/spec.md` Constrained-by)
- Technical: new projection modes are implemented as modules under `build/projections/`, with dispatch + user-scope-prefix-rewrite in `commands/install.py`. (source: `docs/specs/copilot-full-parity/spec.md`)
- Technical: no `docs/architecture/reference.md` — stack detected from the repo: Python, the `agentbundle` build package. (source: probe — `ls docs/architecture/reference.md` → absent)
- Technical: adapter + contract tests live under `build/tests/`; `make build-check` runs no pytest, so CI wires each test path explicitly. (source: `.github/workflows/build-check.yml:91-92`)
- Technical: a contract version bump trips `test_contract*.py` version assertions and risks lexical version-compare bugs. (source: `build/tests/test_contract.py`/`test_contract_v07.py`/`test_contract_v08.py`)
- Technical: Gemini CLI primitive surface, model IDs, tool identifiers, hook events, and the `context.fileName` bridge are doc-confirmed. (source: RFC-0027 § Evidence)
- Process: governed by RFC-0027 (Accepted) + ADR-0016; one PR / one contract bump per RFC-0004 atomicity. (source: `docs/specs/copilot-full-parity/spec.md`)
- Process: spec lifecycle Draft→Approved→Implementing→Shipped, owner eugenelim. (source: `docs/specs/copilot-full-parity/spec.md` header)
- Product: the primary user is an adopter who installs catalogue packs and runs Gemini CLI; "done" = every supported primitive lands under `.gemini/` (+ `~/.gemini/`) and `AGENTS.md` is read via the `context.fileName` bridge. (source: user confirmation 2026-06-11)
- Process: `allowed-adapters` opts `gemini` into **all** packs. (source: user confirmation 2026-06-11)
- Technical: the `context` bridge is a **single** managed-merge into `.gemini/settings.json` alongside `hooks`. (source: user confirmation 2026-06-11)
- Technical: command arg translation is **fail-closed** — translate the single-injection form, error out on anything beyond single injection. (source: user confirmation 2026-06-11)
- Coordination: Cursor (RFC-0026 / ADR-0015) merged at contract v0.11 (#273, 2026-06-11); `copilot-skills-and-web` then merged at v0.12 (#272, no ADR/RFC number); this stacks on the post-copilot main at v0.13 / ADR-0016, reusing Cursor's hand-maintained-site touch-list. (source: user direction 2026-06-11 — copilot took v0.12, use v0.13; `origin/main` post-rebase)
