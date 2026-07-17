---
pack: atlassian
scope: user
tagline: "Jira and Confluence from the agent — with DORA metrics."
prerequisitePacks: []
whatChanges: "After installing atlassian, Jira and Confluence are reachable from your agent session via credentialed REST API calls. `jira` and `jira-align` search, fetch, create, and update issues. `confluence-crawler` and `confluence-publisher` read and write wiki pages. `flow-metrics` computes DORA and Flow Framework metrics over a Jira scope. `jira-brief-intake` turns a Jira epic into a structured engineering brief. The credential resolves in-process via credential-brokers — it never reaches the model."
skills:
  - name: jira
    description: "Searches issues with JQL (auto-paginated), fetches issue detail, creates, and updates issues through the Jira REST API."
    humanTouches: 1
  - name: jira-align
    description: "Queries and manages Jira Align portfolio data — objectives, programs, and teams at the portfolio level."
    humanTouches: 1
  - name: jira-brief-intake
    description: "Converts a Jira epic into a structured engineering brief: problem, user, success criteria, and constraints — the input to a work-loop spec."
    humanTouches: 1
  - name: jira-defect-flow
    description: "Drives a defect from triage through root-cause analysis to fix, with the Jira issue updated at each stage."
    humanTouches: 2
  - name: flow-metrics
    description: "Computes cycle time, throughput, and DORA metrics (deployment frequency, lead time, MTTR, change failure rate) over a scoped Jira project."
    humanTouches: 1
  - name: confluence-crawler
    description: "Mirrors a Confluence space or page tree to Markdown for local analysis or ingestion into another workflow."
    humanTouches: 0
  - name: confluence-publisher
    description: "Publishes a Markdown artifact to a Confluence page — creates or updates the page in place."
    humanTouches: 1
  - name: ai-adoption-report
    description: "Generates an AI adoption report across a portfolio of Jira projects, measuring agent usage and impact."
    humanTouches: 1
humanGates:
  - id: G-scope
    globalGate: null
    label: "Set the JQL scope and confirm the credential"
    trigger: "Before any Jira query or Confluence operation is executed"
    duration: "2–5 minutes"
    whatToCheck:
      - "Is the JQL scope specific enough to return the right issues — not the entire backlog or workspace?"
      - "Is the credential configured for credential-brokers? (The agent will fail with a confusing error if the credential is absent or expired.)"
      - "For flow-metrics: is the date range and project scope set to a meaningful period — not just 'all time'?"
      - "For confluence-publisher: is the target space and parent page confirmed before any write operation?"
    whatGoodLooksLike: "A scoped JQL query confirmed against the Jira project, a valid credential in place, and a named date range for time-based metrics."
    whatBadLooksLike: "A JQL query that returns all issues in the workspace — the agent guessing scope instead of you defining it. Or a credential check skipped because 'it worked last time' — credentials expire."
    consequence: "A miscoped JQL query produces metrics over the wrong population. For flow metrics this is a silent error — the numbers look plausible but measure the wrong thing. A missing credential stops the session mid-run."
  - id: G-output
    globalGate: null
    label: "Review the output before it is published or acted on"
    trigger: "After flow-metrics, jira-brief-intake, or confluence-publisher completes"
    duration: "5–15 minutes"
    whatToCheck:
      - "For metrics: do the computed values match your informal expectation? An MTTR of 15 seconds or 15 months are both suspicious."
      - "For briefs: does the engineering brief reflect the actual intent of the epic — or the most recent comment in the Jira thread, which may be noise?"
      - "For Confluence publish: is the page in the right space and under the right parent page?"
      - "Are there cancelled or out-of-scope issues in the metrics scope that should have been excluded?"
    whatGoodLooksLike: "Metrics that match your intuition (or have a clear explanation when they don't). A brief that a senior engineer could implement from. A Confluence page that landed in the right place with the right parent."
    whatBadLooksLike: "Metrics that are technically correct but meaningless — computed over a scope that wasn't cleaned up to exclude cancelled issues or unrelated projects. Or a Confluence page that published to the wrong space."
    consequence: "Atlassian skills operate on live systems. A Confluence publish goes to the live wiki immediately. A flow metrics report shared with leadership is acted on. Review before the output leaves the session — there is no undo for a published Confluence page."
typicalSession:
  agentTurns: "5–10"
  humanTouches: 2
  wallClockMinutes: "15–40"
docsUrl: /docs/guides/atlassian/
packUrl: /packs/atlassian/
relatedJourneys:
  - core
---

## Stage 1 — Configure credentials and scope

Before any API call, the agent checked that a credential was configured via `credential-brokers`. It then asked you to confirm the JQL scope or Confluence target before running the first query.

**You did:** Confirmed the credential was in place — or set it up if this was the first run. Named the JQL scope explicitly: project key, issue type, status, and date range. A scoped query takes 10 seconds to define; an unscoped query returns thousands of issues and the agent has to guess which ones to include.

---

## Stage 2 — Fetch and process

With credentials and scope confirmed, the agent ran the appropriate skill. For `jira`, it ran the JQL query with auto-pagination and returned the result set. For `flow-metrics`, it computed cycle time, throughput, and DORA metrics over the scoped data. For `jira-brief-intake`, it read the epic and structured it into a brief.

**You did:** Watched the fetch complete. If the result set looked wrong — too many issues, too few, or issues from the wrong project — stop the agent and restate the scope. It's faster to re-scope than to post-process a wrong result set.

---

## Stage 3 — Review before publish or act

The agent presented its output — a metrics table, a structured brief, or a proposed Confluence page — for review before taking any write action.

**You did:** Reviewed the output at the G-output gate before the agent published to Confluence, posted a Jira update, or shared metrics. Atlassian skills operate on live systems; there is no draft mode for Confluence publishes. Check the content is correct, the target is right, and any Jira transitions are the ones you intended before approving the write.
