---
name: new-guide
description: "Deprecated legacy skill. Activates on 'new guide', 'write a guide', 'new tutorial', 'new how-to', 'new reference page', 'new explanation' — legacy invocation syntax only. Redirects to author-product-docs. Use author-product-docs directly for all new documentation work."
---

# new-guide — Deprecated redirect

This skill is a compatibility redirect. The canonical skill is
`author-product-docs` in the `product-documentation` pack.

## What to do

Use `author-product-docs` instead:

> Write a how-to guide for [your task].
> Create a tutorial explaining how to [your workflow].
> Revise the pack README for [pack name].

`author-product-docs` supports create, revise, retrofit, audit, and verify
modes. It uses Diátaxis as a page contract — no four-quadrant folder scaffold is
required.

Install the canonical pack if you haven't already:

```
agentbundle install --pack product-documentation <catalogue>
```

## Overlap note

Both `new-guide` and `author-product-docs` activate on requests like "write a
how-to guide." When both packs are installed, either skill may activate — the
correct resolution is always `author-product-docs`. The agent should prefer the
canonical skill and ignore this redirect when both are present.
