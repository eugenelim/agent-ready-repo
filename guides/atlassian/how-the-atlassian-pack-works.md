---
title: "How the Atlassian pack works"
summary: "The mental model behind the Atlassian pack — how focused workflows compose into a safe, readable team backlog experience without you selecting skills manually."
pack: atlassian
kind: explanation
slug: guides/atlassian/explanation/atlassian-pack
journey: atlassian
order: 4
status: stable
---

The Atlassian pack is one conversational layer over several focused workflows.

You ask in team language. The agent selects the smallest workflow that can answer safely: orient first, improve unclear work when needed, and write only after the requested change is explicit.

## The mental model

```
Ask
  ↓
Orient      →  jira-team-status     Read-only
  ↓
Improve     →  jira-story-triage    Draft first
  ↓
Act         →  jira                 Explicit approved writes
  ↓
Measure     →  flow-metrics         Read-only
or share    →  confluence-publisher Publish only after approval
```

You rarely name a skill. You say "show me the team backlog" and the pack selects `jira-team-status`. You say "improve the weak stories" and it selects `jira-story-triage`. You say "apply the approved changes" and it selects `jira`. Each step is the minimum workflow that can answer safely.

## The four stages

### Orient — see what is available

`jira-team-status` runs first. Always read-only.

It resolves your team scope (board, project set, Team field, saved filter, or JQL), fetches all open issues across the sprint and backlog, groups them by readiness, and discloses scope and completeness before showing any data.

**What you get:**

- Coverage disclosure: how many issues were found, whether the result is complete, filtered, or truncated
- Five groups: Ready to pull · Needs story work · Blocked · In progress · Other open work
- Recommended next candidates
- Confirmation that Jira was not changed

"Ready to pull" is not `statusCategory = To Do`. It means the issue is in scope, has no known unresolved blocker, and has enough definition for the team to begin. Work that looks ready in Jira may still appear in "Needs story work" if acceptance criteria are missing or the scope is unclear.

### Improve — make the backlog actionable

`jira-story-triage` runs when you ask to improve weak stories. Still read-only until you say otherwise.

It applies a five-question readiness bar to each item, explains which question failed and why the gap prevents action, proposes a rewrite of the description and acceptance criteria, surfaces any question only the product owner can answer, and tells you what readiness the issue would reach after the draft is accepted.

No Jira data changes at this stage. Drafts are local until you explicitly approve them.

### Act — apply approved changes

`jira` runs when you say "apply the approved changes" or "update these issues." This is the first step that writes to Jira.

Before any write, the agent shows you the exact payload: issue key, field, current value, proposed value, and a list of protected fields (status, assignee, sprint, priority, labels) that will not be touched. You confirm or cancel. If a write fails for one issue, the others proceed and the failed draft is preserved with a recovery action.

### Measure or share — communicate the result

`flow-metrics` computes DORA and Flow Framework metrics (cycle time, throughput, WIP) from Jira changelogs. Read-only — never writes to Jira.

`confluence-publisher` pushes a report or summary to a Confluence page. Always shows the exact page, space, and content before writing. Publishing requires explicit confirmation — it is never automatic.

## Why the workflows are separate

**Orientation can remain read-only.** The team status snapshot is the most common request. Keeping it read-only means it can run without any confirmation, at any time, without risk. Merging it with the write workflow would make every team status request feel like a write operation — even when nothing changes.

**Story review has a dedicated quality contract.** `jira-story-triage` applies a specific readiness model, produces structured per-item output, and surfaces human questions that the product owner must answer. That contract is different from a general Jira update — it deserves its own skill with its own rules.

**Jira writes require a distinct approval boundary.** Every write must show exact fields and values before executing. Having a dedicated write skill (`jira`) keeps that boundary explicit and testable. No other skill in the pack writes to Jira autonomously.

**Reporting and publishing need different aggregation and output contracts.** A stand-up summary and a Confluence page have different audiences, different formats, and different safety properties. Separating them means each can be tested and approved independently.

**Focused skills carry less irrelevant context.** A skill that does one thing well receives a shorter, cleaner prompt. Less context means fewer misinterpretations and more predictable outputs.

**Natural-language routing means you do not need to select skills manually.** The pack resolves "show me what the team can work on" to `jira-team-status` and "improve these stories" to `jira-story-triage` without you knowing those names. Skill names appear as secondary metadata, below the user-facing action.

## What changes and what does not

**Changes:** After your request, you see grouped, annotated backlog data — not raw Jira issue lists. Weak stories have a draft improvement attached. Approved changes appear in Jira immediately.

**Does not change:** Jira data during orientation or story review. Protected fields (status, assignee, sprint, priority, labels) during any write step. Confluence pages until you explicitly approve a publish.

## The canonical sequence

The tutorial walks through this sequence with the Team Atlas scenario — 184 issues across APP and API, 17 ready to pull, 26 needing story work, and three targeted improvements applied:

1. "Show me the whole Atlas team backlog across APP and API. Do not change Jira."
2. "Take the items that need story work. Draft improvements only."
3. "Update APP-206 and API-104 with the approved drafts."
4. "Give me a stand-up summary. Do not publish until I approve it."

→ [Full start-to-finish tutorial](/agent-ready-repo/docs/guides/atlassian/tutorials/review-your-team-backlog/)

## See also

| Resource | When to use it |
|---|---|
| [Work with Jira — how-to](/agent-ready-repo/docs/guides/atlassian/how-to/work-with-jira/) | Common tasks with copyable requests |
| [Atlassian skills reference](/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/) | Exact read, write, coverage, and approval contracts |
| [Atlassian journey](/journeys/atlassian/) | Four-stage visual storyboard |
| [Atlassian pack](/packs/atlassian/) | Install, credentials, pack overview |
