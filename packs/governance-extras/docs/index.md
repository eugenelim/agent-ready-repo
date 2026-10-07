# Governance Extras

> A repo-scope pack of three skills that give teams a structured, traceable workflow for proposing changes, recording architectural decisions, and navigating the decision corpus.

## Why this pack exists

Without a formal decision record, teams capture choices in Slack threads, PR descriptions, or nowhere at all — making it impossible later to understand why a constraint exists or what alternatives were considered. With this pack, every significant decision gets either an RFC (open proposal under review) or an ADR (closed, immutable record) with a consistent structure that survives team turnover. The navigator lets you query and explore that corpus without learning the file layout.

## What it is

**Skills (3):** `new-rfc` (draft and shepherd a proposal through the RFC lifecycle, including generating follow-on specs for an Accepted RFC), `new-adr` (capture a decision, its context, and the alternatives considered), `navigate-decisions` (read-only query and offline HTML export for ADR and RFC lifecycle, lineage, guidance context, and exact record detail).

No subagents. Installs RFC and ADR file templates plus seed READMEs for `docs/rfc/` and `docs/adr/`.

See the README for the complete manifest table.

## What it is not

- Not a full governance platform — it does not manage voting, quorum, or role-based access to decisions.
- Not a meeting management tool — it produces records, not agendas or minutes.
- Not a replacement for code review — it governs *what* to build and *why*, not *how* it is implemented.

## How it relates to other packs

Requires `core` (the build loop these RFC-based decisions ultimately feed). `catalogue-curation` requires both `core` and `governance-extras` — it uses the RFC skill to create a traceable intake record every time a new primitive is assimilated into the catalogue.
