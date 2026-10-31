# Spec: architect-assess HTML report in the maintainer-view style

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`docs/specs/architect-assess-html-report/spec.md`](../architect-assess-html-report/spec.md) — the renderer's security rules stay in force: escaped values, a CSP naming the one `<style>` by hash, no script, no network. This spec owns the closed element and attribute lists from now on and amends the parent's element and attribute criteria to cite it. The family token file [`docs/design/tokens/skill-html-views.md`](../../design/tokens/skill-html-views.md) supplies the document-view tracks, type, spacing, and interaction floor.
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

A maintainer who opens an assessment report meets the same page family as the `navigate-intents` and `navigate-decisions` views and the `explain-diff` document view: the same header, colour roles, type, hairline rules, pills, and light and dark themes. The report reads top to bottom as a document, with a snapshot line under the title, a margin head per section, a contents rail beside the text on wide screens, and the evidence class of every source shown as a word and a shape.

## What Changes

- The renderer's stylesheet becomes a byte copy of the shared `view-base.css` plus a report layout file, joined into the one `<style>` element the content-security policy names by hash — `packs/architect/.apm/skills/architect-assess/scripts/render_html.py`, `scripts/report_assets/view-base.css`, `scripts/report_assets/report.css`.
- The page becomes a document view: a family header with a snapshot line, a skip link, a contents rail, and one flat section per heading with a margin head — `render_html.py`.
- Evidence classes become provenance marks, heat cells become a neutral ramp, tables sit in keyboard-scrollable wrappers — `render_html.py`, `report.css`.
- The element and attribute lists gain `header`, `nav`, and the attributes the page needs — `render_html.py`, the parent spec's list criteria.
- The family token file gains the provenance marks and the layout-file colour rule — `docs/design/tokens/skill-html-views.md`.
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

- [ ] `scripts/report_assets/view-base.css` equals `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view-base.css` byte for byte.
- [ ] The output's single `<style>` body equals the UTF-8 text of `view-base.css`, one newline, then the text of `report.css`.
- [ ] A missing stylesheet asset makes the renderer exit 3 with a fixed token and write no file.
- [ ] A stylesheet asset larger than 64 KiB of raw bytes makes the renderer exit 3 with a fixed token and write no file.
- [ ] A stylesheet asset that is not valid UTF-8 makes the renderer exit 3 with a fixed token and write no file.
- [ ] A stylesheet asset containing `</style`, `<!--`, `url(`, or `@import`, compared case-insensitively, makes the renderer exit 3 with a fixed token and write no file.
- [ ] `report.css` declares no colour literal (a `#` followed by 3, 4, 6, or 8 hex digits, a colour function, or a named colour), no custom property, no `font-family`, `font-weight`, or `font:`, no `box-shadow`, no `transition`, `animation`, or `scroll-behavior`, and no `border-radius` that is not a `var(--r-` reference.
- [ ] Every spacing value in `report.css` is `0`, `auto`, or a `var(--s-` reference, apart from the document-density type sizes and the track sizes the token file names.
- [ ] Every element in the parsed output is one of `html`, `head`, `meta`, `title`, `style`, `body`, `header`, `nav`, `main`, `section`, `div`, `span`, `p`, `h1`–`h6`, `ul`, `ol`, `li`, `table`, `thead`, `tbody`, `tr`, `th`, `td`, `pre`, `code`, `strong`, `em`, `a`, `details`, `summary`, `br`, or `hr`.
- [ ] Every attribute in the parsed output is one of `class`, `id`, `lang`, `charset`, `http-equiv`, `content`, `href` on an `a`, `aria-label` on a `nav` or a `div`, or `role` and `tabindex` on a `div`.
- [ ] The page's first focusable element is a link with class `skip-link` whose `href` is `#` followed by the id of the `main` element.
- [ ] The page's `h1`, with class `page-title`, sits inside a `header` with class `page-header`, followed by a `p` with class `meta` that holds the effort-directory name, the generation date, the renderer version, whether the checkpoints were confirmed, and the count of `Sources checked` rows for each of the four evidence classes.
- [ ] The unconfirmed banner has class `alert` as well as `banner-unconfirmed`, and the untrusted notice has class `note` as well as `notice-untrusted`.
- [ ] A `nav` with `aria-label` `Report sections` holds one `a` with class `question-link` per rail heading, in source order, with `href` equal to `#` followed by the heading's id and link text equal to the heading's escaped plain text, even when the heading holds a Markdown link; a rail heading is a non-title heading at level 1 or 2, or an orientation heading at any level, and one that is both gets one link.
- [ ] A rail link for an orientation heading deeper than level 2 carries class `rail-sub`.
- [ ] Every non-title heading at level 1 or 2 starts a `section` with class `doc-section` holding an `h2` with class `margin-head` and a `div` with class `doc-body` that holds every block up to the next such heading, and the blocks before the first such heading sit in a leading `section` with class `doc-section` and no `margin-head`.
- [ ] Each `Sources checked` row's evidence class renders as a `span` with classes `mark` and `ev-observed`, `ev-inferred`, `ev-reported`, or `ev-unknown`, holding the cell's text.
- [ ] `report.css` gives each of the four `ev-` classes a `::before` rule whose `content` is a bar glyph of its own (▮▮▮, ▮▮▯, ▮▯▯, ▯▯▯) with an empty alternative text after a plain fallback declaration.
- [ ] No `ev-` or `heat-` rule in `report.css` uses `--c-bad`, `--c-warn`, `--c-ok`, `--c-active`, or `--c-accent`.
- [ ] `report.css` gives each of `heat-low`, `heat-medium`, `heat-high`, and `heat-unknown` a `background` from a different `--c-` role, in the order canvas, raised, rule, then none for unknown with italic text.
- [ ] The text colour on each heat background reaches a contrast ratio of at least 4.5:1 in the light and in the dark theme, computed from the stylesheet's token values.
- [ ] Every table sits inside a `div` with class `table-scroll`, `role` `region`, `tabindex` `0`, and a fixed `aria-label`, and `report.css` gives that class horizontal overflow of `auto`.
- [ ] The `Sources checked:` label paragraph has class `part-head`.
- [ ] `report.css` gives `.question-link` and `.skip-link` a `min-height` of `var(--target)`.
- [ ] `report.css` sets the one-column, margin-and-text, and margin-text-and-contents tracks at 64rem and 100rem, with a text track of `minmax(0, 68ch)`, and makes the contents rail sticky from 100rem.
- [ ] `report.css` gives `.doc-section:target` an inset left bar.
- [ ] `report.css` has an `@media print` block that sets `display: none` on `.rail` and `.skip-link` and `overflow: visible` on `.table-scroll`.
- [ ] `report.css` gives `.page-title` `overflow-wrap: anywhere`.
- [ ] `references/html-report.md` and `guides/architect/reference/architecture-assessment.md` each state that the report uses the maintainer-view style with a contents rail.
- [ ] `docs/design/tokens/skill-html-views.md` states the layout-file colour rule, the four provenance marks, and the heat ramp.
- [ ] The parent spec's element and attribute criteria cite this spec as the owner of those lists.
- [ ] `evals/evals.json` has an assertion on the HTML report case that the page uses the maintainer-view style with a contents rail and provenance marks.
- [ ] `pack.toml` and `.claude-plugin/plugin.json` carry the same version, higher than the version on `origin/main`.
- [ ] `tools/changelog.py validate` passes with the new fragment present.
- [ ] Opened in a real browser from `packs/architect/tests/skills/architect-assess/testdata/html-style-sample.md` rendered, the page at 320 CSS px in light and dark shows one column with no horizontal page scroll, a visible banner and notice above the first section, and the contents list above the text, recorded with screenshots in the verification ledger.
- [ ] The same page at 1280 CSS px shows the margin heads beside the text, and at 2560 CSS px shows the sticky contents rail as a third track, each in light and dark, recorded with screenshots in the verification ledger.
- [ ] The same page shows a pill with a bar glyph for each of the four evidence classes and four distinct heat cells, in light and dark, recorded with screenshots in the verification ledger.
- [ ] A `design-review` and an `experience-reviewer` pass over the 1280 px light and 320 px dark screenshots leave no finding at Major or Blocker after adjudication, recorded in the verification ledger.

## Follow-ons

- eugenelim: [`docs/specs/architect-assess-html-report/notes/diagram-rendering-decision.md`](../architect-assess-html-report/notes/diagram-rendering-decision.md) — how diagrams are drawn in the browser.

## Assumptions

- Technical: document-density type sizes from the token file are set in the layout file as literals because the shared base carries only worklist density — whether the base should gain a document-density variant in every copy (settled by: the owner, as a follow-on).
- Product: the layout file reads colour roles through `var(--c-` where the family's list-and-detail layouts do not — whether to keep that rule or move the table and heat colours into the shared base (settled by: the owner; the token file records the rule).
- Technical: the contents rail has no current-section highlight because the page runs no script — whether a static rail is enough (settled by: the owner after the first look).
