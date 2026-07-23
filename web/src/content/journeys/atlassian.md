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
  - name: jira-align-brief-intake
    description: "Pulls a Jira Align Feature and its child stories/tasks/defects via the jira-align primitive, maps them to a Shape B product brief using a configuration-guided field mapping reference, and hands off to receive-brief."
    humanTouches: 1
  - name: jira-defect-flow
    description: "Drives a defect from triage through root-cause analysis to fix, with the Jira issue updated at each stage."
    humanTouches: 2
  - name: flow-metrics
    description: "Computes cycle time, lead time, throughput, WIP, defect ratio, and the rest of the Flow Framework / DORA set over a Jira project or Jira Align program. Split AI-tagged stories from the control with --cohort-jql 'labels = ai-assisted'."
    humanTouches: 1
  - name: confluence-crawler
    description: "Mirrors a Confluence space or page tree to Markdown for local analysis or ingestion into another workflow."
    humanTouches: 0
  - name: confluence-publisher
    description: "Publishes a Markdown artifact to a Confluence page — creates or updates the page in place."
    humanTouches: 1
  - name: ai-adoption-report
    description: "Pairs flow-metrics JSON outputs and renders a Markdown comparison report. Three modes: baseline (before/after two windows), cohort (AI-tagged vs control within one window), program (roll up across multiple teams or projects). No Jira calls — reads only local JSON files."
    humanTouches: 1
humanGates:
  - id: G-scope
    globalGate: null
    label: "Set the scope, confirm the credential, and agree the labeling convention"
    trigger: "Before any Jira query or Confluence operation is executed"
    duration: "5–10 minutes"
    whatToCheck:
      - "Is the credential configured via credential-brokers? The agent fails with a clear error if the credential is absent or expired — but you want to catch this before starting a long metrics run."
      - "Is the JQL scope specific enough? Project key, date range, and any label or component filters should be named explicitly. An unscoped query returns every issue in the project and the metrics will be meaningless."
      - "For cohort reports: have teams been applying the 'ai-assisted' label consistently for at least two sprints? A cohort of fewer than ten stories produces unreliable percentiles."
      - "For program rollups: do you have the Jira Align program ID and join field name, or the list of project keys to collect individually?"
      - "For Confluence publish: is the target space and parent page confirmed before any write?"
    whatGoodLooksLike: "Credential check passes. Scope is a specific project key with a named date range. Cohort label has been applied consistently for the reporting period. Confluence target confirmed if publishing."
    whatBadLooksLike: "Credential check skipped because 'it worked last time' — credentials expire. A JQL query with no project filter. A cohort report requested for a window where the team hasn't been labeling yet."
    consequence: "A miscoped query produces metrics over the wrong population — the numbers look plausible but measure the wrong thing. An expired credential stops the run mid-collection. An inconsistently labeled cohort produces a report that understates AI adoption and can't be trusted by leadership."
  - id: G-output
    globalGate: null
    label: "Review the report before it is published or shared"
    trigger: "After flow-metrics and ai-adoption-report complete, or after confluence-publisher completes"
    duration: "10–20 minutes"
    whatToCheck:
      - "Do the metric values match your informal expectation? Cycle times of 15 minutes or 15 months are both suspicious — check the state-config mapping and window bounds."
      - "Is the cohort size large enough to trust the percentiles? The report notes section will flag a small cohort."
      - "Are cancelled or out-of-scope issues included? Check the notes section — the skill records cancelled-in-window issues and permission undercounts."
      - "For program mode: are the right projects included? Check the per-scope rows to confirm no unexpected projects were picked up from the inputs directory."
      - "For Confluence publish: is the page in the right space and under the right parent page?"
    whatGoodLooksLike: "Metric deltas that match your intuition, or have a clear explanation when they don't. Cohort size is at least ten stories. Notes section is empty or contains only expected caveats. Confluence target is correct."
    whatBadLooksLike: "A large positive cycle time delta that turns out to be caused by a single long-running outlier story. A cohort so small that the p90 is the same story as the p50. A Confluence page published to the wrong space."
    consequence: "A flow metrics report shared with leadership is acted on. Delivery leads have walked into program reviews with incorrect data because the scope included cancelled work or the cohort was too small to be statistically meaningful. Review before the output leaves the session."
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

Before any API call, the agent checks that a credential is configured via `credential-brokers`. For first-time setup, it walks you through generating a Jira API token and storing it in your OS keychain — the token never appears in a file the agent can read. It then asks you to confirm the JQL scope or Confluence target before running the first query.

**You:** Confirm the credential is in place — or tell the agent to set it up. Name the scope explicitly: project key, date range, and any filters (component, label, team). For AI adoption reports, decide whether you're running a cohort split within one window (`labels = ai-assisted` vs unlabeled) or a before/after comparison across two windows. A scoped query takes 10 seconds to define; an unscoped query returns every issue in the project and the numbers will be meaningless.

---

## Stage 2 — Collect and compute

With credentials and scope confirmed, the agent runs the appropriate skill. For `flow-metrics`, it reads Jira changelogs — never the issues themselves — and computes cycle time, throughput, defect ratio, rework rate, and flow distribution for the scoped period. For a cohort split, it measures the AI-labeled and unlabeled stories against the same window and records both sides in the JSON output. For a program-level rollup, it runs one invocation per project and then passes all JSON files to `ai-adoption-report program`.

**You:** Watch the collection complete. If the agent reports an unmapped status or an empty cohort, address it before continuing — an unmapped status exits with the offending name, and an empty cohort means no stories were labeled in that window. It's faster to fix the scope or labeling than to interpret a report built on incomplete data.

---

## Stage 3 — Review the report and share

The agent presents the adoption report — a Markdown file with metric deltas, a per-scope table (program mode), and a JSON sidecar — for your review before any further action.

**You:** Check that the numbers match your informal expectations. An unexpectedly large or small cohort, a metric that looks implausible, or a scope that accidentally included cancelled work are all worth investigating before the report leaves the session. Once you're satisfied, tell the agent how to share it: publish to Confluence, paste into a Teams update, or extract the headline numbers for a slide. The JSON sidecar is available for dashboards or Power BI if you need a structured feed rather than a formatted document.
