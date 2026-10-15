# Figma

Your agent can read your Figma files from a share link: structure, frames as images, comments, and FigJam diagrams as Mermaid.

## Install

Install the credentials pack first, then this one, once for your user account:

```bash
agentbundle install --pack credential-brokers
agentbundle install --pack figma
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install figma@agent-ready-repo
```

Then create a Figma personal access token, say "set up credentials" in your agent, and type the token when prompted. Your agent never sees it.

## What your agent can do

- List the pages and top-level frames of a file.
- Render a frame to PNG, SVG, JPG, or PDF.
- Read comments and version history, and post a comment after you confirm.
- Turn a FigJam connector graph into a Mermaid diagram.
- Read design variables and dev resources, where your plan allows.

## Skills

- **`figma`** — Reads and inspects Figma Cloud files through the REST API, from a normal share URL and a frame name.

## Works with

Works with Claude Code, Codex, Copilot, Kiro IDE, Cursor, and Gemini CLI. It requires [Credential Brokers](../credential-brokers/README.md) for your token. [Frontend Engineering](../frontend-engineering/README.md) can read a design handoff when you build the screens. See [Inspect a Figma file](../../guides/figma/how-to/inspect-a-figma-file.md).

## Questions

**Does it edit my design?** No. Figma's REST API reads files and posts comments, and this pack stays inside that. Every render ends with a receipt that says `No Figma changes made`.

**Who can see a comment it posts?** Every collaborator on the file. It always asks you first.

**What do I need?** A Figma account with view access to the file, a personal access token, and Python on your machine.

**Why do variables or dev resources return a 403?** Variables usually need an Enterprise organization. Dev resources need Dev Mode and the `file_dev_resources:read` scope. Reading files, frames, and comments works on any plan.

## Details

Scope: user (default), repo · Version: 0.3.4 · Source: [packs/figma](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/figma)
