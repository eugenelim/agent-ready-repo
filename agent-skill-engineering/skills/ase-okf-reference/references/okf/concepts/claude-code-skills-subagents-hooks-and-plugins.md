---
id: claude-code-skills-subagents-hooks-and-plugins
title: Claude Code skills, subagents, hooks, and plugins
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Claude Code skills, subagents, hooks, and plugins

## Scope and routing signals

Use when composing a skill against Claude Code specifically, after the portable
floors have decided the shape. This profile states current behavior for one
runtime and one surface; it does not generalize, and a claim here says nothing
about any other runtime.

## Decisions and minimum evidence

Each capability the profile covers carries its own lifecycle state. A claim
sourced from first-party documentation and confirmed by a bounded probe is
`verified`. A claim sourced but not independently probed is `experimental` and
is not a support claim. A claim whose verification window has elapsed is
`stale` and returns provenance only. A capability that is absent, or whose
sources conflict so that safe verification cannot be performed, is
`unavailable` and is recorded as a delta rather than a gap.

Three capabilities are currently probed: skill body loading, subagent context
isolation, and worktree isolation. Four are sourced and unprobed: nesting
limits, component-scoped hooks, managed hook policy, and package-supplied agent
precedence. Treat the second group as reported behavior, not as support.

## Construction method

Delegate to a subagent when the work is bounded and its intermediate reads
should not reach the main context, because a non-fork subagent starts from a
fresh context window rather than inheriting the conversation. Keep long
reference material in a skill body rather than in always-loaded context, because
the body enters context only on invocation. Use a separate worktree when two
sessions would otherwise edit one checkout.

## Evidence and evaluation

Each probed claim records the gesture performed and the outcome observed, so a
reader can judge whether the gesture tests the claim rather than the harness.
An unprobed claim records its source and retrieval date and nothing more.

## Failure modes

Reading an unprobed row as support overstates what was checked. Assuming a
subagent can see the parent conversation produces briefs that omit what the
delegate actually needs. Assuming package-supplied components always win over
local ones inverts the precedence this runtime documents.

## Security and authority

Delegation narrows rather than widens authority: a subagent receives a
restricted tool set, and restrictions that do not survive the boundary must be
enforced in the parent. Hooks are executable code under runtime and
organization trust controls, and organization-managed policy can define hooks
independently of any project, so a design depending on a local hook must state
what happens when policy narrows it.

## Related topics

For the portable questions this profile answers for one runtime, consult
`skills-and-subagents-common-floor`, `hooks-common-floor`, and
`plugin-package-common-floor`.

## Provenance and lifecycle

Runtime profile for the agent-skill-engineering pack. Maintain as governed OKF
source; generated router copies are not authoring surfaces. Capability-claim
freshness is independent of the portable floors, and every operative claim
carries its own state.

**delegation and skill-loading contract:**
Delegated work runs in a fresh context window that does not inherit the parent conversation, and a skill's body enters context only when the skill is invoked.
Last verified: 2026-08-31.
Revalidate when a release changes subagent context construction or skill body loading.
Ecosystem: Claude Code.
Version range: Claude Code >= 2.1.251, upper bound open.
Claude Code subagents reference — https://code.claude.com/docs/en/sub-agents
Retrieved at: 2026-08-31. Version state: 2.1.251.
Claude Code skills reference — https://code.claude.com/docs/en/skills
Retrieved at: 2026-08-31. Version state: none exposed.
