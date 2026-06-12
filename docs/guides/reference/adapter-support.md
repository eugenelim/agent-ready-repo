# Adapter support matrix

Which agent tools the catalogue projects to, what each one receives, and where a
tool's own limits mean you get less than the full loop. The README's "any agent
that reads a skill file inherits it" is true for the **universal layer** (the
`AGENTS.md` conventions every tool reads); this page is the honest detail
underneath it — the tool-native primitives, and the caveats.

**Source of truth.** The projection columns below are read from the adapter
contract, `packages/agentbundle/agentbundle/_data/adapter.toml` (each adapter's
`[[adapter.<name>.projection]]` rules). If this table and the contract ever
disagree, the contract wins and the drift is a bug — file it. The *caveats* are
the verified runtime findings recorded in the specs linked per row.

## The matrix

| Tool | Skill | Subagent | Slash command | Hook | Tier |
| --- | --- | --- | --- | --- | --- |
| **Claude Code** | ✅ native | ✅ native | ✅ native | ✅ native + `settings.json` merge | **Full** |
| **Codex** | ✅ native | ✅ native (`.codex/agents/*.toml`) | ❌ tool-side | ✅ native + `.codex/hooks.json` merge | **Full**¹ |
| **Copilot** | ✅ instruction file | ⚠️ native, no web tool | ❌ tool-side | ⚠️ user-scope fires; repo-scope regressed | **Partial** |
| **Kiro CLI** | ✅ native | ✅ native | ❌ tool-side | ✅ body | **Near-full** |
| **Kiro IDE** | ✅ native | ✅ native | ❌ tool-side | ⚠️ body only; wiring dropped | **Partial** |
| **Any `AGENTS.md` reader** (Cursor, Gemini CLI, …) | ➖ via `AGENTS.md` | ❌ | ❌ | ❌ | **Universal layer** |

**Legend.** ✅ native — projected to a tool-native file. ➖ — delivered through
the shared `AGENTS.md` universal layer, not a per-tool file. ⚠️ — projected but
with a runtime caveat (see the note). ❌ — not projected.

¹ "Full" bar slash commands, which no listed tool below Claude Code supports — see
the note on commands.

## What "Universal layer" means

Every tool in the matrix — and any future tool that reads `AGENTS.md` — inherits
the **universal layer**: the `AGENTS.md` conventions, the source-of-truth map, and
the work-loop discipline, inlined as text the agent reads on every session. That
is the floor, and it is the same everywhere. The columns above are what each tool
gets *on top of* that floor as tool-native primitives. A tool with no native
primitives (Cursor, Gemini CLI) still runs the loop through `AGENTS.md`; it just
doesn't get per-tool subagent/command/hook files.

## Per-tool caveats

- **Slash commands are dropped on every tool except Claude Code — and that's a
  tool limit, not a catalogue gap.** Codex deprecated custom prompts, the Copilot
  CLI doesn't yet load custom slash commands, and Kiro has no slash-command
  surface. The contract marks `command` as `dropped` for each rather than
  inventing one. When a tool ships the surface, the mapping is added and tested —
  not projected speculatively.
- **Copilot — subagents have no web tool.** Custom Copilot agents expose
  read/grep/glob but no web fetch/search (verified against CLI 1.0.59), so the
  `research` pack's retrieval subagents lose live web access on Copilot
  (read-only degradation). See
  [`copilot-full-parity`](../../specs/copilot-full-parity/spec.md).
- **Copilot — repo-scope hooks regressed.** Repo-scope `.github/hooks/*.json`
  wiring is byte-correct and correctly placed, but the CLI stopped executing it
  between 1.0.59 and 1.0.60; the identical **user-scope** hook (`~/.copilot/hooks/`)
  still fires. Version-sensitive; tracked in the `copilot-full-parity` follow-ons.
- **Kiro IDE — hook-wiring is dropped.** Hook *bodies* project, but the IDE has no
  settings surface the contract models for wiring, and standalone `.kiro.hook`
  IDE-event files are not yet a contract primitive. The **Kiro CLI** split
  (RFC-0022) is the fuller Kiro target. See
  [`kiro-adapter-split`](../../rfc/0022-kiro-adapter-split.md).

## Choosing a tool

- Want the whole loop with every primitive? **Claude Code.**
- Terminal-native with near-full parity? **Codex** or **Kiro CLI** (you lose only
  slash commands, which those tools don't have).
- On **Copilot**, expect skills + subagents + user-scope hooks to work, and plan
  around the no-web-tool and repo-hook caveats above.
- On any other `AGENTS.md`-aware tool, you still get the loop and the
  conventions through the universal layer — just no tool-native extras.
