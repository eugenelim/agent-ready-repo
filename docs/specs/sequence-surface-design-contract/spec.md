# Spec: the sequence surfaces carry their design contract

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Provenance

Slice **S8** of
[`sdlc-guide-uplift-and-learning-paths`](../../product/briefs/sdlc-guide-uplift-and-learning-paths.md).

**Why this exists as a slice rather than an amendment.** S6
([`four-discipline-sequence`](../four-discipline-sequence/spec.md)) shipped, and
the experience-design craft sequence that should have preceded it ran afterwards.
That pass produced obligations no S6 criterion covered, and it also required
changing how [`install-to-ship-walkthrough`](../install-to-ship-walkthrough/spec.md)
defines a stage.

Both of those specs are **Shipped, and therefore frozen**: `docs/CONVENTIONS.md`
§ Documentation classes states that shipped `specs/*` are "Immutable history.
Status fields can change, bodies cannot", and § Lifecycle adds that after a
feature ships "the *code is the truth*, and the spec becomes the record of what
was agreed".

An earlier attempt reopened S6 to `Implementing`, added four criteria to it, and
amended `install-to-ship-walkthrough`'s AC2 in place. An independent review
sustained both as blocking. **Both bodies have been restored**; the behaviour
they described is governed here instead. The code and tests stayed throughout —
they are the truth, and this slice records the contract they were already
meeting.

## Objective

The two surfaces that carry the four-discipline sequence hold their design
contract, so a reader can tell the groups apart, can move from seeing the
sequence to walking it, and is not offered two routes that claim the same case.

Three outcomes:

1. **The journeys index's three groups are distinguishable from each other**
   without relying on their headings. S6 shipped all three sharing one card
   treatment; a design review found they collapsed into a single collection.
2. **The sequence leads somewhere.** S6's journeys index contained zero
   references to `guides/`: it showed the shape and stranded the reader.
3. **The guides hub offers the alternative at the point of choice**, and the two
   routes select on different conditions.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable | `web/src/pages/journeys/index.astro`; `guides/README.md` | `author-product-docs` conventions | Guide validators pass; page builds and renders | Both surfaces carry the contract below |
| Current product truth | Applicable — the brief tracks slice delivery | the brief's § "Spec map" | `lint-brief-coverage` roll-up | Roll-up resolves this spec through its `Brief:` back-link | Roll-up names this spec; no status hand-written |
| Reusable learning | Applicable — three assertions here failed their own mutation before passing | `notes/verification-ledger.md` | This spec's owner | Recorded mutation runs | Ledger records each mutation and its observed failure |
| Decision rationale | **Not applicable** — the design decisions are recorded in the two content briefs by their authors | none | — | — | — |
| Release history | **Not applicable** — `web/` and `guides/` are not published packs | none | — | — | — |
| Interface compatibility | **Not applicable** — no published URL, slug or frontmatter key changes | none | — | — | — |

## Boundaries

### Always do

- Leave frozen spec bodies alone. A shipped spec's record of what was agreed is
  not a description of what is now true; changes go in a live slice.
- Keep group membership derived from the `journeys` collection.

### Ask first

- Any change to `guides/README.md`'s navigation model, which belongs to
  `cohort-orientation-surfaces`.

### Never do

- **Edit any file under `web/src/content/journeys/`.** Generated from
  `packs/*/JOURNEY.md`; editing by hand is a four-pack released change.
- **Add an image to either surface.** The projector rewrites Markdown image
  paths into page URLs and copies no assets.
- **Claim first value, a completed method, or a successful install.** The
  Claude-apps probe is unrun.
- **Describe the two plugin routes as equivalent.**

## Testing Strategy

- **Group signatures (AC-0001):** construction test on the `web/` vitest suite
  over the built page. It scopes each modifier to its own group and requires the
  three at-rest rules to differ. A page-wide check passes when two groups swap
  modifiers, and an any-rule check passes on a `:hover`-only rule — both were
  real defects in earlier versions of this assertion.
- **Onward route (AC-0002):** construction test asserting the anchor's **exact**
  target. A substring check passes on a different path sharing those fragments.
- **Adjacency (AC-0003):** goal-based check over `guides/README.md`.
- **Selection conditions (AC-0004):** a reader comparing the two passages. See
  Accepted residuals.
- **The walkthrough's stage definition (AC-0005):** the existing
  `install-to-ship-walkthrough` cases on the same suite, which must continue to
  pass with the alternative present and fail on a sixth numbered stage.

## Acceptance Criteria

- [x] **AC-0001.** Each of the journeys index's three groups applies its own card
      modifier, scoped to that group, and the three modifiers' at-rest style
      rules differ from one another.
- [x] **AC-0002.** The sequence group links onward to the guides path that walks
      the same four disciplines, at that path's own anchor.
- [x] **AC-0003.** In `guides/README.md` the alternative path is adjacent to the
      step it is an alternative to, with no other stage between them.
- [x] **AC-0004.** The alternative path and the step it replaces do not both
      claim the same selection condition.
- [x] **AC-0005.** `install-to-ship-walkthrough`'s stage cases treat a heading
      labelled `P<n>` with a bare number as a stage and a `P<n>b` heading as an
      alternative, so its five-stage contract still holds with the alternative
      present and still fails on a sixth numbered stage.

## Acceptance-set construction record

Run 2026-09-11 from the design pass's obligations and the frozen-spec
restoration.

- **Candidate obligations:** 9
- **Admitted as criteria:** 5
- **Routed:** 4

| Candidate obligation | Disposition | Criterion / owner | Red input | Observer |
| --- | --- | --- | --- | --- |
| The groups are distinguishable without headings | admitted | AC-0001 | two groups sharing a modifier, or three identical at-rest rules | built page markup and its inlined style |
| The sequence leads onward | admitted | AC-0002 | no anchor, or one targeting anything else | built page |
| The alternative sits beside its step | admitted | AC-0003 | another stage heading between them | `guides/README.md` |
| The two routes select differently | admitted | AC-0004 | both passages naming the same trigger | a reviewer reading the two passages |
| An alternative may sit inside the walkthrough without breaking its contract | admitted | AC-0005 | the five-stage cases failing with the alternative present, or passing with a sixth numbered stage | the `install-to-ship-walkthrough` cases |
| The catch-all group names a relationship | **routed** | `docs/design/content/journeys-index.md` | — | a copy decision; no criterion could fail on it without asserting its own wording |
| Card content agrees with sequence position | **routed** | S7 and the owning packs | — | taglines are generated from `packs/*/JOURNEY.md` |
| The guides hub's above-fold start promise and its search | **routed** | `cohort-orientation-surfaces` | — | its brief already records both as absent; this slice does not own that surface's structure |
| The marketing home's journeys entry | **routed** | `cohort-orientation-surfaces` | — | decided in its content brief, not implemented; the header is the navigation model and drives both sites |

**Set-level result.** *Necessity:* each criterion names a distinct red input; no
two share one. *Uniqueness:* one observer each. *Consistency:* AC-0003 places the
alternative inside the walkthrough section and AC-0005 keeps that section's
five-stage contract true, which is why AC-0005 exists rather than being assumed.
*Joint feasibility:* nothing here requires content another criterion forbids.
*Coverage both ways:* outcome 1 reaches AC-0001; outcome 2 reaches AC-0002;
outcome 3 reaches AC-0003, AC-0004 and AC-0005; each routed row names an owner.
Every criterion traces back to one outcome.

## Accepted residuals

- **AC-0004's observer is a person.** Whether two prose passages claim the same
  condition is a meaning comparison; the mechanical alternatives test wording,
  and would pass on a synonym or fail on a correct rewrite. Discharged once by an
  independent review on 2026-09-11, which quoted both passages and returned PASS.
- **The frozen S6 plan's description of its AC-0004 construction test does not
  match the shipped test.** It says the card heading's accessible name should
  begin with the step number; the spec and the test both require the opposite.
  The test and spec agree with each other and with the implementation. The plan
  is frozen history and is left alone — which is the point of this slice.

## Assumptions

- The three at-rest rules differing is a sufficient proxy for visual
  distinguishability. It is not a rendering check: three rules could differ and
  still look alike. Accepted as the strongest mechanical check available without
  a screenshot oracle, and the design review covers the perceptual question.
