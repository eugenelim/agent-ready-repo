# Verification ledger

## T1

Red runs (before the source change):

- VI-1001/VI-1002, `packs/core/tests/pack/test_intent_delivery_relations.py`: 15 failed, 10 passed. Examples:
  `assert [] == [{'basis': {'intent': 'Decomposed', 'spec': 'Discovery'}, 'intent': 'intent:alpha', ...}]` (typed form yielded no relation);
  `'provenance': [{'field': 'Discovery', 'subject': 'spec:foo', 'target': 'outcome:Bad_Slug'}]` where `delivery-reference-malformed` was expected;
  `assert [] == [{'code': 'delivery-target-missing', ...}]`;
  `assert [] == [{'code': 'delivery-relation-ambiguous', ... 'targets': ['intent:alpha', 'outcome:ghost']}]`.
- VI-1003, `packs/core/tests/skills/close-work/test_closure_typed_discovery_parent.py`, run against the HEAD resolver copy in close-work: 9 failed, 3 passed (the 3 `intent:` cases pass). Failure: `assert [] == [('target-alpha', 'Accepted', 'spec')]`; same for `target-beta` and `target-umbrella` (`'children'`).

Green runs (after the change, source synced to the three skill copies):

- `test_intent_delivery_relations.py`: 87 passed, 2.2 s. Other `test_intent_delivery_relations*.py`: confinement 21, copies 3 (VI-1004), hostile_targets 1, vi2001_vi2003 27, all passed.
- `test_closure_typed_discovery_parent.py` (new, real resolver subprocess and real graph): 12 passed. Whole `close-work/` suite: 424 passed, 25 s.
- `integration/test_intent_delivery_traceability.py`: 2 passed. `navigate-intents/test_query_contract.py`: 57 passed. `work-loop/test_lint_traceability*.py`: 124 passed, 36 s.
- `tests/roster/test_intent_delivery_relations_repository.py`: 4 passed, 11.8 s.
- `tools/test-lint-pack-test-boundary.py`: 158 cases passed.
- `make lint-ruff lint-mypy` (ruff/mypy from the pyenv 3.13 bin on PATH, `PYTHON` set to it): ruff clean, mypy no issues in 155 files.

Notes:

- `_CANONICAL_IDENTIFIER_RE` now accepts all four intent prefixes; its callers (corpus ambiguity targets are paths, the Discovery ambiguity branch) behave unchanged for existing values.
- The architecture page's copy list was stale (omitted `navigate-intents`); corrected alongside the admitted-forms sentence.
- The hostile-targets suite is unchanged; the unsafe and ambiguous cases live in the main resolver suite.

## T2

Red run (tests written first, shared check unchanged), `packs/core/tests/skills/work-loop/test_lint_graph_pointers.py -k discovery`: 18 failed, 5 passed (the clean cases). Examples: `KeyError: 'docs/specs/d-root-link/spec.md'` style misses for every failing-case diagnostic (no `discovery-*` line emitted); CLI invalid fixture `assert 0 == 1` (exit 0, `0 violation(s) in 1 selected artifact(s)`).

Corrections during the green step: `d-root-link` (a spec-relative link `docs/product/intents/...`) resolves under the spec directory, not `docs/product/intents/`, so it is clean per the lexical rule; it moved to the passing cases as `d-ok-spec-relative-link`, and `d-slash-link` (`/docs/product/intents/...`, repository-root form) covers the untyped link case. A "never opens an untyped target" test was dropped: the index walk already refuses a symlinked intent file, so it could not distinguish the two.

Green runs:

- `test_lint_graph_pointers.py`: 71 passed, 29 s (22 Discovery cases in the shared fixture plus legacy-untouched, body-only, intent/brief-not-checked, and two real-CLI tests).
- Finish-checklist pin: old `90d06f1caa06c3e151db49cc24ec9b01cd3ffb62ec6fa3dbcce097c175cd31dd` -> new `3a0e440c7820ee39662e18f63de5cec533e1a5a844fd6d6cbefadf03fed8219a` (computed with the test's own marker/window method); `_WORK_LOOP_CONTRACT_HASH` (Step 0) unchanged and passing. Full `tools/test_workspace_status.py`: 86 passed, 1.4 s.
- `tools/test_build_gate_chain.py`: 40 passed, 27 s; no edit (it and `tools/repo/build_gate_chain.py` still pin the `.claude/skills/work-loop/scripts/lint-graph-pointers.py` invocation).
- `tools/test-lint-pack-test-boundary.py`: 158 cases passed. `make lint-ruff lint-mypy`: clean. Shipped-citation grep over the changed `.apm` files: no hits.
- Real check on this worktree, `lint-graph-pointers.py --root . --base-ref origin/main`: `0 violation(s) in 2 selected artifact(s)`, exit 0.

### T2 controller correction

The plan's *Shared check* code set names any value naming a path under `product/intents/`, as a repository path or a markdown link, as `discovery-untyped`. The implementer's first version cleared a link whose text named `product/intents/` but did not resolve there lexically from the spec directory. The rule now flags any value containing `product/intents/`, plus any link resolving under `docs/product/intents/`. Fixtures `d-spec-relative-link` and `d-escaping-link` moved from passing to `discovery-untyped`. Suite: 73 passed in 33 s; `make lint-ruff lint-mypy` clean.

## T3

### VI-3001 Writers (AC-0009)

Inventory: `notes/writer-inventory.md` (3 instruction, 1 template, 0 example, generated copies listed, excluded readers with reasons). The product-engineering discovery loop does not instruct the form: excluded, pack unchanged.

Pins added to `tests/roster/test_graph_pointer_authoring.py` (already wired in `build-check.yml` and `tools/repo/build_gate_chain.py`, pinned by `tools/test_build_gate_chain.py`; no new wiring): a `DISCOVERY_MANIFEST` with roles, derivation of candidates, typed-kind and repository-path forms per writer, precedence and provenance sentences, the four admitted prefixes in the four refusal entries, the build-loop sentence, and a self-check that the bare-path predicate can fail. The existing Brief path-offer predicate now exempts sentences naming a research or notes path. The existing work-loop guide pin gained `Discovery:`. No `docs/specs/` literal is named, so `.workspace-prune-protected.toml` is untouched.
Result: `test_graph_pointer_authoring.py` 35 passed.

### VI-3002 Sweep (AC-0010, AC-0011)

Script: `notes/sweep_discovery.py` (stdlib; loads the shared check by path; `--check` dry run; `--selftest`).
- Dry run: `would rewrite 27 header value(s) in 27 spec(s); 0 refused`. Manifest `notes/sweep-manifest.md`: 27 rows (20 `intent`, 4 `opportunity`, 2 `outcome`, 1 `capability`).
- Resolver snapshot before and after (`intent_delivery_relations.py --root .`, widened resolver): relations, classifications, diagnostics, artifacts, `complete` identical; the only differences are 2 provenance `target` strings echoing the raw value (`docs/product/intents/FEAT-0033-decision-navigation.md` -> `intent:decision-navigation`, `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md` -> `capability:optional-code-intelligence-composition`). No provenance `intent` field changed.
- Byte check: all 27 files have equal line counts and differ from HEAD on exactly one line, the `- **Discovery:**` line, with the line ending unchanged. `git diff --numstat` is 1/1 for each of the 27 swept specs.
- Second run: `rewrote 0 header value(s) in 0 spec(s); 0 refused`, exit 0; `git diff -- docs/specs` byte-identical to the diff before the run; manifest not rewritten.
- Refusal fixture (`sweep_discovery.py --selftest`, temp dir): missing target, retired target, and slug-less target are each reported `REFUSED` and their files are byte-unchanged; the accepted fixture rewrote only its value (CRLF and trailing comment kept); the repeat run changed nothing. Output ends `selftest: refusals reported and unchanged; accepted value rewrote only its value (CRLF and comment kept); repeat run empty`.
- Refused real candidates: none.
- `lint-graph-pointers.py --root . --base-ref origin/main`: `0 violation(s) in 29 selected artifact(s)`, exit 0.
- `lint-spec-status.py --root .`: `spec metadata clean (29 of 572 spec(s) changed against origin/main)`, exit 0; no finding, so none is pre-existing.

### VI-3003 Guides

`tools/validate_guides.py` (0 errors, 225 checked), `tools/check-guide-index.py` (OK), `tools/lint-guide-titles.py` (231 files OK), `tools/lint-guides-no-repo-only-refs.py` (OK): all exit 0. Pytest for the same: `test_validate_guides`, `test_check_guide_index`, `test_lint_guides_no_repo_only_refs`, `test_lint_guide_titles`, `test_guide_authoring_standard`: 69 passed.

### Gates

- `make lint-ruff lint-mypy` (pyenv 3.13 on PATH, `PYTHON=python3`): ruff clean, mypy no issues in 155 files, exit 0.
- Named roster suites plus `packs/core/tests/pack/test_spec_authority_scoping.py`: 427 passed, 38.8 s. (A first run with the system `python3` on PATH failed `test_conventions_retirement` because a subprocess lacked `tomllib`; it passes with the pyenv 3.13 bin first.)
- `packs/core/tests/skills/new-spec/`: 267 passed, 79 subtests, 75.8 s. No step-5a digest pin changed.
- Shipped-citation grep on the changed `.apm` text: no hit from this change (existing hits are in `evals.json` prompts and a `x-spec` example).

## Review fixes, round 1

- **AC-0004 (adversarial).** The close-work parent test uses placeholder slugs because `AGENTS.md` forbids real identifiers in fixtures. The placeholders reproduce the registered shape of the two named targets: `Kind: outcome`, `Level: feature`, `Decomposed: <date> spec`, and the path-valued Discovery replaced by the typed form. The corpus before/after resolver comparison (VI-3002) covers the real `finding-response-receptacle` and `finding-response-scoring` specs, whose direct-delivery relations to their outcome intents the sweep left unchanged.
- **Fix 1, linear link scan (security).** Red, against the old `_LINK_TARGET_RE.findall` on a line of unclosed `[`: 20,000 characters took 0.147 s and 40,000 took 0.581 s (4x for 2x input, quadratic; about 370 s extrapolated for 1,000,000). Green: `_link_targets` splits on `](` and reads each target up to the first `)`; the regex is removed. New test `test_discovery_link_scan_is_linear_on_hostile_values` runs 1,000,000-character values (`[`, `[](`, `[](<`) and asserts under 2.0 s. `test_lint_graph_pointers.py`: all existing cases still pass.
- **Fix 2, one intent-kind tuple (quality F6).** `_INTENT_KINDS` now feeds `_PARENT_TYPED_RE` and `_INTENT_PREFIXES`. New test `test_intent_kinds_match_the_resolver_kinds` loads `intent_delivery_relations.py` by path and compares the set with `_PARENT_INTENT_KINDS`.
- **Fix 3, narrowed research exemption (quality F1).** The `path_offers` exemption now needs a Discovery passage and no `Brief:` in the sentence. Red-case test: a sentence naming `Brief:` plus "research or notes" still fails. All current writers pass.
- **Fix 4, four-kind pin (quality F2).** `discovery_form_gaps` requires all four kinds (`outcome:`, `opportunity:`, `capability:`, `intent:` not preceded by `Parent `, or the kind name in backticks) inside one passage that names `Discovery:`. Writers updated: new-spec `SKILL.md`, the spec contract reference, the spec template, and the close guide. Self-test `test_discovery_form_predicate_can_fail`: an empty text, a text without `opportunity:`, and a Discovery passage plus an unrelated `Parent intent:` paragraph all fail the pin. Red evidence: before the writers were updated the pin failed for the template (three kinds missing).
- **Fix 5, confined sweep (security).** `confined()` rejects any symlinked component under the root and any resolved path outside `docs/specs` or `docs/product/intents`, for specs and intents. Selftest case: a symlinked spec directory pointing outside the tree is skipped, the outside file stays byte-identical, and no manifest is written.
- **Fix 6, manifest first (quality F3).** The manifest is written from the full planned rewrite set before the first spec is written; with nothing to do, neither is written. Real tree: `sweep_discovery.py --root .` reports `rewrote 0 header value(s) in 0 spec(s); 0 refused`, exit 0, no manifest written; `--check` reports `would rewrite 0 ...`, exit 0. `--selftest` passes.
- **Fixes 7 to 9, prose.** Changelog Highlights rewritten in plain words (3 bullets). The close guide states the accepted `Discovery:` form once, and the four refusal entries refer to it; the roster pin now checks the single form statement for all four kinds and that each entry refers to it. The template `Discovery:` comment is split into short sentences. The shipped-citation grep on the changed `.apm` files is clean.

## Review fixes, round 2

Round-2 experience adjudication (Opus replacement; two Sonnet attempts were structurally invalid) sustained three items, applied by the controller:

- `guides/core/how-to/start-the-work.md`: the check sentence now says an intent-valued `Discovery:` is written `<kind>:<slug>` naming a live intent of that kind, and that a research or notes path is not checked.
- `new-spec/SKILL.md` and `references/spec-and-plan-contract.md`: the precedence clause now states the rule (the intent's `Kind:` line, `capability` for `Level: capability`, otherwise `intent`).
- Release Highlights bullet 2: plain-word gate names and "names no existing intent of that kind".

Gates: `make lint-ruff lint-mypy` clean; roster authoring + new-spec + spec-authority suites 324 passed (53 s); `changelog.py validate`, `validate_guides`, `check-guide-index`, `lint-guide-titles`, `lint-guides-no-repo-only-refs` exit 0. The round-2 quality nit (sweep exits 0 after skipping a symlinked spec) is deferred unchanged: the sweep is complete working material.

## Review fixes, round 3

Final round on Opus (reviewers and adjudicators on their designated model). Sustained and applied:

- Kind rule (guide and template, and aligned in the skill and contract reference): `outcome` or `opportunity` from the intent's `Kind:` line, `capability` for `Level: capability`, `intent` for every other intent. This matches `_registered_kind`.
- Highlights: the refusal is now stated as happening before the work loop completes the change. The pull-request claim was dropped, because the pack installs no PR workflow.
- `artifact-not-in-graph`: the second cause now says the resolver finds the intent but the tree does not hold it. The missing-intent cause stays only under `delivery-target-missing`.
- Link resolution: added fixtures `d-normalized-link` (`[x](../../product/./intents/outcome-a.md)`, no literal `product/intents/`, expects `discovery-untyped`) and `d-ok-scheme-link` (a scheme-prefixed target, passes). Mutation proof: stubbing `_resolves_under_intents` to return `False` turns `test_discovery_diagnostic[d-normalized-link]` red (1 failed, 27 passed); restored source passes.
- Deferred nit (security round 3): the sweep's header-line regex is quadratic on a long whitespace run. The sweep has already run and is working material; no change.

Gates: `make lint-ruff lint-mypy` clean; the check, authoring-roster, new-spec, and closure-guide suites passed 636 tests (89 s); the guide tools and `changelog.py validate` exited 0. The T4 evidence follows under `## T4` once the projections are regenerated from the committed source.

## T4

Bound to revision `aea451fc8` (committed source with projections regenerated by `make build-self`; tree clean before these runs).

- **VI-4001 release:**
  - Core is 3.1.12 in both `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`. `origin/main` is 3.1.11, so this is the next patch.
  - The release fragment is `docs/product/changelog.d/46b74154-b234-4836-ade5-02ca63e95d25.md`, with three Highlights. `tools/changelog.py validate` exits 0.
  - Two evals were added: `finish-graph-pointer-check-discovery` in work-loop and `discovery-header-typed-intent-form` in new-spec.
- **VI-4001 projection:**
  - `agentbundle catalogue self-host --root . --write` exits 0 and leaves the tree clean, so the projections already match the source.
  - After `make build` refreshed the gitignored `dist/`, `agentbundle catalogue verify --root .` reports `catalogue verify: ok` with 0 errors. A first verify run had reported CAT-V-014 against stale `dist/` output left by the earlier build-check run.
- **VI-4002 projected check:**
  - On this repository, `.claude/` and `.agents/` `skills/work-loop/scripts/lint-graph-pointers.py --root . --base-ref origin/main` each report `0 violation(s) in 29 selected artifact(s)` and exit 0.
  - On a disposable git fixture, the intent has `Kind: outcome`. Three specs were changed from `none`, with these results:
    - `outcome:svc` is clean.
    - The intents path gives `docs/specs/b/spec.md: Discovery: discovery-untyped`.
    - `intent:svc` gives `docs/specs/c/spec.md: Discovery: discovery-wrong-kind`.
    - The run ends `2 violation(s) in 3 selected artifact(s)` and exits 1.
- **VI-4002 projected resolver:**
  - `.agentbundle/bin/intent_delivery_relations.py` was run on a one-spec fixture with `Discovery: outcome:svc` naming a `Kind: outcome`, `Decomposed: 2026-10-20 spec` intent.
  - It exits 0 with a `direct-delivery` relation to `intent:svc` and no diagnostics.
  - The legacy path form yields the identical relation.
- **VI-4002 citation scan:** the `packs/AGENTS.local.md` grep was run unscoped, evals included, over the `.apm` lines this change adds (`git diff origin/main...HEAD -U0 -- 'packs/*/.apm/**'`). It finds 1 hit. The hit is the new work-loop eval prompt `finish-graph-pointer-check-discovery`, which names `docs/specs/billing-export/spec.md`. That path is an invented adopter artifact and is classed illustrative, which `packs/AGENTS.local.md` permits. No internal citation was added. Over the whole changed files, the grep also finds the pre-existing illustrative `x-spec: [docs/specs/orders/]` example in `spec-and-plan-contract.md` and older eval prompts, none of which this change added.

## Review fixes, round 4

Confirmation round on Opus. Sustained items and how each was handled:

- **Close-out guide.** The form paragraph now opens with "The accepted `Discovery:` form names ...". The legacy-path note says a spec you add or change cannot use the legacy path. The roster pin now finds the form line by its new opening.
- **`d-ok-scheme-link` fixture.** The target is now `https://example.invalid/../../../../../docs/product/./intents/a.md`. Mutation proof: removing the scheme match in `_resolves_under_intents` turns `test_discovery_passing_cases_exit_zero` red (1 failed, 27 passed). The restored source passes.
- **VI-4002 citation-scan entry.** Restated as the unscoped scan, with its one hit classified.

Gates: the check, authoring-roster, closure-guide, and cooling suites passed 369 tests in 44 s. `make lint-ruff lint-mypy` is clean, and the guide tools exit 0.

## Completion

Every acceptance criterion is met (AC-0001 to AC-0012 checked). Review rounds 1 to 5 closed with every warranted reviewer clean, directly or through adjudication: adversarial, security, quality, and experience. Two Nits were deferred unchanged, both in the one-time sweep script: the exit code after skipping a symlinked spec, and the header-line regex on very long whitespace runs. The spec is Shipped, the plan is Done, and the workspace entry moved from `queue` to `shipped`. The plan's changelog stays at its approved baseline, so this completion note lives here.
