---
journey_id: atlassian
pack: atlassian
start_state: read-only
end_state: confirmed-write
scope: user
tagline: "Run Jira and Confluence from a conversation"
prerequisitePacks: []
contract:
  useItWhen: "You want to see what the team can work on, improve stories that are not actionable, apply approved Jira updates, or share a team summary — without writing JQL or selecting skills manually."
  youProvide: "Your team name, project keys, or a description of the scope you want reviewed. For writes: explicit confirmation of the exact fields to change."
  youReceive: "A grouped, annotated backlog — ready to pull, needs story work, blocked, in progress — with scope and completeness disclosed. Draft story improvements where requested. Exact write previews before any Jira change. A stand-up summary and optional Confluence draft on request."
  decisionGateIds:
    - confirm-backlog-scope
    - review-story-drafts
    - confirm-jira-writes
    - approve-confluence-publish
whatChanges: "After installing the Atlassian pack, you can ask for your team's full backlog in plain language and receive a structured, annotated result — grouped by readiness, with scope and completeness disclosed — without opening a browser or writing JQL. The pack selects the right workflow for each request: orient first (read-only), improve unclear work when needed (draft), and write only after the requested change is explicit and confirmed. You do not need to know which skill handles each stage."
skills:
  - name: jira-team-status
    description: "Read-only team backlog snapshot — grouped by readiness (ready to pull, needs story work, blocked, in progress), with scope and completeness disclosed before any grouped data. Activates from natural team-and-backlog language."
    humanTouches: 1
  - name: jira-story-triage
    description: "Reviews work items against the story-readiness bar — explains why each item is not actionable, drafts improved descriptions and acceptance criteria, surfaces unresolved human questions, and writes to Jira only after per-item approval."
    humanTouches: 1
  - name: jira
    description: "Read and write individual Jira issues — search, create, update, transition, comment. The canonical write target when story-triage or team-status route approved changes here."
    humanTouches: 1
  - name: confluence-publisher
    description: "Publish Markdown content to a Confluence page. Always shows the exact page, space, and content before writing. Publishing requires explicit confirmation."
    humanTouches: 1
  - name: jira-defect-flow
    description: "Handle a Jira defect end-to-end — pull the ticket, fix the code, open a PR, comment and transition the ticket."
    humanTouches: 2
  - name: jira-brief-intake
    description: "Turn a Jira epic and its child issues into a product brief for receive-brief."
    humanTouches: 1
  - name: jira-align
    description: "Read and write Jira Align portfolio data — epics, features, stories, programs, teams."
    humanTouches: 1
  - name: jira-align-brief-intake
    description: "Turn a Jira Align Feature into a product brief. One-way intake — never writes back to Jira Align."
    humanTouches: 1
  - name: flow-metrics
    description: "Compute DORA and Flow Framework metrics (cycle time, lead time, throughput, WIP, flow efficiency) from Jira changelogs. Read-only."
    humanTouches: 1
  - name: confluence-crawler
    description: "Crawl a Confluence space and convert pages to clean Markdown with frontmatter. Read-only."
    humanTouches: 0
  - name: ai-adoption-report
    description: "Compare two flow-metrics outputs and produce a Markdown adoption report. Read-only; does not call Jira or Confluence."
    humanTouches: 1
humanGates:
  - id: confirm-backlog-scope
    globalGate: null
    label: "Confirm the backlog scope"
    trigger: "When the agent resolves more than one plausible team scope — before returning any backlog results"
    duration: "1–2 minutes"
    whatToCheck:
      - "Does the proposed scope match the team you intended to query?"
      - "If two scopes were found (e.g. a Jira board and a Team field), which one reflects the team's actual source of truth?"
      - "Are all the projects you care about included?"
    whatGoodLooksLike: "A scope that names the correct board, project set, or Team field — confirmed in one sentence."
    whatBadLooksLike: "A scope that includes the wrong projects, misses a key sprint, or uses the Team field when the board is the right source of truth."
    consequence: "Wrong scope means wrong backlog. Catching it here is a 30-second correction; catching it after reading 184 issues means starting over."
  - id: review-story-drafts
    globalGate: null
    label: "Review the story drafts"
    trigger: "After jira-story-triage produces proposed rewrites — before any write is requested"
    duration: "5–15 minutes"
    whatToCheck:
      - "Does the proposed description state a clear outcome — what happens, for whom, and under what conditions?"
      - "Do the proposed acceptance criteria cover the edge cases the engineer would need to handle?"
      - "Are there unresolved human questions that must be answered before the story is actionable?"
      - "Does the expected readiness after the draft match your team's actual bar?"
    whatGoodLooksLike: "A draft you could hand to an engineer and have them begin work without asking a follow-up question."
    whatBadLooksLike: "A draft that rewrites prose but leaves the ambiguous scope or missing acceptance criteria untouched."
    consequence: "Approving a weak draft locks in the ambiguity. Story triage is the last cheap moment to catch a missing acceptance criterion before it reaches engineering."
  - id: confirm-jira-writes
    globalGate: "G4"
    label: "Confirm the Jira changes"
    trigger: "After the agent shows the write preview — before any Jira data is changed"
    duration: "2–5 minutes"
    whatToCheck:
      - "Are the exact issue keys correct — are you writing to the right issues?"
      - "Are the proposed field values what you approved in the draft review?"
      - "Are protected fields (status, assignee, sprint, priority, labels) excluded from the write payload?"
      - "Is the total write count what you expected?"
    whatGoodLooksLike: "A write payload that exactly matches the approved draft — no extra fields, no unexpected issues, protected fields not listed."
    whatBadLooksLike: "A payload that includes issues you did not select, or fields beyond description and acceptance criteria."
    consequence: "Jira writes are immediate and visible to the team. Confirming the wrong payload means a manual rollback."
  - id: approve-confluence-publish
    globalGate: null
    label: "Approve publishing to Confluence"
    trigger: "After the agent produces a Confluence-ready draft — before publishing to the space"
    duration: "2–5 minutes"
    whatToCheck:
      - "Is the content accurate — does it reflect the actual backlog state you reviewed?"
      - "Is the tone appropriate for the target audience (stand-up vs executive summary vs team wiki)?"
      - "Is the target Confluence space and page title correct?"
      - "Are there any details that should not be visible to the page's audience?"
    whatGoodLooksLike: "A page you would be comfortable having the team or stakeholders read immediately after publish."
    whatBadLooksLike: "Draft language, placeholder values, or internal comments that should not be visible in the published version."
    consequence: "Confluence publishing is not reversible without a separate edit. Approving the wrong content or wrong space means a manual correction."
typicalSession:
  agentTurns: "6–10"
  humanTouches: 4
  wallClockMinutes: "20–40"
docsUrl: /docs/guides/atlassian/
packUrl: /packs/atlassian/
relatedJourneys:
  - core
goodOutputDescription: "You open with a plain-language backlog request. The agent resolves team scope, discloses that it found 184 issues across APP and API, and returns five groups — 17 ready to pull, 26 needing story work, 8 blocked, 11 in progress, 122 other — with recommended next candidates and a Jira-unchanged confirmation. You ask for story improvements. The agent explains why each of the 26 items fails the readiness bar, proposes rewrites for three, and surfaces one unresolved product-owner question for APP-206. You approve two. The write preview shows exact fields; you confirm. APP-206 and API-104 update immediately. APP-219 fails with a 403; the draft is preserved with a retry path. You request a stand-up summary; the agent produces one and a Confluence draft. You approve and publish."
---

### 1. See what is available

The Atlas team wants to know what is ready to pull, what is stuck, and what needs attention — without opening Jira.

- **You provide:** "Show me the whole Atlas team backlog across APP and API. Include the sprint, open backlog, blocked work, and unassigned issues. Group into ready to pull · needs story work · blocked · in progress. Recommend five items to discuss. Do not change Jira."
- **Agent does:** resolves the Atlas team scope (board or Team field); fetches all open issues via JQL search; groups by readiness; computes unassigned and stale cross-cuts; selects five recommended candidates.
- **You decide:** confirm the resolved scope is correct before reading the grouped results. If the agent found two plausible scopes, it asks one compact question.
- **Output:** scope header (projects, sprint, time horizon, total discovered and inspected, coverage state, Jira-unchanged confirmation) · five readiness groups · recommended next candidates.
- **State:** read-only

---

### 2. Improve weak stories

Twenty-six issues need story work before engineering can begin.

- **You provide:** "Take the items that need story work. Apply the story-readiness bar. Show me why each is not actionable, a proposed rewrite, any question the product owner must answer, and whether the item would be ready after the draft. Draft only. Do not update Jira."
- **Agent does:** applies a five-question readiness bar to each item (outcome clarity, acceptance criteria, scope, dependencies, safe to begin); explains the specific gap for each failure; proposes description rewrites and acceptance criteria; surfaces unresolved human questions.
- **You decide:** review each draft and select which ones to approve. Unapproved drafts are discarded. Unresolved human questions are flagged for follow-up.
- **Output:** per-item analysis — failing question, gap, proposed description, proposed ACs, unresolved question (if any), expected readiness after draft — for all 26 items; Jira-unchanged confirmation.
- **State:** draft

---

### 3. Apply approved changes

Two drafts are approved: APP-206 and API-104. A third (APP-219) was approved but will encounter a permissions error.

- **You provide:** "Update APP-206, APP-219, and API-104 with the approved drafts. Leave every other issue unchanged. Do not change status, assignee, priority, sprint, or labels."
- **Agent does:** prepares the write payload (description and acceptance criteria for each issue); shows the exact preview; waits for explicit confirmation; writes to Jira; reports success or failure per issue; preserves failed drafts with a recovery action.
- **You decide:** review the write preview — exact issue keys, fields, current and proposed values, protected fields, and total write count — then confirm or cancel. Confirmation is required before any write.
- **Output:** write result — successful writes (APP-206, API-104 with links), failed write (APP-219 — 403, reporter-only access), preserved draft and retry path for APP-219, protected-fields confirmation.
- **State:** confirmed-write

---

### 4. Communicate the result

The session ends with a stand-up summary and an optional Confluence-ready draft.

- **You provide:** "Give me a stand-up summary for the Atlas team. Include progress, blockers, risks, and what is ready next. Then prepare a concise weekly version suitable for the Atlas Confluence space. Do not publish until I approve it."
- **Agent does:** generates a stand-up summary from the backlog data reviewed; formats a Confluence-ready draft for the target space; presents both; waits for publish approval.
- **You decide:** review the Confluence draft and approve publishing. If the content needs changes, ask the agent to revise before approving.
- **Output:** stand-up summary (read-only) · Confluence-ready draft (not published) · published page URL and ID after approval.
- **State:** publish
