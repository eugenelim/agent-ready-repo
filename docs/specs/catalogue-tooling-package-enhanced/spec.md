# Spec: Catalogue Tooling — Enhanced Packaging

- **Status:** Draft
- **Owner:** eugenelim
- **Initiative:** ini-005 AgentBundle Portable Catalogue Tooling
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ini-005 brief Bucket 8; spec/catalogue-tooling-verify;
  RFC-0072 (existing package-catalogue command)
- **Shape:** service

> **Spec contract:** this document defines what "done" means.

## Objective

The existing `agentbundle package-catalogue` command (RFC-0072) builds
deterministic archives but has gaps: it assumes a generic `LICENSE` file
(not `LICENSE-APACHE`/`LICENSE-MIT`), hard-codes the include list, lacks a
pre-package comprehensive verify step, and has no staged output with
self-verification before the channel descriptor is written.

This spec rewrites the packaging layer as `agentbundle catalogue package` under
`agentbundle/catalogue_tooling/package.py`, fixing the allowlist, integrating
the full `verify_catalogue` pre-check, adding staging + atomic placement, and
self-verifying the output archive before the channel descriptor is written last.
The existing `agentbundle package-catalogue` becomes a compatibility shim with
a deprecation warning.

## Boundaries

### Always do

- Implement `package_catalogue(root, bundle, release, channel, output, **opts) -> PackageResult`
  in `package.py`. Call `verify_catalogue(root)` internally — never duplicate a
  shallow validator.
- Updated allowlist from Bucket 8 §Required Allowlist Update. Required files:
  `packs/`, `.claude-plugin/marketplace.json`, `LICENSE-APACHE`, `LICENSE-MIT`.
  Default include: `packs/`, `profiles/`, `docs/contracts/`,
  `.claude-plugin/marketplace.json`, `README.md`, `LICENSE-APACHE`, `LICENSE-MIT`.
  Remove assumption that a generic `LICENSE` file exists.
  **Implicit denylist (always excluded regardless of `include`):** `.git/`,
  `tools/`, `packages/agentbundle/`, `dist/`, `__pycache__/`, `*.pyc`,
  `*.pyo`, `.env`, `*.key`, `*.pem`.
- Read include/required sets from `catalogue.toml` when present; enforce that
  required entries are a subset of include entries.
- Staging + atomic placement per Bucket 8 §Staging, Atomicity, Self-Verification:
  1. Construct archive bytes in memory.
  2. Write to staged path in output filesystem.
  3. Calculate/confirm digest.
  4. Write staged checksum sidecar.
  5. Run `verify_archive` against staged archive + sidecar.
  6. Atomically place immutable archive.
  7. Atomically place checksum sidecar.
  8. Generate + atomically place mutable channel descriptor LAST.
- Refuse to overwrite existing immutable release archive (no `--force-overwrite`
  in v1).
- Clean staged files on failure.
- Deterministic archive: sort paths, normalize uid/gid/mtime/modes, zero gzip
  header mtime, `SOURCE_DATE_EPOCH`-aware `generated_at`, stable JSON.
- `catalogue-manifest.json` schema from Bucket 8: schema_version, bundle,
  release, generated_at, source_revision, minimum_agentbundle_version,
  catalogue_identity, adapter_contract_version, pack_schema_version,
  marketplace_digest, files (path+sha256), pack names+versions, profile names.
- Do NOT package: `.git/`, `.github/`, `tools/`, `packages/agentbundle/`,
  caches, env files, credentials, dist/, editor state, raw `catalogue.toml`
  (it may contain enterprise distribution endpoints).
- `catalogue.toml` identity is projected safely into `catalogue-manifest.json`;
  full `catalogue.toml` is not included in the archive.
- Compatibility alias: `agentbundle package-catalogue` → prints deprecation
  warning to stderr, delegates to `agentbundle catalogue package`.
- Python 3.11 stdlib only.
- All existing tests pass.

### Ask first

- Adding `--force-overwrite` flag.
- Changing the archive layout (current: paths at archive root, no wrapper dir).
- Adding `--minimum-agentbundle-version` auto-derive from running version.
- Including `catalogue.toml` in archives under a flag.

### Never do

- Include raw `catalogue.toml` in the default archive (may expose enterprise endpoints).
- Write the channel descriptor before the archive + sidecar are successfully verified.
- Use subprocess to call `agentbundle` CLI from within agentbundle.
- Duplicate the verify logic; always call `verify_catalogue` and `verify_archive`.
- Expose a `--force-overwrite` flag in this implementation.

## Testing Strategy

- **TDD** for all Bucket 12 Packaging Tests, including:
  - archive includes `.claude-plugin/marketplace.json`, `LICENSE-APACHE`, `LICENSE-MIT`
  - missing required file fails packaging
  - generic `LICENSE` no longer assumed
  - existing release archive not overwritten
  - staged files cleaned on failure
  - channel descriptor placed last
  - archive self-verification occurs
  - tampered archive fails (via verify_archive integration)
  - deterministic bytes under SOURCE_DATE_EPOCH
  - extracted archive accepted as local catalogue
- **Goal-based** for CLI wiring and compat alias.

## Acceptance Criteria

- [ ] AC1: `agentbundle catalogue package --root . --bundle eng --release
  2026.07.24.1 --channel stable --output /tmp/out` produces the three-file
  Artifactory layout: archive, sidecar, channel descriptor.
- [ ] AC2: Archive contains `.claude-plugin/marketplace.json`, `LICENSE-APACHE`,
  `LICENSE-MIT`. Missing any required file causes exit non-zero before output.
- [ ] AC3: Generic `LICENSE` file (not `-APACHE`/`-MIT`) is not required.
- [ ] AC4: `catalogue.toml` is NOT present in the archive.
- [ ] AC5: Channel descriptor is written AFTER the archive and sidecar are
  staged and self-verified.
- [ ] AC6: Building twice with identical inputs and `SOURCE_DATE_EPOCH` fixed
  produces byte-identical archives.
- [ ] AC7: Existing release archive path → exit non-zero, no files written.
- [ ] AC8: If verify_archive fails on staged output, all staged files are
  removed and exit is non-zero.
- [ ] AC9: `catalogue-manifest.json` has all required Bucket 8 fields.
- [ ] AC10: `agentbundle package-catalogue <args>` prints deprecation warning
  to stderr and produces equivalent output.
- [ ] AC11: Extracted archive passes `verify_catalogue` (local catalogue).
- [ ] AC12: `agentbundle list-packs --catalogue <extracted-root>` succeeds.
- [ ] AC13: All existing `test_package_catalogue_*.py` tests pass unmodified
  or with only the deprecation-warning adaptation.
- [ ] AC14: The archive layout has no artificial wrapper directory; `packs/` is
  at archive root.
- [ ] AC15: The packaged archive contains no member whose path starts with
  `.git/`, `tools/`, `packages/agentbundle/`, or `dist/`. A test asserts
  this against an archive produced from a fixture that includes stub files at
  those paths; none should appear in the extracted archive members.

## Assumptions

1. spec/catalogue-tooling-verify ships before this spec (provides `verify_catalogue`
   and `verify_archive` functions).
2. The existing `package_catalogue.py` command module is replaced/superseded;
   its tests are updated for the deprecation alias.
3. `catalogue.toml`'s `[catalogue.package]` `include` and `required` lists are
   read when present; the hardcoded defaults apply when absent.
4. `SOURCE_DATE_EPOCH` semantics match spec/package-catalogue-command (already
   implemented in RFC-0072).
