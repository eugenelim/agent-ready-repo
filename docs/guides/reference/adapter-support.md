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
| **Copilot** | ✅ native (`SKILL.md`) | ✅ native (web on CLI/app) | ❌ tool-side | ⚠️ user-scope fires; repo-scope trust-gated | **Partial** |
| **Cursor** | ✅ native | ⚠️ native, no tool allowlist | ✅ native | ✅ native + `.cursor/hooks.json` merge | **Full**² |
| **Kiro CLI** | ✅ native | ✅ native | ❌ tool-side | ✅ body + wiring | **Near-full** |
| **Kiro IDE** | ✅ native | ✅ native | ❌ tool-side | ⚠️ bodies + `.kiro.hook` events; embedded wiring dropped | **Partial** |
| **Any `AGENTS.md` reader** (Gemini CLI, …) | ➖ via `AGENTS.md` | ❌ | ❌ | ❌ | **Universal layer** |

**Legend.** ✅ native — projected to a tool-native file. ➖ — delivered through
the shared `AGENTS.md` universal layer, not a per-tool file. ⚠️ — projected but
with a runtime caveat (see the note). ❌ — not projected.

¹ "Full" bar slash commands — a tool-side limit for Codex and Kiro. Claude Code and
**Cursor** are the two tools that project commands natively (see the note on commands).

² Cursor projects all five primitives, including native slash commands and hooks.
The one fidelity caveat is the subagent **tool allowlist** — see the note below.

## What "Universal layer" means

Every tool in the matrix — and any future tool that reads `AGENTS.md` — inherits
the **universal layer**: the `AGENTS.md` conventions, the source-of-truth map, and
the work-loop discipline, inlined as text the agent reads on every session. That
is the floor, and it is the same everywhere. The columns above are what each tool
gets *on top of* that floor as tool-native primitives. A tool with no native
primitives (Gemini CLI) still runs the loop through `AGENTS.md`; it just
doesn't get per-tool subagent/command/hook files.

## Per-tool caveats

- **Slash commands project to Claude Code and Cursor; they're dropped on the
  others — and that's a tool limit, not a catalogue gap.** Codex deprecated custom
  prompts in favour of skills (which the catalogue *does* project to Codex, at
  `.agents/skills/`); the Copilot CLI won't load custom slash-command files by
  design — prompt files were superseded by skills there too (copilot-cli#618/#1113),
  and the catalogue projects Copilot skills as instruction files
  (`.github/instructions/`); and Kiro ships no standalone command-file primitive for
  the catalogue to project (Kiro IDE still surfaces slash commands via manual-trigger
  hooks and `inclusion: manual` steering). So on those tools what drops is the
  *slash-invocation surface*, not reusable prompt content — that lives on as skills.
  **Cursor**, by contrast, reads `.cursor/commands/<name>.md`, so the catalogue
  projects commands there natively — the second adapter after Claude Code to honour
  them. The contract marks `command` as `dropped` for the rest rather than inventing
  one; when a tool ships a command-file surface, the mapping is added and tested —
  not projected speculatively.
- **Cursor — subagents have no per-agent tool allowlist.** Cursor subagents inherit
  all parent tools, so the source `tools:` allowlist is dropped on projection; for
  a non-mutating agent (one declaring none of `Edit`/`Write`/`MultiEdit`/`NotebookEdit`)
  the catalogue derives `readonly: true` so reviewer/retrieval subagents stay
  least-privilege, and a mutating agent inherits all tools (no `readonly` emitted).
  Documented degradation. See
  [`cursor-full-parity`](../../specs/cursor-full-parity/spec.md).
- **Copilot — subagents get the `web` tool on the CLI + app.** Custom Copilot
  agents resolve `WebFetch`/`WebSearch` to Copilot's `web` tool (the
  custom-agents reference documents `web` aliasing both), so the `research`
  pack's retrieval subagents keep live web access — they are **not** degraded.
  The only non-coverage is the Copilot **cloud agent** (served via repo
  `.github/` only), which has no `web` tool. (An earlier "no web tool" finding
  from a confounded CLI 1.0.59 probe is corrected in
  [`copilot-skills-and-web`](../../specs/copilot-skills-and-web/spec.md) /
  RFC-0024 § Errata E1.)
- **Copilot — repo-scope hooks load only when the folder is trusted.** Repo-scope
  `.github/hooks/*.json` wiring is byte-correct and correctly placed, and
  `.github/hooks/` *is* a loaded hook source in the current CLI — but loading is
  **conditional** on folder-trust, and in prompt mode (`-p`) on an opt-in, per the
  copilot-cli changelog (1.0.8 / 1.0.41 / 1.0.51). The AC23 acceptance smoke on CLI
  1.0.60 saw the repo-scope hook not fire while the identical **user-scope** hook
  (`~/.copilot/hooks/`) did — the trust gate is the likely cause, not a scope-wide
  regression. One open conditional bug also skips repo hooks on `--resume`
  ([copilot-cli#1503](https://github.com/github/copilot-cli/issues/1503)).
  Re-checked against CLI 1.0.61 (2026-06-09); tracked in the `copilot-full-parity`
  follow-ons.
- **Kiro IDE — hooks split three ways.** Hook *bodies* project (to `tools/hooks/`),
  and standalone `.kiro.hook` IDE-event files **do** project now — the
  `kiro-ide-hook` primitive is active (`.kiro/hooks/<pack>--<name>.kiro.hook`, full
  IDE event vocabulary; RFC-0022, Q6 probe 2026-06-01). What drops is
  **agent-embedded** hook-wiring: the IDE loader silently drops any agent carrying a
  `hooks` key (RFC-0022 E2), so packs expressing hooks through the cross-adapter
  `hook-wiring` primitive get less here than on **Kiro CLI**, which retains it.
  Both Kiro targets also read the universal `AGENTS.md` layer via Kiro steering. See
  [`kiro-adapter-split`](../../rfc/0022-kiro-adapter-split.md).

## Choosing a tool

- Want the whole loop with every primitive? **Claude Code** or **Cursor** (Cursor
  projects skills, subagents, slash commands, and hooks natively; the only fidelity
  loss is the per-agent tool allowlist, replaced by a derived `readonly` flag).
- Terminal-native with near-full parity? **Codex** or **Kiro CLI** (you lose only
  slash commands, which those tools don't have).
- On **Copilot**, expect skills (native `SKILL.md`) + subagents (with web on the
  CLI + app) + user-scope hooks to work, and plan around the repo-hook caveat above.
- On any other `AGENTS.md`-aware tool, you still get the loop and the
  conventions through the universal layer — just no tool-native extras.
