---
title: "`linear` — guides"
summary: Understand the boundary between first-time repository intake and approval-gated synchronization of an existing brief.
pack: linear
kind: explanation
---

# `linear` — guides

Linear integration for this catalogue. Read Linear work into the shared
content-based repository route, or keep an existing brief's imported sections
in sync through a separate approval-gated workflow.

The API key never reaches the model. `linear` is a credentialed skill: it
invokes a CLI that resolves your Personal API Key in-process and makes the
GraphQL call itself.

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
