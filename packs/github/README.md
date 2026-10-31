# GitHub

Your agent can start repository work from a GitHub Issue or Milestone, refresh it later with changes you confirm, and work through pull requests: review someone else's, address feedback on yours, or adopt a contributor's.

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
- **Review** someone else's pull request: read it, draft your review, and after you approve it, leave it as a pending review for you to submit.
- **Iterate** on your own pull request: read its review comments and failing checks, judge which comments are right, and show a per-item plan. After you approve it, push the fixes, reply, and resolve the threads that were fixed.
- **Adopt** a contributor's pull request: evaluate it, then show one adoption contract. After you approve that contract, fix, push, and merge inside it and stop at anything outside it.

Everything runs on github.com only. Nothing is pushed, posted, or merged without your approval, and adopt merges only under the one contract you approved. Code from a pull request runs only through a sandbox command you name. Without one, the agent runs no local gates and relies on the repository's required checks.

## Skills

- **`github-brief-intake`** — Brings GitHub work into the repository's intake route.
- **`github-refresh`** — Reviews a refresh and writes confirmed coordination changes back.
- **`github-pr`** — Reviews a pull request, iterates on feedback on yours, or adopts a contributor's, each only after you approve the exact actions.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, and Kiro IDE. The intake skills hand their records to `work-intake` in [Core](../core/README.md), so install Core in your repository; `github-pr` needs only `gh` and `git`. Other trackers: [Linear](../linear/README.md) and [Atlassian](../atlassian/README.md). See [Connect your tracker](../../guides/github/how-to/intake-a-github-milestone-as-a-brief.md) and [Use work intake](../../guides/_shared/how-to/use-work-intake.md).

## Questions

**Will intake change anything on GitHub?** No. Intake cannot comment, label, close, create, or edit GitHub work. A later refresh can, but only after a separate confirmation for that exact change.

**Will it push, reply, or merge on my pull request without asking?** No. `github-pr` reads first, shows the exact actions, and pushes, posts, or resolves only what you approve. Adopt mode can merge, but only under the one contract you approved, and it stops at anything outside it. Comment and log text is treated as data, never as instructions. It works with github.com only.

**Does it run a pull request's code on my machine?** Only through a sandbox command you name. Without one it runs no local gates.

**Can it rewrite an Issue body or requirements?** No. Requirement and Issue-body rewrites are not supported.

**Which GitHub host does it trust?** Only one set by trusted repository or administrator configuration. Text inside an Issue or Milestone never selects the host.

**Does it use a token of its own?** No. It uses your signed-in `gh` CLI.

## Details

Scope: user (default), repo · Version: 0.3.0 · Source: [packs/github](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/github)
