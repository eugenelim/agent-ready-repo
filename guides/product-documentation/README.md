# Product Documentation guides

Documentation for the `product-documentation` pack — create, revise, retrofit, audit, and verify user-facing docs grounded in what your pack actually ships.

## Get started fast

```
Help me write the README for this pack
```

```
Write a how-to guide for rotating a credential token
```

```
Audit the existing docs and tell me what's missing
```

The `author-product-docs` skill infers what you need from your request. You do not need to name a mode.

---

## How-to guides

| Guide | When to use |
|---|---|
| [How to use author-product-docs](how-to/use-author-product-docs.md) | Create guides, READMEs, journeys, or audit docs for any pack |

---

## Explanations

| Guide | What it covers |
|---|---|
| [About the Diátaxis framework](explanation/the-diataxis-framework.md) | The four page kinds — tutorial, how-to, reference, explanation — and when to use each |

---

## Install this pack

```bash
agentbundle install --pack product-documentation
```

Scope: `--scope repo` (default) or `--scope user` (available across all repos).

## Replaces

This pack supersedes [`user-guide-diataxis`](../user-guide-diataxis/). If you have `user-guide-diataxis@0.3.0` installed, you already have this pack as a dependency.
