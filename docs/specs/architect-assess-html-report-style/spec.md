# Spec: architect-assess HTML report in the maintainer-view style

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`docs/specs/architect-assess-html-report/spec.md`](../architect-assess-html-report/spec.md) — the renderer's security rules stay in force: escaped values, a CSP naming the one `<style>` by hash, no script, no network. This spec owns the closed element and attribute lists from now on and amends the parent's element and attribute criteria to cite it. The family token file [`docs/design/tokens/skill-html-views.md`](../../design/tokens/skill-html-views.md) supplies the document-view tracks, type, spacing, and interaction floor, except that this view starts its contents track at 64rem, not 100rem, and the token file records that deviation.
- **Brief:** none
- **Discovery:** none
- **Depends on:** spec:architect-assess-html-report
- **Contract:** none — a stylesheet, markup classes, and two asset files; no API, event, or RPC contract.
- **Shape:** ui — the look and structure of a generated read-only page.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`, `What
> Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working material.

## Outcome

A maintainer who opens an assessment report meets the same page family as the `navigate-intents` and `navigate-decisions` views and the `explain-diff` document view: the same header, colour roles, type, hairline rules, pills, and light and dark themes. Before scrolling, the reader sees what the report is, whether its checkpoints were confirmed, and where it begins. The report then reads top to bottom as a document, with a snapshot line under the title, a margin head per section, a contents rail beside the text on wide screens and a closed contents control on narrow ones, and the evidence class of every source shown as a word and a shape.

## What Changes

- The renderer's stylesheet becomes a byte copy of the shared `view-base.css` plus a report layout file, joined into the one `<style>` element the content-security policy names by hash — `packs/architect/.apm/skills/architect-assess/scripts/render_html.py`, `scripts/report_assets/view-base.css`, `scripts/report_assets/report.css`.
- The page becomes a document view: a family header with a snapshot line, a skip link, a contents rail, and one flat section per heading with a margin head — `render_html.py`.
- Evidence classes become provenance marks, heat cells become a neutral ramp with a level glyph, and tables and source blocks sit in keyboard-scrollable wrappers — `render_html.py`, `report.css`.
- The element and attribute lists gain `header`, `nav`, and the attributes the page needs — `render_html.py`, the parent spec's list criteria.
- The family token file gains the provenance marks, the heat ramp and its glyphs, the pill-style note, the 64rem contents track, and the layout-file colour rule — `docs/design/tokens/skill-html-views.md`.
- The release surface and the eval — `pack.toml`, `plugin.json`, a changelog fragment, `evals/evals.json`, `references/html-report.md`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | The report's layout file may read colour roles, unlike the family's list-and-detail views; provenance marks and heat tints are new | `docs/design/tokens/skill-html-views.md` | eugenelim | diff adding both | the file names the colour rule, the four provenance marks, and the heat ramp |
| Interface compatibility | The parent spec's element and attribute lists move here | `docs/specs/architect-assess-html-report/spec.md` | eugenelim | diff | the parent's two list criteria cite this spec as their owner |
| User-facing promise | The look and rail are part of what the mode promises | `references/html-report.md`, `guides/architect/reference/architecture-assessment.md` | eugenelim | grep | both name the maintainer-view style and the contents rail |
| Verification record | Browser and design review are manual | `docs/specs/architect-assess-html-report-style/notes/verification-ledger.md` | eugenelim | the ledger | holds the screenshots read and the review results |
| Release history | A pack change ships by version bump | `pack.toml`, `plugin.json`, changelog fragment | eugenelim | parity test, fragment validates | bump above `origin/main`, `Highlights` decided |

## Agent Rules

### Always do

- Treat every byte of `assessment.md` as untrusted; the style work never relaxes escaping or the closed lists.
- Take every colour, radius, and spacing value in the layout file from the family tokens.

### Ask first

- Any element, attribute, or CSP source beyond those the acceptance criteria name.
- Editing the copied `view-base.css`; the canonical file owns it.

### Never do

- Add a script, a web font, an image, or any network reference to the page.
- Declare a colour literal or redefine a family token in the layout file.
- Edit `navigate-intents` or `navigate-decisions` to make this work.

## Testing Strategy

- Stylesheet loading and refusals, layout-file rules, markup classes, rail, sections, marks, wrappers, lists, contrast: TDD, because each is an input-to-output rule over the rendered HTML or a text rule over a file.
- Parity of the stylesheet copy: goal-based check, the byte-equality test and `tools/check_view_base_parity.py`.
- Look, narrow and wide layout, light and dark, focus: manual QA in a real browser over the sample fixture, with `design-review` and `experience-reviewer` passes over the screenshots.

## Acceptance Criteria

### Stylesheet assets

- [x] `scripts/report_assets/view-base.css` equals `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view-base.css` byte for byte.
- [x] The output's single `<style>` body equals the UTF-8 text of `view-base.css`, one newline, then the text of `report.css`.
- [x] A missing stylesheet asset makes the renderer exit 3 with a fixed token and write no file.
- [x] A stylesheet asset larger than 64 KiB of raw bytes makes the renderer exit 3 with a fixed token and write no file.
- [x] A stylesheet asset that is not valid UTF-8 makes the renderer exit 3 with a fixed token and write no file.
- [x] A stylesheet asset containing `</style`, `<!--`, `url(`, or `@import`, compared case-insensitively, makes the renderer exit 3 with a fixed token and write no file.
- [x] `RENDERER_VERSION` equals `2`.

### Layout-file rules

- [x] `report.css` declares no colour literal (a `#` followed by 3, 4, 6, or 8 hex digits, a colour function, or a named colour), no custom property, no `font-family`, `font-weight`, or `font:`, no `box-shadow`, no `transition`, `animation`, or `scroll-behavior`, and no `border-radius` that is not a `var(--r-` reference.
- [x] In `report.css`, the properties `margin`, `padding`, `gap`, `row-gap`, `column-gap`, and their side forms hold only `0`, `auto`, or a `var(--s-` reference.
- [x] `report.css` sets `font-size` and `line-height` of `1.75rem` and `1.2` on `.page-title`, `1.3125rem` and `1.3` on `.doc-body h3`, `1.0625rem` and `1.6` on `.doc-body`, `0.875rem` and `1.5` on `.meta`, and `0.75rem` and `1.3` with uppercase text on `.margin-head` and `.part-head`.
- [x] `report.css` gives `.page-title::before` a `display`, `.mark` padding, `.rail-sub` an indent, `table` `border-collapse: collapse`, and `pre` overflow `auto`.

### Closed lists

- [x] Every element in the parsed output is one of `html`, `head`, `meta`, `title`, `style`, `body`, `header`, `nav`, `main`, `section`, `div`, `span`, `p`, `h1`–`h6`, `ul`, `ol`, `li`, `table`, `thead`, `tbody`, `tr`, `th`, `td`, `pre`, `code`, `strong`, `em`, `a`, `details`, `summary`, `br`, or `hr`.
- [x] Every attribute in the parsed output is one of `class`, `id`, `lang`, `charset`, `http-equiv`, `content`, `href` on an `a`, `aria-label` on a `nav` or a `div`, `role` and `tabindex` on a `div`, or `data-mark` and `aria-hidden` on a `span`.
- [x] The parent spec's element and attribute criteria cite this spec as the owner of those lists.

### Structure and first screen

- [x] The page's first focusable element is a link with class `skip-link` whose `href` is `#report`, and the `main` element has the id `report`, which no heading id equals even when a heading's text slugs to `report`.
- [x] `report.css` shows `.skip-link` in the page's flow, unclipped, whenever it has focus.
- [x] The page's `h1`, with class `page-title`, sits inside a `header` with class `page-header`, followed by a `p` with class `meta`.
- [x] The `meta` paragraph holds the effort-directory name, the generation date, and the renderer version.
- [x] The `meta` paragraph holds a `span` with classes `mark` and `data-mark` `approved` and text `Confirmed` when the charter confirms the checkpoints, and `data-mark` `draft` and text `Unconfirmed` otherwise, each with an `aria-hidden` glyph `span` of class `mark-g`.
- [x] The `meta` paragraph ends with the text `Sources: N observed, N inferred, N reported, N unknown`, counting the data rows of every labeled `Sources checked` table inside an orientation subsection by evidence class.
- [x] The unconfirmed banner has class `alert` as well as `banner-unconfirmed`, and the untrusted notice has class `note` as well as `notice-untrusted`.
- [x] `report.css` gives `.notice-untrusted` a border and padding.
- [x] `nav` holds, in this order, a `details` with a `summary` reading `Contents (N sections)`, where N is the number of rail headings, containing a `ul` of rail links, and a `ul` with class `rail-wide` of the same rail links.
- [x] Each rail link is an `a` with class `question-link`, in source order, whose `href` is `#` followed by the id of its target.
- [x] A rail link's text is its heading's plain text, with Markdown link, code, bold, and emphasis syntax reduced to the text inside it, so that the heading `See [docs](https://x)` gives `See docs`.
- [x] A rail heading is a non-title heading at level 1 or 2, or an orientation heading at any level, and one that is both gets one link per list.
- [x] A rail link for an orientation heading deeper than level 2 carries class `rail-sub`.
- [x] Every non-title heading at level 1 or 2 starts a `section` with class `doc-section` that carries the heading's id, holds an `h2` with class `margin-head` and no id, and holds a `div` with class `doc-body` with every block up to the next such heading.
- [x] A `section` with class `doc-section` and no `margin-head` holds the blocks before the first such heading, and no such section is emitted when no block precedes it.
- [x] `report.css` makes the `details` the visible contents control and hides `.rail-wide` below 64rem, and hides the `details` and shows `.rail-wide` from 64rem.

### Tables, marks, heat

- [x] Every table sits inside a `div` with class `table-scroll`, `role` `region`, `tabindex` `0`, and an `aria-label` of `Table: ` followed by the plain text of the nearest preceding heading, or `Table` when none precedes it, and `report.css` gives that class horizontal overflow of `auto`.
- [x] The `Sources checked:` label paragraph has class `part-head`.
- [x] Each `Sources checked` row's evidence class renders as a `span` with classes `mark` and `ev-observed`, `ev-inferred`, `ev-reported`, or `ev-unknown`, holding the cell's text.
- [x] `report.css` gives each `ev-` class a `content: none` declaration followed by a `::before` `content` of its own bar glyph (▮▮▮, ▮▮▯, ▮▯▯, ▯▯▯) with an empty alternative text, a `var(--c-bg)` background, and a `var(--c-rule-strong)` border.
- [x] No `ev-` or `heat-` rule in `report.css` uses `--c-bad`, `--c-warn`, `--c-ok`, `--c-active`, or `--c-accent`.
- [x] `report.css` gives `heat-low` a `var(--c-bg)` background, `heat-medium` a `var(--c-raised)` background, `heat-high` a `var(--c-rule)` background, and `heat-unknown` a `var(--c-bg)` background with italic text, and none of the four a border.
- [x] `report.css` gives each heat class a `content: none` declaration followed by a `::before` `content` of its own level glyph (▂ for low, ▄ for medium, ▆ for high, ? for unknown) with an empty alternative text.
- [x] No heat glyph appears in any evidence glyph (▮ ▯) or in any of the family's eight state glyphs (● ▶ ◆ ◇ ■ ✕ △ ✓).
- [x] The text colour reaches a contrast ratio of at least 4.5:1 on each of the four heat backgrounds in the light and in the dark theme, computed from the stylesheet's token values.
- [x] `report.css` gives `.question-link` and `.skip-link` `display: inline-flex`, `align-items: center`, and a `min-height` of `var(--target)`.

### Layout and print

- [x] `report.css` sets one column below 64rem, a margin track and a `minmax(0, 68ch)` text track from 64rem, a third track of `minmax(0, 1fr)` in each section grid, and a contents track of 16rem in the page grid from 64rem.
- [x] `report.css` makes the contents rail sticky from 64rem with a `max-height` and vertical overflow of `auto`.
- [x] `report.css` gives `.doc-section:target` a 3px solid left border in `var(--c-accent)`.
- [x] `report.css` has an `@media print` block that sets `display: none` on `.rail`, `.skip-link`, and the `details`.
- [x] The `@media print` block sets `overflow: visible` on `.table-scroll` and `.source-scroll`.
- [x] The `@media print` block sets `overflow: visible` and `white-space: pre-wrap` on `pre`.
- [x] The `@media print` block sets `break-inside: avoid` on `tr`.
- [x] Every code fence and every diagram source block sits inside a `div` with class `source-scroll`, `role` `region`, `tabindex` `0`, and an `aria-label` of `Source: ` followed by the plain text of the nearest preceding heading, or `Source` when none precedes it.
- [x] `report.css` gives `.source-scroll` horizontal overflow of `auto`.
- [x] `report.css` gives `.rail summary` a `min-height` of `var(--target)`.
- [x] From 100rem, `report.css` gives `body` a `max-width` of `110rem` with `margin-left` and `margin-right` of `auto`.
- [x] `report.css` gives `.page-title` `overflow-wrap: anywhere`.

### Fixture, docs, release

- [x] `packs/architect/tests/skills/architect-assess/testdata/html-style-sample.md` models a multi-subsystem system: at least six subsystem entries under `Architecture by subsystem`, with a deeper child heading under two of them; a `Sources checked` table of at least twelve rows under `Overall architecture` using all four evidence classes; a heat map of at least eight rows using all four heat values; a table cell holding an unbroken identifier of at least 80 characters; an unconfirmed charter; and at least two Mermaid fences of eight or more nodes each, one flowchart and one sequence diagram.
- [x] `references/html-report.md` and `guides/architect/reference/architecture-assessment.md` each state that the report uses the maintainer-view style with a contents rail.
- [x] The exit 3 row of `references/html-report.md` lists a missing, an oversized, a non-UTF-8, and a forbidden-string stylesheet asset.
- [x] `docs/design/tokens/skill-html-views.md` states the layout-file colour rule, the four provenance marks and that their bars imply a ranking from observed to unknown, the heat ramp with its fills and level glyphs, that the status pill is filled and the provenance pill outlined on purpose, that this view's contents track starts at 64rem as a deviation from the document-view table, the document-density literals this view sets, and `architect-assess` as an adopter.
- [x] `evals/evals.json` has an assertion on the HTML report case that the page uses the maintainer-view style with a contents rail and provenance marks.
- [x] `pack.toml` and `.claude-plugin/plugin.json` carry the same version, higher than the version on `origin/main`.
- [x] `tools/changelog.py validate` passes with the new fragment present.

### Real browser

- [x] Rendered from the fixture and opened in a real browser, the first screen at 320 by 640 CSS px and at 1280 by 800 CSS px, in light and dark, shows the title, the snapshot line, the banner, and the first section's margin head, with the closed contents control above the text at 320 px and the contents list beside the text at 1280 px, recorded with screenshots in the verification ledger.
- [x] At 320 CSS px in light and dark, the page is one column and the screenshot shows no content clipped at the right edge, recorded in the verification ledger.
- [x] At 1024 CSS px, in light and dark, the prose column measures at least 480 CSS px, recorded in the verification ledger.
- [x] At 1280, 1680, and 2560 CSS px the margin heads sit beside the text and the contents list is a third track that stays in view in a screenshot taken after scrolling past its first position, each in light and dark, recorded in the verification ledger.
- [x] The first Tab press at 320 and 1280 CSS px shows the skip link with the family focus ring, recorded in the verification ledger.
- [x] The page shows a pill with a bar glyph for each of the four evidence classes, and the low, medium, and high heat cells rise in fill in light and in dark while the unknown cell differs from low by its glyph and italic text, recorded with screenshots of the heat map in both themes in the verification ledger.
- [x] A `design-review` and an `experience-reviewer` pass over the 1280 px light, 1680 px light, 320 px dark, and 1280 px dark heat-map screenshots leave no finding at Major or Blocker after adjudication, recorded in the verification ledger.

## Terminal Intent

`code` — add the stylesheet assets, the document-view markup, the layout file, the docs and token-file updates, and the release surface.

## Follow-ons

- eugenelim: [`docs/specs/architect-assess-html-report/notes/diagram-rendering-decision.md`](../architect-assess-html-report/notes/diagram-rendering-decision.md) — how diagrams are drawn in the browser.

## Assumptions

- Technical: a `heat-high` cell's fill equals the row rule colour, so its bottom rule blends into the fill; the level glyph carries the level — whether that is acceptable (settled by: the owner, after the first look).
- Technical: document-density type sizes from the token file are set in the layout file as literals because the shared base carries only worklist density — whether the base should gain a document-density variant in every copy (settled by: the owner, as a follow-on).
- Product: the layout file reads colour roles through `var(--c-` where the family's list-and-detail layouts do not — whether to keep that rule or move the table and heat colours into the shared base (settled by: the owner; the token file records the rule).
- Technical: diagrams in the fixture appear as labeled source blocks because drawing them is the open decision in `notes/diagram-rendering-decision.md` — whether and how the style slice should later draw them (settled by: the owner, in a later spec).
- Technical: the contents rail has no current-section highlight because the page runs no script, and the narrow contents control is a closed `details` and a duplicate wide list because `open` cannot be set by width — whether that is enough (settled by: the owner after the first look).
- Technical: older engines without alternative text on generated content show no glyph, since the fallback is `content: none` and the word carries the class — whether that is acceptable (settled by: the owner).

## Changelog

<!-- Approvals only. -->

- 2026-10-31: spec approved by eugenelim (layout file reads colour tokens)
- 2026-10-31: spec amendment approved by eugenelim (heat, contents track, print, source regions)
