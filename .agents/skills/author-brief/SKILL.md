---
name: author-brief
description: Deprecated compatibility alias for author-delivery-brief create. Use only when an older caller explicitly invokes author-brief.
allowed-tools: Read
metadata:
  type: skill
  boundaries: []
---

# Compatibility alias: author-brief

Deprecated. Translate this invocation once to
`author-delivery-brief create`, preserve the caller's bounded input and
authority mode, and return the canonical owner's result unchanged.

Emit one notice before delegation:

> `author-brief` is deprecated; using `author-delivery-brief create`.

The canonical receipt names `author-delivery-brief create` as the processor
and may record `invoked_alias: author-brief`; no other alias identity is
written.

Do not author content, select another route, write an artifact, register work,
or repeat delivery-brief lifecycle rules here. New prompts, receipts, guides,
and internal dispatch use `author-delivery-brief create` directly.

## Compatibility window

Retain this alias for at least two minor Core releases and 90 days from its
deprecation release, whichever is later. Announce removal in advance. At the
first eligible release, removal still requires a named Approver decision. If
alias activation or canonical-receipt fixtures regress, roll back
to the last alias-bearing Core pack release.

## Boundaries

The alias has `Read` only and no write, network, shell, tracker, credential, or
filesystem-read-untrusted boundary. The canonical target applies its own exact
tools and boundaries after delegation.
