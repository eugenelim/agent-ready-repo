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
7. **Frontmatter mapping** (`.apm/agents/<n>.md` → `.agent.md`): map `tools` via an **explicit** Claude→Copilot alias table (an unmapped name **fails the build** rather than silently widening permissions); **drop `model`** (the CLI ignores it / errored on arrays); **omit `target`** (defaults to both runtimes). Verified `Read`/`Grep`/`Glob` resolve in CLI + app 1.0.59 and the read-only restriction holds; **`WebFetch`/`WebSearch` did not surface as app tools** (Run 4) — the spec pins web-tool coverage or documents the `research`-pack degradation (see RFC-0024 Open Q4).

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
- **Tool-alias coverage:** `WebFetch`/`WebSearch` did not surface as Copilot tools in the 1.0.59 app (Run 4); the spec must map web retrieval explicitly or document that `research`'s retrieval subagents are degraded (read/search only) on Copilot. Tracked as RFC-0024 Open Q4.

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

## Errata

> Append-only corrections to this Accepted ADR. Implemented by
> [`docs/specs/copilot-skills-and-web/`](../specs/copilot-skills-and-web/spec.md)
> (contract v0.11 → v0.12, atop RFC-0026 cursor's v0.11); mirrors [RFC-0024 § Errata](../rfc/0024-copilot-subagent-projection.md#errata).

### E1 — `WebFetch`/`WebSearch` are supported on Copilot CLI + app — 2026-06-11

Decision 7 + the "Tool-alias coverage" consequence (line 55) recorded, from
RFC-0024 Run 4, that `WebFetch`/`WebSearch` "did not surface as Copilot tools"
and that the spec would document a `research` degradation. **Corrected:** the
official custom-agents reference documents a `web` tool aliasing `WebSearch`/`WebFetch`,
applicable to the CLI + app (only the cloud agent is excluded). The Run-4 finding
was confounded; pass-through is correct and unchanged, so no `research` web
degradation exists on this repo's CLI/app target — only the cloud agent lacks `web`.
Source: https://docs.github.com/en/copilot/reference/custom-agents-configuration (2026-06-11).

*Signed-off: eugenelim (Decider/Approver), 2026-06-11.*

### E2 — `skill` projects as first-class Agent Skills (`SKILL.md`), not `instruction-file` — 2026-06-11

Decision 4 gave `skill` the `instruction-file` mode (repo `.github/instructions/`,
user `~/.copilot/instructions/`), and "Alternatives considered" rejected the
agent-as-instruction collapse. Copilot has since shipped first-class Agent Skills
(`.github/skills/<name>/SKILL.md` repo, `~/.copilot/skills/<name>/SKILL.md` user),
distinct from custom instructions, so the adapter flips `skill` to the existing
`direct-directory` `SKILL.md` shape and retires copilot's `instruction-file`
usage + the `copilot-instruction` frontmatter-default. Same flip-on-upstream-support
move this ADR already made for codex agents/hooks. Source:
https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills (2026-06-11).

*Signed-off: eugenelim (Decider/Approver), 2026-06-11.*
