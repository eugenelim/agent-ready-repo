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
docsUrl: /docs/guides/atlassian/
journeyUrl: /journeys/atlassian/
---

See what the team can work on, improve weak stories, apply only approved Jira
changes, and prepare team updates — without starting from JQL or internal skill
names.

**Starts read-only.** The first thing you ask is always safe.

---

### Try this first

```
Show me the whole Acme team backlog across APP and API.
Include the current sprint, open backlog, unassigned work, and blocked issues.
Group everything into ready to pull · needs story work · blocked · in progress.
Do not change Jira.
```

What you'll get:

```
Scope: APP and API · Sprint 24 + open backlog · 12 issues (complete)
───────────────────────────────────────────────────────
Ready to pull: 3  ·  Needs story work: 3  ·  Blocked: 2  ·  In progress: 2
───────────────────────────────────────────────────────
Top 5 to discuss:
 APP-203  Add rate limiting to API gateway       Ready · Standard
 API-98   Paginate GET /users endpoint            Ready · Quick
 APP-206  Improve performance                     Needs story work
 APP-215  Migrate auth service                    Blocked — security review
 API-104  Fix search results                      Needs story work
───────────────────────────────────────────────────────
Jira was not changed.
```

---

### Four things you can do

**See what the team can work on**
Ask for the whole backlog, a sprint status, what's blocked, or what's unassigned.
The agent reads Jira and returns a grouped summary. Nothing is written.

> "What can the Acme team pick up next?"
> "What is blocked in APP?"
> "What's sitting unassigned this sprint?"

Uses `jira-team-status` under the hood.

---

**Make the backlog actionable**
Ask the agent to apply the team's readiness bar to weak stories. It explains
exactly why each item fails, then proposes a rewrite. Read-only until you approve.

> "Make these stories actionable."
> "Apply the five-question bar to the items that need story work."

Uses `jira-story-triage` under the hood.

---

**Update Jira safely**
When you're ready to write, name the exact issues and confirm the write before
anything changes. Status, assignee, priority, and labels are protected unless you
explicitly say to change them.

> "Update APP-206, APP-219, and API-104 with the approved drafts."

Uses `jira` under the hood.

---

**Share the result**
Turn a backlog review into a stand-up summary or a Confluence-ready update. The
agent drafts; you approve before anything is published.

> "Give me a stand-up summary. Then prepare a Confluence draft — do not publish yet."

Uses `confluence-publisher` under the hood.

---

### The common journey

Orient → Improve → Approve and act → Communicate

Each stage builds on the last. You can stop at any point — the earlier stages are
always read-only.

---

### Skills included — under the hood

The skills below activate from natural-language requests. You don't need to name
them to use them. See the [skills reference](/docs/guides/atlassian/reference/atlassian-skills/) for exact contracts and limits.
