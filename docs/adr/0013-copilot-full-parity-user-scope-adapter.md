# ADR-0013: Copilot is a full-parity, user-scope-capable adapter

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-04
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0024](../rfc/0024-copilot-subagent-projection.md) (the decision; supersedes-in-part RFC-0012), [ADR-0004](0004-repo-scope-per-adapter-projection.md) (per-adapter projection model this extends), [RFC-0009](../rfc/0009-codex-native-skills.md) + [`dropped-primitives-coverage` spec](../specs/dropped-primitives-coverage/spec.md) (the codex `dropped`→first-class precedent), [ADR-0002](0002-install-scope-per-pack-default-and-allowance.md) (scope dimension)

## Context

When the `copilot` adapter was last specified (RFC-0012 / ADR-0004), GitHub Copilot exposed only a repo-level skills surface (`.github/instructions/`). The contract therefore (a) **dropped** the `agent`, `hook-wiring`, and `command` primitives for Copilot, and (b) gave Copilot a repo-only `[adapter.copilot.scope]` table with the note *"no user-scope analogue exists in the Copilot ecosystem."* Both were accurate then.

They are no longer. Copilot's **app** (a desktop application built on the Copilot CLI) and the **CLI** now read native, filesystem-based config that mirrors the shape we already project for claude-code (`~/.claude/`) and codex (`~/.agents/skills/`):

- custom **agents** — `.github/agents/<n>.agent.md` (repo) + `~/.copilot/agents/<n>.agent.md` (user);
- **hooks** — `.github/hooks/<n>.json` (repo) + `~/.copilot/hooks/<n>.json` (user), `{"version":1,"hooks":{<event>:[…]}}` per file;
- a stable `$HOME` config tree (`~/.copilot/`, `COPILOT_HOME`), including `~/.copilot/instructions/` for user-scope instructions.

The constraint that remains: custom **slash commands / prompt files are not yet loaded by the Copilot CLI** (copilot-cli#618 / #1113). Two packs ship subagents and are the consumers of this gap: `core` (3 reviewers + the implementer executor; repo-only) and `research` (2 retrieval subagents; user-default). This is the same situation ADR-0004's sibling codex work already resolved for codex (RFC-0009 / `dropped-primitives-coverage`): flip a `dropped` primitive to first-class once the upstream tool gains native support.

## Decision

**We treat `copilot` as a full-parity, user-scope-capable adapter: it projects every primitive Copilot supports (skill, agent, hook-wiring, hook-body) at both repo and user scope, against the GitHub Copilot app + CLI's `.github/` and `~/.copilot/` layout.**

Concretely (contract **v0.9 → v0.10**):

1. **`agent`** → new `copilot-agent-md` mode: `.github/agents/<n>.agent.md` (repo) + `~/.copilot/agents/<n>.agent.md` (user). *(was `dropped`)*
2. **`hook-wiring`** → new `copilot-hooks-json` mode: a self-contained `<n>.json` per wiring file at `.github/hooks/` (repo) + `~/.copilot/hooks/` (user). A **new per-file mode**, deliberately *not* the `merge-json` mode codex used — Copilot reads every `*.json` in the hooks dir, which a single mergeable file can't express. *(was `dropped`)*
3. **`copilot` is user-scope-capable** — add `[adapter.copilot.scope].user`; the install resolver no longer refuses copilot at user scope.
4. **`skill`** gains a user-scope home `~/.copilot/instructions/<n>.instructions.md`, mirroring the existing repo `.github/instructions/` projection (same `instruction-file` mode).
5. **`hook-body`** moves from the legacy `tools/hooks/` to `.github/hooks/` + `~/.copilot/hooks/`, alongside the `<n>.json` wiring that references it.
6. **`command` stays `dropped`** — the CLI does not load custom slash commands yet (copilot-cli#618/#1113); the contract-driven warning rail keeps the drop visible. A follow-on flips it when the CLI ships the feature.
7. **Frontmatter mapping** (`.apm/agents/<n>.md` → `.agent.md`): pass `tools` through (Claude tool names are Copilot's case-insensitive compatible aliases — `Read`→`read`, `Grep`/`Glob`→`search`, `WebFetch`/`WebSearch`→`web`, `Edit`/`Write`→`edit`, `Bash`→`execute`), with an unmapped name **failing the build** rather than silently widening permissions; **drop `model`** (the CLI ignores it / errored on arrays); **omit `target`** (defaults to both runtimes).

The guaranteed surface is the **Copilot app + CLI** (`~/.copilot/` + `.github/`). The cloud coding agent and the VS Code workspace also read the repo `.github/` files — compatible, but not the guaranteed target; the VS Code extension's user-profile location is documented inconsistently and is deliberately not targeted.

This decision was gated on a live smoke and verified: RFC-0024 § Acceptance verification, Run 2 (Copilot CLI + app 1.0.59), passed T1–T8 (independently re-confirmed for the CLI in Run 3).

## Consequences

**Positive:**
- Subagents and hooks from `core`/`research` now reach the Copilot ecosystem at both scopes instead of vanishing; `research` is no longer excluded from Copilot.
- Copilot joins claude-code/codex/kiro as a first-class user-scope adapter — the adapter model is symmetric again.
- The change mirrors the established codex `dropped`→first-class pattern, so the warning rail, atomic contract+pack bump, and resolver paths are reused, not invented.

**Negative:**
- Two new projection modes (`copilot-agent-md`, `copilot-hooks-json`) and a hook event-name map to maintain.
- `.github/agents/` and `.github/hooks/` widen the adopter-collision surface vs. `.claude/` (these namespaces overlap adopter-authored content); Tier-1/2/3 + `.upstream.*` companions absorb it but `.upstream.*` files will appear more often.
- `model` is dropped on projection, so Copilot uses its default model rather than the agent's declared one — a fidelity loss accepted for cross-surface robustness.
- The `tools/hooks/` retirement is a behaviour change for any future copilot hook-body consumer (none ship today, so safe now).

**Neutral / to revisit:**
- `command` remains dropped until copilot-cli#618/#1113 land; a follow-on RFC flips it.
- Copilot's full hook event vocabulary fires today (verified), but the live set is CLI-version-sensitive (preview); the implementing spec re-checks against the then-current CLI.

## Alternatives considered

- **Do nothing (keep `dropped` + repo-only).** Rejected: subagents/hooks stay invisible on the widest agent ecosystem and `research` stays excluded, while Copilot demonstrably supports both — the asymmetry with codex is itself a defect.
- **Project agents via the existing `instruction-file` mode** (`.github/instructions/`) instead of a dedicated agent surface. Rejected: collapses an isolated-context subagent into an always-on instruction, losing the delegation that defines a subagent — wrong altitude.
- **Reuse `merge-json` for hook-wiring** (as codex does). Rejected: Copilot reads many independent `*.json` files in its hooks dir, not one mergeable file; the single-target merge model can't express it.
- **Restrict Copilot to repo scope only** (the status quo, hacking pack scopes around it). Rejected: the repo-only limit was self-imposed and is now false — Copilot's app + CLI have a real `~/.copilot/` user home, verified.
- **Target the VS Code extension's user-profile location.** Rejected: documented inconsistently and partly under `%APPDATA%\Code\User\…`/profile-specific paths — not a stable cross-platform projection target.

## References

- [RFC-0024](../rfc/0024-copilot-subagent-projection.md) — full analysis, options, and the T1–T8 acceptance verification (Runs 1–3).
- [ADR-0004](0004-repo-scope-per-adapter-projection.md), [RFC-0012](../rfc/0012-repo-scope-per-adapter-projection.md) — the per-adapter projection model + the copilot repo-only scope decision this extends/supersedes-in-part.
- [`dropped-primitives-coverage` spec](../specs/dropped-primitives-coverage/spec.md) — the codex `dropped`→first-class precedent and the contract-driven warning rail.
