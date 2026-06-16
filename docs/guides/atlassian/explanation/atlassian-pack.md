# The `atlassian` pack as a system

The `atlassian` pack is a thin, uniform layer over the Atlassian REST APIs. Each skill wraps one surface — issues, portfolio, wiki — behind a CLI the agent drives with subcommands. The agent never writes raw REST calls; it picks a subcommand and relays the result.

## The four API surfaces

The pack covers three Atlassian products across four direct-API skills:

- **[`jira`](../../../../packs/atlassian/.apm/skills/jira/)** — the issue tracker. JQL search with auto-pagination, fetch and mutate issues, apply transitions, comment, attach. Handles Cloud (REST v3, ADF) and Server / Data Center (REST v2, plain text) differences automatically.
- **[`jira-align`](../../../../packs/atlassian/.apm/skills/jira-align/)** — the portfolio product. Epics, features, stories, capabilities, portfolios, programs, teams over REST API 2.0 with OData-style filters. A separate product from Jira, with separate credentials.
- **[`confluence-crawler`](../../../../packs/atlassian/.apm/skills/confluence-crawler/)** — a space's page hierarchy out to Markdown with YAML frontmatter.
- **[`confluence-publisher`](../../../../packs/atlassian/.apm/skills/confluence-publisher/)** — Markdown, storage XHTML, or plain text into a new or updated page. The crawler's opposite direction, sharing its credentials.

## The skills that build on top

Several skills compose the surfaces above instead of touching the API directly:

- **[`flow-metrics`](../../../../packs/atlassian/.apm/skills/flow-metrics/)** computes DORA / Flow Framework metrics over a Jira scope. It reads through the `jira` skill, joins `jira-align` for program and portfolio scope, and emits canonical JSON / CSV. It is read-only — it never transitions, comments, or mutates.
- **[`ai-adoption-report`](../../../../packs/atlassian/.apm/skills/ai-adoption-report/)** pairs `flow-metrics` JSON outputs and renders a Markdown comparison report. It makes no upstream calls; its only inputs are local JSON files.
- **[`jira-defect-flow`](../../../../packs/atlassian/.apm/skills/jira-defect-flow/)** handles a Jira defect end-to-end: pulls the ticket via `jira`, hands the fix to the `bug-fix` skill, opens a PR, then comments and transitions the ticket.
- **[`jira-brief-intake`](../../../../packs/atlassian/.apm/skills/jira-brief-intake/)** turns a Jira epic (or a board / JQL selection) into shippable specs: pulls the epic and its children via `jira`, maps them onto a Shape B product brief, and hands off to the `receive-brief` skill to elicit gaps, decompose, and build. Read-only against Jira; degrades gracefully when `receive-brief` is absent.

## The auth model

The four direct-API skills are credentialed. A credentialed skill holds no secret. It invokes a CLI that resolves the credential in-process through a three-tier ladder — environment variable, then OS keyring, then a `~/.agentbundle/credentials.env` dotfile — and makes the API call itself. Cleartext never reaches the model.

This is enforced, not asked for. Each CLI refuses token-shaped flags (`--token`, `--api-token`, `--bearer`, `--pat`, `--password`) and exits. The skill body never reads the dotfile or echoes the token. When a credential is missing or expired, the CLI exits with a user-action code and the agent tells you to run `credential-setup` yourself — it's interactive, and the agent does not run it for you.

`jira` and `jira-align` carry separate credentials. `confluence-crawler` and `confluence-publisher` share one `confluence` namespace — configure either and both work.

The full two-layer model, and how it differs by install route, lives in [Credentialed skills](../../credential-brokers/explanation/credentialed-skills.md).

The composed skills inherit auth by composition. `flow-metrics` reads credentials through the `jira` and `jira-align` skills it invokes by name; it never reads a secret file itself. `ai-adoption-report` needs no credentials — it only reads local files.

## How they fit together

A common arc: `flow-metrics` runs twice over a project — one pre-AI window, one current — and writes two JSON files. `ai-adoption-report` pairs them and renders the deltas. The crawler mirrors a space to Markdown, you edit, and the publisher pushes it back via the frontmatter the crawler left behind. Each skill does one job and hands its output to the next.
