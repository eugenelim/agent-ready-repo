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
