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
