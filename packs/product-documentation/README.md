# Product Documentation

Documentation for any software product — a library, CLI, HTTP API, app, service, plugin, or agent-context pack — that matches what actually ships. Ask for a README, a quickstart, release notes, or an audit, and your agent writes or checks it against the real code.

**Who it is for:** maintainers and contributors who write the docs that people who install, call, or run their product read.

**Not for:** feature specs, design decisions, UI microcopy alone, docstrings alone, or internal maintainer runbooks.

**Runs in:** the agents `agentbundle` installs into, including Claude Code, Codex, Cursor, GitHub Copilot, and Gemini CLI — see [install routes](../../guides/_shared/explanation/install-routes.md).

**Need help?** See the [guide index](../../guides/product-documentation/README.md) or [open an issue](https://github.com/eugenelim/agent-ready-repo/issues). To contribute, read [CONTRIBUTING](../../CONTRIBUTING.md). Licensed under [Apache-2.0](../../LICENSE-APACHE) or [MIT](../../LICENSE-MIT).

## Try it

Paste one of these into your agent:

```
Audit this project's docs and tell me which stages of the reader journey are missing
```

```
Write a quickstart for this CLI
```

```
Write release notes for v2.1
```

```
Fix this README so a newcomer can run something in the first minute
```

You do not need to name a mode.

## What you get back

- **An audit:** a journey gap report with one row per reader stage — discover and evaluate, install, first success, daily tasks, look up, understand, troubleshoot, upgrade, contribute — each marked covered, partial, missing, or not applicable, with the file that proves it.
- **A page:** a README, quickstart, how-to, reference, explanation, troubleshooting page, changelog, migration guide, or contributing guide, written around the reader's task.
- **A check:** a list of verified claims, unverified claims, and claims that contradict current behavior.

## What the skill reads and changes

It reads your repository first: the code, manifests, schemas, `--help` output, and existing docs. That tells it which surface you ship and which reference pages that surface needs. Audits and checks never edit. When you ask for a page, it writes one by default and reports the kind and destination it chose. It places the page where your repository already keeps docs of that kind, asks once when the location is unclear, and never edits generated output. Whether the page is right for your readers stays your decision.

## Install

```bash
agentbundle install --pack product-documentation
```

Scope options: `--scope repo` (default) or `--scope user` (available across all repos).

## Next steps

- Document your own repository step by step: [Getting started](../../guides/product-documentation/getting-started.md)
- Improve and audit a doc set: [How to author product docs](../../guides/product-documentation/how-to/author-product-docs.md)
- Document one shipped feature: [How to write a guide](../../guides/product-documentation/how-to/write-a-guide.md)
- Why each page has one job: [About the Diátaxis framework](../../guides/product-documentation/explanation/the-diataxis-framework.md)

All guides live in [guides/product-documentation/](../../guides/product-documentation/). Version, scope, and dependencies are in [`pack.toml`](pack.toml).

## Using this with a pack

When the repository you document is itself an agent-context pack, ask "Write the README for this pack." The README then leads with starter prompts in the user's language and a preview of what comes back, not a list of skill names.

## Replaces

This pack supersedes `user-guide-diataxis`. The `user-guide-diataxis@0.3.0` compatibility pack installs `product-documentation` as a dependency. If you have `user-guide-diataxis` installed, you already have this pack.
