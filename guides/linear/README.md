---
title: "`linear` — guides"
summary: Understand the boundary between first-time repository intake and approval-gated synchronization of an existing brief.
pack: linear
kind: explanation
---

# `linear` — guides

**Mode: tracker-authoritative.** These guides assume Linear holds the team's
real backlog. If `docs/product/` is canonical and Linear is only for reporting,
choose repo-first projection below.

Linear integration for this catalogue. Read Linear work into the shared
content-based repository route, or compare an existing tracker-origin
artifact through a separate approval-gated refresh workflow.

The API key never reaches the model. `linear` is a credentialed skill: it
invokes a CLI that resolves your Personal API Key in-process and makes the
GraphQL call itself.

Begin the interactive setup with:

```text
Set up credentials for Linear so I can read the Checkout Redesign project into this repository.
```

## Which mode are you in?

**Repo-first projection (the product-shaping default):** Use this when product
shaping happens in `docs/product/` and Linear is a shallow copy for reporting
and team visibility. Feature intents and slices are projected out; the intent
tree stays canonical, status never returns from Linear, and the [projection contract](../../packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md)
is applied by hand or through a one-shot export you operate; no exporter or
live API integration ships today.

**Tracker-authoritative:** Use this when Linear holds the team's real backlog.
Intake reads that work into the repository without changing Linear. Reviewed
refresh can add only a comment, display status, trace link, pull-request link,
or closure after separate confirmation; it cannot create an issue or rewrite a
requirement body.

Do not mix the modes. Requirements edited in two places diverge silently.

New here? Generate a Personal API Key at Linear → Settings → API → Personal
API keys, then run `credential-setup` to store it. Then read
[Choose Linear intake or brief sync](how-to/linear-brief-intake-and-sync.md)
to decide where to start.

## How-to

Task-oriented recipes for a problem you already have.

- [Choose Linear intake or brief sync](how-to/linear-brief-intake-and-sync.md) — use read-only intake for new work and approval-gated sync only for an existing brief.

---

The two-layer credential model — why the skill never holds your token — lives
with the [`credential-brokers`](../credential-brokers/) pack. Installing and
upgrading the catalogue live in [`../_shared/`](../_shared/).
