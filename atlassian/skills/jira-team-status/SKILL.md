---
name: jira-team-status
description: "Team backlog status for sprint, stand-up, and orientation — what the team can pick up, what is ready, blocked, in progress, unassigned, stale, or needs story work. Triggers on \"show me the team backlog\", \"what can the team pick up\", \"what is ready\", \"what is blocked\", \"what is unassigned\", \"sprint status\", \"stand-up summary\", \"stale team work\". Applies the five-question bar only when explicitly asked for agent-ready or one-PR work. Always start read-only; disclose scope and completeness. Do NOT use to improve weak stories (use jira-story-triage), create an issue (use jira), apply approved updates (use jira), turn an epic into specs (use jira-brief-intake), fix a defect end-to-end (use jira-defect-flow), or for the local workspace queue (use workspace-status)."
metadata:
  version: "2.0.0"
---

# Skill: jira-team-status

A read-only team backlog view that answers *where the team's work stands* and *what to pick up next*. It organizes work by the dimensions people ask about: **Ready to pull · Needs story work · Blocked · In progress · Other open work**, with cross-cutting flags for unassigned, stale, and dependency-risk items.

Two readiness concepts are distinct in this skill:

- **Team readiness (default)** — the item is in scope, in an eligible open-work state, has no known blocker, and has enough definition for the team to begin. This is what "ready to pull" means unless the user asks for something more specific.
- **Agent-execution readiness (explicit optional lens)** — the item also passes the five-question bar (self-contained code change, named repo, diff-checkable ACs, no human decision mid-flight, one-PR sized). This lens is activated only when the user asks for "agent-ready work", "one-PR tasks", "coding-agent candidates", "diff-reviewable tasks", or equivalent explicit language.

Read-only by default. This skill does not rewrite stories — that is `jira-story-triage`. When the user wants to improve a weak item, route to `jira-story-triage`. When the user wants to apply approved changes, route to the `jira` skill's `update-issue` with explicit per-issue confirmation.

## Output rendering

Table — When presenting several items that share the same fields, render a Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail list. Right-align numeric columns.
Rationale / narrative — Use short ## headings and 2–3 sentence paragraphs for the header block, recommendations, and risks sections.

## Cross-skill invocation — name, not path

Sibling skills are named **by their `name:` field, never by path**.

## Prerequisites

**`jira` is installed and authenticated — a hard dependency.**
Invoke: `jira: check`.
- Exit 0 → proceed.
- Exit 2 → tell the user to run `credential-setup` themselves and stop.

## The team readiness rule

"Ready to pull" uses a four-clause rule, not a silent `status = "To Do"`. An item is **ready to pull** for the team when **all four** hold:

1. **In the selected team scope** — the project(s), board, sprint, team field, saved filter, or JQL the user asked about.
2. **In an eligible open-work state** — default: Jira `statusCategory = "To Do"` (the stable category that spans Backlog / To Do / Selected for Development / Open across any instance). This excludes `In Progress` and `Done`. **Teams override eligible statuses/fields** — name explicit statuses (e.g. "Ready for Dev") and this rule uses them instead.
3. **No known unresolved blocker** — see [Blocker signal](#the-blocker-signal).
4. **Minimum definition** — all three of: (a) non-empty, non-image-only description; (b) issuetype is not a discovery artifact (Solution Design, Discovery, Spike without acceptance criteria); (c) description does not consist entirely of TBD/to-be-decided/awaiting-alignment language that prevents starting.

**When any clause cannot be determined** — status doesn't map cleanly, blocker state is unreadable, or minimum-definition is ambiguous — label the item **Needs confirmation**. Never assert ready or not-ready on a signal that could not be read.

Items that fail clause 4 go to **Needs story work** (not **Ready to pull**).

## The agent-execution readiness bar (explicit optional lens)

Activated only on explicit user requests: "agent-ready work", "one-PR tasks", "coding-agent candidates", "diff-reviewable tasks", or equivalent.

When active, filter the **Ready to pull** group further: show only items where all five also hold:

> (Q1) it is a **self-contained code/config/doc change** — not discovery, design, or coordination work;
> (Q2) it names a **reachable repo or file scope** so the change can be located without a follow-up meeting;
> (Q3) its **acceptance criteria are checkable by diff review alone** — no "TBD", "coordinate with", "decide on", or "prototype";
> (Q4) **no human decision is needed mid-flight** — no open design question, no external approval gate that cannot be confirmed before work starts;
> (Q5) it is **right-sized for one PR** — the scope is an enumerable set of files or PRs a single person or agent can produce without decomposing into sub-stories.

Label the section **Agent-ready (explicit lens active)** when this filter applies. Items that pass team readiness but not all five go to **Ready to pull (team)** in a sub-list below.

## The blocker signal

An item counts as **Blocked** when any of these is true:
- its **Flagged** / impediment field is set;
- it has an unresolved outward **"is blocked by"** issuelink;
- its status is in a **team-declared blocked set** (none by default).

When none of the three can be read, the blocker state is undeterminable → label the item **Needs confirmation**, not blocked or unblocked.

## Team-scope resolution

Resolve team scope from these sources (in preference order):
1. **Named Jira board** — user supplies board name or ID
2. **Project set** — one or more project keys (e.g. `PROJ, API`)
3. **Team field** — `Team = "Atlas"` (custom field; availability varies by instance)
4. **Saved filter** — a Jira filter name or ID the user provides
5. **Explicit JQL** — the user supplies full JQL

When the phrase "Team Atlas" maps unambiguously from one of the above, proceed.

When two or more plausible scopes exist, ask one compact clarification:
> "I found two possible Atlas scopes:
> 1. The Atlas Jira board
> 2. Issues whose Team field is Atlas
>
> Which should I use?"

When nothing resolves — no board, project key, Team field, filter, or JQL is inferable from context or conversation — ask one compact question:
> "To show the team backlog, I need a scope. Please provide one of: a Jira project key (e.g. ATLAS), a board name or ID, a Team field value, a saved filter name, or explicit JQL."

Do not ask for information already resolvable from current context, saved configuration, previous conversation, or authenticated Jira metadata. Report the final scope used in the output header.

## Lifecycle

### Stage 1 — Repo grounding

Detect `git remote -v` in the working directory. If a URL is found, label it **Invocation repo: `<URL>`**.

If not in a git repo, offer:
> "Optionally supply a repo URL or name — this improves story scope verification. Enter to skip."

Proceed with "Invocation repo: unknown" if the user declines.

### Stage 2 — Scope intake

Ask only for what's missing; don't over-elicit. Accept:
- A Jira project key (one or several), board name/ID, team name, saved filter, or JQL.
- Optional sprint filter (default: `sprint in openSprints()`).
- **Whole-backlog scope:** when the user asks for the entire backlog ("show me the entire ATLAS backlog"), drop the open-sprint default and query `statusCategory != Done` across the project.
- **Explicit time window** for stand-up: "what changed since yesterday?" → add `updated >= -1d` to the query.

After resolving scope, report it explicitly (e.g., "Scope: project = ATLAS AND sprint in openSprints()").

### Stage 3 — Fetch and paginate to completeness

Fetch all fields needed for the status dimensions in one or more calls:

```
jira: search "<JQL>" --fields "summary,description,issuetype,status,statusCategory,assignee,updated,priority,labels,issuelinks,customfield_*" --limit <large_cap>
```

`customfield_*` captures story points and the Flagged/impediment field. Set `--limit` high enough to retrieve the complete result set; do not hardcode 100.

**Pagination on Cloud (cursor-based):**
The `jira` CLI handles Cloud pagination transparently via `nextPageToken`. Use a high `--limit` (e.g. 500 or the team-configured cap); the CLI fetches all pages until `isLast = true`. After fetching, report the total count of items retrieved.

**Pagination on Server/DC (offset-based):**
The `jira` CLI handles Server pagination via `startAt`. The first response includes `total`. After fetching, report total retrieved vs. total available.

**Explicit configured cap:** if a team or workspace has configured a fetch cap (e.g. 200 items), respect it and report the cap in the coverage line.

**Coverage disclosure — report before grouped sections:**
- `Complete — N items`: all available results retrieved
- `Complete — N items (M pages)`: Cloud, multi-page, all pages fetched
- `Filtered — N items (scope excludes <criteria>)`: JQL or sprint filter intentionally narrows the result set
- `Cap reached — N of M items`: Server, reached configured cap before exhausting the result set
- `Cap reached — N items (Cloud — total unknown until complete)`: Cloud, reached cap without fetching all pages
- `Permission-limited — N items accessible`: some projects/boards were inaccessible
- `Partial — request failed after N items`: mid-fetch failure; named which boards/projects were skipped

Do not label a result "the whole backlog" without one of the above completeness statements.

### Stage 4 — Classify each item

Assign each item to exactly one **primary group**, using this precedence (highest priority first):

1. **Blocked** — the blocker signal (see "The blocker signal" section) is present.
2. **In progress** — `statusCategory = "In Progress"` and not blocked.
3. **Needs story work** — in an eligible backlog state, but fails the minimum-definition check (clause 4 of team readiness), or is unscoreable (empty / image-only / discovery issuetype).
4. **Ready to pull** — satisfies all four team-readiness clauses.
5. **Other open work** — in-scope, open, but doesn't fit the above groups (unusual status, custom workflow state).

**Undeterminable clauses never promote an item to Ready to pull.** Route:
- Blocker clause undeterminable → **§3 Blocked**, tagged `needs confirmation`
- Minimum-definition ambiguous → **§2 Needs story work**, tagged `needs confirmation`
- Status doesn't map → **§5 Other open work**, tagged `needs confirmation`

**Cross-cutting flags** (an item may appear here *and* in its primary group):
- **Unassigned** — no `assignee` field. Note: ready-to-pull items are often unassigned; the cross-cut exposes in-progress or blocked items nobody owns.
- **Stale** — `updated` older than the staleness threshold (default 14 days for in-progress, 21 days for blocked; team-overridable). Mark `⚠ stale`.
- **Missing owner** — no assignee AND no mentions in comments (surface as a risk flag).
- **Dependency risk** — has an outward "is blocked by" link where the blocker is also open.

### Stage 5 — Complexity (Ready-to-pull items only)

| Signal | Quick | Standard | Involved |
|---|---|---|---|
| Story-point field | ≤ 2 pts | 3–5 pts | > 5 pts |
| Description length (fallback) | ≤ 100 words | 101–200 words | > 200 words |
| AC count (secondary fallback) | ≤ 2 ACs | 3–5 ACs | > 5 ACs |

### Stage 6 — Output: header block first, then grouped sections

**Always emit the header block before any grouped sections:**

---

**Team status — `<Scope summary>` · `<date>`**

> Scope: `<JQL used>`
> Projects / boards: `<names included>`
> Sprint / filter: `<sprint name or filter applied>`
> Coverage: `<completeness statement from Stage 3>`
> Read-only: Jira was not changed by this run.

**Summary:** `<total> items — Ready to pull: <r> (Quick <q> / Std <s> / Inv <i>) · Needs story work: <n> · Blocked: <b> · In progress: <p> · Other: <o>` | Unassigned: `<u>` · Stale: `<st>` · Needs confirmation: `<c>`

---

Then emit these sections in order. If a section has no items, include its header with "None in this scope."

---

**§1 — Ready to pull** (team-ready items; or agent-ready sub-group if that lens is active)

Items satisfying the team readiness rule, grouped **Quick → Standard → Involved**.

Table columns: `Key | Summary | Priority | Complexity | Updated | Invocation repo match?`

The `Updated` column carries `⚠ stale` for items untouched past the threshold. Mark `needs confirmation` items explicitly.

Concurrency note (optional): if two or more ready items have distinct repo scopes and no stated dependency, add: "Can run concurrently: PROJ-101, PROJ-103."

---

**§2 — Needs story work**

Backlog items not ready — insufficient definition, discovery artifact, or wholly TBD.

Table columns: `Key | Summary | What's missing (coarse) | Confidence | Fix with`

"Fix with" → `jira-story-triage` for the per-item reason and a draft fix. Mark `needs confirmation` where the gap is ambiguous.

---

**§3 — Blocked**

Table columns: `Key | Summary | Blocker signal | Owner | Dependency risk?`

---

**§4 — In progress**

Table columns: `Key | Summary | Assignee | Updated | Priority`

---

**§5 — Other open work** (omit if empty)

Table columns: `Key | Summary | Status | Note`

---

**Cross-cutting flags:**

- **Unassigned items:** compact list of in-scope items with no assignee across all primary groups — `PROJ-108 (Blocked), PROJ-112 (In progress), PROJ-115 (Ready)`.
- **Stale items:** compact list of items carrying `⚠ stale` — `PROJ-101 (In progress, 18d), PROJ-112 (Blocked, 22d)`.
- **Risks and data-quality gaps:** bullet list of identified risks — missing owners on in-progress items, unresolvable blocker signals, items with `needs confirmation` labels, dependency chains with open blockers.

---

**§6 — Recommended next candidates**

For each recommendation, state *why* — not just Jira rank:

> `PROJ-201` — Quick complexity, unassigned, no known blockers, repo scope matches invocation repo. Recommended first.
> `PROJ-207` — Standard, assigned to @alice (but marked stale 18d — may need attention).

Do not merely sort by Jira rank and present that as product judgment.

---

**§7 — Likely follow-up actions**

Based on what was found:
- Items in §2 → "Use `jira-story-triage` to review and improve: PROJ-X, PROJ-Y."
- Blocked items → "PROJ-Z is blocked by PROJ-W — escalate if blocker is stale."
- Approved writes → "To apply field changes, use the `jira` skill with explicit issue/field confirmation."

---

### Stage 7 — Stand-up format (on explicit stand-up request)

When the user asks for a stand-up summary, "what changed since yesterday?", or "progress, blockers, risks, and what's ready next", emit a condensed version of the header block followed by:

**Progress:** (items moved to Done or changed since last report — from `updated` field; note if historical comparison is unavailable)
**Blocked:** (summary from §3)
**Risks:** (data-quality gaps, stale blockers, missing owners)
**Ready next:** (top 3 recommendations from §6)

If historical comparison is unavailable (Cloud does not provide change history from a prior snapshot), say so explicitly:
> "Historical comparison unavailable — Jira does not store a prior snapshot. Showing items updated in the last 24 hours as a proxy."

Remain read-only. Do not publish to Confluence without a separate explicit approved workflow.

### Stage 8 — Pick-up hand-off (read-only)

After the snapshot, offer a pick-up. Read-only routing.

**Option A — Start delivery** (if §1 has items):
> "Ready to start delivery? Suggested: **`<highest-priority Quick item>`** — `<one-line summary>`.
> [yes / pick another / skip]"

- `yes` → issuetype Bug/Defect? Route to `jira-defect-flow`. Otherwise offer `new-spec`. Surface install hint if absent.
- `pick another` → list §1 items by complexity group; user picks.
- `skip` → end gracefully.

**Option B — Improve an item in Needs story work** (if §2 has items):
> "Want to make a story-work item actionable — draft acceptance criteria, clarify the outcome? Suggested: **`<highest-priority §2 item>`**. [yes / pick another / skip]"

- `yes` → route to `jira-story-triage` by name. Surface install hint if absent.
- `pick another` / `skip` → as above.

**Explicit update escape hatch.** If the user explicitly asks to set a specific field on a specific item ("set PROJ-101's priority to High"), this skill may make a **bare pass-through** to `jira: update-issue` — show the exact payload, get a yes, then write. It never runs a multi-step collaborative rewrite; that is `jira-story-triage`'s job.

**Approved write flow** (when user asks to apply approved changes):
Show before writing:
```
Proposed write:
  Issue: PROJ-101
  Field: priority → High (was: Medium)
  Protected fields (not changing): status, assignee, sprint, labels
  Total writes: 1
```
Write only on confirmed yes. Report success, failure, or partial failure per issue. Do not auto-retry on failure; provide a safe recovery action.

## Don't

- Don't rewrite or improve a story's content — route to `jira-story-triage`.
- Don't emit grouped sections before the header block.
- Don't report "the whole backlog" without a completeness statement.
- Don't assert ready or not-ready on an unreadable signal — label **needs confirmation**.
- Don't silently truncate at 100 items; paginate to completeness.
- Don't change protected fields (status, assignee, sprint, priority, labels) without explicit user request naming each field.
- Don't conflate team readiness with agent-execution readiness — use the five-question bar only when explicitly requested.
- Don't invoke `jira-story-triage`, `jira-defect-flow`, or `new-spec` without checking if installed; surface an install hint if absent.

## Edge cases

- **No ready-to-pull items (§1 empty).** Emit §2–§5. Pick-up offers only Option B. Note: "No items ready to pull in this scope — the fastest path is to make a §2 item actionable (`jira-story-triage`)."
- **Everything is ready to pull.** Emit §1 with full complexity grouping and deliver pick-up directly; other sections show "None in this scope."
- **Blocker signal unreadable.** Note "blocker state unverified for this scope" and mark affected items `needs confirmation`.
- **Cloud pagination incomplete (cap reached).** Report `Cap reached — N items (Cloud — total unknown until complete)` and offer to re-run with a higher cap or narrowed scope.
- **Permission-limited scope.** Report "Some boards/projects were inaccessible" and name them.
- **No open sprint.** Query the open backlog (`statusCategory != Done`) instead; note the absence of an active sprint.
- **Empty backlog.** Emit all sections with "None in this scope"; confirm Jira not changed.
- **Stand-up with no historical comparison.** Say so explicitly; proxy with items updated in the last 24h.
- **Ambiguous team scope.** Ask one compact clarification; do not guess.
- `jira-story-triage` / `jira-defect-flow` / `new-spec` absent → install hint, give the item key.

## Examples

See [`references/examples.md`](references/examples.md).
