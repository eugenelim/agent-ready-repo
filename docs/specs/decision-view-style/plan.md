# Plan: Decision view style

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** RFC-0108 D2 and `docs/design/tokens/skill-html-views.md` § Layout and § State marks (source); `packs/core/.apm/skills/navigate-intents/scripts/intent_view.py` lines 187–200, which joins `view-base.css` and `view.css` into one hashed style (analogous implementation); `packs/core/tests/skills/navigate-intents/view_browser_checks.py` and `docs/specs/intent-view-source-and-style/` (tests and precedent criteria); `tools/check_view_base_parity.py` (construction path). Deviation: the decisions view has no question rail in this slice, so it uses the worklist tracks without the rail column.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure.

## Approach

The work lands in four tasks. T1 swaps the stylesheet plumbing first: copy `view-base.css`, join it with today's `explorer.css` into one hashed `<style>`, and drop `'unsafe-inline'`. That keeps the page working with the old markup while the policy tightens, so the riskiest change (a policy that silently drops styles) is proven in isolation. T2 rebuilds the header and the two zones on the shared classes, checked in the List and Context views. T3 restyles rows, marks and the lineage diagram, finishes the `explorer.css` rewrite, and only then adds the layout-file lint and the Graph-view runs of the zone and overflow checks, since those need the diagram wrappers T3 builds. T4 updates docs and the version, captures screens, and runs review.

The riskiest part is keeping the shipped decision-navigation browser checks green while their selectors move. Each edit to an existing test is listed in the ledger with the shipped criterion it verifies and its replacing assertion (spec AC-0016).

A probe on 2026-10-27 in Playwright's Chromium confirmed that a hashed `style-src` applies the `<style>` element with no policy violation. RFC-0108 rule 10 still forbids inline style attributes, so T3 removes the `element.style` writes in `lineage.js` too (spec AC-0020).

## Constraints

- RFC-0108 D2: one canonical stylesheet in `navigate-intents`, byte-copied; the view's own layout rules live in a second file that never overrides a shared colour, type or state-mark rule.
- RFC-0108 D1 rule 10 and errata of 2026-10-16: motion only under `prefers-reduced-motion: no-preference`, at most 200ms.
- `docs/specs/decision-navigation/spec.md` shipped criteria stay true (spec Agent Rules).
- Root `AGENTS.md`: no new dependency; `make build-self` regenerates `.agents/` and `.claude/` projections.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** T4's screenshot matrix, `experience-reviewer` pass and owner approval.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `SKILL.md` § Export and projections | T4 | Theme-switch sentence replaced | `make build-self` leaves no diff |
| Changelog fragment and 2.4.0 versions | T4 | Fragment file, `pack.toml`, `plugin.json` | Changelog lint clean |
| Verification ledger and screens | T1–T4 | Ledger rows, `notes/screens/*.png` | Rows for AC-0016 to AC-0019 filled |

## Design (LLD)

### Design decisions

- **Layout file name.** `explorer_assets/explorer.css` is rewritten in place as the decisions layout file, so `_load_asset` and the asset list do not change. Traces to: AC-0001, AC-0005. Owned by: T1, T2.
- **Theme.** The page follows `prefers-color-scheme` through `view-base.css`; the switch, its `localStorage` key and its `data-theme` attribute go. Traces to: AC-0007. Owned by: T2.
- **Detail placement.** The detail zone is always present beside the list. Picking a row, a graph node or a lineage link fills it. The Detail nav button goes; the List, Graph and Context buttons become a segmented control (`.seg-btn`) at the top of the list zone. Browser history keeps recording view-and-selection states. A `#list/<id>`, `#graph/<id>` or `#context/<id>` hash opens that view with the record picked; a `#detail/<id>` hash, which supersession links and old bookmarks use, opens the view that was current (List on a cold load) with that record picked. At 320 CSS px the detail zone's "Back to list" button returns to the list zone (spec AC-0026). Traces to: AC-0009; keeps decision-navigation criteria 0016 and 0023. Owned by: T2.
- **Mark map.** The map and the word shown are spec AC-0013's. It reuses the intents glyphs for the four marks it can produce: ● active, ◆ approved, ◇ draft, ✓ done. Traces to: AC-0013. Owned by: T3.
- **Supersession marker.** The decision-navigation criterion 0025 marker stays in the row and at the top of detail. It uses the shared `.notice` pattern, whose `--c-warn-bg` tint the token file § Colour assigns to notices, and carries no state mark, so no state tint sits behind a word that is not its own. Traces to: AC-0008, AC-0014. Owned by: T3.
- **Diagram colours and type.** `lineage.js` sets classes (`ln-edge-checked`, `ln-edge-partial`, `ln-edge-unresolved`, `ln-edge-context`, `ln-edge-asserted`, `ln-node`, `ln-node-focus`, `ln-label`) instead of `fill`, `stroke`, `font-weight` and `font-size` attributes. This covers the colours passed through variables and the style table (around lines 411–420, 724 and 773–784) and the named `'white'` at line 192. The layout file styles the classes with `var(--c-…)` tokens and the shared type scale. Line style (dash pattern, width) stays in attributes, since it carries meaning and is not colour.
- **No inline styles.** Show and hide use the `hidden` attribute or a class; the scroll wrappers' `overflow-x: auto` and `max-width: 100%` move to `.lineage-wrap` and `.chain-svg-wrap` in the layout file, and each wrapper gets `tabindex="0"`, `role="group"` and an `aria-label` so it is a keyboard-scrollable container. Traces to: AC-0020, AC-0010. Owned by: T3.

Owned by: T1, T2, T3

### Component / module decomposition

Owned by: T2, T3

- `explorer.py` `_build_html`: header (title, search, the Kind filter as All / ADR / RFC `.seg-btn` buttons as today, the Status `select`, the snapshot line with counts, the boundary sentence, and the bounded-mode `.notice` when the export is bounded), then `.zones` holding `section.worklist` (a toolbar with the List / Graph / Context `.seg-btn` control and Expand all, the Key `details` that replaces the Legend, the three view regions, then the support-inventory and provenance `details`) and `aside.detail`. Legend becomes Key to match the intents view; that rename and the Detail tab's removal are the only visible control changes beyond the theme switch and count tiles.
- `explorer.js`: the list renderer emits one `li.row` per record holding a `button.row-link` (title cell, mark cell, context cell with kind and id), so the shared `.row-link` target size, hover, current inset and fade apply; the supersession marker and its links follow the button inside the `li`, never nested in it. The detail renderer writes into `aside.detail`. Record-body headings are sized below `--t-title` in `explorer.css` (spec AC-0025). The stat-card and theme code is removed.
- `lineage.js`: class-only colouring.

### Quality attributes (NFRs)

Owned by: T2, T3

- Width tracks follow the token file's worklist table without the rail: one column below 40rem with the detail replacing the list when a record is picked and a Back control returning to it; list `minmax(0, 3fr)` and detail `minmax(22rem, 2fr)` from 40rem; detail `clamp(22rem, 30%, 32rem)` from 90rem and `clamp(28rem, 30%, 40rem)` from 120rem. No max-width. Traces to: AC-0009 to AC-0011.
- Contrast comes from the shared tokens, which already pass in the intents view; the layout file adds no colour. Traces to: AC-0014.

## Tasks

### T1: One hashed style from the shared base and the layout file

**Depends on:** none
**Touches:** packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer.py, packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/view-base.css, packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/explorer.css, packs/repo-governance/tests/skills/navigate-decisions/test_html_publication.py, tests/roster/test_skill_html_view_tokens.py

**Tests:**
- In `test_html_publication.py`, new tests read the emitted HTML from the `mixed` export: one `<style>` whose text equals `view-base.css` + `explorer.css` read from the scripts tree (AC-0001); the policy's `style-src` digest computed with `hashlib` over that text, and no `unsafe-inline` or `unsafe-eval` (AC-0002); no `style=` in the HTML and no `url(` or `@import` in either file (AC-0004).
- `tests/roster/test_skill_html_view_tokens.py` gains a test that compares the copy's bytes with the canonical file and sees the copy in `tools/check_view_base_parity.find_copies`, since pack tests stay inside their pack (AC-0003).
- The existing assertion at `test_html_publication.py:1629` that expects `style-src 'unsafe-inline'` is replaced by the AC-0002 test and listed in the ledger.

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/navigate-decisions/test_html_publication.py -q` passes and `python3 tools/check_view_base_parity.py` reports 2 files.

### T2: Shared header, two soft zones and the system theme

**Depends on:** T1
**Touches:** packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer.py, packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/explorer.js, packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/explorer.css, packs/repo-governance/tests/skills/navigate-decisions/browser_checks.py, packs/repo-governance/tests/skills/navigate-decisions/test_html_publication.py

**Tests:**
- `test_html_publication.py`: no `theme-toggle` or `stat-cards` id, no `data-theme-choice`, no `localStorage` token in the script (AC-0007); the snapshot line's text holds `navigate_decisions.BOUNDARY_NOTICE` (AC-0022) and the counts from the export's `summary` (AC-0024).
- `browser_checks.py`, parametrised over the width and theme matrix in the List and Context views: zone radius and shadow, `.row-link` shadow (AC-0008); zone placement with a record picked (AC-0009); overflow and `scrollWidth` (AC-0010); full-width span at 2560 (AC-0011); at 320, the "Back to list" button by keyboard (AC-0026); record-body heading sizes on a `mixed` record with headings (AC-0025).
- Existing browser checks that click `#btn-detail`, read `#view-detail`, `.info-panel`, the stat cards or the theme switch are repointed to the detail zone and the snapshot line. Each is listed in the ledger with the shipped criterion it verifies and its replacing assertion (AC-0016).

**Done when:** `uv run --with playwright --with pytest python -m pytest packs/repo-governance/tests/skills/navigate-decisions/browser_checks.py -q` passes, and `test_html_publication.py` passes.

### T3: Names lead, state marks and token-coloured lineage

**Depends on:** T2
**Touches:** packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/explorer.js, packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/lineage.js, packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/explorer.css, packs/repo-governance/tests/skills/navigate-decisions/browser_checks.py, packs/repo-governance/tests/skills/navigate-decisions/test_html_publication.py, packs/repo-governance/tests/skills/navigate-decisions/fixtures/lifecycle-marks/**

**Tests:**
- `browser_checks.py`: `document.querySelectorAll('[style]')` is empty after the pick, context toggle and node-focus steps in each view (AC-0027); the AC-0008, AC-0010 and AC-0026 checks extended to the Graph view (`mixed` with its first chain selected; `negative/hostile` as it first opens); title first in each row and id after it (AC-0012); `data-mark` and text per AC-0013 over `mixed` and the new eleven-record `lifecycle-marks` fixture (one record per AC-0013 value); text, SVG text and control-border contrast across the matrix and views (AC-0014); reduced-motion durations (AC-0015); SVG computed `fill` and `stroke` against the `:root` `--c-` values in each theme (AC-0023).
- `test_html_publication.py`: a lint over `explorer.css` for the AC-0005 forbidden forms, using the patterns of the intents view's layout-file test (AC-0005); over the three scripts with comments stripped, no colour literal of any AC-0006 form (the named-colour list is CSS Color 4's, held in the test) (AC-0006); no `font-*` attribute writes (AC-0021); no `.style`, `cssText` or `'style'` / `"style"` literal, which catches a style write through the `sa` and `attr` helpers and `setAttributeNS` (AC-0020).
- The shipped decision-navigation criterion 0025 and 0026 browser checks still pass against the restyled marker and diagram.

**Done when:** both suites pass, and the whole `packs/repo-governance/tests/skills/navigate-decisions/` directory passes.

### T4: Docs, version, real-export evidence and review

**Depends on:** T3
**Touches:** packs/repo-governance/.apm/skills/navigate-decisions/SKILL.md, docs/design/tokens/skill-html-views.md, packs/repo-governance/pack.toml, packs/repo-governance/.claude-plugin/plugin.json, docs/product/changelog.d/*.md, docs/specs/decision-view-style/notes/**, .agents/**, .claude/**

**Tests:**
- Real exports of this repository at the base commit and the final commit; the ledger records both commands, file sizes, record count, counts per kind and lifecycle, and relationship count (AC-0017).
- Screenshots at the width and theme matrix into `notes/screens/`; an `experience-reviewer` pass over them, adjudicated, recorded in the ledger (AC-0018).
- Owner approval line with date in the ledger (AC-0019).
- The ledger lists every edited pre-existing test with the shipped criterion it verifies and its replacing assertion (AC-0016).
- The token file § Unresolved entry for the lineage diagram names the `--c-` roles the `ln-*` classes use.

**Done when:** `make build-self` leaves no diff, `make lint-ruff lint-mypy` passes, and ledger rows for AC-0016 to AC-0019 are filled.

## Rollout

Ships with repo-governance 2.4.0. The export is a disposable file, so there is no migration; an adopter sees the new look on their next export.

## Risks

- A shared class in `view-base.css` may assume intents markup. Mitigation: reuse only the generic classes (`.page-header`, `.search`, `.zones`, `.worklist`, `.detail`, `.row`, `.mark`, `.seg-btn`, `.key`, `.notice`, `.meta`) and put decisions-only rules in `explorer.css`. A needed shared change is an Ask-first item.
- The `browser_checks.py` suite is large (3,160 lines) and pins today's markup. Mitigation: T2 and T3 repoint selectors only and list each in the ledger.

## Changelog

- 2026-10-27: spec approved by eugenelim
- 2026-10-27: plan approved by eugenelim
