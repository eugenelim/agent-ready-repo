# Explanation

> *Understanding-oriented.* Discussions that illuminate. Why we made a
> design choice, how a system fits together, what a concept means in
> this product. Theoretical, contextual, opinionated. Read by people
> who want to understand more deeply.

## Writing explanation

Explanation is the kind of doc most engineers *want* to write — and
end up putting in the wrong place (often in tutorials and how-tos,
where it disrupts the flow). When you find yourself wanting to explain
*why* in the middle of any other kind of doc, **stop, write the
explanation here, and link to it.**

A good explanation:

- **Illuminates.** It changes how the reader thinks about a thing.
- **Provides context.** Why this design? Why not the obvious alternative?
  What constraints shaped the answer?
- **Is allowed to be opinionated.** Explanation has a voice. It can say
  "we chose X because we believe Y."
- **Is allowed to wander a little.** Unlike reference and how-to,
  explanation isn't trying to get the reader to a destination — it's
  trying to expand their understanding.

## What goes in explanation

- "Why we built X" pieces.
- "How X works under the hood" deep dives.
- Key concepts: definitions plus the conceptual context.
- Comparisons: "X vs Y, when to use which."
- Architecture overviews aimed at *users* (not contributors — those
  live in `../../architecture/`).

## What does NOT go in explanation

- Step-by-step instructions. Tutorial or how-to.
- Authoritative parameter lists. Reference.
- Decisions written for the team. Those are ADRs (`../../adr/`).

## Explanation vs. ADRs vs. architecture

Subtle but important:

- **ADRs** are decision records, frozen, written for the team. Internal.
- **`docs/architecture/`** describes the current state of the code, written
  for contributors. Internal.
- **Explanation here** is for *users* — people who don't read the code
  but want to understand what they're using. Public.

The same topic might appear in all three with different framing. The ADR
records *why we chose* approach X over Y. The architecture doc describes
*how X is implemented*. The explanation page describes *what X means
for someone using the product*. Don't merge them — each audience needs
the framing that fits them.

## Maintenance

Explanation rots slower than tutorials and how-tos but faster than
reference. Pieces become wrong when the underlying design changes; they
become *misleading* even before they become wrong. Review on each major
release.
