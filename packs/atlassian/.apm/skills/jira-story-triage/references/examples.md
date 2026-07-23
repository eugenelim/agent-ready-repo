# `jira-story-triage` — worked examples

## Example 1: Mixed-tier sprint audit

**Invocation:** "Triage sprint 14 for actionability in the DEVKIT project."

**Skill behaviour:**

1. Runs `jira: check` → exit 0.
2. Detects `git remote -v` → `https://gitlab.org/express-ai/dev-kit` → Invocation repo: `gitlab.org/express-ai/dev-kit`.
3. Runs: `jira: search "project = DEVKIT AND sprint = 'Sprint 14'" --fields "summary,description,issuetype,status,priority,labels,customfield_*"`
4. Receives 12 stories.

**Pre-check (Blocked stories, evaluated first):**
- DEVKIT-106: description = `!image-agent-map.png!` → **Blocked** (image-only; agent fetches raw content to confirm, then marks Blocked).
- DEVKIT-109: issuetype = "Solution Design", no ACs → **Blocked** (discovery issuetype).

**Scoring (10 remaining stories):**

| Key | Q1 | Q2 | Q3 | Q4 | Q5 | Tier | Complexity |
|---|---|---|---|---|---|---|---|
| DEVKIT-101 | ✓ | ✓ | ✓ | ✓ | ✓ (2pts) | A | Quick |
| DEVKIT-103 | ✓ | ✓ | ✓ | ✓ | ✓ (2pts) | A | Quick |
| DEVKIT-104 | ✓ | ✓ | ✓ | ✓ | ✓ (4pts) | A | Standard |
| DEVKIT-107 | ✓ | ✓ | ✓ | ✓ | ✓ (3pts) | A | Standard |
| DEVKIT-112 | ✓ | ✓ | ✓ | ✓ | ✓ (1pt) | A | Quick |
| DEVKIT-108 | ✓ | ✓ | ✓ | ✗ (pending scope decision from @owner) | ✓ | B | — |
| DEVKIT-110 | ✓ | ✗ (no repo named) | ✗ (no ACs) | ✓ | uncertain | C | — |
| DEVKIT-111 | ✗ (discovery lang: "explore options for") | ✗ | ✗ | ✗ | unknown | C | — |
| DEVKIT-113 | ✓ | ✓ | ✓ | ✓ | ✗ (22pts — multi-week) | C | — |
| DEVKIT-114 | ✓ | ✓ | uncertain (ACs present but contain "TBD") | ✓ | ✓ | C | — |

**Output:**

```
Invocation repo: gitlab.org/express-ai/dev-kit (detected)
Triage scope: project = DEVKIT AND sprint = "Sprint 14"
Stories evaluated: 12
```

| Key | Summary | Tier | Complexity | Blocking issue / gate | Q5 right-sized? |
|---|---|---|---|---|---|
| **— Quick —** | | | | | |
| DEVKIT-101 | Update DevKit agent frontmatter to claude-sonnet-5 | A | Quick | — | Yes (2pts) |
| DEVKIT-103 | Remove duplicate Jira skill from power pack | A | Quick | — | Yes (2pts) |
| DEVKIT-112 | Delete unused telemetry helper function | A | Quick | — | Yes (1pt) |
| **— Standard —** | | | | | |
| DEVKIT-104 | Add dotenv support to telemetry dashboard | A | Standard | — | Yes (4pts) |
| DEVKIT-107 | Retrofit telemetry onto renamed ce-ai-enablement-pack | A | Standard | — | Yes (3pts) |
| DEVKIT-108 | Npm scope rename for @sdlc-ai | B | — | Decision: new scope name from @owner (pending) | Yes |
| DEVKIT-110 | Update the agents | C | — | Q1: vague summary; Q2: no repo named; Q3: no ACs | Unknown |
| DEVKIT-111 | Explore options for credential management | C | — | Q1: discovery language; Q2: no repo; Q3: no ACs; Q4: open design | Unknown |
| DEVKIT-113 | Migrate all agents and skills to new CI pipeline | C | — | Q5: 22pts — too large for one PR | No |
| DEVKIT-114 | Add error handling to telemetry collector | C | — | Q3: ACs contain "TBD — decide error format" | Unknown |
| DEVKIT-106 | !image-agent-map.png! | Blocked | — | Image-only description — no text content | — |
| DEVKIT-109 | Solution Design: Auth middleware | Blocked | — | Discovery issuetype (Solution Design) | — |

```
Agent-ready: 5  (Quick: 3, Standard: 2, Involved: 0)
Gated: 1   Need shaping: 4   Blocked: 2
```

---

## Example 2: Invocation-repo-unknown scenario

**Invocation:** "Audit the PLATFORM backlog for agent-readiness" (agent is not in a git repo).

**Skill behaviour:**

1. `jira: check` → exit 0.
2. `git remote -v` → no git repo detected. Agent surfaces:
   > "Optionally supply a repo URL or name — this helps verify whether stories reference a reachable scope. Enter to skip."
3. User presses Enter (skips).
4. Proceeds with "Invocation repo: unknown".

**Output header:**
```
Invocation repo: unknown (no git repo detected; supply a repo URL to improve scope verification)
Triage scope: project = PLATFORM AND sprint in openSprints() AND statusCategory != Done
Stories evaluated: 8
```

The triage table is produced as normal. The Q2 check (repo/file scope) operates
on the story's own description rather than cross-referencing the invocation repo.
The output notes: "Q2 verification is limited — invocation repo unknown, so this
skill cannot confirm whether named repos are reachable from the agent's context."
