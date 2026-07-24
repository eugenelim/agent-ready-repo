# Spec: Catalogue Tooling — Verify

- **Status:** Draft
- **Owner:** eugenelim
- **Initiative:** ini-005 AgentBundle Portable Catalogue Tooling
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ini-005 brief Bucket 6; spec/catalogue-tooling-foundation;
  spec/catalogue-tooling-lint; spec/catalogue-tooling-sync-defaults;
  spec/catalogue-tooling-build-self
- **Shape:** service

> **Spec contract:** this document defines what "done" means.

## Objective

No single portable command can confirm a catalogue is completely valid — that
its packs validate, its build output is current, its marketplace is accurate,
its self-host projection is drift-free, and its defaults are synchronized.
Operators must manually chain `make lint-packs && make build && make build-check`
which is not portable to external catalogues.

This spec implements `agentbundle catalogue verify --root .` and
`agentbundle catalogue verify --archive <archive>` — the canonical comprehensive
verification command — by running the 18-step verification sequence defined in
Bucket 6 of the ini-005 brief. Source-checkout verification chains lint →
schema validation → build → marketplace checks → drift checks. Archive
verification checks the tarball's integrity, structure, and content conformance.

`agentbundle catalogue verify` does NOT run: model-backed evals, SAST, site
generation, changelog enforcement, or internal RFC checks.

Compatibility alias: `python -m agentbundle.build check` → prints deprecation
warning, routes to `agentbundle catalogue self-host --check` (preserving narrow
semantics) — NOT to this comprehensive verify. See design notes.

> **Deliberate design decision:** The ini-005 brief's Bucket 2 alias table maps
> `build check → agentbundle catalogue verify` (brief line 241). This spec
> overrides that mapping by routing `build check` to `catalogue self-host --check`
> (narrow self-host drift only). Authority: brief lines 263-265 — "Preserve any
> narrower self-host-drift semantics of the existing build check through an
> internal compatibility option; do not silently broaden an old command in a way
> that breaks existing automation." The narrowing wins; existing automation that
> expected only a self-host drift report must not suddenly incur 18-step verify
> cost.

## Boundaries

### Always do

- Implement `verify_catalogue(root, pack=None) -> VerifyResult` in
  `agentbundle/catalogue_tooling/verify.py`. Call the underlying functions from
  lint.py, defaults.py, build.py, self_host.py — never their CLI handlers.
- Run verification steps in logical order per Bucket 6 §1-18. Stop at first
  step failure by default; support `--continue-on-error` (internal API, not
  a CLI flag in v1).
- For `--archive`: implement `verify_archive(archive: Path, sha256_file: Path | None) -> VerifyResult` in `archive.py`. Run all archive checks from Bucket 6 §Archive Verification (20+ checks).
- Wire `agentbundle catalogue verify` CLI subcommand (replaces foundation stub);
  support `--root`, `--pack`, `--format`, `--archive`, `--sha256-file`.
- Build into a temporary directory for step 10 (rendered output validation);
  never write to the catalogue root.
- JSON output: one valid JSON document to stdout; progress/warnings to stderr;
  deterministic ordering; include schema_version, command, operation,
  agentbundle_version, catalogue_schema_version; stable diagnostic codes;
  source-relative paths; never include credentials.
- `catalogue verify` automatically runs `check_defaults` in check mode when
  `install-defaults-output` is configured in `catalogue.toml` (step 16).
- Return nonzero exit code for any integrity or conformance failure.
- Python 3.11 stdlib only.
- All existing tests pass.

### Ask first

- Adding a `--stop-at <step>` flag for partial verification.
- Adding `--skip-build` to skip step 10 (rendered output validation) for speed.
- Parallelizing verification steps.

### Never do

- Run model-backed evals, SAST, site generation, changelog enforcement,
  internal RFC checks, or any repository-specific policy as part of verify.
- Execute content from an archive being verified.
- Write files to the catalogue root during verify (build output goes to tmpdir).
- Use subprocess to call `agentbundle` CLI from within `agentbundle`.
- Introduce new runtime dependencies.
- Silently broaden `python -m agentbundle.build check` to run comprehensive
  verify; that alias preserves narrow self-host-drift semantics.

## Testing Strategy

- **TDD** for archive verification: each of the 20+ archive checks has a test
  with a crafted bad archive (no absolute paths, no traversal, no symlinks,
  digest mismatch, undeclared member, etc.).
- **TDD** for the 18 verification steps against fixture catalogues: valid minimal
  catalogue passes all 18; invalid pack fails step 3; missing marketplace fails
  step 12; stale defaults fail step 16.
- **Goal-based** for CLI wiring: `agentbundle catalogue verify --help` exits 0;
  `agentbundle catalogue verify --root <valid-fixture>` exits 0.
- **Goal-based** for external catalogue portability: a temporary directory with
  no Makefile and no tools/ passes `verify_catalogue`.

## Acceptance Criteria

- [ ] AC0: `agentbundle validate <pack-path>` continues to work unchanged; its
  underlying validation function (`agentbundle.build.validate.validate`) is the
  same function step 3 (`_step_pack_schema`) calls — no duplication. A test
  asserts that `validate` passes on a pack that also passes `verify_catalogue`.
- [ ] AC1: `agentbundle catalogue verify --root <valid-catalogue>` exits 0 and
  prints no errors.
- [ ] AC2: `agentbundle catalogue verify --root <catalogue-with-bad-pack>` exits
  non-zero and names the failing pack and step.
- [ ] AC3: `agentbundle catalogue verify --archive <valid.tar.gz>` exits 0.
- [ ] AC4: `agentbundle catalogue verify --archive <tampered.tar.gz>` exits
  non-zero with a clear digest mismatch error.
- [ ] AC5: `agentbundle catalogue verify --archive <archive>
  --sha256-file <sidecar>` validates the sidecar checksum before inspecting
  archive contents; a wrong sidecar causes early exit.
- [ ] AC6: Verification builds into a temp directory; the catalogue root has
  zero new or modified files after verify completes.
- [ ] AC7: Step 16 (sync-defaults check) runs automatically when
  `install-defaults-output` is set in `catalogue.toml`; stale defaults
  produce a verification failure.
- [ ] AC8: `--format json` emits one valid JSON document to stdout; all
  diagnostic and progress output goes to stderr.
- [ ] AC9: JSON output includes schema_version, command (`"catalogue verify"`),
  operation, agentbundle_version, catalogue_schema_version, ok (bool),
  diagnostics list (each with code, severity, pack, path, line, message).
- [ ] AC10: Archive verification rejects absolute member paths.
- [ ] AC11: Archive verification rejects traversal paths (`../`).
- [ ] AC12: Archive verification rejects symlinks and hard links in the archive.
- [ ] AC13: Archive verification rejects duplicate member names.
- [ ] AC14: Archive verification rejects case-insensitive path collisions.
- [ ] AC15: Archive verification rejects undeclared archive members (not in
  `catalogue-manifest.json` and not the manifest itself).
- [ ] AC16: Archive verification validates every declared manifest file digest.
- [ ] AC17: An extracted archive is accepted as a valid local catalogue
  (passes `verify_catalogue` on the extracted root).
- [ ] AC18: All existing tests pass.

## `catalogue-manifest.json` contract (authoritative for this spec)

This spec defines the manifest schema that `archive.py` validates. The
`catalogue-tooling-package-enhanced` spec implements TO this contract.
Accepted schema versions: 1 (legacy from RFC-0072) and 2 (extended).

**Schema version 2 required fields:**
```
schema: integer (1 or 2)
bundle: string
release: string
generated_at: ISO-8601 UTC string
source_revision: string | null
minimum_agentbundle_version: string (when provided)
catalogue_name: string (v2 only)
catalogue_display_name: string (v2 only)
adapter_contract_version: string (v2 only)
pack_schema_version: string (v2 only)
marketplace_digest: string "sha256:<64hex>" (v2 only)
files: [{path: string, sha256: string}]  — sorted by path
packs: [{name: string, version: string}] — sorted by name
profiles: [{name: string}]               — v2 only, sorted by name
```
`catalogue-manifest.json` itself is NOT listed in `files`.

## Assumptions

1. Wave 2 specs (lint, sync-defaults, build-self) are shipped before this spec
   begins implementation.
2. The archive format produced by `catalogue-tooling-package-enhanced` matches
   the archive verification expectations in this spec. Since that spec ships
   after this one, this spec defines the archive contract; the package spec
   implements to it.
3. `agentbundle catalogue verify` is the function `catalogue-tooling-package-enhanced`
   calls internally for pre-package validation — no duplicate validator.
4. `python -m agentbundle.build check` continues to route to `cmd_check` in
   `self_host.py` with only a stderr deprecation notice. It does NOT route to
   comprehensive verify.
5. All 18 verification steps treat an absent `catalogue.toml` as a pass for step 1
   (config validation returns `None` from `load_catalogue_config` → no-op), so
   an extracted archive root that contains no `catalogue.toml` passes all steps.
   Steps that depend on config values skip gracefully when config is `None`.
6. `agentbundle verify packs` alias is intentionally absent: this CLI surface
   never existed on any branch, so no alias is needed.
