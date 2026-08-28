# Atlassian

> A user-scope pack of 11 skills that connect agents directly to Jira, Jira Align, and Confluence — authenticated, composable, and flow-metrics-aware.

## Why this pack exists

Every Jira interaction without this pack is a context-switch to a browser: copy an epic title into a prompt, paste the result back into a ticket, repeat. With it, an agent can triage a sprint backlog, turn a Jira epic into a structured product brief, compute DORA metrics over a project scope, or crawl a Confluence space and produce clean Markdown — all in a single prompt, authenticated against your organization's SSO.

## What it is

**Skills (11):** `jira` (read and mutate Jira items via REST API — JQL search, create, update, transition), `jira-align` (read and mutate Jira Align features and programs), `flow-metrics` (compute cycle time, throughput, and WIP from a Jira scope), `confluence-crawler` (crawl a Confluence space and convert pages to Markdown), `confluence-publisher` (publish Markdown or XHTML to a Confluence page), `jira-brief-intake` (turn a Jira epic into bounded intake for `author-delivery-brief create`), `jira-align-brief-intake` (turn a Jira Align feature into bounded brief intake), `jira-team-status` (read-only sprint and backlog summary for stand-up views), `jira-story-triage` (review items against a five-question readiness bar, writes back only after user approval), `jira-defect-flow` (handle a defect end-to-end: fix, open PR, comment, transition), `ai-adoption-report` (compare flow-metric snapshots to produce a pre-vs-post-AI adoption report).

No subagents. No seeds.

See the README for the complete manifest table.

## What it is not

- Not a Jira admin tool — it cannot create projects, manage schemes, or configure permissions.
- Not a project management dashboard — it produces reports and surfaces data; it does not replace your team's planning ceremonies.
- Not a sync engine — it reads and writes on demand; it does not maintain a live mirror of your Jira state.

## How it relates to other packs

No required pack dependencies. Works best alongside `credential-brokers`, which supplies the SSO-cookie mechanism these skills rely on for authentication against Atlassian cloud instances.
