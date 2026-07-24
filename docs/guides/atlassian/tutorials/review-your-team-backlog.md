# Review your team's Jira backlog from start to finish

**What you'll do:** Ask the agent to show you everything the Atlas team has in their
Jira backlog, identify what's ready to pick up and what needs work, draft story
improvements, approve three targeted Jira updates, and prepare a stand-up summary.

**Prerequisites:** The `atlassian` pack installed; Jira credentials configured via
`credential-setup`. Verify connectivity with `python scripts/jira.py check` — exit 0
means you're ready.

**Time:** About 30 minutes.

> **Starts read-only.** Every step in this tutorial is read-only until you give
> explicit approval to write. You can follow along in a real Jira instance; nothing
> changes until you say so.

---

## Progress

```
1. See the work   →   2. Improve weak stories   →   3. Apply approved changes   →   4. Share the result
```

This tutorial walks all four stages once, in order.

---

## Before you begin

You need:

- The `atlassian` pack installed at user scope:
  ```bash
  agentbundle install --pack atlassian --scope user
  ```
- Jira credentials configured. Run:
  ```bash
  python scripts/jira.py check
  ```
  Exit 0 → proceed. Exit 2 → run `credential-setup` to store your Jira API token.
  The token never appears in a file the agent can read.

For the full credential model, see [Credentialed skills](../../credential-brokers/explanation/credentialed-skills.md).

---

## Stage 1 — See the work

**Goal:** get a complete, read-only snapshot of everything the Atlas team has
across APP and API.

### Step 1.1 — The opening request

Say this to your agent:

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

### Step 1.2 — The agent may ask one scope question

When two matching scopes exist, the agent asks before proceeding:

> "I found two possible Atlas scopes:
>
> 1. The Atlas Jira board
> 2. Issues whose Team field is Atlas
>
> Which should I use?"

Reply with your preference. If you don't have a Team field configured, say "the Atlas board."

### Step 1.3 — What you receive

The agent returns a **summary**, not a raw issue dump:

```
Scope searched:    APP and API, current sprint (Sprint 24) + open backlog
Time horizon:      Sprint 24 (active) + all open backlog items
Issues inspected:  12 issues — complete result, no truncation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ready to pull:     3
Needs story work:  3
Blocked:           2
In progress:       2
Unassigned:        2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Top 5 candidates for team discussion:

1. APP-203 — Add rate limiting to API gateway (Ready to pull · Standard)
2. API-98  — Paginate GET /users endpoint (Ready to pull · Quick)
3. APP-206 — Improve performance (Needs story work — Q2 scope, Q3 ACs missing)
4. APP-215 — Migrate auth service (Blocked — pending security review)
5. API-104 — Fix search results (Needs story work — Q2 scope, Q3 ACs missing)

Data quality: APP-220 and API-107 have no assignee and no sprint assignment.
Jira was not changed.
```

**What "ready to pull" means:** An item is ready to pull when all four hold — it
belongs to the selected team scope, is in an eligible backlog state, has no known
unresolved blocker, and meets the team's story-readiness bar (the five-question
bar below). It is **not** a silent `status = "To Do"`.

**Check:** Does the number of ready items look right? If an item is missing or
misclassified, ask why — the agent will explain what signal it couldn't read and
label it "needs confirmation" rather than asserting.

---

## Stage 2 — Improve weak stories

**Goal:** understand exactly why each weak item fails readiness, draft improvements,
and confirm the draft before anything touches Jira.

### Step 2.1 — Request story work

```
Take the items that need story work.

Apply our five-question bar and show me:

1. why each item fails
2. a proposed rewrite
3. any question the product owner still needs to answer
4. whether the item would be ready after the proposed change

Draft only. Do not update Jira.
```

### Step 2.2 — The five-question bar

The agent applies this bar to every item:

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

### Step 2.3 — What you receive

One block per issue, draft only:

```
APP-206 — "Improve performance"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
What is missing:   Q2 — no service or file scope. Q3 — no metric or baseline.
Why it prevents action: An engineer can't locate the change or know when done.
Proposed improvement:
  "Reduce p95 response time on GET /api/products from 800 ms to ≤ 400 ms.
  Add response-time histogram to API gateway metrics (existing Prometheus
  endpoint). ACs: p95 ≤ 400 ms in load test; histogram labels product-id
  and endpoint; existing tests green."
Unresolved question:  None — scope and metric are determined from existing
                       monitoring. PO confirmation not needed.
Ready after change?   Yes — all five questions would pass.
Jira not changed.

APP-219 — "SSO changes for new IdP"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
What is missing:   Q2 — no service or config path. Q3 — no ACs. Q4 — open
                   design question: which IdP fields to map.
Why it prevents action: An engineer doesn't know what to change or how to
                        verify it.
Proposed improvement:
  "Migrate Okta SAML auth to the new Okta tenant (tenant ID in ticket).
  Update SAML SP config in app/config/sso.yml: entityID, SSO URL, and
  x509 cert. ACs: local SSO login succeeds with new tenant; old tenant
  returns a clear deprecation error."
Unresolved question:  PO to confirm the new Okta tenant ID before work starts.
                       Without it, Q4 still fails.
Ready after change?   Gated — passes once PO confirms tenant ID.
Jira not changed.

API-104 — "Fix search results"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
What is missing:   Q2 — no endpoint or file. Q3 — "fixed" is not checkable.
Why it prevents action: "Fix" says nothing actionable about the expected
                        behavior or scope.
Proposed improvement:
  "GET /api/search?q= returns results ranked by title-match score first,
  then recency. Scope: api/search.py and tests. ACs: query 'atlas' returns
  Atlas project first; empty query returns 400; tests cover ranking and
  edge cases."
Unresolved question:  None — ranking behavior is derivable from existing
                       documentation.
Ready after change?   Yes — all five questions would pass.
Jira not changed.
```

**Your decision:** Review each draft. Do they match what the team intends? If a
draft is wrong, tell the agent — it will revise without touching Jira. When you're
satisfied with three of them, move to the approval step.

---

## Stage 3 — Apply approved changes

**Goal:** write only the three agreed drafts to Jira, nothing else.

### Step 3.1 — The approval request

```
Update APP-206, APP-219, and API-104 with the approved drafts.

Leave every other issue unchanged.
Do not change status, assignee, priority, sprint, or labels.
```

### Step 3.2 — The write preview

Before anything is written, the agent shows you exactly what will change:

```
Write confirmation — review before applying
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Issues to update:    APP-206, APP-219, API-104
Field to change:     description (and acceptance criteria sub-field)
Fields protected:    status, assignee, priority, sprint, labels,
                     issuetype — none of these change
Total writes:        3 (one update-issue call per issue)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Cancel]   [Apply all three]
```

> **This is the point of no return.** Everything up to here has been read-only.
> Saying "Apply" writes to your live Jira instance.

### Step 3.3 — After writing

```
Result
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Changed:   APP-206 (description updated)
           APP-219 (description updated — Gated; remind PO to confirm tenant ID)
           API-104 (description updated)
Unchanged: All other issues in APP and API
Links:     APP-206 · APP-219 · API-104
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Failure handling:** If one write fails (a 409 conflict or a permission error),
the agent reports which issue failed, what the error was, and offers to retry only
that issue. The other two are not rolled back — partial success is reported
explicitly.

---

## Stage 4 — Share the result

**Goal:** produce a stand-up summary and a Confluence-ready weekly update, without
publishing until you say so.

### Step 4.1 — Stand-up summary

```
Give me a stand-up summary for the Atlas team.

Include progress, blockers, risks, and what is ready next.

Then prepare a concise weekly version suitable for the Atlas Confluence space.
Do not publish until I approve it.
```

### Step 4.2 — What you receive

```
Atlas team stand-up — Sprint 24
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
In progress:  APP-198 (OAuth token refresh), API-92 (Webhook retry)
Completed:    —
Ready next:   APP-203 (rate limiting), APP-211 (error messages), API-98 (pagination)
Blockers:     APP-215 — awaiting security review sign-off
Risks:        APP-219 — needs PO to confirm Okta tenant ID before starting
Notes:        3 stories updated this session (APP-206, APP-219, API-104).
              APP-220 and API-107 unassigned — team to triage.

───

Atlas weekly update (draft — not published)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This week, the Atlas team progressed OAuth token refresh (APP-198) and webhook
delivery retry (API-92). Three backlog stories were sharpened to be ready for
engineering. Three items are ready to pull next sprint: rate limiting, error
message standardisation, and user endpoint pagination. One item (APP-215) is
blocked pending a security review.

[Review draft]  [Publish to Confluence]  [Discard]
```

**Your decision:** Review the Confluence draft and say "Publish" when satisfied.
The agent will not publish automatically.

---

## What you built

You walked the complete Atlas team backlog from end to end:

- Oriented to the full backlog state without changing anything
- Applied the five-question bar to surface exactly what was missing
- Drafted improvements without touching Jira
- Previewed the exact write before confirming
- Applied three targeted updates with nothing else changed
- Produced a stand-up summary and a Confluence-ready update

The key boundary: **reading and drafting are always safe; Jira changes require
an explicit, issue-by-issue approval.**

---

## What to read next

- [Work with Jira from a conversation](../how-to/work-with-jira.md) — common tasks,
  quick reference for the requests you'll use most
- [Atlassian skills reference](../reference/atlassian-skills.md) — exact inputs,
  reads, writes, limits, and approval behavior for every skill
- [The Atlassian pack as a system](../explanation/atlassian-pack.md) — why the
  orientation, triage, write, and reporting workflows are separate
