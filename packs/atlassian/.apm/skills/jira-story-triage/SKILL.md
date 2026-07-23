---
name: jira-story-triage
description: Use this skill to audit a Jira backlog, sprint, or any JQL-scoped set of stories for agent-readiness — score each story against the five-question actionability bar and output a Tier A / B / C / Blocked table with complexity grouping. Triggers on "score the backlog", "which tickets are ready to ship", "triage sprint for actionability", "classify PROJ backlog by tier", "what's agent-ready in PROJ", "run a backlog health audit", "score these stories", "which stories in sprint 12 can we execute". Do NOT use for: showing team sprint status with a pick-up hand-off (use `jira-team-status`), creating or updating issues (use `jira`), turning an epic into specs (use `jira-brief-intake`), or fixing a defect (use `jira-defect-flow`).
metadata:
  version: "1.0"
---

# Skill: jira-story-triage

A read-only audit tool. Given a JQL scope, it fetches stories via the `jira`
skill, evaluates each against the five-question actionability bar, and produces
a Tier A / B / C / Blocked table the team can act on directly.

This skill is for one-off or periodic backlog audits. For the sprint-cadence
session entry point with a pick-up hand-off, use `jira-team-status`.

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

## The five-question actionability bar

> A story is actionable when all five are true:
> (Q1) it is a **self-contained code/config/doc change** — not discovery, design, or coordination work;
> (Q2) it names a **reachable repo or file scope** so the change can be located without a follow-up meeting;
> (Q3) its **acceptance criteria are checkable by diff review alone** — no "TBD", "coordinate with", "decide on", or "prototype";
> (Q4) **no human decision is needed mid-flight** — no open design question, no external approval gate that cannot be confirmed before work starts;
> (Q5) it is **right-sized for one PR** — the scope is an enumerable set of files or PRs a single person or agent can produce without decomposing into sub-stories.

Q5 exists because Jira stories are an old delivery-capacity allocation mechanism:
a story sized for a full sprint or cross-team effort passes Q1–Q4 but still
cannot be handed to an agent without being broken down first.

## Tier rubric — total function

**Pre-check (runs before scoring; triggers → Blocked, skip scoring):**
A story is **Blocked** when its description is empty, image-only (`!image-…!`
Jira wiki markup), or its `issuetype` is a discovery artifact (Solution Design,
Discovery, Spike without acceptance criteria, or equivalent). Blocked stories
cannot be scored meaningfully.

**Scored tiers (apply only after the pre-check passes):**

| Tier | Condition |
|---|---|
| **A — Turnkey** | All five bar questions pass. The story can be started immediately. |
| **B — Gated** | Exactly one bar question fails, AND that failure is an **external gate**: a specific named decision pending from a named person, credentials not yet provisioned but provisioning is confirmed, or an external dependency available on a specific future date. Content failures (missing repo scope, missing ACs, missing right-sizing) are **never** Tier B regardless of how many other questions pass. |
| **C — Needs shaping** | Any other outcome: any content dimension fails (Q1, Q2, Q3 missing/wrong), Q4 fails with an open design question rather than a named external gate, or Q5 fails (story is too large and needs decomposition). |

## Lifecycle

### Stage 1 — Repo grounding

Detect `git remote -v` in the working directory. If a URL is found, capture
it as the **invocation repo** — the repo the agent is running from, not
necessarily the target of every story in the backlog.

If not in a git repo (or no remote configured), offer:
> "Optionally supply a repo URL or name — this helps verify whether stories
> reference a reachable scope. Enter to skip."

Proceed with "Invocation repo: unknown" if the user declines.

### Stage 2 — Intake

Accept one of:
- A JQL expression (e.g. `project = PROJ AND sprint in openSprints()`)
- A sprint/board scope (convert to JQL automatically: `project = PROJ AND sprint = "Sprint 12"`)
- A project key alone (default to open sprints: `project = PROJ AND sprint in openSprints() AND statusCategory != Done`)

For a large result set (> 100 stories), paginate using the `jira` skill's
`--limit` and inform the user of the total count before scoring.

### Stage 3 — Fetch

Via the `jira` skill's `search` subcommand:

```
jira: search "<JQL>" --fields "summary,description,issuetype,status,priority,labels,story_points,customfield_*" --limit 100
```

Fetch `customfield_*` to capture story-point fields (typically `customfield_10016`
on Cloud; varies by instance). If a specific story-point field is known, use it;
otherwise infer from the field catalog (`jira: raw GET field`) and cache for the
session.

### Stage 4 — Pre-check (runs first, short-circuits Blocked stories)

For each story, check before scoring:
- Description is empty or contains only `!image-…!` Jira wiki markup? → **Blocked**
- `issuetype.name` matches a discovery artifact pattern (case-insensitive:
  "solution design", "discovery", "spike" — but only when no acceptance criteria
  are present)? → **Blocked**

Confirm suspected image-only descriptions: if the description field appears
truncated in the API response, fetch the raw content before marking Blocked.

Blocked stories skip all further scoring. Mark tier = "Blocked" and reason =
"empty/image-only description" or "discovery issuetype".

### Stage 5 — Score non-Blocked stories

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
"uncertain" and note it in the "Blocking issue" column. Never invent a pass
or fail where the content is genuinely unclear.

### Stage 6 — Classify

Apply the tier rubric (total function):
1. If the pre-check fired → Blocked (already done in stage 4).
2. All five Q pass → Tier A.
3. Exactly one Q fails AND the failure is a named external gate → Tier B.
   (Content failures such as missing repo scope, missing ACs, or missing
   right-sizing are always Tier C regardless of how many other Qs pass.)
4. Any other combination → Tier C.

### Stage 7 — Complexity scoring (Tier A stories only)

For Tier A stories, assign complexity using the following signal hierarchy:

| Signal | Quick | Standard | Involved |
|---|---|---|---|
| Story-point field | ≤ 2 pts | 3–5 pts | > 5 pts |
| Description length (fallback if points absent) | ≤ 100 words | 101–200 words | > 200 words |
| AC count (secondary fallback) | ≤ 2 ACs | 3–5 ACs | > 5 ACs |

Apply signals in order: story-point field (primary), then description length,
then AC count. If all signals are unavailable, mark complexity as "unknown".

### Stage 8 — Output

Header:
```
Invocation repo: <URL> (detected)   [or: Invocation repo: unknown]
Triage scope: <JQL>
Stories evaluated: <total>
```

Markdown table, sorted A → B → C → Blocked. **Within the Tier A block, rows
are sub-grouped by complexity with a sub-header per band (Quick first, then
Standard, then Involved):**

| Key | Summary | Tier | Complexity | Blocking issue / gate | Q5 right-sized? |
|---|---|---|---|---|---|
| PROJ-101 | Add dotenv support to dashboard | A | Quick | — | Yes |
| PROJ-103 | Rename metric key in config | A | Quick | — | Yes |
| PROJ-107 | Retrofit telemetry onto renamed pack | A | Standard | — | Yes |
| PROJ-112 | Npm scope rename | B | — | Decision: new scope name needed from @owner | Yes |
| PROJ-99 | Update the agents | C | — | Q1: vague summary; Q2: no repo named; Q3: no ACs | Unknown |
| PROJ-106 | !image-agent-map.png! | Blocked | — | Image-only description — no text content | — |

Footer:
```
Agent-ready: <n>  (Quick: <q>, Standard: <s>, Involved: <i>)
Gated: <g>   Need shaping: <c>   Blocked: <b>
```

## Don't

- Don't write any Jira verb other than `search` and `get-issue` (for the
  image-content confirmation check). This skill is read-only.
- Don't rewrite a story's content — surface what's wrong; rewriting is for
  the `jira-team-status` shaping hand-off (user-initiated, explicit consent).
- Don't reference local repo files or the local workspace queue.
- Don't hardcode a sibling skill by path; invoke by name.
- Don't classify ambiguous content as a definitive pass or fail — mark it
  "uncertain" and surface the ambiguity in the output.

## Edge cases

- **Story-point field absent or zero.** Fall back to description length + AC count.
  Note "points unavailable — complexity estimated from description" in the complexity
  cell.
- **Non-English backlog.** Q1/Q4 keyword matching will miss non-English signals.
  Note this limitation in the output header; proceed with scoring where possible.
- **Custom issuetype not in the known list.** Mark Q1 as "type unknown — manual
  review"; do not force-classify as pass or Blocked.
- **Large sprint (> 100 stories).** Paginate via the `jira` skill's `--limit`
  with multiple calls; inform the user of the total count and page count before
  beginning.

## Examples

See [`references/examples.md`](references/examples.md).
