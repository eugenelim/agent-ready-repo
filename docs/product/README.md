# Product

> The product-side counterpart to [`architecture/`](../architecture/).
> Architecture answers "what is the code, today?"; product answers "what
> is the product, today?" Both are *living* docs — kept in sync with
> reality, not historical record.

## What lives here

### The product record

[§ What belongs here](#what-belongs-here) below is the one source for what
these hold and how they are maintained:

[`roadmap.md`](roadmap.md) · [`changelog.md`](changelog.md) ·
[`intents/`](intents/) · [`briefs/`](briefs/) · [`shaping/`](shaping/) ·
[`findings/`](findings/) · [`initiatives/`](initiatives/) ·
[`research/`](research/)

A released `changelog.md` highlight also needs the `/now/` projection
regenerated in the same change — see [`AGENTS.md`](AGENTS.md).

### Local to this repository

The table below does not cover these; they are described and governed here.

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
[`../README.md` § The three lifecycle classes](../README.md#the-three-lifecycle-classes).

## What belongs here

What the product is *currently* doing — the counterpart to `architecture/`.
Without this layer you have per-feature contracts and decision history, but no
answer to "what is the product up to right now?"

| File | Holds | Note |
| --- | --- | --- |
| `roadmap.md` | Direction for the next few quarters | Direction, not commitments. An item that has not moved in two consecutive reviews is a drift signal. |
| `changelog.md` | User-visible changes by release | One section per release, naming every artifact it covers. |
| `intents/<TYPE>-NNNN-<slug>.md`, or `intents/<slug>.md` | One admitted outcome, recorded before a solution is chosen | Optional. The typed prefix is allocated at admission for a recognized altitude; an intent without one is complete, and its slug is its identity either way. |
| `briefs/<slug>.md` | One delivery outcome and the specs that deliver it | Optional, for work too large to be one spec. |
| `shaping/<slug>.md` | One outcome still being framed, before it is admitted | Optional. Closes by becoming an intent or being dropped. |
| `findings/<slug>.md` | One observation from real use, with its evidence | Optional. A finding is evidence, not a commitment to act. |
| `initiatives/<slug>.md` | One multi-spec push and the briefs under it | Optional, above the brief layer. |
| `research/<slug>.md` | One answered question and the sources that answered it | Optional. Frozen once answered; supersede rather than edit. |

The changelog's heading level is load-bearing. A section carrying a version and
a date is released, so it sits at the top level directly beneath
`[Unreleased]` — never nested inside it. An entry is required in the same change
that bumps a released artifact's version, because you know the version at write
time: you are setting it. Tooling that ships in no release needs no entry.

A published package also keeps its own changelog beside its source, for readers
who get the package and not the repository.
