---
name: jira-story-triage
description: "Review Jira work items for readiness and improve weak stories — it explains why each item is not ready (which question failed and the specific gap), identifies unresolved human questions, drafts proposed rewrites and acceptance criteria, and writes to Jira only after you approve the exact payload; read-only until then. Triggers on \"which stories are not ready\", \"which stories need more detail\", \"improve these weak stories\", \"make these tickets actionable\", \"draft better acceptance criteria\", \"apply the story-readiness bar\", \"explain why these items are not ready\", \"prepare Jira story improvements without writing\". Do NOT use for a read-only team status snapshot or what to pick up next / blocked / unassigned / in progress / stand-up (use jira-team-status), to create an issue (use jira), to apply approved updates to named issues (use jira), to turn an epic into specs (use jira-brief-intake), or to fix a defect end-to-end (use jira-defect-flow)."
metadata:
  version: "2.0.0"
---

# Skill: jira-story-triage

Review a Jira backlog, sprint, or JQL-scoped set of work items for readiness, explain why each weak item is not ready, and improve them. For every item that is not ready, the output says *why* — which question failed and the specific gap — not just a label. It also identifies unresolved human questions that must be answered before the story can be improved. When the user asks, the skill drafts the fix (acceptance criteria, a clearer outcome, a tighter scope) and writes it back to Jira **only after the user approves the exact drafted payload**.

**Read-only by default.** The review and draft flow is read-only. The write flow is opt-in, per-item, and always shows the exact payload before touching Jira.

For the read-only *team status* view — what the team can pick up next, what is blocked, unassigned, in progress, or a stand-up summary — use `jira-team-status`. This skill judges readiness in depth and fixes weak items. For applying approved changes to named issues, use the `jira` skill's `update-issue` with explicit per-issue confirmation.

## Output rendering

Table — When presenting several items that share the same fields, render a Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail list. Right-align numeric columns.

## Cross-skill invocation — name, not path

This skill names the `jira` skill **by its `name:` field, never by path**.

## Prerequisites

Before stage 1, verify:

**`jira` is installed and authenticated — a hard dependency.**
Invoke: `jira: check`.
- Exit 0 → proceed.
- Exit 2 → tell the user to run `credential-setup` themselves (interactive — do not run it for them), then stop.

## The agent-execution readiness bar (the five-question bar)

This bar evaluates whether a story is ready for a **coding agent or engineer to execute without further clarification**. It is an agent-execution standard, not a general team story quality standard. A story can be ready for a team to begin work without passing all five questions.

> (Q1) it is a **self-contained code/config/doc change** — not discovery, design, or coordination work;
> (Q2) it names a **reachable repo or file scope** so the change can be located without a follow-up meeting;
> (Q3) its **acceptance criteria are checkable by diff review alone** — no "TBD", "coordinate with", "decide on", or "prototype";
> (Q4) **no human decision is needed mid-flight** — no open design question, no external approval gate that cannot be confirmed before work starts;
> (Q5) it is **right-sized for one PR** — the scope is an enumerable set of files or PRs a single person or agent can produce without decomposing into sub-stories.

Q5 exists because Jira stories are a legacy delivery-capacity allocation mechanism: a story sized for a full sprint passes Q1–Q4 but cannot be handed to a single agent or engineer without decomposition.

## Readiness outcomes — reason first

Each item lands in exactly one outcome. The **reason** (which question failed and the specific gap) is the primary output; the outcome label is secondary.

**Pre-check (runs before scoring; on trigger → Needs detail, skip scoring):**
An item is **Needs detail** when its description is empty, image-only (`!image-…!` Jira wiki markup), or its `issuetype` is a discovery artifact (Solution Design, Discovery, Spike without acceptance criteria, or equivalent). There is not enough content to judge readiness.

**Scored outcomes (apply only after the pre-check passes):**

| Outcome | Condition | Reason surfaced |
|---|---|---|
| **Ready for agent execution** | All five bar questions pass. | — (can be assigned immediately to a coding agent or engineer) |
| **Gated (external)** | Exactly one bar question fails, AND that failure is an **external gate**: a specific named decision pending from a named person, credentials not yet provisioned but provisioning is confirmed, or an external dependency available on a specific future date. Content failures (missing repo scope, missing ACs, missing right-sizing) are **never** Gated. | The gate: what must resolve and who owns it. |
| **Not ready — needs shaping** | Any other outcome: any content dimension fails (Q1, Q2, Q3 missing/wrong), Q4 fails with an open design question rather than a named external gate, or Q5 fails (too large — needs decomposition). | Each failed question + its specific gap (e.g. "Q2: no repo named; Q3: no acceptance criteria"). |

## Per-item output (the review output)

For every item, emit:

| Field | Content |
|---|---|
| **Issue** | Key and title |
| **Readiness result** | Ready / Gated / Not ready / Needs detail |
| **Missing or unclear information** | What is absent or ambiguous in the current story |
| **Why that gap matters** | Concrete impact on execution (e.g. "without a repo, an agent cannot locate the affected files") |
| **Proposed rewrite** | Improved summary and description draft (shown in the Improve stage) |
| **Proposed ACs** | Acceptance criteria draft where applicable |
| **Unresolved human questions** | Questions that must be answered by a human before this story can be improved (e.g. "Which API endpoint owns the auth flow?") |
| **Expected readiness after draft** | Which outcome the story would reach if the proposed draft is accepted |
| **Jira-not-changed confirmation** | Explicit statement that Jira was not changed |

The per-item output is shown in the table review; the Proposed rewrite, Proposed ACs, and Unresolved human questions appear in the Improve stage.

## Lifecycle

### Stage 1 — Repo grounding

Detect `git remote -v` in the working directory. If a URL is found, capture it as the **invocation repo**. If not, offer to skip.

### Stage 2 — Intake

Accept:
- A JQL expression
- A sprint/board scope (convert to JQL automatically)
- A project key alone (default to open sprints)

### Stage 3 — Fetch

Via the `jira` skill's `search` subcommand:

```
jira: search "<JQL>" --fields "summary,description,issuetype,status,priority,labels,story_points,customfield_*" --limit <large_cap>
```

Set `--limit` high enough to retrieve the complete result set; do not hardcode 100. Paginate to completeness using the same mechanics as `jira-team-status`: Cloud (cursor-based via `nextPageToken`/`isLast`); Server/DC (offset-based via `startAt`; total is in the first response). Report the total count of items reviewed in the header block before the table.

### Stage 4 — Pre-check (short-circuits Needs-detail items)

For each item:
- Description empty or image-only? → **Needs detail**
- issuetype is a discovery artifact without ACs? → **Needs detail**

Confirm suspected image-only descriptions: if the description appears truncated, fetch raw content via `jira: get-issue` before marking Needs detail.

Needs-detail items skip all scoring. Reason = "empty/image-only description" or "discovery issuetype without acceptance criteria".

### Stage 5 — Score the rest

Apply each bar question using word-boundary matching:

- **Q1**: issuetype.name is Story, Task, Bug, or Sub-task AND summary/description free of discovery/coordination language.
- **Q2**: Description or labels contain a repo URL, repo name, or file path pattern.
- **Q3**: Description or a custom field contains text identifiable as acceptance criteria AND those criteria do not contain ambiguous language ("TBD", "coordinate with", "decide on", "prototype").
- **Q4**: Summary and description free of open-approval language ("pending decision from", "awaiting alignment", "TBD — blocked on", or equivalent).
- **Q5**: Story-point field ≤ team threshold (default 5; fallback: description ≤ 200 words AND ≤ 5 ACs) AND no "multiple repos", "cross-team", or "multi-week" language.

Mark ambiguous content as **uncertain** and say so in the reason. Never invent a pass or fail on unclear content.

### Stage 6 — Classify and name the reason

Apply outcomes:
1. Pre-check fired → Needs detail.
2. All five Q pass → Ready for agent execution.
3. Exactly one Q fails AND the failure is a named external gate → Gated (external).
4. Any other combination → Not ready — needs shaping.

For every item that is not Ready, record: failed question(s) + concrete gap, phrased so a human knows exactly what to fix.

### Stage 7 — Complexity (Ready items only)

| Signal | Quick | Standard | Involved |
|---|---|---|---|
| Story-point field | ≤ 2 pts | 3–5 pts | > 5 pts |
| Description length (fallback) | ≤ 100 words | 101–200 words | > 200 words |
| AC count (secondary fallback) | ≤ 2 ACs | 3–5 ACs | > 5 ACs |

### Stage 8 — Output: review table (read-only)

Header block:
```
Invocation repo: <URL> (detected)   [or: Invocation repo: unknown]
Review scope: <JQL>
Items reviewed: <total>
Jira not changed: confirmed
```

Markdown table, sorted Ready → Gated → Not ready → Needs detail. Within the Ready block, sub-grouped by complexity (Quick first, then Standard, then Involved). The **Why not ready** column and the **Unresolved human questions** column are the point of the table:

| Key | Summary | Outcome | Complexity | Why not ready (failed Q + gap) | Unresolved human questions |
|---|---|---|---|---|---|
| PROJ-101 | Add dotenv support to dashboard | Ready | Quick | — | — |
| PROJ-107 | Retrofit telemetry onto renamed pack | Ready | Standard | — | — |
| PROJ-112 | Npm scope rename | Gated | — | Q4 (external): new scope name pending from @owner | — |
| PROJ-99 | Update the agents | Not ready | — | Q1: vague, not a concrete change; Q2: no repo named; Q3: no acceptance criteria | Which agents? What change is expected? |
| PROJ-106 | !image-agent-map.png! | Needs detail | — | Image-only description — no text to judge | Provide a text description |

Footer:
```
Ready for agent execution: <n>  (Quick: <q>, Standard: <s>, Involved: <i>)
Gated: <g>   Not ready — needs shaping: <c>   Needs detail: <d>
Jira not changed: confirmed
```

### Stage 9 — Improve the weak items (opt-in, draft then confirm)

After the review, offer to improve not-ready items:

> "Want to make any of these ready? I can draft improved content — acceptance criteria, a clearer outcome, a tighter scope — then show you the exact change before anything is written to Jira. Which item (or 'top N', or 'skip')?"

For each item selected:
1. Restate the failed questions and the specific gap.
2. Identify **unresolved human questions** that cannot be answered from the ticket alone — questions the product owner or team must answer before the story can be improved (e.g. "Which API endpoint owns the auth flow?", "Is the scope limited to one region or global?"). Surface these first; do not invent answers.
3. For questions that can be answered from existing context, draft the fix field by field.
4. Present the **complete drafted payload**: Summary, Description, Acceptance Criteria (and issuetype if it changed).
5. State the **expected readiness after draft**: "With these changes, PROJ-99 would pass Q1, Q2, and Q3 — it would reach Ready for agent execution."
6. Ask: **"Write this to Jira for `<KEY>`? [yes / no / display only]"**
7. `yes` → `jira: update-issue <KEY> --field summary="..." --field description="..." ...` — **never before step 6 confirms**.
   - Confirm before writing: exact issue, exact fields, old values (where available), proposed values, protected fields (status, assignee, sprint, priority, labels — not changed), total writes.
   - Relay success message and note which questions the item now passes.
8. `no` / `display only` → show drafted text as plain text; offer to copy. Do not write.

Batch requests iterate steps 1–8 per item — one approval per item, never a bulk write.

**Protected fields:** status, assignee, sprint, priority, and labels are never changed unless explicitly named by the user in their request.

**Write payload format (always shown before writing):**
```
Proposed write for PROJ-99:
  Summary: <new summary>
  Description: <new description>
  Acceptance Criteria: <new ACs>
  Protected fields (not changing): status, assignee, sprint, priority, labels
  Old values: Summary was "<old>", Description was "<old>"
  Total writes: 1 issue, 3 fields
```

**Partial failure:** if writing to one issue fails while others succeed, report which succeeded and which failed. Do not auto-retry destructive or ambiguous writes. Provide a safe recovery action (e.g. "Retry PROJ-99 manually via `jira: update-issue` with the same payload").

## Don't

- Don't write to Jira before the user approves the exact drafted payload in stage 9 step 6. There is no undo. The review (stages 1–8) is read-only.
- Don't write any Jira verb other than `search`, `get-issue` (image-content confirmation), and the approved `update-issue` in stage 9. No create, transition, delete, or bulk write.
- Don't reduce a not-ready item to a bare label — always name the failed question(s) and the specific gap.
- Don't show a team status snapshot or a pick-up hand-off — that is `jira-team-status`.
- Don't change protected fields (status, assignee, sprint, priority, labels) without explicit user request naming each field.
- Don't apply the agent-execution bar as if it were a universal team story quality standard — it is an execution readiness bar, not a team story quality bar.
- Don't claim an item is "not ready" merely because it lacks a repo URL or one-PR sizing — these are agent-execution criteria, not team-readiness criteria.
- Don't present the result as improving team readiness unless the proposed draft addresses the actual failing questions.
- Don't classify ambiguous content as a definitive pass or fail — mark it "uncertain" and surface the ambiguity.

## Edge cases

- **Story-point field absent or zero.** Fall back to description length + AC count. Note "points unavailable — complexity estimated from description" in the complexity cell.
- **Non-English backlog.** Q1/Q4 keyword matching will miss non-English signals. Note this limitation in the output header.
- **Custom issuetype not in the known list.** Mark Q1 as "type unknown — manual review".
- **Large sprint (> 100 items).** Paginate via the `jira` skill's `--limit` with multiple calls; count items progressively on Cloud; read total from first response on Server/DC. Report count and pages before beginning review.
- **Improve request declined at the write step.** Display the drafted fields as plain text; do not retry the write.
- **Unresolved human questions block improvement.** Surface the questions clearly before drafting. Do not invent answers to human questions.
- **Partial write failure.** Report per-issue success/failure; provide safe recovery action; do not auto-retry.

## Examples

See [`references/examples.md`](references/examples.md).
