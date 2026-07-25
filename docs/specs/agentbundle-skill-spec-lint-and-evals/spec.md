---
title: "agentbundle: skill-spec deep lint + pack evals portability"
status: Shipped
type: feature
---

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->

Mode: full (multi-feature + dependent tasks + structural/public-interface change + new optional dependency)

## Objective

Move `tools/lint-skill-spec.py` into `agentbundle catalogue lint --deep` and move `tools/run-pack-evals.py` into `agentbundle pack evals run`, making both linting capabilities portable to any agentbundle adopter. Retire the standalone `tools/` scripts. Rewire CI. Fix pre-existing Windows path-separator and user-scope isolation bugs surfaced by the Windows Gate A failures.

## Scope

Files touched:
- `packages/agentbundle/agentbundle/catalogue_tooling/lint.py` — add `--deep` gate calling new module
- `packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py` — NEW: full agentskills.io spec checks
- `packages/agentbundle/agentbundle/commands/catalogue_lint.py` — pass `deep` flag
- `packages/agentbundle/agentbundle/commands/pack_evals.py` — NEW: pack evals run command
- `packages/agentbundle/agentbundle/cli.py` — add `--deep` to catalogue lint; add `pack evals run` subcommand group
- `packages/agentbundle/pyproject.toml` — add `[lint]` optional extra; bump version 0.16.2 → 0.17.0
- `packages/agentbundle/agentbundle/version.py` — bump `CLI_VERSION`
- `packages/agentbundle/agentbundle/commands/adapt.py` — fix `.as_posix()` on companion path in pending report
- `packages/agentbundle/agentbundle/scope.py` — add `AGENTBUNDLE_USER_ROOT` env var override
- `packages/agentbundle/tests/integration/test_adapt_dual_scope.py` — already fixed; verify
- `packages/agentbundle/tests/integration/test_install_adapt_chain.py` — add `_set_home` helper
- `packages/agentbundle/tests/integration/test_install_dependencies_gate.py` — add `_set_home` helper
- `packages/agentbundle/tests/integration/test_install_dual_scope.py` — add `_set_home` helper
- `packages/agentbundle/tests/integration/test_multi_pack_install.py` — add `_set_home` helper
- `packages/agentbundle/tests/integration/test_recommends_cross_scope.py` — add `_set_home` helper
- `packages/agentbundle/tests/integration/test_reconcile.py` — add `_set_home` helper
- `packages/agentbundle/tests/integration/test_shared_prefix_coexistence.py` — add `_set_home` helper
- `packages/agentbundle/tests/unit/test_catalogue_skill_spec_lint.py` — NEW: port of tools/test-lint-skill-spec.py
- `.github/workflows/docs.yml` — use `agentbundle catalogue lint --deep` in `lint-skill-spec` job
- `.github/workflows/pack-evals.yml` — use `agentbundle pack evals run`
- `tools/lint-skill-spec.py` — REMOVED
- `tools/test-lint-skill-spec.py` — REMOVED
- `tools/run-pack-evals.py` — REMOVED
- `tools/test-all.py` — remove `lint-skill-spec` test entry
- `tools/test-pack-evals-workflow.py` — update CI step assertion
- `packs/AGENTS.md` — update guidance
- `packages/agentbundle/README.md` — update PyPI docs

Not changing:
- `tools/lint-agent-artifacts.py` (different linter, different lifecycle)
- Any pack content
- `docs/contracts/adapter.toml` (no new adapter-contract changes)
- `test_kiro_user_hooks_fixture.py` (bash-not-found failure — different root cause, separate issue)

## Acceptance Criteria

- [x] `agentbundle catalogue lint --root . --deep` exits 0 on the repo's clean catalogue
- [x] `agentbundle catalogue lint --root . --deep` exits 1 when a SKILL.md violates any check ported from `tools/lint-skill-spec.py`
- [x] `agentbundle catalogue lint --root .` (no `--deep`) continues to work without PyYAML installed
- [x] `agentbundle catalogue lint --root . --deep` exits 2 with a clear message when PyYAML is not installed
- [x] `agentbundle pack evals run --pack core` runs without error (graceful exit when `claude` not on PATH)
- [x] `tools/lint-skill-spec.py` and `tools/run-pack-evals.py` removed from the repo
- [x] CI `agentskills.io spec` job uses `agentbundle catalogue lint --deep`
- [x] CI `pack-evals` workflow uses `agentbundle pack evals run`
- [x] `packs/AGENTS.md` guidance references `agentbundle catalogue lint --deep`
- [x] Windows: `adapt` pending report uses forward slashes on all platforms
- [x] Windows: `resolve_user_root` respects `AGENTBUNDLE_USER_ROOT` env var override
- [x] Windows Gate A test failures from HOME patching reduced to only the pre-existing bash-not-found failure
- [x] `agentbundle --version` shows `0.17.0`
- [x] PyPI README updated

## Testing Strategy

- Unit tests: `packages/agentbundle/tests/unit/test_catalogue_skill_spec_lint.py` — all the checks from `tools/test-lint-skill-spec.py` ported to pytest, calling the Python function (not subprocess)
- Integration test: existing `catalogue lint` integration tests pass with the new `--deep` flag
- Windows tests: Gate A windows failures from HOME patching resolved (scope.py + test helper fixes)
- Goal-based: `agentbundle catalogue lint --root . --deep` runs cleanly on the repo
- Goal-based: `agentbundle catalogue lint --root . --deep` exits 1 on a manually-broken SKILL.md

## Assumptions

1. PyYAML ≥6.0 is safe to add as an optional extra (it's already in `tools/requirements.txt`; no known conflicts).
2. `agentbundle` can have a `[lint]` optional extra without breaking zero-deps adopters who don't use `--deep`.
3. `run-pack-evals.py`'s `REPO_ROOT` path logic needs adaptation; the pack path is passed as `--pack <name>` + `--catalogue-root <root>` rather than a hardcoded `REPO_ROOT`.
4. `agentbundle pack evals run` will print a clear "claude CLI not found" message and exit non-zero if the `claude` binary is not on PATH, matching the existing behavior.
5. The `test_kiro_user_hooks_fixture.py` bash failure is a separate pre-existing issue (bash not installed on Windows CI runner); not in scope.
