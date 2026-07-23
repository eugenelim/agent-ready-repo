---
name: jira-team-status
description: Use this skill to get your team's Jira sprint or backlog scored for agent-readiness and to pick up a story to deliver or shape. Shows a scored snapshot grouped by complexity, then offers a pick-up hand-off. Triggers on "show team backlog", "team sprint status", "what can we ship this sprint", "plan the sprint backlog", "which stories are agent-ready for the team", "team backlog health check", "score our sprint and pick one up", "what should we start this sprint". Do NOT use for: local workspace queue or session orientation (use the `workspace-status` skill), a bulk backlog audit without hand-off (use `jira-story-triage`), creating or updating issues without the shaping flow (use `jira`), or fixing a specific defect (use `jira-defect-flow`).
metadata:
  version: "1.0"
---

# Skill: jira-team-status

A session-entry-point tool for sprint planning and daily team coordination.
Modelled on the `workspace-status` session-entry-point pattern: it displays
a scored Jira snapshot, then offers a pick-up hand-off so a team member can
immediately start delivery on a ready story or shape a blocked one.

**Read path:** reads from Jira via the `jira` skill (read-only for the snapshot).
**Write path:** with explicit user consent in the shaping hand-off, calls
`update-issue` once on the story the user chose to rewrite. The write is always
confirmed before it executes.

This skill complements `jira-story-triage` (which is a bulk audit tool without
hand-off). Use `jira-team-status` at sprint-cadence for the "what's our status
and what should I pick up?" moment.

## Cross-skill invocation — name, not path

Sibling and host skills are named **by their `name:` field, never by path**.
When this skill says *"route to `jira-defect-flow`"*, the agent dispatches the
skill registered under that name. If the skill is absent, the agent surfaces an
install hint rather than stopping.

## Prerequisites

**`jira` is installed and authenticated — a hard dependency.**
Invoke: `jira: check`.
- Exit 0 → proceed.
- Exit 2 → tell the user to run `credential-setup` themselves and stop.

## The five-question actionability bar

> A story is actionable when all five are true:
> (Q1) it is a **self-contained code/config/doc change** — not discovery, design, or coordination work;
> (Q2) it names a **reachable repo or file scope** so the change can be located without a follow-up meeting;
> (Q3) its **acceptance criteria are checkable by diff review alone** — no "TBD", "coordinate with", "decide on", or "prototype";
> (Q4) **no human decision is needed mid-flight** — no open design question, no external approval gate that cannot be confirmed before work starts;
> (Q5) it is **right-sized for one PR** — the scope is an enumerable set of files or PRs a single person or agent can produce without decomposing into sub-stories.

Q5 exists because Jira stories are an old delivery-capacity allocation mechanism:
a story sized for a full sprint passes Q1–Q4 but cannot be handed to a single
agent or engineer without decomposition.

## Tier rubric — total function

**Pre-check (runs before scoring; triggers → Blocked, skip scoring):**
A story is **Blocked** when its description is empty, image-only (`!image-…!` Jira wiki markup), or its `issuetype` is a discovery artifact (Solution Design, Discovery, Spike without acceptance criteria, or equivalent). Blocked stories cannot be scored meaningfully because the minimum content for evaluation is absent.

**Scored tiers (apply only after the pre-check passes):**

| Tier | Condition |
|---|---|
| **A — Turnkey** | All five bar questions pass. The story can be started immediately. |
| **B — Gated** | Exactly one bar question fails, AND that failure is an **external gate**: a specific named decision pending from a named person, credentials not yet provisioned but provisioning is confirmed, or an external dependency available on a specific future date. Content failures (missing repo scope, missing ACs, missing right-sizing) are **never** Tier B regardless of how many other questions pass. |
| **C — Needs shaping** | Any other outcome: any content dimension fails (Q1, Q2, Q3 missing/wrong), or Q4 fails with an open design question rather than a named external gate, or Q5 fails (story is too large and needs decomposition). |

## Lifecycle

### Stage 1 — Repo grounding

Detect `git remote -v` in the working directory. If a URL is found, label it
**Invocation repo: `<URL>`** — the repo the agent is running from.

If not in a git repo, offer:
> "Optionally supply a repo URL or name — this improves story scope verification.
> Enter to skip."

Proceed with "Invocation repo: unknown" if the user declines.

### Stage 2 — Intake

Accept:
- A Jira project key + optional sprint (default: `sprint in openSprints()`)
- An optional team name or JQL filter for scope narrowing

Fetch open/in-progress/backlog issues not yet Done or Closed:
```
jira: search "project = PROJ AND sprint in openSprints() AND statusCategory != Done"
      --fields "summary,description,issuetype,status,priority,labels,customfield_*"
      --limit 100
```

### Stage 3 — Pre-check and scoring

Apply the same pre-check and Q1–Q5 scoring as `jira-story-triage` (same five-question
bar, same tier rubric, same word-boundary matching, same Q5 right-sizing signals).

### Stage 4 — Complexity scoring (Tier A stories only)

| Signal | Quick | Standard | Involved |
|---|---|---|---|
| Story-point field | ≤ 2 pts | 3–5 pts | > 5 pts |
| Description length (fallback) | ≤ 100 words | 101–200 words | > 200 words |
| AC count (secondary fallback) | ≤ 2 ACs | 3–5 ACs | > 5 ACs |

### Stage 5 — Output: four sections

Emit the following sections in this order, always. If a section has no stories,
include its header with "None in this scope."

---

**§1 — Agent-ready (Tier A)** — grouped by complexity

Stories that can be handed to an agent or engineer with no meeting or follow-up.
Grouped: **Quick** first, then **Standard**, then **Involved**. Team members
self-select by available bandwidth.

Table columns: `Key | Summary | Priority | Complexity | Invocation repo match?`

"Invocation repo match?" is Yes if Q2 found the invocation repo URL or name in the
story's description, Unknown otherwise.

---

**§2 — Parallel batching candidates**

Tier A stories with mutually distinct repo scopes (no explicit dependency language
between them) that can run concurrently. Format:

> "Can run concurrently: PROJ-101, PROJ-103, PROJ-107 (distinct scopes; no stated
> dependency between them)."

If no independent pairs are found, omit §2.

---

**§3 — Gated (Tier B)**

Table columns: `Key | Summary | Gate (what must resolve first) | Owner hint`

---

**§4 — Needs shaping (Tier C + Blocked)**

Table columns: `Key | Summary | Tier | Specific gap (which Q failed or why Blocked)`

Footer: "These <n> stories need shaping before they can be executed."

---

**Summary line:**
```
Sprint snapshot: <total> total.  Agent-ready: <a> (Quick: <q>, Std: <s>, Inv: <i>).
Gated: <g>.  Need shaping: <c+b>.  Invocation repo: <URL or unknown>.
```

### Stage 6 — Pick-up hand-off

After the snapshot, always offer a pick-up. Two options simultaneously:

**Option A — Start delivery:**
If §1 has stories:
> "Ready to start delivery? Suggested: **`<highest-priority Quick story>`** — `<one-line summary>`.
> [yes / pick another / skip]"

- `yes` → issuetype is Bug/Defect? Route to `jira-defect-flow` by name (surface
  an install hint if absent). Otherwise: offer to open a `new-spec` session scoped
  to this story (surface an install hint if `new-spec` is absent).
- `pick another` → list §1 stories by complexity group; user picks.
- `skip` → end the hand-off gracefully.

**Option B — Shape a story:**
If §4 has stories:
> "Want to shape a story into something executable? Suggested: **`<highest-priority Tier C story>`**.
> [yes / pick another / skip]"

- `yes` → begin the shaping flow:
  1. Read the story's current content aloud (`Key`, `Summary`, `Description`, `ACs`).
  2. Walk through each failed bar question with the user, rewriting each field
     collaboratively. The five-question bar is the acceptance criterion for the rewrite.
  3. After all failed questions are addressed, present the **complete rewritten payload**:
     `Summary`, `Description`, `Acceptance Criteria` (and `issuetype` if changed).
  4. Ask: "Update this story in Jira with the rewritten content? [yes / no]"
  5. `yes` → call `jira: update-issue <KEY> --field summary="..." --field description="..." ...`.
     **Never call `update-issue` before step 4 confirms.** Relay the success message.
  6. `no` → offer to copy the rewritten text to clipboard or display it for manual
     paste; do not call `update-issue`.
- `pick another` / `skip` → behave as above.

If the user declines both options, end gracefully with a session note of what
they could do next session.

## Don't

- Don't conflate this skill with the session-orientation skill for local repo queues.
  This skill is Jira-only; it reads external Jira project data. Trigger phrases,
  domains, and outputs are mutually exclusive from local-queue skills.
- Don't call `update-issue` without the full rewritten payload being confirmed
  by the user in stage 6 step 4. There is no undo.
- Don't read or write any local project state; this skill is Jira-only.
- Don't invoke `jira-defect-flow` or `new-spec` without checking whether they are
  installed (by-name dispatch probe); surface an install hint if absent.
- Don't rewrite a story's content without the user explicitly choosing the shaping
  option. Read-only outside the shaping hand-off.
- Don't hardcode a sibling skill by path; invoke by name.

## Edge cases

- **No Tier A stories (§1 empty).** Still emit §2 (omit if no pairs), §3, §4.
  Pick-up offers only Option B (shape a story). Note: "No agent-ready stories in
  this scope — shaping §4 stories is the fastest path to Tier A."
- **All stories are Tier A.** Emit §1 with full complexity grouping, then offer
  the delivery pick-up directly. §3 and §4 show "None in this scope."
- **Shaping hand-off with `update-issue` rejected.** Display the rewritten fields
  as plain text; offer to copy them. Do not retry the write.
- **`jira-defect-flow` or `new-spec` absent.** Route to the missing skill by name;
  harness reports it as absent; surface: "Install the `<pack>` pack to enable
  this hand-off. In the meantime, here is the story key: `<KEY>`."

## Examples

See [`references/examples.md`](references/examples.md).
