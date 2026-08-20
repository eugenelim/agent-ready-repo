# Recorded design review — site shared chrome

- **Status:** Accepted — reviewed 2026-08-20
- **Reviewer:** eugenelim (human)
- **Spec:** [`../spec.md`](../spec.md) AC13
- **Reviewed at:** `main` `ae6d0e30`

## Why this record exists

AC13 asks whether a recorded design review finds any Major issue against either
renderer's named aesthetic direction or the four tech-site principles. That is
human judgement about how the surfaces read, so it is not self-certifiable and no
gate stands in for it. This file is the record; the verdict below is the human
reviewer's, not the implementer's.

## What was reviewed

Served from one preview server, which covers both renderers because the docs
build writes into `build/docs/` under the marketing build's base.

| Surface | Route |
| --- | --- |
| Marketing home | `/agent-ready-repo/` |
| Now | `/agent-ready-repo/now/` |
| Catalogue | `/agent-ready-repo/catalogue/` |
| Docs home | `/agent-ready-repo/docs/` |
| Nested guide | `/agent-ready-repo/docs/guides/core/how-to/start-a-project/` |

Both docs themes, through Starlight's own theme control. Wide and phone widths.

## Directions and principles it was judged against

- Marketing: `docs/specs/platform-site/aesthetic-direction.md` — the
  alternating-band model, ranked goals **Precision authority** (dominant),
  Staged revelation, Grounded ambition, Identity specificity.
- Docs: `docs/specs/docs-site-design-refresh/creative-direction.md` — ranked
  goals **Instrument-grade clarity** (dominant), Editorial gravitas, Calibrated
  engineering cool, Quiet enterprise polish.
- Both: the four principles in `docs/design/principles/tech-site.md` — lead with
  the user's job; put verifiable evidence beside every claim; keep readers
  oriented through stable names, paths and destinations; preserve each surface's
  reading mode within one product identity.

## What the review was asked to decide

A **Major** was defined as: a reader would be misled or lose their place; the
surface contradicts its named direction's dominant goal; or it breaks a
principle's arbitration test. Named examples of Major: the band competing with or
visually replacing the Starlight header; docs beginning to read as marketing; a
destination whose name or prominence implies a different product map than
marketing's. A **Nit** was defined as spacing, optical alignment, hairline
weight, or letter-spacing — worth fixing, not worth blocking.

The reviewer was also pointed explicitly at the one place this work departs from
stock framework behaviour: the docs header wrapper is `position: sticky` where
Starlight ships `position: fixed`, because the spec requires the band to scroll
away while the header stays sticky, which a viewport-fixed header cannot do.

## Verdict

**No Major issue** against either named aesthetic direction or the four
principles. AC13 is satisfied on this record.

No Nit was raised at review time. Any later finding on these surfaces names the
principle it violates, or says it is a universal quality-floor finding instead,
per the design-review commitment in `docs/design/principles/tech-site.md`.

## Boundary of this record

This is a browser review at the approved widths. The physical-device pass remains
the programme's separate manual release check and is not claimed here — see
`docs/product/release-checklist.md` § site-browser-quality-gate, where it is
recorded with its owner. Unmeasured is not the same as absent.
