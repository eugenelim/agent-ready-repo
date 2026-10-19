# Verification ledger: intent-view-handover-prompt

Every result below ran against code commit `4139ef24161c6ff24e73bdea0741a0e65bbcfca7` (the last code-affecting commit; it adds docs, the version bump and the self-hosted copies on top of the T1 to T3 code commits `b09b8f206`, `f13466155`, `d8d3d0b7f`). Run on 2026-10-19.

## Scripted browser suite (all of `view_browser_checks.py`)

Command: `uv run --no-project -q --with pytest --with playwright --with pyyaml python -m pytest packs/core/tests/skills/navigate-intents/view_browser_checks.py -q -rs`

Result: 320 passed, 0 skipped, 150.91 s (0:02:30).

Collected suites (`packs/core/tests/skills/navigate-intents/` and `packs/core/tests/pack/`): 939 passed, 4 skipped, 29.75 s. The browser file is not collected by that glob.

## AC-0019: scale bench

Command: `uv run --no-project -q --with playwright python packs/core/tests/skills/navigate-intents/view_bench.py --source . --counts 1 10 25 50`

| copies | outstanding available | default rows | file bytes | startup ms | search ms | heap MiB | meets all |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | yes | 31 | 730,692 | 11 | 13 | 5 | yes |
| 10 | no (resource_limit, limit files) | 0 | 5,101,174 | 35 | 41 | 12 | yes |
| 25 | no (resource_limit, limit files) | 0 | 12,552,249 | 72 | 46 | 27 | yes |
| 50 | no (resource_limit, limit files) | 0 | 24,970,703 | 114 | 48 | 56 | yes |

Pass: `meets_all` is true at every count, under the bench's own thresholds.

## AC-0020: real export of this repository

Command: `python3 packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py export --root <repo> --destination <tmp dir outside the repo> --name repo.html`, then a throwaway Playwright script kept outside the repository. It opens the file in headless Chromium with clipboard read and write granted, picks one record per prompt rule by browse route, clicks "Copy prompt", waits for the button to read "Copied", reads the clipboard, and asserts it equals the spec's template with that record's payload path.

Export: `status: ok`, 711,023 bytes.

| Rule | Record | Copied prompt (equals template + payload path) |
| --- | --- | --- |
| 3 | `spec:intent-view-handover-prompt` | Use the work-loop skill to continue building `docs/specs/intent-view-handover-prompt/spec.md`. |
| 4 | `spec:graph-well-formed-authoring` | Use the work-loop skill to implement `docs/specs/graph-well-formed-authoring/spec.md`. |
| 5 | `spec:bounded-remote-create-action` | Use the new-spec skill to finish the spec at `docs/specs/bounded-remote-create-action/spec.md`. |
| 6 | `brief:acceptance-centered-work-loop` | Use the author-delivery-brief skill in continue mode on `docs/product/briefs/acceptance-centered-work-loop.md`. |
| 7 | `intent:tracker-native-value-before-adoption` | Use the intent skill to decompose `docs/product/intents/FEAT-0014-tracker-native-value-before-adoption.md`. |
| 9 | `intent:intent-delivery-traceability` | Use the close-work skill to check whether `docs/product/intents/FEAT-0003-intent-delivery-traceability.md` can close. |
| 10 | `capability:workspace-coordination-reorganization` | Use the intent skill to keep shaping `docs/product/intents/CAP-0003-workspace-coordination-reorganization.md`. |

Rules the corpus did not hold: none; all seven prompt rules were present and all seven assertions passed.

## AC-0021 input: screenshots

Sixteen PNGs in `screens/`, named `<state>-<width>-<theme>.png`. Each is a true Playwright viewport (width 320 at height 900, or width 2560 at height 1400; not a cropped window) with the detail zone's "Next step" scrolled into view. A throwaway script outside the repository produced them over exports of the `mixed` fixture, the long-path corpus, and a data-block rewrite of `mixed`.

- `prompt-shown`: `mixed`, `spec:bravo-spec` picked.
- `path-refused`: the long-path corpus (mixed plus an Implementing spec in `long-` followed by 115 `a`), that spec picked.
- `hostile-path`: `mixed` with `spec:bravo-spec`'s payload path rewritten to `docs/specs/brav`o-spec/spec.md` (a safe path with a backtick inserted).
- `copy-refused`: `mixed`, `spec:bravo-spec` picked, "Copy prompt" clicked in a context without clipboard permission; the prompt shows selected and the status line shows.

| SHA-256 | File |
| --- | --- |
| `404c9821a8fb51bd0e3611d8cc85419314244cb9d37c1ada52ee7a4f9e4504b5` | `screens/copy-refused-2560-dark.png` |
| `340d665e1de40f4fd8e9d56d2af2b006021e4f6610479805cb1d640fdc3c4a8d` | `screens/copy-refused-2560-light.png` |
| `b4d277b503469994f1011d4192f871acfe486441fe59a9105d3beff46fdaf1fd` | `screens/copy-refused-320-dark.png` |
| `0e1854a02f4ff9e1d643d2615e41b1225d007f390dc2bd0aa8440b3f4308aa01` | `screens/copy-refused-320-light.png` |
| `0bd9aade06eec2c07bc3d87794835acbfd6c2f7839567a211e37a61763c33a37` | `screens/hostile-path-2560-dark.png` |
| `6be1d24ac438e27bb06c63403dca4f6e0bcc1205b393852c2dde9da8deb3b26b` | `screens/hostile-path-2560-light.png` |
| `6e5a311768937daf59fc25cbd0f21e809da69c2cb22cf0d01177a60acf5059f9` | `screens/hostile-path-320-dark.png` |
| `111819f2ca4f0a5587b8be032226937bf865b81210b84c01de6d5534c86127ee` | `screens/hostile-path-320-light.png` |
| `c87783e112311f53343d51cf14c636c0867f5aa0426a73a99f0b480a6ff4ef98` | `screens/path-refused-2560-dark.png` |
| `1865b39d6a263f0400d1311983d2465eda487f65b697713e8ea13a39cf243ac9` | `screens/path-refused-2560-light.png` |
| `a8ddbb9ebe407ed36b5b58e950b97be5aefe5983f8abc03b806dc84e728ac92f` | `screens/path-refused-320-dark.png` |
| `e0b4d63d8c5ad6738e48089638318f0d6fa4a011743b415dd98c025b202775a9` | `screens/path-refused-320-light.png` |
| `b610138f6f8bb0c9455fc4cf576b8bdb4763cbb62c2ad9f5026255e9b5cf4117` | `screens/prompt-shown-2560-dark.png` |
| `6ea2c223293aabcaf8ac85e24dd2a9e115b39a7bd721f11f5a243bc831d9d685` | `screens/prompt-shown-2560-light.png` |
| `c3cb60646e8a2fdad0e8089441df955306ae8b4cda5b91e2133a6ddf267522e5` | `screens/prompt-shown-320-dark.png` |
| `6bc553aa632a82ea903fba829f8c5e76c58893ac15ac68144542999d688c8db2` | `screens/prompt-shown-320-light.png` |

## Review dispositions

The `experience-reviewer` pass, the separate visual-polish pass and the `test-corpus.yml` dispatch are run by the controller; their dispositions and run id are added below when they land.
