# Plan: architect-assess HTML report in the maintainer-view style

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** the shared family stylesheet in `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view-base.css` and its layout-file check `_layout_violations` in `packs/core/tests/skills/navigate-intents/test_export_html.py`; the decisions explorer's join of base plus layout into one hashed `<style>` and its asset placement beside the script in `packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer.py` and `explorer_assets/`; the family tokens in `docs/design/tokens/skill-html-views.md` (document view tracks, document density, interaction floor); the parity tool `tools/check_view_base_parity.py`, which finds every `view-base.css` under `packs/*/.apm/`; the renderer and its tests in `packs/architect/.apm/skills/architect-assess/scripts/render_html.py` and `packs/architect/tests/skills/architect-assess/test_render_html.py`. Deviation: the family's layout check bans `var(--c-` in a layout file; this report's layout file reads colour roles through it, because the family list-and-detail views have no tables, code blocks, provenance marks, or heat cells, and the owner decision is recorded in the token file.

> **Plan contract:** `Touches`, `Tests` and `Done when` are what a completion gate
> reads; `Design`, `Approach` and `Risks` are working material.

## Approach

Copy the family stylesheet into `scripts/report_assets/` beside the renderer, add the report layout file, and have the renderer read both through the confinement helper, refuse an unsafe asset, and join them into the one hashed `<style>`. Then change the markup into a document view: a header with a snapshot line, a skip link, a contents rail, and one flat section per heading with a margin head, with provenance marks, heat classes, and keyboard-scrollable table wrappers. The layout file arranges tracks and reads family tokens. The riskiest part is the look at narrow and wide widths, so browser QA with two design passes closes the work.

## Constraints

- AGENTS.md: reuse the repository's solution before adding one; the family stylesheet and document view tracks already exist.
- The parent spec's security rules stay in force; the closed lists widen only as the acceptance criteria name.
- `packs/AGENTS.md`: a non-cosmetic pack update also updates the pack's eval harness; a pack change bumps `pack.toml` and `plugin.json` together.

## Construction tests

**Integration tests:** one test renders the sample fixture and checks the header, skip link, rail, sections, marks, wrappers, banner, notice, CSP hash, and both lists together.
**Manual verification:** T7; the T5 browser pass produced fixes but no ledger, so the T7 ledger is the only browser record.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Token file additions | T4, T6 | diff | grep for the rule, marks, ramp, glyphs, and the 64rem deviation |
| Parent spec list criteria | T4 | diff | both cite this spec |
| Reference, guide, eval | T4 | grep, eval JSON test | named in each |
| Verification ledger | T7 | the ledger | screenshots and review results |
| Release surface | T4 | parity test, fragment | `validate` green |

## Design (LLD)

### Design decisions

- Stylesheet text is read at run time from `scripts/report_assets/` by the confined helper (family placement, beside the script), so the parity tool can byte-check the copy. `render(source, effort_name, today, css=None)` takes the joined text; `None` loads it, and `main` loads it first so an asset failure exits 3 before any render. Owned by: T1.
- An asset is refused before inlining when missing, over 64 KiB, not UTF-8, or holding `</style`, `<!--`, `url(`, or `@import` case-insensitively, each with its own fixed token. Owned by: T1.
- The page is a document view per the token file with one deviation recorded there: one column below 64rem, and from 64rem a margin track, a 68ch text track, and a `minmax(0, 1fr)` third track for tables and source blocks inside each section, plus a sticky 16rem contents rail in the page grid. The flexible third track receives only the space left after the text track reaches its 68ch, so prose is never starved; the body's `max-width` from 100rem bounds the page at wide screens. Below 64rem the contents control is the closed `details` above the text. Section heads are margin heads, inline above the section below 64rem. Document-density type sizes are set in the layout file as literals. Owned by: T3.
- Source order is skip link, header, nav, main; the skip link targets `main#report`, and `report` is reserved in the slug set so no heading can take it. Owned by: T2.
- The rail is one `nav` holding a closed `details` list for narrow widths and a `ul.rail-wide` of the same links for wide ones, because `open` cannot be set by width without script; the layout file shows one and hides the other at 64rem. Owned by: T2, T3.
- A section carries its heading's id and its `h2` carries none, so a followed rail link makes `.doc-section:target` match. Owned by: T2.
- Rail link text and a table wrapper's label come from one plain-text reduction of the heading's Markdown. Owned by: T2.
- A rail heading is a non-title heading at level 1 or 2, or an orientation heading at any level; one that is both gets one link. Link text is the heading's escaped plain text, never `_inline` output, so no anchor nests in an anchor. Owned by: T2.
- Sections start at every non-title level-1 or level-2 heading, matching `_scopes`; blocks before the first start a leading section with no margin head. Owned by: T2.
- Provenance marks reuse the base's `.mark` pill with a `--c-bg` fill and a `--c-rule-strong` outline; the glyphs are bars (▮▮▮, ▮▮▯, ▮▯▯, ▯▯▯) that share no shape with the family's eight state glyphs and carry empty alternative text. Heat cells use fills of surface, raised, and rule that rise in both themes, no border, and a level glyph (▂ ▄ ▆ ?) with empty alternative text that matches no evidence or state glyph, never the ok, warn, bad, active, or accent roles; the tables sit on the `--c-bg` surface. Owned by: T3.
- Colour contrast of each heat tint is computed in a test from the stylesheet's own token values for both themes. Owned by: T3.
- The snapshot line counts `Sources checked` rows by evidence class from the parsed tables. Owned by: T2.

## Tasks

### T1 — Stylesheet assets and loading

Depends on: none
Verification mode: TDD
Touches: `scripts/report_assets/view-base.css`, `scripts/report_assets/report.css` (a minimal first version), `scripts/render_html.py`, `packs/architect/tests/skills/architect-assess/test_render_html.py`
Tests: the copy equals the canonical file and the parity tool exits 0; the single `<style>` body equals base, one newline, layout; the CSP hash matches it; a missing, oversized, non-UTF-8, and forbidden-string asset each exit 3 with a fixed token and write no file.
Done when: the T1 tests pass.

### T2 — Markup

Depends on: T1
Verification mode: TDD
Touches: `scripts/render_html.py`, the test file, `packs/architect/tests/skills/architect-assess/testdata/html-style-sample.md`
Tests: the skip link first and its `#report` target never taken by a heading slug; the header, `page-title`, and the `meta` paragraph with the effort name, date, version, the `Confirmed` or `Unconfirmed` mark, and the exact `Sources:` count text over labeled orientation tables only; `alert` and `note` classes beside the existing banner and notice classes; the nav with `details` and `summary` text and the `rail-wide` list; rail links in source order with `#` hrefs, the plain-text reduction (`See [docs](https://x)` to `See docs`), one link for a heading that is both rail kinds, and `rail-sub`; sections carrying their heading's id with an id-less `margin-head`, a level-1 non-title heading starting a section, the leading section present and absent; marks as `span.mark.ev-*`; `div.table-scroll` with its attributes and the nearest-heading label; `part-head`; the element and attribute lists in full; `RENDERER_VERSION` equal to `2`; the existing banner, evidence, and heat tests updated to the new markup.
Done when: the T2 tests pass.

### T3 — Layout file

Depends on: T2
Verification mode: TDD
Touches: `scripts/report_assets/report.css`, the test file
Tests: the layout-file rule check over every declaration; the spacing-property rule; the document-density literals; the header mark, pill padding, indent, table, and `pre` rules; the four `::before` glyphs with `content: none` before them and empty alternative text, the fill, and the outline; no forbidden role in an `ev-` or `heat-` rule; the four heat fills and borders as named; the contrast computation in both themes; `.table-scroll` overflow; `inline-flex`, `align-items`, and `min-height` on the rail and skip links; the skip link shown on focus; the breakpoints, the details and wide-list switch, and the sticky rail with its `max-height`; the `:target` border; the print block; `overflow-wrap` on the title.
Done when: the T3 tests pass and the parity tool still exits 0.

### T4 — Docs, token file, parent amendment, eval, release

Depends on: T3
Verification mode: goal-based
Touches: `references/html-report.md`, `guides/architect/reference/architecture-assessment.md`, `docs/design/tokens/skill-html-views.md`, `docs/specs/architect-assess-html-report/spec.md`, `evals/evals.json`, `packs/architect/pack.toml`, `packs/architect/.claude-plugin/plugin.json`, a `tools/changelog.py new` fragment
Tests: grep for the style and the rail in both docs; the exit 3 row names the four asset refusals; the token file states the colour rule, the marks and their ranking, the ramp, the density literals, and the adopter; the parent's two list criteria cite this spec; the eval assertion exists; version parity and above `origin/main`; `tools/changelog.py validate`.
Done when: the T4 tests pass, `FORCE=1 make build-self` leaves only the expected projection diff, and the lint gate passes.

### T5 — Browser QA and design review

T5 ran the browser matrix and design passes and shipped the fixes they found in `render_html.py`, `report.css`, and the tests: source-block regions, print rules, the contents summary height, and the wide-screen body width. It wrote no ledger; T7 does.

Depends on: T4
Verification mode: manual QA
Touches: `docs/specs/architect-assess-html-report-style/notes/verification-ledger.md`
Tests: render the sample fixture and open it at 320 by 640, 1280 by 800, 1680, and 2560 CSS px in light and dark; read the first-screen, scrolled-rail, and first-Tab screenshots; then run `design-review` and `experience-reviewer` over the 1280 light, 1680 light, and 320 dark shots and adjudicate.
Done when: the observations and review results are in the ledger.

### T6 — Amended heat, tracks, and token file

Depends on: T5
Verification mode: TDD
Touches: `scripts/report_assets/report.css`, the test file, `docs/design/tokens/skill-html-views.md`, `tests/roster/test_architect_assess_style_docs.py`
Tests: heat fills as bg, raised, rule with no border, and a distinct level glyph per class with empty alternative text and none appearing in an evidence or state glyph; the contrast computation re-run against the new fills in both themes; the section grid's third track as `minmax(0, 1fr)`; the page grid, contents track, sticky rail, and details switch at 64rem with the skip-link placement and the 110rem body width staying at 100rem; the prose column at least 480px at 1024px, measured by the T7 browser pass; the token file text for the heat ramp, glyphs, pill styles, and the 64rem deviation.
Done when: the T6 tests pass.

### T7 — Browser QA and design review of the amended page

Depends on: T6
Verification mode: manual QA
Touches: `docs/specs/architect-assess-html-report-style/notes/verification-ledger.md`
Tests: render the sample fixture and open it at 320 by 640, 1280 by 800, 1680, and 2560 CSS px in light and dark, read the first-screen, scrolled-rail, first-Tab, and heat-map shots in both themes, then run `design-review` and `experience-reviewer` over the screenshot set the spec's design-review criterion names and adjudicate.
Done when: the observations and review results are in the ledger.

## Review

The change touches the page's security surface through the two lists, the asset reads, and the attributes, so the security-reviewer fires at REVIEW on T1 and T2, and the experience-reviewer on the rendered result.

## Risks

- The family stylesheet's selectors assume list-and-detail pages; some may not suit a long-form report, so T3 may leave a base rule unused.
- A static rail has no current-section highlight.
- Document-density sizes live in the layout file until the base gains a variant.

## Changelog

<!-- Approvals only. -->

- 2026-10-31: plan approved by eugenelim
