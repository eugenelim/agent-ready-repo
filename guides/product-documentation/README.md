---
title: "Product Documentation guides"
summary: "Find the product-documentation pack's workflows for auditing, writing, revising, and verifying the docs of any software product."
pack: product-documentation
kind: reference
---

# Product Documentation guides

Documentation for the `product-documentation` pack — create, revise, retrofit, audit, and verify the user-facing docs of any library, CLI, API, app, service, plugin, or agent-context pack, grounded in what it actually ships.

## Get started fast

Start here: [Getting started](getting-started.md)

```
Audit this project's docs and tell me which stages of the reader journey are missing
```

```
Write a quickstart for this CLI
```

```
Write release notes for v2.1
```

The `author-product-docs` skill infers what you need from your request. You do not need to name a mode.

---

## Tutorials

| Guide | What you do |
|---|---|
| [Getting started](getting-started.md) | Audit your own repository's docs, write the first missing page, and check it |

---

## How-to guides

| Guide | When to use |
|---|---|
| [How to author product docs](how-to/author-product-docs.md) | Audit a doc set against the reader journey, then fix the biggest gaps |
| [How to write a guide](how-to/write-a-guide.md) | Document one shipped feature |

---

## Explanations

| Guide | What it covers |
|---|---|
| [About the Diátaxis framework](explanation/the-diataxis-framework.md) | The four page kinds, how they fit the nine-stage reader journey, and what they leave uncovered |

---

## Install this pack

```bash
agentbundle install --pack product-documentation
```

Scope: `--scope repo` (default) or `--scope user` (available across all repos).

## Replaces

This pack supersedes the deprecated `user-guide-diataxis` pack. If you have
`user-guide-diataxis@0.3.0` installed, you already have this pack as a
dependency.
