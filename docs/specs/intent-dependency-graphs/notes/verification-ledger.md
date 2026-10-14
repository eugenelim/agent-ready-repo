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

- `origin/main` has Core 3.1.3 in `pack.toml` and `plugin.json`; both moved to 3.1.4. Fragment `docs/product/changelog.d/114902db-a122-49cd-a972-7097dbe73bbf.md` (from `tools/changelog.py new`; two Highlights bullets and a Changed section); `tools/changelog.py validate` run.
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

- Retaken at `7013131ae`, after the two experience-review fixes (one ruled unit per line with the state under each name; line hairlines in the shared rule colour; every end keeps a 3px gutter, shown in the accent colour on the picked intent, whose link also carries `aria-current`). Same script and procedure as above: `opportunity:work-item-promotion-routing` (3 lines) picked with Both and All, a fresh context per width (height 900) and theme, the Dependencies part scrolled into view. The real-export comparison was re-run with the fix and all three holders still match.

| Width | Theme | File | SHA-256 |
| --- | --- | --- | --- |
| 320 | light | `screens/320-light.png` | `4dd5a3790547f800a8238c7cba2b357f2d9b2e71f84413fa1af89f1de6d95275` |
| 320 | dark | `screens/320-dark.png` | `b413a1b7a33b01f91f987e5a611a4619a555e7a14406b4d078f624eb96758616` |
| 1280 | light | `screens/1280-light.png` | `0ef7d593f90699fe0ead9435666a173b81289e4497926dcacecc40d2426216c5` |
| 1280 | dark | `screens/1280-dark.png` | `9b6dac91f7f4f441d357e93ad2bca99904ed3bccd0a648d463c965a821995a90` |
| 1680 | light | `screens/1680-light.png` | `eb4c76220bc7c1724e581467c13ad3c47035d214ec2fa8db2a6e17f3f1bf6462` |
| 1680 | dark | `screens/1680-dark.png` | `d034b5fe9598b18b026f8ab2044ad4810768debc9c6ae1e1c9b74ebb4a1fc81c` |
| 2560 | light | `screens/2560-light.png` | `f02541cf1f53fe4bb0f61e2acf578b6ccd728b2d6ecbf27b461e74aca2e7b92f` |
| 2560 | dark | `screens/2560-dark.png` | `b13ed815905bc0c96d7b61e43f107e2cf176062e3d391f42fedaa7dc74cb747e` |

(Paths are under `docs/specs/intent-dependency-graphs/notes/screens/`. Each PNG is the stated width by 900.)

- At 320 the detail replaces the list. Each dependency is one ruled unit of two rows: the waiting intent's link with its state, then an indented row holding "waits for" and the prerequisite's link with its state. A hairline divides one line from the next. The picked intent's end carries the accent 3px left rule a selected row uses, wherever it appears, so the two lines that wait for it and the one it waits for read apart without comparing names.
- At 1280 and 1680 the part sits in the right-hand detail zone after "Where it sits" and before "Open the file", with the same two-row unit.
- At 2560 the part is wide enough that each line lays out in aligned tracks: the waiting end on the left, "waits for" with the prerequisite end on the right. Dark files match light in layout. Nothing is clipped or scrolled sideways at any width.
