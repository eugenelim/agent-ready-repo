# Verification ledger: decision-view-questions

Base commit: 47e1b2836

## Edited pre-existing tests (AC-0026)

All tests are in `browser_checks.py`. The List / Graph / Context switch is gone, so a test that clicked `#btn-*` or read the switch's `aria-current` now uses the rail link, and the page's no-hash default is Recently decided, not the corpus list.

| Test | Shipped criterion it verifies | Replacing assertion | Required by |
| --- | --- | --- | --- |
| `test_hash_routing_empty_hash_shows_list` | decision-navigation AC-0016 | Picking a row fills `#detail-body`; Back restores the no-hash entry, an unpicked detail prompt, no `data-picked`, and the default list `#view-recent` visible with its heading "Decided records" (was `#view-list`, "Corpus list") | AC-0003 (no hash opens Recently decided) |
| `test_aria_current_on_nav_buttons` | decision-navigation AC-0016 (the current view is marked with `aria-current="page"`, never `aria-pressed`) | Same two assertions on `#q-recent`, the initial view's rail link, in place of `#btn-list` | AC-0001 (the rail replaces the switch), AC-0003 |
| `test_focus_moves_to_view_heading` | decision-navigation AC-0016 (focus moves to the view's heading after navigation) | Same heading and region assertions after clicking `#q-graph` in place of `#btn-graph` | AC-0016 (a rail link moves focus to the list's level-2 heading) |
| `test_reset_filters_keeps_keyboard_focus` | decision-navigation AC-0016 | Focus lands on the view's `h2` after Reset filters removes itself; the heading is "Decided records" (the default list) in place of "Corpus list" | AC-0003, AC-0004 |
| `test_supersession_banners_in_list_and_detail` | decision-navigation AC-0025 | Same banner texts and the same `#list/ADR-0020` hash after the link; the test routes to `#list` first, since the default page is no longer Browse all | AC-0003, AC-0014 (`#detail/<id>` opens Browse all) |
| `test_back_to_list_returns_to_the_current_view_at_320` | decision-navigation AC-0026 (Back to list shows the list zone in the view that was current) | Same zone, picked-row and node assertions; the current view is read from the rail link's `aria-current` (`#q-list`, `#q-graph`), and for the context view no rail link carries it | AC-0001, AC-0015 (context marks no rail link) |
| `_hash_state` helper, used by the four history tests below | decision-navigation AC-0016 (every history entry restores the view and picked state recorded with it) | The view comes from the rail link with `aria-current="page"`, or `context` when none has it, in place of the switch buttons | AC-0001, AC-0015 |
| `test_history_returns_to_the_view_recorded_with_each_entry` | decision-navigation AC-0016 | Same entries and equality checks; `#q-list` is clicked in place of `#btn-list` | AC-0001 |
| `test_history_after_back_to_list_keeps_the_list_zone_at_320` | decision-navigation AC-0016 | Same checks; `#q-graph` in place of `#btn-graph`, and Back lands on the default list `#view-recent` in place of `#view-list` | AC-0001, AC-0003 |
| `test_back_to_an_old_detail_bookmark_restores_the_view_it_opened_in` | decision-navigation AC-0016 | Same checks; `#q-graph` in place of `#btn-graph` | AC-0001 |
| `test_strike_through_marks_full_supersession_only` | decision-navigation AC-0025 (full supersession strikes the id, partial underlines it) | Same three decoration assertions, read from `#view-list` rows after routing to `#list`; the default Recently decided list no longer holds every record | AC-0003, AC-0005 (the default list holds decided records only) |
| `test_status_filter_text_is_escaped_in_no_results` | decision-navigation AC-0006, AC-0010 (the active status in the no-match message and live region uses the visible escape) | Same escape assertions on `#view-list .empty-msg` and the live region after routing to `#list`; the `Acc[U+202E]epted` record is no decided word, so Recently decided shows its own empty text | AC-0007 (an empty question shows its empty text, not the no-match message) |
| `test_every_row_and_the_detail_line_carry_one_mark_by_the_lifecycle_map` | decision-view-style AC-0013 (every row and the detail line carry one lifecycle mark) | Same mark, text and glyph assertions over every `#view-list` row, in export order, after routing to `#list` | AC-0003, AC-0005 |
| `test_a_row_leads_with_its_title_then_its_id` | decision-view-style AC-0012 (the title is the first text of a row, the id follows) | Same assertions over every `#view-list` row against the data island, after routing to `#list` | AC-0003, AC-0005 |
| `_zone_page` helper and `_ZONE_VIEWS` constant | decision-view-style AC-0008, AC-0010, AC-0014, AC-0027 (the matrix checks run over each view) | `_ZONE_VIEWS` gains `recent`, so every test parametrised over it also runs on Recently decided (mixed and hostile); `_zone_page` opens every section when the view is `areas`. No assertion changed | Spec Terms: each view extended to Recently decided and By area |

## Observations

- T1 gates, all run unfiltered at the T1 commit: `uv run --with ruff ruff check .` pass; `uv run --with mypy python tools/lint-mypy.py` pass (156 files); `python3 -m pytest packs/repo-governance/tests/skills/navigate-decisions/ tests/roster/test_skill_html_view_tokens.py` 403 passed in 8.7 s; `python3 tools/check_view_base_parity.py` ok; `browser_checks.py` on bundled Chromium 416 passed in 213 s (372 at base, 44 new).
- The 44 new T1 tests were run against the base page first: they failed there (rail absent, no-hash page not Recently decided).
- Until T2, Recently decided, Still being decided, Replaced and By area show their list head over the narrowed corpus rows, so the shipped tests that wait for `li.row` on the default page keep working. T2 replaces that body with each question's own rows.
- T2 replaced the four placeholder bodies with each question's own rows. The new `questions` fixture (18 records) and 142 new browser tests were written first: 23 of the new tests that read the four lists failed against the T1 page, then passed. Hidden regions keep their last rows, so the four edited tests above scope their selectors to `#view-list`.
- T2 gates, run unfiltered at the T2 commit: ruff check pass; mypy pass (156 files); `python3 -m pytest packs/repo-governance/tests/skills/navigate-decisions/ tests/roster/test_skill_html_view_tokens.py` 403 passed; `check_view_base_parity.py` ok; `lint-pack-test-boundary.py` passed; `browser_checks.py` on bundled Chromium 558 passed in 290 s (416 at T1, 142 new).
