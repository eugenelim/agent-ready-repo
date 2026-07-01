# Adapter scope of the research retrieval-subagent web-tools nudge

**Question.** The research pack's two retrieval subagents
(`packs/research/.apm/agents/evidence-retriever.md`, `source-extractor.md`)
declare `tools: Read, Grep, Glob, WebFetch, WebSearch`. After a fresh install, on
which adapters can they actually do live web retrieval, and on which must the
adopter first grant web-tool permission? This scopes the install-nudge AC in
[`../spec.md`](../spec.md) (Web-tools install nudge).

**Finding (2026-06-30 adapter investigation).** The gap is **Claude Code-specific.**

| Adapter | Supports the subagent primitive? | Web-tool grant needed at install? | Evidence |
|---|---|---|---|
| **Claude Code** | yes (`.claude/agents/<name>.md`) | **YES** | non-interactive subagents cannot surface an approval prompt, so a permission-gated tool absent from `permissions.allow` is denied; `packages/agentbundle/agentbundle/build/adapters/claude_code.py` (direct-file agent projection) |
| Copilot | yes (`.github/agents/<name>.agent.md`) | no | `WebFetch`/`WebSearch` pass through and Copilot resolves both to its built-in `web` tool on CLI + app; `packages/agentbundle/agentbundle/build/projections/copilot_agent_md.py` docstring; `docs/specs/copilot-skills-and-web/spec.md` |
| Cursor | yes (`.cursor/agents/<name>.md`) | no | subagents inherit all parent tools; no per-agent allowlist; `packages/agentbundle/agentbundle/build/adapters/cursor.py`; ADR-0015 |
| Gemini | yes (`.gemini/agents/<name>.md`) | no | tools name-mapped at build time, not runtime-gated; `packages/agentbundle/agentbundle/build/adapters/gemini.py`; ADR-0016 |
| Codex | yes (`.codex/agents/<name>.toml`) | no | tools preserved in the agent TOML; no runtime allowlist; `packages/agentbundle/agentbundle/build/adapters/codex.py` |
| Kiro (IDE + CLI) | yes (`.kiro/agents/<name>.{md,json}`) | no | tools normalized into the agent JSON/frontmatter at build time; `packages/agentbundle/agentbundle/build/adapters/kiro.py`, `kiro_ide.py` |

**Bottom line.** Only Claude Code gates the subagents' web tools behind an
allow-list a non-interactive sub-invocation cannot satisfy. On every other
adapter the tools are passed through to the parent session's model or baked in at
projection time. So the README install-nudge is **scoped to Claude Code**.

**Corroborating project memory** (session context, not a repo artifact): the
subagent web-tools finding (an allow-list gap, not a scope wall — user-scope
`~/.claude/settings.local.json` with both tools works, empirically confirmed) and
the standing research-pack TODO to surface the grant at install/adapt time as a
guidance note, **not** as bundle-managed `permissions.allow` machinery.

**To re-confirm at implementation time.** The adapter projection files above are
the ground truth; re-grep them if the adapter set or projection model has changed
before the implementing PR lands.
