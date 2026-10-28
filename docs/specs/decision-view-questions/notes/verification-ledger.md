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

## Observations

- T1 gates, all run unfiltered at the T1 commit: `uv run --with ruff ruff check .` pass; `uv run --with mypy python tools/lint-mypy.py` pass (156 files); `python3 -m pytest packs/repo-governance/tests/skills/navigate-decisions/ tests/roster/test_skill_html_view_tokens.py` 403 passed in 8.7 s; `python3 tools/check_view_base_parity.py` ok; `browser_checks.py` on bundled Chromium 416 passed in 213 s (372 at base, 44 new).
- The 44 new T1 tests were run against the base page first: they failed there (rail absent, no-hash page not Recently decided).
- Until T2, Recently decided, Still being decided, Replaced and By area show their list head over the narrowed corpus rows, so the shipped tests that wait for `li.row` on the default page keep working. T2 replaces that body with each question's own rows.
