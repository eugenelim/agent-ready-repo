# Plan: Intent view for session start

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/.apm/skills/navigate-intents/scripts/intent_view.py` (`_SHELL`, `_read_asset`, `build_html`); `view_assets/view.js` (`escapeDisplay`, `el`, `parseRoute`, `handleRoute`, `renderDetail`) and `view_assets/view.css`; tests `packs/core/tests/skills/navigate-intents/test_export_html.py`, `view_browser_checks.py`, `view_bench.py`; the build-check chain in `tools/repo/build_gate_chain.py` (`build_check`, the closure-terminality checker and self-test pair as the step pattern); design inputs `docs/design/screens/session-start-orientation-ia.md`, `docs/design/direction/skill-html-views.md`, `docs/design/tokens/skill-html-views.md`.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/intent-view-session-start/notes/verification-ledger.md`. A genuine
> artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material.

## Approach

The payload and the Python publisher stay as they are, apart from joining two stylesheets into the one hashed style. The page shell gains the question navigation, the header search and the three layout zones. `view.js` is rewritten around one route object and five list builders, reusing the shipped escape, element and source-link helpers unchanged. The style splits into `view-base.css`, which carries the token values, and a `view.css` that holds layout only. The riskiest part is the layout's behaviour at 320px and at very wide screens, so each task that builds behaviour writes its browser tests in the same task, at true viewport sizes. The parity checker is a small standalone script with a self-test, registered beside the closure-terminality pair.

## Constraints

- RFC-0108 D1 rules 1 to 10 and D2; RFC-0105 D3 and D4 unchanged for this slice: no readiness, no prompt, no launcher.
- ADR-0074 and ADR-0007: standard-library-only skill scripts; the checker is a repository tool and is standard-library-only too.
- The shipped content-security policy string, data-block escape and forbidden-API list are unchanged; `test_export_html.py` keeps asserting them.
- `close-work/scripts/intent_graph.py` is not touched.
- No `.apm/` source carries an internal citation (packs/AGENTS.local.md grep).

## Construction tests

**Integration tests:** `view_browser_checks.py` is rewritten in T3 and extended in T4; it is the cross-task check for both. Run it with `uv run --no-project -q --with pytest --with playwright python -m pytest packs/core/tests/skills/navigate-intents/view_browser_checks.py -q -rs`.

**Manual verification:** T7's screenshots, experience review and owner check.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User procedure (`guides/core/how-to/navigate-intents.md`) | T6 | Guide lints pass | Section names the four questions |
| Skill instructions and activation (`SKILL.md`, `eval_queries.json`) | T6 | Self-host with no diff on re-run | Eval case present |
| Architecture (`packs/core/DESIGN.md`) | T6 | Section diff | Names `view-base.css`, the join, the gate |
| Current product truth (export spec `Amended in part by:`) | T6 | Header line | Line present |
| Release history (changelog fragment) | T6 | `tools/changelog.py` validation | Fragment at core 3.1.2 |
| Verification record (ledger, screenshots) | T3, T4, T5, T7 | Ledger entries | Ledger cited by the PR |
| Coordination (`workspace.toml`, brief Spec map) | T6 | Entry present | Moved to `shipped` on ship |

## Design (LLD)

### Component decomposition

Owned by: T1, T3, T4

- **Shell (`intent_view.py` `_SHELL`).** `header` holds the `h1` "Intent graph", the meta line, the scope banner and the search field. `nav` holds the five destination links. `main` holds two zones: `.worklist` (list header with title, lead line, count, sort key and the Key disclosure; then the list) and `.detail` (`h2` and body). The live region and `noscript` notice stay.
- **Style join.** `build_html` reads `view-base.css` and `view.css` through `_read_asset`, refuses either one if it holds `</style` or `<!--`, as it does today, and joins them as `base + "\n" + layout`. The digest is of the joined text.
- **Script modules (one file, sections).** Shipped helpers kept as they are: `escapeDisplay`, `el`, `add`, `clear`, `sourceBlock`, `edgeItem`, `relationItem`, the label tables and `validData`. New ones:
  - `displayName(node)`: strips one leading label from the closed list in the spec's terms, and falls back to the slug.
  - `statusWord(s)`: returns the leading ASCII letters.
  - `markFor(item)`: returns `{glyph, word}` by AC-0010, rules in order.
  - `openIndex`: builds the beneath map from each open item's ancestor lists once at start.
  - `QUESTIONS`: a fixed table of key, name, title, sort key, empty line and builder for `next`, `capabilities`, `noparent`, `broken` and `browse`.
  - `nextStep(node)`: holds the AC-0015 sentence rules, first match wins.
  - `renderDetail`: renders the parts in AC-0013 order.

### State & control flow

Owned by: T3

- One route object `{q, node, search, level, kind, status, type}` parsed from the fragment; an unknown `q` falls back to `next`. Picking a question or row uses `location.hash =` (a history entry); search and filters use `history.replaceState`, then re-render.
- On a width of 40rem or more, picking a row keeps focus on the row and announces "Showing <name>". Below 40rem, `main` gets `data-picked` and the CSS hides the worklist. Focus then moves to the detail `h2`, and "Back to list" clears `node`, restores the stored scroll offset and focuses the row. The width test is `matchMedia('(min-width: 40rem)')`, and no listener on it changes content.
- With nothing picked, the detail zone shows "Pick an item to see its next step." It never auto-selects, so no row is marked current without a pick.
- Lists render in full on each route change. The delivery resolver stops at 10,000 files under the three collections, so at the larger benchmark multiples `outstanding` is unavailable and the default list is the "Can't list open work" line; the largest list measured is at the biggest multiple where `outstanding` is still available, and AC-0044 records the row count there. If startup exceeds budget, chunked rendering below the fold is the fallback, and nothing above the list moves.

### Visual system

Owned by: T1, T4

Values come from `docs/design/tokens/skill-html-views.md`.

- **`view-base.css`.** It holds the colour roles for light (`:root`) and dark (`@media (prefers-color-scheme: dark)`). It also holds the worklist type scale, the spacing scale `--s-1` to `--s-7`, the system font stacks and tabular numerals. Then come the base element rules, the focus outline (`2px solid var(--c-accent)` with a `2px` offset), the 2rem target floor, the state-mark classes (`.mark-g` glyph, colour by `data-mark` value) and `.visually-hidden`. Corners are square, and it has no shadows and no motion.
- **`view.css`.** It holds zones and grids only. Below 40rem: one column, with the nav stacked. From 40rem to below 90rem: the nav as one row, then `minmax(0,3fr) minmax(22rem,2fr)`. From 90rem: `14rem minmax(0,3fr) minmax(26rem,2fr)`. Page padding is `--s-5`, with no max-width. The row grid is `name minmax(0,1fr) | state 8.5rem | context minmax(8rem,16rem)`, and it collapses to stacked cells below 40rem. Sticky regions carry `scroll-padding` equal to their height.

### Interfaces & contracts

Owned by: T2

- `tools/check_view_base_parity.py [--root DIR]`: it finds every `packs/*/.apm/**/view-base.css`. It exits 0 when all match the canonical file byte for byte, and exits 1 when any file differs or the canonical file is missing, naming each one on stderr. It is standard-library-only and reads no symlinked file (a symlink counts as a difference).
- `tools/test_check_view_base_parity.py`: builds a temporary root with the canonical file, an identical copy and a differing copy, and asserts both exit codes.

## Tasks

### T1: Shared stylesheet and the style join

**Depends on:** none
**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/intent_view.py`, `view_assets/view-base.css`, `view_assets/view.css`, `packs/core/tests/skills/navigate-intents/test_export_html.py`

**Tests:**
- `test_export_html.py`: `test_csp_is_first_head_child_and_pins_both_digests` compares the style with `view-base.css + "\n" + view.css` (AC-0026).
- `test_export_html.py`: a token test parses the § Colour table of `docs/design/tokens/skill-html-views.md` and compares each role's light and dark value with `view-base.css`; `test_stylesheet_declares_no_motion` and the `url(`/`@import` ban cover both files (AC-0027).
- `test_export_html.py`: a test scans `view.css` for `#` hex, `rgb(`, `hsl(`, named colours, `font-family` and `--c-`/`--t-` declarations (AC-0028).

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents/test_export_html.py -q` passes.

### T2: Parity checker and gate

**Depends on:** T1
**Touches:** `tools/check_view_base_parity.py`, `tools/test_check_view_base_parity.py`, `tools/repo/build_gate_chain.py`

**Tests:**
- `tools/test_check_view_base_parity.py` covers identical copies giving exit 0, a differing copy giving exit 1 with its path on stderr, a missing canonical file giving exit 1, and a copy that is a symlink to the canonical file giving exit 1; both run as build-check chain steps (AC-0029).
- `tools/test-lint-ci-parity.py` and `tools/lint-ci-parity.py` stay green with the two new chain steps.

**Done when:** both tests pass, and `python3 tools/check_view_base_parity.py` exits 0 on the tree.

### T3: The four-question script and its browser checks

**Depends on:** T1
**Touches:** `view_assets/view.js`, `intent_view.py` (`_SHELL`), `packs/core/tests/skills/navigate-intents/view_browser_checks.py`

**Tests:**
- `view_browser_checks.py` is rewritten with one test per criterion in AC-0050, AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0030, AC-0042 and AC-0043, at a 1280 CSS px viewport unless the criterion names a width.
- Its exports fixture keeps the `mixed`, `hostile`, `empty`, incomplete-delivery, scoped (`--from intent:bravo-feat`) and related exports. It adds a `hostile` export whose resolver seam appends one delivery diagnostic (AC-0006), and a copy of `mixed` where `intent:juliet-done` names `intent:india-none` as its parent (AC-0015).
- The tests kept for the carried export criteria are: source links (0028), escapes (0034), no network (0036), outside-export plain text (0045), damaged data (0054) and no script (0055).
- The regression tests kept are `test_delivery_relation_on_a_non_intent_node_renders_as_a_link` and `test_startup_render_failure_shows_the_alert_and_logs_the_error`, re-targeted to the new DOM.
- `test_export_html.py`'s forbidden-API and escape-parity tests stay green, and the forbidden-API scan also refuses a script write of inline style: a `.style` property write, `cssText`, or `setAttribute('style'`.

**Done when:** `view_browser_checks.py` passes with none skipped.

### T4: Layout by width and the access floor

**Depends on:** T3
**Touches:** `view_assets/view.css`, `view_assets/view-base.css`, `packs/core/tests/skills/navigate-intents/view_browser_checks.py`

**Tests:**
- `view_browser_checks.py` gains one test per criterion in AC-0031, AC-0032, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041. Each test uses `browser.new_context(viewport=..., color_scheme=...)` across the width and theme matrix where the criterion names it.

**Done when:** `view_browser_checks.py` passes with none skipped.

### T5: Scale bench and real export

**Depends on:** T4
**Touches:** `packs/core/tests/skills/navigate-intents/view_bench.py`, `docs/specs/intent-view-session-start/notes/verification-ledger.md`

**Tests:**
- `view_bench.py` loads with no fragment, so startup measures "What can I work on next?", types into the header search field, and reports whether `outstanding` was available and the default list's row count (AC-0044).
- A throwaway script exports this repository to the temporary directory, opens it in headless Chromium, expands every "Browse all intents" subtree and compares the intent rows with the payload's records (AC-0045).

**Done when:** the ledger records both runs, with the commit and the three asset digests, and every threshold is met.

### T6: Docs, skill, evals, release and coordination

**Depends on:** T3
**Touches:** `packs/core/.apm/skills/navigate-intents/SKILL.md`, `packs/core/.apm/skills/navigate-intents/evals/eval_queries.json`, `guides/core/how-to/navigate-intents.md`, `packs/core/DESIGN.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `docs/specs/intent-navigation-export/spec.md`, `docs/product/briefs/intent-navigation-delivery.md`, `workspace.toml`, adapter projections via self-host

**Tests:**
- The new eval case is added and its activation run follows the procedure the export ledger records for its criterion 0067: three fresh tool-less `claude -p` runs seeing every `core` skill description plus `navigate-decisions`, graded with `agentbundle pack evals run --pack core --mode in-harness` (AC-0046).
- `tools/lint-guide-titles.py`, `tools/validate_guides.py` and `tools/lint-guides-no-repo-only-refs.py` pass.
- `make build-self` run twice gives no diff on the second run.
- The packs/AGENTS.local.md citation grep finds nothing new.

**Done when:** every check above passes and the activation run is in the ledger.

### T7: Screenshots, review and owner check

**Depends on:** T5, T6
**Touches:** `docs/specs/intent-view-session-start/notes/screens/`, `notes/verification-ledger.md`

**Tests:**
- A throwaway Playwright script exports this repository to the temporary directory and captures 8 first-screen PNGs at true viewports (AC-0047).
- The `experience-reviewer` agent reviews the screenshots and the rendered page facts, and its findings are adjudicated (AC-0048).
- The owner's first-screen check is recorded (AC-0049).
- After the last code-bearing commit, `view_browser_checks.py` and `test_export_html.py` run once more and the ledger records the commit id, the SHA-256 of `view.js`, `view.css` and `view-base.css`, and the count of tests run with none skipped (Testing Strategy record for the browser criteria).

**Done when:** the ledger lists the 8 digests, the adjudicated review, the owner's answer and the final-commit browser-suite record.

## Rollout

- **Delivery:** big bang in core 3.1.2; the export is regenerated on demand, so rollback is reverting the release.
- **Infrastructure, external systems:** none.
- **Sequencing:** merges straight to the default branch, before slice 8's re-fit and slice 11.

## Risks

- The detail zone at 2560px may read as sparse text in a very wide column; T7's review decides whether the 2fr track needs a reading measure inside it.
- A large startable list could push startup past budget with full rendering; T5 measures it before any chunking is built.

## Changelog

- 2026-10-13: spec approved by eugenelim
- 2026-10-13: plan approved by eugenelim
