# Verification ledger: intent view tree, roadmap and grouped rail

## Base commit

- Base commit: `94774e03b3538855753d214420823df357fbf72a`, `origin/main` after PR #1573 merged, on 2026-10-17. Every criterion and proof that names the base commit uses this id.

## T1

- Implemented by an `implementer` subagent. `fixtures/roadmap/` holds 36 records (25 intents, 4 briefs, 6 specs) with each record's band, placement, progress, cells and tree roots stated by hand in its README. `_roadmap_expectations` agrees with every hand-stated value (`test_roadmap_fixture_matches_hand_stated_bands`). The resolver refuses one edge of a parent loop, so the unreachable-loop branch of the Tree root rule is exercised by `test_roadmap_tree_roots_take_the_first_loop_member_when_no_edge_is_refused`, which edits the payload so no loop edge is refused. The fixture has no strategy between two capabilities; that rule is stated in the spec's terms only.
- Gates: `test_export_html.py` 24 passed; `view_browser_checks.py -k roadmap` 2 passed; `lint-pack-test-boundary.py` ok; `make lint-ruff lint-mypy` clean; navigate-intents suite without the browser file 518 passed, 4 skipped in 191s.
