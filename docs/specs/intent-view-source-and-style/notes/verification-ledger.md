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
