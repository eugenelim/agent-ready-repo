# RFC-0027: Gemini CLI full-parity adapter

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-11
- **Date closed:** 2026-06-11
- **Related:** RFC-0026 (Cursor full-parity adapter) · RFC-0024 / ADR-0013 (Copilot full-parity user-scope adapter) · RFC-0022 / ADR-0012 (Kiro adapter split) · RFC-0004 (install-scope dimension) · RFC-0005 (user-scope hook support) · spec `apm-install-route-parity` (already names Gemini as a deferred APM hook-firing target, AC17)

## The ask

- **Recommendation (BLUF):** Add a native `gemini` distribution adapter that projects every catalogue primitive to Gemini CLI's `.gemini/*` (repo) and `~/.gemini/*` (user) discovery paths, following the Cursor (RFC-0026) and Copilot (RFC-0024) precedent. Approve the seven decisions below.
- **Why now (SCQA):**
  - *Situation.* The catalogue ships five reference adapters (Claude Code, Codex, Copilot, Kiro IDE, Kiro CLI) and RFC-0026 has accepted a sixth (Cursor). Gemini CLI is named as an `AGENTS.md` reader in the root `AGENTS.md` and as a deferred APM hook-firing target in the `apm-install-route-parity` spec.
  - *Complication.* The support matrix (`docs/guides/_shared/reference/adapter-support.md`) records Gemini CLI as **"Universal layer only"** — no skills, subagents, commands, or hooks. **That is stale.** As of mid-2026 Gemini CLI has first-class native support for subagents (`.gemini/agents/`), skills (`.gemini/skills/`), TOML slash commands (`.gemini/commands/`), and a lifecycle hook system (`hooks` in `.gemini/settings.json`). A Gemini adopter today gets nothing under `.gemini/` and — unlike Cursor — does not even read our shared `AGENTS.md` by default (Gemini's default context file is `GEMINI.md`).
  - *Question.* Should we add a full native Gemini adapter, and how should each primitive map to Gemini's native formats — in particular its model IDs, its tool-name vocabulary, its TOML command format, and its `AGENTS.md` opt-in?
- **Decisions requested:**
  1. **Adapter scope** — recommend **full native adapter** (project all primitives to `.gemini/*`), not a thin adapter and not do-nothing. · default: full · decide-by 2026-06-18.
  2. **Agent tools fidelity** — Gemini subagents **do** carry a per-agent `tools:` allowlist (unlike Cursor). Recommend **keeping `tools:` and mapping the Claude tool names to Gemini's identifiers** (`Read→read_file`, `Bash→run_shell_command`, `Edit→replace`, …) — higher fidelity than the Cursor/Copilot degradation, no allowlist dropped. · default: keep-and-map · decide-by 2026-06-18.
  3. **Model-ID mapping** — recommend a **tier-preserving** alias map to the stable Gemini 2.5 line: `opus → gemini-2.5-pro`, `sonnet → gemini-2.5-flash`, `haiku → gemini-2.5-flash-lite`; omit `model` when the source agent omits it (Gemini defaults to `inherit`). · default: as recommended · decide-by 2026-06-18.
  4. **Commands** — recommend projecting `command` primitives **first-class** via a new `gemini-command-toml` mode (Markdown body → TOML `prompt`/`description`, `$ARGUMENTS`→`{{args}}`), to `.gemini/commands/<name>.toml`. This is the one projection-**mode**-enum addition (it parallels the existing `codex-agent-toml` mode); the decision-5 bridge is a separate, non-mode mechanism. · default: first-class · decide-by 2026-06-18.
  5. **AGENTS.md context bridge** — Gemini does not read `AGENTS.md` by default; without a bridge the universal layer is silently dropped. Recommend **requiring** a managed `context.fileName` entry (`["AGENTS.md", "GEMINI.md"]`) in `.gemini/settings.json`. The *emission mechanism* is the genuinely-open part — no existing contract construct emits a static file with no driving primitive — and is deferred to Open Q2, not decided here. · default: require the bridge; mechanism per Open Q2 · decide-by 2026-06-18.
  6. **Hook-event mapping** — recommend a contract mapping table keyed on the **Claude-Code source event names the shipped wiring uses** (PascalCase, e.g. `[[hooks.SessionStart]]`) — mirroring the `copilot-hooks-json` `_EVENT_MAP`, **not** the lowercase Kiro `agent-event-vocabulary` — mapping **with zero drops** (`SessionStart→SessionStart`, `UserPromptSubmit→BeforeAgent`, `PreToolUse→BeforeTool`, `PostToolUse→AfterTool`, `Stop→AfterAgent`, `SessionEnd→SessionEnd`); fail-closed on an unrecognised event. · default: as recommended · decide-by 2026-06-18.
  7. **Self-host** — recommend **distribution-only** (do **not** add `gemini` to `SELF_HOST_ADAPTERS`), matching Copilot/Kiro/Cursor (Codex is the only non-Claude adapter this repo self-hosts). · default: distribution-only · decide-by 2026-06-18.

All seven carry the user's prior sign-off; this RFC records the reasoning and the precise mappings for review.

## Problem & goals

**Diagnosis.** Adapters exist so that one canonical set of pack primitives (`.apm/skills`, `.apm/agents`, `.apm/hooks`, `.apm/hook-wiring`, `.apm/commands`) projects into each tool's native discovery layout. Gemini CLI is a widely used agentic CLI we do not yet project into. The support matrix lists it as an `AGENTS.md` reader only — and that classification is doubly wrong now: Gemini CLI (a) supports the full primitive set natively, and (b) does not actually read `AGENTS.md` without an opt-in. So a Gemini adopter's experience degrades **below** the "universal layer" we believe we ship: no `.gemini/` artifacts, and the root `AGENTS.md` unread unless they hand-edit settings.

Unlike Cursor (RFC-0026), Gemini does **not** cross-read foreign ecosystems (`.claude/`, `.codex/`), so there is no incidental fallback — the gap is total, not partial. This raises the severity relative to Cursor.

**Goals.**
- A `gemini` adapter that projects skill / agent / hook-body / hook-wiring / command to Gemini's native paths at both repo and user scope.
- Full fidelity where Gemini supports it — including the `tools:` allowlist and a real model-ID mapping, both of which Gemini supports natively and which Cursor could not.
- Honour the canonical `AGENTS.md` via a managed `context.fileName` bridge, so the universal layer is never silently dropped.
- Zero new behaviour for the existing adapters; a contract version bump plus exactly one new projection mode (`gemini-command-toml`).

**Non-goals.**
- *MCP projection.* Gemini reads `mcpServers` in settings.json and inline per-subagent, but the catalogue has no MCP primitive for *any* adapter today; adding one is a separate cross-adapter RFC.
- *`GEMINI.md` projection.* The shared-context need is met by bridging `AGENTS.md` into `context.fileName`; emitting a second `GEMINI.md` would duplicate the universal layer. Deliberately dropped (see Options).
- *Gemini 3 preview model line.* The alias map targets the stable 2.5 line; pinning `gemini-3-*-preview` IDs (which churn) is deliberately deferred — a future re-point is a contract bump, not a redesign.
- *Self-hosting this repo onto Gemini.* Out of scope per decision 7.
- *Remote (A2A) subagents, `temperature`/`max_turns`/`timeout_mins` tuning.* We project `local` subagents with our existing frontmatter fields; Gemini's extra knobs take their documented defaults.

## Proposal

A new `gemini` adapter module (`packages/agentbundle/agentbundle/build/adapters/gemini.py`), registered in `adapters/__init__.py`, driven by a new `[adapter.gemini]` block in `packages/agentbundle/agentbundle/_data/adapter.toml` (contract bump **v0.11 → v0.12**, post-Cursor — see Open Q1), mirrored byte-for-byte to `docs/contracts/adapter.toml`.

This is a larger contract change than RFC-0026's "block + version bump only," along **two** surfaces:
1. **One new projection mode** (`gemini-command-toml`), added to the `mode` enum in `adapter.schema.json` and its `docs/contracts/` mirror — because Gemini's command format is TOML, not the Markdown every other command-capable tool uses. Every other *primitive* reuses an existing enumerated mode.
2. **A static, primitive-less settings emission** for the `AGENTS.md` bridge (decision 5). No existing contract construct expresses this — every projection today is driven by a source primitive. The mechanism is Open Q2, not assumed solved.

### Projection table

Scope-agnostic emission (repo-relpaths), with the `~/.gemini/…` user-scope home produced by the install handler's prefix rewrite — the Copilot/Cursor pattern.

| Primitive | Mode | Repo target | User target (via rewrite) | Notes |
|---|---|---|---|---|
| `skill` | `direct-directory` | `.gemini/skills/<name>/` | `~/.gemini/skills/<name>/` | `SKILL.md` format is identical to ours — straight copy. Gemini also reads a `.agents/skills/` alias, but `.gemini/skills/` is the precedence-winning native path. |
| `agent` | `direct-file` + frontmatter-mapping `gemini-agent-frontmatter-v0.NN` | `.gemini/agents/<name>.md` | `~/.gemini/agents/<name>.md` | MD + YAML frontmatter, body = system prompt; Kiro-IDE shape. See mapping below. |
| `hook-body` | `direct-file` | `tools/hooks/<name>.{sh,py}` | `~/.agentbundle/.../hooks/<name>.{sh,py}` | Hook scripts referenced by absolute/relative command from settings.json. |
| `hook-wiring` | `merge-json` (managed-key `hooks`) | `.gemini/settings.json` | `~/.gemini/settings.json` | Merge into the `hooks` key; event mapping below. |
| `command` | `gemini-command-toml` (**new mode**) | `.gemini/commands/<name>.toml` | `~/.gemini/commands/<name>.toml` | MD body → TOML `prompt`; description → `description`; subdir `/` → `:` namespacing. |

Gemini consumes none of the Kiro-only primitives. `kiro-ide-hook` is a declared primitive (`[primitive."kiro-ide-hook"]`) that happens to be absent from the projection-array `primitive` enum; adapters that consume or drop it use the `[adapter.<name>.projections.kiro-ide-hook]` table form (kiro-ide activates it, kiro-cli drops it). Gemini declares no row for it, so it neither projects nor drops it — consistent with how Codex/Copilot/Cursor leave it unmentioned.

Additionally, a **static adapter-level emission** writes the `AGENTS.md` context bridge into the same `.gemini/settings.json` (managed-key `context`) — see decision 5. The exact mechanism for a static, primitive-less merge is settled in the implementing spec (Open Q2).

Scope block:

```toml
[adapter.gemini.scope]
repo = "."
user = "~"
allowed-prefixes.repo = [".gemini/", ".agentbundle/", "tools/hooks/"]
allowed-prefixes.user = [".gemini/", ".agentbundle/"]
```

### Agent frontmatter mapping (`gemini-agent-frontmatter-v0.NN`)

Gemini subagent frontmatter fields are `name`, `description`, `kind`, `tools`, `mcpServers`, `model`, `temperature`, `max_turns`, `timeout_mins` (the last four default to `local` / `inherit` / `1` / `30` / `10`). We map the four Claude-style fields and let the rest default:

- `name` → `name` (passthrough; Gemini slug rules — lowercase, digits, `-`, `_` — match ours).
- `description` → `description` (passthrough).
- `tools` → `tools` with a **name-translation `values` map** (mirrors `codex-agent-frontmatter`'s `tools` block, `normalize = "to-list"`):

  | Claude tool | Gemini identifier |
  |---|---|
  | `Read` | `read_file` |
  | `Grep` | `grep_search` |
  | `Glob` | `glob` |
  | `Edit` | `replace` |
  | `Write` | `write_file` |
  | `Bash` | `run_shell_command` |
  | `WebFetch` | `web_fetch` |
  | `WebSearch` | `google_web_search` |
  | `LS` | `list_directory` |

  A Claude tool with no Gemini identifier is dropped from the list with a build-time log line (no silent truncation). Note `Edit → replace` — Gemini's in-place edit tool is named `replace`, not `edit`. (No shipped agent currently declares `LS`, but it is mapped rather than omitted so a future one is not silently degraded.)
- `model` → `model` with a **tier-preserving `values` map**:

  | Claude alias | Gemini model ID | Positioning |
  |---|---|---|
  | `opus` | `gemini-2.5-pro` | most advanced / flagship |
  | `sonnet` | `gemini-2.5-flash` | best price-performance / balanced |
  | `haiku` | `gemini-2.5-flash-lite` | fastest / most budget-friendly |

  Provenance: `gemini-2.5-pro`/`gemini-2.5-flash` are confirmed on the CLI model-selection page; `gemini-2.5-flash-lite` is confirmed on the [Gemini API models page](https://ai.google.dev/gemini-api/docs/models) (the CLI page names "Flash-Lite" without the ID), so the implementing spike should verify it first. When the source agent omits `model`, emit nothing — Gemini defaults to `inherit`. (Codex collapses `opus`/`sonnet` to one ID and re-separates them with a `model_reasoning_effort` knob; Gemini's subagent frontmatter has no reasoning knob, so the cost/performance tiers must live in the model ID itself — hence three distinct targets.)

### Command mapping (`gemini-command-toml`)

Our `command` primitives are Markdown (optional frontmatter + body). Gemini commands are TOML:

```toml
description = "<from frontmatter description, or generated from filename>"
prompt = """
<the Markdown command body>
"""
```

- Frontmatter `description` → TOML `description` (omitted → Gemini generates one from the filename).
- Markdown body → TOML `prompt` (multi-line string).
- Argument tokens map to Gemini's `{{args}}` single-injection form. The exact rule — and how positional `$1…` (which `{{args}}` does not natively distinguish) are handled — is the recommended default in Open Q3, pinned and tested in the implementing spec rather than decided here.
- Sub-directory namespacing: `commands/git/commit.md` → `.gemini/commands/git/commit.toml` → `/git:commit`.

### Hook-event mapping

Our shipped hook-wiring keys on Claude-Code's PascalCase event names (the live `packs/core/.apm/hook-wiring/session-start.toml` uses `[[hooks.SessionStart]]`), and the `copilot-hooks-json` `_EVENT_MAP` keys on exactly those source names. The Gemini map follows that precedent — **not** the lowercase `agent-event-vocabulary`, which is a Kiro-only construct for the `merge-into-agent-json` mode. It maps with **no event dropped**:

| Source event (Claude-Code) | Gemini event | Gemini semantics (verbatim) |
|---|---|---|
| `SessionStart` | `SessionStart` | "When a session begins (startup, resume, clear)" |
| `SessionEnd` | `SessionEnd` | "When a session ends (exit, clear)" |
| `UserPromptSubmit` | `BeforeAgent` | "After user submits prompt, before planning" |
| `PreToolUse` | `BeforeTool` | "Before a tool executes" |
| `PostToolUse` | `AfterTool` | "After a tool executes" |
| `Stop` | `AfterAgent` | "When agent loop ends" |

The source→Gemini event map mirrors `copilot-hooks-json`'s `_EVENT_MAP` (a `dict` keyed on the PascalCase source event, fail-closed on a `KeyError`); whether it lives as a new contract field or adapter-code logic is settled in the implementing spec to match the copilot precedent. Wiring merges into `.gemini/settings.json` under `hooks`, shape `{ "hooks": { "<Event>": [ { "matcher": "...", "hooks": [ { "type": "command", "command": "..." } ] } ] } }`; a source `matcher` passes through unchanged. An unrecognised source event **fails the build** (the copilot precedent), never a silent drop.

### Migration path

None for existing state — additive. A Gemini adopter installs the `gemini` adapter fresh. Packs opt in by adding `"gemini"` to `allowed-adapters` (default stays `["claude-code"]`).

## Options considered

**Axis: how much of Gemini's native surface we project into** — exhaustive from "nothing" to "everything Gemini reads," grounded in how the existing adapters chose their surface (Claude Code = everything; Copilot = everything-it-supports with documented drops; Kiro = everything with a CLI/IDE split; Cursor (RFC-0026) = full native).

| Option | What it does | Trade-off |
|---|---|---|
| **A. Do-nothing** | Rely on Gemini reading root `AGENTS.md` | Zero cost now — but Gemini does **not** read `AGENTS.md` by default and does **not** cross-read `.claude/`, so the adopter gets *nothing*. Worse than the Cursor do-nothing baseline, which at least had cross-reading. Cost of delay grows with Gemini adoption. |
| **B. Thin adapter** | Project only the `context.fileName` bridge + skills, lean on nothing for agents/hooks/commands | Least code; restores the universal layer; but leaves agents, hooks, and commands unprojected even though Gemini supports all three natively — an arbitrary, hard-to-explain partial. |
| **★ C. Full native adapter** | Project every primitive to `.gemini/*` at both scopes + the `AGENTS.md` bridge | Most work (one new mode + a static settings emission); but self-contained, matches every existing adapter's shape, and is the only option that restores the universal layer *and* delivers the native primitives Gemini supports. |

**Recommended: C.** A Gemini adopter gets nothing today; B restores only part of what Gemini can consume; C is the only option consistent with the catalogue's one-adapter-per-tool model and with the "don't silently drop supported capability" principle that motivated this RFC.

## Risks & what would make this wrong

**Pre-mortem.**
- *Gemini changes its `.gemini/` layout or renames a tool/event/model.* Mitigation: paths, tool names, event names, and model IDs all live in the version-pinned contract; a change is a contract bump, not a code rewrite — same exposure as every other adapter. The tool/event/model vocabularies were confirmed against current official docs (see Evidence).
- *`settings.json` merge clobbers an adopter's existing file.* Mitigation: `merge-json` with managed keys (`hooks`, `context`) — never whole-file overwrite (the Codex `hooks.json` precedent). The implementing spec must add a merge test against a pre-populated `settings.json` carrying both keys.
- *Command arg-translation mistranslates `$ARGUMENTS`/`$1`* into broken `{{args}}`, silently producing a command that drops its input. Mitigation: pin and test the arg-translation rule in the spec; the single live consumer (`conventions-check.md`) takes no args, so the first projection is low-risk, but the rule must be correct before a second command lands.
- *Model alias re-points.* If Google promotes Gemini 3 to GA and deprecates 2.5, the alias map points at aging models. Mitigation: stable-line choice is deliberate and a re-point is a one-line contract bump; flagged as a known follow-up.
- *Modeled on the Cursor precedent — now built.* RFC-0026 (Cursor) **merged** at v0.11 (#273), so the scope-agnostic-emission + install-time prefix-rewrite pattern this RFC reuses is now proven in code, and Cursor's diff is the worked reference for every hand-maintained site Gemini touches. Residual risk: a *third* adapter landing before this PR merges would re-trigger the co-bump rebase trap — re-pin the version if so.

**Key assumptions (falsifiable).**
- Gemini CLI reads `.gemini/{skills,agents,commands}`, `.gemini/settings.json` (`hooks` + `context`), and the user-scope `~/.gemini/…` equivalents. *(Verified against current Gemini CLI docs — see Evidence.)*
- Gemini's `settings.json` tolerates multiple managed keys and ignores unknown ones, so a `merge-json` managed-key write is safe. *(Documented multi-key settings; foreign-key tolerance to be spike-tested in the implementing spec.)*
- The tool mapping covers every tool our shipped agents declare (verified: shipped agents use only `Read`/`Grep`/`Glob`/`Bash`/`Edit`/`Write`/`WebFetch`/`WebSearch`); any unmapped tool is logged, not silently dropped. *(To be asserted by a test that scans shipped agent frontmatter against the mapping.)*
- All five hook-wiring events have a Gemini target. *(Confirmed — zero drops — against the full 11-event lifecycle list.)*

**Drawbacks.** Net-new adapter code + tests; **one new projection mode** (`gemini-command-toml`) — a larger contract surface than RFC-0026, which introduced none; a contract version bump that ripples to every adapter's version-compare test (a known trap on bumps); and a static, primitive-less settings emission (the `context` bridge) that no existing adapter has, needing a small new mechanism. These are accepted as the honest cost of Gemini's TOML-command and opt-in-context design.

## Evidence & prior art

**Spike / de-risk result.** Riskiest assumption: that a full Gemini adapter is *mechanical* and needs at most a small contract change. Checked each primitive against current official documentation:
- Subagents — `.gemini/agents/*.md` (and `~/.gemini/agents/*.md`), MD + YAML frontmatter (`name`/`description`/`kind`/`tools`/`mcpServers`/`model`/`temperature`/`max_turns`/`timeout_mins`), body = system prompt, `tools:` allowlist with wildcards, `model` defaults `inherit`. [Subagents docs](https://geminicli.com/docs/core/subagents/)
- Tools — model-facing identifiers `read_file`, `write_file`, `replace`, `glob`, `grep_search`, `list_directory`, `read_many_files`, `run_shell_command`, `web_fetch`, `google_web_search`, `ask_user`, `activate_skill`, … [Tools reference](https://geminicli.com/docs/reference/tools/)
- Models — selectable IDs `gemini-3-pro-preview`, `gemini-3-flash-preview`, `gemini-2.5-pro`, `gemini-2.5-flash`; Flash-Lite ID `gemini-2.5-flash-lite` (most budget-friendly). [Model selection](https://geminicli.com/docs/cli/model/) · [Gemini API models](https://ai.google.dev/gemini-api/docs/models)
- Commands — TOML `prompt`/`description` in `.gemini/commands/` (project) and `~/.gemini/commands/` (user); subdir → `:` namespacing; `{{args}}` injection. [Custom commands](https://geminicli.com/docs/cli/custom-commands/)
- Skills — `SKILL.md` in `.gemini/skills/` or `.agents/skills/` alias (workspace) and `~/.gemini/skills/` / `~/.agents/skills/` (user); discovered at session start, activated via `activate_skill`. [Skills](https://geminicli.com/docs/cli/skills/)
- Hooks — `hooks` key in `.gemini/settings.json` + `~/.gemini/settings.json`; 11 lifecycle events (`SessionStart`, `SessionEnd`, `BeforeAgent`, `AfterAgent`, `BeforeModel`, `AfterModel`, `BeforeToolSelection`, `BeforeTool`, `AfterTool`, `PreCompress`, `Notification`); matcher (regex for tool events, exact for lifecycle). [Hooks](https://geminicli.com/docs/hooks/) · [Hooks reference](https://geminicli.com/docs/hooks/reference/)
- Context — default `GEMINI.md`; `context.fileName` array bridges `AGENTS.md`. [Context files](https://geminicli.com/docs/cli/gemini-md/)

Conclusion: all five primitives map; the only fidelity loss is dropping unmapped tools (logged). The contract change is **one new mode + a static context emission**, larger than Cursor's but bounded and precedented (`codex-agent-toml`; managed-key merge). No redesign needed.

**Repo precedent.**
- RFC-0026 (Cursor full-parity adapter, Accepted) — the template this RFC follows: scope-agnostic emission + install-time user-scope rewrite, per-file agent `.md` via a frontmatter-mapping, contract bump, distribution-only. Gemini diverges by *keeping* the tool allowlist (Cursor dropped it) and *adding* one projection mode (Cursor added none).
- RFC-0024 / ADR-0013 (Copilot) — documented degradation for unmappable fields; the precedent for dropping-with-a-log rather than failing.
- `_data/adapter.toml` — `codex-agent-frontmatter-v0.8` is the exact pattern for the `tools` `values` map (`normalize = "to-list"`) and the `model` `values` map; `codex-agent-toml` is the precedent for a tool-specific non-Markdown projection mode; `copilot-hooks-json`'s `_EVENT_MAP` (keyed on PascalCase source events, fail-closed) is the precedent for the hook-event map.
- spec `apm-install-route-parity` (AC17) — already names Gemini as a deferred APM hook-firing target. **Coordination point:** the implementing spec should confirm the route-parity layer and this adapter agree on Gemini's user-scope home.
- `self_host.py` — `SELF_HOST_ADAPTERS = ("claude-code", "codex")`; decision 7 leaves it unchanged.

**External prior art.** Gemini CLI documents reading the provider-agnostic `AGENTS.md` filename via `context.fileName`, and the broader agentic-CLI/IDE field (Cursor reading `.claude/`/`.codex/`, the `AGENTS.md` convention) is converging on a shared primitive vocabulary — the premise of this whole adapter catalogue.

## Open questions

1. **Contract version sequencing with RFC-0026.** ✅ **Resolved (2026-06-11):** the Cursor adapter (RFC-0026 / ADR-0015) merged at contract **`0.11`** (#273), so this adapter bumps **`0.11 → 0.12`**. The implementing spec/plan were rebased on the merged Cursor block and inherit its hand-maintained-site touch-list.
2. **Static `context` bridge mechanism.** The `AGENTS.md` → `.gemini/settings.json` `context.fileName` write has no driving primitive; needs either a static adapter-level emission or folding into the same managed-merge that writes `hooks`. · *Recommended default:* a single managed-merge into `.gemini/settings.json` carrying both `context` and `hooks` keys, mechanism pinned in the spec. · owner: eugenelim · decide-by: implementing spec.
3. **Argument-token translation rule.** Exact `$ARGUMENTS`/`$1…` → `{{args}}` mapping for `gemini-command-toml` (Gemini's single-injection form differs from positional). · *Recommended default:* map `$ARGUMENTS` → `{{args}}` and log any positional `$1…` as unsupported; the one live command takes no args, so this is pin-and-test in the spec. · owner: eugenelim · decide-by: implementing spec.

## Follow-on artifacts

Filled in on acceptance:
- [ADR-0016](../adr/0016-gemini-cli-full-parity-adapter.md): Gemini CLI full-parity distribution adapter (records the seven decisions). Cursor took ADR-0015.
- Spec: `docs/specs/gemini-full-parity/` (+ plan) — adapter module, `[adapter.gemini]` contract block, `gemini-agent-frontmatter` (tool + model `values` maps) + `gemini-command-toml` mode + hook-event mapping tables, `context.fileName` bridge, contract version bump + `gemini-command-toml` mode-enum addition, unit tests in `build/tests/test_adapter_gemini.py` (incl. settings.json multi-managed-key merge test), `allowed-adapters` acceptance, CI wiring, support-matrix (`docs/guides/_shared/reference/adapter-support.md`) correction from "Universal layer" to its true tier, root `AGENTS.md` line.
- Contract bump `packages/agentbundle/agentbundle/_data/adapter.toml` **v0.11 → v0.12**, mirrored to `docs/contracts/adapter.toml`, with the new `gemini-command-toml` mode added to both `adapter.schema.json` mirrors.
- Spec + plan: [`docs/specs/gemini-full-parity/`](../specs/gemini-full-parity/spec.md) (Approved).
