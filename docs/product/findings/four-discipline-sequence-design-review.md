# Design review, 2026-09-11 — findings and dispositions

Independent experience/design review of the **rendered** surfaces
(`build/journeys/index.html`, `build/docs/guides/index.html`, `build/index.html`)
against `packs/experience-design/DESIGN.md`'s quality floor and the two content
briefs. Verdict: **SHIP WITH CHANGES** — 1 blocking, 8 major, 3 minor.

This is the design pass S6 should have had and did not. Most findings are
**pre-existing surface defects**, surfaced because the review was pointed at
whole surfaces rather than at the diff. They are recorded with owners rather
than absorbed, because absorbing nine unrelated defects into this slice is the
boundary mistake in the other direction.

## Repaired here

| Finding | Severity | What was wrong |
| --- | --- | --- |
| P2 and P2b gave contradictory choice criteria | MAJOR | P2 said reach past to the robust path "when the problem itself is unclear"; P2b said "take this when [the question] is not [framed]". Both claimed the unclear-problem case, so the pair read as a duplicated step rather than a choice. Rewritten on a non-overlapping axis: **which disciplines the work needs**, not how clear the problem is. P2's robust path already handles an unclear problem |
| P2b sat inside the five-stage walkthrough | — | Not a review finding; caught by the `web/` suite immediately after. `install-to-ship-walkthrough` is **Shipped** and pins five stages with a successor chain, counting every `h3` in that section. P2b is an alternative route, not a sixth stage, so it moved to its own "The wider shaping route" section after the walkthrough. The P2 cross-link, not adjacency, carries the discoverability the review credited |
| A shipped test counted P2b as a sixth stage | — | Not a review finding; caught by the `web/` suite. `install-to-ship-walkthrough` implemented "stage" as every `h3` in the section. **My first repair moved P2b out, which was wrong** — it reshaped the page to satisfy a snapshot and moved away from the placement this review had endorsed. A Shipped spec records what was true at delivery; it does not bind the product's future shape. The spec and test were amended instead to define a stage as `P<n>` with a bare number, re-verified by mutation, and P2b stays adjacent to P2 |
| The three journey groups shared one card treatment | MINOR | Without their headings the groups collapsed into one collection, making the four-discipline block read as cards bolted onto an existing grid. The left edge now carries the relationship: accent bar plus numeral for the ordered sequence, muted bar for the loops underneath, no bar for optional additions |
| "Everything else" was not a relationship | MINOR | Renamed to "Add one when the work needs it", with body copy stating that none of them is a step in the sequence |

## Refuted

**MAJOR — "primary navigation falsely marks Catalogue as current" on `/journeys/`.**
Not a defect. `web/src/lib/shared-chrome.ts` `currentState()` does this
deliberately: `link.id === 'catalogue' && routePath.startsWith('/journeys/')`
returns `'location'`, and `aria-current="location"` is the correct ARIA value for
an *ancestor* of the current page. Journeys is intentionally nested under
Catalogue.

**It does become a live question if the recorded header decision ships.** With
Journeys as its own header destination, `/journeys/` would carry both
`aria-current="page"` on Journeys and `aria-current="location"` on Catalogue.
That is defensible but should be decided, not discovered. Flagged for whoever
implements the header change.

## Routed — generated content

**MAJOR — the Product Engineering card contradicts its position in the sequence.**
Its tagline reads "Raw idea → build-ready decision brief", so the fourth
discipline appears to restart the sequence and stop before implementation, while
the group copy says it receives a designed bet and ends at an approved merged
change.

Real, and not fixable in this slice: taglines come from
`web/src/content/journeys/*.md`, which carry `generated: true` and project from
`packs/*/JOURNEY.md`. **AC-0018 forbids touching them**, and editing the source
is a released pack change. **Owner: the `product-engineering` pack.** S7 should
carry it, since S7 already owns the walk's handoff semantics.

## Routed — pre-existing, with owners

None of these was introduced by this slice; several are predicted verbatim by
the briefs that govern the surfaces ("Does not exist today").

| Finding | Severity | Owner |
| --- | --- | --- |
| "Start in one command" offers only a terminal route, against the brief's "two equal doors" | **BLOCKING** | `claude-apps-first-value-entry` — and `claude-apps-route-docs` is the Draft, unimplemented spec for it |
| Guides hub has no above-fold "start here" promise; opens taxonomy-first | MAJOR | **Routing withdrawn 2026-09-11 — implemented instead.** A sentence and a link are content, which the guides content brief governs; `cohort-orientation-surfaces` owns the navigation model, untouched. Routing it away was avoidance dressed as ownership discipline |
| Guides hub search is a generic header widget on a 229-page search-first site | MAJOR | `cohort-orientation-surfaces`; the brief already records it as absent |
| Marketing home has no intentional entry to the journeys index | MAJOR | `cohort-orientation-surfaces`. **Decided 2026-09-11** in the marketing brief — header destination plus a zone 7 entry — and deliberately not implemented, because the header is the navigation model and `site.toml` drives both sites' chrome. The review independently endorsed that two-placement answer and warned against folding the disciplines into `ThreeLoops`, which "would blur two distinct models" |
| Marketing home leads with a mechanism and a self-reported number strip rather than checkable proof | MAJOR | `cohort-orientation-surfaces`; the brief already specifies the replacement |
| Guides hub has no route back to the internal-case material | MAJOR | `cohort-orientation-surfaces`; the brief already requires it |
| Guides hub slips into persuasion register — `core` as "flagship", "most rigorous" | MINOR | `cohort-orientation-surfaces`; the brief forbids persuasion register on this surface |
| Marketing home copy button has an empty `catch {}` and no failure state | MINOR | `cohort-orientation-surfaces`; violates the quality floor's error-state requirement |

## What held up

Confirmed by the reviewer against the built output, not asserted:

- The four-discipline group reads as ordered: semantic `<ol>`, visible 1–4
  markers, DOM order matching visual order, explicit handoffs. Hiding the
  numerals from assistive technology does not erase ordered-list semantics.
- P2b is discoverable exactly when P2 is evaluated, and the `Nb` label is
  defensible — the conflicting selection rule was the problem, not the label.
- Focus: card links carry visible global `:focus-visible` outlines; sections use
  `aria-labelledby`.
- Contrast clears AA on the pairs inspected: amber `#8b5e0a` on `#f0efed` ≈ 4.9:1,
  docs accent `#4f7df0` on `#0c111c` ≈ 5.0:1.
- Motion respects preference: journey-card transitions are removed under
  `prefers-reduced-motion: reduce`.
