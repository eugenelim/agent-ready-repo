---
name: new-guide
description: "Create or substantially revise user guides, pack pages, and journey pages using Diátaxis plus conversation-first UX. Use when asked to write, simplify, restructure, audit, or modernize tutorials, how-to guides, reference pages, explanations, pack pages, or journey pages so readers can start from a natural-language goal, see what to say, understand what happens next, and reach an outcome without learning internal skill names first. Do NOT use for feature contracts (use `new-spec`), cross-cutting proposals (use `new-rfc`), recording decisions (use `new-adr`), minor single-line edits (normal PR), contributor docs, docstrings, release notes, or blog posts."
---

# Compatibility shim — use `author-product-docs` instead

This skill is deprecated. The `product-documentation` pack (installed as a dependency of this pack) provides `author-product-docs` with the same triggers and five explicit modes: create, revise, retrofit, audit, and verify.

## What to do

Your request will work with `author-product-docs`. You can invoke it explicitly or just describe what you need — the skill activates on the same natural-language triggers:

- "Write a how-to guide for X"
- "Create a tutorial for Y"
- "Revise this guide"
- "Audit the docs for Z"
- "Verify this documentation against what ships"

`author-product-docs` is already installed via the `product-documentation` dependency. No reinstall needed.

## What changed

The new skill supports five modes (create, revise, retrofit, audit, verify), treats Diátaxis as a page contract rather than a required directory structure, inspects canonical sources before making product claims, and correctly routes between the catalogue-facing `guides/` tree and the internal `docs/guides/` tree.

The four-quadrant seed scaffold is no longer installed. Your existing `docs/guides/` directory is unaffected.

## Migrating

Replace `user-guide-diataxis` with `product-documentation` in your profiles and install commands:

```bash
agentbundle install --pack product-documentation
```
