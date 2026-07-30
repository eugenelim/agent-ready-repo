- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none

Mode: full (risk triggers: structural CLI change, multi-feature, dependent tasks, destructive/irreversible deletion)

## Objective

Fold six standalone `tools/` scripts into the `agentbundle` CLI — four into `catalogue lint` (as new `_check_*` methods) and two into `catalogue verify` (as new step functions). Delete the scripts, remove their call sites in `pre_pr_catalogue.py`, update CLI help strings, update docs, bump `agentbundle` to `0.18.0`, and cut the release.

## Boundaries

**In scope:** Moving check logic from the six scripts into `lint.py` / `verify.py`. Deleting the six scripts and their self-tests. Removing the four now-redundant invocations from `pre_pr_catalogue.py`. Updating CLI help text. Version bump and changelogs. Release tag.

**Out of scope:** Adding new checks beyond what the scripts already do. Changing existing diagnostic codes or step numbers 1–18. Adding a compatibility shim for any deleted script. Checking `.claude/skills/` for credentialed-skill violations (the per-pack `.apm/skills/` check in `_PackRules` is the source of truth; `.claude/skills/` is a build projection).

## Assumptions

1. `0.18.0` is the correct target version (current: `0.17.1`, one minor increment).
2. PyYAML is available in the test environment for `_step_agent_artifacts` (already required by the existing `lint-agent-artifacts.py` and gated by `pip install 'agentbundle[lint]'`).
3. The `_step_agent_artifacts` step checks `root / ".claude"` (source artifacts), not `tmpdir / "dist"`. The step is post-build (placed at step 11) so it runs in the same pipeline but checks the source tree, consistent with how `pre_pr_catalogue.py` runs it today.
4. `_step_plugin_manifests` reads from `tmpdir / "dist" / "claude-plugins"` (the build output populated in step 10), consistent with `DIST_DIR` in the standalone script.
5. The `lint_credentialed_skills.py` scope reduction from three patterns (`.claude/skills/`, `packs/*/.apm/skills/`, `skills/`) to one (`packs/<pack>/.apm/skills/`) is intentional: in the engine context, the pack is the unit; `.claude/skills/` is the projected output of build-self and checking the source packs is sufficient. The top-level `skills/` pattern is vestigial (no such directory exists in this repo); its removal carries no live coverage gap.
6. `_PackRules` constructor gains a `root: Path` parameter (needed for tutorial path resolution in `_check_first_value`). The calling site in `lint_catalogue()` passes `root` to each `_PackRules(pack_dir, root)` instance.
7. `test-lint-profiles.py`, `test-lint-catalogue-seeds.py`, and `test-lint-credentialed-skills.py` will be deleted since their coverage is subsumed by the new agentbundle unit tests added in Tasks 2–5. `test-lint-first-value-contract.py` is also deleted (subsumed).
8. Three existing agentbundle tests reference the deleted scripts by path and must be migrated: `test_lint_agent_artifacts_metadata_auth.py` (subprocess-invokes `tools/lint-agent-artifacts.py`), `test_credbroker_lint_hardening.py` (importlib-loads `tools/lint_credentialed_skills.py`), and `test_pre_pr_py.py` (asserts `pre_pr_catalogue.py` contains the old invocations). These are updated/rewritten in Task 8c.
9. The `LINT_APM_ROOT` env override in `lint-agent-artifacts.py` is intentionally retired with the self-test; the folded step hardcodes `root / "packs" / "core" / ".apm" / "skills"` which matches the existing default.
10. Four CI workflow files reference the deleted scripts and must be updated in Task 8c: `.github/workflows/docs.yml` (lint-agent-artifacts, lint-catalogue-seeds, lint-profiles jobs + `on: paths:` entries), `.github/workflows/build-check.yml` (test-lint-profiles.py, lint-profiles.py calls), `.github/workflows/publish-claude-plugins.yml` (validate-claude-plugin-manifests.py step), `.github/workflows/catalogue-tooling-ci-gates.yml` (pyyaml step label update).

## Acceptance Criteria

- [ ] **AC1** — `_CatalogueRules._check_profiles()` is present in `lint.py` and checks all profile invariants: invalid-scope-value, non-empty-packs-list, pack-not-found-in-catalogue, scope-homogeneity, dependency-completeness (version-range satisfaction), order-validity (dep before dependent pack), unsupported-range-grammar, profile-parse-failure. Uses `CAT_L028` diagnostics. Message strings byte-identical to the standalone script for all invariants.
- [ ] **AC2** — `_PackRules._check_seeds()` is present in `lint.py` and enforces the seeds contract (fail-loud on unknown seeds, patterns.jsonl empty, required placeholders, blocklist, sentinel handling) using `CAT_L029` diagnostics. Fires only on packs with `[pack].lint-seeds = true`. Message strings are byte-identical to the standalone script **except** the fail-loud message for unknown seeds: that message is updated to reference `lint.py (_PackRules._check_seeds)` instead of the deleted `tools/lint-catalogue-seeds.py`.
- [ ] **AC3** — `_PackRules._check_first_value()` is present in `lint.py` and enforces Level A, Level B (when `level-b = true`), `writes-to-repo` gate, and tutorial existence using `CAT_L030` diagnostics. Message strings are byte-identical to the standalone script.
- [ ] **AC4** — `_PackRules._check_credentialed_skills()` is present in `lint.py` and enforces the four broker-variant conventions (D1 security phrases, D2 argv ban, D2b deny-set, D3 dotfile AST, AC25 broker-specific) using `CAT_L031` diagnostics, scoped to `<pack>/.apm/skills/*/SKILL.md`. Message strings are byte-identical to the standalone script.
- [ ] **AC5** — `diagnostics.py` contains `CAT_L028` through `CAT_L031` with stable docstrings.
- [ ] **AC6** — `_CatalogueRules.collect()` and `_PackRules.collect()` call the new methods (profiles, seeds, first-value, credentialed-skills respectively).
- [ ] **AC7** — `_step_agent_artifacts(root, config, pack, tmpdir)` is wired at step 11 in `_VERIFY_STEPS`, replacing the `"generated output schema"` pass-through (label updated to `"agent artifact lint"`). Checks `root / ".claude"` skills/agents/commands plus APM leak guard; enforces: frontmatter presence, kebab-case `name`, name==dir/filename, unknown keys rejected, `metadata.credentialed`/`primitive-class`/`auth` broker admission, duplicate-frontmatter-key, Norway-boolean typing, stray non-SKILL.md files, empty-body, broken-link resolution. PyYAML guard: if absent, returns one `CAT-V-011` error rather than crashing. All `yaml.*` references (including `class _FrontmatterLoader`) must be inside the guarded scope — none at `verify.py` module scope. Uses `CAT-V-011` code. `LINT_APM_ROOT` override retired with the self-test.
- [ ] **AC8** — `_step_plugin_manifests(root, config, pack, tmpdir)` is wired at step 13 in `_VERIFY_STEPS`, replacing the `"marketplace pack membership/version"` pass-through (label updated to `"plugin manifest schema validation"`). Reads from `tmpdir / "dist" / "claude-plugins"`. Graceful no-op when the directory is absent (build didn't produce claude-plugins output). When present, validates each `*.claude-plugin/plugin.json` against the derived schema and validates `marketplace.json` (no `hooks` in plugin entries). Uses `CAT-V-013` code.
- [ ] **AC9** — All six scripts deleted; `tools/lint-credentialed-skills.sh` also deleted. All four invocations in `pre_pr_catalogue.py` (agent-artifact, catalogue-seeds, credentialed-skill, profiles + their self-tests) are removed. CI files updated: `.github/workflows/docs.yml` jobs + `on: paths:` trigger entries for those scripts removed; `.github/workflows/build-check.yml` lint-profiles lines + stale comment removed; `.github/workflows/publish-claude-plugins.yml` validate-claude-plugin-manifests.py step removed; `.github/workflows/catalogue-tooling-ci-gates.yml` pyyaml step label updated. Existing agentbundle tests updated: `test_lint_agent_artifacts_metadata_auth.py`, `test_credbroker_lint_hardening.py`, `test_pre_pr_py.py`, `test_reference_architecture.py`, `test_install_snapshot.py` (sync comments repointed to `lint.py`). No broken references remain — grep across `.github/**/*.yml`, `tools/**/*.py`, `packs/**/*.toml`, `docs/**/*.md`, and `packages/**/*.py` finds none of the six script filenames in live invocation context.
- [ ] **AC10** — CLI `help=` strings for `catalogue lint` and `catalogue verify` extended by one phrase each describing the new check areas.
- [ ] **AC11** — `docs/product/changelog.md` and `packages/agentbundle/CHANGELOG.md` each contain a new versioned section for `0.18.0` with the six checks listed.
- [ ] **AC12** — `python tools/catalogue/pre_pr_catalogue.py` exits 0. `python -m pytest packages/agentbundle/` exits 0. `python -m pytest tools/test_build_gate_chain.py` exits 0.
- [ ] **AC13** — `packages/agentbundle/pyproject.toml` version is `0.18.0`. `[project.urls]` matches the spec brief exactly.
- [ ] **AC14** — PR merged; tag `agentbundle-v0.18.0` applied.

## Testing Strategy

**TDD tasks (Tasks 2–5, 6–7):** For each `_check_*` method and step function, construction tests go in the existing `test_catalogue_tooling_lint.py` and `test_catalogue_tooling_verify.py` files. Stubs created before implementation. Goal: exercise the happy path (clean input → no diagnostics), one finding path per invariant (violation → correct diagnostic code and message substring), and opt-in gating (e.g., `lint-seeds = false` → no seeds check fires).

**Goal-based tasks (Tasks 8, 8a, 8b):** Verified by `grep` (no dead references), `python tools/catalogue/pre_pr_catalogue.py` (exit 0), and `python -m pytest packages/agentbundle/` (exit 0).
