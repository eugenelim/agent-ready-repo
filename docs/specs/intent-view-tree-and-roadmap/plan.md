# Plan: Intent view tree, roadmap and grouped rail

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** RFC-0108 D1; the `intent-view-source-and-style` part list in `packs/core/.apm/skills/navigate-intents/scripts/intent_view.py` (a new part is one tuple entry); `view_src/list-bodies.js` `bodyBrowse` and `treeRow` (the shipped tree this extends); `view_src/labels.js` `QUESTIONS` and `view_src/chrome.js` `buildNav` (the rail); `packs/core/tests/skills/navigate-intents/view_browser_checks.py` and its fixture builders (the construction path). Deviation: none — no payload or derivation change.

## Approach

Six tasks in dependency order, one review unit. A new fixture corpus comes first, because every criterion needs strategies, nested capabilities and every delivery band, and the shipped fixtures have none of those. The rail change is small and lands next. The roadmap question is the riskiest part — its bands and work-beneath walk must agree with an independent Python reading of the payload — so its tests compute expectations in Python from the fixture's own payload rather than reusing the view's logic. The Browse controls extend the shipped tree. Docs, the version and the measurements close it. The owner-reviewed prototype lives in `notes/prototype/` as the design reference.

## Constraints

- RFC-0108 D1 rules 1 to 10 with rule 9 as corrected; the `skill-html-views` direction and token file.
- RFC-0105: the view never re-derives the graph. "Open" comes only from the payload's open items; the band split of open and non-open items reads status words, as the view's existing active-word table already does.
- The source-and-style spec's criteria 0001 to 0010 keep holding: one hashed script from parts, banned APIs, the layout sheet's limits.
- `packs/AGENTS.md`: self-host after edits; bump both version files; no internal-governance citations in shipped pack content.

## Construction tests

**Integration tests:** `view_browser_checks.py` exports the `roadmap` fixture through `nav.run_export` and reads expectations from a Python helper over that export's payload.
**Manual verification:** the real export, screenshots, the `experience-reviewer` pass and the owner's approval, recorded in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Amended-in-part header | T5 | Header line | Names this spec and the amended criteria |
| Design evidence | T5 | `docs/design/evidence/tracker-navigation-survey.md` | Present; rail order matches |
| User guide and skill | T5 | Guide lints; self-host no diff | Six questions and Browse controls described |
| Changelog and version | T5 | Fragment; both version files | Fragment validates |
| Verification ledger and screens | T6 | Ledger; `notes/screens/` | Cited by the PR |
| Coordination | T5 | `workspace.toml` entry; Spec map row | Follows spec status |

## Design (LLD)

### Component / module decomposition

Traces to: AC-0005 to AC-0020, AC-0042.

Owned by: T3

`view_src/roadmap.js` is a new part, placed after `list-bodies.js` in the part list. It holds the band classification, the work-beneath walk, the cell apportionment and the roadmap body, and registers `roadmap` in the list bodies' dispatch table. The band reads the shipped `isOpen` and `statusWord` and the shipped active-word table, plus one delivered-word set; the spec's terms own the rule. Briefs' specs come from the payload's resolved `Brief:` edges, indexed once.

### State & control flow

Traces to: AC-0021 to AC-0039.

Owned by: T4

The route gains `show` and `group`, parsed and written like the shipped filters, so they replace the fragment without a history entry. Visibility is memoised per render: a row is shown when it matches or a child in the current grouping is shown. "Expand all" and "Collapse all" walk the first section's rendered rows and reuse each row's open/close function. A context row carries a visible "context" tag and a visually hidden "shown for context" inside its link.

### Quality attributes (NFRs)

Traces to: AC-0002, AC-0003, AC-0020, AC-0028.

Owned by: T2, T3, T4

Rail groups are lists labelled by visible headings, so assistive technology hears the group name with each list. The bar is decorative — every number it shows is also words — so its cells need only be distinct; delivered cells use `--c-ok`, in-progress `--c-active`, not-started a `--c-raised` fill with a `--c-rule-strong` outline, and empty cells the canvas colour with the same outline.

## Tasks

### T1: The `roadmap` fixture exists, with each record's band stated by hand

**Depends on:** none

**Tests:**
- Criteria: AC-0042, AC-0044.
- `fixtures/roadmap/` holds two product strategies, a capability nested under another capability, a capability under no strategy, a stopped capability with an open child capability, a capability with nothing beneath, a capability whose only work is stopped, intents, briefs and specs in every band (including an `Accepted` intent with children and a status with a trailing date such as `Fulfilled (2026-01-01)`), a brief with specs placed by `Brief:`, a refused parent edge, and an intent with no parent and nothing beneath. Its `README.md` table states each record's expected band and section by hand.
- `_roadmap_expectations(payload)` in `view_browser_checks.py` computes sections, nesting, band counts, shares and cells from the payload by the spec's terms; `test_roadmap_fixture_matches_hand_stated_bands` compares it with the README table.
- `roadmap.js` joins the part list as an empty part; `test_view_source_names_no_health_words` scans `view_src/` and the fixture.

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents/test_export_html.py -q` and `test_roadmap_fixture_matches_hand_stated_bands` pass.

### T2: The rail is grouped and ordered by job

**Depends on:** T1

**Tests:**
- Criteria: AC-0001, AC-0002, AC-0003, AC-0004, AC-0043, AC-0050.
- `test_layout_sheet_holds_no_new_style` (extending the source-and-style layout-sheet test) runs from this task on, so each later task's CSS meets AC-0043 as it lands.
- `test_rail_order_groups_and_counts` and `test_rail_group_labels_by_width` read the nav's lists, their computed accessible names, link text and counts at 1280 and 1680, and the empty-corpus and outstanding-unavailable exports.
- Shipped checks that read questions by position move to reading them by `data-q`, keeping what they assert: `_QUESTIONS` gains `roadmap` in the new order; `test_ac_0001_five_destinations_with_counts`, `test_ac_0003_title_lead_and_no_readiness_glyph`, `test_ac_0009_row_is_one_link_with_three_cells`, `test_ac_0042_unavailable_open_work`, `test_ac_0043_empty_corpus`, both `test_vi_3004_broken_rows_and_state_line` cases and `test_vi_3004_mixed_counts_are_unchanged` stop indexing counts by position; the sweeps in `_visit_everything`, `test_ac_0023_search`, `test_ac_0028_source_links_are_labelled_or_inert`, `test_ac_0034_unsafe_code_points_show_as_escapes`, `test_ac_0036_no_network_and_no_policy_violation`, `test_ac_0038_keyboard_alone_reaches_every_function`, `test_ac_0040_live_region_announces_list_title_and_count`, `test_ac_0041_names_contain_visible_labels` and `test_nothing_spills_out_of_a_zone` include `roadmap`.

**Done when:** those tests pass and the full `view_browser_checks.py` suite passes.

### T3: The roadmap question shows progress under each strategy

**Depends on:** T1, T2

**Tests:**
- Criteria: AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0040, AC-0048.
- `test_roadmap_sections_and_nesting`, `test_roadmap_progress_text`, `test_roadmap_cells`, `test_roadmap_strategy_headings`, `test_roadmap_without_outstanding` (the shipped resolver seam), `test_roadmap_no_capability` (the `mixed` fixture with its capabilities' levels rewritten in a temporary copy) and the shipped empty-corpus check, `test_roadmap_scoped_export` and `test_roadmap_cell_colours` compare the page with `_roadmap_expectations`.

**Done when:** those tests pass and a red proof (one hand-stated band altered) is recorded in the ledger.

### T4: Browse all intents has Show, Group and expand controls

**Depends on:** T1, T2

**Tests:**
- Criteria: AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0032, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0041, AC-0049.
- New: `test_browse_toolbar_and_defaults`, `test_expand_and_collapse_all`, `test_tree_row_tag_and_counts`, `test_full_hierarchy_sections`, `test_by_capability_sections`, `test_show_open_and_done_with_context_rows`, `test_browse_count_and_announcements`, `test_browse_without_outstanding`, `test_filters_flatten_and_intersect_show`, `test_show_and_group_in_fragment`, `test_browse_scoped_export` (both groupings, a leaf scope and a capability scope), and a parent-loop case in the `roadmap` fixture for AC-0030, with a tail intent whose name sorts before the loop's first member, asserting each intent appears once.
- Shipped checks that read the tree: every tree list carries the class `tree` (sections) inside `#list`; `_tree_ids` reads rows inside every `#list .tree` and opens each disclosure first; `test_ac_0031_back_to_list_restores_scroll` picks the last row of the first section; `test_fix_filter_change_keeps_focus_and_clear_controls_leave_focus` keeps waiting on `#list .tree`; `test_ac_0024_browse_all_intents`, `test_ac_0012_browse_row_shows_refused_parent`, `test_ac_0025_scoped_export` and `test_ac_0030_fragment_holds_state_and_history` use it, keeping what they assert.

**Done when:** those tests pass and the full `view_browser_checks.py` suite passes.

### T5: Docs, version, projections and records follow the change

**Depends on:** T3, T4

**Tests:**
- Goal-based: the survey present; the session-start spec's `Amended in part by:` line; `guides/core/how-to/navigate-intents.md` and `navigate-intents/SKILL.md` updated; both version files bumped with a changelog fragment; `agentbundle catalogue lint --root . --deep`, `agentbundle catalogue verify --root .`, a second self-host with no diff, `tools/check_view_base_parity.py`, `tools/lint-pack-test-boundary.py`, the guide linters and `lint-spec-status.py` passing; the brief's Spec map and `workspace.toml` list this spec.

**Done when:** those checks pass.

### T7: Short rail labels, Browse's sort key per grouping, capability loops, and review fixes

**Depends on:** T1, T2, T3, T4, T5

**Tests:**
- Criteria: AC-0001, AC-0005, AC-0006, AC-0007, AC-0026, AC-0027, AC-0031, AC-0034, AC-0043, AC-0049, AC-0051, AC-0052, AC-0053, AC-0054.
- T2's label assertions and its test `test_ac_0001_five_destinations_with_counts` (renamed `test_ac_0001_six_destinations_with_counts` during T2) move to the short labels here, since T2 is complete; `guides/core/how-to/navigate-intents.md`, `navigate-intents/SKILL.md` and the changelog fragment name the short labels and their questions, since T5 is complete; the session-start spec's `Amended in part by:` line names AC-0051 and AC-0054 against criterion 0001 and AC-0052 and AC-0053 against criterion 0007; self-host, `check_view_base_parity.py`, `lint-pack-test-boundary.py`, the guide linters and `lint-spec-status.py` are re-run.
- `test_rail_links_describe_their_questions` checks AC-0054's accessible descriptions for all six links.
- `test_rail_order_groups_and_counts` and `test_ac_0001_six_destinations_with_counts` read the short labels; `test_question_line_above_each_list_title` checks AC-0051 for all six questions; `test_ac_0041_names_contain_visible_labels` keeps passing on the short labels.
- `test_browse_summary_follows_show_and_group` asserts AC-0052's sort keys, including "By name" under a filter, and AC-0053's exact lead strings.
- A payload-edit capability loop (two capabilities naming each other, both edges resolved) shows each capability exactly once on the roadmap and in By capability; a payload-edit strategy between two capabilities nests the lower capability under the upper one; both expectations are stated by hand in `fixtures/roadmap/README.md` and fail against the current code before the fix.
- The fixture README states by hand the "c/t closed", "n open items" and context-row flag for the anchor capability, its sub-capability, a withdrawn child and a feature under a strategy; the page and `_browse_expectations` are each asserted against those literals.
- Hardening with no criterion of its own, listed in the PR's `Bundled fixes:` with its verification (review fixes): `test_ac_0040_live_region_announces_list_title_and_count`'s last step waits for the filter to apply (the selected option and the changed count) before comparing; 16 consecutive solo passes are recorded in the ledger before the `pre-existing-intent-view-live-region-test-flake` entry closes.
- Hardening with no criterion of its own, also listed in `Bundled fixes:`: the x-alignment checks also run at 1280 and 1440 at the fixture's deepest depth; the done/capability context-row guard is asserted; `test_roadmap_cells` counts strategies instead of assuming 2.
- `.rm-cell` uses a radius token (AC-0043's static test). Hardening with no criterion of its own, also listed in `Bundled fixes:`: the pressed-choice ✓ has a plain `content` fallback before the alt-text form (verified by a static test that both declarations are present in order).
- The flake's closure is carried work: the `workspace.toml` entry closes only after the 16 recorded solo passes.

**Done when:** those tests pass; the full `view_browser_checks.py` suite passes; and T5's checks pass again on T7's change — `agentbundle catalogue lint --root . --deep`, `agentbundle catalogue verify --root .`, a second self-host with no diff, `check_view_base_parity.py`, `lint-pack-test-boundary.py`, the guide linters, `lint-spec-status.py`, and a changelog fragment at the bumped version.

### T6: The real export is measured, captured and reviewed

**Depends on:** T5, T7

**Tests:**
- Criteria: AC-0045, AC-0046, AC-0047.
- Goal-based: the real export compared with `_roadmap_expectations`; screenshots of the roadmap question and the Browse tree at 320, 1280, 1680 and 2560 in both themes under `notes/screens/` with SHA-256; the full browser suite at the final code commit.
- Visual / manual QA: the `experience-reviewer` pass, then the owner's recorded approval.

**Done when:** the ledger holds each record.

## Rollout

Ships as a normal core patch release; reverting the PR restores the shipped view. No payload, query or stored state changes.

## Risks

- The work-beneath walk can double count a spec reachable through two paths; the spec counts each node once and the Python oracle uses a set.
- The rail reorder and the sectioned tree break shipped checks that read by position or by `#list > ul > li`; T2 and T4 list each one and move it to reading by key or section, without changing what it asserts.

## Changelog

- 2026-10-17: spec approved by eugenelim
- 2026-10-17: plan approved by eugenelim
- 2026-10-17: amended spec approved by eugenelim
- 2026-10-17: amended plan approved by eugenelim
