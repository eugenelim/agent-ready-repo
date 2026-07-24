# Plan: Catalogue Tooling — Enhanced Packaging

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

## Approach

Four tasks building on the existing RFC-0072 implementation: (1) update the
allowlist and manifest schema; (2) implement the staging + atomic placement
sequence with self-verification; (3) wire `agentbundle catalogue package` CLI
and add the `package-catalogue` compat alias; (4) update the existing package
tests for the new command surface. Most of the archive assembly logic exists in
`commands/package_catalogue.py` — this spec migrates it to `catalogue_tooling/package.py`
and extends it rather than rewriting from scratch.

## Constraints

- ini-005 brief Bucket 8, all staging/atomicity/self-verification requirements.
- Depends on `verify_catalogue` and `verify_archive` from spec/catalogue-tooling-verify.
- Must not duplicate shallow validator — always call `verify_catalogue`.
- Channel descriptor written last (after archive + sidecar verified).
- `catalogue.toml` excluded from archive.
- Python 3.11 stdlib only; `SOURCE_DATE_EPOCH` determinism preserved from RFC-0072.

## Construction tests

- `test_package_includes_required_files`: fixture with `LICENSE-APACHE`, `LICENSE-MIT`,
  marketplace; assert archive contains both.
- `test_package_missing_license_apache_fails`: remove `LICENSE-APACHE`; assert exit
  non-zero before output.
- `test_package_no_generic_license_assumed`: fixture without `LICENSE`; assert no
  error (generic LICENSE is not required).
- `test_package_catalogue_toml_excluded`: assert `catalogue.toml` not in archive.
- `test_package_channel_descriptor_written_last`: use a `_write_spy`; assert
  channel descriptor write call comes after archive + sidecar calls.
- `test_package_deterministic`: build twice, SOURCE_DATE_EPOCH fixed; assert
  sha256 equal.
- `test_package_overwrite_refused`: pre-create archive path; assert exit non-zero.
- `test_package_staged_cleanup_on_failure`: inject failure in verify_archive;
  assert staged files removed.
- `test_extracted_archive_valid_local_catalogue`: extract; call `verify_catalogue`;
  assert ok.

## Design (LLD)

### Staging sequence

```python
def package_catalogue(root, bundle, release, channel, output, **opts):
    # 1. Pre-package verify
    verify_result = verify_catalogue(root)
    if not verify_result.ok:
        return PackageResult(ok=False, ...)

    # 2. Construct archive bytes (in-memory)
    archive_bytes, manifest = _build_archive(root, bundle, release, opts)

    # 3. Write staged archive
    staged_archive = _staging_path(output_archive_path)
    staged_archive.write_bytes(archive_bytes)

    # 4. Compute + write staged sidecar
    digest = hashlib.sha256(archive_bytes).hexdigest()
    staged_sidecar = staged_archive.with_suffix('.sha256')
    staged_sidecar.write_text(digest + "\n")

    # 5. Self-verify staged archive + sidecar
    verify_result = verify_archive(staged_archive, staged_sidecar)
    if not verify_result.ok:
        staged_archive.unlink(missing_ok=True)
        staged_sidecar.unlink(missing_ok=True)
        return PackageResult(ok=False, ...)

    # 6. Atomic place archive
    staged_archive.rename(output_archive_path)

    # 7. Atomic place sidecar
    staged_sidecar.rename(output_sidecar_path)

    # 8. Write channel descriptor LAST
    _write_channel_descriptor(output, bundle, channel, release, digest, opts)
    return PackageResult(ok=True, ...)
```

### Updated catalogue-manifest.json schema

Extended from RFC-0072 to add Bucket 8 required fields:
```json
{
  "schema": 2,
  "bundle": "...",
  "release": "...",
  "generated_at": "...",
  "source_revision": null,
  "minimum_agentbundle_version": "...",
  "catalogue_name": "...",
  "catalogue_display_name": "...",
  "adapter_contract_version": "...",
  "pack_schema_version": "...",
  "marketplace_digest": "sha256:...",
  "files": [...],
  "packs": [...],
  "profiles": [...]
}
```
Note: `schema` bumped from 1 → 2 to signal extended manifest. Archive verifier
must handle both schema 1 (legacy) and schema 2. AC-level: the `verify_archive`
function from spec/catalogue-tooling-verify must handle schema=2 manifests.

### Compat alias

In `agentbundle/commands/package_catalogue.py`:
```python
def run(args) -> int:
    import sys
    print(
        "WARNING: agentbundle package-catalogue is deprecated. "
        "Use: agentbundle catalogue package",
        file=sys.stderr
    )
    # Map old args to new signature
    from agentbundle.catalogue_tooling.package import package_catalogue
    result = package_catalogue(...)
    ...
```

---

## Tasks

### T1: Updated allowlist + manifest schema

**Verification mode:** TDD

**Tests:**
- `test_package_includes_required_files`
- `test_package_missing_license_apache_fails`
- `test_package_no_generic_license_assumed`
- `test_package_catalogue_toml_excluded`
- `test_manifest_schema_v2_fields`

**Approach:** Move archive assembly logic from `commands/package_catalogue.py`
to `catalogue_tooling/package.py`. Update `_REQUIRED_FILES` and `_DEFAULT_INCLUDE`
sets. Extend manifest builder to include new Bucket 8 fields. Update all
existing `test_package_catalogue_*.py` tests to reflect new command location.

**Depends on:** spec/catalogue-tooling-foundation

---

### T2: Staging + atomic placement + self-verification

**Verification mode:** TDD

**Tests:**
- `test_channel_descriptor_written_last`
- `test_staged_cleanup_on_verify_failure`
- `test_overwrite_refused`
- `test_deterministic_under_source_date_epoch`

**Approach:** Implement the 8-step staging sequence. Use `with_suffix('.tmp')`
for staged paths in same directory as final output. Inject `verify_archive`
via parameter for testability. Test the ordering invariant via call-ordering
spy.

**Depends on:** T1, spec/catalogue-tooling-verify (verify_archive function)

---

### T3: CLI wiring + compat alias

**Verification mode:** Goal-based check

**Tests:**
- `test_cli_catalogue_package_help` — flags: `--root`, `--bundle`, `--release`,
  `--channel`, `--output`, `--source-revision`, `--minimum-agentbundle-version`
- `test_cli_package_catalogue_deprecation` — subprocess; assert stderr contains
  "deprecated"

**Approach:** Replace `NotImplementedError` stub in `catalogue package` CLI
handler. Update `commands/package_catalogue.py` to print deprecation warning
and delegate.

**Depends on:** T2

---

### T4: Extracted archive as local catalogue

**Verification mode:** Visual / manual QA

**Tests:**
- `test_extracted_archive_valid_local_catalogue`
- `test_list_packs_against_extracted`

**Approach:** Package a test fixture catalogue; extract to tmpdir; call
`verify_catalogue(extracted)` and assert ok; call `list_packs(catalogue=extracted)`
and assert pack names appear. This is the round-trip proof.

**Depends on:** T3

## Changelog
