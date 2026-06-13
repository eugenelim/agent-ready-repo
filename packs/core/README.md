# core

The core pack ships the agent-ready-repo skills (work-loop, new-spec,
new-rfc, …), the four specialist subagents (adversarial-reviewer,
security-reviewer, quality-engineer, implementer), the canonical
session-start hook, and the `/adapt-to-project` command.

## Install routes and adaptation

`core` ships through three install routes — `agentbundle install`
(CLI), `claude plugin install` (Claude-plugins), and `apm install`
(APM). Whichever route an adopter uses, the install→adapt chain ends
the same way: a `[[packs-installed]]` entry lands in the
scope-correct `.adapt-install-marker.toml`, the next session of a
HookIntegrator-covered target tool surfaces a *"N pack(s) pending
adaptation; run `/adapt-to-project`"* nudge, and the skill adapts the
brownfield repo (or user-home for user-scope packs) to the project.

APM's HookIntegrator projects the `SessionStart` install-marker hook
to four of seven supported target tools: `Claude Code`, `Copilot`,
`Cursor`, and `Gemini`. The remaining three — `Codex`, `OpenCode`,
and `Windsurf` — silently lack the hook surface in upstream APM
today; their adopters run the documented manual fallback once after
install:

```
agentbundle adapt --scope <project|user>
```

This is the same gesture CLI-route adopters use, and the same gesture
adopters at HookIntegrator-covered targets can run if they prefer to
opt out of hooks for safety. See
[`docs/specs/apm-install-route-parity/spec.md`](../../docs/specs/apm-install-route-parity/spec.md)
for the contract surface and
[`docs/rfc/0010-apm-install-route-parity.md`](../../docs/rfc/0010-apm-install-route-parity.md)
for the design rationale.

## Usage

`core` is the loop itself. Ask your agent, for example:

- "Start a new spec for a rate-limiting feature." (`new-spec`)
- "Implement this spec with the work-loop." (`work-loop`)
- "Fix this bug: the importer drops the last row." (`bug-fix`)
- "Adapt this repo to the installed packs." (`/adapt-to-project`)
