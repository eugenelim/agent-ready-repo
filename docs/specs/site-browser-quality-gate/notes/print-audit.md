# Representative print audit

- **Status:** Accepted — measured 2026-08-18
- **Owner:** eugenelim
- **Programme:** `tech-site-completion`
- **Producing task:** `site-browser-quality-gate/T4`
- **Allowed final disposition:** `close-stale` or `shape`

## Decision rule

Prefer `close-stale`: accept browser/framework defaults when content remains
legible and navigation-only chrome does not corrupt the printed result. Choose
`shape` only for an observed failure, and then record the smallest route and
selector boundary required. Do not propose a general print stylesheet from
source inspection or visual preference.

Measured 2026-08-18. All six representative routes print without a demonstrated
contract failure, so the disposition is **`close-stale`**: browser and framework
defaults are accepted and this programme adds no print CSS.

## Representative routes

| Page role | Emitted route |
| --- | --- |
| Marketing landing | `/` |
| Docs landing | `/docs/` |
| Ordinary guide | `/docs/guides/core/how-to/start-a-project/` |
| Code-heavy guide | `/docs/guides/catalogue-curation/tutorials/your-first-skill/` |
| Aside-heavy guide | `/docs/guides/atlassian/tutorials/review-your-team-backlog/` |
| Long-table page | `/docs/guides/converters/reference/converter-skills/` |

Resolve every path through the configured deployment base.

## Evidence contract

For each route, record:

- browser, version, paper size, orientation, scale, margins, and print settings;
- whether marketing, product-orientation, Starlight, sidebar, table of contents,
  pagination, and footer navigation are absent or non-disruptive;
- legibility and continuity of body text, headings, links, code, asides, and
  tables where present;
- clipping, overlap, content outside the printable area, orphaned headings,
  unusable page breaks, and unexpected blank pages;
- whether link URLs or decorative treatments preserve or harm reading; and
- the final disposition and owner.

## Audit record

**Engine and settings, once for all six rows:** Google Chrome for Testing
**151.0.7922.34**, driven headless through Playwright's Chromium build; A4 portrait;
0.4in margins on all sides; `printBackground: false`; **scale 1** (Playwright's
default, not overridden); light docs theme. Printable width at A4 portrait with
0.4in margins is **717 CSS px** at 96dpi.

Layout was measured with the viewport set to that width — see the method note
below, which is the load-bearing part of this record.

The per-row `Paper settings` column repeats the paper geometry only; the engine and
version are stated once above rather than six times. An earlier revision renamed
that column and dropped the engine from every row, which left the evidence
contract's "browser, version … scale" clause unmet.

What each column is measured from, so no cell claims more than the method
supports. `Navigation, measured per route` is computed visibility under print media
(`display`/`visibility`) **measured on each route separately**, not a visual
inspection. An earlier revision of this table carried one hand-written value
repeated across all six rows, which claimed Starlight chrome on `/` where none
exists and claimed pagination "remains present" where it is absent — recorded
here because a column described as measured must be measured. `Clipping / overlap / breaks`
reports element-box geometry against the printable width and document-level
horizontal overflow — the column is headed `Clipping / width overflow` for that
reason; **vertical overlap was not separately inspected**, and the
grounds for reading it as absent are that no element exceeds the page width and
the full body text is present on every route. `Content result` is the PDF page
count and the character count of `<main>`'s rendered text.

| Route | Paper settings | Navigation, measured per route | Content result | Code / aside / table result | Clipping / width overflow | Observed failure and smallest rule boundary | Disposition | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/` | A4 portrait, 0.4in margins, backgrounds off | present: marketing nav bar (717×76) with logo and the 44×44 mobile disclosure, footer, skip link; hidden by the sub-desktop breakpoint, not by print rules: `.nav__links`, `.nav__cta`; not on this route: Starlight header, sidebar, table of contents, pagination | 8 page(s), 5,588 chars of `<main>` text | rendered in flow at 717px | **0px** overflow, **0** boxes past the printable width | none observed | `close-stale` | eugenelim |
| `/docs/` | A4 portrait, 0.4in margins, backgrounds off | present: Starlight header, table of contents, footer, skip link; hidden by print rules: sidebar; not on this route: marketing nav, pagination | 3 page(s), 3,260 chars of `<main>` text | rendered in flow at 717px | **0px** overflow, **0** boxes past the printable width | none observed | `close-stale` | eugenelim |
| `/docs/guides/core/how-to/start-a-project/` | A4 portrait, 0.4in margins, backgrounds off | present: Starlight header, table of contents, footer, skip link; hidden by print rules: sidebar; not on this route: marketing nav, pagination | 4 page(s), 3,842 chars of `<main>` text | rendered in flow at 717px | **0px** overflow, **0** boxes past the printable width | none observed | `close-stale` | eugenelim |
| `/docs/guides/catalogue-curation/tutorials/your-first-skill/` | A4 portrait, 0.4in margins, backgrounds off | present: Starlight header, table of contents, footer, skip link; hidden by print rules: sidebar; not on this route: marketing nav, pagination | 12 page(s), 14,992 chars of `<main>` text | rendered in flow at 717px | **0px** overflow, **0** boxes past the printable width | none observed | `close-stale` | eugenelim |
| `/docs/guides/atlassian/tutorials/review-your-team-backlog/` | A4 portrait, 0.4in margins, backgrounds off | present: Starlight header, table of contents, footer, skip link; hidden by print rules: sidebar; not on this route: marketing nav, pagination | 12 page(s), 13,397 chars of `<main>` text | rendered in flow at 717px | **0px** overflow, **0** boxes past the printable width | none observed | `close-stale` | eugenelim |
| `/docs/guides/converters/reference/converter-skills/` | A4 portrait, 0.4in margins, backgrounds off | present: Starlight header, table of contents, footer, skip link; hidden by print rules: sidebar; not on this route: marketing nav, pagination | 12 page(s), 15,488 chars of `<main>` text | rendered in flow at 717px | **0px** overflow, **0** boxes past the printable width | none observed | `close-stale` | eugenelim |

Per-route content inventory, so a later reader can tell the representative roles
were actually exercised rather than assumed: `/` 1 table / 35 links / 25 headings;
`/docs/` 1 code block / 46 links; ordinary guide 6 code blocks; code-heavy guide
17 code blocks and 1 table; aside-heavy guide **12 asides** and 3 tables;
long-table page **16 tables** and 7 code blocks.

## Method note — measuring at the wrong width invents clipping

The first pass measured layout at a 1280px viewport with `emulateMedia({media:
'print'})` and reported five to six elements per route as "wider than the
printable area". Every one was an artifact: `emulateMedia` switches media
*queries*, not the layout viewport, so the page was laid out at 1280px and
compared against a 717px limit, and every full-bleed `<section>` looked like a
clipping defect. Re-measured with the viewport set to 717px: zero offenders on all
six routes.

Recorded because `close-stale` rests on the corrected numbers, and because the
naive method is the one a later reader will reach for first.

### A second consequence of measuring at 717px

The printable width is below the marketing site's desktop breakpoint, so **A4
portrait prints the mobile layout**. That is a property of the paper, not a defect:
the nav collapses to its burger, `.nav__links` and `.nav__cta` compute to zero size,
and the footer stacks. Every marketing row below should be read that way, and a
reader expecting the desktop link list in a printout will not find it. Re-verified
2026-08-18 by running the procedure below: `nav.nav` 717×76 present, `.nav__links`
and `.nav__cta` 0×0, `.nav__mobile` 44×44 present.

### Re-measuring these rows

The probe was ad-hoc and is deliberately not committed: it measures a disposition
that this audit closes, so a tracked script would be dead code the repository has
to keep working. The procedure is the reproducible part, and it is five steps:

1. Build and serve the emitted site. The build order is load-bearing and owned by
   [`docs/guides/how-to/verify-a-site-release.md`](../../../guides/how-to/verify-a-site-release.md)
   — follow its block rather than a copy, then `astro preview`.
2. Per route, open a Playwright page and set **both**:
   - `await page.emulateMedia({ media: 'print' })`, without which step 3 reads
     *screen* media and every "hidden by print rules" attribution below is wrong —
     Starlight's sidebar hiding lives inside `@media print`; and
   - the viewport to **717 × 900**, the printable width itself. `emulateMedia`
     switches media queries, not the layout viewport, so print media *without* this
     width is what produced the false clipping described above. Both are required;
     neither substitutes for the other.
3. Set `localStorage['starlight-theme'] = 'light'` *before* navigating — Starlight's
   default is `auto`, resolved from `prefers-color-scheme`, so a dark-preferring host
   otherwise measures a theme this record does not describe.
4. Read navigation visibility from computed `display`/`visibility` on each chrome
   selector *on that route*, never carried across routes.
5. Take the PDF for the page count, and `<main>`'s `innerText.length` for the
   character count. `margin` is an object, not a string — a string throws
   `pdf.margin: expected object, got string`, and dropping it silently yields
   Playwright's default **zero** margins, a 794px printable width, and page counts
   that disagree with every row above:

   ```js
   await page.pdf({
     format: 'A4',
     margin: { top: '0.4in', right: '0.4in', bottom: '0.4in', left: '0.4in' },
     printBackground: false,
   });
   ```

Anyone re-running this should expect the counts to drift as guides are edited; the
load-bearing values are the **0px overflow** and **0 boxes past the printable
width** columns, which are what `close-stale` rests on.

## Residual, stated rather than hidden

Navigation-only chrome is still present in print output, and which chrome differs
by route: `/` prints its marketing nav bar — in the **collapsed mobile form**, since
717px is below the desktop breakpoint, so the burger prints and the desktop link
list and CTA do not — plus its footer and skip link, and has no Starlight elements
at all; the five docs routes print the Starlight header, table of
contents, footer and skip link, with the sidebar hidden by Starlight's own print
rules and pagination absent from these routes entirely. The evidence above shows
it does not corrupt content on the axes measured: no element exceeds the printable
width, document horizontal overflow is 0px, and the full body text is present on
every route. Whether its *presence* is worth removing is
a legibility preference, not a demonstrated contract failure, and the decision
rule prefers `close-stale` and bars proposing print rules from preference. If a
future reader wants it gone, that needs an observed failure first.

## What this audit does not discharge

`workspace.toml [backlog].open` slug `docs-site-print-styles` remains open. It asks
whether the docs accent colours and hairlines are tuned for paper — an aesthetic
question. This audit measured content integrity: clipping, width overflow, per-route
navigation visibility and body text presence. `close-stale` here means no
demonstrated content failure, and therefore no print CSS from this programme. It
does not mean print is aesthetically finished, and the decision rule above bars
proposing rules from preference.

Also not measured: vertical overlap and page-break quality — orphaned headings,
unusable breaks, unexpected blank pages. Page COUNT is recorded; break quality is
not, and the two are not the same. Registered as `[backlog].open` slug
`print-audit-page-break-quality`.

## Acceptance bar

- `close-stale` requires all six rows to show acceptable defaults with no
  demonstrated contract failure. **Met**: six rows, zero failures, zero clipping,
  zero overflow.
- `shape` requires at least one exact failing row, the smallest necessary print
  rule, construction proof that reproduces the failure, emitted print/browser
  evidence after remediation, and an independently shippable owning spec.
- Mixed evidence cannot be generalized: acceptable routes keep defaults, and
  rules target only the demonstrated failing boundary.
