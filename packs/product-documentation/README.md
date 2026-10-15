# Product Documentation

Your agent can write, improve, and audit the docs your users read, checked against what your code actually does.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it from inside the repository you document:

```bash
cd path/to/your-repo
agentbundle install --pack product-documentation
```

It also installs at user scope, which covers every repository:

```bash
agentbundle install --pack product-documentation --scope user
```

## What your agent can do

- Audit your docs and report which stage of the reader journey is covered, partial, or missing, with the file that proves it.
- Write a README, quickstart, how-to, reference page, troubleshooting page, release notes, migration guide, or contributing guide around the reader's task.
- Check a page's claims and list the verified, unverified, and contradicted ones.
- Fix a README so a newcomer can run something in the first minute.
- Write the README for an agent-context pack, led by starter prompts in the user's language.

## Skills

- **`author-product-docs`** — Creates, revises, retrofits, audits, or verifies user-facing docs for any software product. You do not need to name a mode.

## Works with

Works with Claude Code, Codex, Cursor, Copilot, and Gemini CLI. It replaces [User Guide (Diátaxis)](../user-guide-diataxis/README.md). See [Write the docs](../../guides/product-documentation/README.md), [Author product docs](../../guides/product-documentation/how-to/author-product-docs.md), and [Getting started](../../guides/product-documentation/getting-started.md).

## Questions

**Does it change my files during an audit?** No. Audits and checks change nothing unless you also ask for fixes.

**Where does it put a new page?** Where your repository already keeps docs of that kind. It asks once when the place is unclear, and it never edits generated output.

**Does it read my code?** Yes, first: code, manifests, schemas, `--help` output, and existing docs. That tells it what you ship and which reference pages you need.

**What is it not for?** Feature specs, design decisions, UI microcopy alone, docstrings alone, or internal runbooks.

## Details

Scope: repo (default), user · Version: 0.1.2 · Source: [packs/product-documentation](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/product-documentation)
