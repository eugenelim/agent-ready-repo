# Plan: Decision view questions

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** RFC-0108 D1 rules 1, 2, 6, 7 and its errata of 2026-10-17, and `docs/design/tokens/skill-html-views.md` § Layout (source); `packs/core/.apm/skills/navigate-intents/scripts/view_src/chrome.js` `buildNav`, `labels.js` `QUESTIONS` and `RAIL_GROUPS`, `detail-render.js` `listSummary`, and `view_assets/view.css` rail rules (analogous implementation); `packs/core/tests/skills/navigate-intents/view_browser_checks.py` and `docs/specs/intent-view-tree-and-roadmap/` (tests and precedent criteria); `docs/specs/decision-view-style/` (the slice this builds on). Deviation: the intents view routes by query parameters (`#q=…&node=…`); this view keeps its `#<view>/<id>` grammar so every shipped link keeps working, and adds question keys as views.

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

Four tasks. T1 lays the frame: the rail markup, its counts, the route grammar, the list head, and the rail's layout, with Browse all and Lineage as its first two questions, since those are today's List and Graph views and keep every shipped test meaningful while the switch goes. T2 adds the four new question lists and the `questions` fixture that pins their membership and order. T3 reorders the detail so it leads with action and adds the empty-detail summary. T4 updates docs and the version, captures the real-export evidence, and runs review.

The riskiest part is keeping the shipped browser checks green while the List / Graph / Context switch goes and the default list changes. Most checks route by hash through `_show`, so T1 keeps `#list`, `#graph` and `#context` as routes and a `#view-<key>` region per view; the checks that read or click `#btn-*` or call `_hash_state` are repointed to the rail, and each edited test is listed in the ledger with the shipped criterion it verifies (spec AC-0026).

A probe on 2026-10-27 confirmed that the shared `view-base.css` already styles `.question-link`, `.rail-group`, `.q-count`, `.list-question` and `.list-summary`, and hides the rail group labels below 90rem. So the rail needs only layout rules in `explorer.css`.

## Constraints

- RFC-0108 D1 rule 1 with its 2026-10-17 errata: short rail labels are allowed when the list names its full question above its title and each link carries the full question as its accessible description.
- RFC-0108 D2: `view-base.css` stays a byte copy of the canonical file; the layout file never overrides a shared colour, type or mark rule (decision-view-style AC-0005).
- `docs/specs/decision-navigation/spec.md` and `docs/specs/decision-view-style/spec.md` shipped criteria stay true.
- Root `AGENTS.md`: no new dependency; `make build-self` regenerates `.agents/` and `.claude/`.
- `packs/AGENTS.md`: pack tests stay inside the pack; repo-governance bumps minor (2.4.0 → 2.5.0) for the new capability.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** T4's screenshot matrix, `experience-reviewer` pass and owner approval.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `SKILL.md` § Export and projections | T4 | Switch sentence replaced by the rail and detail links | `make build-self` leaves no diff |
| Changelog fragment and 2.5.0 versions | T4 | Fragment file, `pack.toml`, `plugin.json`, the two roster tests | `python3 tools/changelog.py validate` exits 0 |
| Verification ledger and screens | T1–T4 | Ledger rows, `notes/screens/*.png` | Rows for AC-0026 to AC-0029 filled |

## Design (LLD)

### Design decisions

- **Questions as views.** `VALID_VIEWS` is the literal array `recent`, `deciding`, `replaced`, `graph`, `areas`, `list`, `context`, checked by `indexOf` as today, so a key such as `constructor` is never a view. The first six are rail questions; `context` is reached from the detail. Each view keeps its own region `#view-<key>` holding its own list head and `h2`, so `render`, `focusViewHeading` and the tests' `_show` work by the same rule for every view. Routes stay `#<view>[/<id>[/unpicked]]`; an empty hash is `recent`; an unknown first part is `list`; `#detail/<id>` on a cold load opens `list` and is rewritten with `replaceState` as today. Traces to: AC-0003, AC-0014, AC-0015. Owned by: T1.
- **One question table.** A `QUESTIONS` array in `explorer.js` holds each question's key, label, full question, heading, sort text and empty text, and a `RAIL_GROUPS` array the three groups, as in the intents view's `labels.js`. The rail, the list head and the summary read from it, so a label lives once; lookups into it go through a function that walks the array, never an object index. Traces to: AC-0001, AC-0004, AC-0007. Owned by: T1, T2.
- **Rail links.** Each rail link is an `<a id="q-<key>" href="#<key>">` with a click handler that, for an unmodified primary click, keeps the selection unpicked and pushes one history entry (the shipped `switchView`), so a selection survives a question change (decision-navigation criterion 0023). A modified click keeps the browser's own handling, as the supersession links do. The links are built once; a render only moves `aria-current`. Traces to: AC-0016. Owned by: T1.
- **Membership functions.** One function per question returns its records (and, for Replaced and By area, its groups) from `records` and `rels`, with no reference to filters; the renderer then intersects with `filtered()`. A list's count and summary count records once each, so a record under two areas counts once. The rail count is the length of the unfiltered result, except By area (number of areas) and Lineage (number of chains, from `Lineage`'s existing chain finder, exposed on the `Lineage` object). Traces to: AC-0002, AC-0013, AC-0021. Owned by: T1, T2.
- **Own-key maps.** The decided and being-decided word sets and the area grouping use `Object.create(null)` maps read with `Object.prototype.hasOwnProperty.call`, as `markName` does. The pre-existing `chainOf` and `statusMap` lookups are not changed. Traces to: AC-0006, AC-0024. Owned by: T2.
- **Grouped lists.** Recently decided and Still being decided add a `.group-head` heading only before the undated tail. Replaced uses two `.group-head` headings. By area uses one `details.key.area-group` per area, closed, so Expand all opens them. Traces to: AC-0005, AC-0006, AC-0008, AC-0009. Owned by: T2.
- **Row context.** In Recently decided, Still being decided and By area, the row's context cell starts with the date that sorts it, then kind and id, so the sort key shows on each row. Traces to: AC-0004. Owned by: T2.
- **Picked row.** Every row of the selected record carries `aria-current="true"`; `focusRow` searches the current view's region rather than `#view-list` only, opening a closed area section before focusing. Traces to: AC-0017. Owned by: T2.
- **Detail lead.** `renderDetail` writes: heading, state line, notices, "Replaces" line, facts line, links line (`.detail-links`: two `<a>` with click handlers that call `switchView` with the selection kept, then the shipped `makeLink` source link or inert path), record content, Relationships, Support references, then `details.all-fields` with the shipped `meta-table` inside. Traces to: AC-0018, AC-0019, AC-0020. Owned by: T3.
- **Empty detail summary.** With nothing selected, `renderDetail` writes the `.note` prompt and a `.list-summary` line from the current list's records after narrowing, like the intents view's `listSummary`. Below 40rem the empty detail is hidden, as today. Traces to: AC-0021. Owned by: T3.

Owned by: T1, T2, T3

### Component / module decomposition

Owned by: T1, T2, T3

- `explorer.py` `_build_html`: the header is unchanged. Inside `.app`, a `nav#questions-nav.questions` labelled "Questions" holding `div#question-list.rail` precedes `main#app-main.zones`. The list zone's `.tools` row loses the view switch and keeps Expand all; the shared `#list-count` paragraph moves into each list region's head. Regions `#view-recent`, `#view-deciding`, `#view-replaced`, `#view-graph`, `#view-areas`, `#view-list` and `#view-context` follow the Key; support inventory and provenance stay.
- `explorer.js`: the question table, rail build, membership functions, list renderers and the reordered detail.
- `lineage.js`: exposes its chain finder for the Lineage count; no drawing change.
- `explorer.css`: the rail tracks from the intents view's `view.css`, `.group-head`, `.area-group`, `.detail-links`, `.list-summary` spacing.

### State & control flow

Owned by: T1, T3

- `state.view` names the question or `context`; `state.sel` and `state.picked` keep their meanings (spec terms "selected" and "picked"). `render()` updates `aria-current` on rail links, the current region's list head from the question table, the region, then the detail.
- Focus after a rail link or a detail link: the current region's `h2` (the shipped `focusViewHeading`).

### Quality attributes (NFRs)

Owned by: T1

- Width tracks follow `docs/design/tokens/skill-html-views.md` § Layout's worklist table, as the intents view's `view.css` implements it. Traces to: AC-0022.

## Tasks

### T1: The rail, the route grammar and the list head

**Depends on:** none
**Touches:** packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer.py, packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/explorer.js, packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/lineage.js, packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/explorer.css, packs/repo-governance/tests/skills/navigate-decisions/browser_checks.py, packs/repo-governance/tests/skills/navigate-decisions/test_html_publication.py, docs/specs/decision-view-questions/notes/verification-ledger.md

**Mode:** visual / manual QA, exercised by scripted Chromium checks written before the code and seen to fail against the base page.

**Tests:**
- `browser_checks.py` new tests: rail labels, groups and descriptions read through `aria-describedby` (AC-0001); rail counts against Python-computed values from the data island, with search and both filters set (AC-0002); empty-hash default (AC-0003); list-head order, heading and sort text for Browse all and Lineage (AC-0004; the other four in T2); Lineage atlas and Browse all order (AC-0011, AC-0012); every route form, including an unknown first part, `#detail/<id>` cold load and bare and id-carrying `#context` (AC-0014, AC-0015); Enter, focus, selection kept, one history entry and Back (AC-0016); rail rectangles at 320, 1280, 1680 and 2560 (AC-0022); the slice-1 overflow, contrast and target-size checks extended to the rail across the matrix (AC-0023).
- `test_html_publication.py`: the shipped policy and lint tests run unchanged (AC-0025).
- Shipped tests repointed and listed in the ledger (AC-0026): every test that reads or clicks a `#btn-*` element (`test_aria_current_on_nav_buttons`, `test_focus_moves_to_view_heading`, `test_back_to_list_returns_to_the_current_view_at_320` and the history tests that click), every caller of `_hash_state`, whose view now comes from the rail link with `aria-current` or from `context` when none has it, `_navigate_graph` if it clicks, and the tests that expect the no-hash page to be the corpus list (`test_hash_routing_empty_hash_shows_list`, `test_reset_filters_keeps_keyboard_focus`).

**Done when:** the T1 tests and the whole `packs/repo-governance/tests/skills/navigate-decisions/` directory pass, `browser_checks.py` included.

### T2: The four new question lists

**Depends on:** T1
**Touches:** packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/explorer.js, packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/explorer.css, packs/repo-governance/tests/skills/navigate-decisions/browser_checks.py, packs/repo-governance/tests/skills/navigate-decisions/fixtures/questions/**

**Mode:** visual / manual QA, exercised by scripted Chromium checks written before the code.

**Tests:**
- A `questions` fixture holding: ADRs with an equal decision-date pair, a decided ADR with no `Date`, a decided RFC with an empty `Date closed`; one record for each being-decided word, one with a dated and one with an undated opened date; records with `Status: Constructor` (the inherited-name case) and `Status: ToString` (an unknown-word case), each with an area and in no supersession relationship; full and partial supersession; areas `<img src=x onerror=alert(1)>`, `constructor`, `__proto__`, an exact repeat within one record and two areas differing only in case; one record a title search removes from an area section; and one RFC with no `Areas` field.
- Corpora generated inside the test with the existing `_publish_with` helper: a one-record corpus holding a `Proposed` ADR (AC-0007 for Recently decided and Replaced) and a two-record corpus where both records have an area (AC-0010 absence). `lineage-chain` serves AC-0007 for Still being decided and By area.
- `browser_checks.py` new tests, each deriving its expected rows in Python from the data island: Recently decided (AC-0005), Still being decided with the `constructor` and `tostring` records (AC-0006), the four empty texts (AC-0007), Replaced (AC-0008), By area sections and order (AC-0009), the no-area line on `questions` and its absence (AC-0010), narrowing and the count line in each list (AC-0013), every row of the selected record marked and the 320 Back focus in By area (AC-0017), hostile area names as By area sections (AC-0024), the supersession marker and unresolved note on every list's rows (AC-0030), counts on `questions` (AC-0002), and the list-head heading and sort text for these four lists (AC-0004).
- The slice-1 matrix checks run over the Recently decided list on `mixed` and `negative/hostile`, and over the By area list on `questions`.

**Done when:** the T2 tests and the whole `navigate-decisions` test directory pass.

### T3: A detail that leads with action, and the empty-detail summary

**Depends on:** T1, T2
**Touches:** packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/explorer.js, packs/repo-governance/.apm/skills/navigate-decisions/scripts/explorer_assets/explorer.css, packs/repo-governance/tests/skills/navigate-decisions/browser_checks.py, docs/specs/decision-view-questions/notes/verification-ledger.md

**Mode:** visual / manual QA, exercised by scripted Chromium checks written before the code.

**Tests:**
- `browser_checks.py` new tests: part order on ADR-0001 (partially superseded) and on ADR-0020 (it replaces part of ADR-0001) in `mixed`, and on a `questions` record with areas, whose facts line shows its areas after its date (AC-0018); the closed "All header fields" section holding its rows (AC-0019); the two links at 1280 and at 320 (AC-0020); the summary for each list from 40rem, and its absence with no record shown (AC-0021); the hostile areas in the facts line, and the 320 Back to list in By area with that record picked, on `questions` (AC-0024).
- `test_detail_shows_every_header_field_exactly`, `test_wrapped_status_shows_its_own_row` and any other test reading the meta-table while it is collapsed are repointed to open it first, and listed in the ledger (AC-0026).

**Done when:** the T3 tests and the whole `navigate-decisions` test directory pass.

### T4: Docs, version, real-export evidence and review

**Depends on:** T2, T3
**Touches:** packs/repo-governance/.apm/skills/navigate-decisions/SKILL.md, packs/repo-governance/pack.toml, packs/repo-governance/.claude-plugin/plugin.json, tests/roster/test_new_rfc_governance_surfaces.py, tests/roster/test_repo_governance_rename_completeness.py, docs/product/changelog.d/*.md, docs/specs/decision-view-questions/notes/**, .agents/**, .claude/**

**Mode:** goal-based check, then visual / manual QA.

**Tests:**
- Real exports of this repository at the base commit and the final code commit; the ledger records both commands, file sizes, record count, counts per kind and lifecycle, and relationship count (AC-0027).
- Screenshots at the width and theme matrix into `notes/screens/`; an `experience-reviewer` pass over them, adjudicated, recorded in the ledger (AC-0028).
- Owner approval line with date in the ledger (AC-0029).
- The ledger lists every edited pre-existing test (AC-0026).
- The two roster tests pin 2.5.0.

**Done when:** `make build-self` leaves no diff, `uv run --with ruff ruff check .` and `uv run --with mypy python tools/lint-mypy.py` pass, `python3 tools/check_view_base_parity.py` reports ok, the two roster tests pass, and ledger rows for AC-0026 to AC-0029 are filled.

## Rollout

Ships with repo-governance 2.5.0. The export is a disposable file, so there is no migration; an adopter sees the rail on their next export, and their old `#list`, `#graph`, `#context` and `#detail` links still open.

## Risks

- A shipped test assumes the no-hash page is the corpus list. Mitigation: T1 repoints it to `#list` and lists it in the ledger.
- The 320px rail stacks six links above the list, pushing the first row down. Mitigation: it matches the intents view at 320; AC-0020 and the experience review check it.
- `browser_checks.py` grows past 4,000 lines and runs about 5 minutes. Mitigation: new checks reuse `_open_page`, `_show` and the matrix fixtures.

## Changelog

- 2026-10-27: spec approved by eugenelim
- 2026-10-27: plan approved by eugenelim
