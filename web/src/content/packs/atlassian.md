---
name: Atlassian
scope: user
tagline: "Jira and Confluence from the agent — with DORA metrics."
skills:
  - jira
  - jira-align
  - jira-brief-intake
  - jira-align-brief-intake
  - jira-defect-flow
  - flow-metrics
  - confluence-crawler
  - confluence-publisher
  - ai-adoption-report
installCommand: "agentbundle install --pack atlassian --scope user"
docsUrl: /docs/guides/atlassian/
journeyUrl: /journeys/atlassian/
---

Atlassian installs credentialed CLIs for Jira, Jira Align, and Confluence — plus the workflow skills built on top. `flow-metrics` computes cycle time, throughput, and DORA metrics over a Jira project or Jira Align program. `ai-adoption-report` pairs those outputs to show how AI-tagged stories compare to the control: before/after a rollout, cohort vs control within a window, or rolled up across a program. `jira-defect-flow` handles defects end-to-end from Jira to PR. `jira-brief-intake` turns a Jira epic into a structured engineering brief. Credentials resolved via `credential-brokers` — cleartext never reaches the model.
