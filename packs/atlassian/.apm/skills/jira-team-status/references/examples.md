# jira-team-status — examples

## Example 1: One project, one sprint, complete result

**Prompt:** Show the team status for PLATFORM sprint 12.

---

**Team status — PLATFORM sprint 12 · 2026-07-28**

> Scope: `project = PLATFORM AND sprint = "Sprint 12" AND statusCategory != Done`
> Projects / boards: PLATFORM
> Sprint / filter: Sprint 12
> Coverage: **Complete — 8 items**
> Read-only: Jira was not changed by this run.

**Summary:** 8 items — Ready to pull: 3 (Quick 2 / Std 1 / Inv 0) · Needs story work: 2 · Blocked: 1 · In progress: 2 · Other: 0 | Unassigned: 4 · Stale: 1 · Needs confirmation: 0

---

### §1 — Ready to pull

| Key | Summary | Priority | Complexity | Updated | Repo match? |
|---|---|---|---|---|---|
| PLATFORM-201 | Add dotenv support to the API service | Medium | Quick | 2d | Yes |
| PLATFORM-202 | Rename metric key in config | Low | Quick | 3d | Unknown |
| PLATFORM-206 | Retrofit telemetry onto renamed pack | Medium | Standard | 5d | Yes |

Can run concurrently: PLATFORM-201, PLATFORM-202 (distinct scopes; no stated dependency).

### §2 — Needs story work

| Key | Summary | What's missing | Confidence | Fix with |
|---|---|---|---|---|
| PLATFORM-204 | Update the agents | Empty description; vague title | High | jira-story-triage |
| PLATFORM-208 | Integrate with partner API | "TBD — awaiting partner decision" throughout | High | jira-story-triage |

### §3 — Blocked

| Key | Summary | Blocker signal | Owner | Dependency risk? |
|---|---|---|---|---|
| PLATFORM-215 | Fix auth token refresh | Flagged (impediment set) | @alice | No |

### §4 — In progress

| Key | Summary | Assignee | Updated | Priority |
|---|---|---|---|---|
| PLATFORM-198 | Migrate legacy config format | @bob | 1d | High |
| PLATFORM-199 | Add retry logic to export | @carol | 16d ⚠ stale | Medium |

### §5 — Other open work

None in this scope.

---

**Cross-cutting flags:**

- **Unassigned:** PLATFORM-201 (Ready), PLATFORM-202 (Ready), PLATFORM-204 (Needs story work), PLATFORM-208 (Needs story work)
- **Stale:** PLATFORM-199 (In progress, 16d — last touched 2026-07-12)
- **Risks and data-quality gaps:**
  - PLATFORM-199 is in progress but stale (16d); no update from @carol. May need attention.
  - PLATFORM-215 blocked (Flagged) with no stated blocker resolution path.

---

### §6 — Recommended next candidates

- **PLATFORM-201** — Quick complexity, unassigned, no known blockers, repo scope matches invocation repo. Recommended first pickup.
- **PLATFORM-202** — Quick complexity, unassigned, no known blockers. Second pickup.
- **PLATFORM-206** — Standard complexity, unassigned. Ready if capacity allows.

### §7 — Likely follow-up actions

- **Needs story work (2 items):** Use `jira-story-triage` to review PLATFORM-204 and PLATFORM-208 — it will explain exactly what's missing and draft a fix for approval.
- **Blocked:** PLATFORM-215 is flagged — escalate if the blocker hasn't resolved.
- **Stale:** PLATFORM-199 in progress for 16d — check in with @carol or re-assign.

---

*Pick-up hand-off:*

> Ready to start delivery? Suggested: **PLATFORM-201** — "Add dotenv support to the API service."
> [yes / pick another / skip]

---

## Example 2: More than 100 issues — full pagination

**Prompt:** Show me the full DEVKIT backlog.

---

**Team status — DEVKIT open backlog · 2026-07-28**

> Scope: `project = DEVKIT AND statusCategory != Done`
> Projects / boards: DEVKIT
> Sprint / filter: open backlog (whole-backlog scope requested)
> Coverage: **Complete — 137 items (2 pages, Cloud cursor-based pagination)**
> Read-only: Jira was not changed by this run.

**Summary:** 137 items — Ready to pull: 41 (Quick 18 / Std 19 / Inv 4) · Needs story work: 52 · Blocked: 8 · In progress: 31 · Other: 5 | Unassigned: 67 · Stale: 14

[... grouped sections follow ...]

---

## Example 3: Ambiguous team scope — compact clarification

**Prompt:** Show me the Team Atlas backlog.

---

I found two possible Atlas scopes:

1. The **Atlas Jira board** (board ID 42, 15 issues in current sprint)
2. Issues whose **Team field is Atlas** (returns 23 issues across projects APP and API)

Which should I use?

---

*After user selects option 2:*

**Team status — Team field = Atlas · 2026-07-28**

> Scope: `"Team" = "Atlas" AND statusCategory != Done`
> Projects / boards: APP, API
> Coverage: **Complete — 23 items**
> Read-only: Jira was not changed by this run.
> Note: Scope resolved using Team field (option 2).

[... grouped sections follow ...]

---

## Example 4: Explicit agent-execution readiness lens

**Prompt:** Show me agent-ready work in ATLAS sprint 12 — which items can a coding agent take?

---

**Team status — ATLAS sprint 12 · 2026-07-28 (agent-execution lens active)**

> Scope: `project = ATLAS AND sprint = "Sprint 12" AND statusCategory != Done`
> Coverage: **Complete — 10 items**
> Read-only: Jira was not changed by this run.
> Note: Agent-execution lens active (explicit request). Items filtered further by the five-question bar.

**Summary:** 10 items total. Agent-ready (all 5 Q): 3 · Team-ready (not all Q): 4 · Needs story work: 2 · Blocked: 1

### Agent-ready (explicit lens — all five Q pass)

| Key | Summary | Priority | Complexity |
|---|---|---|---|
| ATLAS-201 | Add dotenv support to API service | Medium | Quick |
| ATLAS-202 | Rename metric key in config | Low | Quick |
| ATLAS-207 | Fix auth token refresh | High | Standard |

### Ready to pull — team (does not pass all Q for agent execution)

| Key | Summary | Complexity | Barrier |
|---|---|---|---|
| ATLAS-210 | Update product briefing template | Standard | Q2: no repo named |
| ATLAS-213 | Review API partner onboarding flow | Standard | Q1: coordination work, not a code change |
| ATLAS-218 | Migrate legacy config format | Involved | Q5: multi-week scope, needs decomposition |
| ATLAS-222 | Expand reporting coverage | Standard | Q2: no repo named |

*These items are ready for the team; they need further refinement before a coding agent can take them.*

[... §2 Needs story work, §3 Blocked follow ...]

---

## Example 5: Stand-up request, no historical comparison

**Prompt:** Give me a stand-up summary for PLATFORM sprint 9. What changed since yesterday?

---

**Team status — PLATFORM sprint 9 stand-up · 2026-07-28**

> Scope: `project = PLATFORM AND sprint = "Sprint 9" AND statusCategory != Done`
> Coverage: Complete — 12 items
> Read-only: Jira was not changed by this run.

**Progress** *(historical comparison unavailable — Cloud does not store a prior snapshot. Showing items updated in the last 24 hours as a proxy.)*
- PLATFORM-198: @bob updated description (1h ago); status unchanged
- PLATFORM-206: moved from To Do → In Progress (22h ago)
- PLATFORM-199: no update (stale — 17d)

**Blocked**
- PLATFORM-215: Flagged, 3d since last update. Blocker reason not stated. Escalate?

**Risks**
- PLATFORM-199: in progress 17d, no recent update — possible stall.
- PLATFORM-204 and PLATFORM-208: still in Needs story work; `jira-story-triage` session recommended before sprint end.

**Ready next**
- PLATFORM-201 (Quick, unassigned, repo match) — recommended for immediate pickup.
- PLATFORM-202 (Quick, unassigned) — second pickup.

*Read-only confirmed. To publish this summary to Confluence, start a separate Confluence Publisher session.*
