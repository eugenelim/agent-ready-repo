# ADR-0016: Gemini CLI is a full-parity distribution adapter

- **Status:** Accepted — **partially amended:** the **skill-home sub-decision** (`skill` → `.gemini/skills/<name>/`, with "the `.agents/skills/` alias is not relied on") is **superseded by [ADR-0040](0040-route-cohort-skills-to-shared-agents-skills-home.md)** (cohort skills route to the shared `.agents/skills/`, which Gemini now prefers, 2026-06-26); the agent / hook / command / context-bridge projection decisions in this ADR stand.
- **Date:** 2026-06-11
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0027](../rfc/0027-gemini-cli-full-parity-adapter.md) (the decision), [RFC-0026](../rfc/0026-cursor-full-parity-adapter.md) / ADR-0015 (Cursor full-parity adapter — the immediate precedent and template), [RFC-0024](../rfc/0024-copilot-subagent-projection.md) / [ADR-0013](0013-copilot-full-parity-user-scope-adapter.md) (Copilot full-parity, scope-agnostic emission + user-scope rewrite), [ADR-0004](0004-repo-scope-per-adapter-projection.md) (per-adapter projection model), [ADR-0002](0002-install-scope-per-pack-default-and-allowance.md) (scope dimension)

> **Numbering note.** Confirmed: the Cursor adapter (RFC-0026) merged first (#273), taking **ADR-0015**; this record is **ADR-0016**.

## Context

The adapter catalogue projects one canonical set of pack primitives (`.apm/skills`, `.apm/agents`, `.apm/hooks`, `.apm/hook-wiring`, `.apm/commands`) into each tool's native discovery layout. Gemini CLI was classified in `docs/guides/_shared/reference/adapter-support.md` as a **"Universal layer" / `AGENTS.md` reader only** — no skills, subagents, commands, or hooks.

That classification is stale in **both** directions, confirmed against current official Gemini CLI documentation (RFC-0027 § Evidence):

- Gemini CLI now has **first-class native support** for subagents (`.gemini/agents/*.md`), skills (`.gemini/skills/`, plus a `.agents/skills/` alias), TOML slash commands (`.gemini/commands/*.toml`), and an 11-event lifecycle hook system (`hooks` in `.gemini/settings.json`).
- Gemini CLI does **not read `AGENTS.md` by default** (its default context file is `GEMINI.md`); the shared filename is honoured only when `context.fileName` is configured.

So a Gemini adopter today gets **nothing** under `.gemini/`, and — unlike Cursor, which cross-reads `.claude/`/`.codex/` — Gemini has no incidental fallback. The gap is total, not partial.

## Decision

**We treat `gemini` as a full-parity distribution adapter: it projects every primitive Gemini CLI supports (skill, agent, hook-body, hook-wiring, command) to Gemini's native `.gemini/*` layout at both repo and user scope, and bridges the canonical `AGENTS.md` into Gemini's context discovery.** It follows the scope-agnostic-emission + install-time prefix-rewrite pattern established for Copilot (ADR-0013) and Cursor (ADR-0015).

Concretely (contract bump **v0.11 → v0.12**, post-Cursor):

1. **`skill`** → `direct-directory` to `.gemini/skills/<name>/` (+ `~/.gemini/skills/`). `SKILL.md` format is identical; straight copy. (`.gemini/skills/` is the precedence-winning native path; the `.agents/skills/` alias is not relied on.)
2. **`agent`** → `direct-file` + a `gemini-agent-frontmatter` mapping to `.gemini/agents/<name>.md` (+ `~/.gemini/agents/`). Body becomes the system prompt.
3. **`hook-body`** → `direct-file`; **`hook-wiring`** → `merge-json` (managed-key `hooks`) into `.gemini/settings.json` (+ `~/.gemini/settings.json`).
4. **`command`** → a **new `gemini-command-toml` mode**: Markdown body → TOML `prompt`/`description` at `.gemini/commands/<name>.toml` (+ user scope). Gemini is the third adapter (after Claude Code and Cursor) to honour commands; it is the first whose command format is TOML rather than Markdown, hence the new mode.
5. **`AGENTS.md` context bridge** — a managed `context.fileName = ["AGENTS.md", "GEMINI.md"]` entry written into `.gemini/settings.json`, so the universal layer is honoured rather than silently dropped. This is a static, primitive-less emission with no existing contract construct; its mechanism is settled in the implementing spec.

**Agent frontmatter mapping** (`gemini-agent-frontmatter`):
- `name` / `description` → passthrough (Gemini's slug rules match ours).
- `tools` → **kept and name-mapped** (Gemini subagents carry a real per-agent allowlist, unlike Cursor): `Read→read_file`, `Grep→grep_search`, `Glob→glob`, `Edit→replace`, `Write→write_file`, `Bash→run_shell_command`, `WebFetch→web_fetch`, `WebSearch→google_web_search`, `LS→list_directory`. An unmapped tool is dropped with a build-time log line (no silent truncation).
- `model` → **tier-preserving** map: `opus→gemini-2.5-pro`, `sonnet→gemini-2.5-flash`, `haiku→gemini-2.5-flash-lite`. When the source omits `model`, emit nothing (Gemini defaults to `inherit`). Codex collapses opus/sonnet to one ID and re-separates them via `model_reasoning_effort`; Gemini's subagent frontmatter has no reasoning knob, so the cost/performance tiers must live in the model ID itself.

**Hook-event mapping** — keyed on the Claude-Code PascalCase source events the shipped wiring uses (mirroring `copilot-hooks-json`'s `_EVENT_MAP`, not the lowercase Kiro `agent-event-vocabulary`), mapping to Gemini's lifecycle events with **zero drops**: `SessionStart→SessionStart`, `SessionEnd→SessionEnd`, `UserPromptSubmit→BeforeAgent`, `PreToolUse→BeforeTool`, `PostToolUse→AfterTool`, `Stop→AfterAgent`; fail-closed on an unrecognised event.

**Distribution-only.** `gemini` is **not** added to `SELF_HOST_ADAPTERS` (`("claude-code", "codex")` stays); this repo does not self-host onto Gemini, matching Copilot/Kiro/Cursor. Packs opt in by adding `"gemini"` to `allowed-adapters` (default stays `["claude-code"]`).

## Consequences

**Positive:**
- A Gemini adopter goes from *nothing* to skills + subagents + commands + hooks at both scopes, with the universal `AGENTS.md` layer restored.
- Higher agent fidelity than Cursor: the `tools:` allowlist is preserved (Cursor had to degrade it to `readonly`) and a real model-ID map is applied (Cursor passed model through).
- Reuses the Copilot/Cursor scope-agnostic-emission + prefix-rewrite plumbing rather than inventing it.

**Negative:**
- A **larger contract surface than Cursor's** (which added no mode): one new projection mode (`gemini-command-toml`) **and** a static, primitive-less settings emission for the `context` bridge — a construct no existing adapter has.
- A contract version bump ripples to every adapter's version-compare test (a known trap on bumps).
- New adapter module + tests to maintain; `.gemini/` widens the adopter-collision surface (absorbed by the Tier-1/2/3 + `.upstream.*` companion mechanism).

**Neutral / to revisit:**
- The alias map targets the stable Gemini 2.5 line, not `gemini-3-*-preview` (preview IDs churn); a re-point when Gemini 3 reaches GA is a one-line contract bump.
- `gemini-2.5-flash-lite` is sourced from the Gemini API models page (the CLI model-selection page names "Flash-Lite" without the ID); the implementing spike verifies it first.
- This record models on RFC-0026 (Cursor), now **merged** at v0.11 (#273); the spec was rebased onto it and inherits its proven scope-agnostic-emission + prefix-rewrite pattern and its hand-maintained-site touch-list.

## Alternatives considered

- **Do nothing (keep "Universal layer").** Rejected: Gemini reads no `.gemini/` artifacts *and* does not read `AGENTS.md` by default, so the adopter gets nothing — worse than the Cursor do-nothing baseline, which at least had cross-reading.
- **Thin adapter (bridge + skills only).** Rejected: leaves agents, hooks, and commands unprojected even though Gemini supports all three natively — an arbitrary partial.
- **Drop `tools:` like Cursor.** Rejected: Gemini *has* a per-agent allowlist; dropping it would discard fidelity Gemini supports natively.
- **Collapse opus/sonnet to one model ID (Codex-style).** Rejected: Codex re-separates them via `model_reasoning_effort`; Gemini has no equivalent knob, so collapsing would erase the cost/performance tier the user explicitly cares about.
- **Project a `GEMINI.md` instead of bridging `AGENTS.md`.** Rejected: duplicates the universal layer; the `context.fileName` bridge keeps `AGENTS.md` canonical (RFC-0027 Non-goals).

## References

- [RFC-0027](../rfc/0027-gemini-cli-full-parity-adapter.md) — full analysis, the seven decisions, options, and the doc-confirmed Gemini CLI capability evidence.
- [RFC-0026](../rfc/0026-cursor-full-parity-adapter.md) / ADR-0015 — the Cursor full-parity adapter this record is modeled on.
- [ADR-0013](0013-copilot-full-parity-user-scope-adapter.md) — the Copilot scope-agnostic-emission + user-scope-rewrite + documented-degradation precedent.
- [ADR-0004](0004-repo-scope-per-adapter-projection.md), [ADR-0002](0002-install-scope-per-pack-default-and-allowance.md) — the per-adapter projection model and scope dimension this extends.
