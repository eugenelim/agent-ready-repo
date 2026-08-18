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

## Measured axes

The canonical list, because an earlier revision stated it three incompatible ways
across four files. **Four axes are measured**, all per route, all under print media
at a 717px viewport:

1. element-box geometry against the printable width — count of boxes wider than it;
2. document horizontal overflow, in px;
3. PDF page count;
4. `<main>`'s rendered text length, in characters — a DOM measure, not a page measure.

**`close-stale` rests on axes 1 and 2**, which are the only ones that can demonstrate
a content failure; 3 and 4 are recorded so a re-runner can tell the routes were
actually exercised. Nothing else is measured. Two axes the evidence contract below
asks for are *not* delivered, each with a register slug: per-route navigation
visibility (`print-chrome-paint-inventory`) and page-break quality
(`print-audit-page-break-quality`).

Everywhere else — `spec.md` AC12, `plan.md`'s T4 record, the `workspace.toml`
comments — points here rather than restating this list.

## Evidence contract

For each route, record:

- browser, version, paper size, orientation, scale, margins, and print settings;
- whether marketing, product-orientation, Starlight, sidebar, table of contents,
  pagination, and footer navigation are non-disruptive on the measured axes.
  **The per-element disposition — which of them prints, and by which rule — is
  withdrawn**; see § The navigation inventory this audit does not deliver, and
  `[backlog].open` slug `print-chrome-paint-inventory`. What this audit records
  against this bullet is non-disruption: nothing exceeds the printable width and
  document overflow is 0px on all six routes;
- legibility and continuity of body text, headings, links, code, asides, and
  tables where present;
- clipping, overlap, content outside the printable area, orphaned headings,
  unusable page breaks, and unexpected blank pages. **Delivered for clipping and
  content outside the printable area (axes 1 and 2); vertical overlap and
  page-break quality are NOT measured** — see `[backlog].open` slug
  `print-audit-page-break-quality`;
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
supports. The navigation column is **withdrawn** and nothing replaced it — see
§ The navigation inventory this audit does not deliver for why. (That column's history is part of why it is withdrawn: an earlier revision carried
one hand-written value repeated across all six rows, and each attempt to replace it
with a measured one was also wrong.) `Clipping / overlap / breaks`
reports element-box geometry against the printable width and document-level
horizontal overflow — the column is headed `Clipping / width overflow` for that
reason; **vertical overlap was not separately inspected**, and the
grounds for reading it as absent are that no element exceeds the page width and
`<main>`'s rendered text length is unchanged under print media — a DOM measure, not
a page measure, and named as such. `Content result` is the PDF page
count and the character count of `<main>`'s rendered text.

| Route | Paper settings | Navigation (withdrawn) | Content result | Code / aside / table result | Clipping / width overflow | Observed failure and smallest rule boundary | Disposition | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/` | A4 portrait, 0.4in margins, backgrounds off | withdrawn — see § The navigation inventory this audit does not deliver | 8 page(s), 5,588 chars of `<main>` text | rendered in flow at 717px | **0px** overflow, **0** boxes past the printable width | none observed | `close-stale` | eugenelim |
| `/docs/` | A4 portrait, 0.4in margins, backgrounds off | withdrawn — see § The navigation inventory this audit does not deliver | 3 page(s), 3,260 chars of `<main>` text | rendered in flow at 717px | **0px** overflow, **0** boxes past the printable width | none observed | `close-stale` | eugenelim |
| `/docs/guides/core/how-to/start-a-project/` | A4 portrait, 0.4in margins, backgrounds off | withdrawn — see § The navigation inventory this audit does not deliver | 4 page(s), 3,842 chars of `<main>` text | rendered in flow at 717px | **0px** overflow, **0** boxes past the printable width | none observed | `close-stale` | eugenelim |
| `/docs/guides/catalogue-curation/tutorials/your-first-skill/` | A4 portrait, 0.4in margins, backgrounds off | withdrawn — see § The navigation inventory this audit does not deliver | 12 page(s), 14,992 chars of `<main>` text | rendered in flow at 717px | **0px** overflow, **0** boxes past the printable width | none observed | `close-stale` | eugenelim |
| `/docs/guides/atlassian/tutorials/review-your-team-backlog/` | A4 portrait, 0.4in margins, backgrounds off | withdrawn — see § The navigation inventory this audit does not deliver | 12 page(s), 13,397 chars of `<main>` text | rendered in flow at 717px | **0px** overflow, **0** boxes past the printable width | none observed | `close-stale` | eugenelim |
| `/docs/guides/converters/reference/converter-skills/` | A4 portrait, 0.4in margins, backgrounds off | withdrawn — see § The navigation inventory this audit does not deliver | 12 page(s), 15,488 chars of `<main>` text | rendered in flow at 717px | **0px** overflow, **0** boxes past the printable width | none observed | `close-stale` | eugenelim |

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

The printable width is below **both** renderers' desktop breakpoints, so **A4
portrait prints the mobile layout on all six routes**. That is a property of the
paper, not a defect, but it is why several attempts at the navigation inventory went
wrong, and it is worth stating on its own:

- On `/`, `ul.nav__links` is `display:none` below 768px, so the desktop link list is
  not in the printed output and a reader expecting it will not find it.
- On the five docs routes, 717px is below Starlight's 800px main breakpoint and its
  `72rem` table-of-contents breakpoint, so the desktop layout — sidebar beside
  content, table of contents in a right rail — is not the *screen* layout at that
  width. For print the width is beside the point: `nav.sidebar` and
  `aside.right-sidebar-container` both carry `print:hidden`, which resolves to
  `display:none` inside `@media print`, so neither prints at **any** width. Stated
  separately because conflating the two is the error this audit kept making.

Which individual elements survive into the printed page, and by which rule, is the
question this audit **withdraws**; see § The navigation inventory this audit does not
deliver. The layout fact above is measured and stable. The per-element attributions
were not, and two successive revisions of the rows stated them wrongly — including
one that named a breakpoint where a `print:hidden` rule was doing the work.

What is unchanged by any of that: `close-stale` rests on § Measured axes 1 and 2 —
0 boxes past the printable width and 0px document overflow — reproduced on all six
routes. Page counts and `<main>` character counts (axes 3 and 4) are also unchanged,
and are recorded so a re-runner can tell the routes were exercised rather than
assumed; they cannot demonstrate a content failure.

### Re-measuring the content rows

This reproduces the columns the audit still stands behind: page count, `<main>`
character count, document overflow and boxes past the printable width. The probe was
ad-hoc and is deliberately not committed — it measures a disposition this audit
closes, so a tracked script would be dead code the repository has to keep working.
The procedure is the reproducible part, and it is five steps:

1. Build and serve the emitted site. The build order is load-bearing and owned by
   [`docs/guides/how-to/verify-a-site-release.md`](../../../guides/how-to/verify-a-site-release.md)
   — follow its block rather than a copy, then serve it with
   `npm run preview --prefix web -- --port <the port in web/src/test/e2e/site-base.ts>`.
2. Per route, open a Playwright page and set **both**:
   - `await page.emulateMedia({ media: 'print' })`, without which the whole run
     measures *screen* media. The content columns happen to be stable across the
     two here, but nothing guarantees that, and any future chrome question depends
     on it — Starlight's sidebar hiding lives inside `@media print`; and
   - the viewport to **717 × 900**, the printable width itself. `emulateMedia`
     switches media queries, not the layout viewport, so print media *without* this
     width is what produced the false clipping described above. Both are required;
     neither substitutes for the other.
3. `await page.addInitScript(() => localStorage.setItem('starlight-theme', 'light'))`,
   then navigate. Starlight's default is `auto`, resolved from `prefers-color-scheme`,
   so a dark-preferring host otherwise measures a theme this record does not describe.
   It must be `addInitScript` rather than a `page.evaluate` before the first `goto`:
   that would run on `about:blank`, where `localStorage` throws `SecurityError` and
   the value would not belong to the preview origin anyway.
4. **Skip the per-element chrome inventory.** It is withdrawn — see § The navigation
   inventory this audit does not deliver. If you are re-deriving it anyway, know what
   the three abandoned definitions were and why none of them answers the question:
   `display`/`visibility` alone reports a zero-box element as printing; adding a
   non-zero `getBoundingClientRect()` still reports `clip:rect(0,0,0,0)`,
   `transform:translateY(-150%)` and a box inside a closed disclosure as printing,
   because a box is not paint; and diffing extracted PDF text against `<main>`'s is
   the right oracle but is swamped by extraction artifacts. Whatever you use, use
   `querySelectorAll` — `.nav__cta` matches two elements whose fates differ — and
   never carry a result across routes.
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

Anyone re-running this should expect the character and page counts to drift as guides
are edited; the load-bearing values are the **0px overflow** and **0 boxes past the
printable width** columns, which are what `close-stale` rests on. Both have now
reproduced twice on all six routes.

## The navigation inventory this audit does not deliver

**Withdrawn, not deferred quietly.** The evidence contract asked, before this
narrowing, which chrome is "absent or non-disruptive" per route; bullet 2 above now
asks only for non-disruption. Three generations of probe answered that
question, and all three were wrong:

1. **Hand-written.** One value repeated across six rows. Claimed Starlight chrome on
   `/`, where none exists.
2. **`display`/`visibility` per route.** Reported any element with neither property
   as present — so a zero-box element read as printing. This is how five rows came to
   claim a table of contents that does not print.
3. **Box-aware, multi-instance.** Rejected zero-box elements, and still wrong,
   because a box is not paint. It recorded the skip link as printing at 148×42 and
   114×28 (`clip:rect(0,0,0,0)` on docs, `transform:translateY(-150%)` on `/` — laid
   out, painting nothing) and recorded a `.nav__cta` as printing at 35×110 (a box
   inside the closed mobile drawer that paints nothing). It also attributed the
   hidden table of contents to the `sl-hidden lg:sl-block` breakpoint when the
   binding, width-independent cause is `print:hidden` on
   `aside.right-sidebar-container`, which resolves to `display:none` inside
   `@media print`.

The fourth attempt read the rendered PDF and diffed its text against `<main>`'s.
*Printed* does mean *in the printed output*, so the oracle is right in principle, but
it has two limits that between them account for everything the diff reported.

**Extraction noise.** PDF text extraction normalizes apostrophes, rewrites `://`, and
rewraps lines, so most "extra" lines are `<main>` content that merely fails to string
match.

**No discriminating power on the docs routes.** Starlight places the breadcrumb, the
previous/next pagination **and the footer** inside `<main>`. A PDF-minus-`<main>` diff
therefore cannot identify chrome on those five routes at all, and every line it
flagged there was extraction noise. An earlier draft of this very section read that
noise as evidence and claimed the breadcrumb prints as chrome — the same mistake as
the rows it replaced, one layer up.

So the diff establishes exactly two things, and they are all this section claims:

- On `/`, where the nav and footer DO sit outside `<main>`, the nav **logo** prints
  (page 1) and the **footer** prints (page 8: the brand line and `© 2026`).
- Starlight's previous/next pagination is inside `<main>`, so it was never chrome —
  the rows that called it "not on this route" were answering the wrong question.

For the five docs routes it establishes nothing either way. What is *dis*established
there, by CSS that is unambiguous on inspection, is the set of claims the withdrawn
rows made: the skip link cannot paint (`clip:rect(0,0,0,0)` until `:focus`), and the
table of contents cannot paint (`print:hidden` → `display:none` inside `@media
print` on `aside.right-sidebar-container`).

A precise per-element paint inventory needs an oracle none of the four probes
provided: paint, not layout, not computed style, not extracted text — and, on the
docs routes, one that does not depend on a chrome/content split the markup does not
make. Rather than ship a fifth guess, the column is withdrawn and registered as
`[backlog].open` slug `print-chrome-paint-inventory`.

**This does not touch AC13.** `close-stale` rests on § Measured axes 1 and 2, and
both have now reproduced twice on all six routes: **0** boxes past the printable
width and **0px** document overflow. Axes 3 and 4 also reproduced — page counts
8/3/4/12/12/12 and `<main>` character counts
5,588/3,260/3,842/14,992/13,397/15,488 — and are recorded as exercise evidence, not
as grounds for the disposition. No demonstrated content failure, and therefore no
print CSS from this programme.

## Residual, stated rather than hidden

Some navigation-only chrome still prints: on `/`, the nav logo and the footer. On the
five docs routes the question is open — Starlight keeps breadcrumb, pagination and
footer inside `<main>`, so the method that answered it for `/` has no purchase there.
Which elements precisely, and why each is or is not painted, is the withdrawn
inventory; this paragraph deliberately claims no more than that section supports.

What the evidence does show is that it **does not corrupt content** on § Measured
axes 1 and 2, the two `close-stale` rests on: no element exceeds the printable width,
and document horizontal overflow is 0px on all six routes. Axis 4 is
stated as what was actually measured — `<main>`'s rendered text length under print
media at 717px — rather than as "the body text reached the page", which would need
the PDF-versus-`<main>` comparison this file discredits in exactly that
string-matching direction. Whether the *presence* of surviving chrome is
worth removing is a legibility preference, not a demonstrated contract failure; the
decision rule prefers `close-stale` and bars proposing print rules from preference.
If a future reader wants it gone, that needs an observed failure first — and, given
the four failed probes above, an oracle for paint rather than layout.

## What this audit does not discharge

`workspace.toml [backlog].open` slug `docs-site-print-styles` remains open. It asks
whether the docs accent colours and hairlines are tuned for paper — an aesthetic
question. This audit measured the four axes in § Measured axes. Per-route navigation
visibility was attempted and withdrawn. `close-stale` here means no
demonstrated content failure, and therefore no print CSS from this programme. It
does not mean print is aesthetically finished, and the decision rule above bars
proposing rules from preference.

Also not measured: vertical overlap and page-break quality — orphaned headings,
unusable breaks, unexpected blank pages. Page COUNT is recorded; break quality is
not, and the two are not the same. Registered as `[backlog].open` slug
`print-audit-page-break-quality`.

Also not delivered: the per-element print-paint inventory, withdrawn above and
registered as `[backlog].open` slug `print-chrome-paint-inventory`.

## Acceptance bar

- `close-stale` requires all six rows to show acceptable defaults with no
  demonstrated contract failure. **Met**: six rows, zero failures, zero clipping,
  zero overflow.
- `shape` requires at least one exact failing row, the smallest necessary print
  rule, construction proof that reproduces the failure, emitted print/browser
  evidence after remediation, and an independently shippable owning spec.
- Mixed evidence cannot be generalized: acceptable routes keep defaults, and
  rules target only the demonstrated failing boundary.
