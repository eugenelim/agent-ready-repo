# linear-brief-intake — examples

## Happy path: Issue with sub-issues

**Input:** `LIN-123` — "Redesign the onboarding flow" with 3 sub-issues.

**Fetch:**
```
linear: check        → exit 0
linear: get-issue LIN-123
```

**Result (abbreviated):**
```json
{
  "identifier": "LIN-123",
  "title": "Redesign the onboarding flow",
  "description": "The current onboarding flow has a 40% drop-off at step 3...",
  "children": {
    "nodes": [
      { "identifier": "LIN-124", "title": "Replace step 3 with a progress bar" },
      { "identifier": "LIN-125", "title": "Add a skip-for-now option on optional steps" },
      { "identifier": "LIN-126", "title": "Email summary after onboarding completes" }
    ]
  },
  "project": { "id": "proj-abc", "name": "Growth Q3", "url": "https://linear.app/myorg/project/growth-q3" }
}
```

**Brief written to `docs/product/briefs/redesign-the-onboarding-flow.md`:**
```markdown
# Brief: Redesign the onboarding flow

- **Slug:** `redesign-the-onboarding-flow`
- **Received:** 2026-07-22
- **Owner:** <owner>
- **Epic:** https://linear.app/myorg/project/growth-q3

## Outcome
Redesign the onboarding flow

The current onboarding flow has a 40% drop-off at step 3...

## Success metrics

## Scope / Non-goals
**In scope:**
-
**Non-goals:**
-

## Appetite

## Rabbit holes

## Instrumentation

## User stories
- **US-1.** (LIN-124) As a new user, I want a progress bar at step 3, so that I know how far I am.
- **US-2.** (LIN-125) Add a skip-for-now option on optional steps
- **US-3.** (LIN-126) Email summary after onboarding completes

## Spec map
| Spec | Status |
| --- | --- |
```

**Next:** `receive-brief` is invoked by name to elicit gaps, decompose, and build.
`workspace.toml` gains `{ slug = "redesign-the-onboarding-flow" }` under `[brief_queue].draft`.

---

## Edge case: Issue with no children

**Input:** `LIN-200` — "Fix the export button label".

`children.nodes` is empty. This is a single feature, not a multi-feature brief.

**Skill response:**
> LIN-200 has no sub-issues — it looks like a single feature rather than a
> multi-feature brief. I recommend using `new-spec` for this. Should I treat it
> as a brief anyway?

The user must confirm before the skill proceeds.

---

## Edge case: Project with >10 issues

**Input:** Project UUID `proj-xyz` — "Platform Migration Q4" with 34 issues.

**Skill response:**
> "Platform Migration Q4" has 34 issues — too many for a single shaped brief
> (>10 stories is a backlog, not a brief). Please filter to the issues that
> belong in one brief. You can filter by:
> - **Label:** e.g., "milestone-1"
> - **Assignee:** e.g., issues assigned to @alice
> - **Explicit selection:** list the issue identifiers you want included
>
> Which filter should I apply?

The PE specifies a filter; the skill re-scopes to matching issues and proceeds.
