# Spec: Decision view style

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0108 (D1 rules 3, 4, 5, 8, 9 and 10; D2), RFC-0105
- **Depends on:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer who opens the `navigate-decisions` HTML explorer meets the same page family as the `navigate-intents` view: the same header, soft list and detail zones, state pills, type, colour and motion. They pick a decision by its title, read its detail beside the list, and use every width from 320 to 2560 CSS px in light and dark with nothing they learned in the intents view working differently.

This release is a step toward RFC-0108 D5 step 2, not the adoption itself: `navigate-decisions` counts as adopted, and D1 binds it, from the release that ships `decision-view-questions`.

## What Changes

- The explorer's stylesheet becomes a byte copy of the shared `view-base.css` plus a decisions layout file, joined into one `<style>` element that the content-security policy names by hash. `'unsafe-inline'` leaves the policy — `packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer.py`, `explorer_assets/`.
- The header becomes the intents view's compact header: title, search, Kind and Status filters, and one snapshot line carrying the time, counts and the reference-policy sentence. The gradient title, the five count tiles, the callout box and the Auto / Light / Dark switch go; the page follows the system theme.
- The list and the record detail sit side by side as two soft zones. The List, Graph and Context views switch inside the list zone; the separate Detail tab goes.
- A list row leads with the record's title, shows its lifecycle as a word plus a shape, and moves the id to secondary text.
- The Legend becomes an on-demand Key in the list zone; support references and provenance stay collapsed at the end of the list zone.
- The lineage diagram takes its colours and type from the shared stylesheets, so it follows the dark theme, and the scripts write no inline styles.
- `SKILL.md` and repo-governance's version (2.3.0 → 2.4.0) describe the new view.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | The skill's export section describes the theme switch, which goes | `packs/repo-governance/.apm/skills/navigate-decisions/SKILL.md` § Export, and its built projections | navigate-decisions owner | Text names the system-following theme and the side-by-side detail; no theme-switch sentence | `make build-self` leaves no diff |
| Current product truth | Not applicable: no page under `guides/` describes the explorer's look; `SKILL.md` is its only user-facing description | none | — | — | — |
| Release history | Visible change to a shipped skill | `docs/product/changelog.d/<uuid>.md` for repo-governance 2.4.0; `pack.toml` and `plugin.json` version | navigate-decisions owner | Fragment and both versions at 2.4.0 | Fragment lints clean |
| Decision rationale | RFC-0108 D5 already decides this step | none — RFC-0108 D5 owns this step toward adoption; no new decision is taken | — | — | — |
| Design tokens | The token file § Unresolved leaves the lineage diagram's colours to this view's adoption work, which this spec settles | `docs/design/tokens/skill-html-views.md` § Unresolved | navigate-decisions owner | Entry reworded to name the `--c-` roles the diagram uses | Entry matches the shipped classes |
| Activation evals | Not applicable: the skill's description and triggers do not change, so `evals/eval_queries.json` has nothing new to route | none | — | — | — |
| Verification record | Browser evidence and owner approval | `docs/specs/decision-view-style/notes/verification-ledger.md` and `notes/screens/` | implementer | Ledger rows for AC-0016 to AC-0019 | Every row filled |

## Agent Rules

### Always do

- Edit the canonical `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view-base.css` and every copy in one change if the shared style needs a change, and bump each affected pack.
- Keep every shipped decision-navigation acceptance criterion true, in particular its criteria 0008, 0010, 0016, 0021, 0023, 0025, 0026 and 0027 in `docs/specs/decision-navigation/spec.md`.
- Run `make build-self` after editing pack sources and commit the regenerated projections.

### Ask first

- Any change to the canonical `view-base.css`, since it also changes the intents view and needs a core version bump.
- Any change to the export payload, the query envelope, or the data the JSON block carries.
- Removing or renaming any visible control beyond the theme switch, the count tiles and the Detail tab this spec names.

### Never do

- No new dependency, no new module boundary, and no new top-level directory.
- No `'unsafe-inline'`, `'unsafe-eval'` or inline `style` attribute anywhere in the export, and no `url(` or `@import` in either stylesheet. Same-document SVG references such as `marker-end="url(#…)"` set by script stay allowed.
- No change to record admission, lineage derivation, trust classes or source-link rules.
- No question rail, no new grouping and no new ordering; those belong to the next slice.

## Testing Strategy

- **Policy, join and stylesheet rules (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0020, AC-0021, AC-0022, AC-0024):** TDD. They are string properties of the emitted file and the asset files, so contract tests in `test_html_publication.py` decide them without a browser.
- **Rendered layout, marks and themes (AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0023, AC-0025, AC-0026, AC-0027):** scripted Chromium checks in `browser_checks.py`, because computed styles, rectangles and contrast exist only in a rendered page.
- **Regression of the shipped contract (AC-0016, AC-0017):** goal-based. The existing suites run unchanged except for tests the ledger lists under AC-0016's rule, each with the shipped `decision-navigation` criterion it verified and its replacing assertion, and the real-export counts are compared before and after.
- **Whole-page judgement (AC-0018, AC-0019):** visual and manual QA on a real export of this repository, with screenshots, an `experience-reviewer` pass and the owner's approval recorded in the ledger.

## Acceptance Criteria

Unless a criterion names another fixture, it is checked on a full export of the `mixed` fixture corpus, opened from local disk. **Width and theme matrix** means true viewport widths of 320, 1280, 1680 and 2560 CSS px, each in the light and the dark theme, over the `mixed` and `negative/hostile` exports. **Its background** means the computed `background-color` of the nearest ancestor-or-self element whose computed `background-color` has a non-zero alpha. **The token file** is `docs/design/tokens/skill-html-views.md`. **Each view** means the List view, the Graph view with the first chain in its display order selected (in `mixed`, ADR-0001 superseded in part by ADR-0020), or, where the export holds no chain, the Graph view as it first opens, and the Context view. **An SVG text's background** is the computed `fill` of the topmost shape drawn before it, in the same or an ancestor group, whose computed `fill` is not `none` and whose box contains the text's box; with no such shape, it is the zone's background. **Colour equality** compares the two values as sRGB channels, each token resolved by assigning `var(--c-…)` to a probe element's `color` and reading the computed value. **A list row** is the `.row-link` control that picks one record in the List view; the record's supersession marker sits beside it in the same `.row`, never inside it. **The explorer's scripts** are `explorer.js`, `lineage.js` and `markdown.js` under `explorer_assets/`.

### Policy and join

- [x] **AC-0001.** The export contains exactly one `<style>` element, and its content is the UTF-8 text of the explorer's `view-base.css`, then the text of its decisions layout file, with nothing between them.
- [x] **AC-0002.** The content-security policy's `style-src` is exactly one `'sha256-…'` source equal to the base64 SHA-256 of that `<style>` element's content, and the policy contains neither `'unsafe-inline'` nor `'unsafe-eval'` anywhere.
- [x] **AC-0003.** The explorer's `view-base.css` is byte-identical to the canonical copy, and `tools/check_view_base_parity.py` reports it among the files it checks.
- [x] **AC-0004.** The emitted HTML contains no `style=` attribute, and neither stylesheet contains `url(` or `@import`, compared case-insensitively.
- [x] **AC-0020.** The explorer's scripts, comments removed, contain no `.style` token, no `cssText`, and no `'style'` or `"style"` string literal.
- [x] **AC-0027.** Across the width and theme matrix, in each view, after a record is picked, the Graph view's contextual relationships are shown and a diagram node has focus, no element in the document carries a `style` attribute.

### Layout file rules

- [x] **AC-0005.** The decisions layout file declares no colour literal (hex, `rgb(`, `hsl(`, any other CSS colour function, or a named colour), no `font-family`, `font-weight` or `font` shorthand, no `box-shadow`, no `border-radius` whose value is not a `var(--r-` reference, no `transition*` or `animation*` property, and no `--` custom property.
- [x] **AC-0006.** The explorer's scripts, comments removed, contain no colour literal in any form: no `#` followed by 3, 4, 6 or 8 hex digits inside a string, no `rgb(`, `rgba(`, `hsl(`, `hsla(`, `hwb(`, `lab(`, `lch(`, `oklab(`, `oklch(` or `color(`, and no CSS named colour as a whole string literal other than `none`, `transparent` and `currentColor`.
- [x] **AC-0021.** The explorer's scripts set no `font-family`, `font-weight`, `font-size` or `font` attribute on any element.
- [x] **AC-0007.** The export contains no element with the id `theme-toggle` or `stat-cards`, no `data-theme-choice` attribute, and no `localStorage` token in its script.
- [x] **AC-0024.** The header's snapshot line's text contains the export's total record count and, for each kind in the export's `summary.by_kind`, its count followed by the kind's name, singular for a count of one and plural otherwise ("1 ADR", "109 RFCs"), each equal to the export's `summary`.
- [x] **AC-0022.** The header's snapshot line contains, as an exact substring of its text content, the `BOUNDARY_NOTICE` string defined in `navigate_decisions.py`.

### Rendered page

- [x] **AC-0008.** Across the width and theme matrix, in each view, the list zone and the detail zone each compute a non-zero `border-radius` and a `box-shadow` other than `none`, and every list row computes `box-shadow` as `none` or as inset shadows only.
- [x] **AC-0009.** At 1280, 1680 and 2560 CSS px, with a record picked, the detail zone's left edge is at or right of the list zone's right edge and their vertical extents overlap; at 320 CSS px, with a record picked, the detail zone's top edge is at or below the list zone's bottom edge, or the list zone is hidden.
- [x] **AC-0010.** Across the width and theme matrix, in each view, with the first row picked, no element inside the list zone or the detail zone has a `getBoundingClientRect()` extending more than 1 CSS px past the left or right edge of its zone, and the document's `scrollWidth` does not exceed the viewport width. The one exception is a descendant of a diagram scroll container: an element whose computed `overflow-x` is `auto` or `scroll`, that has `tabindex="0"` and an accessible name; that container itself meets the edge test.
- [x] **AC-0011.** At 2560 CSS px, the union of the header and the two zones spans the viewport width less at most twice the `--s-5` page padding plus 2 CSS px.
- [x] **AC-0012.** In every list row, the record's title is the first text in DOM order, and the record id appears in the same row only after it.
- [x] **AC-0013.** Every list row and the detail state line carry one `.mark` element whose `data-mark` follows this map from the lifecycle value's first run of letters, compared case-insensitively: `accepted` → `approved`; `experimental` → `active`; `proposed`, `draft`, `open` and `final` → `draft`; `superseded`, `deprecated`, `rejected` and `withdrawn` → `done`; any other word, and no lifecycle value, → `draft`. Its visible text is a glyph hidden from assistive technology, then the record's lifecycle `display_value`, or "No status" when there is none. Checked on the `mixed` fixture, which holds `Accepted (superseded in part by ADR-0020 for D3)`, and on a `lifecycle-marks` fixture holding one record for each of `accepted` (lowercase), `Experimental`, `Proposed`, `Open`, `Final Comment Period`, `Superseded`, `Deprecated`, `Rejected`, `Withdrawn`, an unknown word, and no status line.
- [x] **AC-0014.** Across the width and theme matrix, in each view, every text element, SVG `text` included and measured against its SVG background, in the header, the list zone and the detail zone has a contrast ratio of at least 4.5:1 against its background, and the border of the search field, of every `select` and of every bordered `button` has at least 3:1.
- [x] **AC-0015.** With `prefers-reduced-motion: reduce`, every rendered element computes every `transition-duration` and `animation-duration` as `0s`; with `no-preference`, a list row computes a `transition-duration` greater than `0s`.

- [x] **AC-0023.** Across the width and theme matrix, in the Graph view, every SVG element under the diagram computes a `fill` and a `stroke` that is `none` or, under colour equality, equals one of the `--c-` custom properties declared on `:root` in that theme.

- [x] **AC-0025.** With a record picked whose body holds headings, every heading element inside the record-content container computes a `font-size` smaller than both the page `h1`'s and the detail heading's.
- [x] **AC-0026.** At 320 CSS px, with a record picked from any view and the list zone hidden, the detail zone holds a button named "Back to list" that, activated by Enter or Space, shows the list zone again in the view that was current; when that view is List or Graph, the picked record's list row or diagram node carries `aria-current="true"`.

### Regression and review

- [x] **AC-0016.** Every test in `test_html_publication.py`, `test_query_contract.py` and `browser_checks.py` at the base commit passes against this change unedited, except tests the verification ledger lists one by one. Each listed test names the shipped `decision-navigation` criterion it verified and the replacing assertion that still verifies that criterion against the new markup; a test may be removed without replacement only when what it checks is the theme switch, the count tiles or the Detail tab, which this spec removes.
- [x] **AC-0017.** An export over this repository at the final code commit shows the same record count, the same count per kind and per lifecycle value, and the same number of relationships as an export at the base commit, and the ledger records both commands, file sizes and counts.
- [x] **AC-0018.** An `experience-reviewer` pass over screenshots of the real export across the width and theme matrix, against RFC-0108 D1 rules 3, 4, 5, 8, 9 and 10 and the `skill-html-views` direction's ranked goals, leaves no Major or Blocker finding after adjudication, recorded in the ledger.
- [x] **AC-0019.** The owner records in the ledger, with the date, that the real export at the final code commit matches the `navigate-intents` view's visual identity.

## Follow-ons

- eugenelim: `docs/specs/decision-view-questions/spec.md` (to be authored) — the question rail (Recently decided, Still being decided, Replaced, By area, Lineage, Browse all) and a detail that leads with action, completing RFC-0108 D1 rules 1, 2, 6 and 7 for this view.

## Assumptions

- Product: AC-0013 maps every lifecycle word the ADR and RFC templates define; an adopter's own word falls back to `draft` with its own text — what it would change: one row of AC-0013's map (settled by: the owner, if an adopter's vocabulary needs another mark).
