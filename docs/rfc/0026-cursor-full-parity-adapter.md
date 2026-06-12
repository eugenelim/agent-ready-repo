# RFC-0026: Cursor full-parity adapter

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-11
- **Date closed:** 2026-06-11
- **Related:** RFC-0022 (Kiro adapter split) · RFC-0024 / ADR-0013 (Copilot full-parity user-scope adapter) · RFC-0004 (install-scope dimension) · RFC-0005 (user-scope hook support) · spec `apm-install-route-parity` (already treats Cursor as an install target via `${CURSOR_PLUGIN_ROOT}`)

## The ask

- **Recommendation (BLUF):** Add a native `cursor` distribution adapter that projects every catalogue primitive to Cursor's `.cursor/*` discovery paths (and `~/.cursor/*` at user scope), following the Copilot (RFC-0024) and Kiro (RFC-0022) precedent. Approve the five projection decisions below.
- **Why now (SCQA):**
  - *Situation.* The catalogue ships four reference adapters (Claude Code, Kiro, Copilot, Codex). Cursor is already named as an install **target** (`${CURSOR_PLUGIN_ROOT}`, `~/.cursor/extensions/…`) in the `apm-install-route-parity` spec and as an AGENTS.md reader in the root `AGENTS.md`.
  - *Complication.* There is no Cursor **projection** adapter, so a Cursor adopter gets nothing under `.cursor/` — they rely entirely on Cursor incidentally reading our root `AGENTS.md` and any co-installed `.claude/` tree. As of Cursor v2.6 (Feb 2026) Cursor has first-class native support for skills, subagents, hooks, and commands that we project to no other tool today.
  - *Question.* Should we add a full native Cursor adapter, and how should each primitive map to Cursor's native formats?
- **Decisions requested:**
  1. **Adapter scope** — recommend **full native adapter** (project all primitives to `.cursor/*`), not a thin adapter and not do-nothing. · default: full · decide-by 2026-06-18.
  2. **Agent tools fidelity** — Cursor subagents have no per-agent tool allowlist. Recommend: drop the `tools:` allowlist (Cursor inherits all parent tools) and derive a `readonly` flag for non-mutating agents, documenting the degradation. The exact read-only predicate is deferred to the implementing spec (Open Q2). · default: drop-tools + derive-readonly · decide-by 2026-06-18.
  3. **Commands** — recommend projecting `command` primitives **first-class** to `.cursor/commands/<name>.md` (Cursor is the second adapter after Claude Code to honour commands; Copilot/Kiro drop them). · default: first-class · decide-by 2026-06-18.
  4. **Hook-event mapping** — recommend a contract mapping table from our hook-wiring event vocabulary → Cursor's `sessionStart` / `beforeSubmitPrompt` / `preToolUse` / `postToolUse` / `stop`, dropping events with no Cursor equivalent with a build-time log. · default: as recommended · decide-by 2026-06-18.
  5. **Self-host** — recommend **distribution-only** (do **not** add `cursor` to `SELF_HOST_ADAPTERS`), matching Copilot and Kiro. · default: distribution-only · decide-by 2026-06-18.

All five carry the user's prior sign-off; this RFC records the reasoning and the precise mappings for review.

## Problem & goals

**Diagnosis.** Adapters exist so that one canonical set of pack primitives (`.apm/skills`, `.apm/agents`, `.apm/hooks`, `.apm/hook-wiring`, `.apm/commands`) projects into each tool's native discovery layout. Cursor is the most widely used agentic IDE we do not yet project into. Today a Cursor adopter's experience degrades silently to "whatever Cursor picks up from root `AGENTS.md`," with no skills, agents, hooks, or commands under `.cursor/`.

Cursor *does* read some foreign ecosystems for compatibility — confirmed for subagents (`.claude/agents/`, `.codex/agents/`) and skills (`.claude/skills/`, `~/.claude/skills/`). That cross-reading is a reason the gap is **low-severity**, not a reason to skip the adapter: it only helps adopters who *also* installed the Claude Code projection, it gives Cursor nothing under its own precedence-winning `.cursor/` tree, and it does not cover hooks or commands at all.

**Goals.**
- A `cursor` adapter that projects skill / agent / hook-body / hook-wiring / command to Cursor's native paths at both repo and user scope.
- Full fidelity where Cursor supports it; explicit, documented degradation where it does not (agent tool allowlists).
- Zero new behaviour for the four existing adapters; a contract version bump only.

**Non-goals.**
- *MCP projection.* Cursor reads `.cursor/mcp.json`, but the catalogue has no MCP primitive for *any* adapter today; adding one is a separate cross-adapter RFC, not Cursor-specific.
- *`.cursor/rules/*.mdc` projection.* The always-apply context need is already met by Cursor reading root `AGENTS.md` directly; per-skill `.mdc` rules would duplicate the skill projection. Deliberately dropped (see Options).
- *Self-hosting this repo onto Cursor.* Out of scope per decision 5.
- *Cursor CLI vs IDE split.* Cursor's CLI and IDE share the same `.cursor/` discovery layout (unlike Kiro, which forced the RFC-0022 split). One adapter covers both.

## Proposal

A new `cursor` adapter module (`packages/agentbundle/agentbundle/build/adapters/cursor.py`), registered in `adapters/__init__.py`, driven by a new `[adapter.cursor]` block in `_data/adapter.toml` (contract version **0.10 → 0.11**), mirrored byte-for-byte to `docs/contracts/adapter.toml`.

**No new projection mode is introduced.** Every Cursor primitive reuses an existing, already-enumerated mode (`direct-directory`, `direct-file`, `merge-json`, `dropped`) — the agent shape follows the Kiro-IDE pattern (`direct-file` + a `frontmatter-mapping`), not a bespoke mode like Copilot's `copilot-agent-md`. This keeps the projection-mode enum in `adapter.schema.json` (and its `docs/contracts/adapter.schema.json` mirror) untouched, so the contract change is the `[adapter.cursor]` block + a version bump only. The one open risk is whether the `tools → readonly` derivation (decision 2) can be expressed as a declarative frontmatter-mapping; if not, the implementing spec adds a minimal projection helper (the Copilot precedent) rather than a new contract mode.

### Projection table

Scope-agnostic emission (repo-relpaths), with the `~/.cursor/…` user-scope home produced by the install handler's prefix rewrite — exactly the Copilot pattern.

| Primitive | Mode | Repo target | User target (via rewrite) | Notes |
|---|---|---|---|---|
| `skill` | `direct-directory` | `.cursor/skills/<name>/` | `~/.cursor/skills/<name>/` | SKILL.md format is identical to ours — straight copy, like Kiro |
| `agent` | `direct-file` + frontmatter-mapping `cursor-agent-frontmatter-v0.11` | `.cursor/agents/<name>.md` | `~/.cursor/agents/<name>.md` | MD + frontmatter, Kiro-IDE shape; see mapping below |
| `hook-body` | `direct-file` | `.cursor/hooks/<name>.{sh,py}` | `~/.cursor/hooks/<name>.{sh,py}` | Cursor runs project hooks from project root via `.cursor/hooks/…` |
| `hook-wiring` | `merge-json` (managed-key `hooks`) | `.cursor/hooks.json` | `~/.cursor/hooks.json` | single aggregated JSON, `{version:1, hooks:{event:[{command}]}}` |
| `command` | `direct-file` | `.cursor/commands/<name>.md` | `~/.cursor/commands/<name>.md` † | filename → slash-command name |

† Project-scope path is confirmed (Cursor 1.6 changelog); the user-scope `~/.cursor/commands/` home is reported only by secondary sources and is pending Open Q1.
| `kiro-ide-hook` | `dropped` | — | — | Kiro-only primitive |

Scope block:

```toml
[adapter.cursor.scope]
repo = "."
user = "~"
allowed-prefixes.repo = [".cursor/", ".agentbundle/"]
allowed-prefixes.user = [".cursor/", ".agentbundle/"]
```

### Agent frontmatter mapping (`cursor-agent-frontmatter-v0.11`)

Cursor subagent frontmatter fields are `name`, `description`, `model`, `readonly`, `is_background` — **no `tools:` field** (subagents inherit all parent tools).

- `description` → `description` (passthrough).
- `name` → `name` (passthrough; Cursor otherwise derives from filename).
- `model` → `model` (passthrough where a Cursor model id is given; absent → Cursor default `inherit`).
- `tools` → **dropped**, with a derived `readonly: true` for non-mutating agents; otherwise inherit-all. Candidate predicate: read-only when the source `tools:` list contains no mutating tool (no `Edit`/`Write`/`NotebookEdit`). The exact predicate is settled in the implementing spec (Open Q2).
- `is_background` → not emitted (defaults `false`); reserved for future use.

This is the same documented-degradation shape ADR-0013 accepted for Copilot's tool handling.

### Hook-event mapping

Our hook-wiring event vocabulary (`agentSpawn`, `userPromptSubmit`, `preToolUse`, `postToolUse`, `stop` — the set Kiro already enumerates) maps to Cursor's `hooks.json` events:

| Our event | Cursor event |
|---|---|
| `agentSpawn` | `sessionStart` |
| `userPromptSubmit` | `beforeSubmitPrompt` |
| `preToolUse` | `preToolUse` |
| `postToolUse` | `postToolUse` |
| `stop` | `stop` |

Any source event with no Cursor target is dropped with a build-time log line (no silent truncation — per the catalogue's no-silent-caps rule). The mapping table lives in the contract, not the adapter code.

### Migration path

None for existing state — additive. A Cursor adopter installs the `cursor` adapter fresh. Packs opt in by adding `"cursor"` to `allowed-adapters` (default stays `["claude-code"]`).

## Options considered

**Axis: how much of Cursor's native surface we project into** — exhaustive from "nothing" to "everything Cursor reads," grounded in how the existing four adapters chose their surface (Claude Code = everything; Copilot = everything-it-supports with documented drops; Kiro = everything with a CLI/IDE split).

| Option | What it does | Trade-off |
|---|---|---|
| **A. Do-nothing** | Rely on Cursor reading root `AGENTS.md` + any co-installed `.claude/` tree | Zero cost now; but no `.cursor/` artifacts, no hooks, no commands, and a hard dependency on the adopter *also* installing Claude Code. Cost of delay grows as Cursor adoption grows. |
| **B. Thin adapter** | Project only the divergent primitives (skills → `.cursor/skills/`, hooks → `.cursor/hooks.json`, commands → `.cursor/commands/`); lean on `AGENTS.md` + `.claude/agents/` for context + agents | Least code; but bets that `.claude/` is always co-installed, and produces a Cursor tree that's incomplete by precedence (`.cursor/` wins over `.claude/`, so a half-populated `.cursor/` is worse than none) |
| **★ C. Full native adapter** | Project every primitive to `.cursor/*` at both scopes | Most work and some redundancy with Cursor's cross-reading; but self-contained, matches every existing adapter's shape, and unlocks hooks + commands the claude-code projection can't give Cursor |

**Recommended: C.** A Cursor adopter should never be forced to also install the Claude projection; `.cursor/` precedence means a partial tree (B) is actively worse than a complete one; and C is the only option consistent with the catalogue's one-adapter-per-tool model.

## Risks & what would make this wrong

**Pre-mortem.**
- *Cursor changes its `.cursor/` layout.* Mitigation: paths live in the contract, version-pinned; a layout change is a contract bump, not a code rewrite — same exposure as every other adapter.
- *`hooks.json` merge clobbers an adopter's existing file.* Mitigation: `merge-json` with managed-key `hooks` (the Claude Code `settings.local.json` precedent), never whole-file overwrite. The implementing spec must add a merge test against a pre-populated `hooks.json`.
- *Read-only predicate misclassifies an agent*, making a writing agent `readonly: true` (breaks it) or a reviewer inherit-all (over-privileged). Mitigation: conservative predicate (read-only only when zero mutating tools present); pin and test in the spec.

**Key assumptions (falsifiable).**
- Cursor v2.6 reads `.cursor/{skills,agents,commands}`, `.cursor/hooks.json`, and `.cursor/hooks/` at both project and `~/.cursor` scope. *(Verified against current Cursor docs — see Evidence.)*
- Cursor's `hooks.json` accepts multiple `command` entries per event and ignores unknown top-level keys, so a `merge-json` managed-key write is safe. *(Schema confirmed; multi-entry/foreign-key tolerance to be spike-tested in the implementing spec.)*
- Cursor's CLI and IDE share one `.cursor/` layout (no RFC-0022-style split needed). *(Confirmed: CLI and editor follow the same configuration precedence.)*

**Drawbacks.** Net-new adapter code + tests to maintain; a contract version bump that ripples to every adapter's version-compare test (a known trap on bumps); and some projected redundancy for adopters who *also* run Claude Code (Cursor reads both; `.cursor/` simply wins). These are the standard cost of an adapter, accepted four times before.

## Evidence & prior art

**Spike / de-risk result.** Riskiest assumption: that Cursor's native primitive surface actually matches our five primitives closely enough that a full adapter is mechanical, not a redesign. Checked each primitive against current Cursor documentation:
- Skills — `.cursor/skills/<name>/SKILL.md`, `name`/`description` frontmatter, `~/.cursor/skills/` user scope; **also reads `.claude/skills/`** for compatibility. Format is effectively identical to ours → straight directory copy. [Cursor Skills docs](https://cursor.com/docs/skills)
- Subagents — `.cursor/agents/` (and reads `.claude/agents/`, `.codex/agents/`; `.cursor/` wins ties), MD + frontmatter `name`/`description`/`model`/`readonly`/`is_background`, **no tools allowlist**. [Cursor Subagents docs](https://cursor.com/docs/agent/subagents)
- Hooks — `.cursor/hooks.json` and `~/.cursor/hooks.json`, `{version:1, hooks:{event:[{command}]}}`, events incl. `sessionStart`, `preToolUse`, `postToolUse`, `beforeSubmitPrompt`, `stop`; scripts referenced as `.cursor/hooks/script.sh` from project root. [Cursor Hooks docs](https://cursor.com/docs/agent/hooks)
- Commands — "Commands are stored in `.cursor/commands/[command].md`"; filename → command name; `~/.cursor/commands/` for global. [Cursor 1.6 changelog](https://cursor.com/changelog/1-6)
- Rules — root `AGENTS.md` (and nested) read directly; `.cursor/rules/*.mdc` is the conditional-rules alternative (intentionally not a projection target — see Non-goals). [Cursor Rules docs](https://cursor.com/docs/rules)

Conclusion: all five primitives map mechanically; the only fidelity loss is the agent tool allowlist (decision 2). No redesign needed.

**Repo precedent.**
- RFC-0024 / ADR-0013 (Copilot full-parity user-scope adapter) — the template this RFC follows: scope-agnostic emission + install-time user-scope rewrite, per-file agent `.md`, documented tool degradation, distribution-only.
- RFC-0022 / ADR-0012 (Kiro adapter split) — precedent for `merge-into-agent-json` hook wiring and an `agent-event-vocabulary` contract list; Cursor needs the simpler single-file `merge-json` instead.
- `_data/adapter.toml` — Claude Code already projects `command` to `.claude/commands/` (`direct-file`); Kiro and Copilot drop it. The catalogue ships exactly one command primitive today (`packs/core/.apm/commands/conventions-check.md`), so decision 3 has a live consumer.
- spec `apm-install-route-parity` — already wires Cursor as an install target (`${CURSOR_PLUGIN_ROOT}`, `~/.cursor/extensions/…`). **Coordination point:** the install/route layer anticipates Cursor; this RFC adds the missing projection half. The implementing spec should confirm the route-parity per-target tests and this adapter agree on Cursor's user-scope home.

**External prior art.** Cursor itself documents reading foreign-ecosystem primitives (`.claude/`, `.codex/`) for compatibility — direct evidence that the agentic-IDE field is converging on a shared primitive vocabulary, which is the premise of this whole adapter catalogue.

## Open questions

1. **User-scope `~/.cursor/commands/` path** — confirmed for project scope via the 1.6 changelog; the global path is reported only by secondary sources. · *Recommended default:* `~/.cursor/commands/` (mirrors every other user-scope primitive). · owner: eugenelim · decide-by: implementing-spec spike.
2. **Read-only predicate for agents** — exact rule for emitting `readonly: true` (zero mutating tools vs. an explicit allowlist of reviewer agents). · *Recommended default:* zero-mutating-tools predicate, pinned + tested in the spec. · owner: eugenelim · decide-by: implementing spec.

## Follow-on artifacts

Filled in on acceptance:
- ADR-0015: Cursor full-parity distribution adapter (record the five decisions).
- Spec: `docs/specs/cursor-full-parity/` (+ plan) — adapter module, `[adapter.cursor]` contract block, `cursor-agent-frontmatter-v0.11` + hook-event mapping tables, contract version bump (no mode-enum change), unit tests in `build/tests/test_adapter_cursor.py`, `allowed-adapters` acceptance, CI wiring, root `AGENTS.md` line.
- Contract bump `_data/adapter.toml` 0.10 → 0.11, mirrored to `docs/contracts/adapter.toml`.
