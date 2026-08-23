# Hook adapter contract audit

- **Observed:** 2026-08-22
- **Scope:** current `agentbundle` hook adapters plus the external APM package route
- **Local Codex baseline:** `codex-cli 0.149.0`; `codex features list` reported
  `hooks stable false`; the repository contains `.codex/hooks.json` with
  `SessionStart` and `UserPromptSubmit` entries.

This audit separates four questions that the product documentation previously
collapsed: whether a runtime supports hooks, whether `agentbundle` projects a
native hook file, whether the active runtime will execute it, and whether the
hook output is in the runtime's context-injection format.

## Contract sources

- Codex: [Hooks](https://learn.chatgpt.com/docs/hooks)
- Claude Code: [Hooks reference](https://code.claude.com/docs/en/hooks)
- GitHub Copilot: [Hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference)
- Cursor: [Hooks](https://cursor.com/docs/hooks)
- Gemini CLI: [Hooks reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/reference.md)
- Kiro: [Hooks](https://kiro.dev/docs/hooks/)
- APM: [Hooks and commands](https://microsoft.github.io/apm/producer/author-primitives/hooks-and-commands/)

The local projection source is `contracts/adapter.toml`. The portable core
wiring is `packs/core/.apm/hook-wiring/session-start.toml`; its command runs
`packs/core/.apm/hooks/session-start.py`, which emits the adaptation nudge as
plain stdout.

## Adapter findings

| Surface | Current projection | Current upstream contract | Verdict |
| --- | --- | --- | --- |
| Claude Code | `tools/hooks/` plus `.claude/settings.local.json`; nested Claude event shape | Project/local settings carry `hooks`; `SessionStart` accepts plain stdout as context; workspace trust gates settings hooks; `${CLAUDE_PROJECT_DIR}` is the stable project-root reference | Location, event shape, and nudge output are compatible. The relative command is not root-stable after the session cwd changes. |
| Codex | `tools/hooks/` plus `.codex/hooks.json`; nested `SessionStart` shape | Repository `.codex/hooks.json` is supported; project-layer trust, exact-definition hook review, the `hooks` feature, and managed requirements independently gate execution; `SessionStart` accepts plain stdout | Projection exists and its output protocol is compatible. The relative command can fail when Codex starts below the repository root; official guidance prefers git-root resolution. The active managed runtime currently reports hooks disabled. |
| GitHub Copilot | `.github/hooks/<name>.json`; version 1; event and body-path rewrite | Repository `.github/hooks/*.json` and user `~/.copilot/hooks/*.json` are supported; command output is parsed as JSON; `sessionStart` context uses `additionalContext` | File, event, and repo path projection are compatible. The core hook's plain stdout is not a valid context result, so the projected hook does not reliably deliver the nudge. |
| Cursor | `.cursor/hooks.json`; version 1; event and body-path rewrite | Project `.cursor/hooks.json` runs from the project root in trusted workspaces; command hooks return JSON; `sessionStart` context uses `additional_context` | File, event, and repo path projection are compatible. Plain stdout is not the documented output protocol, so the nudge is not reliably injected. |
| Gemini CLI | `.gemini/settings.json`; event and body-path rewrite | Project settings carry nested hooks; `hooksConfig.enabled` and optional folder trust gate execution; command stdout must be one JSON object; `SessionStart` context uses `hookSpecificOutput.additionalContext` | Location, event mapping, and repo path projection are compatible. Plain stdout violates the documented output protocol, so the nudge is not reliably injected. |
| Kiro IDE / CLI | IDE emits legacy `*.kiro.hook`; CLI embeds hooks in agent JSON | IDE 1.0 and CLI 3.0 use standalone `.kiro/hooks/*.json`, schema `version: "v1"`, PascalCase triggers, and `action` objects; command actions receive context on stdin, while agent actions inject prompts | Both direct adapters are stale. Their current hook projections target superseded formats; current tests pin the obsolete formats. The documented contract does not establish command stdout as a context-injection channel, so nudge delivery remains unverified even after schema migration. |
| APM package route | Publishes portable `.apm/hooks/install-marker.json` and its script for APM's HookIntegrator | Current HookIntegrator deploys hook bundles to Claude-family targets (Claude, Cursor, Codex, Gemini, Antigravity, and Windsurf), Copilot, and Kiro; OpenCode remains unsupported | The core README and install-routes guide are stale: Codex, Antigravity, and Windsurf are absent from their current support description. This is separate from direct `agentbundle` adapter behavior. |

## Installation-scope flow for core

This table covers direct `agentbundle install`, not APM or Claude plugin package
routes.

| Scope | Hook projected | Seeds | Marker | Chained CLI `adapt` | Hook nudge | Deterministic `Next:` after this change | Manual action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Repo | Yes, for the selected adapter | Yes | Yes | Yes | Only if the runtime executes the hook and accepts its output protocol | Yes | Ask the agent to run `adapt-to-project`; use the CLI `adapt` command only for deterministic substitution/bookkeeping |
| Local | Yes, into the working tree | No | No | No | No marker exists, so the current hook has nothing to nudge from | Yes | Ask the agent to run `adapt-to-project`; start a new session if the skill is not yet discovered |
| User | Fresh core install is refused because core allows repo scope only | No install | No install | No install | No install | No install | Choose repo or local scope; user scope remains available only to packs that declare it |

## Disposition

### In the current change

- Correct living documentation that says Codex lacks hooks, that APM cannot
  project Codex or Windsurf hooks, that every route writes a marker, or that
  `agentbundle adapt --scope ...` is valid.
- Add a deterministic core installer `Next:` action for every successful repo
  or local install.
- Preserve all local-scope omissions and fresh user-scope refusal.
- Correct portable hook-wiring comments so they no longer describe a
  Claude-only source.

### Separate decision required

- Migrate Kiro IDE and CLI to the current standalone v1 hook schema.
- Add adapter-specific context-output rendering for Copilot, Cursor, and Gemini,
  and determine whether Kiro needs an agent action or another documented
  context-injection mechanism.
- Make Claude Code and Codex repository hook commands root-stable without
  weakening cross-platform command safety.

These deferred adapter repairs are not required to close the triggering local
install case because a local install intentionally has no marker to consume.
The installer handoff must remain sufficient even when a projected hook is
disabled, untrusted, path-broken, output-incompatible, or unsupported.
