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
| `_hash_state` helper, used by the three history tests below and by the unedited `test_an_old_detail_bookmark_still_opens_the_record` | decision-navigation AC-0016 (every history entry restores the view and picked state recorded with it) | The view comes from the rail link with `aria-current="page"`, or `context` when none has it, in place of the switch buttons | AC-0001, AC-0015 |
| `test_history_returns_to_the_view_recorded_with_each_entry` | decision-navigation AC-0016 | Same entries and equality checks; `#q-list` is clicked in place of `#btn-list` | AC-0001 |
| `test_history_after_back_to_list_keeps_the_list_zone_at_320` | decision-navigation AC-0016 | Same checks; `#q-graph` in place of `#btn-graph`, and Back lands on the default list `#view-recent` in place of `#view-list` | AC-0001, AC-0003 |
| `test_back_to_an_old_detail_bookmark_restores_the_view_it_opened_in` | decision-navigation AC-0016 | Same checks; `#q-graph` in place of `#btn-graph` | AC-0001 |
| `test_strike_through_marks_full_supersession_only` | decision-navigation AC-0025 (full supersession strikes the id, partial underlines it) | Same three decoration assertions, read from `#view-list` rows after routing to `#list`; the default Recently decided list no longer holds every record | AC-0003, AC-0005 (the default list holds decided records only) |
| `test_status_filter_text_is_escaped_in_no_results` | decision-navigation AC-0006, AC-0010 (the active status in the no-match message and live region uses the visible escape) | Same escape assertions on `#view-list .empty-msg` and the live region after routing to `#list`; the `Acc[U+202E]epted` record is no decided word, so Recently decided shows its own empty text | AC-0007 (an empty question shows its empty text, not the no-match message) |
| `test_every_row_and_the_detail_line_carry_one_mark_by_the_lifecycle_map` | decision-view-style AC-0013 (every row and the detail line carry one lifecycle mark) | Same mark, text and glyph assertions over every `#view-list` row, in export order, after routing to `#list` | AC-0003, AC-0005 |
| `test_a_row_leads_with_its_title_then_its_id` | decision-view-style AC-0012 (the title is the first text of a row, the id follows) | Same assertions over every `#view-list` row against the data island, after routing to `#list` | AC-0003, AC-0005 |
| `_zone_page` helper and `_ZONE_VIEWS` constant | decision-view-style AC-0008, AC-0010, AC-0014, AC-0027 (the matrix checks run over each view) | `_ZONE_VIEWS` gains `recent`, so every test parametrised over it also runs on Recently decided (mixed and hostile); `_zone_page` opens every section when the view is `areas`. No assertion changed | Spec Terms: each view extended to Recently decided and By area |
| `test_detail_shows_every_header_field_exactly` | decision-navigation AC-0025 (the detail lists each header-region field by label and recorded value) | Same row assertions; the test opens "All header fields" first and waits for the table to be attached | AC-0019 (the header table sits in a closed details) |
| `test_wrapped_status_shows_its_own_row` | decision-navigation AC-0025 (a wrapped Status shows its own row beside the lifecycle row) | Same `{ADR-0001: 2, ADR-0002: 1}` count; "All header fields" is opened for each record before the rows are read | AC-0019 |
| `test_hostile_status_line_detail_renders_in_linear_time` | decision-navigation AC-0025 (a near-2 MiB Status value renders its detail in under 2 s) | Same 2 s bound, timed until the detail's state line, which prints the hostile Status value, is visible (the table now sits in a closed details, so it is never visible) | AC-0019 |

## Observations

- T1 gates, all run unfiltered at the T1 commit: `uv run --with ruff ruff check .` pass; `uv run --with mypy python tools/lint-mypy.py` pass (156 files); `python3 -m pytest packs/repo-governance/tests/skills/navigate-decisions/ tests/roster/test_skill_html_view_tokens.py` 403 passed in 8.7 s; `python3 tools/check_view_base_parity.py` ok; `browser_checks.py` on bundled Chromium 416 passed in 213 s (372 at base, 44 new).
- The 44 new T1 tests were run against the base page first: they failed there (rail absent, no-hash page not Recently decided).
- Until T2, Recently decided, Still being decided, Replaced and By area show their list head over the narrowed corpus rows, so the shipped tests that wait for `li.row` on the default page keep working. T2 replaces that body with each question's own rows.
- T2 replaced the four placeholder bodies with each question's own rows. The new `questions` fixture (18 records) and 142 new browser tests were written first: 23 of the new tests that read the four lists failed against the T1 page, then passed. Hidden regions keep their last rows, so the four edited tests above scope their selectors to `#view-list`.
- T2 gates, run unfiltered at the T2 commit: ruff check pass; mypy pass (156 files); `python3 -m pytest packs/repo-governance/tests/skills/navigate-decisions/ tests/roster/test_skill_html_view_tokens.py` 403 passed; `check_view_base_parity.py` ok; `lint-pack-test-boundary.py` passed; `browser_checks.py` on bundled Chromium 558 passed in 290 s (416 at T1, 142 new).
- T3 wrote 34 new browser tests first (detail part order, All header fields, the two links at 1280 and 320, the list summary for each list and under narrowing, hostile areas in the facts line, Back to list at 320). Run against the T2 page, 36 of the new and repointed tests failed; the three that passed hold on either page (the context no-summary case and two Back to list cases). The three tests that read the header table while it was closed are listed above. The empty detail now also re-renders on a search or filter change while nothing is selected, so its summary follows narrowing.
- T3 gates, run unfiltered: ruff check pass; mypy pass (156 files); `python3 -m pytest packs/repo-governance/tests/skills/navigate-decisions/ tests/roster/test_skill_html_view_tokens.py` 403 passed; `check_view_base_parity.py` ok; `browser_checks.py` on bundled Chromium 592 passed in 307 s (558 at T2, 34 new).

## Real-export comparison (AC-0027)

| Export | Commit | Command | Bytes | Records | ADR / RFC | Accepted / Superseded / Rejected | Relationships |
| --- | --- | --- | ---: | ---: | --- | --- | ---: |
| Base | 47e1b2836 (checked out as a scratch worktree) | `python3 packs/repo-governance/.apm/skills/navigate-decisions/scripts/navigate_decisions.py export --root /private/tmp/ndq/base-wt --destination /private/tmp/ndq/cmp --name base.html` | 6,706,491 | 258 | 149 / 109 | 254 / 3 / 1 | 883 |
| Final | 520986b62 (HEAD with the 2.5.0 projections) | same, `--root .` and `--name head.html` | 6,705,049 | 258 | 149 / 109 | 254 / 3 / 1 | 883 |

Every count matches (records, kinds, lifecycle values, relationships); the file shrinks by 1,442 bytes. Counts come from the `nav-data` JSON island of each file.

## Screenshots (AC-0028 evidence)

`notes/screens/<width>-<theme>-first.png` (no hash, the first screen) and `<width>-<theme>-picked.png` (first Recently decided row clicked), true viewports of 320x800, 1280x900, 1680x1000 and 2560x1200, light and dark: 16 files, from the final export (`/private/tmp/ndq/cmp/head.html`), captured with Playwright's bundled Chromium.

## Build and lint (T4)

- `make build-self`: regenerated the `.agents/` and `.claude/` projections (committed); a second run leaves no diff.
- `uv run --with ruff ruff check .`, `uv run --with mypy python tools/lint-mypy.py`, the navigate-decisions suites with the two roster tests and `test_skill_html_view_tokens.py`, `python3 tools/check_view_base_parity.py` and `python3 tools/changelog.py validate`: see the T4 report; all exit 0.
- Edited-test list checked by comparing function ASTs against 47e1b2836: 18 changed functions and the `_ZONE_VIEWS` constant, all in `browser_checks.py`, all in the table above. `test_html_publication.py` and `test_query_contract.py` have no changed function.
