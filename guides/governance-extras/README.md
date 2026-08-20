---
title: "`governance-extras` — guides"
summary: Choose the governed workflow for proposing a cross-cutting change, recording a decision, or updating repository conventions.
pack: governance-extras
kind: explanation
---

# `governance-extras` — guides

A written trail for the decisions a long-lived repo accumulates. Three skills, three artifacts: `new-rfc` proposes a change whose direction is still open, `new-adr` records a decision once it's made, and `rfc-status` surveys what is open, accepted, or rejected. The pack also ships the `docs/rfc/` and `docs/adr/` shapes those skills write into.

New here? [Propose a change with an RFC](how-to/new-rfc.md) when something is still open; [record it with an ADR](how-to/new-adr.md) once it's settled.

## Tutorials

- [Your first governance session](tutorials/governance-extras-first-session.md) — install the pack, record one ADR with the preview-confirm gate, and commit it in about fifteen minutes.

## How-to

- [Propose a cross-cutting change (RFC)](how-to/new-rfc.md) — open a proposal for input before a decision is locked in.
- [Record a decision (ADR)](how-to/new-adr.md) — capture what was decided, the context, and the alternatives weighed.
- [Set up a governance index](how-to/governance-index.md) — build a domain → ADR manifest so an agent loads 2–3 files instead of the whole ADR tree.
- [Define an extension contract](how-to/extension-contract.md) — document a plugin or customisation hook so adopters know what is stable.

---

Installing and upgrading live in [`../_shared/`](../_shared/).
