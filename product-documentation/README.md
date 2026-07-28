# Product Documentation

Create, revise, retrofit, audit, and verify product documentation — pack READMEs, user guides, journeys, and Diátaxis pages — grounded in what your pack actually ships.

## What this helps you do

- **Write a pack README** that leads with outcomes rather than a skill inventory
- **Create a guide** — tutorial, how-to, reference, or explanation — for any user-facing behavior
- **Retrofit connected pages** around a coherent user journey
- **Audit existing docs** for inventory-first writing, audience mismatch, or unverified behavior claims
- **Verify documentation** against current canonical behavior before you ship

## Install

```bash
agentbundle install --pack product-documentation
```

Scope options: `--scope repo` (default) or `--scope user` (available across all repos).

## Get started

```
Help me create product documentation for [pack name]
```

```
Write a how-to guide for rotating a credential token
```

```
Audit the existing docs for this pack and tell me what's missing
```

The skill infers what you need (create, revise, retrofit, audit, or verify) from your request. You do not need to name a mode.

## How it works

The skill inspects canonical behavior — `pack.toml`, actual skill sources, schemas, and permissions — before making any product claim. It selects the minimum useful artifact set. It does not create empty category directories or sibling pages for their own sake.

Diátaxis is an authoring contract, not a required directory structure. The four kinds (tutorial, how-to, reference, explanation) determine what a page does for the reader — not where it must live.

## Guides

Full documentation for this pack: [guides/product-documentation/](../../guides/product-documentation/)

- [How to use author-product-docs](../../guides/product-documentation/how-to/use-author-product-docs.md)
- [About the Diátaxis framework](../../guides/product-documentation/explanation/the-diataxis-framework.md)

## Replaces

This pack supersedes `user-guide-diataxis`. The `user-guide-diataxis@0.3.0` compatibility pack installs `product-documentation` as a dependency. If you have `user-guide-diataxis` installed, you already have this pack.
