# Plan: Intent view source parts and refined style

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** RFC-0108 D1 and D2 (the view standard and the shared stylesheet); `packs/core/.apm/skills/navigate-intents/scripts/intent_view.py` `build_html` and `_read_asset`, which already join two stylesheets into one hashed element — the script join reuses that seam; `packs/core/tests/skills/navigate-intents/test_export_html.py` and `view_browser_checks.py` are the construction path. Deviation: `_read_asset` gains a confined-root parameter so `view_src/` reads stay under the same confinement helper; no new module.

## Approach

Two independent review units, in order. The first is a WIDE, behaviour-preserving move: `view.js` is cut at top-level declaration boundaries into parts under `view_src/`, and `build_html` joins them. Its proof is mechanical — the joined script equals the base commit's `view.js` with only its header comment moved inside the function — so review reads the transformation, the join and the rewired tests, not the moved lines. The second unit carries the style: the governance records first, then the stylesheet values and the three markup hooks, then the browser checks, then the measurements. The riskiest part is contrast across tinted surfaces in both themes, so the browser matrix runs before screenshots are taken.

## Constraints

- RFC-0108 D1 rules 1 to 10, with rule 9 as corrected by the 2026-10-16 errata entry this change adds; D2's canonical-file and parity-gate rule for `view-base.css`.
- RFC-0105: the view never re-derives the graph; this change touches no payload field.
- `packs/AGENTS.md`: `.apm/` is source; run self-host after edits; bump core's `pack.toml` and `.claude-plugin/plugin.json` together; no internal-governance citations in shipped pack content, so `view_src/` comments cite no RFC, spec or criterion.
- Root `AGENTS.md` "Cut before adding": the join is string concatenation in the standard library; no bundler.

## Construction tests

**Integration tests:** `test_export_html.py` builds the `mixed` and `hostile` exports through `nav.run_export` and reads the page's one script and one style; every script-content assertion reads the joined script from the built page, not from a file.
**Manual verification:** the real-export pair, the screenshots, the `experience-reviewer` pass and the owner's approval, each recorded in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| RFC-0108 errata | T2 | Errata entry diff | Entry dated 2026-10-16, signed eugenelim |
| Direction and tokens | T2, T3 | File diffs; `test_base_declares_token_tables` | No contradicting sentence; token test green |
| Architecture (`packs/core/DESIGN.md`) | T5 | Paragraph diff | Names `view_src/` and the part list |
| Amended-in-part headers | T2 | Header lines | Both specs name this spec and the amended criteria |
| Delivery brief | T2 | Brief diff | Slices 11a, 11b, 12, 13 and the Spec-map row |
| User guide | T5 | Guide lints | Reduced-motion sentence present |
| Changelog and version | T5 | Fragment; `pack.toml` and `plugin.json` at the same next patch version | Fragment validates |
| Verification ledger and screens | T1, T4, T6 | Ledger entries; `notes/screens/*.png` | Cited by the PR |
| Coordination | T2 | `workspace.toml` entry | Follows spec status |

## Design (LLD)

### Component / module decomposition

Traces to: AC-0001, AC-0003, AC-0005.

Owned by: T1

Each part begins at a section banner or a top-level declaration of the shipped file, so no function spans two parts. Line numbers are the base commit's:

| Part | Base lines | Holds |
| --- | --- | --- |
| `escape.js` | 2–10, then 12–52 | Header comment, schema constant, unsafe ranges, `escapeDisplay`, the CommonJS export and the no-document return |
| `labels.js` | 53–151 | Fixed label, help and question tables |
| `utilities.js` | 152–177 | `el`, `add`, `text`, `button` and small helpers |
| `data.js` | 178–399 | Payload load and indexes |
| `lists.js` | 400–474 | Question membership |
| `routing.js` | 475–505 | Fragment parse and write |
| `small-parts.js` | 506–619 | Chips, node links, edge items, source block |
| `rows.js` | 620–682 | Row links and state marks in rows |
| `list-bodies.js` | 683–992 | Each question's list body and `renderList` |
| `detail.js` | 993–1050 | Next-step sentence and broken entries |
| `dependencies.js` | 1051–1207 | The dependency walk and its part |
| `detail-parts.js` | 1208–1356 | `part`, `stateLine`, fact lists, record details |
| `detail-render.js` | 1357–1509 | List summary, `renderDetail`, back-to-list |
| `chrome.js` | 1510–1707 | Page start, events, and the `start()` call |

Line 1 (`'use strict';`) and line 11 (`(function () {`) become the builder's fixed prologue, and line 1708 (`})();`) its epilogue. A part file holds its lines, each ending in a newline, so the join adds nothing between parts. The part list is a tuple constant in `intent_view.py` beside `_ASSET_DIR` and is the only owner of order; `_SOURCE_DIR` names `view_src/`, and `_read_asset` takes the confined root as a parameter.

### Behavior & rules

Traces to: AC-0011 to AC-0016.

Owned by: T3

Motion is two rules inside one `@media (prefers-reduced-motion: no-preference)` block in `view-base.css`: a 120ms background, colour, border and shadow transition on rows, rail links, controls and disclosures; and a 160ms fade with a 4px rise on each child of the detail body when it is rendered. Nothing scrolls smoothly and nothing is tied to scroll.

### Quality attributes (NFRs)

Traces to: AC-0019, AC-0020, AC-0022, AC-0025, AC-0026, and the carried contrast, focus and target criteria through AC-0021.

Owned by: T3, T4

The colour roles are chosen so every text role clears 4.5:1 on every surface it sits on (card, canvas, raised, each pill tint) and every control border clears 3:1 against its card; the token file's contrast table records each pair. In-progress states use a violet hue so blue marks only links, focus and selection. The values and rules come from the owner-approved prototype, `notes/prototype/approved-overlay.css`, written as an overlay on the shipped sheets; it is folded into the two sheets by their ownership rule, and its `!important` overrides disappear once the rules they overrode are replaced.

## Tasks

### T1: The joined script equals the base `view.js`; every script test reads the joined script

**Depends on:** none


**Tests:**
- Criteria: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008.
- Transformation proof, recorded in the ledger with the base commit id: the joined script at the T1 commit is byte-identical (`cmp`) to the base commit's `view.js` with lines 2–10 moved to follow line 11.
- `test_export_html.py` gains `test_joined_script_is_prologue_parts_epilogue`, `test_script_digest_covers_the_joined_script`, `test_part_list_matches_view_src`, `test_a_missing_or_unsafe_part_refuses_the_export` (part list patched to a missing name, and a temporary part holding `</script`, then `<!--`), `test_no_part_exceeds_400_lines` and `test_joined_script_is_printable_ascii`.
- The shipped `test_script_holds_no_forbidden_api`, `test_escape_function_matches_the_text_output` and `test_hostile_export_keeps_the_csp_string_and_the_script_stays_clean` read the joined script from the built page; the first gains AC-0006's added tokens with identifier-boundary matching; the second writes the joined script to `tmp_path` before `require`.
- `view_browser_checks.py`'s `test_vi_4002_hostile_values_stay_inert` reads the joined script through the builder.

**Done when:** the proof is in the ledger, and `python3 -m pytest packs/core/tests/skills/navigate-intents -q` passes with `view_assets/view.js` deleted.

### T2: Governance records admit the refined style

**Depends on:** none

**Tests:**
- Goal-based: the errata entry, the direction and token rewrites, the two `Amended in part by:` lines, the brief amendment and the `workspace.toml` entry are in the diff; `python3 tools/validate_guides.py` and `python3 .claude/skills/work-loop/scripts/lint-spec-status.py --root .` pass.

**Approach:**
- The errata entry carries the rule 9 sentence the spec's Decision-rationale row quotes, and records that D2's direction was refined by the owner on 2026-10-16.
- The direction's Form, Material and depth, Containment, Chromatic intensity and Motion rows, its "Quiet surface" meaning and its counterfactual table are rewritten to the refinement; the signature device stays.
- The token file gains § Radius, § Elevation and § Motion tables and a revised § Colour table with its contrast pairs; its "may not adapt" line drops square corners, shadows and motion.

**Done when:** the Tests checks pass.

### T3: The shared stylesheet carries the refined values; the detail card's hooks exist

**Depends on:** T1, T2


**Tests:**
- Criteria: AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0019, AC-0022, AC-0023.
- `test_base_declares_token_tables` parses the token file's three tables and finds each role's light and dark declaration in `view-base.css`.
- `test_layout_stylesheet_defines_no_colour_font_or_token` gains the `box-shadow`, `border-radius`, motion and custom-property checks.
- `test_motion_sits_behind_reduced_motion`, `test_transitions_name_only_paint_properties`, `test_keyframes_fade_and_rise_only` and `test_motion_is_short_and_not_scroll_driven` share one brace-depth walk of both stylesheets that records each declaration with its enclosing at-rule chain.
- `test_state_mark_backgrounds_differ` resolves each `data-mark` rule's `background` through the token table per theme.
- The shipped `test_stylesheets_declare_no_motion_or_external_loads` keeps its `url(` and `@import` checks and drops its motion checks.

**Done when:** those tests pass and the export opens with no console error.

### T4: Rendered style, motion and access hold across the matrix

**Depends on:** T3


**Tests:**
- Criteria: AC-0015, AC-0016, AC-0017, AC-0018, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027.
- `view_browser_checks.py` gains `test_reduced_motion_is_still`, `test_rows_transition_when_motion_allowed`, `test_zones_are_raised`, `test_rows_are_flat`, `test_control_borders_clear_3_to_1`, `test_search_placeholder`, `test_state_line_reads_word_then_type`, `test_broken_entries_are_tinted`, `test_broken_entries_have_a_bar`, `test_current_question_has_a_bar` and `test_nothing_spills_out_of_a_zone`.
- `test_ac_0036_text_contrast` reads its page-background literal from the token file's `--c-canvas` row.

**Done when:** `python -m pytest packs/core/tests/skills/navigate-intents/view_browser_checks.py -q -rs` reports every test passed and none skipped at the final code commit, recorded in the ledger.

### T5: Docs, version and projections follow the change

**Depends on:** T1, T3

**Tests:**
- Goal-based: `agentbundle catalogue lint --root . --deep`, `agentbundle catalogue verify --root .`, a second `agentbundle catalogue self-host --root . --write` showing no diff, `.claude/skills/navigate-intents/scripts/view_src/` present and `.claude/skills/navigate-intents/scripts/view_assets/view.js` absent after self-host, the changelog fragment validating, and `python3 tools/check_view_base_parity.py` exiting 0.

**Done when:** those checks pass and `packs/core/DESIGN.md`, `guides/core/how-to/navigate-intents.md` and the two version files are in the diff.

### T6: The real export is measured, captured and reviewed

**Depends on:** T4, T5


**Tests:**
- Criteria: AC-0028, AC-0029, AC-0030.
- Goal-based: the real-export pair at the base and final commits; eight screenshots of the real export with a row picked, at 320, 1280, 1680 and 2560 CSS px in light and dark, committed under `notes/screens/` with SHA-256 from `shasum -a 256`.
- Visual / manual QA: `experience-reviewer` over the screenshots against the refined direction, adjudicated; then the owner's recorded approval.

**Done when:** the ledger holds the export pair, the screenshot list, the review result and the owner's approval.

## Rollout

Ships as a normal core patch release; reverting the PR restores the shipped view, and no stored state or payload changes.

## Risks

- A part boundary inside a function would break the join; the T1 byte proof catches it before any style work.
- A tinted surface can drop a text pair below 4.5:1 in one theme only; the matrix runs both themes before screenshots.

## Changelog

- 2026-10-16: spec approved by eugenelim
- 2026-10-16: plan approved by eugenelim
