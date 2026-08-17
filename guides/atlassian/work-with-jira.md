---
title: "Work with Jira from a conversation"
summary: "Common Jira tasks — from reviewing the whole team backlog to applying approved story updates — without writing JQL or selecting skills manually."
pack: atlassian
kind: how-to
slug: guides/atlassian/how-to/work-with-jira
journey: atlassian
order: 2
status: stable
---

Ask in your own words. The agent selects the right workflow, starts read-only, and only writes to Jira after you approve the exact change.

**Reviewing and drafting do not change Jira. Only an explicitly approved update request writes to Jira.**

Jump to what you need:

- [Start repository work from Jira or Jira Align](#start-repository-work-from-jira-or-jira-align)
- [Review the whole team backlog](#review-the-whole-team-backlog)
- [Find ready work](#find-ready-work)
- [Find blockers and stale work](#find-blockers-and-stale-work)
- [Find unassigned work](#find-unassigned-work)
- [Improve stories that are not actionable](#improve-stories-that-are-not-actionable)
- [Update approved Jira issues](#update-approved-jira-issues)
- [Prepare a team or sprint summary](#prepare-a-team-or-sprint-summary)

---

## Start repository work from Jira or Jira Align

Use intake when tracked content should become canonical repository work:

:::tip[YOU SAY]
Intake Jira issue PROJ-123 as repository work. Start read-only.
:::

For Jira Align, name the Feature or selection instead. The adapter reads through
the sibling Jira or Jira Align acquisition skill, minimizes the result into
`normalized-intake.v1`, and delegates to `work-intake`.

**Read/write status:** tracker intake is read-only. It does not create, edit,
transition, comment on, or otherwise write tracker work. It also does not create
a repository artifact directly; `work-intake` owns that step after validation.

Jira types, hierarchy, boards, sprints, Program Increments, and query results are
profile hints. Content decides the route:

- one independently shippable behavior can become a spec;
- one coherent multi-spec outcome can become a Draft brief;
- unrelated collections become separate units, a view-only result, or one
  clarifying question;
- a regression reaches `bug-fix` only with durable expected-behavior evidence.

The default profiles bound pages, items, bytes, timeouts, retries, and backoff.
Configured destinations must be profile-allowed HTTPS hosts and pass address
validation before credentials are resolved. Partial results are explicit.

**Likely follow-up:** review the proposed route and answer any ambiguity or
confidentiality question, then continue with the named processor.

→ [Choose a tracker integration](/agent-ready-repo/docs/guides/_shared/how-to/choose-a-tracker-integration/)\
→ [Tracker vocabulary](/agent-ready-repo/docs/guides/_shared/reference/tracker-vocabulary/)

---

## Review the whole team backlog

The most common starting point. Shows you everything the team has across the sprint and open backlog, grouped by readiness, with scope and completeness disclosed before any data.

:::tip[YOU SAY]
Show me the whole Atlas team backlog across APP and API.

Include the current sprint, open backlog, unassigned work, and blocked issues.

Group everything into: ready to pull · needs story work · blocked · in progress.

Do not change Jira.
:::

**Scope assumptions:** the agent resolves your team from a Jira board, the Team field, a saved filter, or a project set. If the scope is ambiguous, it asks one compact question before returning results.

**Read/write status:** Read-only. Nothing changes in Jira.

**Possible compact clarification:**

> I found two possible Atlas scopes: (1) the Atlas Jira board, (2) issues whose Team field is Atlas. Which should I use?

**What is inspected:** all open issues in the specified scope — current sprint + open backlog — across all listed projects.

**What you receive:**

- Scope header: projects, sprint(s), time horizon, total discovered, total inspected, coverage state
- Grouped result: ready to pull · needs story work · blocked · in progress · other open work
- Recommended next candidates
- Cross-cutting flags: unassigned work, stale work
- Confirmation that Jira was not changed

**Likely follow-up:** "Take the items that need story work and show me why they are not ready."

→ [Full start-to-finish walkthrough with the Atlas scenario](/agent-ready-repo/docs/guides/atlassian/tutorials/review-your-team-backlog/)\
→ [Exact jira-team-status reference](/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/#jira-team-status)

---

## Find ready work

Ask for items the team can pick up now without story work.

:::tip[YOU SAY]
What is ready to pull in the Atlas backlog? Show the top ten.
:::

**Read/write status:** Read-only.

**What is inspected:** the team scope you have configured or the agent last resolved. "Ready to pull" means: in scope, in an eligible open-work state, no known unresolved blocker, and enough definition to begin. It is not the same as Jira `To Do`.

**What you receive:** a ranked list with issue key, title, component or area, and a one-line readiness summary. The agent notes if any candidate's readiness could not be confirmed (shown as "Needs confirmation" rather than forcing certainty).

**Likely follow-up:** "Update the sprint for the top five" (will require confirmation before writing).

---

## Find blockers and stale work

Ask for what is stuck or going nowhere.

:::tip[YOU SAY]
What is blocked in the Atlas backlog? Include anything stale for more than 14 days.
:::

**Read/write status:** Read-only.

**What is inspected:** issues with a known unresolved dependency, a blocker link, or no status change in the configured stale window.

**What you receive:** blocked issues with the blocker reason; stale issues with days since last update. Both groups are cross-cutting — an issue can appear as Blocked and In Progress simultaneously.

**Likely follow-up:** "Who can unblock this?" or "Show me all blockers waiting on the platform team."

---

## Find unassigned work

Ask for open work with no owner.

:::tip[YOU SAY]
Show me all unassigned issues in the Atlas backlog that are ready to pull.
:::

**Read/write status:** Read-only.

**What you receive:** unassigned issues filtered by the status group you specify. Unassigned is a cross-cutting flag; the agent shows the readiness group alongside the unassigned flag so you can prioritise.

**Likely follow-up:** "Assign APP-312 to me" (will require confirmation before writing).

---

## Improve stories that are not actionable

Ask the agent to review weak stories and produce improvements — without writing to Jira.

:::tip[YOU SAY]
Take the items that need story work.

Apply our story-readiness bar and show me:

1. why each item is not actionable
2. a proposed rewrite
3. any question the product owner still needs to answer
4. whether the item would be ready after the proposed change

Draft only. Do not update Jira.
:::

**Read/write status:** Read-only. The agent produces drafts only. Nothing goes to Jira until you explicitly approve in a separate step.

**Scope assumptions:** works on the group of items from a previous backlog review, or on issues you name explicitly (e.g. "improve APP-206 and API-104").

**What is inspected:** each issue's description and acceptance criteria, checked against the story-readiness bar (five questions: outcome clarity, acceptance criteria, scope, dependencies, and safe-to-begin).

**What you receive:** for each issue —

- Which readiness question failed and the specific gap
- A proposed description rewrite
- Proposed acceptance criteria (where applicable)
- An unresolved human question (if any)
- Expected readiness after the proposed draft is applied
- Confirmation that Jira was not changed

**Progression:**

```
Review (read-only) → Draft (read-only) → Approve → Write (confirmed)
```

**Likely follow-up:** "Update APP-206 and API-104 with the approved drafts."

→ [Full story improvement walkthrough with the Atlas scenario](/agent-ready-repo/docs/guides/atlassian/tutorials/review-your-team-backlog/#stage-2--improve-weak-stories)\
→ [Exact jira-story-triage reference](/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/#jira-story-triage)

---

## Update approved Jira issues

Apply drafts you have reviewed and approved. This is the first step that writes to Jira.

:::tip[YOU SAY]
Update APP-206, APP-219, and API-104 with the approved drafts.

Leave every other issue unchanged.

Do not change status, assignee, priority, sprint, or labels.
:::

**Read/write status:** Writes to Jira only after you confirm the exact payload.

**What happens before any write:**

The agent shows you a preview:

- Exact issue keys
- Exact fields being changed
- Current values (where available)
- Proposed values
- Protected fields (will not change): status · assignee · sprint · priority · labels
- Total number of writes
- Confirm or cancel action

Type `confirm` to proceed. Type `cancel` to stop. Nothing is written until you confirm.

**What you receive after writing:**

- Successful changes (with issue keys and links)
- Failed changes (with reason and recovery action)
- Confirmation that protected fields were not changed
- Partial-success state if any writes failed

**Partial failure:** if one write fails (e.g. 403 due to reporter-only access), the others succeed. The agent preserves the failed draft and tells you exactly how to retry.

**Likely follow-up:** "Retry APP-219 with the same draft" (once you have edit access).

→ [Full write confirmation walkthrough](/agent-ready-repo/docs/guides/atlassian/tutorials/review-your-team-backlog/#stage-3--apply-approved-changes)\
→ [Exact jira write reference](/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/#jira)

---

## Prepare a team or sprint summary

Ask for a stand-up summary or a Confluence-ready weekly update.

:::tip[YOU SAY]
Give me a stand-up summary for the Atlas team.

Include progress, blockers, risks, and what is ready next.

Then prepare a concise weekly version suitable for the Atlas Confluence space.

Do not publish until I approve it.
:::

**Read/write status:** Read-only for the stand-up summary. The Confluence draft is read-only until you explicitly say "publish."

**What you receive:**

- A stand-up summary (read-only): progress, blockers, risks, recommended next work
- A Confluence-ready draft (not published): formatted for the target Confluence space
- Confirmation that Confluence has not been updated

**Likely follow-up:** "Publish the Confluence draft to the Atlas space" (will show you the exact page, space, and content before writing).

→ [Exact confluence-publisher reference](/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/#confluence-publisher)

---

## See also

| Resource | When to use it |
|---|---|
| [Review your team backlog — tutorial](/agent-ready-repo/docs/guides/atlassian/tutorials/review-your-team-backlog/) | Full start-to-finish walkthrough with the Team Atlas scenario |
| [Atlassian skills reference](/agent-ready-repo/docs/guides/atlassian/reference/atlassian-skills/) | Exact read, write, coverage, limit, and approval contracts |
| [How the Atlassian pack works](/agent-ready-repo/docs/guides/atlassian/explanation/atlassian-pack/) | Why the workflows are separate; composition model |
| [Atlassian journey](/journeys/atlassian/) | Four-stage visual storyboard |
| [Atlassian pack](/packs/atlassian/) | Pack overview, install, credentials |
