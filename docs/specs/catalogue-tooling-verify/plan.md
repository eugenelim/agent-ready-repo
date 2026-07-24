# Plan: Catalogue Tooling — Verify

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

## Approach

Five tasks building from isolation upward: (1) archive safety primitives; (2)
archive verify pipeline; (3) source-checkout verify pipeline (18 steps); (4)
CLI wiring to replace foundation stubs; (5) confirmation of archive-as-local-catalogue
round-trip. Tasks 1-2 and 3 can be written in parallel since they touch different
files.

## Constraints

- ini-005 brief Bucket 6, all 18 source-checkout steps + 20+ archive checks.
- Depends on: `lint_catalogue` (spec/catalogue-tooling-lint), `check_defaults`
  (spec/catalogue-tooling-sync-defaults), `build_catalogue` and
  `check_self_host` (spec/catalogue-tooling-build-self).
- Python 3.11 stdlib only.
- No new runtime deps.
- `python -m agentbundle.build check` narrow semantics MUST be preserved.
- Build output during verify goes to `tempfile.mkdtemp()` — never to root.

## Construction tests

- `test_verify_valid_fixture`: call `verify_catalogue(fixture_root)`; assert `result.ok`.
- `test_verify_bad_pack_fails_step3`: fixture with invalid pack.toml; assert
  `result.ok is False` and diagnostic code names the pack.
- `test_archive_verify_valid`: create a minimal tarball with manifest; pass to
  `verify_archive`; assert ok.
- `test_archive_verify_digest_mismatch`: tamper one file byte in archive; assert
  non-ok with `CAT-V-DIGEST` code.
- `test_archive_verify_traversal_rejected`: member path `../secret`; assert rejection.
- `test_verify_defaults_step16`: fixture with stale install-defaults.toml;
  assert failure at step 16 when `install-defaults-output` configured.

## Design (LLD)

### 18-step source-checkout verification

```python
VERIFY_STEPS = [
    (1,  "catalogue.toml validation",         _step_config_validation),
    (2,  "catalogue lint",                    _step_lint),
    (3,  "pack schema validation",            _step_pack_schema),
    (4,  "plugin manifest validation",        _step_plugin_validation),
    (5,  "pack/plugin version parity",        _step_version_parity),
    (6,  "profile schema + pack refs",        _step_profiles),
    (7,  "dependency reference validation",   _step_dependencies),
    (8,  "adapter contract compatibility",    _step_adapter_compat),
    (9,  "primitive layout validation",       _step_primitive_layout),
    (10, "build output validation (tmpdir)",  _step_build_output),
    (11, "generated output schema",           _step_generated_schema),
    (12, "marketplace aggregation",           _step_marketplace),
    (13, "marketplace pack membership/version", _step_marketplace_parity),
    (14, "generated output drift checks",     _step_output_drift),
    (15, "self-host drift checks",            _step_selfhost_drift),
    (16, "sync-defaults check",               _step_sync_defaults),
    (17, "package preflight",                 _step_package_preflight),
    (18, "deterministic fixture checks",      _step_fixture_checks),
]
```

Each step function signature: `(root: Path, config: CatalogueConfig | None,
pack: str | None, tmpdir: Path) -> list[Diagnostic]`. Returns empty list on
pass. Verification stops at first non-empty step result unless
`continue_on_error=True`.

### Archive verification pipeline

Safety checks first (member-level), then semantic checks (manifest-level):
```python
ARCHIVE_CHECKS = [
    _check_sha256_sidecar,      # AC5 — early exit on sidecar mismatch
    _check_gzip_parseable,
    _check_compressed_size,
    _check_member_count_limit,
    _check_expanded_size,
    _check_no_absolute_paths,   # AC10
    _check_no_traversal,        # AC11
    _check_no_symlinks,         # AC12
    _check_no_hard_links,       # AC12
    _check_no_device_files,
    _check_no_fifos,
    _check_no_duplicate_members,# AC13
    _check_no_case_collisions,  # AC14
    _check_manifest_parseable,
    _check_manifest_schema,
    _check_all_manifest_digests,# AC16
    _check_no_undeclared_members, # AC15
    _check_catalogue_markers,
    _check_required_files,
    _check_pack_manifests,
    _check_plugin_manifests,
    _check_marketplace_parity,
    _check_profile_references,
    _check_min_agentbundle_compat,
    _check_local_discoverability, # AC17 — safe tmpdir extraction
]
```

### Stable diagnostic codes

```
CAT-V-001  catalogue.toml invalid
CAT-V-002  lint failure
CAT-V-003  pack schema invalid
CAT-V-004  plugin schema invalid
CAT-V-005  pack/plugin version mismatch
CAT-V-006  profile invalid
CAT-V-007  dependency unresolved
CAT-V-008  unsupported adapter
CAT-V-009  primitive layout invalid
CAT-V-010  build output invalid
CAT-V-011  generated schema invalid
CAT-V-012  marketplace invalid
CAT-V-013  marketplace pack mismatch
CAT-V-014  output drift detected
CAT-V-015  self-host drift detected
CAT-V-016  defaults drift detected
CAT-V-017  package preflight failed
CAT-V-018  fixture check failed
CAT-V-ARC-001  sha256 sidecar mismatch
CAT-V-ARC-002  gzip parse error
CAT-V-ARC-003  size limit exceeded
CAT-V-ARC-004  absolute member path
CAT-V-ARC-005  traversal path
CAT-V-ARC-006  symlink or hard link
CAT-V-ARC-007  device/special file
CAT-V-ARC-008  duplicate member
CAT-V-ARC-009  case collision
CAT-V-ARC-010  manifest parse error
CAT-V-ARC-011  manifest schema invalid
CAT-V-ARC-012  file digest mismatch
CAT-V-ARC-013  undeclared member
CAT-V-ARC-014  missing catalogue marker
CAT-V-ARC-015  missing required file
```

---

## Tasks

### T1: Archive safety primitives

**Verification mode:** TDD

**Tests:**
- `test_no_absolute_paths_detected`
- `test_traversal_detected`
- `test_symlink_in_archive_detected`
- `test_hard_link_detected`
- `test_duplicate_members_detected`
- `test_case_collision_detected`

**Approach:** Implement `archive.py` check functions operating on
`tarfile.TarInfo` objects. Each function takes a list of members and returns
`list[Diagnostic]`. No extraction needed for safety checks — just member headers.

**Depends on:** spec/catalogue-tooling-foundation (result types)

---

### T2: Archive verify pipeline

**Verification mode:** TDD

**Tests:**
- `test_archive_valid_passes_all`
- `test_archive_digest_mismatch_fails`
- `test_archive_undeclared_member_fails`
- `test_archive_sidecar_mismatch_early_exit`
- `test_archive_size_limits`
- `test_extracted_archive_is_valid_catalogue`

**Approach:** Implement `verify_archive(archive, sha256_file=None) -> VerifyResult`
orchestrating the 25-check pipeline. For the discoverability check, extract to
`tempfile.mkdtemp()` and call `verify_catalogue` (step 25 — this is the
round-trip). Safe extraction: only extract if all header checks pass.

**Depends on:** T1

---

### T3: Source-checkout verify pipeline (18 steps)

**Verification mode:** TDD

**Tests:**
- `test_verify_valid_minimal_catalogue`
- `test_verify_bad_pack_fails_step3`
- `test_verify_missing_marketplace_fails_step12`
- `test_verify_stale_defaults_fails_step16`
- `test_verify_builds_only_into_tmpdir`
- `test_verify_no_tools_dir_needed` (external catalogue portability)

**Approach:** Implement `verify_catalogue(root, pack=None, tmpdir=None) -> VerifyResult`.
Each step delegates to the appropriate Wave 2 function. Step 10 creates/uses
`tmpdir`. Run full test suite for regression.

**Depends on:** Wave 2 specs all shipped (lint, sync-defaults, build-self)

---

### T4: CLI wiring

**Verification mode:** Goal-based check

**Tests:**
- `test_cli_verify_help` — assert exit 0, flags present
- `test_cli_verify_valid_fixture` — subprocess; assert exit 0
- `test_cli_verify_archive` — subprocess with test archive; assert exit 0
- `test_cli_verify_format_json` — assert stdout is valid JSON

**Approach:** Replace `NotImplementedError` stub in `catalogue verify` CLI
handler. Wire `--archive` and `--sha256-file` flags. Add format rendering
(table and JSON) using `CommandResult` from results.py.

**Depends on:** T2, T3

---

### T5: External-catalogue portability smoke

**Verification mode:** Goal-based check

**Tests:**
- `test_external_catalogue_no_makefile`: create minimal external catalogue
  in `tmp_path` (no Makefile, no tools/); call `verify_catalogue`; assert ok

**Approach:** Fixture: minimal `catalogue.toml` + one pack + marketplace.json.
No repo-internal paths. Assert `verify_catalogue` returns `ok=True`. This is
the portable engine test.

**Depends on:** T3

## Changelog
