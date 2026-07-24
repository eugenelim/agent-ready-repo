---
name: jira-story-triage
description: "Review Jira work items for readiness and improve weak stories using the pack's five-question bar — it explains why each item is not ready (which question failed and the specific gap), drafts the fix, and writes to Jira only after you approve the exact payload; read-only until then. Triggers on \"which stories are not ready for engineering\", \"clean up the weak items in the backlog\", \"make these tickets actionable\", \"draft acceptance criteria for the top five\", \"apply the five-question bar\", \"show me what is missing before changing Jira\", \"which tickets aren't ready to ship\", \"triage the backlog for actionability\". Do NOT use for a read-only team status snapshot or what to pick up next / blocked / unassigned / in progress / stand-up (use jira-team-status), to create an issue (use jira), to turn an epic into specs (use jira-brief-intake), or to fix a defect end-to-end (use jira-defect-flow)."
metadata:
  version: "1.1"
---

# Skill: jira-story-triage

Review a Jira backlog, sprint, or JQL-scoped set of work items for **readiness to
hand to engineering**, and **improve the weak ones**. For every item that is not
ready, the output says *why* — which question failed and the specific gap — not just
a label. When the user asks, the skill drafts the fix (acceptance criteria, a clearer
outcome, a tighter scope) and writes it back to Jira **only after the user approves
the exact drafted payload**.

Read-only until an approval. The default flow reviews and explains; the write flow is
opt-in, per-item, and always shows the payload before it touches Jira.

For the read-only *team status* view — what the team can pick up next, what is
blocked, unassigned, in progress, or a stand-up summary — use `jira-team-status`.
This skill is the one that *judges readiness and fixes weak items*.

## Cross-skill invocation — name, not path

This skill names the `jira` skill **by its `name:` field, never by path**.
Install locations vary by IDE and scope. When this skill says *"via the `jira`
skill: `search ...`"*, the agent uses its native skill-dispatch mechanism to
invoke the skill registered under that name.

## Prerequisites

Before stage 1, verify:

**`jira` is installed and authenticated — a hard dependency.**
Invoke: `jira: check`.
- Exit 0 → proceed.
- Exit 2 → the user must act. Tell them to run `credential-setup` themselves
  (interactive — do not run it for them), then stop. **Do not dispatch any
  reads into an auth failure.**

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

## Readiness outcomes — reason first

Each item lands in exactly one outcome. The **reason** (which question failed and the
specific gap) is the primary output; the outcome label is secondary.

**Pre-check (runs before scoring; on trigger → Needs detail, skip scoring):**
An item is **Needs detail** when its description is empty, image-only (`!image-…!`
Jira wiki markup), or its `issuetype` is a discovery artifact (Solution Design,
Discovery, Spike without acceptance criteria, or equivalent). There is not enough
content to judge readiness. Reason: "empty/image-only description" or "discovery
issuetype — no acceptance criteria".

**Scored outcomes (apply only after the pre-check passes):**

| Outcome | Condition | Reason surfaced |
|---|---|---|
| **Ready for engineering** | All five bar questions pass. | — (can be started immediately) |
| **Gated (external)** | Exactly one bar question fails, AND that failure is an **external gate**: a specific named decision pending from a named person, credentials not yet provisioned but provisioning is confirmed, or an external dependency available on a specific future date. Content failures (missing repo scope, missing ACs, missing right-sizing) are **never** Gated. | The gate: what must resolve and who owns it. |
| **Not ready — needs shaping** | Any other outcome: any content dimension fails (Q1, Q2, Q3 missing/wrong), Q4 fails with an open design question rather than a named external gate, or Q5 fails (too large — needs decomposition). | Each failed question + its specific gap (e.g. "Q2: no repo named; Q3: no acceptance criteria"). |

## Lifecycle

### Stage 1 — Repo grounding

Detect `git remote -v` in the working directory. If a URL is found, capture
it as the **invocation repo** — the repo the agent is running from, not
necessarily the target of every item in the backlog.

If not in a git repo (or no remote configured), offer:
> "Optionally supply a repo URL or name — this helps verify whether items
> reference a reachable scope. Enter to skip."

Proceed with "Invocation repo: unknown" if the user declines.

### Stage 2 — Intake

Accept one of:
- A JQL expression (e.g. `project = PROJ AND sprint in openSprints()`)
- A sprint/board scope (convert to JQL automatically: `project = PROJ AND sprint = "Sprint 12"`)
- A project key alone (default to open sprints: `project = PROJ AND sprint in openSprints() AND statusCategory != Done`)

For a large result set (> 100 items), paginate using the `jira` skill's
`--limit` and inform the user of the total count before reviewing.

### Stage 3 — Fetch

Via the `jira` skill's `search` subcommand:

```
jira: search "<JQL>" --fields "summary,description,issuetype,status,priority,labels,story_points,customfield_*" --limit 100
```

Fetch `customfield_*` to capture story-point fields (typically `customfield_10016`
on Cloud; varies by instance). If a specific story-point field is known, use it;
otherwise infer from the field catalog (`jira: raw GET field`) and cache for the
session.

### Stage 4 — Pre-check (runs first, short-circuits Needs-detail items)

For each item, check before scoring:
- Description is empty or contains only `!image-…!` Jira wiki markup? → **Needs detail**
- `issuetype.name` matches a discovery artifact pattern (case-insensitive:
  "solution design", "discovery", "spike" — but only when no acceptance criteria
  are present)? → **Needs detail**

Confirm suspected image-only descriptions: if the description field appears
truncated in the API response, fetch the raw content before marking Needs detail.

Needs-detail items skip all further scoring. Reason = "empty/image-only description"
or "discovery issuetype".

### Stage 5 — Score the rest

Apply each bar question using word-boundary matching (English; non-English
text or unknown issuetypes fall through to "type unknown — manual review"):

- **Q1**: `issuetype.name` is Story, Task, Bug, or Sub-task AND summary/description
  free of "define how", "explore", "assess", "design the approach", "discuss",
  "align with", "determine", "investigate", "look into", "coordinate with"
  (word-boundary match, case-insensitive).
- **Q2**: Description or labels contain a repo URL, repo name, or file path pattern
  (e.g. `gitlab.org/…`, `github.com/…`, a recognizable path like `src/` or `.py`).
- **Q3**: Description or a custom field contains text identifiable as acceptance
  criteria (checkbox list, "AC:", "Acceptance Criteria:", or numbered list of
  verifiable conditions) AND those criteria do not contain "TBD", "coordinate with",
  "decide on", or "prototype".
- **Q4**: Summary and description free of "pending decision from", "awaiting alignment",
  "TBD — blocked on", or equivalent open-approval language.
- **Q5**: Story-point field ≤ team threshold (default 5; fallback: description ≤ 200
  words AND ≤ 5 ACs) AND no "multiple repos", "cross-team", or "multi-week" language.

If a question is ambiguous (content not deterministic), mark the question as
**uncertain** and say so in the reason. Never invent a pass or fail where the content
is genuinely unclear.

### Stage 6 — Classify and name the reason

Apply the outcomes (total function):
1. If the pre-check fired → Needs detail (already done in stage 4).
2. All five Q pass → Ready for engineering.
3. Exactly one Q fails AND the failure is a named external gate → Gated (external).
   (Content failures such as missing repo scope, missing ACs, or missing
   right-sizing are always "Not ready — needs shaping" regardless of how many other
   Qs pass.)
4. Any other combination → Not ready — needs shaping.

For every item that is not "Ready for engineering", **record the reason**: the
failed question(s) and the concrete gap, phrased so a human knows exactly what to
fix (e.g. "Q2: no repo or file named; Q3: acceptance criteria contain 'TBD — decide
error format'").

### Stage 7 — Complexity (Ready-for-engineering items only)

For ready items, assign complexity using the following signal hierarchy:

| Signal | Quick | Standard | Involved |
|---|---|---|---|
| Story-point field | ≤ 2 pts | 3–5 pts | > 5 pts |
| Description length (fallback if points absent) | ≤ 100 words | 101–200 words | > 200 words |
| AC count (secondary fallback) | ≤ 2 ACs | 3–5 ACs | > 5 ACs |

Apply signals in order: story-point field (primary), then description length,
then AC count. If all signals are unavailable, mark complexity as "unknown".

### Stage 8 — Output: readiness review, reason first

Header:
```
Invocation repo: <URL> (detected)   [or: Invocation repo: unknown]
Review scope: <JQL>
Items reviewed: <total>
```

Markdown table, sorted Ready → Gated → Not ready → Needs detail. **Within the Ready
block, rows are sub-grouped by complexity (Quick first, then Standard, then
Involved).** The **Why not ready** column carries the reason and is the point of the
table:

| Key | Summary | Outcome | Complexity | Why not ready (failed question + gap) |
|---|---|---|---|---|
| PROJ-101 | Add dotenv support to dashboard | Ready | Quick | — |
| PROJ-103 | Rename metric key in config | Ready | Quick | — |
| PROJ-107 | Retrofit telemetry onto renamed pack | Ready | Standard | — |
| PROJ-112 | Npm scope rename | Gated | — | Q4 (external): new scope name pending from @owner |
| PROJ-99 | Update the agents | Not ready | — | Q1: vague, not a concrete change; Q2: no repo named; Q3: no acceptance criteria |
| PROJ-106 | !image-agent-map.png! | Needs detail | — | Image-only description — no text to judge |

Footer:
```
Ready for engineering: <n>  (Quick: <q>, Standard: <s>, Involved: <i>)
Gated: <g>   Not ready — needs shaping: <c>   Needs detail: <d>
```

### Stage 9 — Improve the weak items (opt-in, write only after approval)

After the review, offer to improve the not-ready items:

> "Want to make any of these ready? I can draft acceptance criteria, clarify the
> outcome, and tighten the scope for a story, then show you the exact change before
> anything is written to Jira. Which item (or 'top N', or 'skip')?"

For each item the user selects:
1. Read the item's current content (`Key`, `Summary`, `Description`, `ACs`) and
   restate the reason it is not ready (the failed questions).
2. Walk through each failed question with the user, drafting the fix field by field.
   The five-question bar is the acceptance criterion for the draft: address every
   failed question.
3. Present the **complete drafted payload**: `Summary`, `Description`,
   `Acceptance Criteria` (and `issuetype` if it changed).
4. Ask: **"Write this to Jira for `<KEY>`? [yes / no]"**
5. `yes` → `jira: update-issue <KEY> --field summary="..." --field description="..." ...`.
   **Never call `update-issue` before step 4 confirms.** Relay the success message and
   note which questions the item now passes.
6. `no` → offer to display or copy the drafted text for manual paste; do not write.

Batch requests ("draft acceptance criteria for the top five") iterate steps 1–6 per
item, confirming each write separately — one approval per item, never a bulk write.

## Don't

- Don't write to Jira before the user approves the exact drafted payload in stage 9
  step 4. There is no undo. The review (stages 1–8) is read-only.
- Don't write any Jira verb other than `search`, `get-issue` (image-content
  confirmation), and the approved `update-issue` in stage 9. No create, transition,
  delete, or bulk write.
- Don't reduce a not-ready item to a bare label — always name the failed question(s)
  and the specific gap.
- Don't show a team status snapshot or a pick-up hand-off — that is `jira-team-status`.
- Don't reference local repo files or the local workspace queue.
- Don't hardcode a sibling skill by path; invoke by name.
- Don't classify ambiguous content as a definitive pass or fail — mark it
  "uncertain" and surface the ambiguity in the reason.

## Edge cases

- **Story-point field absent or zero.** Fall back to description length + AC count.
  Note "points unavailable — complexity estimated from description" in the complexity
  cell.
- **Non-English backlog.** Q1/Q4 keyword matching will miss non-English signals.
  Note this limitation in the output header; proceed with review where possible.
- **Custom issuetype not in the known list.** Mark Q1 as "type unknown — manual
  review"; do not force-classify as pass or Needs detail.
- **Large sprint (> 100 items).** Paginate via the `jira` skill's `--limit`
  with multiple calls; inform the user of the total count and page count before
  beginning.
- **Improve request declined at the write step.** Display the drafted fields as plain
  text; offer to copy them. Do not retry the write.

## Examples

See [`references/examples.md`](references/examples.md).
