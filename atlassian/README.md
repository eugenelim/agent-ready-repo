# atlassian

Atlassian primitives plus the workflows that compose them. Credentialed CLIs —
`jira`, `jira-align`, and `confluence-crawler`/`-publisher` — and workflow
skills: `flow-metrics`, `ai-adoption-report`, `jira-defect-flow`,
`jira-brief-intake`, and `jira-align-brief-intake`.

## What's inside

- Credentialed CLI primitives for Jira, Jira Align, and Confluence.
- Workflow skills that turn those primitives into flow metrics, an
  AI-adoption report, a Jira defect-flow analysis, a Jira epic → product-brief
  intake, and a Jira Align Feature → product-brief intake — all feeding
  `receive-brief`.
- Team backlog skills: `jira-team-status` (a read-only team status view organized
  by Ready to pull · Needs story work · Blocked · In progress — with scope and
  completeness disclosure before grouped sections, cross-cutting flags for
  unassigned and stale work, and a pick-up hand-off) and `jira-story-triage`
  (reviews items against the agent-execution readiness bar, explains why each weak
  item is not ready — which question failed and the specific gap — surfaces
  unresolved human questions, drafts improvements, and writes back to Jira only
  after per-item approval). "Ready to pull" means the item is in scope, in an
  eligible open-work state, has no known blocker, and has enough definition for the
  team to begin — not merely `statusCategory = To Do`. Unassigned is a cross-cutting
  flag; an item can be Blocked and Unassigned simultaneously. Both skills activate
  from natural team-and-backlog language; neither needs you to name the skill.

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

- "Show me what Team Atlas can work on next. Start read-only and tell me if the result is incomplete."
- "What is blocked in PLATFORM sprint 12?"
- "Which stories are not ready for engineering in DEVKIT sprint 14?"
- "Make ATLAS-204 actionable but do not update Jira yet."
- "Pull this sprint's flow metrics from the PLATFORM Jira board."
- "Crawl the ENG Confluence space and summarise the onboarding pages."
- "Build the AI-adoption report for last quarter."
- "Show the defect flow for project ORD over the last 30 days."

---

→ **Go deeper:** the [`atlassian` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/guides/atlassian/).
