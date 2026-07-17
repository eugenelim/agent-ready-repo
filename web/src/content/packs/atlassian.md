---
name: Atlassian
scope: user
tagline: "Jira and Confluence from the agent — with DORA metrics."
skills:
  - jira
  - jira-align
  - jira-brief-intake
  - jira-defect-flow
  - flow-metrics
  - confluence-crawler
  - confluence-publisher
  - ai-adoption-report
installCommand: "agentbundle install --pack atlassian --scope user"
docsUrl: /docs/guides/atlassian/
journeyUrl: /journeys/atlassian/
---

Atlassian installs Jira and Confluence primitives (credentialed CLI with SSO-cookie auth) plus four workflow skills: `flow-metrics` (DORA + cycle time), `ai-adoption-report` (measuring agent adoption across a portfolio), `jira-defect-flow` (triage to fix), and `jira-brief-intake` (turning Jira tickets into structured engineering briefs). Credentials resolved via `credential-brokers` — cleartext never reaches the model.
