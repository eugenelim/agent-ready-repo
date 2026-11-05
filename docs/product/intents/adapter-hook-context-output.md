# Hook adapter delivery repairs

- **Slug:** `adapter-hook-context-output`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Decomposed:** 2026-11-05 brief

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

- **Riskiest assumption:** each client's documented hook-output format, last read 2026-08-22, still matches the current client. Slice H2 re-reads the documentation first and builds one parsing fixture per adapter from it; a real client run is manual and non-blocking, so claims stay `documentation-verified`.

- Plain stdout remains valid for Claude Code and Codex, so their context behavior does not regress.
- Kiro IDE 1.x and CLI 3.x remain the target contract when this item is shaped.
- The Claude Code and Codex fixes may need different root tokens or dispatch wrappers.

## Unresolved questions

- Whether Kiro has a documented context-injection channel, or the nudge stays unverified there after the schema migration.
- Whether context output is rendered by the projected hook wrapper per adapter or by a mode of the portable hook, and which owner carries the per-runtime protocol.
- Which root-stable form is safe on Windows, given the command-safety guardrail.
- Whether the three defects ship as one spec or as three, since the Kiro migration has the largest blast radius and the root fix the smallest.

## Readiness

- **Route:** delivery brief [`adapter-hook-context-output-delivery`](../briefs/adapter-hook-context-output-delivery.md), three slices. They answer the first three open questions as follows.
- **Verified 2026-11-05:** `.codex/hooks.json` still runs `python tools/hooks/session-start.py` and `python tools/hooks/work-loop-check.py`, both relative to the working directory; from a subdirectory that command fails with "can't open file". `tools/hooks/session-start.py` prints plain text and contains no `additionalContext`. `packs/core/.apm/kiro-ide-hooks/` still ships only the legacy `work-loop-check.kiro.hook`.
- **Unresolved questions, answered:** the nudge on Kiro stays "unverified" after the schema migration unless Kiro documents a context channel; the installer's `Next:` handoff covers it. Context output is rendered per adapter by the projected wrapper, not by a mode of the portable hook, so the hook body keeps its intent. Three specs, not one, because the Kiro migration has the widest blast radius. The Windows-safe root form is decided inside slice H1.

## Source

- Mode: repo-origin
- Locator: docs/specs/codex-hook-adaptation-handoff/hook-adapter-audit.md
- Revision: sha256-bytes-v1:3e6d9b52c6316d6fb13eacbd46737a12d5acd437b310ba1eb3d1876df959d8c1
