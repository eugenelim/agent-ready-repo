# Hook adapter delivery repairs

- **Slug:** `adapter-hook-context-output`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim

## Outcome

- **Steerable input:** Reduce the number of supported runtimes where a projected core hook fails to run, fails to start from its installed path, or runs but does not deliver its context.
- **Lagging outcome:** After a repository install, each runtime that executes the projected hook starts it from any working directory below the repository root and receives the adaptation nudge through that runtime's documented output protocol.
- **Guardrail:** Claude Code and Codex keep their current plain-stdout behavior, non-hook adapter output does not change, and no repair weakens cross-platform command safety. The installer's deterministic `Next:` action stays sufficient when a hook is disabled, untrusted, path-broken, or output-incompatible.

## Opportunity

- **Functional job:** Have a projected session-start hook reach the agent in the runtime the adopter actually uses.
- **Emotional job:** Trust that a hook which projects also delivers, so that a silent miss does not read as a working install.
- **Social job:** Let maintainers state a per-runtime hook support claim that the audit, the projection and the tests all agree on.
- **Struggling moment:** The 2026-08-22 [hook adapter audit](../../specs/codex-hook-adaptation-handoff/hook-adapter-audit.md) found three separate defects behind one symptom, that the nudge does not arrive:
  - **Output protocol.** Copilot, Cursor and Gemini CLI parse hook output as JSON and read context from `additionalContext`, `additional_context` and `hookSpecificOutput.additionalContext`. The core hook prints plain stdout, so they do not reliably inject it. Kiro's documented contract does not establish stdout as a context channel at all.
  - **Hook schema.** The Kiro IDE adapter still emits the legacy `*.kiro.hook` format and the CLI embeds hooks in agent JSON. Kiro IDE 1.x and CLI 3.x use standalone `.kiro/hooks/*.json` with `version: "v1"`, and the current tests pin the superseded formats.
  - **Root-stable dispatch.** The repository `.codex/hooks.json` runs `python tools/hooks/session-start.py`, a command relative to the working directory. It fails when Claude Code or Codex starts below the repository root or changes directory. Claude Code documents `${CLAUDE_PROJECT_DIR}` and Codex guidance prefers git-root resolution.

## Boundary

Includes:

- runtime-specific context output for the projected session-start hook, for the runtimes the audit lists as incompatible;
- migration of Kiro IDE and CLI hook projection to the standalone v1 schema, and the audit's open question of whether Kiro needs an agent action or another documented context channel;
- root-stable commands for the Claude Code and Codex repository hooks.

Excludes:

- the installer's `Next:` handoff, which the audit's own change already delivered;
- changing the portable hook body's intent;
- APM and Claude plugin package routes, which [distribution routes](../../architecture/distribution-routes.md) owns;
- non-hook adapter behavior.

## Assumptions

- Plain stdout remains valid for Claude Code and Codex, so their context behavior does not regress.
- Kiro IDE 1.x and CLI 3.x remain the target contract when this item is shaped.
- The Claude Code and Codex fixes may need different root tokens or dispatch wrappers.

## Unresolved questions

- Whether Kiro has a documented context-injection channel, or the nudge stays unverified there after the schema migration.
- Whether context output is rendered by the projected hook wrapper per adapter or by a mode of the portable hook, and which owner carries the per-runtime protocol.
- Which root-stable form is safe on Windows, given the command-safety guardrail.
- Whether the three defects ship as one spec or as three, since the Kiro migration has the largest blast radius and the root fix the smallest.

## Source

- Mode: repo-origin
- Locator: docs/specs/codex-hook-adaptation-handoff/hook-adapter-audit.md
- Revision: sha256-bytes-v1:3e6d9b52c6316d6fb13eacbd46737a12d5acd437b310ba1eb3d1876df959d8c1
