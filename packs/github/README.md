# GitHub

Your agent can start repository work from a GitHub Issue or Milestone, then refresh it later with changes you confirm.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it once for your user account:

```bash
agentbundle install --pack github
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install github@agent-ready-repo
```

You also need the [`gh` CLI](https://cli.github.com), signed in for any repository that needs access.

## What your agent can do

- Read a GitHub Issue, Milestone, view, or a selection across repositories, starting read-only.
- Turn it into the right local artifact. Content decides: an Issue is not always a spec, and a Milestone is not always a brief.
- Refresh a tracked artifact and show you the field-by-field delta before anything local changes.
- Write coordination back to GitHub, such as a trace link, pull-request link, status label, comment, or closure, after you confirm that exact change.

## Skills

- **`github-brief-intake`** — Brings GitHub work into the repository's intake route.
- **`github-refresh`** — Reviews a refresh and writes confirmed coordination changes back.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, and Kiro IDE. It hands its records to `work-intake` in [Core](../core/README.md), so install Core in your repository. Other trackers: [Linear](../linear/README.md) and [Atlassian](../atlassian/README.md). See [Connect your tracker](../../guides/github/how-to/intake-a-github-milestone-as-a-brief.md) and [Use work intake](../../guides/_shared/how-to/use-work-intake.md).

## Questions

**Will intake change anything on GitHub?** No. Intake cannot comment, label, close, create, or edit GitHub work. A later refresh can, but only after a separate confirmation for that exact change.

**Can it rewrite an Issue body or requirements?** No. Requirement and Issue-body rewrites are not supported.

**Which GitHub host does it trust?** Only one set by trusted repository or administrator configuration. Text inside an Issue or Milestone never selects the host.

**Does it use a token of its own?** No. It uses your signed-in `gh` CLI.

## Details

Scope: user (default), repo · Version: 0.2.3 · Source: [packs/github](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/github)
