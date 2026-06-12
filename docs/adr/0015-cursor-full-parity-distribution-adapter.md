# ADR-0015: Cursor is a full-parity distribution adapter

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-11
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0026](../rfc/0026-cursor-full-parity-adapter.md) (the decision), [ADR-0013](0013-copilot-full-parity-user-scope-adapter.md) (the full-parity user-scope template this follows), [ADR-0012](0012-kiro-adapter-split.md) (the `.md`-agent + frontmatter-mapping shape Cursor's agent projection reuses), [ADR-0004](0004-repo-scope-per-adapter-projection.md) (the per-adapter projection model this extends), [spec `apm-install-route-parity`](../specs/apm-install-route-parity/spec.md) (already treats Cursor as an install target via `${CURSOR_PLUGIN_ROOT}`)

## Context

The catalogue ships four reference distribution adapters (Claude Code, Kiro, Copilot, Codex). Each takes one canonical set of pack primitives (`.apm/skills`, `.apm/agents`, `.apm/hooks`, `.apm/hook-wiring`, `.apm/commands`) and projects it into a tool's native discovery layout. Cursor is the most widely used agentic IDE we do **not** yet project into.

Two facts already in the tree make the gap concrete and the fix overdue:

- Cursor is already named as an install **target** in the `apm-install-route-parity` spec (`${CURSOR_PLUGIN_ROOT}`, `~/.cursor/extensions/…`) and as an `AGENTS.md` reader in the root `AGENTS.md`. The install/route half anticipates Cursor; the **projection** half is missing.
- As of Cursor v2.6 (Feb 2026) Cursor has first-class native support for skills (`.cursor/skills/`), subagents (`.cursor/agents/`), hooks (`.cursor/hooks.json` + `.cursor/hooks/`), and commands (`.cursor/commands/`) — primitives we project to no other tool's full set today, and that the existing four adapters between them already cover.

Without a Cursor adapter, a Cursor adopter gets nothing under `.cursor/`: they rely entirely on Cursor incidentally reading our root `AGENTS.md` and any co-installed `.claude/` tree. Cursor *does* cross-read `.claude/skills/`, `.claude/agents/`, and `.codex/agents/` for compatibility — but that only helps adopters who *also* installed the Claude Code projection, gives Cursor nothing under its own precedence-winning `.cursor/` tree, and covers neither hooks nor commands.

Constraints that shaped the projection mappings:

- **Cursor subagents have no per-agent tool allowlist.** The subagent frontmatter vocabulary is `name`, `description`, `model`, `readonly`, `is_background` — there is no `tools:` field; subagents inherit all parent tools. Our agents carry a `tools:` allowlist that has no faithful target.
- **Cursor's CLI and IDE share one `.cursor/` discovery layout** (unlike Kiro, which forced the RFC-0022 CLI/IDE split). One adapter covers both.
- **Cursor's `.cursor/` prefix is identical at repo and user scope** (`.cursor/` repo, `~/.cursor/` user) — the claude-code/codex shape, not Copilot's `.github/`→`~/.copilot/` divergence.
- **No new projection mode is wanted.** The four existing adapters between them exercise `direct-directory`, `direct-file`, `merge-json`, and `dropped`; Cursor's five primitives all map onto those.

## Decision

**We treat `cursor` as a full-parity distribution adapter: it projects every catalogue primitive to Cursor's native `.cursor/*` discovery paths at both repo and user scope, reusing only existing projection modes, with documented degradation for the one primitive (agent tools) Cursor cannot represent.**

Concretely (contract **v0.10 → v0.11**, a new `[adapter.cursor]` block mirrored byte-for-byte to `docs/contracts/adapter.toml`, **no projection-mode-enum change**):

1. **Full native adapter.** Project all five primitives to `.cursor/*` (repo) and `~/.cursor/*` (user) — `skill`→`.cursor/skills/<name>/` (`direct-directory`), `agent`→`.cursor/agents/<name>.md` (`direct-file` + a `cursor-agent-frontmatter-v0.11` mapping, the Kiro-IDE `.md` shape), `hook-body`→`.cursor/hooks/<name>.{sh,py}` (`direct-file`), `hook-wiring`→`.cursor/hooks.json` (`merge-json`, managed-key `hooks`), `command`→`.cursor/commands/<name>.md` (`direct-file`). The Kiro-only `kiro-ide-hook` primitive is `dropped`. Chosen over a do-nothing or thin adapter because `.cursor/` precedence means a partial `.cursor/` tree is *worse* than none, and a Cursor adopter should never be forced to also install the Claude projection.

2. **Drop the agent `tools:` allowlist; derive a `readonly` flag for non-mutating agents.** Cursor has no per-agent tool allowlist, so `tools:` is dropped and the projection emits `readonly: true` for agents whose declared tool set contains no mutating tool, letting reviewer/retrieval subagents stay least-privilege while mutating agents inherit all tools. This is the same documented-degradation shape ADR-0013 accepted for Copilot. The exact predicate is pinned in the implementing spec (`docs/specs/cursor-full-parity/`).

3. **Project `command` first-class** to `.cursor/commands/<name>.md` (repo) + `~/.cursor/commands/<name>.md` (user). Cursor is the second adapter after Claude Code to honour commands (Copilot and Kiro drop them, pending upstream support). The catalogue ships exactly one command primitive today (`packs/core/.apm/commands/conventions-check.md`), so this decision has a live consumer.

4. **Map our hook events to Cursor's, dropping unmapped events with a build-time log.** A contract-declared mapping table translates our hook-wiring event vocabulary to Cursor's `sessionStart` / `beforeSubmitPrompt` / `preToolUse` / `postToolUse` / `stop`. Any source event with no Cursor target is dropped with a build-time log line (no silent truncation — the catalogue's no-silent-caps rule). This is fail-**open**-with-log, deliberately unlike Copilot's fail-closed `copilot-hooks-json` map; the implementing spec settles the exact source-event keying.

5. **Distribution-only.** `cursor` is **not** added to `SELF_HOST_ADAPTERS` — this repo does not self-host onto Cursor, matching Copilot and Kiro. The adapter ships for adopters; the repo continues to self-host onto Claude Code + Codex only.

## Consequences

**Positive:**
- A Cursor adopter gets a complete, self-contained `.cursor/` tree (skills, agents, hooks, commands) at both scopes instead of silent degradation to "whatever Cursor reads from root `AGENTS.md`."
- Cursor joins claude-code/kiro/copilot/codex as a first-class adapter — the one-adapter-per-tool catalogue model stays symmetric.
- Reusing only existing projection modes keeps the contract change to a `[adapter.cursor]` block + a version bump, with no projection-mode-enum churn and no new mode for the four existing adapters to ignore.
- Commands reach a second tool, validating that the `command` primitive is not Claude-Code-only.

**Negative:**
- Net-new adapter code + tests to maintain, and a contract version bump that ripples to every adapter's version-compare test (a known trap — the implementing spec runs the full `agentbundle` pytest, not just `make build-check`).
- The agent `tools:` allowlist is lost on projection: a mis-derived `readonly` flag could make a writing agent read-only (breaks it) or leave a reviewer inherit-all (over-privileged). Mitigated by a conservative predicate (read-only only when a tool set is declared and contains zero mutating tools), pinned and tested in the spec.
- Some projected redundancy for adopters who *also* run Claude Code — Cursor reads both `.cursor/` and `.claude/`; `.cursor/` simply wins. Accepted four times before; the standard cost of an adapter.

**Neutral / to revisit:**
- `.cursor/rules/*.mdc` and `.cursor/mcp.json` are deliberately **not** projection targets — the always-apply-context need is met by Cursor reading root `AGENTS.md`, and the catalogue has no MCP primitive for any adapter. Adding either is a separate cross-adapter RFC.
- The hook-event map is version-sensitive (Cursor's event vocabulary may shift); a layout or event change is a contract bump, not a code rewrite — the same exposure as every other adapter.
- The agent `model` field is passed through verbatim rather than alias-translated (Cursor resolves a known id or falls back to inherit); the spec records the rationale and a follow-on to add a Cursor model-id map if a shipped model proves unresolvable.

## Alternatives considered

- **Do nothing (rely on Cursor reading root `AGENTS.md` + a co-installed `.claude/` tree).** Rejected: produces no `.cursor/` artifacts, no hooks, no commands, and a hard dependency on the adopter *also* installing Claude Code. The cost of delay grows as Cursor adoption grows.
- **Thin adapter (project only the divergent primitives — skills, hooks, commands — and lean on `.claude/agents/` + `AGENTS.md` for the rest).** Rejected: bets that `.claude/` is always co-installed, and produces a `.cursor/` tree that is incomplete by precedence — and because `.cursor/` wins over `.claude/`, a half-populated `.cursor/` is *actively worse* than none.
- **A bespoke projection mode (e.g. a `cursor-agent-md` / `cursor-hooks-json` pair, mirroring Copilot's two new modes).** Rejected: Cursor's agent shape is the Kiro-IDE `.md` + frontmatter-mapping shape and its hook-wiring is a single aggregated JSON — both expressible with the existing `direct-file` / `merge-json` modes plus a minimal pack-specific helper (the readonly derivation and event remap). A new mode would add enum surface every other adapter must carry for no gain.
- **Self-host this repo onto Cursor (add `cursor` to `SELF_HOST_ADAPTERS`).** Rejected: matches the Copilot/Kiro precedent of distribution-only; self-hosting onto every adapter multiplies the projected working tree without exercising anything the Claude Code + Codex self-host pair doesn't already cover.
- **Project agents via Cursor's `.cursor/rules/*.mdc` instead of `.cursor/agents/`.** Rejected: collapses an isolated-context subagent into an always-on rule, losing the delegation that defines a subagent — wrong altitude, the same reason ADR-0013 rejected the instruction-file route for Copilot agents.

## References

- [RFC-0026](../rfc/0026-cursor-full-parity-adapter.md) — the full analysis, the five decisions, the per-primitive projection table, the agent frontmatter mapping, the hook-event map, and the two open questions deferred to the implementing spike.
- [ADR-0013](0013-copilot-full-parity-user-scope-adapter.md) / [RFC-0024](../rfc/0024-copilot-subagent-projection.md) — the full-parity, user-scope, documented-tool-degradation template this adapter follows.
- [ADR-0012](0012-kiro-adapter-split.md) / [RFC-0022](../rfc/0022-kiro-adapter-split.md) — the `.md`-agent + frontmatter-mapping shape Cursor's agent projection reuses.
- [`docs/specs/cursor-full-parity/`](../specs/cursor-full-parity/spec.md) — the implementing spec: adapter module, `[adapter.cursor]` block, `cursor-agent-frontmatter-v0.11` + hook-event map, readonly predicate, contract bump, tests, CI wiring.
</content>
</invoke>
