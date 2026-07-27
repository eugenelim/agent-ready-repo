# Plan: fold-standalone-linters-into-cli

## Task 0 — Rebase against main (done)
**Depends on:** none
**Verification:** Goal-based — `git status` clean; branch current with `origin/main`; version confirmed `0.17.1` → target `0.18.0`.

Done.

## Task 1 — Design reading pass (done during PLAN)
**Depends on:** none
**Verification:** Goal-based — notes below serve as the record.

Notes:
- `lint-profiles.py`: scope-homogeneity, dep-completeness, order-validity on `profiles/*.toml`; caret-minor satisfaction logic; pure stdlib.
- `lint-catalogue-seeds.py`: opt-in (`[pack].lint-seeds = true`), blocklist scan with sentinel exemption, required-placeholder positive check, patterns.jsonl must-be-empty special case; per-pack.
- `lint-first-value-contract.py`: Level A fields (audience-posture, surfaces, prerequisites, verification, recovery), Level B fields (when `level-b = true`), `writes-to-repo` gate, tutorial existence; per-pack with `root` for tutorial resolution.
- `lint_credentialed_skills.py`: broker-agnostic D1 (security phrases), D2 (argv ban for credentialed-cli), D2b (deny-set completeness + scrubbing backstop), D3 (dotfile AST walk); broker-specific: `creds` (resolver import), `env` (namespace+keys+reads), `sso-cookie` (broker path or credbroker), `cli` (no positive enforcement). Scans `packs/*/.apm/skills/*/SKILL.md`.
- `lint-agent-artifacts.py`: skill/agent/command frontmatter (PyYAML), broken-link check, APM leak guard (`packs/core/.apm/skills/`). Reads `root / ".claude"`.
- `validate-claude-plugin-manifests.py`: validates `dist/claude-plugins/*.claude-plugin/plugin.json` and `marketplace.json` using `agentbundle.build.validate.validate` + `_read_bundled`. Reads `tmpdir / "dist" / "claude-plugins"`.

## Task 2 — `_CatalogueRules._check_profiles()`
**Depends on:** Task 1
**Verification:** TDD — construction tests in `test_catalogue_tooling_lint.py`

Tests:
- `test_check_profiles_no_profiles_dir` — no `profiles/` dir → empty list
- `test_check_profiles_invalid_scope_value` — profile has `scope = "cluster"` (not in allowed set) → CAT_L028, `"invalid scope"`
- `test_check_profiles_empty_packs_list` — profile with `packs = []` → CAT_L028, `"non-empty packs list"`
- `test_check_profiles_pack_not_found` — profile references pack name absent from catalogue → CAT_L028, `"not found in catalogue"`
- `test_check_profiles_scope_homogeneity_violation` — profile `scope="user"`, pack only allows `repo` → CAT_L028, message contains `"does not allow scope"`
- `test_check_profiles_dependency_incomplete` — pack requires dep not in profile → CAT_L028, `"dependency-incomplete"`
- `test_check_profiles_order_invalid` — dep listed after the pack that needs it → CAT_L028, `"mis-ordered"`
- `test_check_profiles_unsupported_range_grammar` — pack declares a dep version like `"~=1.0"` (not `^major.minor`) → CAT_L028, `"unsupported range grammar"`
- `test_check_profiles_parse_failure` — malformed TOML profile → CAT_L028, `"failed to parse"`
- `test_check_profiles_clean` — valid profile → empty list

Approach:
- Add helper functions `_profile_allowed_scopes`, `_profile_required_deps`, `_profile_satisfies`, `_load_packs_for_profiles` at module level (prefixed to avoid name collision with existing helpers)
- Add `_check_profiles(self) -> list[Diagnostic]` to `_CatalogueRules`
- Call it from `_CatalogueRules.collect()`
- Use `_diag(DiagnosticCode.CAT_L028, Severity.ERROR, message)` for all findings
- Add `CAT_L028 = "CAT-L028"` to `DiagnosticCode` in `diagnostics.py`

## Task 3 — `_PackRules._check_seeds()`
**Depends on:** Task 1
**Verification:** TDD

Tests:
- `test_check_seeds_opt_out` — `lint-seeds` absent → empty list
- `test_check_seeds_unknown_seed` — seed not in REQUIRED_PLACEHOLDERS → CAT_L029 fail-loud
- `test_check_seeds_blocklist_hit` — seed contains `"agent-ready-repo"` → CAT_L029
- `test_check_seeds_missing_placeholder` — seed missing required token → CAT_L029
- `test_check_seeds_sentinel_exemption` — seed line has sentinel above → no violation
- `test_check_seeds_stacked_sentinel` → CAT_L029
- `test_check_seeds_patterns_jsonl_nonempty` → CAT_L029
- `test_check_seeds_clean` → empty list

Approach:
- Move `BLOCKLIST_PATTERNS`, `_BLOCKLIST_RE`, `REQUIRED_PLACEHOLDERS`, `SENTINEL_RE`, `FENCE_RE`, `_is_blank_or_comment`, the per-file scan logic into lint.py as module-level constants/functions (prefixed `_seeds_*`)
- `_PackRules.__init__` already has `self._dir`; opt-in check uses `self._get_pack_toml()`
- Add `CAT_L029 = "CAT-L029"` to `DiagnosticCode`
- Use `_diag(DiagnosticCode.CAT_L029, ...)` for all findings

## Task 4 — `_PackRules._check_first_value()`
**Depends on:** Task 1
**Verification:** TDD

Tests:
- `test_check_first_value_missing_section` → CAT_L030, `"[pack.first-value] section missing"`
- `test_check_first_value_level_a_missing_field` → CAT_L030 per missing required field
- `test_check_first_value_level_b_required_when_flagged` → CAT_L030 for level-b fields when `level-b = true`
- `test_check_first_value_writes_to_repo_gate` → CAT_L030 when `safety-gate` missing
- `test_check_first_value_tutorial_missing_file` → CAT_L030, `"does not exist"`
- `test_check_first_value_clean` → empty list

Approach:
- `_PackRules.__init__` gains `root: Path` parameter; update all callsites in `lint_catalogue()`
- Inline `_check_pack` logic from lint-first-value-contract.py as `_check_first_value(self) -> list[Diagnostic]`
- `root` needed for tutorial path resolution; use `self._root` (store in constructor)
- Add `CAT_L030 = "CAT-L030"` to `DiagnosticCode`

## Task 5 — `_PackRules._check_credentialed_skills()`
**Depends on:** Task 1
**Verification:** TDD

Tests:
- `test_check_credentialed_skills_no_skills_dir` → empty list
- `test_check_credentialed_skills_missing_security_heading` → CAT_L031
- `test_check_credentialed_skills_missing_required_phrase_cli` → CAT_L031
- `test_check_credentialed_skills_argv_ban` → CAT_L031, `"argv-borne credential flag"`
- `test_check_credentialed_skills_env_missing_env_read` → CAT_L031
- `test_check_credentialed_skills_denyset_incomplete` — D2b: deny-set declared but missing a required flag entry → CAT_L031, `"deny-set"`
- `test_check_credentialed_skills_dotfile_read` — D3: skill Python body reads `~/.gitconfig` via AST-detectable path chain → CAT_L031, `"dotfile"`
- `test_check_credentialed_skills_clean` → empty list

Approach:
- Move all AST helper functions (`add_argument_flags`, `_literal_string`, `env_reads`, `has_credentials_shim_import`, `has_credbroker_import`, `has_credbroker_sso_import`, `sso_broker_call_targets`, `has_subprocess_run`, `disallowed_subprocess_calls`, `imports_playwright`, `denyset_flag_groups`, `has_scrubbing_parser`, `_check_dotfile_read`, `_path_chain_components`, `_is_dotfile_chain`, `_is_canonical_shim`, `_shim_source_bytes`) from `lint_credentialed_skills.py` into `lint.py` as module-level functions prefixed `_cs_`
- Also move constants: `_CS_BANNED_FLAGS`, `_CS_DOTFILE_PARENT`, etc.
- The scan loop becomes `_check_credentialed_skills(self) -> list[Diagnostic]` scoped to `self._dir / ".apm" / "skills"`
- `report()` calls become `_diag(DiagnosticCode.CAT_L031, Severity.ERROR, message)` appended to a local list
- `relpath(p)` calls: use `str(p.relative_to(self._dir))` for path in diagnostic
- Add `CAT_L031 = "CAT-L031"` to `DiagnosticCode`

## Task 6 — `_step_agent_artifacts()` (verify step 11)
**Depends on:** Task 1
**Verification:** TDD

Tests:
- `test_step_agent_artifacts_no_claude_dir` → empty list (graceful)
- `test_step_agent_artifacts_skill_missing_name` → CAT-V-011, message contains `"frontmatter missing required key: name"`
- `test_step_agent_artifacts_agent_missing_model` → CAT-V-011
- `test_step_agent_artifacts_credentialed_skill_bad_auth` → CAT-V-011 (from metadata.auth validation)
- `test_step_agent_artifacts_unknown_skill_key` → CAT-V-011
- `test_step_agent_artifacts_broken_link` → CAT-V-011
- `test_step_agent_artifacts_pyyaml_absent` — monkeypatch `builtins.__import__` to raise `ImportError` for "yaml"; assert exactly one CAT-V-011 result with message containing `"PyYAML required"`
- `test_step_agent_artifacts_no_module_scope_yaml` — assert `verify` module has no `yaml` attribute at import time (i.e., `import yaml` does not appear at module scope in `verify.py`); this test passes if and only if the PyYAML fence is maintained
- `test_step_agent_artifacts_pipeline_integration` — run `_step_agent_artifacts` against the in-repo root (REPO_ROOT) where `root/.claude` exists; assert the return value is an empty list (clean repo) AND assert a counter captured inside the step shows ≥1 skill/agent file was actually inspected (non-vacuous execution)
- `test_step_agent_artifacts_clean` → empty list

Approach:
- ALL `yaml.*` references (including `_FrontmatterLoader` class definition, `_FrontmatterLoader.add_constructor(...)`) MUST be inside the `_step_agent_artifacts` function body (or a helper called from within), after the guarded `import yaml`. Zero `yaml.*` at `verify.py` module scope.
- Define `_FrontmatterLoader` and helpers (`parse_frontmatter`, `check_links`, `check_skill`, `check_agent`, `check_command`) as nested functions or module-level functions with lazy-import guard pattern — whichever keeps them inside the PyYAML fence.
- `_step_agent_artifacts(root, config, pack, tmpdir)` checks `root / ".claude"` skills/agents/commands; APM leak guard on `root / "packs" / "core" / ".apm" / "skills"` if it exists
- PyYAML import guarded: `try: import yaml; except ImportError: return [_err("CAT-V-011", "PyYAML required for agent-artifact lint — install agentbundle[lint]")]`
- Error findings use `_err("CAT-V-011", message, path=str(path))`
- Replace `_step_generated_schema` (step 11 pass-through) with `_step_agent_artifacts`; update label to `"agent artifact lint"`

## Task 7 — `_step_plugin_manifests()` (verify step 13)
**Depends on:** Task 1
**Verification:** TDD

Tests:
- `test_step_plugin_manifests_no_dist_dir` → empty list (graceful — skip when dist absent)
- `test_step_plugin_manifests_invalid_manifest` → CAT-V-013, schema error message
- `test_step_plugin_manifests_marketplace_with_hooks` → CAT-V-013
- `test_step_plugin_manifests_clean` → empty list
- `test_step_plugin_manifests_pipeline_integration` — run `_step_build_output` then `_step_plugin_manifests` on the in-repo catalogue root; assert step 13 finds ≥1 manifest (non-vacuous execution). Ensures a future regression that stops emitting the claude-plugin route fails loudly rather than passing with nothing validated.

Approach:
- Inline `main()` logic from `validate-claude-plugin-manifests.py` into `_step_plugin_manifests(root, config, pack, tmpdir)`
- `DIST_DIR` becomes `tmpdir / "dist" / "claude-plugins"`
- Import `_read_bundled` and `validate_instance` from `agentbundle.build.main` and `agentbundle.build.validate`
- Error findings use `_err("CAT-V-013", message, pack=pack_name, path=str(rel))`
- Replace `_step_marketplace_parity` (step 13 pass-through) with `_step_plugin_manifests`

## Task 8 — Delete scripts and clean call sites
**Depends on:** Tasks 2–7
**Verification:** Goal-based — `grep -r "lint-profiles\|lint-catalogue-seeds\|lint-first-value-contract\|lint_credentialed_skills\|lint-credentialed-skills\|lint-agent-artifacts\|validate-claude-plugin-manifests" tools/ docs/ .github/ packages/agentbundle/ --include="*.py" --include="*.sh" --include="*.md" --include="*.yml" --include="*.yaml"` finds no remaining live references.

Done when:
- Six scripts deleted
- `tools/lint-credentialed-skills.sh` deleted
- `pre_pr_catalogue.py`: lines for agent-artifact lint, catalogue-seeds lint + self-test, credentialed-skill lint + self-test, profiles lint + self-test removed
- Self-test scripts `test-lint-profiles.py`, `test-lint-catalogue-seeds.py`, `test-lint-credentialed-skills.py`, `test-lint-first-value-contract.py`, and `test-lint-agent-artifacts.sh` deleted
- Full-repo grep for all six names finds only history/docs that don't break

## Task 8c — Migrate existing tests and update CI workflows
**Depends on:** Tasks 2–7, Task 8
**Verification:** Goal-based

Done when:
- `packages/agentbundle/tests/unit/test_lint_agent_artifacts_metadata_auth.py` migrated — assertions moved onto `_step_agent_artifacts` or new `_check_credentialed_skills` unit tests; subprocess invocation of `tools/lint-agent-artifacts.py` removed
- `packages/agentbundle/tests/unit/test_credbroker_lint_hardening.py` migrated — importlib load of `tools/lint_credentialed_skills.py` replaced with direct calls to `_check_credentialed_skills()`
- `packages/agentbundle/tests/hooks/test_pre_pr_py.py` expected-tool list updated to remove the four deleted invocations
- `packages/agentbundle/tests/unit/test_reference_architecture.py` updated — any reference to `lint-catalogue-seeds.py` removed or repointed
- `packages/agentbundle/tests/integration/test_install_snapshot.py` updated — references to `lint-catalogue-seeds.py` removed; sync comments repointed to `lint.py (_PackRules._check_seeds)` to preserve the BLOCKLIST_PATTERNS mirror invariant
- `.github/workflows/docs.yml`: lint-agent-artifacts/lint-catalogue-seeds/lint-profiles *jobs* removed AND the six `on: paths:` trigger entries for those scripts removed
- `.github/workflows/build-check.yml` test-lint-profiles.py and lint-profiles.py lines removed; stale comment at line 84 (`tools/lint-agent-artifacts.py (and siblings)`) updated
- `.github/workflows/publish-claude-plugins.yml` validate-claude-plugin-manifests.py step removed (now covered by `agentbundle catalogue verify`)
- `.github/workflows/catalogue-tooling-ci-gates.yml` pyyaml install step label updated (was "Install pyyaml for lint-agent-artifacts and credentialed-skill tests")
- `tools/repo/build_gate_chain.py` steps for `validate-claude-plugin-manifests`, `test-lint-first-value-contract`, `lint-first-value-contract` removed (all three scripts deleted; validate-claude-plugin-manifests covered by `catalogue verify` step 13)
- `tools/test_build_gate_chain.py` expected-chain assertions for those three steps removed (lines ~193, 201, 202)
- `tools/test-all.py` entries for `lint-agent-artifacts` (bash self-test) and `lint-catalogue-seeds` (Python self-test) removed from the test registry
- `tools/test-check-contract-drift.py` docstring reference to `tools/test-lint-profiles.py` repointed to `lint.py`
- `packages/agentbundle/agentbundle/commands/profile.py` comment referencing `tools/lint-profiles.py` repointed to `lint.py (_check_profiles)`
- `packages/agentbundle/agentbundle/commands/install.py` comment referencing `tools/lint-profiles.py` repointed
- `packs/core/pack.toml` and `packs/governance-extras/pack.toml` comments referencing `tools/lint-catalogue-seeds.py` repointed to `lint.py (_PackRules._check_seeds)`

## Task 8a — Update CLI help strings
**Depends on:** Task 8
**Verification:** Goal-based — `python -m agentbundle catalogue lint --help` and `… verify --help` include the new check names.

Done when:
- `cli.py` `catalogue lint` help extended with: profiles, seeds, first-value-contract, credentialed-skills check descriptions
- `cli.py` `catalogue verify` help extended with: agent-artifacts and plugin-manifests check descriptions

## Task 8b — Update docs
**Depends on:** Task 8
**Verification:** Goal-based — grep finds no doc pages still describing the scripts as standalone.

Done when:
- `docs/CONVENTIONS.md` or any reference guide updated if it named the standalone scripts
- `packs/AGENTS.md` or `AGENTS.local.md` references to deleted script filenames removed

## Task 9 — Run full gate chain
**Depends on:** Tasks 8, 8a, 8b, 8c
**Verification:** Goal-based

Done when:
- `python tools/catalogue/pre_pr_catalogue.py` exits 0
- `python -m pytest packages/agentbundle/` exits 0
- `python -m pytest tools/test_build_gate_chain.py` exits 0

## Task 10 — Version bump and changelogs
**Depends on:** Task 9
**Verification:** Goal-based

Done when:
- `packages/agentbundle/pyproject.toml` version = `0.18.0`
- `[project.urls]` updated per brief
- `packages/agentbundle/CHANGELOG.md` has `## [0.18.0] — 2026-07-25`
- `docs/product/changelog.md` has `## [agentbundle][0.18.0] — 2026-07-25`

## Task 11 — PR and CI
**Depends on:** Task 10
**Verification:** Visual/manual QA — PR opened, CI green, merged.

Branch: `eugenelim/fold-standalone-linters-into-cli`
PR title: `feat(agentbundle): fold six standalone linters into catalogue lint/verify`

## Task 12 — Release
**Depends on:** Task 11 (merge confirmed)
**Verification:** Goal-based — tag `agentbundle-v0.18.0` applied; PyPI publish triggered.
