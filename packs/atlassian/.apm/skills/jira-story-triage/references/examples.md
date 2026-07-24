# `jira-story-triage` — worked examples

## Example 1: Reason-first readiness review

**Invocation:** "Which stories are not ready for engineering in DEVKIT sprint 14?"

**Skill behaviour:**

1. Runs `jira: check` → exit 0.
2. Detects `git remote -v` → `https://gitlab.org/express-ai/dev-kit` → Invocation repo: `gitlab.org/express-ai/dev-kit`.
3. Runs: `jira: search "project = DEVKIT AND sprint = 'Sprint 14'" --fields "summary,description,issuetype,status,priority,labels,customfield_*"`
4. Receives 12 items. Applies the pre-check, then Q1–Q5, then records a reason for every not-ready item.

**Pre-check (Needs-detail items, evaluated first):**
- DEVKIT-106: description = `!image-agent-map.png!` → **Needs detail** (image-only; agent fetches raw content to confirm).
- DEVKIT-109: issuetype = "Solution Design", no ACs → **Needs detail** (discovery issuetype).

**Output:**

```
Invocation repo: gitlab.org/express-ai/dev-kit (detected)
Review scope: project = DEVKIT AND sprint = "Sprint 14"
Items reviewed: 12
```

| Key | Summary | Outcome | Complexity | Why not ready (failed question + gap) |
|---|---|---|---|---|
| **— Ready · Quick —** | | | | |
| DEVKIT-101 | Update DevKit agent frontmatter to claude-sonnet-5 | Ready | Quick | — |
| DEVKIT-103 | Remove duplicate Jira skill from power pack | Ready | Quick | — |
| DEVKIT-112 | Delete unused telemetry helper function | Ready | Quick | — |
| **— Ready · Standard —** | | | | |
| DEVKIT-104 | Add dotenv support to telemetry dashboard | Ready | Standard | — |
| DEVKIT-107 | Retrofit telemetry onto renamed ce-ai-enablement-pack | Ready | Standard | — |
| DEVKIT-108 | Npm scope rename for @sdlc-ai | Gated | — | Q4 (external): new scope name pending from @owner |
| DEVKIT-110 | Update the agents | Not ready | — | Q1: vague, not a concrete change; Q2: no repo named; Q3: no acceptance criteria |
| DEVKIT-111 | Explore options for credential management | Not ready | — | Q1: discovery language ("explore options"); Q2: no repo; Q3: no ACs; Q4: open design question |
| DEVKIT-113 | Migrate all agents and skills to new CI pipeline | Not ready | — | Q5: 22pts — too large for one PR, decompose into per-pack stories |
| DEVKIT-114 | Add error handling to telemetry collector | Not ready | — | Q3: acceptance criteria contain "TBD — decide error format" |
| DEVKIT-106 | !image-agent-map.png! | Needs detail | — | Image-only description — no text to judge |
| DEVKIT-109 | Solution Design: Auth middleware | Needs detail | — | Discovery issuetype (Solution Design), no acceptance criteria |

```
Ready for engineering: 5  (Quick: 3, Standard: 2, Involved: 0)
Gated: 1   Not ready — needs shaping: 4   Needs detail: 2
```

The point of the table is the **Why not ready** column — a reader knows exactly what
to fix, not just that an item scored low.

---

## Example 2: Improve a weak item — draft, approve, write

**Invocation (continuing from Example 1):** "Make DEVKIT-110 actionable."

**Skill behaviour:**

1. Restates the reason DEVKIT-110 is not ready: *Q1 vague, Q2 no repo named, Q3 no acceptance criteria.*
2. Reads the current content:
   > **Summary:** Update the agents
   > **Description:** The agents need updating.
   > **Acceptance Criteria:** (none)
3. Drafts the fix field by field, addressing each failed question (Q1 concrete change, Q2 repo/file scope, Q3 checkable ACs).
4. Presents the complete drafted payload:

   > **Summary:** Update DevKit agent frontmatter model IDs to `claude-sonnet-5`
   > **Description:** In `gitlab.org/express-ai/dev-kit`, update the `model:` field in every agent under `.apm/agents/*.md` from the legacy id to `claude-sonnet-5`.
   > **Acceptance Criteria:**
   > - [ ] Every `.apm/agents/*.md` file's frontmatter `model:` reads `claude-sonnet-5`.
   > - [ ] No agent file retains a legacy model id (grep is clean).
   > - [ ] `make build-check` passes.
   >
   > **Write this to Jira for DEVKIT-110? [yes / no]"**

**User:** yes

> Running: `jira: update-issue DEVKIT-110 --field summary="Update DevKit agent frontmatter model IDs to claude-sonnet-5" --field description="In gitlab.org/express-ai/dev-kit, update the model: field ... Acceptance Criteria: ..."`
>
> Updated. DEVKIT-110 now passes Q1, Q2, and Q3 — it is ready for engineering.

The write is per-item and gated on the explicit `yes`. A batch request ("draft
acceptance criteria for the top three not-ready items") repeats this draft → confirm →
write loop once per item, confirming each write separately — never a bulk write.

---

## Example 3: Invocation-repo-unknown scenario

**Invocation:** "Show me what's missing before changing the PLATFORM backlog" (agent is not in a git repo).

**Skill behaviour:**

1. `jira: check` → exit 0.
2. `git remote -v` → no git repo detected. Agent surfaces:
   > "Optionally supply a repo URL or name — this helps verify whether items reference a reachable scope. Enter to skip."
3. User presses Enter (skips).
4. Proceeds with "Invocation repo: unknown".

**Output header:**
```
Invocation repo: unknown (no git repo detected; supply a repo URL to improve scope verification)
Review scope: project = PLATFORM AND sprint in openSprints() AND statusCategory != Done
Items reviewed: 8
```

The reason-first review is produced as normal. The Q2 check (repo/file scope) operates
on the item's own description rather than cross-referencing the invocation repo. The
output notes: "Q2 verification is limited — invocation repo unknown, so this skill
cannot confirm whether named repos are reachable from the agent's context."
