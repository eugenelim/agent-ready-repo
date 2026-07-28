# Product Documentation

Create, revise, retrofit, audit, and verify product documentation.
The `author-product-docs` skill works across five modes and uses Diátaxis as a
page contract — not a mandatory folder scaffold. Install at repo or user scope;
no directory skeleton is written on install.

## What you can do

- **Create** a new guide, pack README, journey, or explanation page from
  canonical source behavior.
- **Revise** an existing artifact while preserving or deliberately correcting its
  role.
- **Retrofit** a connected documentation experience across entry surfaces and
  related pages.
- **Audit** for inventory-first writing, audience drift, or stale behavior claims.
- **Verify** that documentation matches current shipped behavior and renders
  correctly.

## First request

Ask your agent:

> Write a how-to guide explaining how to [your most common user task].

The skill reads the relevant pack sources, proposes a documentation contract
(mode, audience, artifact type), and drafts a task-first guide. You confirm
before any files change.

## The Diátaxis compass

`author-product-docs` assigns one page kind per artifact — tutorial, how-to,
reference, or explanation — by reader posture, not by topic. You do not need to
name the kind; the skill infers it. You do not need four empty quadrant folders;
the kind is a contract, not a directory.

| Reader posture | Page kind |
|---|---|
| On rails, wants a guaranteed result | Tutorial |
| Named problem, wants the recipe | How-to |
| Scanning for an authoritative answer | Reference |
| Away from keyboard, wants to understand *why* | Explanation |

## Install

```
agentbundle install --pack product-documentation <catalogue>
```

Repo scope is the default. For user-scope install (skill available across all
your repos):

```
agentbundle install --scope user --pack product-documentation <catalogue>
```

## Guides

Product documentation guides live at
[`guides/product-documentation/`](../../guides/product-documentation/).

## Migrating from user-guide-diataxis

`user-guide-diataxis` is now a deprecated compatibility shim that depends on
this pack. Install `product-documentation` directly for all new work.
