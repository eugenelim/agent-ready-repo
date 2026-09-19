---
type: evidence-manifest
surface: marketing site (web/) — /catalogue/
mode: retrofit
tier: production
date: 2026-09-18
---

# Evidence manifest — /catalogue/ ruled record lists

Covers one route and one change: `/catalogue/`'s three card grids converted to
ruled record lists. It closes the Major finding
[`marketing-home-retrofit.md`](marketing-home-retrofit.md) left open under
*known exceptions* — the route's `.outcome-card`, `.role-grid` and `.cat-card`
carried a tinted fill, a border and a radius against a direction sheet whose
Containment row reads "rules divide and rank; no cards, no tinted panels, no
shadows, no overlap".

**One name in that finding was wrong, and it propagated.** The class was
`.role-grid`, whose `a` children carried the fill, border and radius; the
earlier manifest recorded it as `.role-card` in the middle row of the
three-class table under its `/catalogue/` inspection finding, and the
`workspace.toml` entry, the request that commissioned this change, and this
change's own first draft all inherited that name. Two commands settle it, and
either alone is sufficient:
`git log -S "role-card" -- web/src/pages/catalogue/index.astro` returns no
commit, and `git show HEAD:web/src/pages/catalogue/index.astro | grep -c
role-card` returns 0. No such class ever existed on this route. Corrected here,
in `workspace.toml`, and at both places in the earlier manifest.

Every number below was measured on the build under test. Nothing is carried
forward from the earlier manifest's run; where a figure is compared with the
shipped homepage, that comparison was measured in the same session against the
same build.

## routes

One route: `/catalogue/`. The change touches no other emitted page.
`rg -n "outcome-card|role-grid|cat-card" web/src/` — the names the route
actually carried, not the misrecorded `.role-card` — returns exactly one hit:
`web/src/design-system.md:586`, a documentation reference this same change
authors, in the sentence recording what replaced those classes. No `.astro`,
`.ts` or `.css` file matches, so nothing else referenced them.

## viewports

Declared breakpoints for this surface: **640, 768, 1100**. Declared supported
minimum width: **320**. No breakpoint was discarded by the minimum.

Channels, as width predicates: `>=320 <640`, `>=640 <768`, `>=768 <1100`,
`>=1100`. These come from the declared breakpoints, not from the fallback
bands.

Captured at 320, 640, 768 and 1100 — every channel's lower bound — plus 390 and
1440, each at viewport heights 600 and 900, at rest and scrolled. The page is
scrollable at every one of them, so no `page-scrollable: no` was recorded.

640 was missing from the first pass, which left `>=640 <768` with no capture at
either height while this section claimed all four bounds were covered. It was
captured rather than recorded as a gap: 640x600 and 640x900 both report
`scrollWidth == innerWidth == 640` and a page height of 5,807 CSS px, and axe at
640 reports 0 violations.

## browsers

Chromium, the Playwright-managed build `playwright.config.ts` declares. This is
the engine the deploy gate is judged on. Firefox and WebKit were not re-run for
this change: it adds no feature outside Baseline Widely Available — one-dimension
flexbox, `border-top`, `text-decoration-thickness` and `scroll-margin-top` — and
the earlier manifest records the cross-engine layout parity run for this surface.

## states

All eighteen states are named below exactly once — **five exercised, thirteen
inapplicable** with a reason each. The count closes, so a state missing from
this section is a defect in the section rather than something a closing "the
rest are inapplicable" sentence can absorb. The table below holds six rows, not
five: `empty` is dispositioned in place rather than in the prose, because its
reason is about how these particular lists are built and belongs beside them.

11 + 1 + 1 inapplicable (the shared-reason group, `large-data-set`, `empty`)
plus 5 exercised = 18.

Eleven are inapplicable for one shared reason: the surface is a prerendered
static listing with no async fetch, no form, no mutation, no auth and no
client-side filter, so **loading**, **error**, **partial**, **success**,
**first-run**, **no-results**, **permission/denied**, **offline**, **blocked**,
**destructive-confirmation** and **disabled** have nothing to attach to — no
request can be in flight or fail, nothing is submitted, no identity is checked,
and there is no control that can be turned off.

**large-data-set** is inapplicable for a different reason, and the reason above
does not reach it: this surface does have a data set. All 22 packs render, none
is sliced, paginated or virtualised, and what that costs is measured under
*long-content* in the table. Nothing is dropped silently, which is the failure
the state exists to catch.

| State | Exercised? | Covered how |
| --- | --- | --- |
| content | yes | The normal state, captured at every channel and both heights |
| long-content | yes | 22 pack records in one column; the page is 7,539 CSS px at 320 and 5,662 at 1440 |
| high-zoom | yes | 320 CSS px is the 400%-zoom state of a 1280 viewport; no horizontal scroll |
| keyboard-only | yes | Every record is reachable by Tab; the browser gate asserts a contrasting ring on every focus stop on this route at 360 and 1440 |
| reduced-motion | yes | Vacuously covered, and deliberately: the change REMOVED the route's only transition (`.cat-card`'s `border-color`) and its `prefers-reduced-motion` guard with it. Nothing on the route animates, so there is no motion left to suppress |
| empty | no — inapplicable | Structurally so: both lists are driven by `catalogue-navigation.ts` constants and the `packs` content collection, and an empty pack collection fails the build before it renders |

## screenshots

Thirty-six captures under the session scratchpad: the matrix of twenty-four,
`<width>x<height>-{rest,scrolled}.png` at 320, 390, 640, 768, 1100 and 1440 by
heights 600 and 900; six full-page captures, one per matrix width; five region
captures of the roles and packs lists at 1440, 768 and 320; and one re-take of
1440 after the hero axis repair. Five fields recorded per matrix capture: route
`/catalogue/` (no query string, no fragment), viewport width, viewport height,
attained scroll offset, and `page-scrollable`.

6 widths x 2 heights x 2 scroll positions = 24, plus 6 + 5 + 1 = 36.

## inspection observations

**Result state: completed. Verdict: pass.**

- The outcome band now reads as the same component as the homepage's
  `.work-records`: serif titles, body-ink descriptions, underlined mono pack
  links, a hairline above each record and a boundary rule closing the list. Side
  by side with `/`, the two are one site.
- The ragged bottom edge is gone. Seven descriptions of unequal length in an
  `auto-fit` grid gave every row a different box height with a visible tint
  behind it; a record bounded by a rule ends where its content ends.
- No orphan at any count. The seventh outcome no longer sits alone in a
  part-width row, and the same holds for 22 packs at every captured width.
- **One defect found in the raster that no numeric gate saw, and fixed.** At
  1440 the hero's left axis measured 150 px while every band below it measured
  190 px — a 40 px break in the `[edge]` "one dominant left axis" commitment,
  appearing only above 1220 px. The hero's horizontal padding was outside its
  max-width wrapper rather than inside it. Repaired; re-measured at 1440, 1280,
  1100 and 320, aligned at all four. The homepage hero already measured 190,
  which is what established the correct value rather than a preference.
- The scope chip keeps a 2 px radius and a hairline outline. That is `StatusChip`,
  a shared primitive this change does not touch, and `[rectilinear]` form
  explicitly permits 2 px on fields and chips.

## a11y result

axe-core 4.13.0, tags `wcag2a wcag2aa wcag21a wcag21aa wcag22aa`, injected by
the same mechanism the repository's browser gate uses:

| Width | Violations |
| --- | --- |
| 390 | 0 |
| 640 | 0 |
| 1280 | 0 |

Manual checks:

- **2.5.8 Target Size (Minimum), AA — pass, two rows on the criterion itself and
  one on its spacing exception.** `.role-record__link` measures 686.4 x 58.4 and
  `.pack-record__link` 686.4 x 98.2, both over 24 x 24, and both preserve the
  whole-row target the card had. `.outcome-record__packs a` measures
  115.2 x 16.0 — under the floor, and identical to the shipped homepage links it
  copies, which measure 115.2 x 16.0. It passes on the spacing exception, which
  asks that 24 px circles centred on each target not intersect — that is,
  centres at least 24 px apart. Measured rather than reasoned: across all 46
  adjacent pairs in the seven pack rows, the closest two centres are **55.6 px**
  apart (`linear` and `figma`), then 59.2, 70.0 and 80.8. The vertical
  contribution is a 24 px line box plus the 8 px row gap, 32 px between wrapped
  rows; the horizontal is the 16 px column gap plus half of each label.
- **2.4.13 Focus Appearance (AAA enhancement, not AA baseline) — pass.** The
  global 2 px ring at 3 px offset from `base.css` is unchanged, and the browser
  gate's `expectEveryFocusStopHasContrastingRing` passes on this route at 360
  and 1440.
- **Stated WCAG 2.2 AA gap, not covered by the tag group above:** 2.4.11 Focus
  Not Obscured (Minimum), 2.5.7 Dragging Movements, 3.2.6 Consistent Help,
  3.3.7 Redundant Entry, 3.3.8 Accessible Authentication (Minimum). The last
  four have no surface here — no drag, no help affordance, no re-entered data,
  no authentication — but they are recorded as gap rather than as pass, because
  nothing measured them.
- **Safari list semantics — unverified, same instrument gap as before.** Every
  new `ul` carries `role="list"` and `list-semantics.test.ts` holds it open from
  the emitted HTML, but the behaviour the role exists for cannot be observed in
  any engine available here.

Contrast, measured in Chromium against the composited ground rather than read
off the token file:

| Pairing | Ratio | Floor | |
| --- | ---: | ---: | --- |
| outcome title | 15.85:1 | 3 | pass |
| outcome description | 12.09:1 | 4.5 | pass |
| outcome pack link | 15.85:1 | 4.5 | pass |
| role name | 15.85:1 | 4.5 | pass |
| role destination field | 4.89:1 | 4.5 | pass |
| pack name | 17.16:1 | 3 | pass |
| pack tagline | 13.09:1 | 4.5 | pass |
| pack skill-count field | 5.30:1 | 4.5 | pass |
| scope chip label | 13.09:1 | 4.5 | pass |
| outcome list boundary rules | 3.26:1 | 3 | pass |
| role list boundary rules | 3.26:1 | 3 | pass |
| pack list boundary rules | 3.53:1 | 3 | pass |

Inter-record hairlines measure **1.89:1** on `--ds-surface-alt` and **2.05:1** on
`--ds-surface`, which does not clear 3:1, and that is recorded here rather than
argued away. It is not owed on these rules: `--ds-rule-hairline` divides records
that space and type already separate, so no information depends on it and it is
never the sole carrier of a state or of a control's edge. The list edges that do
carry the non-text obligation use `--ds-rule-boundary` and clear it at 3.26 and
3.53. The shipped `PackCatalogue.astro` and `WhatYouInstall.astro` make the
identical pairing and measure identically — 2.05 and 1.89 — so this matches the
adjudicated treatment rather than relaxing it.

One unreconciled contradiction, named rather than leaned on: `tokens.css:116`
annotates `--ds-rule-hairline` "non-text contrast floor", the same annotation
`--ds-rule-boundary` carries on the next line, while the token measures below
that floor. ("Decorative only" belongs to a different token,
`--ds-rule-hairline-dk`, which this route does not use.) That annotation predates
this page and governs three components; reconciling it is not this change's to
make, and nothing above rests on it.

## perf result

**CWV unmeasured, and localhost timings are not a CWV measurement.** What is
measurable here is payload: the change removes CSS and adds none, emits no new
request, and ships no script. Page height at 320 is 7,539 CSS px. Field data
needs 28 days after deploy, which is the same trigger the earlier manifest
records.

## console/network result

No page or console errors on `/catalogue/` at any captured width — asserted by
`collectPageErrors` in the browser gate, which passes on this route at all five
gate widths. No third-party requests; the route loads only same-origin CSS and
fonts.

## analytics events

None. This surface fires no measurement event and the change adds none.

## known exceptions

| Exception | Status |
| --- | --- |
| **Flagship ranking not carried to this route** | **Open, deliberate, owner decision.** `catalogue-navigation.ts` marks `build` as `flagship`, and the homepage ranks it with a 2 px ink rule. `/catalogue/` has never ranked it and this change does not start: adding rank is a content decision, not a restyle. The two surfaces therefore disagree about whether an outcome is ranked. |
| **The `forWhom` audience line is absent from this route** | **Open, deliberate.** The homepage record carries it; `/catalogue/` carries `cataloguePromise` instead and never showed `forWhom`. A restyle keeps content, it does not import it. |
| **Inter-record hairlines below 3:1** | **Accepted, matching the shipped treatment.** Rationale and measurements under *a11y result*. |
| **`StatusChip` outline at 2.05:1** | **Pre-existing, unchanged, not a sole channel.** The chip's label carries the information at 13.09:1. The primitive is shared across surfaces and out of this change's scope. |
| **11 stylelint errors** | **Pre-existing, registered.** All in `src/pages/direction-preview.astro`, all off-scale font sizes, already logged in `workspace.toml` `[backlog].open` pending a scale decision. This change adds none. |

## unverified items

| Item | Why |
| --- | --- |
| Core Web Vitals | No field data; localhost is not a measurement. Unblocks 28 days after deploy. |
| Safari / VoiceOver list semantics | Same instrument gap the earlier manifest records: Playwright 1.63 removed `page.accessibility`, and `ariaSnapshot` returns the same DOM-derived answer in every engine. Needs real Safari with VoiceOver. |
| Firefox and WebKit rendering | Not re-run for this change. No feature outside Baseline Widely Available is introduced. |

## security/privacy review status

**Not applicable, with a reason rather than a blank.** The surface takes no user
input, stores nothing, sets no cookie, reads no credential and makes no
third-party call. The change is markup and CSS on a statically generated page
whose content comes from repository constants and a build-time content
collection. No trust boundary, data flow or guarding control is touched, so
`security-reviewer` is not triggered by this diff.

## reliability/recovery status

**Not applicable at this surface's failure model.** There is no request to fail:
the page is prerendered and served as static HTML, so it has no error path, no
retry and no runtime dependency to lose. Availability is the hosting platform's,
not this surface's. No SLO or alerting owner is claimed for it, and none is
implied.
