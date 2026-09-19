---
type: evidence-manifest
surface: marketing site (web/)
mode: retrofit
tier: production
date: 2026-09-18
---

# Evidence manifest — paper-first editorial retrofit

Covers the retrofit through its closing stage, 2026-09-18: the `/now/` surface
restyle, the `frontend-engineering` GATES phase over the marketing site, and
the two-phase close-out that moved "Own the catalogue" to a light band, ran
forced-colors and WebKit, rendered the `/now/` empty state, fixed the hero's
rule measure, extended the capture matrix to `/now/` and `/catalogue/`, and
turned §1 of `design-system.md` into a projection of `tokens.css`.

A third stage, same day, closed the cheap verification gaps the close-out left:
Firefox, the reduced-motion / print / hover-active state captures, the capture
matrix on the last three routes, a re-take of the `/now/` and `/catalogue/`
matrices at the band lower bounds they should have used, and Gate 3, which is
now a configured, mutation-checked stylelint run rather than a named skip.

Twelve base fields plus the two production fields. Every number below was
measured on the build under test; nothing is carried forward from an earlier
run. Where a figure was superseded by the close-out it has been replaced, not
appended to.

## routes

Six routes were exercised:

| route | gate 1 (HTML) | gate 2 (axe) | gate 4 (16-capture matrix) |
| --- | --- | --- | --- |
| `/` | run | run | run |
| `/catalogue/` | run | run | run (re-taken at the band lower bounds) |
| `/packs/core/` | run | run | run |
| `/journeys/core/` | run | run | run |
| `/now/` | run | run | run (re-taken at the band lower bounds) |
| `/404` (`404.html`) | run | run | run |

Routes are recorded with the query string and fragment stripped. Every capture
resolved to `/agent-ready-repo/` — the deployment's base path, not a bare `/`.

## viewports

Channels are width predicates derived from the site's canonical breakpoints,
not from a fallback band set.

| channel | width predicate | capture width |
| --- | --- | --- |
| 1 | `>=320 <640` | 320 |
| 2 | `>=640 <768` | 640 |
| 3 | `>=768 <1100` | 768 |
| 4 | `>=1100` | 1100 |

- **Source:** declared breakpoints. 640, 768 and 1100 are the site's canonical
  breakpoints; they were not invented for this run.
- **Supported minimum in force:** 320.
- **Breakpoints the minimum discarded:** none. No declared breakpoint sits
  below 320, so the supported minimum removed no band and the four channels are
  the complete partition of the width axis.

**Every matrix capture is at its band's lower bound** — 320, 640, 768, 1100.
That is where a breakpoint defect shows, and it is the rule for all six routes.

The `/now/` and `/catalogue/` matrices did not originally meet it: they ran at
the interior widths 390, 700, 900 and 1280. The widths were checked against
this table and did not match, so **both matrices were re-taken** at 320, 640,
768 and 1100 and the tables below are the re-takes. The interior-width run is
not retained; an interior width is a valid sample of its channel but it is not
the sample this field specifies, and keeping both would leave two answers to
one question.

Two interior-width captures are kept deliberately and are labelled as such:
`s4_now_1440.png` and the four `cat-mid-*` captures, which exist to reach
content no lower-bound at-rest or scrolled-to-bottom capture lands on.

Axe ran at 390 and 1280, which fall in channels 1 and 4.

## browsers

**Three engines**, all Playwright-managed builds from
`~/Library/Caches/ms-playwright`, driven through `playwright-core` 1.63.0:

- **Chromium** (`HeadlessChrome/153.0.8010.12`). All gates, every matrix, axe,
  forced-colors, the three state captures.
- **WebKit** (`AppleWebKit/605.1.15`, `Version/26.6 Safari/605.1.15`),
  installed for this run via `npx playwright install webkit`. `/` was loaded at
  390 and 1280 and compared with Chromium element by element.
- **Firefox 155.0** (`Gecko/20100101 Firefox/155.0`, playwright build v1543),
  installed for this run via `npx playwright install firefox` — 104.3 MiB,
  downloaded without error. `/`, `/catalogue/` and `/now/` were loaded at 390
  and 1280 and compared with Chromium element by element.

**WebKit result — layout parity.** Thirteen elements spanning the nav, hero,
transcript figure, terminal, outcome list, receipt, close band and footer were
measured in both engines at both widths. Every `x`, `y` and `width` agrees
within 0.1 CSS px. The only differences anywhere are a **1.9 px** shorter
`.terminal` in WebKit — sub-pixel rounding in the tab/panel stack — and the
2 px of document height that follows from it: 10156 against 10158 at 390, and
7718 against 7720 at 1280. `scrollWidth === clientWidth` in both engines at
both widths, so there is no horizontal overflow in either. The same font files
resolve in both (`Newsreader Variable`, `Inter Variable`, `JetBrains Mono`).

**What WebKit could NOT settle, and why — see *unverified items*.** The
`<ul role="list">` workaround exists for Safari's accessibility behaviour, and
that behaviour was **not** confirmed, because Playwright removed
`page.accessibility` in 1.63.0 — `typeof page.accessibility` is `undefined`.
What remains is `ariaSnapshot`, which is Playwright's own ARIA computation over
the DOM and returns the same answer in every engine, so it cannot see an
engine-specific AX mapping; and WebKit's `window.internals` is absent from the
Playwright build. The workaround is therefore still held on the documented
Safari behaviour, not on a measurement taken here. Layout parity is measured;
AX-tree parity is not.

**Firefox result — layout parity.** Twenty-three elements on `/` and
thirteen each on `/catalogue/` and `/now/` — nav, hero, transcript figure,
terminal, tab panel, outcome list, receipt, adapter table, close band, footer,
card grids and release records — were measured in both engines at both widths,
six route/width combinations in all.

- **`x` and `width` agree everywhere.** The largest disagreement on either axis
  is **0.4 CSS px** (`.org` and `.units__list` widths at 1280). No element is
  positioned or sized differently.
- **No horizontal overflow in either engine.** `scrollWidth === clientWidth` in
  all twelve measurements: 390/390 and 1280/1280 on every route.
- **Document height agrees to within 0.16%.** `/` 10158 against 10195 at 390
  and 7720 against 7719 at 1280; `/catalogue/` 9718/9702 and 5182/5173;
  `/now/` 62238/62287 and 35438/35444. The largest absolute gap, 49 px, is on
  the 62,238 px `/now/` document.
- **`y` drift is cumulative, not structural.** Firefox rounds each block's
  height a fraction differently, so an element's `y` drifts further down the
  document: 0 px in the nav and hero, 36.8 px at the `/` footer at 390, 48.1 px
  at the `/now/` footer at 390. Within one section the drift is flat, which is
  what a rounding accumulation looks like rather than a layout difference.
- **Two real differences, both the same ones WebKit showed.** `.terminal` and
  `.tabs__panels` are **2 px shorter** in Firefox at both widths — line-box
  rounding on the two terminal lines. `.outcome-card` on `/catalogue/` is 2 px
  shorter, and the heading `y` inside `.cat-hero` and `.now-hero` sits 1.2 px
  higher.

**What the raster shows, beyond the numbers.** Element-level captures of
`.terminal`, `.hero__figure`, `.adapters__table`, `.receipt`, `.nav__inner` and
`.outcome-card` were taken in both engines and compared by eye. The terminal's
tab row, active-tab underline, prompt glyphs and monospace lines are the same
in both; the 2 px is leading, not a missing or shifted element. The
`/catalogue/` card grid, the role cards, the skill chips and the arrow glyphs
render identically. The only visible difference anywhere is **text
rasterisation**: Firefox's glyph antialiasing is very slightly heavier, which
is a platform font-smoothing difference and not a layout or styling one. No
clipping, no reflow, no missing rule, no colour shift.

**Same instrument limit as WebKit.** Firefox settles layout, not AX-tree
mapping — Playwright 1.63.0 exposes no accessibility API in any engine. See
*unverified items* for Safari's list semantics, which Firefox cannot settle
either.

## states

Of the 18-state matrix, **13 were exercised** and 5 were not. Two moved across
in the close-out (`empty` and `forced-colors`) and three in this stage
(`reduced-motion`, `print`, `hover`/`active`). **Every applicable state has now
been exercised**; the five that remain have no rendered representation on a
static surface with no fetching and no form controls.

Exercised: default/at-rest; scrolled; short viewport (600 CSS px); tall viewport
(900 CSS px); keyboard-focus (every focusable element on 7 route/width
combinations); disclosure-collapsed and disclosure-expanded (the mobile nav
`<details>` drawer, measured in both); populated-with-real-data (the `/now/`
list renders 122 real releases from the committed projection); **empty**;
**forced-colors**; **reduced-motion**; **print**; and **hover** / **active**.

**empty — `/now/` with no released highlights.** The live projection carries 122
releases, so the route cannot take that branch on its own. It was rendered by
stubbing `groups` to `[]` in `web/src/lib/now-highlights.generated.json`,
building, measuring, and then restoring the projection. **No stub shipped**:
that file is gitignored (`.gitignore:146`), the npm `prebuild` hook regenerates
it from the changelog on every build, and the restored file carries 122 groups
again. Results under *inspection observations*.

**forced-colors.** Chromium's `forced-colors: active` emulation on `/` and
`/now/` at 390 and 1280. Results and the two repairs it produced are under
*a11y result*.

**reduced-motion — three arms on `/` at 390 and 1280, six runs.** The guard in
`Hero.astro` is a `prefers-reduced-motion: no-preference` wrapper, not a
`reduce` opt-out, so the default with no media support at all had to be checked
as well as `reduce`. Arm C models that UA by rewriting the media feature name
in the served CSS to one no engine knows: an unknown media feature never
matches, which is what a non-supporting UA does with `no-preference`.

| arm | `.hero__inner` opacity at first paint | `animation-name` | animations on the document after settle |
| --- | --- | --- | --- |
| A — no override (control) | **0.191** | `hero-fade` | 1, then `finished` |
| B — `reduce` | 1 | `none` | 0 |
| C — no media support at all | 1 | `none` | 0 |

Arm A is the control that makes the other two mean something: the fade demonstrably
runs, caught mid-flight at 19% opacity, so arms B and C are the guard working and
not the animation being absent. In both B and C the hero is at **opacity 1 from
the first paint** — no animation is created, so there is nothing to interrupt and
nothing to leave stranded.

**Nothing is left at opacity 0.** A sweep of every laid-out element on the page
returns the same four in all three arms: the `.tabs__radio` inputs, which are
the 1×1 px visually-hidden radios driving the CSS-only install tabs. They are
`opacity: 0` in the default arm too, so they are the standard hiding pattern,
not content the guard stranded.

**One thing the sweep found that the numbers alone would not.** The site uses
two motion patterns. `Hero.astro`'s opacity fade and `SiteNav.astro`'s burger
`transform` — the two motion-bearing rules — use the `no-preference` wrapper,
so both are off under arm C. Every other transition (`.copy-btn`, `.cat-card`,
`.journey-link`, `.btn-primary`, `.btn-ghost`) uses a `reduce` opt-out and
therefore survives arm C. That split is coherent rather than a defect: the
surviving transitions are ≤0.2 s **colour and border-colour only**, with no
transform and no movement, so they are outside what a motion preference is for.
Recorded so the next reader does not "fix" one pattern into the other.

**print — Chromium `emulateMedia({media:'print'})` on `/` at 390 and 1280,
plus a full A4 paginated model.** `matchMedia('print').matches` was confirmed
true. Pagination was modelled at Chromium's own A4 print box — 717 × 1045 CSS
px, A4 at 96 dpi less the default 0.4 in margins — and each page band captured.

- **There is no print stylesheet.** Zero `@media print` rules and zero `@page`
  rules in the marketing site's CSS. Everything below follows from that.
- **The page is 9 A4 sheets.**
- **The dark footer costs 0.82 of a sheet in solid ink.** `.footer` is
  717 × 859 CSS px of `#14120f`, starting part-way down sheet 8 and filling
  sheet 9. With "Background graphics" on, that is most of two sheets running
  near-black.
- **With backgrounds off — the print dialog's default — the footer very nearly
  disappears.** The ground drops to white but the text colours do not change:
  the brand and column labels are `#DCD8CE` at **1.42:1** on white, the links
  `#B8B2A6` at **2.11:1**, the copyright `#938D82` at **3.30:1**. All three
  fail 4.5:1; the first is effectively invisible. On the dark ground they
  measure 13.14:1, 8.87:1 and 5.67:1, so the colours are right for the screen
  and wrong for the only sheet a reader is likely to print.
- **Links lose their targets.** 64 links on `/`, 2 of them off-site, and no
  rule exposes `attr(href)` in print. A printed page carries 64 underlined
  phrases that point nowhere.
- **Screen-only chrome prints.** The nav prints with the hamburger glyph
  (22 × 2 px of bar, `display: block`) because the A4 print width of 717 px is
  below the 768 breakpoint, so paper gets the mobile nav. The "Copy install
  commands" button prints as a button.
- **Three of the four install variants are lost.** The tab panel is a CSS-only
  radio control, so `With discovery`, `Full inception` and `Solution architect`
  are `display: none` on paper. Only `Flagship loop` prints.
- **Seven of the eight page breaks cut through a block.** Nothing declares
  `break-inside: avoid`. Sheet 2 splits an `li.actor` mid-description, 3 splits
  a `.unit`, 4 and 5 each split a `.work-record`, 6 splits `.adapters__table`
  mid-row so the remaining rows carry no header, 7 orphans `h2.org__headline`
  from its body, and 8 splits a list item. Only the sheet-1 break lands in
  whitespace.

None of this is a WCAG failure and none of it is new damage — it is the
untouched consequence of never having written a print stylesheet, which the
close-out recorded as unexercised rather than absent. It is now measured. The
remedy is a design decision and is **not** made here.

**hover / active — every interactive element class, all six routes, 390 and
1280.** Twenty-eight distinct classes were enumerated from `a[href]`, `button`,
`input`, `select`, `textarea`, `summary`, `[tabindex]` and `label[for]`, and
each was sampled at rest, under a real pointer hover, under a real pointer
press, and under `:focus-visible` with keyboard as the last input modality.
Transitions were frozen with `reduce` so every sample is a settled value.

- **Every one of the 28 has a focus style. 28 of 28** move `outline-style` from
  `none` to `solid` under `:focus-visible`. There is no class whose hover is a
  style the keyboard never gets.
- **No hover state is the sole carrier of meaning. 12 of 28** change on hover;
  every one of those 12 changes only `color`, `background-color`,
  `border-color` or `text-decoration-color`. Not one changes `::before` or
  `::after` content, reveals a hidden child, or alters `transform` or
  `opacity` — so nothing is disclosed on hover that a keyboard or touch reader
  cannot reach. The affordance itself is carried at rest by the `:where(a)`
  underline baseline or by the button's fill and border.
- **`:active` is never distinguished from `:hover`. 0 of 28** classes have an
  active delta that differs from their hover delta, so a pointer user gets no
  press feedback distinct from the pre-press state. Finding class: a missing
  state, not a broken one. **Severity: Minor** — no WCAG criterion requires a
  press state and every control still shows hover and focus. Recorded, not
  fixed: adding one is a design decision.
- **One expected non-match.** `label.tabs__label` reports
  `:focus-visible` false because a `<label>` is not focusable. It still shows
  an indicator, through `.tabs__radio:focus-visible + .tabs__label`, which is
  the rule that produced its `outline-offset: -2px`. Correct as built.

Not exercised, with the reason: loading, error, disabled and pressed. This
surface is static HTML with no client-side data fetching and no form controls,
so none of the four has a rendered representation to exercise. That is the
whole remainder of the 18-state matrix.

## screenshots

**One hundred and seventy-two captures and two PDFs**, all in the session
scratchpad
(`/private/tmp/claude-501/-Users-<user>-orca-workspaces-agent-ready-repo-marketing-work/f785c095-4962-4d5c-a91d-4d673099e457/scratchpad/`).

The 16-capture matrix on `/`. Every capture carries all five required fields;
none is missing a field, so none is unusable.

| file | route | vw | vh | scroll attained | page-scrollable (asked of the page) |
| --- | --- | --- | --- | --- | --- |
| `s4_home_c320_short_atrest.png` | `/agent-ready-repo/` | 320 | 600 | 0 | true |
| `s4_home_c320_short_scrolled.png` | `/agent-ready-repo/` | 320 | 600 | 6466 | true |
| `s4_home_c320_tall_atrest.png` | `/agent-ready-repo/` | 320 | 900 | 0 | true |
| `s4_home_c320_tall_scrolled.png` | `/agent-ready-repo/` | 320 | 900 | 6286 | true |
| `s4_home_c640_short_atrest.png` | `/agent-ready-repo/` | 640 | 600 | 0 | true |
| `s4_home_c640_short_scrolled.png` | `/agent-ready-repo/` | 640 | 600 | 4987 | true |
| `s4_home_c640_tall_atrest.png` | `/agent-ready-repo/` | 640 | 900 | 0 | true |
| `s4_home_c640_tall_scrolled.png` | `/agent-ready-repo/` | 640 | 900 | 4807 | true |
| `s4_home_c768_short_atrest.png` | `/agent-ready-repo/` | 768 | 600 | 0 | true |
| `s4_home_c768_short_scrolled.png` | `/agent-ready-repo/` | 768 | 600 | 4838 | true |
| `s4_home_c768_tall_atrest.png` | `/agent-ready-repo/` | 768 | 900 | 0 | true |
| `s4_home_c768_tall_scrolled.png` | `/agent-ready-repo/` | 768 | 900 | 4658 | true |
| `s4_home_c1100_short_atrest.png` | `/agent-ready-repo/` | 1100 | 600 | 0 | true |
| `s4_home_c1100_short_scrolled.png` | `/agent-ready-repo/` | 1100 | 600 | 4238 | true |
| `s4_home_c1100_tall_atrest.png` | `/agent-ready-repo/` | 1100 | 900 | 0 | true |
| `s4_home_c1100_tall_scrolled.png` | `/agent-ready-repo/` | 1100 | 900 | 4058 | true |

`page-scrollable` was read from the page (`scrollHeight > clientHeight`), not
inferred from whether a scroll succeeded. Scrolled captures targeted 60% of the
scrollable range; the attained position above is what the page reported after
the scroll settled, not the target.

### The 16-capture matrix on `/now/` — re-taken at the band lower bounds

**Superseded.** The first run of this matrix used 390/700/900/1280. Those are
interior widths, not the band lower bounds this manifest's *viewports* field
specifies, so the matrix was re-taken at 320/640/768/1100 and the table below
replaces it. All five required fields per capture. `page-scrollable` was
**asked of the page** (`scrollHeight > clientHeight`), not inferred; `scroll
attained` is what the page reported after the scroll settled, and every
scrolled capture reached its 60%-of-range target exactly.

| file | route | vw | vh | scroll attained | page-scrollable |
| --- | --- | --- | --- | --- | --- |
| `mx_now_c320_short_atrest.png` | `/agent-ready-repo/now/` | 320 | 600 | 0 | true |
| `mx_now_c320_short_scrolled.png` | `/agent-ready-repo/now/` | 320 | 600 | 44784 | true |
| `mx_now_c320_tall_atrest.png` | `/agent-ready-repo/now/` | 320 | 900 | 0 | true |
| `mx_now_c320_tall_scrolled.png` | `/agent-ready-repo/now/` | 320 | 900 | 44604 | true |
| `mx_now_c640_short_atrest.png` | `/agent-ready-repo/now/` | 640 | 600 | 0 | true |
| `mx_now_c640_short_scrolled.png` | `/agent-ready-repo/now/` | 640 | 600 | 26599 | true |
| `mx_now_c640_tall_atrest.png` | `/agent-ready-repo/now/` | 640 | 900 | 0 | true |
| `mx_now_c640_tall_scrolled.png` | `/agent-ready-repo/now/` | 640 | 900 | 26419 | true |
| `mx_now_c768_short_atrest.png` | `/agent-ready-repo/now/` | 768 | 600 | 0 | true |
| `mx_now_c768_short_scrolled.png` | `/agent-ready-repo/now/` | 768 | 600 | 25476 | true |
| `mx_now_c768_tall_atrest.png` | `/agent-ready-repo/now/` | 768 | 900 | 0 | true |
| `mx_now_c768_tall_scrolled.png` | `/agent-ready-repo/now/` | 768 | 900 | 25296 | true |
| `mx_now_c1100_short_atrest.png` | `/agent-ready-repo/now/` | 1100 | 600 | 0 | true |
| `mx_now_c1100_short_scrolled.png` | `/agent-ready-repo/now/` | 1100 | 600 | 21226 | true |
| `mx_now_c1100_tall_atrest.png` | `/agent-ready-repo/now/` | 1100 | 900 | 0 | true |
| `mx_now_c1100_tall_scrolled.png` | `/agent-ready-repo/now/` | 1100 | 900 | 21046 | true |

### The 16-capture matrix on `/catalogue/` — re-taken at the band lower bounds

Same correction, same reason: the first run used 390/700/900/1280.

| file | route | vw | vh | scroll attained | page-scrollable |
| --- | --- | --- | --- | --- | --- |
| `mx_catalogue_c320_short_atrest.png` | `/agent-ready-repo/catalogue/` | 320 | 600 | 0 | true |
| `mx_catalogue_c320_short_scrolled.png` | `/agent-ready-repo/catalogue/` | 320 | 600 | 6150 | true |
| `mx_catalogue_c320_tall_atrest.png` | `/agent-ready-repo/catalogue/` | 320 | 900 | 0 | true |
| `mx_catalogue_c320_tall_scrolled.png` | `/agent-ready-repo/catalogue/` | 320 | 900 | 5970 | true |
| `mx_catalogue_c640_short_atrest.png` | `/agent-ready-repo/catalogue/` | 640 | 600 | 0 | true |
| `mx_catalogue_c640_short_scrolled.png` | `/agent-ready-repo/catalogue/` | 640 | 600 | 4595 | true |
| `mx_catalogue_c640_tall_atrest.png` | `/agent-ready-repo/catalogue/` | 640 | 900 | 0 | true |
| `mx_catalogue_c640_tall_scrolled.png` | `/agent-ready-repo/catalogue/` | 640 | 900 | 4415 | true |
| `mx_catalogue_c768_short_atrest.png` | `/agent-ready-repo/catalogue/` | 768 | 600 | 0 | true |
| `mx_catalogue_c768_short_scrolled.png` | `/agent-ready-repo/catalogue/` | 768 | 600 | 3392 | true |
| `mx_catalogue_c768_tall_atrest.png` | `/agent-ready-repo/catalogue/` | 768 | 900 | 0 | true |
| `mx_catalogue_c768_tall_scrolled.png` | `/agent-ready-repo/catalogue/` | 768 | 900 | 3212 | true |
| `mx_catalogue_c1100_short_atrest.png` | `/agent-ready-repo/catalogue/` | 1100 | 600 | 0 | true |
| `mx_catalogue_c1100_short_scrolled.png` | `/agent-ready-repo/catalogue/` | 1100 | 600 | 2714 | true |
| `mx_catalogue_c1100_tall_atrest.png` | `/agent-ready-repo/catalogue/` | 1100 | 900 | 0 | true |
| `mx_catalogue_c1100_tall_scrolled.png` | `/agent-ready-repo/catalogue/` | 1100 | 900 | 2534 | true |

### The 16-capture matrix on `/packs/core/`

| file | route | vw | vh | scroll attained | page-scrollable |
| --- | --- | --- | --- | --- | --- |
| `mx_packs-core_c320_short_atrest.png` | `/agent-ready-repo/packs/core/` | 320 | 600 | 0 | true |
| `mx_packs-core_c320_short_scrolled.png` | `/agent-ready-repo/packs/core/` | 320 | 600 | 1591 | true |
| `mx_packs-core_c320_tall_atrest.png` | `/agent-ready-repo/packs/core/` | 320 | 900 | 0 | true |
| `mx_packs-core_c320_tall_scrolled.png` | `/agent-ready-repo/packs/core/` | 320 | 900 | 1411 | true |
| `mx_packs-core_c640_short_atrest.png` | `/agent-ready-repo/packs/core/` | 640 | 600 | 0 | true |
| `mx_packs-core_c640_short_scrolled.png` | `/agent-ready-repo/packs/core/` | 640 | 600 | 1244 | true |
| `mx_packs-core_c640_tall_atrest.png` | `/agent-ready-repo/packs/core/` | 640 | 900 | 0 | true |
| `mx_packs-core_c640_tall_scrolled.png` | `/agent-ready-repo/packs/core/` | 640 | 900 | 1064 | true |
| `mx_packs-core_c768_short_atrest.png` | `/agent-ready-repo/packs/core/` | 768 | 600 | 0 | true |
| `mx_packs-core_c768_short_scrolled.png` | `/agent-ready-repo/packs/core/` | 768 | 600 | 1202 | true |
| `mx_packs-core_c768_tall_atrest.png` | `/agent-ready-repo/packs/core/` | 768 | 900 | 0 | true |
| `mx_packs-core_c768_tall_scrolled.png` | `/agent-ready-repo/packs/core/` | 768 | 900 | 1022 | true |
| `mx_packs-core_c1100_short_atrest.png` | `/agent-ready-repo/packs/core/` | 1100 | 600 | 0 | true |
| `mx_packs-core_c1100_short_scrolled.png` | `/agent-ready-repo/packs/core/` | 1100 | 600 | 977 | true |
| `mx_packs-core_c1100_tall_atrest.png` | `/agent-ready-repo/packs/core/` | 1100 | 900 | 0 | true |
| `mx_packs-core_c1100_tall_scrolled.png` | `/agent-ready-repo/packs/core/` | 1100 | 900 | 797 | true |

### The 16-capture matrix on `/journeys/core/`

| file | route | vw | vh | scroll attained | page-scrollable |
| --- | --- | --- | --- | --- | --- |
| `mx_journeys-core_c320_short_atrest.png` | `/agent-ready-repo/journeys/core/` | 320 | 600 | 0 | true |
| `mx_journeys-core_c320_short_scrolled.png` | `/agent-ready-repo/journeys/core/` | 320 | 600 | 11398 | true |
| `mx_journeys-core_c320_tall_atrest.png` | `/agent-ready-repo/journeys/core/` | 320 | 900 | 0 | true |
| `mx_journeys-core_c320_tall_scrolled.png` | `/agent-ready-repo/journeys/core/` | 320 | 900 | 11218 | true |
| `mx_journeys-core_c640_short_atrest.png` | `/agent-ready-repo/journeys/core/` | 640 | 600 | 0 | true |
| `mx_journeys-core_c640_short_scrolled.png` | `/agent-ready-repo/journeys/core/` | 640 | 600 | 7754 | true |
| `mx_journeys-core_c640_tall_atrest.png` | `/agent-ready-repo/journeys/core/` | 640 | 900 | 0 | true |
| `mx_journeys-core_c640_tall_scrolled.png` | `/agent-ready-repo/journeys/core/` | 640 | 900 | 7574 | true |
| `mx_journeys-core_c768_short_atrest.png` | `/agent-ready-repo/journeys/core/` | 768 | 600 | 0 | true |
| `mx_journeys-core_c768_short_scrolled.png` | `/agent-ready-repo/journeys/core/` | 768 | 600 | 7454 | true |
| `mx_journeys-core_c768_tall_atrest.png` | `/agent-ready-repo/journeys/core/` | 768 | 900 | 0 | true |
| `mx_journeys-core_c768_tall_scrolled.png` | `/agent-ready-repo/journeys/core/` | 768 | 900 | 7274 | true |
| `mx_journeys-core_c1100_short_atrest.png` | `/agent-ready-repo/journeys/core/` | 1100 | 600 | 0 | true |
| `mx_journeys-core_c1100_short_scrolled.png` | `/agent-ready-repo/journeys/core/` | 1100 | 600 | 7348 | true |
| `mx_journeys-core_c1100_tall_atrest.png` | `/agent-ready-repo/journeys/core/` | 1100 | 900 | 0 | true |
| `mx_journeys-core_c1100_tall_scrolled.png` | `/agent-ready-repo/journeys/core/` | 1100 | 900 | 7168 | true |

### The 16-capture matrix on `/404`

The route is recorded as `/agent-ready-repo/404.html` — the file the static
server resolves. Query string and fragment are stripped, as on every other row.

| file | route | vw | vh | scroll attained | page-scrollable |
| --- | --- | --- | --- | --- | --- |
| `mx_404_c320_short_atrest.png` | `/agent-ready-repo/404.html` | 320 | 600 | 0 | true |
| `mx_404_c320_short_scrolled.png` | `/agent-ready-repo/404.html` | 320 | 600 | 607 | true |
| `mx_404_c320_tall_atrest.png` | `/agent-ready-repo/404.html` | 320 | 900 | 0 | true |
| `mx_404_c320_tall_scrolled.png` | `/agent-ready-repo/404.html` | 320 | 900 | 427 | true |
| `mx_404_c640_short_atrest.png` | `/agent-ready-repo/404.html` | 640 | 600 | 0 | true |
| `mx_404_c640_short_scrolled.png` | `/agent-ready-repo/404.html` | 640 | 600 | 511 | true |
| `mx_404_c640_tall_atrest.png` | `/agent-ready-repo/404.html` | 640 | 900 | 0 | true |
| `mx_404_c640_tall_scrolled.png` | `/agent-ready-repo/404.html` | 640 | 900 | 331 | true |
| `mx_404_c768_short_atrest.png` | `/agent-ready-repo/404.html` | 768 | 600 | 0 | true |
| `mx_404_c768_short_scrolled.png` | `/agent-ready-repo/404.html` | 768 | 600 | 511 | true |
| `mx_404_c768_tall_atrest.png` | `/agent-ready-repo/404.html` | 768 | 900 | 0 | true |
| `mx_404_c768_tall_scrolled.png` | `/agent-ready-repo/404.html` | 768 | 900 | 331 | true |
| `mx_404_c1100_short_atrest.png` | `/agent-ready-repo/404.html` | 1100 | 600 | 0 | true |
| `mx_404_c1100_short_scrolled.png` | `/agent-ready-repo/404.html` | 1100 | 600 | 272 | true |
| `mx_404_c1100_tall_atrest.png` | `/agent-ready-repo/404.html` | 1100 | 900 | 0 | true |
| `mx_404_c1100_tall_scrolled.png` | `/agent-ready-repo/404.html` | 1100 | 900 | 92 | true |

**All 80 captures across the five matrices completed.** No navigation failed,
no capture failed, no capture is missing a field, and on every one of the 80
`scrollWidth === clientWidth` — there is no horizontal overflow at any width on
any of the five routes. On every scrolled capture the position **attained**
equals the position targeted, so no scroll was silently short.

Each route's at-rest captures land on the hero, so four mid-page captures were
added — `cat-mid-390x900.png`, `cat-mid-700x900.png`, `cat-mid-900x600.png`,
`cat-mid-1280x900.png` — to judge the card grids, which no at-rest or
scrolled-to-bottom capture reaches. These are the two interior-width captures
the *viewports* field keeps on purpose; they supplement the lower-bound
matrix, they do not stand in for it.

Six supporting captures:

| file | what it shows |
| --- | --- |
| `s4_now_1440.png` | `/now/` at 1440x1000, scrolled to the record list — the Part 1 restyle |
| `s4_now_320.png` | `/now/` at 320x900, scrolled to the record list — the restyle at the supported minimum |
| `now-empty-320.png` | `/now/` **empty state** at 320, projection stubbed to zero groups |
| `now-empty-1440.png` | `/now/` **empty state** at 1440, same stub |
| `diag_focus_cta.png` | `.hero__cta--primary` focused: ink ring, 3px paper gap, ink fill |
| `diag_focus_orgcta.png` | `.org__cta` focused: ink ring on paper. **Re-taken** — this capture previously showed a paper ring on the dark close band, and that band is no longer dark. |

### Cross-browser and state captures

| set | count | what it holds |
| --- | --- | --- |
| `ff/chromium_*`, `ff/firefox_*` | 24 | `/`, `/catalogue/` and `/now/` at 390 and 1280, at the fold and at 35% scroll, in both engines — the pairs the Firefox parity read is taken from |
| `ff/el_chromium_*`, `ff/el_firefox_*` | 12 | element-level pairs of `.terminal`, `.hero__figure`, `.adapters__table`, `.receipt`, `.nav__inner` and `.outcome-card` — the raster comparison behind "no visible difference but antialiasing" |
| `states/rm_[ABC]_{390,1280}.png` | 6 | reduced-motion, one file per arm per width |
| `states/print_{390,1280}_fold.png` | 2 | `/` under print emulation at both widths |
| `states/printpage_1..9.png` | 9 | the nine A4 sheets of `/`, at Chromium's own 717 × 1045 print box |
| `states/printpage_nobg_footer.png` | 1 | the footer with background graphics off — the near-invisible state |
| `states/hv_*_{rest,hover,active}.png` | 12 | `.hero__cta--primary`, `.copy-btn`, `.decision-chip` and `.nav__link` in all three pointer states |
| `states/print_home.pdf`, `print_home_nobg.pdf` | 2 PDFs | Chromium's own A4 pagination, with and without background graphics |

## inspection observations

Result state and verdict are two separate answers and are given **per route**.
The state says whether the work ran to the end — every capture navigated,
captured and judged, no missing field, no failed step. The verdict says whether
an unresolved Blocker-severity finding exists. Severity is classified from the
finding class, never taken from the judgement step.

| route | result state | verdict |
| --- | --- | --- |
| `/` | completed | pass |
| `/now/` | completed | pass |
| `/catalogue/` | completed | **pass with a Major finding** |
| `/packs/core/` | completed | **pass with two Minor findings** |
| `/journeys/core/` | completed | **pass with a Minor finding** |
| `/404` | completed | pass |

No route has an unresolved Blocker. The result state is "completed" on all six
because every capture navigated, captured and was judged with no missing field
and no failed step — which is a separate answer from the verdict, and stays
separate even where they agree.

### `/` — result state: completed. Verdict: pass.

All 16 captures navigated, captured and were judged, with no missing field and
no failed step.

What looking at the captures found. Severity is classified from the finding
class, not taken from the judgement step.

**1. Minor — the hero's rules stop short of every rule beneath them, in
channels 2 and 3 (`>=640 <1100`).** `.hero__proof` is capped at 403 CSS px and
does not grow with the band, while `.work-records` below it takes the full
measure. Measured right edges: at 640, proof ends at x=435 against the record
list's x=608 (173px short); at 768, x=442 against x=730 (288px short). At 1100
and above the hero goes two-column and the 403px cap is correct, so the defect
is confined to the two middle channels. Reader-visible as a hero whose
horizontal rules are visibly indented from the rules directly below them, on a
surface whose whole containment argument is that rules do the dividing. Not a
Blocker: nothing is clipped, overlapped, unreachable or unreadable. Pre-existing
— not introduced by this retrofit.

**2. Nit — the annotation receipt reads as a stranded strip in channels 2 and
3.** In `s4_home_c640_tall_scrolled.png` and `s4_home_c768_tall_scrolled.png`
the "Catalogue size" receipt renders about 205 CSS px wide, left-aligned under a
691px band, because the annotation margin only becomes a real column at 1100.
It is legible and correctly ordered in the DOM; it just does not look placed.
Same root cause as finding 1 and pre-existing.

**No layout failure of any kind was found at 320.** Channel 1 was the channel
most at risk, and it is the cleanest of the four.

What the captures confirm rather than fault: no horizontal overflow at any of
the 16 (`scrollWidth > clientWidth` was false in every one); short viewports
(600px) behave as tall ones with less content, with no sticky chrome eating the
fold; the outcome record list reads consistently across all four channels; and
the ruled treatment now applied to `/now/` matches what the homepage bands do.

**Finding 1 is FIXED, and re-measured.** `.hero__proof` and `.hero__fineprint`
carried `max-width: 56ch`, and because the border that draws each rule is on
that capped box, capping the measure capped the rule. Both caps are removed;
the two ruled fields now span the lede column, and `.hero__friction` between
them — prose, and carrying no rule — keeps its 56ch measure. Measured right
edge of `.hero__proof` against the band's content column, after the change:

| viewport | content column (or lede column at >=1100) | `.hero__proof` width | shortfall |
| --- | --- | --- | --- |
| 390 | 350.0 | 350.0 | 0 (was already 0 — 56ch exceeded the band) |
| 700 | 630.0 | 630.0 | 0 (was 403.2, **226.8 short**) |
| 768 | 691.2 | 691.2 | 0 (was 403.2, **288.0 short**) |
| 900 | 820.0 | 820.0 | 0 (was 403.2, **416.8 short**) |
| 1280 | 547.8 (lede track of the two-column hero) | 547.8 | 0 (was 403.2, **144.6 short**) |

The 1100+ channel was **not** correct before, contrary to what finding 1
originally recorded: the two-column hero gives the lede a 547.8px track and the
403.2px cap fell 144.6px short of it there too. The rule now spans its own
block at every channel, which is the gesture, rather than spanning the page.
Side effect, measured: the proof line wraps to fewer lines, so the element is
shorter (81px to 57px at 700–1280).

**Finding 2 is unchanged** — the receipt is still a narrow strip below 1100.
It is the annotation margin's designed narrow-width behaviour, not a defect,
and it is recorded here as an observation only.

### `/now/` — result state: completed. Verdict: pass.

All 16 captures navigated, captured and judged; all five fields present on
every one; every scrolled capture reached the document maximum exactly.

**No horizontal overflow at any of the 16.** `scrollWidth === clientWidth` in
all sixteen, including 390.

**1. Moderate — the route is 61,638 CSS px tall at 390, and nothing bounds
that.** Finding class: information architecture / progressive disclosure. 122
releases render as one unpaginated document; at 390x900 that is **68 viewport
heights**, and at 1280 it is still 38. The direction's *Staged revelation* goal
asks that complexity earn its way in, and this route asks for all of it at
once. Not a Blocker — nothing is clipped, unreachable or unreadable, and every
release is real, checkable content. But the route's stated job is "what has
actually shipped", and beyond roughly the first ten entries no reader reaches
it. Recorded here rather than fixed: bounding it is a content decision (recent
N, grouped by year, or paginated) with its own review, not a retrofit edit.
It is already flagged from the other side under *reliability/recovery status*,
where the same growth is a 402 KB single document.

**2. Nit — the footer's column grid leaves a hole in channel 2.** At 700 the
footer's three link columns wrap to a 2-up grid, so "Project" sits alone on the
second row with the right half of the band empty. Cosmetic; no content is lost
or unreachable.

**Empty state — verified, at 320 and 1440.** Rendered by stubbing the
projection to zero groups (see *states* for why no stub shipped).

| property | 320 | 1440 |
| --- | --- | --- |
| top / bottom rule | `1px solid #8a8172` both edges | same |
| rule contrast on `#f7f5f0` | **3.53:1** (1.4.11 floor is 3:1) | same |
| rule spans the band's content box | 20→300 of 20→300 | 190→1250 of 190→1250 |
| `.now-empty__text` contrast | **17.16:1** | same |
| `.now-empty__link` contrast | **17.16:1**, underlined | same |
| reflow (`scrollWidth` vs `clientWidth`) | 320 vs 320 — **pass** | 1440 vs 1440 — **pass** |
| axe (`wcag2a wcag2aa wcag21a wcag21aa wcag22aa`) | **0 violations** | **0 violations** |

The branch is bounded by the same `--ds-rule-boundary` pair a one-record list
is, so the populated and empty branches occupy the same shape — which is what
the restyle set out to do, and it is now seen rather than assumed.

### `/catalogue/` — result state: completed. Verdict: pass with a Major finding.

All 16 captures navigated, captured and judged; all five fields present on
every one; no horizontal overflow at any of the 16.

**1. Major — `/catalogue/` is still built out of cards, and the direction sheet
forbids cards.** Finding class: direction-sheet contradiction on a shipped
route — the same class, on the same axes, that was already adjudicated and
fixed twice elsewhere. The sheet's Containment row reads `[ruled]`: "Rules
divide and rank. **No cards, no tinted panels, no shadows, no overlap.** A rule
is structure; it never decorates." Three classes on this route contradict it:

| class | what it draws | line |
| --- | --- | --- |
| `.outcome-card` | `--ds-surface` fill, border, `--ds-radius-lg` | `catalogue/index.astro:237` |
| `.role-card` | fill, border, `--ds-radius-md` | `catalogue/index.astro:284` |
| `.cat-card` | `--ds-surface-alt` fill, border, `--ds-radius-lg`, hover lift | `catalogue/index.astro:320` |

Plus rounded pack chips at `--ds-radius-md` inside each card.

This is not a new opinion. `NowHighlights.astro`'s own comment records that
"the homepage's outcome band had exactly the same contradiction and it was
resolved the same way", and both `PackCatalogue` (`.work-records` /
`.work-record`) and `/now/` (`.now-list` / `.now-release`) were converted to
ruled records. `/catalogue/` was not, and it is one nav click from both. The
reader-visible consequence is that the catalogue reads as a different site from
the home and now routes: tinted rounded panels against a paper-and-rules
surface.

**Severity reasoning.** Major, not Blocker: nothing is clipped, overlapped,
unreachable, unreadable or failing a contrast floor, and axe is clean at both
widths. Major, not Minor: it is the primary content treatment of an entire
route, it contradicts an axis the owner has already settled, and the same
contradiction has now been repaired on two other surfaces — a third instance
is a pattern, not an oversight.

**Not fixed in this change, deliberately.** Converting three card grids to
ruled records changes the route's whole layout, including how the 22-pack
inventory grid reflows in all four channels. That is a design change with its
own review, not a retrofit edit, and doing it inside a close-out pass is how it
would ship unreviewed. It is carried to *unverified items* as outstanding work
with its evidence attached.

**2. Nit — the last outcome row is ragged at 1280.** The 3-up grid leaves two
empty cells on its final row. A ruled record list, which is what the homepage
uses for the same content, has no ragged edge; the observation therefore points
at the same root cause as finding 1 and is not tracked separately.

### `/packs/core/` — result state: completed. Verdict: pass with two Minor findings.

All 16 captures navigated, captured and were judged, with no missing field and
no failed step. No horizontal overflow at any of the four widths.

**1. Minor — a sentence runs into the link that follows it, on 7 of 22 pack
pages.** The install note emits `…Use the command above.<a …>Browse the
catalogue →</a>` with no whitespace between the full stop and the anchor, so
the reader sees "**above.Browse the catalogue →**". Visible in
`mx_packs-core_c320_tall_scrolled.png`, `mx_packs-core_c640_short_scrolled.png`
and `mx_packs-core_c1100_tall_scrolled.png` — it is not a wrap artefact, it is
in the emitted HTML. Finding class: a reader-visible text defect in shipped
copy. **Severity: Minor** — the link still works, is still underlined and is
still distinguishable; only the sentence reads wrong. It affects the 7
repo-scoped pack pages that carry this note, not all 22. Not fixed here: the
repair is one character in a copy string, but copy on this surface is owned
upstream of a verification pass, so it is reported rather than edited.

**2. Minor — the ≥1100 channel leaves a third of the page empty.** The body
column caps at about 725 CSS px and stays left-aligned inside the 1140 px
container, so `mx_packs-core_c1100_tall_atrest.png` and
`mx_packs-core_c1100_tall_scrolled.png` show roughly 375 px of unused ground
down the right edge. The nav and footer use the full container, which makes the
asymmetry read as an omission rather than as a margin. The homepage avoids it
by putting the transcript figure in that space; this route has nothing there.
Finding class: an unbalanced measure at one channel. **Severity: Minor** —
nothing is clipped, overlapped or unreachable, the reading measure itself is
correct, and choosing what belongs in that space is a design decision.

The `.journey-link` panel on this route is a tinted, bordered, rounded card,
which is the **same** contradiction with the direction sheet's Containment row
already recorded as the open Major on `/catalogue/`. It is the same finding on
another route, not a second one, and it is tracked there.

### `/journeys/core/` — result state: completed. Verdict: pass with a Minor finding.

All 16 captures navigated, captured and were judged, with no missing field and
no failed step. No horizontal overflow at any of the four widths. This is the
longest of the three new routes — 11,398 CSS px of scroll range at 320.

**1. Minor — a separator dangles at the end of a line in channel 1.** The hero
meta line reads `18 skills · 2 human gates · 25–45 min/session`. At 320 it
wraps after the second separator, so `mx_journeys-core_c320_tall_atrest.png`
shows a line ending in a bare "·" with `25–45 min/session` beneath it. The
separators are plain text between spans rather than generated content, so
nothing suppresses one at a line end. Confined to channel 1: at 640, 768 and
1100 the line fits and no separator dangles. Finding class: a typographic
defect at the narrowest supported width. **Severity: Minor** — the content is
complete and correctly ordered; only the line ending is wrong.

Observed and **not** classified as a finding: the `From scoped work to a
reviewed merge` band holds one short monospace line in roughly 200 CSS px of
height at 1100. It is loose against the 8 px rule pitch rather than off it, and
a deliberately airy band is within the direction sheet's range.

### `/404` — result state: completed. Verdict: pass.

All 16 captures navigated, captured and were judged, with no missing field and
no failed step. No horizontal overflow at any of the four widths. The route
renders with full navigation and a full footer at every channel, both CTAs are
present and both meet the 44 px touch floor, and the shortest scroll range of
any route — 92 CSS px at 1100 × 900 — still reports `page-scrollable: true`
from the page rather than from a successful scroll. At 320 × 600 the second CTA
sits below the fold, which is ordinary below-fold content on a scrollable page
and not a finding.

### What pointing the guard at the build found — 20 journey pages

Finding class: a defect invisible to the check that was supposed to cover it.
**Severity: Major** — it is the same accessibility defect the whole workaround
exists for, on 20 shipped pages, and the first version of the guard could not
see it.

The list guard was first written as a scan of `web/src/**/*.astro`. It passed.
Re-pointing it at the **emitted build** failed immediately, on twenty pages:

```
journeys/core/index.html  <ul>  markers stripped by:
  .journey-narrative[data-astro-cid-suvgfjbn] ul { list-style: none }
```

Those lists come out of each journey's Markdown body through `<Content />`.
**There is no `.astro` tag to put an attribute on**, so a source scan cannot
see them and cannot be made to — the defect class is "a list that exists only
after rendering". `.journey-narrative ul` stripped their markers *and* set
`display: grid`, which removes list semantics a second way, because a grid
container generates no markers for its items even if asked.

**Repaired at the cause, not compensated for.** The template route was
unavailable and so was the plugin route: Astro 7's default Markdown processor
rejects `markdown.rehypePlugins` outright —

```
Error: `markdown.remarkPlugins`, `markdown.rehypePlugins`, and
`markdown.remarkRehype` run on the `unified` processor from
`@astrojs/markdown-remark`, which is no longer installed by default now that
Sätteri is the default Markdown processor.
```

— which is a new dependency **and** a change of Markdown processor, on a
surface whose scoped `AGENTS.md` records that it deliberately runs a different
engine from `docs-site/`. That was tried, refused by the build, and reverted;
`astro.config.ts` sets no `markdown` config, exactly as before.

So the markers were put back instead. The surface already had the precedent
for this exact content class: `.pack-description ul` / `ol` restore `outside`
and `decimal` for Markdown prose. `.journey-narrative` now agrees with it —
`list-style: disc outside` / `decimal outside`, `display: grid` replaced by a
normal block list with the former `gap` carried as a sibling margin, the panel
itself unchanged, and a muted `::marker`. Verified in the browser at 1000px:
`list-style-type: disc`, `display: block`, `::marker` at
`--ds-on-surface-muted`. **No ARIA was added**, because there is no longer a
defect to compensate for — the guard now records these lists as restored and
asks no role of them. axe on `/journeys/core/` at 390 and 1280: **0 violations**
after the change.

## a11y result

**Gate 2, automated.** axe-core 4.13.0 with `wcag2a wcag2aa wcag21a wcag21aa
wcag22aa`, on all six routes at 390 and 1280 — 12 runs.

**Zero violations in all 12 runs.** Passing-rule counts ran 17–33 per run.

Incomplete (axe could not decide): one item per run, always `color-contrast` on
the nav CTA, message "Element content contains only non-text characters". This
is the arrow glyph in "Try the build loop →", which is `aria-hidden` decoration
beside the labelled text. Reviewed and not a defect.

**Gate 1 repairs made during this run.** The first Gate 1 pass surfaced 26
errors; two were genuine assistive-technology defects and were fixed:

- `JourneyHero.astro` carried `aria-label="Session statistics"` on a bare
  `<div>`. A `<div>`'s implicit role is `generic`, and ARIA in HTML forbids a
  name on `generic`, so every assistive technology dropped that label. Now
  `role="group"`.
- `Receipt.astro` renders an `<aside>`, which is a `complementary` landmark, and
  `/` carries three of them with no accessible name — indistinguishable in a
  screen reader's landmark list. Each now takes `aria-labelledby` pointing at
  its own visible label, so the name cannot drift from the text.

**Manual check 1 — WCAG 2.5.8 Target Size (Minimum), AA. Pass.**

Every interactive target on all six routes was measured at 390 and 1280, after
filtering to elements the page actually renders (`checkVisibility` with
`contentVisibilityAuto`, `opacityProperty` and `visibilityProperty`, plus
exclusion of content inside a closed `<details>`).

An early measurement reported the mobile nav links at 4x86 CSS px. That was an
instrument fault, not a defect: those links live inside the closed `<details>`
drawer, where `content-visibility: hidden` applies size containment, so they
have a layout box that no reader ever sees. With the drawer opened explicitly,
every drawer row measures **350x44** — above the 24x24 minimum on both axes and
above the 44px touch guideline.

Targets under 24x24 are all text links. Each was checked against the **Spacing
exception**: a 24px-diameter circle centred on the target must not intersect
another target's circle, or another target's bounding box. Both variants were
computed — circle-to-circle for undersized pairs, circle-to-box for undersized
against full-size.

| route | width | visible targets | under 24x24 | tightest measured distance | verdict |
| --- | --- | --- | --- | --- | --- |
| `/` | 390 | 55 | 29 | 28.0 px (`atlassian` ↔ `converters`) | pass |
| `/` | 1280 | 60 | 52 | 34.4 px (`Catalogue` ↔ `Use cases`) | pass |
| `/catalogue/` | 390 | 73 | 0 | n/a | pass |
| `/catalogue/` | 1280 | 78 | 20 | 34.4 px | pass |
| `/packs/core/` | 390 | 22 | 3 | 122.5 px | pass |
| `/packs/core/` | 1280 | 27 | 23 | 34.4 px | pass |
| `/journeys/core/` | 390 | 32 | 2 | 47.2 px | pass |
| `/journeys/core/` | 1280 | 37 | 24 | 34.4 px | pass |
| `/now/` | 390 | 140 | 0 | n/a | pass |
| `/now/` | 1280 | 145 | 20 | 34.4 px | pass |
| `/404` | 390 | 20 | 0 | n/a | pass |
| `/404` | 1280 | 25 | 20 | 34.4 px | pass |

**Zero spacing failures across 12 measurements.** The tightest measured
nearest-centre distance anywhere is **28.0 CSS px**, against a 24 px threshold —
a 4 px margin, which is thin. It occurs between adjacent pack-name links in the
homepage outcome list at 390.

**Manual check 2 — WCAG 2.4.13 Focus Appearance (AAA enhancement). Pass.**

Every focusable element was tabbed on 7 route/width combinations: `/` at 390 and
1280, and `/catalogue/`, `/packs/core/`, `/journeys/core/`, `/now/`, `/404` at
1280. **429 focus stops in total** — 61, 56, 145, 78, 27, 37 and 25
respectively.

The indicator is uniform: `outline: 2px solid` at `outline-offset: 3px`
(`--ds-focus-ring`), with `.decision-chip` at 3px. A 2px solid perimeter ring
exceeds 2.4.13's minimum indicator area.

- **Against the adjacent background: minimum 13.14:1**, maximum 17.16:1, across
  all 429 stops. The requirement is 3:1.
- **Against the element's own fill:** an arithmetic check flagged 1:1 on filled
  controls — ink ring on an ink-filled button. That flag does not hold. The 3px
  `outline-offset` means the ring never touches the element's fill; the colour
  on both sides of the ring is the surrounding ground. Confirmed by looking, not
  only by arithmetic: `diag_focus_cta.png` shows the ink ring separated from the
  ink button by a clear paper gap.
- **`.org__cta` re-measured after it moved to the light band.** Its ring was
  the off-white dark-ground ring inherited from `.section--dark`; that carrier
  is gone, so the value was re-derived rather than carried over. It now takes
  the `:root` paper ink ring: `2px solid rgb(20, 18, 15)` at `3px` offset on
  `--ds-surface-alt` `#efece5` — **15.85:1**, against a 3:1 requirement.
  `diag_focus_orgcta.png` is the re-taken capture.

**Manual check 3 — `forced-colors: active`. Two defects found and fixed.**

Chromium's forced-colors emulation, `/` and `/now/` at 390 and 1280, with every
reading taken from `getComputedStyle` in both modes and compared.

*What survives, confirmed rather than assumed:*

- **Every rule.** All 18 painting rule declarations in the marketing components
  are drawn as a `border`, and not one is drawn as a `background`. Verified by
  exhaustive grep as well as by measurement: the only `background-image` or
  gradient anywhere in `web/src` is the Receipt leader below. Under forced
  colors each border repaints to `CanvasText` **at its authored width**, so the
  1px/2px weight hierarchy that ranks a divider against a boundary survives
  intact — `.hero__proof` stays 1px, `.rec__group--held` stays 2px.
- **`HELD`.** Colour is the only one of its five signals that is lost
  (`#8c2f1f` → `CanvasText`, the same ink as everything else). The literal
  uppercase string "HELD" in the markup, `font-weight: 600` against the 400 of
  every neighbouring value, `letter-spacing: 1.04px`, the gloss "awaiting a
  person", and the 2px rule above the group all survive. Five signals, one
  lost: WCAG 1.4.1 holds with room.

*What is lost, and the judgement on it:*

- **The Receipt's dotted leader vanishes.** `Receipt.astro`'s
  `repeating-linear-gradient` is a background-image, and forced colors strips
  it: `background-image` reads `none`. **Accepted, no fallback added.** The
  leader's job is to carry the eye from a field name to its value; the
  association itself is carried by the `dt`/`dd` pairing, which is semantic and
  survives everything, and the value still sits at the row's right edge on the
  same baseline. A decoration is allowed to be a decoration. Replacing it with
  a `border-bottom` would add 1px to every row and walk the whole receipt off
  the 8px rule grid — the reason the comment in that file gives for painting it
  in the first place.

*The two defects, both fixed:*

- **The mobile nav burger disappeared completely.** `.nav__burger` and its two
  pseudo-elements are 2px-high boxes filled with `background-color`, the one
  drawing technique forced colors erases: all three measured
  `rgb(255, 255, 255)` on a white ground. Below 768px that icon is the **only**
  route into the site's navigation, so the whole menu became unreachable for a
  high-contrast user. Fixed with a `@media (forced-colors: active)` block
  setting the three bars to `CanvasText`; re-measured at `rgb(0, 0, 0)`. The
  open-state X is untouched — `.nav__mobile[open] .nav__burger` is more
  specific, and `transparent` is preserved by forced colors.
- **Three filled controls lost their shape.** `.org__cta`, `.nav__cta` and the
  skip link `.skip-nav` each drew their whole edge with a fill and no border.
  Forced colors sends `background-color` to `Canvas`, and since all three opt
  out of the underline, each became an undecorated run of `LinkText` — a
  control identified by colour alone. Fixed by giving each a `1px` border in
  its own fill colour: invisible in normal mode, and repainted to `LinkText`
  under forced colors, which is exactly what already made
  `.hero__cta--primary` survive. Re-measured: all three report a 1px
  `rgb(0, 0, 159)` border. No geometry regression — `.org__cta` is 44.39 px
  tall in both modes, because `box-sizing: border-box` absorbs the border.

**Stated WCAG 2.2 AA gap — not covered.** The following AA criteria were **not
verified** by any gate in this run, and nothing here should be read as covering
them:

| criterion | status |
| --- | --- |
| 2.4.11 Focus Not Obscured (Minimum) | not covered |
| 2.5.7 Dragging Movements | not covered |
| 3.2.6 Consistent Help | not covered |
| 3.3.7 Redundant Entry | not covered |
| 3.3.8 Accessible Authentication (Minimum) | not covered |

axe-core has no rule for any of the five. Three of them (2.5.7, 3.3.7, 3.3.8)
have no applicable content on this surface, since it has no drag interaction,
no multi-step entry and no authentication — but "no applicable content" is a
judgement, not a measurement, and it is recorded here as uncovered either way.

## perf result

**No Core Web Vitals measurement exists for this surface.** There is no field
data — no RUM, no CrUX entry, no synthetic history. Localhost timings against a
`python3 -m http.server` on the same machine are not a CWV measurement and are
not reported as one. LCP, INP and CLS are therefore **unmeasured**.

What was measured is payload and request count, from the same Chromium runs:

| route | requests | transferred (sum of `content-length`) |
| --- | --- | --- |
| `/` | 7 | 306,073 bytes |
| `/catalogue/` | 7 | 281,107 bytes |
| `/packs/core/` | 7 | 263,928 bytes |
| `/journeys/core/` | 7 | 299,521 bytes |
| `/now/` | 6 | 402,030 bytes |
| `/404` | 6 | 249,840 bytes |

Identical at 390 and 1280 — no width-conditional asset loading. `/now/` is the
heaviest because it renders 122 real releases as server-rendered HTML in one
document; that is the projection's real size, not a regression. The counts
exclude any response that did not send a `content-length` header.

## console/network result

**Clean.** Across all 12 axe runs (six routes x two widths): **zero console
errors, zero page errors, zero failed requests**. Every navigation returned HTTP
200, including `/404`, which is served as a static file here rather than via a
404 status.

A sanity gate ran before any measurement was taken, because a 404ing stylesheet
renders readable HTML and makes every capture worthless. On `/now/` at 1440:
2 stylesheets attached, 94 CSS rules parsed, the stylesheet itself returning
HTTP 200, `body` background `rgb(247, 245, 240)` — the paper ground — and `h1`
resolving to `Newsreader Variable` at 64px. The CSS was loaded and applied.

## analytics events

**None. This site has no tracking of any kind.** No analytics library, no tag
manager, no beacon, no pixel, no event dispatch. The request tables above are
the whole network surface: HTML, CSS and fonts, 6–7 requests per route, all
first-party. There is no event taxonomy to verify because there are no events,
and this field is recorded as "none by design" rather than left blank.

## known exceptions

**1. Multi-surface token divergence — not resolved, and it has a cost.**

The `frontend-engineering` skill requires all surfaces in a product to share one
token contract. This product ships two: `web/` (this surface) and `docs-site/`.
`docs-site/` is **owner-scoped-out of this work** and keeps its own palette.

The cost is not theoretical. The two surfaces are **one click apart**: the
primary nav's "Docs" entry crosses from one to the other, and they are
co-deployed under a single origin and base path. A reader who follows that link
experiences a ground, type and rule system change mid-session, with no
navigational signal that they have crossed a boundary — because they have not
crossed one that the URL or the chrome admits to. Every "consistent across the
product" claim in this manifest is therefore scoped to `web/` alone and does not
survive that click. The divergence is accepted for this change, not fixed, and
it does not shrink as `web/` improves — each step of this retrofit widens the
gap the Docs link crosses.

**2. Gate 1 is CLEAN — resolved, not waived.**
`npx html-validate --preset standard,a11y --max-warnings 0 'build/**/*.html'`
exits **0** with no output. This supersedes the 22 standing errors this field
used to record. Each of the three classes was resolved on its merits, and each
resolution is a reviewable entry in `.htmlvalidate.cjs` carrying its own reason,
its own known limit, and the condition under which it should be removed. None
is a blanket suppression.

| former class | count | how it is resolved now |
| --- | --- | --- |
| `aria-label-misuse` | 14 | Fixed in the markup, not exempted. |
| `no-redundant-role` | 7 | `'no-redundant-role': ['error', { exclude: ['list'] }]` — the exemption matches the **role value** `list` only. `role="button"` on a `<button>`, `role="navigation"` on a `<nav>`, `role="listitem"` on an `<li>` and every other redundant role still error. It caught a real `role="region"` on a `<section>` in `WriteConfirmation.astro` on its first run, which was fixed rather than exempted. |
| `prefer-native-element` | 1 → then 7 | Fixed in the markup (the `<div role="region">` became a named `<section>`). It then re-fired seven times for a different reason — see below. |

**Why `prefer-native-element` is now exempted for `list`, and what replaced
it.** Making the Safari workaround consistent (see *unverified items*, and
`base.css`) put `role="list"` on five `<ol>` elements. The rule holds **one**
native element per role and for `list` that element is `ul`, so it reported
"Prefer to use the native `<ul>` element" seven times across the built site on
markup that already **is** the correct native element. HTML has two list
elements; the rule's mapping can only name one.

Three ways out were available. Dropping the role from the `<ol>`s was rejected:
Safari drops list semantics from an `<ol>` styled `list-style: none` exactly as
it does from a `<ul>`, and on an ordered list what is lost is position in a
sequence — the more load-bearing of the two. Re-pointing the mapping at `ol`
was rejected: it moves the false report onto every `<ul>`, which is most of
them. So the keyword is exempted, and the check it used to provide is replaced
rather than dropped.

The cost was one real thing: `prefer-native-element` catching a list role on a
generic element, `<div role="list">`. `web/src/test/list-semantics.test.ts`
covers that now, and covers it more tightly than the linter did, because it
admits **both** native list elements where the linter can only name one. The
claim in the `no-redundant-role` comment that "prefer-native-element still
covers the case that matters" was amended in place rather than left standing —
a stale "something else covers it" is worse than no claim at all.

All three — the two exemptions and the test — rest on the same premise and
retire together: Safari preserving list semantics under `list-style: none`, or
`base.css` no longer suppressing markers globally.

**3. The Safari list-semantics workaround is now enforced, not observed.**

`base.css` suppresses list markers on every `ul`/`ol`; Safari then drops list
semantics and VoiceOver stops announcing "list, N items" and each item's
position. `role="list"` restores both. **Chromium does not have the behaviour,
so nothing else in this evidence file can see the defect** — not a capture, not
axe, not html-validate. Before this close-out, eight lists carried the role and
twenty-one did not, and nothing failed.

All twenty-nine now carry it, and `web/src/test/list-semantics.test.ts` holds
that open. The guard's design is the load-bearing part:

- **Both sides are derived at test time.** The stripping rules are parsed out
  of the stylesheets each emitted page actually links or inlines; the lists are
  read out of the emitted HTML. Nothing names a file, a selector or a component.
  A hand-maintained allow-list would be the same staleness in a new place, and
  it would have passed on the day the workaround covered eight lists in
  twenty-nine.
- **It reads the BUILD, not `web/src`.** That is not a detail — see §4.
- **It follows the cascade.** A blanket "every list needs the role" is wrong on
  this surface and the emitted CSS proves it: `.pack-description ul` restores
  `list-style: outside` and `.pack-description ol` restores `decimal`, so the
  Markdown prose lists on a pack page keep their markers, keep their Safari
  semantics, and are owed no role. Each list is resolved against the WINNING
  declaration — specificity, then source order.
- **Its cascade model's three premises are asserted, not assumed**: no
  `!important` on a list-style declaration, no inline `style` setting one, and
  no selector skipped as unparseable. A hole in a scan reads as a pass, so each
  hole has its own failing test.
- **It has floors.** Pages scanned, lists found, stripping rules found, and
  lists the stripping actually reaches are each asserted above a threshold set
  far below the real counts. A scan that reaches nothing cannot report green.

**Proved it can fail.** `role="list"` was removed from `.footer__list` — a real
marker-stripped list — and the site rebuilt. The suite went to
`1 failed | 7 passed (8)`, naming every one of the 51 affected pages, the
element, the browser, and the exact rule that strips it:

```
gives every marker-stripped list an explicit role="list"
AssertionError: SAFARI/VOICEOVER: a list whose markers are suppressed loses its
list semantics — VoiceOver stops announcing "list, N items" and stops
announcing each item's position. Chromium does not have this behaviour, so no
capture, axe run or rendered check in this repo can see it. …
index.html  <ul.footer__list>  markers stripped by:  .footer__list[data-astro-cid-qup6pdxl] { list-style: none }
```

Note which rule it blames: the **component** rule, not the global `ul, ol`
reset, because the component rule wins on specificity. The cascade model is
doing real work in the message a reader gets. The attribute was restored, the
file verified byte-identical to its backup, the site rebuilt, and the suite
returned `8 passed (8)`.

**4. Gate 3 is configured and RED — a measured result, not a skip.**

Stylelint did not exist anywhere in this repository. It does now, declared in
the owning manifest:

| where | what |
| --- | --- |
| `web/package.json` devDependencies | `stylelint` 17.15.0, `stylelint-declaration-strict-value` 1.12.1, `postcss-html` 2.0.0 — exact pins, no carets |
| `web/package.json` scripts | `"lint:css": "stylelint \"src/**/*.{css,astro}\""` |
| `web/stylelint.config.mjs` | the rule, and a comment for every judgement in it |
| `web/AGENTS.md` | the dependency record and the command |

`python3 tools/lint-npm-allow-scripts.py` exits **0** after the install: none
of the three new packages carries an install script, so no `allowScripts`
entry was needed and none was added.

**What it enforces.** `scale-unlimited/declaration-strict-value` requires a
`var(--ds-*)` token for `color`, `background-color`, `border-color` and
`font-size`, ignoring `inherit`, `transparent` and `currentColor`.

**Three keywords were added to `ignoreValues` beyond those three, and the
reason matters.** `Canvas`, `CanvasText` and `LinkText` are CSS system colours
that appear only inside `@media (forced-colors: active)`. Windows High Contrast
substitutes the user's own theme for them; replacing one with a token would pin
the colour and defeat the mode — and `SiteNav.astro`'s `CanvasText` is one of
the two repairs the forced-colors run produced, recorded under *a11y result*.
The rule's first run flagged it. Ignoring it is correcting the rule's scope to
match the keyword class the brief already named, not suppressing a finding.

**The scan reaches the component CSS.** Component styles live in `.astro`
`<style>` blocks, so `postcss-html` is wired in as `customSyntax` for
`**/*.astro`. Without it the rule would read only the four files under
`src/styles/` and report a clean pass while all 47 components went unchecked —
the exact shape of a gate that passes because it scanned nothing. The glob
resolves **51 files: 4 CSS and 47 `.astro`**.

**Mutation check — it can fail, and on all four properties.** Three literals
were injected into `Hero.astro` against the **final** config:

```
src/components/marketing/Hero.astro:171:5: … for "color", not the literal "#14120f". (scale-unlimited/declaration-strict-value) [error]
src/components/marketing/Hero.astro:225:5: … for "background-color", not the literal "#14120f". (scale-unlimited/declaration-strict-value) [error]
src/components/marketing/Hero.astro:344:5: … for "border-color", not the literal "#dddddd". (scale-unlimited/declaration-strict-value) [error]

14 problems (14 errors, 0 warnings)     exit 2
```

`font-size` needs no injection: the eleven standing findings below are all
`font-size`. So all four configured properties are demonstrated live.

Reverted, `Hero.astro` is **byte-identical** to its pre-mutation backup —
`sha256 2c0c0f8e7bd1abf3d958882467d8bccb37cc13b9111df570e74e4c076cf77fce` on
both — and the run returns to the standing state:

```
11 problems (11 errors, 0 warnings)     exit 2
```

**The true state: 50 of 51 files are clean; all 11 findings are in one file,
`src/pages/direction-preview.astro`.** No component, layout, primitive or page
other than the direction preview carries an untokenised value in any of the
four properties.

**Six were fixed; five classes were not, and the reason is the token scale.**
The six substitutions are value-identical — the document root is 16 px on this
route, confirmed live — so the render could not change, and it did not: the
computed `font-size`, `line-height`, `font-family` and document height of every
`.dp__*` element at 390 and 1280 are identical before and after.

| literal | count | disposition |
| --- | --- | --- |
| `12px` | 5 | **Fixed** → `var(--ds-type-xs)` (`0.75rem` = 12px). Exact. |
| `1.125rem` | 1 | **Fixed** → `var(--ds-type-body-lg)`, whose stated role is "lead / intro" and whose only use here is `.dp__deck`. Exact in value and in role. |
| `11px` | 5 | **Open.** No token is 11px. The nearest, `--ds-type-xs`, is 12px, so substituting would change the render. Needs a scale decision. |
| `13px` | 4 | **Open.** `--ds-type-mono-sm` is 13px, but its stated role is "inline code, skill names". Three of the four sites are `--ds-font-mono` and would fit; the fourth, `.dp__navlinks`, is `--ds-font-sans`, so one token would carry two meanings. Needs a naming decision. |
| `0.9375rem`, `1.0625rem` | 1 each | **Open.** 15px and 17px; no token at either. Needs a scale decision. |

Gate 3 is therefore **red with 11 known findings in one non-component file**,
not green. Forcing it green would mean either adding tokens nobody has agreed
to or widening `ignoreValues` past the keyword class, and both are design
decisions this pass does not own.

## unverified items

| item | reason |
| --- | --- |
| Gate 3 — the 11 open `direction-preview.astro` font sizes | **The gate itself is no longer unverified**; it is configured, mutation-checked and reporting, and its result is under *known exceptions* §4. What is unresolved is the finding it makes: 11 literals in one file that need either new tokens (11px, 15px, 17px) or a naming decision (13px against `--ds-type-mono-sm`). Both are scale decisions, so the gate stands red rather than forced green. |
| **Safari's list-semantics behaviour** | **Still unverified, and the instrument is the reason.** WebKit was installed and `/` was loaded in it, but Playwright 1.63.0 removed `page.accessibility` (`typeof page.accessibility === 'undefined'`), `ariaSnapshot` is Playwright's own DOM-derived computation and returns the same answer in every engine, and `window.internals` is absent from the Playwright WebKit build. So the `role="list"` workaround is held on the documented Safari behaviour, not on a measurement taken here. What WebKit **did** settle is layout parity — see *browsers*. Settling this needs real Safari with VoiceOver, or a WebKit build exposing its AX controller. |
| **`/catalogue/` card treatment** | **Open, Major, evidence attached.** The route still uses `.outcome-card`, `.role-card` and `.cat-card` — tinted, bordered, rounded panels — against a direction sheet whose Containment row forbids cards outright, and after the same contradiction was repaired on the homepage's outcome band and on `/now/`. Full finding under *inspection observations*. Not fixed here because converting three card grids to ruled records is a layout change across four channels with its own review. |
| **`/now/` route length** | **Open, Moderate.** Re-measured on the lower-bound matrix: **75,240 CSS px at 320** — 83.6 viewport heights at 900 — falling to 35,977 at 1100, for 122 releases in one unpaginated document whose emitted `index.html` is **160 KB**. These supersede the 61,638 px / 402 KB figures, which came from the superseded 390-wide run; the two were not reconciled and the earlier pair is not carried forward. Nothing in the build bounds the growth. Bounding it is a content decision, not a retrofit edit. |
| Core Web Vitals | No field data and no synthetic history. See *perf result*. |
| Print stylesheet | **The state is now exercised** — see *states* for nine measured sheets, the 0.82-sheet ink cost, the 1.42:1 footer with backgrounds off, 64 links with no printed targets, 3 of 4 install variants lost, and 7 of 8 page breaks cutting a block. What remains unverified is any remedy: there is still no `@media print` rule, and writing one is a design decision. |
| A distinct `:active` state | **The state is now exercised** — see *states*. 0 of 28 interactive classes distinguish `:active` from `:hover`, so a pointer user gets no press feedback. Minor, and adding one is a design decision. |
| `docs-site/` | Owner-scoped out. It was built to satisfy the documented build order — the `web/` build cleans repository `build/`, so `build/docs/` must be rebuilt after it or four `rendered-output` / `fixture-axe` tests fail on a missing docs build — and nothing more. |
| **`/packs/<pack>/` install-note whitespace** | **Open, Minor, 7 of 22 pack pages.** The emitted HTML is `…Use the command above.<a …>Browse the catalogue →</a>` with no space, so the reader sees "above.Browse the catalogue →". Full finding under *inspection observations*. Not fixed here: it is one character, but it is shipped copy, and this pass verifies rather than edits copy. |
| **`/journeys/<journey>/` hero meta separator at 320** | **Open, Minor, channel 1 only.** The line wraps after a plain-text "·", leaving the separator dangling at a line end. Full finding under *inspection observations*. |
| **`/packs/<pack>/` measure at ≥1100** | **Open, Minor.** About 375 CSS px of the 1140 px container is unused down the right edge, where the homepage puts its figure. Full finding under *inspection observations*. What belongs there is a design decision. |
| Security and reliability review | Not performed. See the two fields below. |

Moved **out** of this list by the close-out, each with its evidence above: the
16-capture matrix on `/now/` and `/catalogue/`; cross-browser rendering
(partially — WebKit layout is measured, Safari AX is not, so the item was split
rather than closed); `forced-colors` / Windows High Contrast; the `/now/` empty
state; and the 22 standing `html-validate` errors.

Moved **out** by this third stage, each with its evidence above:

- **Firefox.** Three routes, two widths, both element geometry and raster. Row
  deleted; result under *browsers*.
- **The 16-capture matrix on `/packs/core/`, `/journeys/core/` and `/404`.**
  48 captures, all five fields each, verdicts under *inspection observations*.
- **Lower-bound widths on the `/now/` and `/catalogue/` matrices.** Checked,
  found wrong, and both matrices re-taken at 320/640/768/1100.
- **`prefers-reduced-motion`.** Three arms including the no-media-support case
  the `no-preference` wrapper makes necessary, plus a control arm proving the
  animation runs when it should.
- **Hover and active as states.** All 28 interactive classes exercised. The
  state is closed; the Minor finding it produced — no distinct `:active` — is
  a new row above, because a closed state and a clean result are not the same
  answer.
- **Gate 3.** Configured, mutation-checked on all four properties, and run.
  The gate is closed; its 11 findings are a new row above.

Three rows are **deliberately narrowed rather than deleted**: print, `:active`
and Gate 3 each keep a row because exercising a state is not the same as
resolving what it found. Nothing in this list has been marked done on the
strength of a run that only reached the edge of the question.

## security/privacy review status

**Status: not reviewed. Handoff: open, routed to `security-reviewer`.**

This field is recorded as outstanding, not as clear. A manifest that reports
green gates while staying silent on security is the exact shape this field
exists to prevent, so the following is a statement of what was observed, not a
review verdict.

What can be said from the measurements above: this surface **takes no user
input** — no forms, no text fields, no search box, no upload, no authentication.
It **stores nothing** — verified directly: after loading `/`, the browser
context held **0 cookies**, `localStorage.length` and `sessionStorage.length`
were both **0**, and a grep of the emitted marketing-site HTML and JS for
`localStorage`, `sessionStorage`, `indexedDB` and `document.cookie` matched
**no files**. It **makes no
third-party calls** — all 6–7 requests per route are first-party HTML, CSS and
self-hosted fonts; there is no analytics, tag manager, beacon or CDN script, as
recorded under *analytics events*. The seven requests on `/` were enumerated:
the document, two stylesheets, and four self-hosted `woff2` font files, every
one on the serving origin.

What that does **not** cover, and what is routed to `security-reviewer`:
the content-security-policy and security-header posture of the real deployment
(this run served over plain HTTP from `python3 -m http.server`, which tells you
nothing about production headers); whether any content projected into these
pages from `docs/product/changelog.md` through `now-highlights.generated.json`
crosses a trust boundary, given that the `/now/` route renders repository-authored
text as HTML; and the dependency posture of the build chain. None of the three
was examined here.

## reliability/recovery status

**Status: not reviewed. Handoff: open, routed to `quality-engineer`.**

Again, observations rather than a verdict.

What was observed: the surface is statically generated, so there is no runtime
to fail and no recovery path to exercise at request time. Two build-time
contracts do exist and are deliberately fail-closed — `NowHighlights`'s host
page throws if `now-highlights.generated.json` is not `schemaVersion 1`, and
`Receipt.astro` throws on an unknown receipt key or a schema-version mismatch.
Both fail the build rather than rendering a blank or half-populated public page.
The `/404` route exists and renders with full navigation. The web suite passes **198 tests in 23 files** — the 185-test baseline with no
regression, plus thirteen tests added by this close-out: eight in
`list-semantics.test.ts` and five in `design-system-projection.test.ts`. Both
new guards were **mutation-checked**, with the red run and the green run
recorded; see *known exceptions* §4 for the list guard and *inspection
observations* for what its first real run found. Re-run after this change's
edits, not carried over from before them.

What that does **not** cover, and what is routed to `quality-engineer`:
whether the `/now/` route degrades acceptably as the projection grows — it is
already 402 KB of HTML for 122 releases in a single unpaginated document, and
nothing in the build bounds that growth; deployment rollback and cache
invalidation behaviour under the `/agent-ready-repo/` base path; and whether the
two build-time throws are covered by a test that would catch their removal.
None of the three was examined here.
