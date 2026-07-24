---
pack: atlassian
scope: user
tagline: "Run Jira and Confluence from a conversation"
prerequisitePacks: []
contract:
  useItWhen: "You need to review a team's Jira backlog, improve weak stories, apply approved changes, or prepare a team summary — without starting from JQL or internal skill names."
  youProvide: "A team name or Jira project scope, and explicit approval before any issue is updated."
  youReceive: "A grouped backlog summary, story-readiness findings with proposed rewrites, a write-confirmation preview, and a stand-up or Confluence-ready summary."
  yourDecisions:
    - "Which team scope to use when more than one matches"
    - "Whether each story draft is correct before approving the write"
    - "Which issues to update and which to leave unchanged"
    - "Whether to publish the Confluence update"
whatChanges: "After installing the atlassian pack, Jira and Confluence are reachable from your agent session. You can ask for a team backlog summary, have stories reviewed against the five-question readiness bar, approve targeted updates to individual issues, and produce stand-up or Confluence output — all from a conversation. The credential resolves in-process via credential-brokers; it never reaches the model."
skills:
  - name: jira-team-status
    description: "A read-only status view of a team's Jira work, grouped by Ready to pull, In progress, Blocked, Unassigned, and Needs detail. 'Ready to pull' is a defined rule — in scope, eligible state, no unresolved blocker, and meets the five-question readiness bar — not a silent status check."
    humanTouches: 1
  - name: jira-story-triage
    description: "Reviews a Jira backlog or JQL scope for story readiness using the five-question bar. Explains exactly why each item fails, proposes a rewrite, and writes to Jira only after you approve the exact drafted payload. Read-only until an approval."
    humanTouches: 1
  - name: jira
    description: "Reads and updates Jira issues via the REST API. Used for targeted writes after story-triage approval — only the fields and issues you named."
    humanTouches: 1
  - name: confluence-publisher
    description: "Publishes a Markdown artifact to a Confluence page — creates or updates in place. Requires explicit approval before publishing."
    humanTouches: 1
  - name: jira-defect-flow
    description: "Handles a Jira defect end-to-end: pulls the ticket, hands the fix to the bug-fix skill, opens a PR, then comments and transitions the ticket."
    humanTouches: 2
  - name: jira-brief-intake
    description: "Turns a Jira epic or multi-issue selection into a structured engineering brief and hands off to receive-brief."
    humanTouches: 1
  - name: jira-align
    description: "Queries and manages Jira Align portfolio data — objectives, programs, and teams."
    humanTouches: 1
  - name: jira-align-brief-intake
    description: "Pulls a Jira Align Feature and maps it to a product brief using a configuration-guided field mapping reference, then hands off to receive-brief."
    humanTouches: 1
  - name: flow-metrics
    description: "Computes DORA and Flow Framework metrics over a Jira project or Jira Align program. Read-only."
    humanTouches: 1
  - name: confluence-crawler
    description: "Mirrors a Confluence space or page tree to Markdown for local analysis."
    humanTouches: 0
  - name: ai-adoption-report
    description: "Pairs flow-metrics JSON outputs and renders a Markdown comparison report. Three modes: baseline, cohort, and program rollup. No Jira calls — reads only local JSON files."
    humanTouches: 1
humanGates:
  - id: G-scope
    globalGate: null
    label: "Confirm team scope"
    trigger: "When the agent finds more than one matching team scope"
    duration: "1 minute"
    whatToCheck:
      - "Which scope matches your team — the Jira board, or issues where the Team field is your team name?"
      - "If you have a custom Team field with a different name, provide it explicitly so the agent doesn't guess."
    whatGoodLooksLike: "A single, confirmed scope. All subsequent reads use this scope and disclose what was searched."
    whatBadLooksLike: "An unverified scope that silently includes issues from another team's board."
    consequence: "A misscoped read produces a backlog view that includes the wrong work. Ready counts look plausible but measure the wrong team."
  - id: G-draft-review
    globalGate: null
    label: "Review story drafts before approving"
    trigger: "After the agent returns story-readiness findings and proposed rewrites"
    duration: "5–10 minutes"
    whatToCheck:
      - "Does the proposed rewrite match what the team actually intends for this story?"
      - "Are the acceptance criteria checkable — no 'TBD', no 'coordinate with', no unresolvable assumption?"
      - "For items flagged as Gated: has the blocking external dependency been named precisely? Who owns it and by when?"
      - "Is the scope right-sized for one PR, or does it need to be split?"
    whatGoodLooksLike: "Each approved draft gives an engineer a clear, located, self-contained task. No open design questions remain inside the approved scope."
    whatBadLooksLike: "Approving a draft because 'it looks fine' without checking whether the ACs are genuinely checkable by diff review."
    consequence: "A story that passes the readiness bar on paper but fails in practice delays the sprint and produces a PR that doesn't know when it is done."
  - id: G-write-confirm
    globalGate: null
    label: "Confirm the write before applying"
    trigger: "After you request an update and the agent shows the write-confirmation panel"
    duration: "2–3 minutes"
    whatToCheck:
      - "Are the exact issues listed the ones you intended to update?"
      - "Is the field being changed (description or acceptance criteria) the right one — not status, assignee, or priority?"
      - "Are the protected fields listed? The agent should name status, assignee, priority, sprint, and labels as protected."
      - "Is the number of writes correct — one per issue?"
    whatGoodLooksLike: "Three issues listed, description field only, protected fields confirmed, total writes = 3."
    whatBadLooksLike: "An issue ID you didn't name appearing in the list, or a field like status or priority appearing as a change."
    consequence: "A write to the wrong issue or field is visible to everyone on the instance. Undo requires manual revert."
  - id: G-publish
    globalGate: null
    label: "Approve before publishing to Confluence"
    trigger: "After the agent produces a Confluence-ready draft"
    duration: "5 minutes"
    whatToCheck:
      - "Is the draft going to the right Confluence space and parent page?"
      - "Does the content accurately reflect the sprint state, or does it include items from a previous review?"
      - "Is the tone appropriate for the audience (team vs. leadership)?"
    whatGoodLooksLike: "A draft that a reader unfamiliar with the sprint could understand. Target space confirmed. Content matches current Jira state."
    whatBadLooksLike: "A Confluence page published to the wrong space, or one that includes issue IDs that have since changed."
    consequence: "A published Confluence page is immediately visible to the space's readers. Incorrect data shared with leadership is acted on."
typicalSession:
  agentTurns: "6–10"
  humanTouches: 4
  wallClockMinutes: "20–40"
docsUrl: /docs/guides/atlassian/
packUrl: /packs/atlassian/
relatedJourneys:
  - core
goodOutputDescription: "A grouped backlog summary showing 12 issues across APP and API (3 ready, 3 needs work, 2 blocked, 2 in progress, 2 unassigned). Story-readiness findings for 3 weak items with proposed rewrites. A write-confirmation panel listing APP-206, APP-219, and API-104 with description as the only changed field. A stand-up summary and a Confluence draft ready to review."
---

### 1. See the work

- **You say:** "Show me the whole Acme team backlog across APP and API. Include the current sprint, open backlog, unassigned work, and blocked issues. Group everything into ready to pull, needs story work, blocked, in progress. Do not change Jira."
- **Agent does:** Checks credentials. Resolves scope — if two Acme scopes exist (board and team field), asks which to use. Reads all open issues across APP and API. Discloses scope searched, time horizon, issue count, and whether the result is complete or filtered.
- **You get:** A summary: 12 issues inspected, 3 ready to pull, 3 needs story work, 2 blocked, 2 in progress, 2 unassigned. Top 5 candidates listed with readiness state. Jira not changed.
- **You decide:** Does the ready count look right? If an item is missing or mislabelled, ask why — the agent will explain what signal it couldn't read.

---

### 2. Improve weak stories

- **You say:** "Take the items that need story work. Apply our five-question bar and show me why each fails, a proposed rewrite, any question the product owner still needs to answer, and whether the item would be ready after the change. Draft only. Do not update Jira."
- **Agent does:** Applies the five-question readiness bar to APP-206, APP-219, and API-104. For each: names the failed questions and the specific gap, proposes a rewrite, flags any unresolved human question. No Jira write.
- **You get:** Per-item findings — what is missing, why it prevents action, the proposed improvement, any unresolved question, and whether the item would pass after the draft. Jira not changed.
- **You decide:** Is each draft correct? If a draft is wrong, say so and the agent revises. When satisfied with the three drafts, move to the approval step.

---

### 3. Apply approved changes

- **You say:** "Update APP-206, APP-219, and API-104 with the approved drafts. Leave every other issue unchanged. Do not change status, assignee, priority, sprint, or labels."
- **Agent does:** Shows a write-confirmation panel listing the exact issues, the field to change (description), the protected fields (status, assignee, priority, sprint, labels), and the total number of writes (3). Waits for your confirmation.
- **You get:** After you say apply: a result showing what changed (APP-206, APP-219, API-104 descriptions updated), what remained unchanged (everything else), and links to each updated issue. Any failure reported explicitly with a retry path.
- **You decide:** Review the write-confirmation panel before saying apply. This is the point of no return — everything up to here was read-only.

---

### 4. Share the result

- **You say:** "Give me a stand-up summary for the Acme team. Include progress, blockers, risks, and what is ready next. Then prepare a concise weekly version suitable for the Acme Confluence space. Do not publish until I approve it."
- **Agent does:** Produces a stand-up block (in-progress, ready, blocked, risks) and a Confluence draft. Does not publish.
- **You get:** A stand-up summary and a Confluence draft to review. The draft shows the target page and space.
- **You decide:** Review the Confluence draft. When satisfied, say "Publish." The agent will not publish without your instruction.
