---
name: Atlassian
scope: user
tagline: "Run Jira and Confluence from a conversation"
skills:
  - jira
  - jira-align
  - jira-brief-intake
  - jira-align-brief-intake
  - jira-defect-flow
  - jira-story-triage
  - jira-team-status
  - flow-metrics
  - confluence-crawler
  - confluence-publisher
  - ai-adoption-report
installCommand: "agentbundle install --pack atlassian --scope user"
docsUrl: /guides/atlassian/
journeyUrl: /journeys/atlassian/
---

See what the team can work on, improve weak stories, apply only approved Jira
changes, and prepare team updates — without starting from JQL or internal skill
names.

**Starts read-only.** No Jira data changes until you confirm the exact fields.

---

Try this first:

```
Show me the whole Atlas team backlog across APP and API. Include the sprint,
open backlog, blocked work, and unassigned issues. Group into ready to pull,
needs story work, blocked, and in progress. Do not change Jira.
```

What you get: 184 issues inspected · 17 ready to pull · 26 need story work ·
8 blocked · 11 in progress — with scope, completeness, and recommended next
candidates. Jira was not changed.

---

### What you can do

**See what the team can work on**

Ask for the whole backlog, a sprint status, what is blocked, or what is unassigned.
The agent reads Jira and returns a grouped, annotated result with scope and
completeness disclosed. Nothing is written.

```
What can the Atlas team pick up next?
```

---

**Make the backlog actionable**

Ask for story improvements. The agent explains why each item fails the readiness
bar, proposes a rewrite of the description and acceptance criteria, and surfaces
any question only the product owner can answer. Read-only until you approve.

```
Take the items that need story work. Draft improvements. Do not update Jira.
```

---

**Update Jira safely**

When you are ready to write, the agent shows the exact issue keys, fields, current
values, and proposed values before writing anything. Protected fields — status,
assignee, sprint, priority, labels — are never touched unless you explicitly name
them.

```
Update APP-206 and API-104 with the approved drafts. Leave everything else unchanged.
```

---

**Share the result**

Turn a backlog review into a stand-up summary or a Confluence-ready weekly update.
The agent drafts; you approve before anything is published.

```
Give me a stand-up summary. Then prepare a Confluence draft — do not publish until I approve it.
```

---

### The common journey

Orient (read-only) → Improve (draft-only) → Approve and act → Communicate

Each stage is optional. You can stop after the backlog review, improve only
selected stories, or skip directly to a stand-up summary. The earlier stages
are always read-only.

[See the full start-to-finish tutorial](../../docs/guides/atlassian/tutorials/review-your-team-backlog/)
· [Follow the four-stage storyboard](../../journeys/atlassian/)

---

### Skills included — under the hood

You do not need to name these skills. They activate from natural-language requests.

See the [skills reference](../../docs/guides/atlassian/reference/atlassian-skills/)
for exact read, write, coverage, limit, and approval contracts.
