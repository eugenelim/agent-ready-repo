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

Real export at `441bd1cd1` (after T7), reduced motion on, true viewport sizes. `roadmap-*` shows "How far along is each capability?"; `browse-*` shows "Browse all intents" with Show = Open, Group = By capability, after Expand all.

| File | SHA-256 |
| --- | --- |
| `notes/screens/browse-1280-dark.png` | `bbf426946096392e35c4253fdb4ade32868edff068ada78b4fa1c2f7909a5e19` |
| `notes/screens/browse-1280-light.png` | `73d4c728c5b0929b4588cc4ad7ebe572f315a5ecf8d80cd0024218bd76c92787` |
| `notes/screens/browse-1680-dark.png` | `b8cdf15283f024768d4273da994a5932608c9effa709e5cb1f5700e0b43d5216` |
| `notes/screens/browse-1680-light.png` | `83fb055254494c5958e1357120a44dc2c84c7f249e3f7412f8ac3bd2ace11df6` |
| `notes/screens/browse-2560-dark.png` | `956aa867d7a0ac0cf54892ccae1e2ea3ed78903a5257903dc430d2b2c784bf4f` |
| `notes/screens/browse-2560-light.png` | `319d549eb6042f0faea8e82c636791100c6fd48b28850305d4de0778418afd11` |
| `notes/screens/browse-320-dark.png` | `7ad31587bcc543a40507496028290dbf06ef3bd7db81e0f3e545410ab4f834a3` |
| `notes/screens/browse-320-light.png` | `7bcf1a19d6f2c0de8b66d8e906c3a02342ee7ab4015fc2fe82a54470c148e852` |
| `notes/screens/roadmap-1280-dark.png` | `8417fb1a6943da557c7a324d788c057a291018965e8ab1f97cc7226a5c8a8c75` |
| `notes/screens/roadmap-1280-light.png` | `16e7fe96360468283e0d2b0b5e1d96b9e90554f74e29625d00e5e0de6bf8e3a2` |
| `notes/screens/roadmap-1680-dark.png` | `4600cae0f6d9e3fc7e433551646ac71298f9004971f0f73df4edf33d9c3e3e8e` |
| `notes/screens/roadmap-1680-light.png` | `c84ce3f6704a475cb728bd064f29d6a9ba27ae6dffabc940754590ad3751aed0` |
| `notes/screens/roadmap-2560-dark.png` | `53064888e72f9067cc0e219389b8053c5add91dd40f4fdc84d8da360030ddaf4` |
| `notes/screens/roadmap-2560-light.png` | `2d709ae6e7ded9732f2c33c470f752872e56f70b615f0171ca24aaa94aa2ad13` |
| `notes/screens/roadmap-320-dark.png` | `4941906334344ef251d085f1d115919b6373a62780e01a3a2a01b30adc12eb49` |
| `notes/screens/roadmap-320-light.png` | `6e8869f6f2e9bf38375553dc263f27f184d359eec11f04815bf48f5a6e16c884` |

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
- AC-0045 re-run at the final code commit `ee4374c4b`: export 703,768 bytes; sections equal to the oracle's, 22 capability rows, 0 mismatches. The full browser suite at this code is the polish run above (238 passed).
- Round 2, same reviewer over the re-taken screenshots and two context-row screens: Majors 1, 2, 3, 4, 5, 7, 8 and 9 fixed (the disabled-while-filtered part of 9 is covered by `test_filter_disables_grouping_and_expanding` rather than a screenshot); Major 6 open as a deliberate deferral to the session-start spec's criterion 0011, pending the owner's decision. No new Major or Blocker. New Minors recorded and left as they are: context rows run to three lines and show open items on a Done view; level tags use the accent and in-progress hues; 320 rail groups are subtle; at 320 Browse opens on controls; the note does not say which records count as items; the Browse lead reads "Open work only. Every intent …"; empty bar cells read like zeros.

## Owner approval (AC-0047)

- 2026-10-17: eugenelim approved the rendered real export at `ee4374c4b` for planning and leadership reporting, and accepted the experience review's remaining Major 6 (repeated "Intent · <level> · under <parent>" context text on tree rows) as a follow-on rather than a change to this spec; see § Follow-ons.

## Code review round 1 and the contract amendment

- `frontend-reviewer`: `Clean — ready to commit.` with six Minors (a literal 2px cell radius, untokened sizes, no fallback for the ✓ alt-text content, a toggle name that reads "Show …" while expanded, synchronous Expand all on very large exports, no state captures); the radius and the ✓ fallback are taken in T7, the rest left as they are.
- `quality-engineer`: Concern 1 (the Browse oracle mirrors `browse.js` and is pinned to no hand-stated value) and Concern 2 (`test_ac_0040`'s last step still waits on state that can be stale; the flake is not shown fixed) sustained; Nits 3 to 6 taken where cheap (x-alignment at 1280 and 1440, the done/capability context-row guard, the hard-coded `- 2` bar count). The backlog entry `pre-existing-intent-view-live-region-test-flake` stays open until 16 consecutive solo passes are recorded.
- `adversarial-reviewer`: Concern 1 (Browse's sort key changes under "By capability" with no criterion), Concern 2 (a capability parent loop drops those capabilities from the roadmap and the by-capability tree, and the oracle mirrors the same walk), Concern 3 (the strategy-between-capabilities rule has no case) sustained; Concern 4 (closeout statuses) is closeout work.
- Owner request, 2026-10-17 (eugenelim): use shorter terms for each rail link — chosen: "Next up", "Broken", "Capability progress", "Open by capability", "No parent", "All intents", with each list showing its full question above its title so the view still names the questions it answers.
- These change the accepted criteria, so the contract is amended under the owner's authority above: AC-0001 names the short labels; new AC-0051 (the full question above each list title), AC-0052 (Browse's sort key and lead per Group and Show) and a capability-loop term; a new task T7 carries the work. Completed tasks T1 to T6 keep their evidence in the sections above.

## T7

- Implemented by an `implementer` subagent under the amended contract. Short labels (AC-0001), the question line above each list (AC-0051, empty during a search), link descriptions through visually hidden `q-desc-<key>` spans (AC-0054), Browse's sort keys and leads (AC-0052, AC-0053), and capability loops (`onParentLoop` in `nearestUp`; red proof: with the rule removed both `test_capability_loop_lists_each_capability_once` cases failed). The strategy-between-capabilities case passed on the old code too: the old walk already nested the lower capability. Hand-stated Browse values for four nodes are asserted against the page and `_browse_expectations`.
- `test_ac_0040_live_region_announces_list_title_and_count`, with its last step now waiting for the filter to apply, passed 16 of 16 consecutive solo runs; the base commit `f07d39b53` failed 3 of 8. The `pre-existing-intent-view-live-region-test-flake` entry is removed from `workspace.toml`, which also retires the source-and-style spec's owner-accepted exception.
- Bundled fixes (no criterion of their own): the live-region wait (16/16 solo passes); x-alignment checks at 1280 and 1440 at the deepest depth (parametrized tests green); `test_roadmap_cells` counts strategies (`len(strategies) >= 2` guard); the done/capability context-row guard; `.rm-cell` radius `var(--r-1)` (`test_roadmap_cells_use_a_radius_token`); the pressed ✓ plain `content` before the alt-text form (`test_pressed_choice_mark_has_a_plain_content_before_the_alt_text_form`); the tree row name-track floor 6rem → 5rem, which the 1440 x-alignment test required (545 vs 543 → pass).
- Gates: full `view_browser_checks.py` 251 passed; navigate-intents suite without the browser file 521 passed, 4 skipped; self-host twice (second run no diff); catalogue lint `--deep` and verify ok; `check_view_base_parity.py`, `lint-pack-test-boundary.py`, `changelog.py validate`, `lint-spec-status.py` and the four guide linters exit 0; `make lint-ruff lint-mypy` clean.

## T6 re-run after T7

- AC-0045 at the final code commit `441bd1cd1`: export 705,479 bytes; sections equal to the oracle's, 22 capability rows, 0 mismatches.
- The 16 screenshots in `notes/screens/` were re-taken at `441bd1cd1` (SHA-256 table above updated); they show the short rail labels and the question line above each list title.
- Experience review round 3 (after T7): no new Major or Blocker; the only open Major is round 2's #6, the owner's recorded deferral. Minors recorded and left as they are: below 1440 the short labels carry no visible hint of their question until clicked (a hover hint would help); the question line is styled unlike other eyebrows; Browse's eyebrow "Browse all intents" is not a question and repeats the title; the roadmap restates its question in title and subtitle; the Browse lead "Open work only. Every intent …" still reads oddly and "Top-level capabilities" is inexact; 320 rail groups are subtle.
- `frontend-reviewer` round 2: `Clean — ready to commit.` with two Minors (Browse's question line repeats its title; an empty question paragraph stays in the DOM during search), left as they are.
- `quality-engineer` round 2: `Clean — ready to commit.` Concerns 1 and 2 closed; Nits left as they are: a comment in `test_ac_0024` naming `test_full_hierarchy_sections` as the cross-section order check, and `generatedText` string surgery in the roadmap legend.

## Final approval after T7 (AC-0046, AC-0047)

- AC-0046 after T7: the experience review's round 3 (above) covers the screenshots re-taken at `441bd1cd1` and found no new Major or Blocker; its one open Major is the owner's recorded deferral.
- AC-0047 after T7: 2026-10-17, eugenelim approved the rendered real export at `9b8106758` (code identical to `441bd1cd1`) for planning and leadership reporting — the short rail labels, the question line above each list, and two layout changes made in T7: bar cells rounded with `var(--r-1)` (6px, was 2px) and the tree row's name-track floor at 5rem (was 6rem, which drifted 2px at 1440). Those two are therefore owner-accepted design changes rather than ride-alongs.

## CI correction before merge

- PR #1574 failed two checks. `tests/roster/test_skill_html_view_tokens.py::test_token_file_names_every_property_the_base_sheet_declares` found eight layout track properties in `view-base.css` (`--name-w`, `--rm-bar`, `--rm-in`, `--rm-prog`, `--rm-self`, `--rm-share`, `--tr-in`, `--tr-self`) that the token file did not name; the token file now lists them under "Track properties". The web build's `/now/` invariant refused the changelog highlight's "in progress"; it now reads "being built or not yet started". Local: the roster token test 3 passed; `tools/changelog.py validate` exit 0. The roster run's `maintenance.lock` `FileNotFoundError` came from an unrelated end-to-end test and is re-run.
