# atlassian

Atlassian primitives plus the workflows that compose them. Three credentialed
CLIs — `jira`, `jira-align`, and `confluence-crawler` — and three workflow
skills: `flow-metrics`, `ai-adoption-report`, and `jira-defect-flow`.

## What's inside

- Credentialed CLI primitives for Jira, Jira Align, and Confluence.
- Workflow skills that turn those primitives into flow metrics, an
  AI-adoption report, and a Jira defect-flow analysis.

## Install

`atlassian` is **user-scope by default** (your Atlassian credentials are yours,
not a project's).

```
agentbundle install --pack atlassian <catalogue>
```

## Set up credentials

The Jira / Confluence CLIs need an API token. Install the `credential-brokers`
pack, then tell your agent **"set up credentials"** — the interactive
`credential-setup` skill prompts you for each key and stores it in your OS
keychain (or a `0600` dotfile on Linux). Secrets never go on the command line
and never enter the repo. See the
[`credential-brokers` README](../credential-brokers/README.md).

## Usage

Once credentials are set up, ask your agent, for example:

- "Pull this sprint's flow metrics from the PLATFORM Jira board."
- "Crawl the ENG Confluence space and summarise the onboarding pages."
- "Build the AI-adoption report for last quarter."
- "Show the defect flow for project ORD over the last 30 days."

---

→ **Go deeper:** the [`atlassian` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/atlassian/).
