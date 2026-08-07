# jira-story-triage — examples

## Example 1: Draft-only triage (read-only, no Jira write)

**Prompt:** Which stories are not ready for engineering in DEVKIT sprint 14? Show me what is missing but do not update Jira.

---

```
Invocation repo: github.com/example-org/devkit-service (detected)
Review scope: project = DEVKIT AND sprint = "Sprint 14" AND statusCategory != Done
Items reviewed: 12
Jira not changed: confirmed
```

| Key | Summary | Outcome | Complexity | Why not ready (failed Q + gap) | Unresolved human questions |
|---|---|---|---|---|---|
| DEVKIT-115 | Add dotenv support to API service | Ready | Quick | — | — |
| DEVKIT-119 | Rename metric key in config | Ready | Quick | — | — |
| DEVKIT-122 | Retrofit telemetry onto renamed pack | Ready | Standard | — | — |
| DEVKIT-130 | New API scope pending from @pm | Gated | — | Q4 (external): scope decision pending from @pm | When will @pm decide? |
| DEVKIT-110 | Add dotenv support | Not ready | — | Q2: no repo or file named; Q3: no acceptance criteria | — |
| DEVKIT-112 | Update the agents | Not ready | — | Q1: vague — not a concrete change; Q2: no repo; Q3: no ACs | Which agents? What changes? |
| DEVKIT-118 | !image-solution-design.png! | Needs detail | — | Image-only description — no text to judge | Provide a text description |
| DEVKIT-125 | Explore new auth flow | Needs detail | — | Discovery issuetype without acceptance criteria | — |

*[... 4 more rows ...]*

```
Ready for agent execution: 3  (Quick: 2, Standard: 1, Involved: 0)
Gated: 1   Not ready — needs shaping: 2   Needs detail: 2   (skipped: 4 Done)
Jira not changed: confirmed
```

---

> "Want to make any of these ready? I can draft acceptance criteria, clarify the outcome, and tighten the scope — then show you the exact change before anything is written to Jira. Which item (or 'top N', or 'skip')?"

---

## Example 2: Draft → confirm → write loop

**Prompt:** Improve DEVKIT-110. Then apply the change.

---

**Step 1 — Review DEVKIT-110:**

DEVKIT-110 is "Not ready" because:
- Q2 fails: no repo or file named — a coding agent cannot locate the change without a follow-up meeting.
- Q3 fails: no acceptance criteria — nothing to verify against.

**Unresolved human questions:** None — the invocation repo (devkit-service) is a reasonable scope assumption given the sprint context.

**Step 2 — Draft:**

> Proposed for DEVKIT-110:
>
> **Summary:** Add dotenv support to devkit-service API
>
> **Description:** The devkit-service API currently requires all config to be baked into the image. Add dotenv support so local and CI environments can set config via a `.env` file without image rebuilds.
>
> **Acceptance Criteria:**
> - [ ] `dotenv` package is installed and loads `.env` at startup if present.
> - [ ] Existing environment variables take precedence over `.env` values.
> - [ ] A `.env.example` file documents all supported variables.
> - [ ] Existing config tests pass with no changes.
> - [ ] `.env` is in `.gitignore`.
>
> **Expected readiness after draft:** DEVKIT-110 would pass Q1, Q2, Q3, Q4, and Q5 — it would reach **Ready for agent execution (Quick complexity)**.

---

**Proposed write for DEVKIT-110:**
```
  Issue: DEVKIT-110
  Fields changing:
    Summary: "Add dotenv support" → "Add dotenv support to devkit-service API"
    Description: (new — see above)
    Acceptance Criteria: (new — see above)
  Protected fields (not changing): status, assignee, sprint, priority, labels
  Old summary: "Add dotenv support"
  Total writes: 1 issue, 3 fields
```

**Write this to Jira for DEVKIT-110? [yes / no / display only]**

*User: yes*

Updated. DEVKIT-110 now passes Q1, Q2, Q3, Q4, and Q5 — it is **Ready for agent execution (Quick)**.

---

## Example 3: Unresolved human questions block improvement

**Prompt:** Make PROJ-99 actionable — draft improved acceptance criteria.

---

Before I can draft an improvement for PROJ-99 ("Update the agents"), these questions need human answers:

1. **Which agents should be updated?** The current description says "the agents" without naming them.
2. **What specific changes are expected?** What will each agent do differently after this change?
3. **Is this a code change, a configuration change, or both?** This determines Q1 (self-contained code/config change vs. discovery work).

Once you answer these, I can draft acceptance criteria, clarify the scope, and name the repo so an agent or engineer can pick this up without a meeting. Jira was not changed.

---

## Example 4: Confirmed write with protected fields

**Prompt:** Update APP-206, APP-219, and API-104 with the approved drafts. Leave every other issue unchanged. Do not change status, assignee, priority, sprint, or labels.

---

**Proposed writes:**

```
APP-206 — 2 fields:
  Description: (approved draft)
  Acceptance Criteria: (approved draft)
  Protected (not changing): status, assignee, sprint, priority, labels

APP-219 — 1 field:
  Description: (approved draft)
  Protected (not changing): status, assignee, sprint, priority, labels

API-104 — 1 field:
  Acceptance Criteria: (approved draft)
  Protected (not changing): status, assignee, sprint, priority, labels

Total writes: 3 issues, 4 fields
```

**Apply these writes? [yes / no]**

*User: yes*

- APP-206: updated (description + ACs) ✓
- APP-219: updated (description) ✓
- API-104: updated (ACs) ✓

No other issues were changed.

---

## Example 5: Partial write failure

**Prompt:** Apply the approved drafts to APP-206, APP-219, and API-104.

---

Results:
- APP-206: updated successfully ✓
- APP-219: **failed** — 403 Permission denied (you may not have edit access to this issue)
- API-104: updated successfully ✓

**2 of 3 succeeded.**

Recovery action for APP-219: Ask a Jira project admin to grant you edit access, or have a project owner apply this change manually. Here is the exact payload that was not applied:

```
APP-219 — 1 field:
  Description: <exact approved draft>
```

APP-219 was not changed. No auto-retry was attempted.
