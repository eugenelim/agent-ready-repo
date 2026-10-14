# Verification ledger: intent dependency graphs

Execution observations for [`spec.md`](../spec.md) and [`plan.md`](../plan.md). Each entry names the commit it ran against.

## T1: dependency query and text

### Real-input corpus (VI-1003)

Characterized before the refusal fixtures were finalized, at base commit `93c1054755fa`.

| Intent file | SHA-256 | `Depends on:` value | Form | Result |
| --- | --- | --- | --- | --- |
| `docs/product/intents/FEAT-0007-work-item-promotion-routing.md` | `1f5bd12821fb…` | `docs/product/intents/FEAT-0006-work-item-capture-contract.md` | `path` | edge |
| `docs/product/intents/FEAT-0008-governance-item-record-routing.md` | `87f4795f5ea9…` | `docs/product/intents/FEAT-0007-work-item-promotion-routing.md` | `path` | edge |
| `docs/product/intents/FEAT-0009-duplicate-coverage-check.md` | `5c84b4e5dc41…` | `docs/product/intents/FEAT-0007-work-item-promotion-routing.md` | `path` | edge |

Three headers, all legacy paths with a trailing preamble comment: 3 accepted, 0 refused. No typed value is in use yet, so the path rule is what makes today's dependencies visible.

### Red and green

- Red: with `dependencies` removed from the operation set, `test_dependencies.py` gave 31 failed, 9 passed (the 9 are the refusal and compatibility cases that hold either way).
- Seeded defects, each reverted: dropping the self-loop rule failed 1 test; dropping the empty/`.`/`..` segment check failed 1 test.
- Green: `test_dependencies.py` 40 passed in 4.2 s. The navigator and `close-work` suites: 899 passed, 4 skipped (by-design whole-operation-failure corpora) in 26 s. `make lint-ruff lint-mypy` clean.
- Dispatch: T1 was built by the controller in-session; the owner directed on 2026-10-14 that it be recorded `human-directed`. T2 to T6 go to the `implementer` subagent.

## T2: the view payload carries dependencies

- Implemented by the `implementer` subagent. The payload gains `dependencies` after `source_links`; a `--from` export carries the linked set's records.
- Golden for the unchanged members: the pre-change navigator from `93c105475` was loaded by path from a scratch directory outside the repository and run over copies of `mixed` and `dependency`; each member's SHA-256 over canonical JSON (excluding `provenance.generated_at`) is inlined in `test_export_payload.py`.
- Gates: navigator and `close-work` suites 907 passed, 4 skipped (by design) in 26 s; `make lint-ruff lint-mypy` clean.

## T3: the Dependencies part, broken entries, record groups and Key

- Implemented by the `implementer` subagent. Browser suite 115 passed, 0 skipped in 39 s (91 inherited checks, some amended as the spec states, plus 24 new). Collected suites 907 passed, 4 skipped (by design) in 26 s.
- Design calls inside the spec's latitude: the sort-key line shows only when edge lines exist; an `outside_scope` entry also names its source intent; a self-dependency's "What is broken" entry reads "It names itself."; changing "Show" or "Steps" refills only the part's result, so the control keeps focus; "Show"/"Steps" persist across picks.

## T4: keyboard, width, theme and inert content

- Implemented by the `implementer` subagent; no layout or script change was needed. Browser suite 125 passed, 0 skipped (adds the keyboard path, the 8-cell width and theme matrix over `intent:india` with Both and All, and the hostile-inertness walk). Collected suites include the new CSP/banned-API and symlinked-intent refusal tests.

## T6: docs, skill, evals, release and coordination

Implemented by the `implementer` subagent at base `814962997`, uncommitted in the worktree for the controller.

### Activation (AC-0014)

- Eight cases appended to `packs/core/.apm/skills/navigate-intents/evals/eval_queries.json` (indexes 47 to 54): positives q47 "Which intents does FEAT-0008 depend on?", q48 "What depends on this intent?", q49 "Show the dependency graph for this capability's intents", q50 "Trace prerequisites for intent:x"; near-misses q51 "Block starting work on an intent until its prerequisites have shipped", q52 "Reorder the work queue so dependencies come first", q53 "Migrate the needs in our workspace queue into Depends on headers on the intents", q54 "Edit the Depends on header of this intent to add a prerequisite". The file holds 55 queries (32 positive, 23 negative). The `description` is unchanged (1,012 characters of the 1,024 limit).
- Procedure as the export ledger's "Activation (AC-0067)" entry: three fresh tool-less processes per query in an empty directory, `claude -p --safe-mode --disable-slash-commands --tools ""` (Claude Code 2.1.296), prompt on stdin, one call at a time (up to two retries, none needed). Prompt set: a fixed head (22 skill descriptions: every `core` skill plus `navigate-decisions`; SHA-256 `65cc9c6db5f052f8aff7ade92952e5a97d5ca2f950ad5deb43ff6f15c5c64ef9`) asking for one line naming the single skill or `none`, then the query between `<<<BEGIN REQUEST>>>` and `<<<END REQUEST>>>` markers. Fidelity is `reported`: a description-match judgement, not the real router. Scripts and the reports file stayed outside the repository (`/tmp/t6act`).
- Reported skills, 3 runs each: q47 to q50 `navigate-intents` x3; q51 `work-loop` x3; q52 `workspace-status` x3; q53 `work-loop` x3; q54 `none` x3. 0 errored runs. Codex was not run.
- Graded with `agentbundle pack evals run --pack core --mode in-harness --reports <file>` over a reports file holding only q47 to q54: q47 to q50 `[ok ] should_trigger=True trigger_rate=1.00`; q51 to q54 `[ok ] should_trigger=False trigger_rate=0.00` (q51 and q53 also fired `work-loop`, q52 `workspace-status`). The other 47 queries were not re-run (the description is unchanged); only these eight lines are evidence.
- Result: pass.

### Docs (AC-0015)

- `SKILL.md`: a Dependencies use case, a "Dependency enforcement, ordering, migration, or editing" not-to-use item, the `dependencies` command and its options, defaults, depth, header-only scope, typed and legacy-path acceptance, diagnostics and the `result_too_large` route; the view's Dependencies part; the scoped-export sentence. `guides/core/how-to/navigate-intents.md`: a `dependencies` section (command run over the `dependency` fixture, output pasted), the Dependencies part, and the two `--from` lines corrected (flag table and "With `--from`") to say a scoped export carries the dependency records of intents linked to the subtree and names those outside it by id. `packs/core/DESIGN.md` § Intent-edge derivation: the re-read through the same confined helpers, display only, not the enforcing reader.
- `validate_guides.py`: OK (0 errors, 237 checked). `lint-guide-titles.py`: OK (243 files). `lint-guides-no-repo-only-refs.py`: OK.
- Citation grep from `packs/AGENTS.local.md`: the whole tree has existing hits (illustrative and test fixtures); none of the added non-test lines under `packs/` matches an RFC/ADR/AC id or a `docs/specs` path.

### Release (VI-6003)

- Core moved to 3.1.5 in `pack.toml` and `plugin.json`. The build first took 3.1.4 while `origin/main` had 3.1.3; another change released 3.1.4 on `origin/main` (`3216c5b40`) before this one merged, so after rebasing on it this release is 3.1.5, the next unused patch. Fragment `docs/product/changelog.d/114902db-a122-49cd-a972-7097dbe73bbf.md` (from `tools/changelog.py new`, version and anchor moved to 3.1.5; two Highlights bullets and a Changed section); `tools/changelog.py validate` exits 0.
- `FORCE=1 make build-self` wrote the `.agents/` and `.claude/` navigate-intents projections (SKILL.md, eval_queries.json, navigate_intents.py, view.css, view.js). A second `FORCE=1 make build-self` left `git status --short` and `git diff` byte-identical to the first. (A run without `FORCE` refuses on the dirty tree, which is the check's purpose.)
- `agentbundle catalogue verify --root .`: ok.
- Installed navigator: `.claude/skills/navigate-intents/scripts/navigate_intents.py` and the `.agents/` copy are byte-identical to the source. Over the `dependency` fixture, `query --operation dependencies --id intent:alpha --direction both --depth 2 --format text` and the JSON query for `intent:bravo` (dependents, depth 3, `generated_at` and `root` removed) give identical SHA-256 from the installed and source copies; `export --from intent:alpha` payloads are equal apart from `generated_at` (5 dependency edges, 1 diagnostic).

### Gates

- `make lint-ruff lint-mypy` clean; `packs/core/tests/skills/navigate-intents/` 497 passed, 4 skipped (by design); `packs/core/tests/pack/` plus the roster version-parity, ledger-contract, cognitive-load, delivery-relations and skill-census suites 471 passed; `tools/test_changelog.py` and `tools/test-run-pack-evals.py` 72 passed.

## T5: scale, real export and screenshots (VI-5001, VI-5002)

Implemented by the `implementer` subagent at `eaa20e66d`, uncommitted in the worktree for the controller. `view_bench.py` needed no change. The experience review (VI-5003) and the final-commit browser record (VI-5004) are the controller's.

### Scale (AC-0025)

- Command: `uv run --no-project -q --with playwright --with pytest --with pyyaml python packs/core/tests/skills/navigate-intents/view_bench.py --source . --counts 1 10 25 50` at `eaa20e66d8c9c53e24f2a56b259a6cca08c05a64`. Chromium headless, macOS. Corpora are N renumbered copies of this repository's records.
- Asset digests under `packs/core/.apm/skills/navigate-intents/scripts/view_assets/`:
  - `view.js` `bdab0fb3b2b36a3bfd705a3b77767fee49c2e6407f77201e202952510dea7483`
  - `view.css` `02ea78557e0ebde16fb4e90f2b5e7e0e8596cdc95e0f7052c557c46ba9c86dd2`
  - `view-base.css` `52c618bea9b58edc484f5dde5945b3ccf1b75343b22f67f0e99fc93b1cb596c1`
- Thresholds unchanged: file at most 104,857,600 bytes, startup at most 3,000 ms (median of 3 cold loads), search at most 300 ms (median of 5), heap at most 1,024 MiB.

| Copies | `outstanding` available | Default rows | File bytes | Startup ms | Search ms | Heap MiB | Meets every threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | yes | 31 | 676,099 | 10 | 10 | 5 | yes |
| 10 | no (`resource_limit`, limit `files`) | 0 | 5,015,736 | 32 | 38 | 11 | yes |
| 25 | no (`resource_limit`, limit `files`) | 0 | 12,414,836 | 74 | 46 | 28 | yes |
| 50 | no (`resource_limit`, limit `files`) | 0 | 24,746,665 | 102 | 50 | 47 | yes |

- Result: pass at every size. The default list is empty from 10 times up for the same reason as the earlier scale entry (`outstanding` unavailable at the file limit).

### Real export (AC-0026)

- Command: `uv run --no-project -q --with playwright --with pyyaml python /tmp/s8/real_check.py <repo root> <screens dir>` (script outside the repository, not committed), at `eaa20e66d`. It ran `python packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py export --root . --destination /tmp/s8 --name real.html`: exit 0, `status: ok`, `/private/tmp/s8/real.html`, 656,573 bytes, outside the repository.
- Holders of `Depends on:` found from the payload's `dependencies` (edge sources and diagnostic sources): `opportunity:duplicate-coverage-check`, `opportunity:governance-item-record-routing`, `opportunity:work-item-promotion-routing`. The payload has 3 edges and 0 diagnostics. Live intents: 169.
- For each, the export was opened from `file://` at 1280 by 900, the intent picked with Show = Both (`#dep-dir` read back `both`) and Steps = All (`#dep-steps` read back `all`), and the part's waiting/prerequisite pairs, intent set (line ends plus the start) and diagnostic count compared with `query --operation dependencies --id <id> --direction both --depth 169`:

| Intent | Page lines | Query edges | Intents page / query | Diagnostics page / query | Result |
| --- | --- | --- | --- | --- | --- |
| `opportunity:duplicate-coverage-check` | 2 | 2 | 3 / 3 | 0 / 0 | match |
| `opportunity:governance-item-record-routing` | 2 | 2 | 3 / 3 | 0 / 0 | match |
| `opportunity:work-item-promotion-routing` | 3 | 3 | 4 / 4 | 0 / 0 | match |

- Result: pass, all three match as sorted pair sets. The query's order was not compared; the page's order is covered by the browser suite.

### Screenshots

- Retaken at `7e4a76c38`, after the experience-review and polish fixes (one ruled unit per line with the state under each name; line hairlines in the shared rule colour; every end keeps a 3px gutter, shown in the accent colour on the picked intent, whose link also carries `aria-current`). Same script and procedure as above: `opportunity:work-item-promotion-routing` (3 lines) picked with Both and All, a fresh context per width (height 900) and theme, the Dependencies part scrolled into view. The real-export comparison was re-run with the fix and all three holders still match.

| Width | Theme | File | SHA-256 |
| --- | --- | --- | --- |
| 320 | light | `screens/320-light.png` | `098dbdcb96bd00462a3f7c3344adc4586d00143cadf7090d26768490daa34ef0` |
| 320 | dark | `screens/320-dark.png` | `e51a296b6653dc0518aeac9f7337d9678d076e3560329de7497d7570acc443f3` |
| 1280 | light | `screens/1280-light.png` | `f7e8da4944292b3dfd20d32c1190ed0c07d6a43851df553cdac72d1a8e50017e` |
| 1280 | dark | `screens/1280-dark.png` | `ee18bf609228592f4eaa7f5e7881f68756eecf60c5ee3107a7e70268355097c7` |
| 1680 | light | `screens/1680-light.png` | `8ff3b3908f4b34b0da338353d65a1ae9af78df97afb79c8eb6af6e16bc8dd3ad` |
| 1680 | dark | `screens/1680-dark.png` | `047e1d88be28215956a619fabde2bb687b261b16d606f521611b1609c9f8cf36` |
| 2560 | light | `screens/2560-light.png` | `f4f86c4ccc4071e7744923e59b0d3626cab7a9eb06b94f967aacaae56ea07e10` |
| 2560 | dark | `screens/2560-dark.png` | `f2ebab14fa130a2aa34eb49f5a051d7af043767563dd1465573cb2ee1ba951a4` |

(Paths are under `docs/specs/intent-dependency-graphs/notes/screens/`. Each PNG is the stated width by 900.)

- At 320 the detail replaces the list. Each dependency is one ruled unit of two rows: the waiting intent's link with its state, then an indented row holding "waits for" and the prerequisite's link with its state. A hairline divides one line from the next. The picked intent's end carries the accent 3px left rule a selected row uses, wherever it appears, so the two lines that wait for it and the one it waits for read apart without comparing names.
- At 1280 and 1680 the part sits in the right-hand detail zone after "Where it sits" and before "Open the file", with the same two-row unit.
- At 2560 the part is wide enough that each line lays out in aligned tracks: the waiting end on the left, "waits for" with the prerequisite end on the right. Dark files match light in layout. Nothing is clipped or scrolled sideways at any width.

### Experience review (AC-0027, VI-5003)

- Round 1 (screens at `eaa20e66d`): SHIP WITH CHANGES. Adjudication sustained one Major (a dependency line did not hold together as one unit across widths) and one Minor (the picked intent was not marked); it refuted seven findings that contradicted AC-0018, AC-0024, AC-0026 or AC-0009, or stated a preference. Fixed in `7013131ae`'s parent fix commit.
- Round 2: SHIP WITH CHANGES. One Major (the new hairline and picked-end rule had no colour role, so they drew in text colour) and three Minors (state placement, gutter alignment, picked end not exposed to assistive tech), all repaired in `7013131ae`: `.dep-line` takes the shared rule colour, every end keeps a 3px gutter coloured only on the picked intent, the state sits under each name, and the picked link carries `aria-current="true"`.
- Round 3 (screens at `7013131ae`): no Blocker, no Major. Deferred, not acted on: Minor — the Key does not explain the picked end's accent bar (`view.js` Key rows; a Key row or an accent background would add it); Nit — the picked intent's link reopens the shown intent (AC-0018 requires the link); Nit — a one-line name sits a few px further above its mark because of the 24 px target floor.
- Result: AC-0027 met.

### Final-commit browser record (VI-5004)

- Last code-bearing commit: `7013131ae`. Asset SHA-256: `view.js` `266f8f4330774ea06ec52d90eead065f90bc5ecb9d985e55a90bb7cdcf0d1227`; `view.css` `13ce089e60f32f0d2716bac0b0d054e6fcbeb65b61f509f7fe07187e6fe24283`; `view-base.css` `169980e3c1d48d43ca118dba6e2fc0860bb71c91b4ce45c8b5344ddb6d7fc0ff`.
- `view_browser_checks.py`: 125 passed, 0 skipped in 41 s. `test_export_html.py`: 9 passed, 0 skipped. The contrast checks (AC-0010) cover the part's muted lead and sort lines in both themes.
- Scale re-check at `7013131ae` after the layout fix: 1 copy 677,752 bytes, startup 10 ms, search 15 ms, heap 5 MiB; 50 copies 24,748,318 bytes, startup 111 ms, search 49 ms, heap 50 MiB; every threshold met.

## Code review round 1 repairs

- Rebased on `origin/main` at `3216c5b40`, which had released Core 3.1.4; this release moved to 3.1.5 (§ Release above).
- Deviation from T3/T4 `Touches`: the second experience-review fix added four border-colour rules to `view_assets/view-base.css` (`.dep-line` joins `.part` and `.key-list .fact` on `--c-rule`; `.dep-waiting, .dep-prereq` on `--c-bg`; `.dep-self` on `--c-accent`). The plan forbids colour in `view.css`, and the base file's own rule is that a layout file sets a border's width and style while its colour is chosen there; `tools/check_view_base_parity.py` passes (one copy).
- VI-1001 cases added to the dependency fixture and its hand-written manifest: an empty segment, a `..` segment, a leading `/`, a URL scheme, `featre:a/b`, a `docs/specs/` path, a typed value with a malformed slug, a tombstone with no reissue (`quebec-old`), and `intent:ghost` written twice by `india` (one diagnostic). New tests: removing or tombstoning an intent between the two reads refuses with `unsafe_input`; live brief and spec targets, typed and path, are `outside_scope`; JSON and text byte limits admit at exactly the observed size and refuse one byte under it. Dropping the empty-segment guard now fails 1 test. `test_dependencies.py`: 43 passed.
- The skill's `outside_scope` sentence now names typed `brief:`/`spec:` values and brief/spec paths only, and says other non-intent values such as ADR references are unparseable. The guide counts `export` as the eighth command.

### Visual polish review

- Asked for after the contract-fit passes: a finish review over the real-export set and a fixture-state set, taken at `7e4a76c38` with the throwaway `/tmp/s8/polish.py` (outside the repository) from an export of the dependency fixture: `golf-faults` (`intent:golf`, Both, 1 step: 2 lines and 19 problem rows), `india-cycle` (`intent:india`, Both, All: a 3-intent cycle and two faults), `rootb-empty` (`capability:root-b`, empty state, keyboard focus on "Steps"), at 320 and 2560 CSS px in light and dark, height 1100.
- Pass 1: no Blocker; Majors — problem rows had no shared columns at wide widths, and narrow problem rows broke unpredictably with values split mid-token; Minors — no break between lines and problems, a large gap before "waits for" for short names, a double hairline at the part's end, two left edges, an uneven name-to-mark gap, cycle members running together; Nits — a one-word orphan in the lead, and the "What is broken" part's different fault layout. All but the last were repaired: a subgrid for problem rows when the part is at least 40rem wide (tracks: mark, state, source 12–16rem, value at least 12rem, note; the columns apply from a 51rem part width, where those tracks fit), one stacked status / source / value / note anatomy with a break opportunity after `/`, `\` and `:` when narrow, a rule and gap above the problem list, shared fit-content | auto | 1fr tracks for lines, the gutter hung into the panel padding by a relative offset (so it never narrows the name's track), a fixed link line height, wider gaps between cycle members, and `text-wrap: pretty` on the lead.
- Pass 2: no Blocker, no Major. Repaired: a waiting name that wrapped because the hung gutter shrank its track; problem rows with no status reading as part of the row above (every problem row is now ruled off); the note column drifting from short values. Deferred, not acted on: a long value can still break at a hyphen inside a file name (`FEAT-0001-` / `alpha.md`), and the "What is broken" part keeps its own fault layout.

| State screenshot | SHA-256 |
| --- | --- |
| `screens/states/golf-faults-320-light.png` | `6592762d2cce61fc10089a36b5cb1a5b4e6a96c858398d7bef3b6c4461cd469d` |
| `screens/states/golf-faults-320-dark.png` | `dc0f8760da3557d09135c1335865c0c0f09006eb0971556f1bde31c7bce96c71` |
| `screens/states/golf-faults-2560-light.png` | `3b592cc4a72f751e50238978a5ed396a32f9685331cd7022f8dccb97748190f0` |
| `screens/states/golf-faults-2560-dark.png` | `712a03e4bb06d531d4263acf527cd665d5b0ca579c8374c4da2cc9f87ad75235` |
| `screens/states/india-cycle-320-light.png` | `35fab182b6f716e8da3985061e27cc30e2514280caf67710e9846537586ae260` |
| `screens/states/india-cycle-320-dark.png` | `1152e5b2ae27c23232d331b455074b20a9939459ae6af1348ab4e568db14cf47` |
| `screens/states/india-cycle-2560-light.png` | `276365252f38ec7854512244b01bdcc60f9cca35191a61d88c08febab100065b` |
| `screens/states/india-cycle-2560-dark.png` | `a5c8ec7b5a656b0a463f9a841d723d2ec2bef02b7e9edabcde000df348bbe926` |
| `screens/states/rootb-empty-320-light.png` | `94bce2536912871144c03f2cfcebaa62a27472d0e0dc8e1ec74ef2106422987b` |
| `screens/states/rootb-empty-320-dark.png` | `dea2a0bb6af16093ebf637a869a8e714c28313585f6fa4a142a7070a7bbfc433` |
| `screens/states/rootb-empty-2560-light.png` | `bcacdd576dcedcc976390292a7c55e08121e6796f3d446b3b6fbde21e4ef69a9` |
| `screens/states/rootb-empty-2560-dark.png` | `2da71f600079a9e635b5e807429938235d49538c1cf0fb4d663040b639f350a3` |
- Code review round 2 found that a long source title squeezed the wide value column to 0 px (one character per line, the detail scrolling sideways). The tracks above fix it: the source wraps inside its 16rem cap and the value keeps at least 12rem. New browser check `test_vi_4001_long_source_titles_keep_values_readable` retitles two sources with a 63-character title and asserts, at 320, 1280, 1680 and 2560, no sideways scroll of the page or the detail zone and no value taller than three lines; it failed at 2560 before the fix.
- Code review round 3 found the round-2 fix moved the squeeze into the source column at part widths just above 40rem (33 px for the source; its state mark ran 18 px into the value). The problem grid now has its own 51rem container query and a 12–16rem source track. The long-title check now runs over `dependency_long` and the plain `dependency` export at 320, 1280, 1680, 2000, 2080, 2160, 2240 and 2560 CSS px, and also asserts that no child of a source cell extends past it or into the value beside it and that a source stays within six lines; with the round-2 tracks it fails 4 of its 16 cases.
