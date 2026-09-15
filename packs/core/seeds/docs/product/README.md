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
[`../README.md` § The three lifecycle classes](../README.md#the-three-lifecycle-classes).

## What belongs here

What the product is *currently* doing — the counterpart to `architecture/`.
Without this layer you have per-feature contracts and decision history, but no
answer to "what is the product up to right now?"

| File | Holds | Note |
| --- | --- | --- |
| `roadmap.md` | Direction for the next few quarters | Direction, not commitments. An item that has not moved in two consecutive reviews is a drift signal. |
| `changelog.md` | User-visible changes by release | One section per release, naming every artifact it covers. |
| `intents/<slug>.md` | One admitted outcome, recorded before a solution is chosen | Optional. |
| `briefs/<slug>.md` | One delivery outcome and the specs that deliver it | Optional, for work too large to be one spec. |

The changelog's heading level is load-bearing. A section carrying a version and
a date is released, so it sits at the top level directly beneath
`[Unreleased]` — never nested inside it. An entry is required in the same change
that bumps a released artifact's version, because you know the version at write
time: you are setting it. Tooling that ships in no release needs no entry.

A published package also keeps its own changelog beside its source, for readers
who get the package and not the repository.
