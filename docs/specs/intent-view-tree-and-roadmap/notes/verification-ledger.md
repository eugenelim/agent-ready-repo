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

## T6

### Real export against the oracle (AC-0045)

- `navigate_intents.py export --root .` at `1cebab93f` (698,358 bytes, outside the repository) opened in headless Chromium at 1680×1100 and read with `_read_roadmap`, compared with `_roadmap_expectations` over the same export's payload: 3 sections in the same order, 22 capability rows, 0 mismatches in counts, shares or cells.
- Graph-powered SDLC: Decision graph 33%; Delivery-system coexistence 0%; Repository work graph 69%; Workspace coordination reorganization 0%.
- Trustworthy organisation-owned catalogues: Catalogue publication 0%; Catalogue trust and adoption 0%.
- Not under a product strategy in this export: Digital experience doctrine 14%; First-class distribution routes 33%; Loop telemetry governance 0%; Nontechnical-pack first-value rollout 0%; Optional code intelligence composition 78%; RFC-0088 browser pilot readiness 0%; Work-item capture and disposition 11%; Work-loop delivery efficiency 29%; and 8 capabilities with nothing beneath yet.

### Screenshots

Real export at `ee4374c4b` (after the review fixes below), reduced motion on, true viewport sizes. `roadmap-*` shows "How far along is each capability?"; `browse-*` shows "Browse all intents" with Show = Open, Group = By capability, after Expand all.

| File | SHA-256 |
| --- | --- |
| `notes/screens/browse-1280-dark.png` | `4801bb22e72d676f162cc9b4110317b978a358d83abbeff1a92b7b45f3ddb556` |
| `notes/screens/browse-1280-light.png` | `bc014e12e76591e20e292e3df704b265b5a4a000d690972187f022ca2743368f` |
| `notes/screens/browse-1680-dark.png` | `8c2cd0fb718e0584291d9cdf4c035c134a216cfe9222ee83b71891f8e974fa32` |
| `notes/screens/browse-1680-light.png` | `7aecb150a8db63078828c22ed696f73763db6006ea55a2bdca7effc8eb78c5c9` |
| `notes/screens/browse-2560-dark.png` | `060000f5b546db15f660e5ba08c4e40a3bc83d27dc152ea8c8d6a2be8cfa76cc` |
| `notes/screens/browse-2560-light.png` | `e804b2c8b632615deafe946ad7936f5f8129da11148b494f49ead48012bbee67` |
| `notes/screens/browse-320-dark.png` | `f5351a005f8a67b90050963645f220ff461a10fc547cfefef70bc19d56683b41` |
| `notes/screens/browse-320-light.png` | `00f66d66cfd93274ceb67ca6c7525d54b38fefbee2b4ee46660b7b3d7bd32bff` |
| `notes/screens/roadmap-1280-dark.png` | `3ec1843eeeebb6dc12c76b429c36ec1c0730fa1b0aac617b794fc9500c1cd86b` |
| `notes/screens/roadmap-1280-light.png` | `0dcebfb8af7f204f579bcbcae3465d700815b43e9e75c93a4dfd0e49420fff24` |
| `notes/screens/roadmap-1680-dark.png` | `fd230fa2fceeab1fd01f6c50b876d58b742f9ba64d22c1d70d6af23da0dcbf46` |
| `notes/screens/roadmap-1680-light.png` | `f0b0ae7a6adc670540f0c1f13778f99117e1eb75928ad02c356363eb0786a187` |
| `notes/screens/roadmap-2560-dark.png` | `ebf9e4db838823492236fe082734cec9ea1ce7dd95a3599bc03e72864f60afbe` |
| `notes/screens/roadmap-2560-light.png` | `4bef430cbc00d6811c83868ece747d95594bb271aa644831a832108a62bc50e0` |
| `notes/screens/roadmap-320-dark.png` | `bdff53ddce5e92d3f57500aec52a2f3a1b4333d83740a577393547cbb715a2e0` |
| `notes/screens/roadmap-320-light.png` | `420ebf361f45e498f725c8cf15414278109bc51b90c0a1e432acbb07fb87b7ec` |

### Experience review (AC-0046)

- Round 1, `experience-reviewer` over the 16 screenshots at `1cebab93f`: SHIP WITH CHANGES, no Blocker, 9 Majors. Dispositions:
  - 1 (strategy and capability bars on different axes) — fixed: one bar column, fixed bar and share widths, one left edge for counts at every depth.
  - 2 (strategy totals do not sum from the rows) — not a defect: a strategy's work beneath includes the capabilities themselves and work placed directly under it, by the spec's term. Fixed by stating it under each strategy heading.
  - 3 (share has no stated meaning) — fixed: "<p>% delivered of <n> items" and a visible line saying the bar counts items, not effort, that withdrawn and archived work is stopped and not in the share, and the snapshot time.
  - 4 (Browse summary contradicts the controls) — fixed: the lead and sort key follow Show and Group.
  - 5 (state and context step right with depth) — fixed: trailing tracks hold one x at every depth (`test` added).
  - 6 (context text is boilerplate) — not changed: the context text is fixed by the session-start spec's criterion 0011, which this spec carries; recorded as a follow-on.
  - 7 (rail grouping invisible below 1440) — fixed within AC-0003: labels stay hidden, groups show as dividers and gaps.
  - 8 (1280 list squeezed beside an empty detail) — fixed: the list takes `2.4fr` against a `minmax(18rem, 1fr)` detail until a row is picked.
  - 9 (toolbar order, wrapping, colour-only selection, filters vs Group) — fixed: toolbar above filters, whole-segment wrapping, a ✓ and weight on the pressed button, Group and expand disabled with a hint while a filter is set.
  - Minors fixed: 10 (no separator starts a line), 12 (open items in the link accent), 16 (Expand all looks the same in both themes), 17 (dark empty-cell outline measured at 4.18:1, faintest anti-aliased pixel about 3.2:1), 19 (toggle aligned to the name, 32×32 target). Minors 11, 13, 14, 15, 18, 20 and nits 21–25 left as they are; 14 and 15 name sections the spec fixes.
- Polish gates at `ee4374c4b`: full `view_browser_checks.py` 238 passed in 376s; navigate-intents suite without the browser file 519 passed, 4 skipped; `lint-pack-test-boundary.py` ok; `make lint-ruff lint-mypy` clean; self-host and parity ok.
