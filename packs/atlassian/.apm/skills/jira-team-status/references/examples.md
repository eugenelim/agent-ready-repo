# `jira-team-status` — worked examples

## Example 1: Stand-up status snapshot with pick-up hand-off

**Invocation:** "Give me a team status for stand-up — the PLATFORM team, sprint 8."

**Skill behaviour:**

1. Runs `jira: check` → exit 0.
2. Detects `git remote -v` → `https://github.com/acme/platform-core` → **Invocation repo: `github.com/acme/platform-core`**.
3. Runs:
   ```
   jira: search "project = PLATFORM AND sprint = 'Sprint 8' AND statusCategory != Done"
         --fields "summary,description,issuetype,status,statusCategory,assignee,updated,priority,labels,issuelinks,customfield_*"
         --limit 100
   ```
4. Receives 8 items. Classifies each into a primary dimension; computes cross-cutting views.

**Output:**

```
Invocation repo: github.com/acme/platform-core (detected)
Scope: project = PLATFORM AND sprint = "Sprint 8"
Coverage: all 8 items (not truncated)
```

---

### §1 — Ready to pull

Meets the ready-to-pull rule (eligible state · no blocker · passes the readiness bar).

**Quick** (≤ 2pts)

| Key | Summary | Priority | Complexity | Updated (⚠ if stale) | Invocation repo match? |
|---|---|---|---|---|---|
| PLATFORM-201 | Remove deprecated `FeatureFlags.LEGACY_AUTH` constant | High | Quick | yesterday | Yes |
| PLATFORM-202 | Update `platform-core` agent frontmatter to claude-sonnet-5 | Medium | Quick | 3 days ago | Yes |

**Standard** (3–5pts)

| Key | Summary | Priority | Complexity | Updated (⚠ if stale) | Invocation repo match? |
|---|---|---|---|---|---|
| PLATFORM-206 | Add structured logging to the credential rotation hook | High | Standard | 2 days ago | Yes |

Can run concurrently: **PLATFORM-201, PLATFORM-202, PLATFORM-206** (distinct scopes; no stated dependency).

---

### §2 — In progress

| Key | Summary | Assignee | Updated |
|---|---|---|---|
| PLATFORM-207 | Retrofit telemetry onto the renamed `ce-ai-enablement-pack` | @dev-mira | 4h ago |
| PLATFORM-208 | Migrate CI pipeline from Jenkins to GitHub Actions | @dev-omar | ⚠ 18 days ago (stale) |

---

### §3 — Blocked

| Key | Summary | Blocker (which signal) | Owner hint |
|---|---|---|---|
| PLATFORM-203 | Enable mTLS for service-to-service calls | "is blocked by" PLATFORM-190 (cert provisioning), unresolved | @infra-lead |

---

### §4 — Unassigned

| Key | Summary | Primary dimension | Status |
|---|---|---|---|
| PLATFORM-201 | Remove deprecated `FeatureFlags.LEGACY_AUTH` constant | Ready to pull | To Do |
| PLATFORM-202 | Update `platform-core` agent frontmatter to claude-sonnet-5 | Ready to pull | To Do |
| PLATFORM-206 | Add structured logging to the credential rotation hook | Ready to pull | Selected for Dev |
| PLATFORM-204 | Investigate options for distributed tracing | Needs detail | To Do |

(Ready-to-pull items are expected to be unassigned; the signal to watch is that no
*in-progress* item is orphaned here.)

---

### §5 — Needs detail (product attention)

| Key | Summary | What's missing (coarse) | Fix with |
|---|---|---|---|
| PLATFORM-204 | Investigate options for distributed tracing | Discovery-shaped; no repo/ACs | `jira-story-triage` |
| PLATFORM-205 | !arch-diagram.png! | Image-only description | `jira-story-triage` |

---

**Recently changed:** PLATFORM-207 (4h ago), PLATFORM-201 (yesterday), PLATFORM-206 (2 days ago).

```
Team status: 8 items.  Ready to pull: 3 (Quick 2 / Std 1 / Inv 0).
In progress: 2.  Blocked: 1.  Unassigned: 4.  Needs detail: 2.  Stale: 1.
Scope: project = PLATFORM AND sprint = "Sprint 8".  Coverage: all 8.  Invocation repo: github.com/acme/platform-core.
```

---

### Pick-up hand-off (read-only)

**Option A — Start delivery:**

> "Ready to start delivery? Suggested: **PLATFORM-201** — Remove deprecated `FeatureFlags.LEGACY_AUTH` constant (Quick, High priority, scope matches invocation repo).
> [yes / pick another / skip]"

**User:** yes

> "PLATFORM-201 is a Task — routing to `new-spec` to scope the delivery."
> → `new-spec` skill loads with PLATFORM-201 context.

**Option B — Improve an item that needs detail:**

> "Want to make a not-ready item actionable — draft acceptance criteria, clarify the outcome? Suggested: **PLATFORM-204** — Investigate options for distributed tracing.
> [yes / pick another / skip]"

**User:** yes

> "Routing to `jira-story-triage` for PLATFORM-204 — it will explain exactly what's
> missing and draft a fix you approve before anything is written to Jira."
> → `jira-story-triage` loads scoped to PLATFORM-204.

This skill runs no rewrite of its own — improvement lives in `jira-story-triage`.

---

## Example 2: "What is blocked / unassigned?" across the whole backlog

**Invocation:** "Show me the entire ALPHA backlog — what's blocked and what's sitting unassigned?"

**Skill behaviour:**

1. `jira: check` → exit 0.
2. Whole-backlog scope requested → drops the open-sprints default:
   ```
   jira: search "project = ALPHA AND statusCategory != Done" --fields "...,assignee,updated,issuelinks,statusCategory,..." --limit 100
   ```
3. Result exceeds `--limit` → discloses coverage.

**Output (abridged to the asked dimensions):**

```
Scope: project = ALPHA (whole backlog, statusCategory != Done)
Coverage: truncated at 100 — total 137 items (narrow scope or ask to paginate for the rest)
```

### §3 — Blocked

| Key | Summary | Blocker (which signal) | Owner hint |
|---|---|---|---|
| ALPHA-031 | Deploy new auth middleware to staging | Flagged (impediment set) | @sec-lead |
| ALPHA-044 | Wire billing webhook | "is blocked by" ALPHA-040, unresolved | — |
| ALPHA-052 | Migrate session store | needs confirmation — blocker field not in response | — |

### §4 — Unassigned

| Key | Summary | Primary dimension | Status |
|---|---|---|---|
| ALPHA-028 | Make the API faster | Needs detail | Backlog |
| ALPHA-033 | Add rate-limit headers | Ready to pull | To Do |
| ALPHA-047 | Refund flow edge cases | In progress | In Progress |

ALPHA-047 is **in progress but unassigned** — the kind of orphaned WIP §4 exists to
surface. ALPHA-052's blocker state couldn't be read, so it is **needs confirmation**,
not asserted unblocked.
