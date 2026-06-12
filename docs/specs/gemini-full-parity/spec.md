# Spec: gemini-full-parity

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0027](../../rfc/0027-gemini-cli-full-parity-adapter.md) (the decision: add a full-parity `gemini` distribution adapter projecting all primitives to `.gemini/*` + `~/.gemini/*`; keep+map agent `tools:`; tier-preserving model map; new `gemini-command-toml` mode; `AGENTS.md` `context.fileName` bridge; zero-drop hook-event map; distribution-only); [ADR-0016](../../adr/0016-gemini-cli-full-parity-adapter.md) (the recorded decision); [RFC-0026](../../rfc/0026-cursor-full-parity-adapter.md) + [ADR-0015](../../adr/0015-cursor-full-parity-distribution-adapter.md) (the Cursor full-parity adapter — **merged** at contract **v0.11** (#273); this stacks on it at **v0.12**, reusing its now-proven scope-agnostic-emission + prefix-rewrite pattern and its hand-maintained-site touch-list); [RFC-0024](../../rfc/0024-copilot-subagent-projection.md) + [ADR-0013](../../adr/0013-copilot-full-parity-user-scope-adapter.md) + [`copilot-full-parity`](../copilot-full-parity/spec.md) (the full-parity adapter pattern this mirrors — new projection-mode modules under `build/projections/`, the explicit tool-alias table that **fails the build** on an unmapped name, the dual-copy contract invariant, the atomic contract+pack bump); [RFC-0011](../../rfc/0011-pack-allowed-adapters.md) (`allowed-adapters` — edited across **all** packs); [RFC-0005](../../rfc/0005-user-scope-hook-support.md) (`merge-json` / user-scope-hook precedent for the `.gemini/settings.json` merge); [RFC-0004](../../rfc/0004-repo-scope-per-adapter-projection.md) (one-PR-one-contract-bump atomicity; install-scope dimension); [ADR-0004](../../adr/0004-repo-scope-per-adapter-projection.md) (per-adapter projection model); [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md) (per-pack scope default + allowance). Modifies [`packages/agentbundle/agentbundle/_data/adapter.toml`](../../../packages/agentbundle/agentbundle/_data/adapter.toml) (new `[adapter.gemini]` block + `gemini-agent-frontmatter` + hook-event map; contract version bump) and [`packages/agentbundle/agentbundle/_data/adapter.schema.json`](../../../packages/agentbundle/agentbundle/_data/adapter.schema.json) (`gemini-command-toml` admitted to the `mode` enum at every site) — **both dual-copy** into [`docs/contracts/adapter.toml`](../../contracts/adapter.toml) + [`docs/contracts/adapter.schema.json`](../../contracts/adapter.schema.json) (byte-identical, per `test_contract_files_byte_identical`); a new projection-mode module under `packages/agentbundle/agentbundle/build/projections/`; the dispatch + user-scope-prefix-rewrite in `packages/agentbundle/agentbundle/commands/install.py`; the new adapter `packages/agentbundle/agentbundle/build/adapters/gemini.py` + its registry entry in `adapters/__init__.py`; `allowed-adapters` across **all** packs (`packs/*/pack.toml`); and the support matrix [`docs/guides/reference/adapter-support.md`](../../guides/reference/adapter-support.md) + root [`AGENTS.md`](../../../AGENTS.md) reader line.
- **Contract:** none <!-- no REST/event/RPC interface surface; the adapter contract (`adapter.toml`) is internal build-pipeline data, named in Constrained by above -->
- **Shape:** integration <!-- wiring the adapter/contract to an external tool's (Gemini CLI's) native surfaces; pulls dependencies & integration + interfaces & contracts + failure & resilience into the plan's LLD -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Scope: one PR, one contract bump (`v0.11 → v0.12`).** The contract block +
> version bump, the new `gemini-command-toml` mode, the `gemini-agent-frontmatter`
> mapping, the scope table, the `AGENTS.md` bridge, the packs `allowed-adapters`
> edit, the support-matrix correction, and the adapter module all land in a
> **single PR** per the RFC-0004 atomicity precedent inherited from
> `copilot-full-parity`. Splitting risks the contract claiming `.gemini/*`
> projection with no implementation that writes there.

> **Coordination (numbers now pinned).** The Cursor adapter (RFC-0026 / ADR-0015)
> **merged** at contract **v0.11** (#273) on 2026-06-11. This work therefore stacks
> on it: contract **v0.11 → v0.12**, **ADR-0016** (Cursor took 0015). The Cursor
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
`gemini-command-toml` mode), its hook bodies under `tools/hooks/` with the wiring
merged into `.gemini/settings.json` (`hooks` key), and a managed `context.fileName`
entry in that **same** `.gemini/settings.json` so the root `AGENTS.md` is read. At
`--scope user` the identical tree lands under `~/.gemini/` via the install-time
prefix rewrite. No supported primitive is dropped; an unmappable tool name is
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
- **Hook-event mapping** (PascalCase source `SessionStart→SessionStart`, `UserPromptSubmit→BeforeAgent`, `PreToolUse→BeforeTool`, `PostToolUse→AfterTool`, `Stop→AfterAgent`, `SessionEnd→SessionEnd`): **TDD** — source-event→Gemini-event table, unit-level, with a fail-closed assertion on an unrecognised event and a matcher-passthrough assertion.
- **Skill / hook-body projection + scope user-rewrite** (`.gemini/skills/`, `tools/hooks/`, `~/.gemini/` rewrite): **goal-based**, exercised by an **integration** test over the adapter's projection at both scopes.
- **Contract byte-identical + version-compare**: **goal-based** — `test_contract_files_byte_identical` and the swept `test_contract*.py` green.
- **All-packs `allowed-adapters` + no marketplace/build drift**: **goal-based** — `gemini` present in every `packs/*/pack.toml`; `make build-check` green (drift gate, marketplace aggregation).
- **Shipped-agent tool coverage**: **goal-based** — a test scanning shipped agent frontmatter asserts every declared tool is in the mapping (so an unmapped tool would surface, not silently drop).

## Acceptance Criteria

- [ ] **AC1.** A `gemini` adapter module exists at `packages/agentbundle/agentbundle/build/adapters/gemini.py` and is registered in `adapters/__init__.py` (`registry` map).
- [ ] **AC2.** `[adapter.gemini]` in `_data/adapter.toml` projects `skill` → `direct-directory` `.gemini/skills/<name>/`, `agent` → `direct-file` + `gemini-agent-frontmatter` `.gemini/agents/<name>.md`, `hook-body` → `direct-file` `tools/hooks/`, `hook-wiring` → `merge-json` (managed-key `hooks`) `.gemini/settings.json`, `command` → `gemini-command-toml` `.gemini/commands/<name>.toml`.
- [ ] **AC3.** `[adapter.gemini.scope]` declares `repo = "."`, `user = "~"`, and `allowed-prefixes` for both scopes (`.gemini/`, `.agentbundle/`, `tools/hooks/` at repo).
- [ ] **AC4.** `gemini-command-toml` is added to the `mode` enum at **every** enumerating site in `_data/adapter.schema.json` and its `docs/contracts/` mirror.
- [ ] **AC5.** `gemini-agent-frontmatter` maps `tools` via `values` (`Read→read_file`, `Grep→grep_search`, `Glob→glob`, `Edit→replace`, `MultiEdit→replace`, `Write→write_file`, `Bash→run_shell_command`, `WebFetch→web_fetch`, `WebSearch→google_web_search`, `LS→list_directory`) with `normalize = "to-list"`; an unmapped tool is dropped with a build-time log line. (`MultiEdit` is mapped for parity with the `codex`/`claude`/`kiro` maps, which all cover it.)
- [ ] **AC6.** `gemini-agent-frontmatter` maps `model` via `values` (`opus→gemini-2.5-pro`, `sonnet→gemini-2.5-flash`, `haiku→gemini-2.5-flash-lite`); a source agent that omits `model` produces no `model` field in the output.
- [ ] **AC7.** The `command` projection translates a single-injection command (`$ARGUMENTS`→`{{args}}`, body→`prompt`, description→`description`, subdir `/`→`:`) and **raises a build error** for any command requiring positional (`$1`/`$2`) or multi-injection arguments `{{args}}` cannot express.
- [ ] **AC8.** Hook-wiring **and** the `AGENTS.md` `context.fileName = ["AGENTS.md", "GEMINI.md"]` bridge land in a **single** managed-merge into `.gemini/settings.json` (managed keys `hooks` + `context`); a pre-existing foreign key in that file survives the merge.
- [ ] **AC9.** The hook-event map is keyed on the **Claude-Code source event names** the shipped hook-wiring actually uses (PascalCase, e.g. `[[hooks.SessionStart]]`) — mirroring the `copilot-hooks-json` `_EVENT_MAP` precedent — mapping `SessionStart→SessionStart`, `SessionEnd→SessionEnd`, `UserPromptSubmit→BeforeAgent`, `PreToolUse→BeforeTool`, `PostToolUse→AfterTool`, `Stop→AfterAgent`. The map lives in the contract, drops no event, and **fails the build** (not silently) on an unrecognised source event. A source hook `matcher` (Gemini supports a regex matcher on `BeforeTool`/`AfterTool`) is passed through unchanged; no shipped wiring sets one today.
- [ ] **AC10.** At `--scope user`, every target lands under `~/.gemini/` via the install-time prefix rewrite (no `gemini`-specific home-path logic duplicated).
- [ ] **AC11.** `gemini` is appended to the `allowed-adapters` list of the **7 packs that declare one** (`architect`, `atlassian`, `contracts`, `converters`, `credential-brokers`, `figma`, `research`); the **4 line-less packs** (`core`, `governance-extras`, `monorepo-extras`, `user-guide-diataxis`) are left untouched — at repo scope any shipped adapter is admissible, so they already admit `gemini` and an explicit list would *narrow* them. After the edit `gemini` is admissible for every pack and `make build-check` is green (no marketplace/drift regression).
- [ ] **AC12.** `gemini` is **not** in `SELF_HOST_ADAPTERS`; `make build-self` projects no `.gemini/` tree into this repo.
- [ ] **AC13.** `_data/adapter.toml` + `_data/adapter.schema.json` are byte-identical to their `docs/contracts/` mirrors (`test_contract_files_byte_identical` green); the contract version is bumped **v0.11 → v0.12**; and every shipped-adapter/version-pinned assertion is updated and green — `test_contract.py` (`ALL_ADAPTERS` + pair-count + version), `tests/unit/test_install_argparse_adapter_flag.py` (shipped-adapter tuple; `gemini` sorts before `kiro`), `tests/unit/test_contract_v0_3_schema.py`, `tests/integration/test_multi_pack_install.py` (adapter tuple + a `_skill_path` branch returning `.gemini/skills/<n>/SKILL.md`), **and the per-adapter contract-version pins in `build/tests/test_adapter_kiro_ide.py` + `build/tests/test_adapter_cursor.py`** (both currently `assertEqual(version, "0.11")`). All are CI-only roots not in `make build-check`.
- [ ] **AC14.** `test_adapter_gemini.py` exists under `build/tests/` and is wired into `.github/workflows/build-check.yml` as an explicit pytest path (matching how Cursor's #273 wired `test_adapter_cursor.py` — `build-check.yml` only; the Windows workflow runs no `test_adapter_*` suite).
- [ ] **AC15.** The support matrix `docs/guides/reference/adapter-support.md` gains a **dedicated Gemini CLI row** at its true tier (skill/subagent/command/hook native — like the Cursor row), and Gemini is **removed** from the "Any `AGENTS.md` reader" example (it is no longer universal-layer-only). The root `AGENTS.md` Gemini reader line reflects native projection (edited directly — `AGENTS.md` is `EXCLUDED_PATTERNS`, not projected — with the `packs/core/seeds/AGENTS.md` copy kept in sync).

## Assumptions

- Technical: adapters are Python modules under `packages/agentbundle/agentbundle/build/adapters/`, registered in `adapters/__init__.py` (`registry` map). (source: `packages/agentbundle/agentbundle/build/adapters/__init__.py:39`)
- Technical: the contract is `_data/adapter.toml` + `_data/adapter.schema.json`, byte-mirrored into `docs/contracts/` (`test_contract_files_byte_identical`). (source: `docs/specs/copilot-full-parity/spec.md` Constrained-by)
- Technical: new projection modes are implemented as modules under `build/projections/`, with dispatch + user-scope-prefix-rewrite in `commands/install.py`. (source: `docs/specs/copilot-full-parity/spec.md`)
- Technical: no `docs/architecture/reference.md` — stack detected from the repo: Python, the `agentbundle` build package. (source: probe — `ls docs/architecture/reference.md` → absent)
- Technical: adapter + contract tests live under `build/tests/`; `make build-check` runs no pytest, so CI wires each test path explicitly. (source: `.github/workflows/build-check.yml:91-92`)
- Technical: a contract version bump trips `test_contract*.py` version assertions and risks lexical version-compare bugs. (source: `build/tests/test_contract.py`/`test_contract_v07.py`/`test_contract_v08.py`)
- Technical: Gemini CLI primitive surface, model IDs, tool identifiers, hook events, and the `context.fileName` bridge are doc-confirmed. (source: `.context/gemini-cli-research.md`; RFC-0027 § Evidence)
- Process: governed by RFC-0027 (Accepted) + ADR-0016; one PR / one contract bump per RFC-0004 atomicity. (source: `docs/specs/copilot-full-parity/spec.md`)
- Process: spec lifecycle Draft→Approved→Implementing→Shipped, owner eugenelim. (source: `docs/specs/copilot-full-parity/spec.md` header)
- Product: the primary user is an adopter who installs catalogue packs and runs Gemini CLI; "done" = every supported primitive lands under `.gemini/` (+ `~/.gemini/`) and `AGENTS.md` is read via the `context.fileName` bridge. (source: user confirmation 2026-06-11)
- Process: `allowed-adapters` opts `gemini` into **all** packs. (source: user confirmation 2026-06-11)
- Technical: the `context` bridge is a **single** managed-merge into `.gemini/settings.json` alongside `hooks`. (source: user confirmation 2026-06-11)
- Technical: command arg translation is **fail-closed** — translate the single-injection form, error out on anything beyond single injection. (source: user confirmation 2026-06-11)
- Coordination: Cursor (RFC-0026 / ADR-0015) merged at contract v0.11 (#273, 2026-06-11); this stacks on it at v0.12 / ADR-0016, reusing its hand-maintained-site touch-list. (source: user confirmation 2026-06-11; `origin/main` post-rebase)
