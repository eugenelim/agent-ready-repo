# Product

> The product-side counterpart to [`architecture/`](../architecture/).
> Architecture answers "what is the code, today?"; product answers "what
> is the product, today?" Both are *living* docs — kept in sync with
> reality, not historical record.

## What lives here

- [`roadmap.md`](roadmap.md) — direction for the next 2-4 quarters.
  Direction, not commitments. Updated quarterly.
- [`changelog.md`](changelog.md) — user-visible changes by release,
  in [Keep a Changelog](https://keepachangelog.com/) format. Updated
  every PR that changes user-visible behavior.
- [`personas.md`](personas.md) — who we're building for. Optional;
  add only if it's actively used to make decisions.
- [`release-checklist.md`](release-checklist.md) — manual-QA rows
  CI cannot exercise. Copy each spec's section into the release PR
  description before tagging. Optional; add the file the first time a
  spec needs out-of-band verification.

## What does NOT live here

- **Why we made past choices** → [`../adr/`](../adr/) (immutable history).
- **What we're proposing to change** → [`../rfc/`](../rfc/) (governance).
- **What an individual feature does** → [`../specs/<feature>/spec.md`](../specs/).
- **The mission and scope of the project** → [`../CHARTER.md`](../CHARTER.md).
- **How users actually use the product** → [`../guides/`](../guides/) (Diátaxis-organized user docs).

## The product/ layer is *living*

Unlike ADRs and shipped specs (which are frozen records), files here must
match current reality. Drift is a bug. The maintenance rules are in
[`../CONVENTIONS.md`](../CONVENTIONS.md#document-lifecycle).
