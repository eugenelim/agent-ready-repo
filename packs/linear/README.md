# Linear

Your agent can start repository work from a Linear Issue or Project, then refresh it later with changes you confirm.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install the credentials pack first, then this one, once for your user account:

```bash
agentbundle install --pack credential-brokers
agentbundle install --pack linear
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install linear@agent-ready-repo
```

Then say "set up credentials" and type a Linear personal API key when prompted. The key never goes in a request or a repository file.

## What your agent can do

- Read a Linear Issue, sub-issues, Project, Cycle, view, or a selection across repositories, starting read-only.
- Turn it into the right local artifact. Content decides whether it becomes an intent, brief, spec, defect, or separate units. Linear types and labels are only hints.
- Read an Issue or Project directly, and check your credentials.
- Refresh a tracked artifact and show you the field-by-field delta before anything local changes.
- Write one coordination change back to Linear, such as a trace link, status update, comment, or closure, after you confirm it.

## Skills

- **`linear-brief-intake`** — Brings Linear work into the repository's intake route.
- **`linear-brief-sync`** — Catches a brief up with its linked Linear Issue, through the refresh route.
- **`linear`** — Reads Issues and Projects through the Linear API and runs confirmed write-back actions.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, and Kiro IDE. Install [Credential Brokers](../credential-brokers/README.md) first for your key. It hands its records to `work-intake` in [Core](../core/README.md). Other trackers: [GitHub](../github/README.md) and [Atlassian](../atlassian/README.md). See [Connect your tracker](../../guides/linear/how-to/linear-brief-intake-and-sync.md) and [Use work intake](../../guides/_shared/how-to/use-work-intake.md).

## Questions

**Will intake change anything in Linear?** No. Intake never writes to Linear.

**What if the artifact is being built?** Requirement refresh is unavailable while the artifact is executing.

**Does it retry a failed write?** No. A remote change is never retried automatically, and each one needs a fresh confirmation.

## Details

Scope: user (default), repo · Version: 0.3.3 · Source: [packs/linear](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/linear)
