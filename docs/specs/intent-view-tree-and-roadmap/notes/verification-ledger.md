# Verification ledger: intent view tree, roadmap and grouped rail

## Base commit

- Base commit: `94774e03b3538855753d214420823df357fbf72a`, `origin/main` after PR #1573 merged, on 2026-10-17. Every criterion and proof that names the base commit uses this id.

## T1

- Implemented by an `implementer` subagent. `fixtures/roadmap/` holds 36 records (25 intents, 4 briefs, 6 specs) with each record's band, placement, progress, cells and tree roots stated by hand in its README. `_roadmap_expectations` agrees with every hand-stated value (`test_roadmap_fixture_matches_hand_stated_bands`). The resolver refuses one edge of a parent loop, so the unreachable-loop branch of the Tree root rule is exercised by `test_roadmap_tree_roots_take_the_first_loop_member_when_no_edge_is_refused`, which edits the payload so no loop edge is refused. The fixture has no strategy between two capabilities; that rule is stated in the spec's terms only.
- Gates: `test_export_html.py` 24 passed; `view_browser_checks.py -k roadmap` 2 passed; `lint-pack-test-boundary.py` ok; `make lint-ruff lint-mypy` clean; navigate-intents suite without the browser file 518 passed, 4 skipped in 191s.

## T2

- Implemented by an `implementer` subagent. The rail is four `aria-labelledby` lists under `h2.rail-group` headings (hidden below 90rem by a media rule copying `.visually-hidden`), built from a `RAIL_GROUPS` table. `view.css` gained a 66–89.99rem rule keeping six tabs on one line, which `test_ac_0032_mid_width_questions_row_above_list_beside_detail` required. `test_ac_0040_live_region_announces_list_title_and_count` now waits for the clicked link's `aria-current` before reading the live region — the cause the source-and-style review named for its flake.
- Gates: full `view_browser_checks.py` 205 passed in 335s; navigate-intents suite without the browser file 519 passed, 4 skipped; `lint-pack-test-boundary.py` ok; `make lint-ruff lint-mypy` clean; self-host and `check_view_base_parity.py` ok.

## T3

- Implemented by an `implementer` subagent: `view_src/roadmap.js` (160 lines). Band separators are a `border-left` rather than a generated `·`, because Chromium put generated text into the row link's accessible name and `test_ac_0041_names_contain_visible_labels` failed on it. Red proofs: changing `birch-cap`'s hand-stated progress in the fixture README failed `test_roadmap_fixture_matches_hand_stated_bands`; removing `Shipped` from the view's delivered words failed `test_roadmap_progress_text` and `test_roadmap_cells` on `capability:anchor-cap` (1 delivered and 13% against the expected 3 and 30%). Both restored.
- Gates: full `view_browser_checks.py` 215 passed in 298.6s; navigate-intents suite without the browser file 519 passed, 4 skipped; `lint-pack-test-boundary.py` ok; `make lint-ruff lint-mypy` clean; self-host and parity ok. A real export at 1680×1100 shows 3 sections and 22 capability rows in both themes.

## T4

- Implemented by an `implementer` subagent. The tree moved from `list-bodies.js` into a new part, `view_src/browse.js` (248 lines; `list-bodies.js` 233), with Show and Group as route keys (`show`, `group`; defaults omitted from the fragment). Tree rows keep the shipped context text (so "refused parent:" and "outside this export" still show) beside the context tag, "c/t closed" and "n open items". `treeRoots` now follows the spec's loop rule. Red proof: changing the context tag to `ctx` failed `test_show_open_and_done_with_context_rows[open-hierarchy]`; restored.
- Gates: full `view_browser_checks.py` 234 passed in 355.7s; navigate-intents suite without the browser file 519 passed, 4 skipped; `lint-pack-test-boundary.py` ok; `make lint-ruff lint-mypy` clean; self-host and parity ok. A real export under "Open" lists 145 intents: this repository's 169 less its 24 terminal intents.

## T5

- Done by the controller (receipt `human-directed`: the controller wrote the docs and release records). Also in this task: the Browse lead now reads "Every intent in the export, under its parent or its nearest capability." (the old "Every live intent under its parent." did not describe By capability), and the subtree toggle's arrow is 1rem in `--c-muted`, both from the T4 screenshots. An eval case for the progress question joins `evals/eval_queries.json` (56 queries).
- Checks: core 3.1.8 in `pack.toml` and `.claude-plugin/plugin.json`; `tools/changelog.py validate` exit 0; a second self-host shows no diff; `agentbundle catalogue lint --root . --deep` ok (75 pre-existing findings); `agentbundle catalogue verify --root .` ok; `check_view_base_parity.py`, `lint-pack-test-boundary.py`, `lint-guide-titles.py`, `validate_guides.py`, `lint-guides-no-repo-only-refs.py` and `check-guide-index.py` exit 0; `lint-spec-status.py` clean; `make lint-ruff lint-mypy` clean.
