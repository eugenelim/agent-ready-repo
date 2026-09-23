# Plan: agentbundle-engine-stragglers

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `packages/agentbundle/agentbundle/render.py` — AC1.
- `packages/agentbundle/agentbundle/catalogue_tooling/{lint.py,verify.py}` +
  the module the shared helper lands in — AC3, AC4.
- `packages/agentbundle/agentbundle/catalogue_tooling/{results.py,initialise.py}`
  and `commands/catalogue_init.py` — AC7.
- `packages/agentbundle/agentbundle/cli.py` — AC8.
- `tools/repo/check_release_impact.py` — AC9.
- Tests: `tests/unit/test_plugin_scope_filter.py` (AC2), new lint tests (AC5),
  new CLI help test (AC8), new release-impact test (AC10).
- `packages/agentbundle/pyproject.toml` + `agentbundle/version.py`,
  `docs/product/changelog.md` — AC11.
- `workspace.toml` — AC12.

**What demonstrates done**
- TDD: AC5's three tests red against the old probe path, green after.
- TDD: AC8's drift test and AC10's release-gate test.
- Goal-based: `inspect.signature` assertions (AC2); `make build-check` (AC6);
  Gate G (AC11).
- Manual QA: `agentbundle catalogue init --json` shows `next_steps`;
  `agentbundle list-targets --help` shows all eight targets.

**What I am NOT changing**
- No new diagnostic code (AC12's residuals stay in the backlog).
- No default for `aggregate_scope`, anywhere.
- No eager import in `cli.py`.
- No pack content — the 22 packs are already clean under the turned-on checks.

## Declined patterns

- **Tempted:** give `render_packs_to_dir` a `"catalogue"` default so the signature
  change is non-breaking. **Declined:** `run_recipe`'s docstring names this exact
  function as the reason it refuses a default — a default reintroduces the silent
  misclassification. A breaking change on a function with zero callers is cheaper
  than a silent wrong policy.
- **Tempted:** generate the `list-targets` help from the registry, as the backlog
  entry proposes. **Declined:** measured 429 ms import cost on every CLI
  invocation, against an explicit `_lazy()` design note. A drift test buys the
  same guarantee for free.
- **Tempted:** fix the two verify residuals while in `verify.py`. **Declined:**
  each needs a new diagnostic code — a contract change with its own review.
- **Tempted:** also sweep `contracts/` for other stale prefixes while editing
  `check_release_impact.py`. **Declined:** out of the named concern; the entry
  scopes to one prefix swap plus its test.
- **Tempted:** split this into four PRs for reviewability. **Declined:** three of
  the four are release-impacting, so splitting means three version bumps for four
  small fixes; the operator asked for related groups.

## Tasks

### T1 — AC1/AC2: `render_packs_to_dir` aggregate scope
- **Mode:** goal-based. `Done when:` `inspect.signature` shows the parameter
  keyword-only with no default, and the extended tuple test passes.
- **Tests:** extend `test_aggregate_scope_is_required_with_no_default`.

### T2 — AC3/AC4/AC5: lint manifest path
- **Mode:** TDD. Write three failing tests (one per code) against a fixture pack
  with a real `.claude-plugin/plugin.json`; confirm red; lift the helper; confirm
  green.
- **Tests:** extended `tests/unit/test_catalogue_tooling_lint.py` rather than a new
  file — its `_add_pack` helper was itself writing the manifest to the pack root
  (fixture and probe agreeing with each other and with no real pack), so the fix
  belonged in that file, next to the CAT-L007/L009 tests it un-blinds.

### T3 — AC7: `InitResult.next_steps`
- **Mode:** TDD + manual QA. Mirror `_build_next_steps`'s shape from the
  self-hosted sibling.
- **Tests:** extend `tests/unit/test_catalogue_tooling_init.py` JSON assertions.

### T4 — AC8: `list-targets` help + drift test
- **Mode:** TDD. Test asserts the help string names exactly `list_adapters()`.
- **Tests:** new CLI help test.

### T5 — AC9/AC10: release-impact prefix
- **Mode:** TDD. Test the `contracts/`-only changeset both ways.
- **Tests:** extend `test_check_release_impact` (or new).

### T6 — AC11/AC12: release + backlog disposition
- **Mode:** goal-based. `Done when:` Gate G passes and `[backlog].open` reflects
  the dispositions.
- **Tests:** no stub (goal-based).

## Anchor-test sweep

Ran before EXECUTE. Contract-anchor tests that pin content this change edits:
- `tests/unit/test_plugin_scope_filter.py:106` — `inspect.signature` assertion on
  the `aggregate_scope` tuple. **Must be updated** (T1 does this).
- `test_contract_files_byte_identical` — pins `contracts/adapter.toml` against the
  packaged twin. Not touched by this change (AC9 edits the gate's prefix list, not
  the contract file).
- Version/changelog pins under Gate G — T6 handles.

## Verification log

- **AC1/AC2** `pytest tests/unit/test_plugin_scope_filter.py` green with
  `render_packs_to_dir` added to the keyword-only/no-default tuple.
- **AC3/AC5** TDD red proven first: pointing the fixture at
  `.claude-plugin/plugin.json` failed `test_cat_l007_unparse_plugin_json` and
  `test_cat_l009_name_version_mismatch` against the unfixed probe — the dormancy
  proof. Green after the path fix. CAT-L008 test added (it had none). A fourth test
  pins that lint does NOT read a root-level manifest (that case is verify's CAT-V-004).
- **AC4** `grep -rn '"plugin.json"' catalogue_tooling/*.py` -> one hit, in manifest.py.
- **AC6** dry run before implementing: 0 findings across 22 packs. Confirmed after by
  `make build-check` exit 0.
- **AC7** manual QA: `agentbundle catalogue init /tmp/qa-init --format json` ->
  `next_steps` present with all three entries.
- **AC8** manual QA: `agentbundle --help` shows all eight adapters. Drift test proven
  non-tautological — the old string leaves 5 adapters missing, so the test fails on it.
- **AC9/AC10** `pytest tools/test_check_release_impact.py` 7 passed. Wiring caught by
  `lint-ci-parity` (exit 1, "not reachable from make ci") until added to BOTH
  build-check.yml and the Makefile — the gate working as designed.
- **AC11** 0.35.3 -> 0.36.0 in pyproject + version.py; both changelogs updated.
- **AC12** three entries removed; `lint-plugin-json-probes-wrong-path` narrowed to its
  two verify residuals and renamed `verify-parity-silent-skip-codes`.
- **GATES** `make lint-ruff` exit 0; full agentbundle suite green; `make build-check`
  exit 0 WITH SAST ("every leg of this target was invoked").
- **Doc drift** `lint-spec-status` initially failed hard on a `(deferred:)` anchor
  pointing at a removed entry; three sibling specs updated to record the resolution.
- **REVIEW** `adversarial-reviewer` = named skip (session instruction prohibits
  subagent dispatch unless requested). Self-reviewed against the spec-less checklist.
