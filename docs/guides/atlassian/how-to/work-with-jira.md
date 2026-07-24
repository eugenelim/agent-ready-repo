# Work with Jira from a conversation

Ask in your own words. The agent selects the right workflow, starts read-only, and
only writes to Jira after you approve the exact change.

**Tasks on this page:**

| I want to… | Jump to |
| --- | --- |
| Review the whole team backlog | [→ Review the whole team backlog](#review-the-whole-team-backlog) |
| Find work that is ready to pull | [→ Find ready work](#find-work-that-is-ready-to-pull) |
| Find blockers and stale work | [→ Find blockers](#find-blockers-and-stale-work) |
| Make stories actionable | [→ Improve stories](#improve-stories-that-are-not-actionable) |
| Update approved Jira issues | [→ Update Jira](#update-approved-jira-issues) |
| Prepare a team summary | [→ Prepare a summary](#prepare-a-team-or-sprint-summary) |

> **Reviewing and drafting do not change Jira. Only an explicitly approved update
> request writes to Jira.**

---

## Review the whole team backlog

**YOU SAY**

```
Show me the whole Atlas team backlog across APP and API.

Include the current sprint, open backlog, unassigned work, and blocked issues.
Group everything into:

- ready to pull
- needs story work
- blocked
- in progress

Recommend five items for the team to discuss next.
Do not change Jira.
```

**WHAT HAPPENS**

The agent checks Jira credentials, resolves the Atlas team scope (it may ask
which scope to use if two match — board or team field), then reads all open issues
across APP and API. Read-only. Scope and coverage are disclosed.

**WHAT YOU GET**

A summary showing scope searched, time horizon, issue counts, and a short
prioritized candidate list. Not a raw issue list.

Example:

```
Scope: APP and API · Sprint 24 + open backlog · 12 issues (complete result)
─────────────────────────────────────────────────────
Ready to pull: 3 · Needs story work: 3 · Blocked: 2 · In progress: 2
─────────────────────────────────────────────────────
Top 5 to discuss:
1. APP-203  Add rate limiting to API gateway       Ready to pull · Standard
2. API-98   Paginate GET /users endpoint            Ready to pull · Quick
3. APP-206  Improve performance                     Needs story work
4. APP-215  Migrate auth service                    Blocked — security review
5. API-104  Fix search results                      Needs story work
─────────────────────────────────────────────────────
APP-220, API-107 unassigned — no sprint assigned.
Jira was not changed.
```

**WHAT TO ASK NEXT**

```
Take the items that need story work and show me why each fails.
```

---

## Find work that is ready to pull

**YOU SAY**

```
What can the Atlas team pick up next in APP and API?
```

**SCOPE ASSUMPTIONS**

Current sprint in APP and API, or open backlog if no sprint is specified.

**READ/WRITE**  Read-only.

**WHAT YOU GET**

Items grouped as Quick (≤ half a day), Standard (1–2 days), or Involved (more),
only those that pass all four readiness conditions:

1. In the selected team scope
2. In an eligible backlog state (not already in progress or done)
3. No known unresolved blocker
4. Meets the [five-question story-readiness bar](#the-five-question-bar)

Items where any condition can't be determined are labelled **needs confirmation**,
not asserted ready.

**WHAT TO ASK NEXT**

```
Show me the Quick items with no assignee.
```

---

## Find blockers and stale work

**YOU SAY**

```
What is blocked in the Atlas backlog?
What items haven't been updated this week?
```

**WHAT YOU GET**

Blocked items with the blocker named — flagged field, unresolved "is blocked by"
link, or a status in a team-declared blocked set. Stale items with last-update date.

**WHAT TO ASK NEXT**

```
Which blocked items have had no update for more than five days?
```

---

## Improve stories that are not actionable

There are two ways to ask:

**Natural:**

```
Make these stories actionable.
```

**Expert phrasing:**

```
Apply the five-question bar to the items that need story work.
```

Both activate the same workflow.

### The five-question bar

> A story is actionable when all five are true:
> **(Q1)** it is a **self-contained code/config/doc change** — not discovery, design,
> or coordination work;
> **(Q2)** it names a **reachable repo or file scope** so the change can be located
> without a follow-up meeting;
> **(Q3)** its **acceptance criteria are checkable by diff review alone** — no "TBD",
> "coordinate with", "decide on", or "prototype";
> **(Q4)** **no human decision is needed mid-flight** — no open design question,
> no external approval gate that cannot be confirmed before work starts;
> **(Q5)** it is **right-sized for one PR** — the scope is an enumerable set of files
> or PRs a single person or agent can produce without decomposing into sub-stories.

**WHAT YOU GET**

For each weak item:

```
APP-206 — "Improve performance"
What is missing:       Q2 (no scope) · Q3 (no metric or ACs)
Why it prevents action: An engineer can't locate the change or know when done.
Proposed improvement:  "Reduce p95 on GET /api/products from 800 ms to ≤ 400 ms.
                        ACs: p95 ≤ 400 ms in load test; histogram added."
Unresolved question:   None.
Ready after change?    Yes.
Jira not changed.
```

**YOUR DECISION**

Review each draft. If a draft is wrong, say so — the agent revises without touching
Jira. When you're satisfied, move to the approval step.

---

## Review → Draft → Approve → Write

These four phases are always separate. The agent never skips from reading to writing.

| Phase | What happens | Jira changes? |
| --- | --- | --- |
| Review | Read all issues; group by state | No |
| Draft | Propose improvements per item | No |
| Approve | You confirm exact issues and fields | No |
| Write | Agent updates only approved items | **Yes** |

---

## Update approved Jira issues

**YOU SAY**

```
Update APP-206, APP-219, and API-104 with the approved drafts.
Leave every other issue unchanged.
Do not change status, assignee, priority, sprint, or labels.
```

**BEFORE WRITING** — the agent shows a write confirmation:

```
Issues to update:  APP-206, APP-219, API-104
Field to change:   description
Protected fields:  status, assignee, priority, sprint, labels
Total writes:      3
─────────────────────────────────────────────────────
[Cancel]   [Apply all three]
```

**AFTER WRITING** — the agent confirms what changed and what didn't, with links
to each updated issue. Partial success (one write failed) is reported explicitly,
with a retry path.

---

## Prepare a team or sprint summary

**YOU SAY**

```
Give me a stand-up summary for the Atlas team.
Include progress, blockers, risks, and what is ready next.

Then prepare a concise weekly version suitable for the Atlas Confluence space.
Do not publish until I approve it.
```

**WHAT YOU GET**

A stand-up block (in-progress, ready, blocked, risks) and a Confluence draft.
The draft is not published until you say so.

---

## Common follow-ups

```
Which ready items have no assignee?
Which blocked items have had no update this week?
Show only backend-ready work.
What changed since yesterday?
Turn this into a stand-up summary.
Prepare a Confluence update, but do not publish it.
```

---

## Want the full start-to-finish walkthrough?

See the [tutorial: Review your team's Jira backlog from start to finish](../tutorials/review-your-team-backlog.md).

For exact skill contracts, limits, and field lists: [Atlassian skills reference](../reference/atlassian-skills.md).
