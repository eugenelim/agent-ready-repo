# Product

> The product-side counterpart to [`architecture/`](../architecture/).
> Architecture answers "what is the code, today?"; product answers "what
> is the product, today?" Both are *living* docs — kept in sync with
> reality, not historical record.

## What lives here

### Governed by the conventions

[`../CONVENTIONS.md` § 5b](../CONVENTIONS.md#5b-docsproduct--for-maintainers)
is the one source for what these hold and how they are maintained. Read it
there, not here:

[`roadmap.md`](roadmap.md) · [`changelog.md`](changelog.md) ·
[`intents/`](intents/) · [`briefs/`](briefs/) · [`shaping/`](shaping/) ·
[`findings/`](findings/) · [`initiatives/`](initiatives/) ·
[`research/`](research/)

One local delta: a released `changelog.md` highlight also needs the `/now/`
projection regenerated in the same change — see [`AGENTS.md`](AGENTS.md).

### Local to this repository

§ 5b does not cover these; they are described and governed here.

- [`release-checklist.md`](release-checklist.md) — manual-QA rows CI cannot
  exercise. Copy each spec's section into the release PR description before
  tagging. Add the file the first time a spec needs out-of-band verification.
- [`journeys/`](journeys/) — role journeys: what each audience does end to end.
- [`design/`](design/) — experience and lifecycle design records for surfaces
  that are decided but not yet specced.
- [`voice/`](voice/) — the product's voice and register.
- [`ini-003-phase0-reconciliation.md`](ini-003-phase0-reconciliation.md) — a
  one-off parity audit retained as evidence.
- [`workspace-toml-deps.md`](workspace-toml-deps.md) — the `workspace.toml`
  inline dependency notation.

## What does NOT live here

- **Why we made past choices** → [`../adr/`](../adr/) (immutable history).
- **What we're proposing to change** → [`../rfc/`](../rfc/) (governance).
- **What an individual feature does** → [`../specs/<feature>/spec.md`](../specs/).
- **The mission and scope of the project** → [`../CHARTER.md`](../CHARTER.md).
- **How users actually use the product** → [`../../guides/`](../../guides/)
  (Diátaxis-organized user docs).

## The product/ layer is *living*

Unlike ADRs and shipped specs (which are frozen records), files here must
match current reality. Drift is a bug. The maintenance rules are in
[`../CONVENTIONS.md`](../CONVENTIONS.md#document-lifecycle).
