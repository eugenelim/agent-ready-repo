# User Guide (Diátaxis) — Deprecated

This pack is deprecated. Install [Product Documentation](../product-documentation/README.md) instead, which does the same job and more.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install the replacement from inside your repository:

```bash
cd path/to/your-repo
agentbundle install --pack product-documentation
```

## What your agent can do

- Keep the old `new-guide` trigger phrases working. They route to `author-product-docs`.
- Create, revise, retrofit, audit, or verify user-facing docs, through the replacement pack.

## Skills

- **`new-guide`** — A compatibility shim. It activates on the same triggers as before and routes to `author-product-docs`.

## Works with

Works with Claude Code. Version 0.3.0 installs [Product Documentation](../product-documentation/README.md) as a dependency, so if you have this pack you already have the new one. See [Write the docs](../../guides/product-documentation/README.md).

## Questions

**Do I need to move?** Replace `user-guide-diataxis` with `product-documentation` in your install commands and profiles.

**Does it still install the four-folder scaffold?** No. It no longer installs `tutorials/`, `how-to/`, `reference/`, or `explanation/`. The new skill inspects your existing guide structure and writes there.

**Does it still need Core?** No. That dependency is removed.

**Can I install it for my user account?** Yes, through the `product-documentation` dependency.

## Details

Scope: repo (default) · Version: 0.3.1 · Source: [packs/user-guide-diataxis](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/user-guide-diataxis)
