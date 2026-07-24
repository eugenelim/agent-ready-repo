---
name: jira-team-status
description: "Summarize a Jira team's work and backlog for sprint, stand-up, and team-status views — what the team can pick up next, and what is ready, blocked, in progress, unassigned, stale, recently changed, or needs product attention. Triggers on \"show me the entire backlog\", \"what can the team pick up next\", \"what is blocked\", \"what is sitting unassigned\", \"what changed in this sprint\", \"give me a team status for stand-up\", \"which items need product attention\", \"team sprint status\". Ask only for missing team or time scope; read-only unless the user explicitly asks to update an item; disclose coverage or truncation. Do NOT use to judge readiness in depth or improve weak stories / draft acceptance criteria (use jira-story-triage), to create an issue (use jira), to turn an epic into specs (use jira-brief-intake), to fix a defect (use jira-defect-flow), or for the local workspace queue (use workspace-status)."
metadata:
  version: "1.1"
---

# Skill: jira-team-status

A read-only status view of a team's Jira work. It answers *where the team's work
stands* and *what to pick up next* — organized by the dimensions people actually ask
about: **Ready to pull, In progress, Blocked, Unassigned, and Needs detail**, plus a
recently-changed note. Then it offers a pick-up hand-off so a team member can start
delivery on a ready item.

Read-only by default. This skill does not judge item quality in depth or rewrite weak
stories — that is `jira-story-triage`. When the user wants to fix a weak item (draft
acceptance criteria, clarify the outcome), this skill routes them to
`jira-story-triage` by name. Its only write is a bare pass-through to the `jira`
skill's `update-issue` when the user explicitly asks to set a field, with the payload
confirmed first.

## Output rendering

Table — When presenting several items that share the same fields, render a Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail list. Right-align numeric columns.

## Cross-skill invocation — name, not path

Sibling and host skills are named **by their `name:` field, never by path**.
When this skill says *"route to `jira-story-triage`"*, the agent dispatches the
skill registered under that name. If the skill is absent, the agent surfaces an
install hint rather than stopping.

## Prerequisites

**`jira` is installed and authenticated — a hard dependency.**
Invoke: `jira: check`.
- Exit 0 → proceed.
- Exit 2 → tell the user to run `credential-setup` themselves and stop.

## The "ready to pull" rule

"Ready to pull" is a defined rule, not a silent `status = "To Do"`. An item is
**ready to pull** when **all four** hold:

1. **In the selected team scope** — the project(s), board, sprint, or team field the
   user asked about.
2. **In an eligible backlog state** — default: Jira `statusCategory = "To Do"` (the
   stable category that spans Backlog / To Do / Selected for Development / Open across
   any instance). This deliberately excludes work already `In Progress` or `Done`.
   **Teams override the eligible statuses/fields** — name explicit statuses (e.g.
   "Ready for Dev") and this rule uses them instead of the default.
3. **No known unresolved blocker** — see [the blocker signal](#the-blocker-signal).
4. **Meets the team's story-readiness bar** — the [five-question readiness
   bar](#the-five-question-readiness-bar) below.

**When any clause cannot be determined** for an item — the status doesn't map cleanly,
the blocker state is unreadable, or readiness is ambiguous — the item is labelled
**needs confirmation**. The skill never asserts an item is ready (or not ready) on a
signal it could not read.

## The five-question readiness bar

> A story is actionable when all five are true:
> (Q1) it is a **self-contained code/config/doc change** — not discovery, design, or coordination work;
> (Q2) it names a **reachable repo or file scope** so the change can be located without a follow-up meeting;
> (Q3) its **acceptance criteria are checkable by diff review alone** — no "TBD", "coordinate with", "decide on", or "prototype";
> (Q4) **no human decision is needed mid-flight** — no open design question, no external approval gate that cannot be confirmed before work starts;
> (Q5) it is **right-sized for one PR** — the scope is an enumerable set of files or PRs a single person or agent can produce without decomposing into sub-stories.

Q5 exists because Jira stories are a legacy delivery-capacity allocation mechanism:
a story sized for a full sprint passes Q1–Q4 but cannot be handed to a single
agent or engineer without decomposition.

## The blocker signal

An item counts as **Blocked** when any of these is true:
- its **Flagged** / impediment field is set;
- it has an unresolved outward **"is blocked by"** issuelink;
- its status is in a **team-declared blocked set** (none by default).

When none of the three can be read from the fetched fields, the blocker state is
undeterminable → the item is **needs confirmation**, not asserted blocked or unblocked.

## Lifecycle

### Stage 1 — Repo grounding

Detect `git remote -v` in the working directory. If a URL is found, label it
**Invocation repo: `<URL>`** — the repo the agent is running from.

If not in a git repo, offer:
> "Optionally supply a repo URL or name — this improves story scope verification.
> Enter to skip."

Proceed with "Invocation repo: unknown" if the user declines.

### Stage 2 — Intake

Ask only for what's missing to set scope; don't over-elicit. Accept:
- A Jira project key (or several, across projects).
- An optional **sprint** (default: `sprint in openSprints()`), a **team name**, or a
  **JQL filter** to narrow.
- **Whole-backlog scope:** when the user asks for the entire backlog ("show me the
  entire ATLAS backlog"), drop the `sprint in openSprints()` default and query the
  project's open backlog (`statusCategory != Done`), not just the current sprint.

Fetch the fields the status dimensions need — status (and its category), assignee,
last-updated, blocker signals — in one call:
```
jira: search "project = PROJ AND sprint in openSprints() AND statusCategory != Done"
      --fields "summary,description,issuetype,status,statusCategory,assignee,updated,priority,labels,issuelinks,customfield_*"
      --limit 100
```
`customfield_*` captures story points and the Flagged/impediment field (names vary by
instance). **Disclose coverage:** if the result is truncated at `--limit`, say so and
report the total.

### Stage 3 — Classify each item into a status dimension

Assign each item to exactly one **primary** dimension, by this precedence:
1. **Blocked** — the blocker signal is present.
2. **In progress** — `statusCategory = "In Progress"` (and not blocked).
3. **Needs detail** — in an eligible backlog state but either unscoreable (empty /
   image-only / discovery issuetype) **or** it fails the readiness bar on content
   (Q1/Q2/Q3, or Q5 too-large, or Q4 open design question). This is the coarse
   "needs product attention" bucket; `jira-story-triage` is the tool that breaks down
   *why* per item and fixes it.
4. **Ready to pull** — satisfies [the ready-to-pull rule](#the-ready-to-pull-rule)
   (eligible state + no blocker + passes the bar).

**Undeterminable clauses never default an item into Ready to pull.** Route explicitly:
- **Blocker clause undeterminable** (Flagged field / issuelinks not readable) → surface
  in **§3 Blocked**, tagged `needs confirmation`.
- **A readiness-bar clause undeterminable** (content ambiguous) → surface in **§5 Needs
  detail**, tagged `needs confirmation`.
- **Status doesn't map to a known category** → surface in **§5 Needs detail**, tagged
  `needs confirmation`.

An item reaches §1 Ready to pull only when all four ready-to-pull clauses are
affirmatively true — never when one is merely *not known to be false*.

**Cross-cutting views** (an item may appear here *and* in its primary dimension):
- **Unassigned** — every in-scope item with no `assignee`. (Ready-to-pull items are
  expected to be unassigned; the value is spotting *in-progress* or stuck items nobody
  owns.)
- **Recently changed** — items whose `updated` falls within the window (sprint start,
  or the last 7 days for a backlog scope), most-recent first — answers "what changed?".
- **Stale** — a `⚠ stale` marker on any In-progress or Ready item whose `updated` is
  older than the staleness threshold (default 14 days; team-overridable).

### Stage 4 — Complexity (Ready-to-pull items only)

| Signal | Quick | Standard | Involved |
|---|---|---|---|
| Story-point field | ≤ 2 pts | 3–5 pts | > 5 pts |
| Description length (fallback) | ≤ 100 words | 101–200 words | > 200 words |
| AC count (secondary fallback) | ≤ 2 ACs | 3–5 ACs | > 5 ACs |

### Stage 5 — Output: the status snapshot

Emit these sections in order, always. If a section has no items, include its header
with "None in this scope."

---

**§1 — Ready to pull** — grouped by complexity

Items that satisfy the ready-to-pull rule. Grouped **Quick**, then **Standard**, then
**Involved**, so team members self-select by bandwidth.

Table columns: `Key | Summary | Priority | Complexity | Updated (⚠ if stale) | Invocation repo match?`

"Invocation repo match?" is Yes if Q2 found the invocation repo URL or name in the
item's description, Unknown otherwise. The `Updated` column carries the `⚠ stale`
marker for a ready item untouched past the staleness threshold. Mark any
`needs confirmation` items explicitly.

Batching note (optional): if two or more ready items have distinct repo scopes and no
stated dependency between them, add: "Can run concurrently: PROJ-101, PROJ-103."

---

**§2 — In progress**

Table columns: `Key | Summary | Assignee | Updated (⚠ if stale)`

---

**§3 — Blocked**

Table columns: `Key | Summary | Blocker (which signal) | Owner hint`

---

**§4 — Unassigned**

Every in-scope item with no assignee. Table columns:
`Key | Summary | Primary dimension | Status`

---

**§5 — Needs detail (product attention)**

Backlog items that are not ready — unscoreable or failing the bar on content.
Table columns: `Key | Summary | What's missing (coarse) | Fix with`

The "Fix with" cell points to `jira-story-triage` for the item-by-item reasons and a
draft fix.

---

**Recently changed:** a compact list — `PROJ-108 (2h ago), PROJ-101 (yesterday), …` —
top items by `updated`. Omit if the scope has no recent changes.

**Summary line:**
```
Team status: <total> items.  Ready to pull: <r> (Quick <q> / Std <s> / Inv <i>).
In progress: <p>.  Blocked: <b>.  Unassigned: <u>.  Needs detail: <d>.  Stale: <st>.
Scope: <JQL>.  Coverage: <all N | truncated at limit — total M>.  Invocation repo: <URL or unknown>.
```

### Stage 6 — Pick-up hand-off (read-only)

After the snapshot, offer a pick-up. Read-only routing — this skill starts no rewrite
of its own.

**Option A — Start delivery** (if §1 has items):
> "Ready to start delivery? Suggested: **`<highest-priority Quick item>`** — `<one-line summary>`.
> [yes / pick another / skip]"

- `yes` → issuetype is Bug/Defect? Route to `jira-defect-flow` by name. Otherwise offer
  to open a `new-spec` session scoped to this item. (Surface an install hint if the
  target skill is absent.)
- `pick another` → list §1 items by complexity group; user picks.
- `skip` → end gracefully.

**Option B — Improve an item that needs detail** (if §5 has items):
> "Want to make a not-ready item actionable — draft acceptance criteria, clarify the
> outcome? Suggested: **`<highest-priority §5 item>`**. [yes / pick another / skip]"

- `yes` → route to `jira-story-triage` by name, scoped to that item (it explains the
  reason and drafts the fix with write-after-approval). Surface an install hint if
  `jira-story-triage` is absent; in the meantime give the item key.
- `pick another` / `skip` → behave as above.

**Explicit update escape hatch.** If the user explicitly asks to set a specific field
on a specific item ("set PROJ-101's priority to High"), this skill may make a **bare
pass-through** to `jira: update-issue` — show the exact payload, get a yes, then write.
It never runs a multi-step collaborative rewrite; that is `jira-story-triage`'s job.

If the user declines both options, end gracefully with a note of what they could do
next.

## Don't

- Don't rewrite or improve a story's content here — route improvement to
  `jira-story-triage`. This skill is a read-only status view plus routing.
- Don't run a multi-step collaborative rewrite or draft acceptance criteria yourself;
  the only write is the confirmed bare pass-through `update-issue` in stage 6.
- Don't assert an item is ready, blocked, or not — or hide uncertainty — when the
  signal can't be read. Label it **needs confirmation**.
- Don't conflate this skill with the local workspace-queue / session-orientation
  skill. This skill is Jira-only; it reads external Jira project data.
- Don't read or write any local project state; this skill is Jira-only.
- Don't invoke `jira-story-triage`, `jira-defect-flow`, or `new-spec` without checking
  whether they are installed (by-name dispatch probe); surface an install hint if absent.
- Don't hardcode a sibling skill by path; invoke by name.

## Edge cases

- **No ready-to-pull items (§1 empty).** Still emit §2–§5. Pick-up offers only Option B
  (improve a §5 item). Note: "No items ready to pull in this scope — the fastest path is
  to make a §5 item actionable (`jira-story-triage`)."
- **Everything is ready to pull.** Emit §1 with full complexity grouping and offer the
  delivery pick-up directly; other sections show "None in this scope."
- **Blocker signal unreadable.** If the Flagged field and issuelinks aren't in the
  response, note "blocker state unverified for this scope" and mark affected items
  **needs confirmation** rather than assuming unblocked.
- **`jira-story-triage` / `jira-defect-flow` / `new-spec` absent.** Route by name;
  harness reports it absent; surface: "Install the `<pack>` pack to enable this
  hand-off. In the meantime, here is the item key: `<KEY>`."
- **Truncated result.** Always disclose in the summary's Coverage field; offer to
  narrow scope or paginate.

## Examples

See [`references/examples.md`](references/examples.md).
