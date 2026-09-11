# Defect: sub-agent fallbacks are keyed on absence, not on capability

Found 2026-09-10 while checking what ADR-0107's newly supported surface
actually receives. Recorded here because this spec owns what the
Claude-plugin route carries and at what scope.

## The condition

The `claude-plugins` route declares `agent = { status = "native", mode =
"direct-file", target-path = "agents/" }`, and the Claude Code adapter
projects `agent → .claude/agents/<name>.md`. So sub-agents ship in the plugin
and land on disk for a user-scope install.

Anthropic documents that on the Claude apps' chat surface, "hooks and
sub-agents run only in Cowork, so they appear grayed out in chat". The agent
file is therefore **present, listed, and unrunnable** on that surface.

## Why the existing fallbacks do not fire

Three packs ship sub-agents, and all three have a documented degradation
stance — but each is keyed on the sub-agent being **absent**:

| Pack | Agents | Stated fallback | Keyed on |
| --- | --- | --- | --- |
| `product-engineering` | 3 | reviewers "degrade only in depth … never to nothing" | pack/depth absence |
| `desk-research` | 2 | "on hosts without subagents the skills run inline" | host lacking subagents |
| `experience-design` | 1 | absence is "a named skip, not a silent pass" | reviewer not installed |

On the chat surface nothing is absent. The pack is installed, the agent file
exists, and the capability is missing — a state none of these conditions
describe. `desk-research`'s wording ("hosts without subagents") is the closest
to correct and is still keyed on the host lacking the primitive rather than on
the surface within a host lacking it.

## The consequence, stated at its sharpest

`experience-reviewer-work-loop-gate` is a **Shipped** spec guaranteeing that a
missing reviewer is "a named skip, not a silent pass". On the chat surface the
reviewer is not missing, so the guarantee's trigger never fires, and the user
gets the silent pass the contract exists to prevent.

For `desk-research`, standard and deep modes lose parallel retrieval without
saying so. The method still produces an artifact; it is the thinner one, and
nothing marks it.

## Contrast that shows this is a route choice, not a platform limit

The Agent Plugins 1.0.0 standard supports exactly two component types — Agent
Skills and MCP servers — and no agents. The `agent-plugin` route therefore
declares `agent = dropped` and **emits no artifact at all** for packs carrying
one, naming `product-engineering`, `frontend-engineering`, `architect` and
`release-engineering` among the exclusions.

So one route refuses a pack it cannot fully carry, and the other ships it into
a surface that cannot execute part of it. The refusing behaviour is the safer
default; this defect is about the difference.

## What a fix is not

Not "add a warning to the guides". Documentation can disclose the difference —
and the `claude-apps-route-docs` spec's capability reference does — but the
contract being violated is the packs', not the documentation's. A reader who
never opens the reference still gets a silent pass.

## Status

Open. No owner assigned. Not scheduled. Raised separately from
`claude-apps-route-docs`, which documents the surface difference but cannot
repair a degradation contract it does not own.
