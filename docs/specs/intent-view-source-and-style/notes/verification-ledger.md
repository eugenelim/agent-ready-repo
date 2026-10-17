# Verification ledger: intent view source parts and refined style

## Base commit

- Base commit: `f07d39b534b32a8b71c0f1572d1567f72ca76104`, the merge-base of `eugenelim/navigate-decisions` with `origin/main` on 2026-10-16. Every criterion and proof that names the base commit uses this id.

## Transformation proof (T1)

The joined script is byte-identical to the base commit's `view.js` with lines 2-10 moved to follow line 11. Base commit: `f07d39b534b32a8b71c0f1572d1567f72ca76104`. Run before `view_assets/view.js` was deleted.

Command (the joined script is the builder's prologue, the 14 parts in the builder's part list order, and the epilogue, written to `/tmp/t1_joined.js`):

```
git show f07d39b534b32a8b71c0f1572d1567f72ca76104:packs/core/.apm/skills/navigate-intents/scripts/view_assets/view.js > /tmp/t1_base.js
{ sed -n '1p' /tmp/t1_base.js; sed -n '11p' /tmp/t1_base.js; sed -n '2,10p' /tmp/t1_base.js; sed -n '12,$p' /tmp/t1_base.js; } > /tmp/t1_expected.js
cmp /tmp/t1_joined.js /tmp/t1_expected.js
```

Result: `cmp` printed nothing and exited 0 (identical). The working-tree `view_assets/view.js` also `cmp`-equalled the base file before deletion.

Largest part: `list-bodies.js`, 310 lines (limit 400). The parts total 1705 lines, which is the base file's 1708 less the 3 prologue and epilogue lines.

SHA-256 of each part:

| Part | SHA-256 |
| --- | --- |
| `escape.js` | `b85d3aeb8f8d732a59547e97f21e93100a0a455b182c71eeb730d38372e0e9d1` |
| `labels.js` | `32f6309a25b791dd20639ff0f65066d858b438ba4fc64528a0889b02ada08bc7` |
| `utilities.js` | `fb122d46c885d02f11823b571ea2c06b8d6ad3e0c7259e61538d51635973ab34` |
| `data.js` | `d7dd712308bf8c2d3a220a032f97147a24b3444e1db95d23d78cb4e8dba1f496` |
| `lists.js` | `0043fbb2e113d249e62d24095a93139ae526ab60174f36b48acd87d6849641d3` |
| `routing.js` | `cee6a0454e74d45dd90e12a4d0718389d295e396436fc24e676e9c89dba9802c` |
| `small-parts.js` | `8052383bf679535cc3738631d35f6a65d4f70c28e991d4257c0dcfa27ec1ca26` |
| `rows.js` | `7ac319eec898556bd32ecdda3ff4394b18d7a969d1ca6724a41af8a8e2f98aa7` |
| `list-bodies.js` | `fa8097b759b592fd7deeed67ab35c710679ed107e702acc92052c49ac9318c85` |
| `detail.js` | `32ce1a75d9b0848e7cdfb5346d1a320bec52727eaf2852867ea7b76d3a6bb673` |
| `dependencies.js` | `9d6e2beb378739a387eb62769cd185c137b9f81e73eddf8a8effb0b8421a4379` |
| `detail-parts.js` | `7ee32743b999db90ad3f21d6ebaab23073d9329b40f4717e37c77e3ee2c3dfee` |
| `detail-render.js` | `fb2f58b385c10aa059147a9b5e324b5f2663d6f35f8a8e797c1ab15b9c9d7623` |
| `chrome.js` | `d6d0fa91fb476d76daa4f33f42e81ccf51f708e9fa855404e6f70b48f5d3e87f` |

## Dispatch notes

- T1 was implemented by an `implementer` subagent and verified by the controller: `test_export_html.py` 16 passed in 7.8s; `make lint-ruff lint-mypy` clean; the implementer's full run of `packs/core/tests/skills/navigate-intents` was 507 passed, 4 skipped.
- T2 was written by the controller, not an implementer, because its records carry the owner's 2026-10-16 decisions and the owner's Approver signature on the RFC-0108 errata. The receipt vocabulary offers only `no-implementer-installed` and `human-directed`; it is recorded as `human-directed`, the closer of the two. Checks: `tools/validate_guides.py` exit 0; `lint-spec-status.py --root .` clean; `workspace.toml` parses.
- T3 was implemented by an `implementer` subagent: `packs/core/tests/skills/navigate-intents` 514 passed, 4 skipped (pre-existing corpus skips in `test_review_regressions.py`) in 230s; `view_browser_checks.py` 144 passed, 1 failed in 250s. Its first-pass rendering of the real export was pixel-identical (0 differing pixels, light and dark, 1440×1000) to the base stylesheets plus `notes/prototype/approved-overlay.css`. Four shipped browser checks then required small differences from the prototype, made in the style and not the tests: the empty detail heading uses small capitals instead of an uppercase transform (`test_ac_0030` reads `inner_text`); the approved mark's glyph keeps `--c-text` (`test_fix_approved_glyph_uses_the_text_colour`); "Open beneath" keeps its two-column grid (`test_fix_open_beneath_aligns_name_and_state`); the three-track row starts at 66rem (`test_fix_rows_stay_inside_their_row_from_640_to_1440`).
- The one failure, `test_ac_0040_live_region_announces_list_title_and_count`, is pre-existing and flaky: alone it failed 3 of 8 runs on the base commit and 3 of 8 on this change. It is recorded as `pre-existing-intent-view-live-region-test-flake` in `workspace.toml` `[backlog].open`.
- Controller follow-ups after T3: the unused `--c-accent-ring` role removed from the base and the token file; the dependency gutter colour set to `--c-detail-bg`; the token file's row breakpoint corrected to 66rem. `test_export_html.py` 23 passed in 5.4s; `make lint-ruff lint-mypy` clean.
- T5 was done by the controller (receipt `human-directed`; see the T2 note for why that reason is used). Checks: `agentbundle catalogue self-host --root . --write --force` (forced past the dirty-tree check only, because T4's test file was mid-edit; projections exclude tests) synced `view_src/` into `.claude/` and `.agents/` and removed both `view_assets/view.js` copies; a second run showed no diff; `agentbundle catalogue lint --root . --deep` ok (75 pre-existing findings); `agentbundle catalogue verify --root .` ok; `tools/check_view_base_parity.py` ok (1 file); `tools/changelog.py validate` exit 0; `tools/lint-guide-titles.py`, `tools/validate_guides.py` and `tools/lint-guides-no-repo-only-refs.py` exit 0. Core is 3.1.7 in `pack.toml` and `.claude-plugin/plugin.json`.
- T4 was implemented by an `implementer` subagent: the full `view_browser_checks.py` run was 191 passed, 1 failed, 0 skipped in 369s; the failure was the pre-existing flake `test_ac_0040_live_region_announces_list_title_and_count` (alone, 3 re-runs: pass, fail, fail). Red proofs, each by appending breaking CSS to `view-base.css` and restoring it: a transition and an animation outside the reduced-motion block turned `test_reduced_motion_is_still` red; transparent control borders turned `test_control_borders_clear_3_to_1[1280-light]` red (ratio 1.0); a name shifted 3000px left turned `test_nothing_spills_out_of_a_zone[1280-light]` red.

## Real export pair (AC-0028)

- Both exports read this repository's corpus at `a7e126f47`, so only the view code differs: the base builder from `git archive f07d39b534b32a8b71c0f1572d1567f72ca76104 packs/core/.apm/skills/navigate-intents/scripts`, and the final builder at `a7e126f47`. The corpus at the base commit lacks this spec, which would change the first count for a reason unrelated to the view.
- Commands: `python3 <base-scripts>/navigate_intents.py export --root . --destination <tmp> --name base.html` (status ok, 663,612 bytes) and `python3 packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py export --root . --destination <tmp> --name final.html` (status ok, 674,990 bytes). Both files were written outside the repository and not committed.
- Four question counts read from `.q-count` in headless Chromium at 1440×900: base 31, 14, 105, 10; final 31, 14, 105, 10. Result: pass.

## Screenshots (T6)

Real export at `84626d4d1` (after the review fix to "Open beneath" below), "What is still open under a capability?" with its first row picked, true viewport sizes, headless Chromium:

| File | Viewport | SHA-256 |
| --- | --- | --- |
| `notes/screens/320-light.png` | 320×900 | `44d9f70c3ce0a80b979f2d0dde69894bc8938855bb7362ab151a5197e0ceeed1` |
| `notes/screens/320-dark.png` | 320×900 | `aa2b56c09652610b2383877ba87ea32c6b7d03153c521a8b3aba07a0582ee12c` |
| `notes/screens/1280-light.png` | 1280×900 | `5116b226bb6d4a55127e5a5a3fafc5dc5ed35252ea9d40a8aa9731ed412b12bb` |
| `notes/screens/1280-dark.png` | 1280×900 | `3bd52b47d5e06594a53d1e3155ff3d84f068193924641c109d135512404eae86` |
| `notes/screens/1680-light.png` | 1680×1050 | `c017d85474b7c1404561f399aafeaf76e6dd53f4d1d63a0a9c8519fdccf7975c` |
| `notes/screens/1680-dark.png` | 1680×1050 | `3d0f8682f0d0c5d5578375224d20a3a72ca3ee8aeeca523c4ac83741282b1214` |
| `notes/screens/2560-light.png` | 2560×1440 | `3ec0105ec7243f2150109e1da058e816a129d2eb58610c0a7175317320b892b9` |
| `notes/screens/2560-dark.png` | 2560×1440 | `b3d744ac6796b0748e451fb236c9d201591e3281da339608bfa7c27f8b373d92` |

## Experience review (AC-0029)

- Round 1, `experience-reviewer` over the eight screenshots at `a7e126f47`: SHIP WITH CHANGES, no Blocker, one Major: "Open beneath"'s fixed 8.5rem state column squeezed names to 4–7 lines at 320 and 1680. Fixed at `84626d4d1`: the column is 7rem, and a detail zone narrower than 28rem stacks the state under the name. `view_browser_checks.py -k "beneath or spill or ac_0031 or ac_0033 or ac_0034 or ac_0035 or ac_0036 or sticky or detail"`: 54 passed in 128s. Screenshots re-taken at `84626d4d1` (table above).
- Minors left as they are (not required by AC-0029, which bars only Major and Blocker): "Ready" shares the approved mark; two pill axes in the detail at 2560; at 320 the header and questions sit above a picked item; the 2560 list zone is under half used with this 14-row list. Nits: the script-focused heading ring at 320, the small Key marker, and screenshot coverage of only one state.
- Round 2, same reviewer over the re-taken screenshots at `84626d4d1`: no Major or Blocker remains. New Minor: in a narrow detail zone the stacked state no longer forms an aligned column (accepted as the trade-off for zones under 28rem). New Nit: the gap above a stacked pill varies by about 5px between one-line and two-line names. Result for AC-0029: pass.

## Full browser suite at the final code commit (AC-0021)

- `python3 -m pytest packs/core/tests/skills/navigate-intents/view_browser_checks.py -q -rs` at `84626d4d1`: 192 passed, 0 failed, 0 skipped in 319.5s.
- Owner-accepted exception, 2026-10-17 (eugenelim): `test_ac_0040_live_region_announces_list_title_and_count` is flaky on the base commit and on this change because of its own wait condition (it can pass on the previous question's stale state). AC-0021's "every test passes" is held with this one exception, which stays tracked as `pre-existing-intent-view-live-region-test-flake` in `workspace.toml` `[backlog].open`. It passed in the run above.

## Owner approval (AC-0030)

- 2026-10-17: eugenelim approved the rendered real export at `84626d4d1` as matching the prototype in `notes/prototype/approved-overlay.css`, with the differences recorded in the T3 note and the "Open beneath" stacking fix.

## Code review dispositions

- `security-reviewer`: `Clean — ready to commit.` with a `## Not checked` footer, adjudicated by the controller. Its first item (no test asserts the stylesheets hold no `url(` or `@import`) is already covered by the shipped `test_stylesheets_declare_no_motion_or_external_loads`, which keeps both checks. The remaining items (browser runtime digest, dependency scanning, install file modes, unchanged parts beyond a sink grep) are outside a source review of this change.
- `adversarial-reviewer` round 1: Blocker 1 (the navigation survey names other products) is refuted: the owner's rule bars naming the restyle's inspiration source, and the owner asked for that survey by name. The survey is input to slice 13, not this spec, so it was moved off this branch and travels with slice 13. Blocker 2 and Concerns 3 to 5 are accepted: the full-suite pass, the re-review, the owner approval and the export pair at the final commit are recorded here; the plan is `Executing`; the ledger and screenshots are committed.
- `frontend-reviewer`: Major 1 (selection indicators vanish under forced colors) accepted and fixed in the review-fix batch. Minors 2 to 5 (dimension literals outside the token set, focus radius overriding element radius, a `1.5rem` target that depends on the root font size, the stacked-pill gap) are not required by this spec's criteria and are left as they are; the `1.5rem` target predates this change.
- `quality-engineer`: Concerns 2 to 4 and Nits 5 and 7 accepted and fixed in the review-fix batch. Concern 1 (the flaky test's cause) is handled by the owner-accepted exception above and the corrected backlog entry. Nits 6, 8 and 9 are left as they are.

## Final code commit

- The final code commit is `fd64d63a0`. After `84626d4d1` it changed a `@media (forced-colors: active)` block in `view-base.css`, the missing-part refusal message in `intent_view.py`, tests, the token file (it now names `--s-6` and `--target`), and removed the navigation survey from this branch, so the screenshots and the owner's approval at `84626d4d1` show the same rendering in normal colour mode.
- Real export pair re-run at `fd64d63a0` (AC-0028), same method as above: base builder 663,612 bytes, final builder 675,678 bytes; counts base 31, 14, 105, 10 and final 31, 14, 105, 10. Result: pass.
- Review-fix batch checks at `fd64d63a0`: `test_export_html.py` 25 passed in 6.5s; `make lint-ruff lint-mypy` clean; browser subset (`broken_entries`, `ac_0036`, `ac_0037`, `current_question`, `rows_are_flat`) 31 passed in 97s; forced-colours spot check: current question and picked row compute a 3px solid outline; `tools/check_view_base_parity.py` ok.
- Full `view_browser_checks.py` at the final code commit `fd64d63a0`: 192 passed, 0 failed, 0 skipped in 383.9s (AC-0021, with the owner-accepted `test_ac_0040` exception, which passed in this run).
- `python3 -m pytest packs/core/tests/skills/navigate-intents -q` at `fd64d63a0`: 516 passed, 4 skipped (pre-existing corpus skips in `test_review_regressions.py`) in 243.6s. `lint-spec-status.py --root .` clean; `lint-contract-item-alignment.py` 0 findings.
- T6 was done by the controller (receipt `human-directed`, as for T2 and T5).

## CI correction before merge

- PR #1573's "Pack runtime boundary" step (`tools/lint-pack-test-boundary.py`) failed: 8 pack-test paths reached above `packs/core` (the repository token file, and part paths joined from a variable). `1d5849276` moves the token-file checks to `tests/roster/test_skill_html_view_tokens.py` (named build-check step and `lint-ci-parity.py` entries added), looks parts up through a confined glob, and makes `test_ac_0036_text_contrast` read `--c-canvas` from `view-base.css`. AC-0021's wording and the Testing Strategy were corrected to match, with no change to what either checks: the roster test proves the token file and `view-base.css` agree. Local results: `lint-pack-test-boundary.py` 0 failures; `test-lint-pack-test-boundary.py` 158 passed; `lint-ci-parity.py` ok; `test-lint-ci-parity.py` 218 passed; roster token test 3 passed; `test_export_html.py` 23 passed; browser `-k "ac_0036 or vi_4002"` 10 passed; `make lint-ruff lint-mypy` and `ruff check .` clean.
