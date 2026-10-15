# Atlassian

Your agent can run Jira and Confluence from a conversation: see what your team can pick up, fix weak stories, and update Jira only after you confirm.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install the credentials pack first, then this one, once for your user account:

```bash
agentbundle install --pack credential-brokers
agentbundle install --pack atlassian
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install atlassian@agent-ready-repo
```

Then say "set up credentials" and give an API token, or use [SSO sign-in](../../guides/atlassian/how-to/authenticate-jira-confluence-with-sso-cookies.md) if your company requires it.

## What your agent can do

- Show the team backlog grouped as ready to pull, needs story work, blocked, and in progress. This is read-only.
- Explain why a story is not ready and draft a better description and acceptance criteria.
- Update Jira fields after a preview of the exact changes. Protected fields stay untouched.
- Start repository work from a Jira or Jira Align item, and refresh it later.
- Publish a summary to Confluence after you approve the draft, or copy a Confluence space to Markdown.
- Report DORA and Flow metrics from Jira, and compare them before and after AI adoption.

## Skills

- **`jira-team-status`** — Shows the team backlog by readiness.
- **`jira-story-triage`** — Reviews story readiness and drafts rewrites.
- **`jira`** — Reads and updates Jira issues, with confirmation before any write.
- **`jira-defect-flow`** — Takes a Jira defect from ticket to fix, pull request, and transition.
- **`jira-epic-outcome-view`** — Shows what a project's Epics delivered beside what they were meant to change.
- **`jira-brief-intake`** — Brings Jira work into repository intake.
- **`jira-refresh`** — Reviews Jira changes and applies confirmed comments, transitions, or closures.
- **`jira-align`** — Reads and updates Jira Align records.
- **`jira-align-brief-intake`** — Brings Jira Align work into repository intake.
- **`jira-align-refresh`** — Reviews Jira Align changes. Write-back is not supported.
- **`confluence-publisher`** — Publishes Markdown to a Confluence page, after a preview.
- **`confluence-crawler`** — Mirrors a Confluence space to Markdown.
- **`flow-metrics`** — Computes DORA and Flow metrics from Jira changelogs.
- **`ai-adoption-report`** — Compares flow-metrics runs into an adoption report.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, and Kiro IDE. Install [Credential Brokers](../credential-brokers/README.md) first for your token. It hands intake to `work-intake` in [Core](../core/README.md). Other trackers: [GitHub](../github/README.md) and [Linear](../linear/README.md). Guides: [Connect your tracker](../../guides/atlassian/README.md), [Review your team backlog](../../guides/atlassian/review-your-team-backlog.md), and [Work with Jira](../../guides/atlassian/work-with-jira.md).

## Questions

**Will it change Jira without asking?** No. It starts read-only and previews the exact fields, current and proposed values, before any write.

**Does it publish to Confluence on its own?** No. You see the draft first.

**What about SSO-only instances?** SSO cookie sessions are read-only for anything but GET and HEAD requests. Use a token if you need Jira writes.

**What access do I need?** Read access to the projects you query, write access only to the issues you approve, and write access to the Confluence space you publish to.

## Details

Scope: user (default), repo · Version: 0.10.2 · Source: [packs/atlassian](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/atlassian)
