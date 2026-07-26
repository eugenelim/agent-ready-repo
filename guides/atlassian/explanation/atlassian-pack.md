# The Atlassian pack as a system

The Atlassian pack is one conversational layer over several focused workflows.

You ask in team language. The agent selects the smallest workflow that can answer
safely: orient first, improve unclear work when needed, and write only after the
requested change is explicit.

---

## The mental model

```
USER INTENT
"What can the team do next?"
        ↓
ORIENT
jira-team-status
Read-only
        ↓
IMPROVE
jira-story-triage
Draft first — no Jira write
        ↓
ACT
jira (update-issue)
Explicit approved writes only
        ↓
MEASURE OR SHARE
flow-metrics · ai-adoption-report · confluence-publisher
Reporting and publishing
```

Each stage produces an artifact the next stage can consume. You can stop at any
point. The earlier stages are always safe to run.

---

## Why the workflows are separate

**Orientation can remain read-only.** A backlog summary, a sprint status, and a
stand-up view don't need write access. `jira-team-status` never modifies Jira — this
is structural, not configurable.

**Story review has a dedicated quality contract.** The five-question readiness bar is
a fixed, team-independent standard. `jira-story-triage` applies it consistently and
explains *why* each item fails — which question and which gap — rather than returning
a tier label. Keeping this separate from `jira-team-status` means the team-status
view is always fast and read-only, while the quality review is thorough.

**Jira writes need a distinct approval boundary.** No workflow in this pack writes to
Jira without showing the user the exact issues and fields first. The write path is
always: draft → confirm payload → apply. Mixing read and write in one workflow makes
that boundary invisible.

**Reporting and publishing require different aggregation.** `flow-metrics` computes
metrics from Jira changelogs — it doesn't read the same issue fields as the team
status or triage skills. `ai-adoption-report` works entirely from local JSON files.
`confluence-publisher` handles Confluence's versioning and optimistic-lock conflict
model separately from any Jira operation.

**Users don't need to select the implementation skill manually.** Natural language
requests route automatically — "show me the team backlog" activates `jira-team-status`,
"make these tickets actionable" activates `jira-story-triage`. The skill name is
secondary metadata, not a prerequisite for using the pack.

---

## What each workflow owns

| Workflow | Reads | Writes | When to use |
| --- | --- | --- | --- |
| `jira-team-status` | Jira issue fields, status, blockers, team scope | Nothing (by default) | Team backlog state, stand-up, sprint review |
| `jira-story-triage` | Issue description, ACs, type, size | Description / ACs after approval | Story quality, readiness judging, draft improvements |
| `jira` | Any Jira field | Any field, status, comment, attachment | Targeted single-issue operations |
| `jira-defect-flow` | One Jira defect | Comment + transition after PR | Defect end-to-end |
| `jira-brief-intake` | Epic and children | Brief file (local only) | Epic-to-spec conversion |
| `flow-metrics` | Jira changelogs | Nothing | Delivery metrics, DORA |
| `ai-adoption-report` | Local JSON files | Report file (local only) | AI adoption comparison |
| `confluence-crawler` | Confluence page tree | Nothing | Mirror space to Markdown |
| `confluence-publisher` | Confluence page version | Confluence page | Publish report or weekly update |

---

## The read / draft / write / publish boundary

The pack makes four states explicit:

**Read-only** — `jira-team-status` and `flow-metrics`. No Jira change possible by design.

**Draft** — `jira-story-triage` before approval. The proposed improvement exists in
the conversation, not in Jira.

**Proposed write** — `jira-story-triage` after drafting, before the user confirms. The
write-confirmation panel shows the exact issues and fields. No write has occurred.

**Confirmed write** — after the user says apply. `jira: update-issue` fires for each
named issue. Nothing outside the named list changes.

The same four states apply in the Confluence path: the crawler and `ai-adoption-report`
are read-only; the publisher shows a `--dry-run` preview; and the user confirms before
publishing.

---

## Learn more

- [Tutorial: Review your team's backlog from start to finish](../tutorials/review-your-team-backlog.md) — walk the full journey once
- [Work with Jira from a conversation](../how-to/work-with-jira.md) — common tasks and quick reference
- [Atlassian skills reference](../reference/atlassian-skills.md) — exact contracts, limits, and approval behavior
- [Pack page](../../../../packs/atlassian/) — installation and capability overview
