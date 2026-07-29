---
status: Done
---

# Implementation Plan: catalogue-tooling-init

## Task 1 — Schema relaxation + owner metadata
**Depends on:** none  
**Verification:** TDD  
**Files:** `packages/agentbundle/agentbundle/_data/catalogue.schema.json`, `packages/agentbundle/agentbundle/catalogue_tooling/config.py`

Make `contracts`, `install-defaults-output`, `default-source` optional in schema v1. Add `[catalogue.owner]` table (optional; `name` required when present).

**Tests:**
```python
# test_config_optional_fields.py
def test_contracts_path_optional():  # catalogue.toml without contracts passes
def test_install_defaults_output_optional():  # absent install-defaults-output passes
def test_default_source_optional():  # absent default-source passes
def test_owner_optional():  # catalogue without owner passes
def test_owner_name_required_when_present():  # owner table without name fails
def test_legacy_catalogue_unchanged():  # host catalogue.toml still validates
def test_contracts_path_validated_when_present():  # contracts still path-validated when set
```

## Task 2 — CatalogueOwner dataclass + config loading update
**Depends on:** Task 1  
**Verification:** TDD  
**Files:** `packages/agentbundle/agentbundle/catalogue_tooling/config.py`

Add `CatalogueOwner`, `CatalogueConfig.owner`, update loading to handle optional fields.

**Tests:**
```python
def test_owner_loaded_when_present():  # CatalogueConfig.owner.name correct
def test_owner_none_when_absent():  # CatalogueConfig.owner is None
def test_contracts_none_when_absent():  # CataloguePaths.contracts is None
def test_contracts_validated_when_present():  # path validation still runs when set
def test_default_source_skipped_when_empty():  # _validate_source not called when empty
```

## Task 3 — InitResult type
**Depends on:** none  
**Verification:** TDD  
**Files:** `packages/agentbundle/agentbundle/catalogue_tooling/results.py`

Add `FileAction`, `FilePlan`, `InitVerification`, `InitSummary`, `InitResult` dataclasses. `InitResult` extends `CommandResult` and carries `agentbundle_version` and `catalogue_schema_version` for parity with all other commands.

**Tests:**
```python
def test_init_result_ok_shape():  # ok=True result has expected fields including versions
def test_init_result_json_serializable():  # can be passed to render_json
def test_init_result_has_agentbundle_version():
def test_init_result_has_catalogue_schema_version():
```

## Task 4 — sync-defaults no-op when install-defaults-output absent
**Depends on:** Task 2  
**Verification:** TDD  
**Files:** `packages/agentbundle/agentbundle/catalogue_tooling/defaults.py`, `packages/agentbundle/agentbundle/commands/catalogue_sync_defaults.py`

When `config.distribution.agentbundle.install_defaults_output is None`, `check_defaults()` and `write_defaults()` return no-op success with info message. Note: `verify.py` step 16 already guards with `if not output_path: return []` — no verify.py change needed. The `catalogue sync-defaults` command handler also needs to handle None cleanly.

Optional fields use `str | None` (not `""`) so `is None` is the canonical not-configured predicate.

**Tests:**
```python
def test_check_defaults_noop_when_not_configured():  # ok=True, info message
def test_write_defaults_noop_when_not_configured():  # ok=True, no file written
def test_check_defaults_still_works_when_configured():  # existing behavior unchanged
def test_sync_defaults_command_exits_0_when_not_configured():  # command handler
```

## Task 5 — Scaffold loader (internal API extension + path-safety validation)
**Depends on:** none  
**Verification:** TDD  
**Files:** `packages/agentbundle/agentbundle/scaffold.py`

Add `validate_manifest_paths(manifest)` (rejects absolute/traversal/duplicate/case-collision/Windows-reserved paths in manifest). Add `verify_hashes_detailed()` returning per-file results. Add `list_files_with_hashes()` returning `{path: sha256}`. Add `find_unexpected_files()` returning files in scaffold dir not in manifest. Keep existing public API unchanged.

**Tests:**
```python
def test_validate_manifest_paths_accepts_safe_paths():
def test_validate_manifest_paths_rejects_absolute():
def test_validate_manifest_paths_rejects_traversal():
def test_validate_manifest_paths_rejects_duplicates():
def test_validate_manifest_paths_rejects_case_collision():
def test_validate_manifest_paths_rejects_windows_reserved():  # CON, PRN, AUX, NUL, etc.
def test_list_files_with_hashes_matches_manifest():
def test_verify_hashes_detailed_all_pass():
def test_verify_hashes_detailed_missing_file():
def test_read_file_returns_bytes():
def test_scaffold_works_from_package_data():
```

## Task 6 — TOML emitter (shared helper)
**Depends on:** none  
**Verification:** TDD  
**Files:** `packages/agentbundle/agentbundle/catalogue_tooling/toml_emit.py` (new)

Safe, minimal TOML emitter for generated `catalogue.toml`. Deterministic output.

**Tests:**
```python
def test_emit_str_basic():
def test_emit_str_special_chars():  # backslash, quote, newline, tab
def test_emit_str_unicode():  # UTF-8 passthrough
def test_emit_array_of_strings():
def test_emit_bool():
def test_emit_section():
def test_catalogue_toml_deterministic():  # same inputs → same output
def test_catalogue_toml_no_credentials():  # no URL, no API key
def test_catalogue_toml_valid_toml():  # tomllib.loads succeeds
def test_catalogue_toml_empty_marketplace_path():  # correct default path
```

## Task 7 — Empty marketplace generator (pure function)
**Depends on:** none  
**Verification:** TDD  
**Files:** `packages/agentbundle/agentbundle/catalogue_tooling/initialise.py` (marketplace part)

Pure function `generate_empty_marketplace(name, description, owner_name) -> str` returning JSON bytes.

**Tests:**
```python
def test_empty_marketplace_valid_json():
def test_empty_marketplace_shape():  # name, description, owner.name, plugins=[]
def test_empty_marketplace_deterministic():
def test_empty_marketplace_no_invented_url():
def test_empty_marketplace_utf8_final_newline():
```

## Task 8 — Init engine core (initialise.py)
**Depends on:** Tasks 2, 3, 5, 6, 7  
**Verification:** TDD  
**Files:** `packages/agentbundle/agentbundle/catalogue_tooling/initialise.py`

Full init engine: metadata resolution, plan construction, conflict detection, staging, apply, rollback.

**Tests:**
```python
def test_resolve_name_from_flag():
def test_resolve_name_from_dir_basename():
def test_resolve_name_invalid_basename_requires_flag():
def test_resolve_display_name_humanize():
def test_resolve_description_default():
def test_resolve_owner_name_default():
def test_resolve_preferred_adapter_from_flag():
def test_resolve_preferred_adapter_invalid_fails():
def test_build_plan_creates_correct_files():
def test_conflict_detection_create():  # nonexistent path → create
def test_conflict_detection_already_present():  # byte-identical → already-present
def test_conflict_detection_conflict_different_content():
def test_conflict_detection_conflict_symlink():
def test_conflict_detection_conflict_wrong_type():
def test_single_conflict_blocks_all():
def test_idempotent_second_run_all_already_present():
def test_dry_run_no_files_written():
def test_dry_run_no_target_dir_created():
def test_staging_verify_called():
def test_rollback_removes_only_created_files():
def test_rollback_preserves_preexisting_files():
def test_no_root_readme_created():
def test_no_network_request():
def test_no_subprocess_call():
```

## Task 9 — catalogue_init.py command handler
**Depends on:** Task 8  
**Verification:** TDD  
**Files:** `packages/agentbundle/agentbundle/commands/catalogue_init.py`

CLI handler with table and JSON rendering.

**Tests:**
```python
def test_run_new_target_exits_0():
def test_run_conflict_exits_1():
def test_run_usage_error_exits_2():
def test_run_json_format_parses():
def test_run_dry_run_no_writes():
def test_run_dry_run_conflict_exits_1():
```

## Task 10 — CLI registration + catalogue group help fix
**Depends on:** Task 9  
**Verification:** TDD  
**Files:** `packages/agentbundle/agentbundle/cli.py`

Register `init` subcommand. Fix catalogue group `--help` to use standard `HelpAction` (exit 0) instead of `_StubHelpAction`. Add `target` path normalization.

**Tests:**
```python
def test_catalogue_help_exits_0():
def test_init_in_catalogue_help_output():
def test_target_default_is_dot():
def test_target_explicit_path():
def test_init_all_flags_registered():
```

## Task 11 — CI contract guide: scaffold inclusion + link fix
**Depends on:** none  
**Verification:** goal-based  
**Files:** `tools/catalogue/sync_authoring_scaffold.py`, `guides/_shared/reference/catalogue-ci-contract.md`

Add `guides/_shared/reference/catalogue-ci-contract.md` to `_SYNC_PAIRS`. Fix "See also" relative links to be standalone-valid. Run `--write` then `--check`.

**Done when:** `python3 tools/catalogue/sync_authoring_scaffold.py --check` exits 0 after running `--write`. Links in "See also" section do not reference host-specific paths.

## Task 12 — How-to guide
**Depends on:** none  
**Verification:** goal-based  
**Files:** `guides/_shared/how-to/create-a-catalogue.md`

Write canonical how-to guide for creating a catalogue.

**Done when:** guide exists at the expected path with correct frontmatter.

## Task 13 — Version bump + changelog
**Depends on:** Tasks 1–12  
**Verification:** goal-based  
**Files:** `packages/agentbundle/pyproject.toml`, `packages/agentbundle/agentbundle/version.py`, changelog

Bump to `0.24.0`.

**Done when:** `agentbundle --version` prints `0.24.0`.

## Task 14 — Integration tests + dogfooding test
**Depends on:** Tasks 8–10  
**Verification:** TDD  
**Files:** new test files under `packages/agentbundle/tests/integration/`

Full integration coverage per Bucket 11 test matrix.

**Tests:**
```python
def test_new_target_full_lifecycle():
def test_existing_repo_unrelated_files_untouched():
def test_idempotence():
def test_conflict_catalogue_toml():
def test_conflict_packs_readme():
def test_conflict_symlink():
def test_rollback_on_staged_verify_failure():
def test_dry_run_no_target_created():
def test_json_output_parses():
def test_no_network_request():
def test_dogfood_blank_catalogue_passes_verify():
def test_dogfood_no_host_files_leaked():
def test_list_packs_zero_after_init():
def test_list_profiles_zero_after_init():
```
