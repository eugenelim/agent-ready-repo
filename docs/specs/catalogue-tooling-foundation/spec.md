# Spec: Catalogue Tooling Foundation

- **Status:** Shipped
- **Owner:** eugenelim
- **Initiative:** ini-005 AgentBundle Portable Catalogue Tooling
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ini-005 brief (Buckets 1, 2, 3); RFC-0072 (existing package-catalogue command)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

No structured boundary exists between the portable catalogue engine and the
repository-specific tooling. All linting, building, verification, and packaging
logic lives directly under `agentbundle/build/` or in `tools/` with no
distinction. An external catalogue cannot use any of it without copying the
Makefile and `tools/` directory.

This spec establishes the three architectural layers defined in the ini-005
brief: creates the `agentbundle/catalogue_tooling/` package with its module
skeleton and shared result/diagnostic types, defines the `catalogue.toml`
configuration schema (JSON Schema + TOML loading + validation), writes the
repo's `catalogue.toml`, and registers the `agentbundle catalogue` and
`agentbundle lint packs` CLI subcommand groups as stubs that return usage
errors. All Wave 2 specs depend on these foundations.

## Boundaries

### Always do

- Create `agentbundle/catalogue_tooling/` with modules: `__init__.py`,
  `config.py`, `diagnostics.py`, `lint.py`, `verify.py`, `build.py`,
  `self_host.py`, `package.py`, `archive.py`, `defaults.py`, `results.py`.
  Wave 2-4 specs fill the logic; this spec writes stubs that raise
  `NotImplementedError` with a docstring explaining what each module owns.
- Define all shared result and diagnostic types in `results.py` and
  `diagnostics.py`. These types are the stable contract between all modules.
- Define `catalogue.toml` JSON Schema at `docs/contracts/catalogue.schema.json`
  and bundle a copy at `agentbundle/_data/catalogue.schema.json`. Add a
  drift check (stdlib `filecmp` or byte comparison) invoked from the test suite.
- Implement `config.py`: `load_catalogue_config(root: Path) -> CatalogueConfig | None`.
  Returns `None` when `catalogue.toml` is absent (backward compat). On presence,
  validates against the schema and raises `CatalogueConfigError` on violation.
- Write `catalogue.toml` at the repository root matching the shape in Bucket 3.
- Register `agentbundle catalogue <sub>` as a new top-level subparser group in
  `agentbundle/cli.py`. Each sub-subcommand (`lint`, `verify`, `build`,
  `self-host`, `package`, `sync-defaults`) is registered with `--root`,
  `--pack`, and `--format` where applicable; all stubs exit 1 with
  `"not yet implemented"` until Wave 2-4 specs fill them.
- Register `agentbundle lint packs` as a new top-level `lint` subparser group
  with a `packs` subcommand; the stub delegates to the `catalogue lint` stub.
- Enforce config validation rules from Bucket 3: schema integer check,
  catalogue name safe-identifier check, all paths relative and inside root,
  no traversal, no symlink escape, required entries subset of include entries,
  recipes are bundled IDs or safe relative TOML paths, preferred-adapter
  exists in adapter contract, default-source passes existing source validator,
  no credential-bearing URLs, minimum-agentbundle-version safe-comparable,
  unknown keys rejected.
- Use Python 3.11 stdlib only.
- All new tests pass; all existing tests pass.

### Ask first

- Adding extension tables (unknown-key opt-in) to the catalogue.toml schema.
- Changing the package name from `catalogue_tooling` to anything else.
- Adding `catalogue.toml` as a runtime catalogue marker (Bucket 3 explicitly
  says do NOT make it a new marker in this change).

### Never do

- Move `agentbundle/catalogue.py` (the catalogue-source resolver) — its name
  is distinct from the new subpackage.
- Put repo-specific governance logic (RFC checks, SAST wiring) inside
  `catalogue_tooling/`.
- Implement any Wave 2-4 logic in this spec; stubs only.
- Accept credentials, bearer tokens, or credential-bearing URLs in
  `catalogue.toml` validation.

## Testing Strategy

- **TDD** for all `config.py` validation rules: one test per validation failure
  path + one test for valid public config + one test for valid enterprise config
  + absent-file backward-compat test.
- **TDD** for schema drift check: read both copies, assert byte-equal.
- **Goal-based** for CLI stub registration: `agentbundle catalogue --help` exits
  non-zero (not 0) with usage listing all sub-subcommands; `agentbundle lint
  packs --help` lists `--root`. No logic yet, just parser registration.
- **Goal-based** for module stubs: import each `catalogue_tooling` module; no
  `ImportError`; calling any stub raises `NotImplementedError`.

## Acceptance Criteria

- [x] AC1: `agentbundle/catalogue_tooling/` exists with all 11 modules
  importable with no `ImportError`.
- [x] AC2: Every stub function/class in Wave 2-4 modules raises
  `NotImplementedError` (not `pass` — the raise is the signal to Wave 2 implementers).
- [x] AC3: `results.py` exports at least: `Severity` (enum: ERROR/WARN/INFO),
  `Diagnostic` (dataclass: code, severity, pack, path, line, col, message,
  remediation), `CommandResult` (dataclass: ok, diagnostics, schema_version,
  command, operation, agentbundle_version, catalogue_schema_version),
  `LintResult(CommandResult)`, `VerifyResult(CommandResult)`,
  `BuildResult(CommandResult)`, `SelfHostResult(CommandResult)`,
  `PackageResult(CommandResult)`, `SyncDefaultsResult(CommandResult)`.
- [x] AC4: `docs/contracts/catalogue.schema.json` exists and is valid JSON.
  `agentbundle/_data/catalogue.schema.json` exists and is byte-identical.
  A test asserts byte equality.
- [x] AC5: `load_catalogue_config(root)` returns `None` when `catalogue.toml`
  is absent, preserving all existing default behavior.
- [x] AC6: `load_catalogue_config(root)` raises `CatalogueConfigError` for each
  of the 14 validation failure paths listed in Boundaries: bad schema integer,
  unsafe name, absolute path, traversal, symlink escape, required not in include,
  unknown recipe, unsafe recipe path, unknown preferred-adapter, invalid source,
  malformed Artifactory fields, credential URL, non-comparable version string,
  unknown top-level key (without extension table).
- [x] AC7: `catalogue.toml` at repo root is present, parses without error, and
  passes `load_catalogue_config` validation.
- [x] AC8: `catalogue.toml` contains: `schema`, `[catalogue]` (name,
  display-name, description, minimum-agentbundle-version),
  `[catalogue.paths]` (packs, profiles, contracts, marketplace, build-output),
  `[catalogue.build]` (recipes list, self-host bool, claude-plugin-branch,
  marketplace-description), `[catalogue.package]` (include, required),
  `[distribution.agentbundle]` (install-defaults-output, preferred-adapter,
  default-source), `[distribution.agentbundle.artifactory]` (enabled = false).
- [x] AC9: `agentbundle catalogue --help` exits non-zero (stub) and lists
  `lint`, `verify`, `build`, `self-host`, `package`, `sync-defaults` in output.
- [x] AC10: `agentbundle lint packs --help` exits non-zero (stub) and shows
  `--root` in the help text.
- [x] AC11: All existing AgentBundle tests pass unmodified.

## Assumptions

1. The `agentbundle/catalogue.py` module name does not conflict with
   `agentbundle/catalogue_tooling/` as a package (Python package vs module).
2. The existing `agentbundle/build/validate.py` JSON-Schema validator is used
   for schema validation within `config.py` (no new dep).
3. The adapter contract at `docs/contracts/adapter.toml` lists the valid
   preferred-adapter values; `config.py` reads it at validation time.
4. `minimum-agentbundle-version` in `catalogue.toml` uses a placeholder version
   (`"0.14.0"`) that will be updated to the actual release version at the end
   of ini-005.
