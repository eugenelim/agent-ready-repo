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

**§1 — Ready to pull**

| Key | Summary | Priority | Complexity | Updated |
|---|---|---|---|---|
| APP-203 | Add rate limiting to API gateway | High | Standard | 2d ago |
| APP-211 | Refactor auth token refresh | Medium | Standard | 4d ago |
| API-98 | Paginate GET /users endpoint | Medium | Quick | 3d ago |

**§3 — Blocked**

| Key | Summary | Blocker | Owner hint |
|---|---|---|---|
| APP-215 | Migrate auth service | Security review pending | Security team |

**§5 — Needs detail**

| Key | Summary | What's missing | Fix with |
|---|---|---|---|
| APP-206 | Improve performance | No acceptance criteria | jira-story-triage |
| API-104 | Fix search results | Scope too broad | jira-story-triage |

```
Team status: 12 items.  Ready to pull: 3 (Quick 1 / Std 2).  In progress: 2.
Blocked: 1.  Needs detail: 3.  Scope: APP, API · Sprint 24.  Jira was not changed.
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
them to use them. See the [skills reference](../../docs/guides/atlassian/reference/atlassian-skills/) for exact contracts and limits.
