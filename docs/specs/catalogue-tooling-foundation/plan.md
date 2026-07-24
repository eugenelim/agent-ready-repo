# Plan: Catalogue Tooling Foundation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

## Approach

Four tasks, sequential: (1) create the package skeleton + result/diagnostic
types; (2) implement config loading and validation; (3) write `catalogue.toml`
at repo root + both schema copies + drift test; (4) wire CLI stub subcommand
groups. Each task is independently testable before the next begins.

## Constraints

- ini-005 brief Bucket 1 (architecture), Bucket 2 (CLI stubs), Bucket 3
  (catalogue.toml schema and validation).
- Python 3.11 stdlib only — use the existing `agentbundle/build/validate.py`
  JSON-Schema validator, not a new dependency.
- Must not move or rename `agentbundle/catalogue.py`.
- Must not break any existing test.

## Construction tests

- `test_catalogue_tooling_imports`: import every `catalogue_tooling` module;
  assert no `ImportError`.
- `test_result_types_exported`: from `results.py` import each required type;
  assert `issubclass(LintResult, CommandResult)` etc.
- `test_config_absent_returns_none`: call `load_catalogue_config` with a temp
  dir containing no `catalogue.toml`; assert returns `None`.
- `test_config_valid_public`: parse the repo's `catalogue.toml`; assert success.
- `test_config_schema_drift`: read both schema copies; assert byte-equal.
- `test_cli_catalogue_group_registered`: run `agentbundle catalogue --help` via
  subprocess; assert subs appear in output.

## Design (LLD)

### Package skeleton

```
agentbundle/catalogue_tooling/
  __init__.py          # exports CatalogueConfigError, load_catalogue_config
  config.py            # CatalogueConfig dataclass + loader/validator
  diagnostics.py       # DiagnosticCode enum (stable string codes)
  results.py           # Severity, Diagnostic, CommandResult + subtypes
  lint.py              # stub: lint_catalogue(root, pack=None) -> LintResult
  verify.py            # stub: verify_catalogue(root, pack=None) -> VerifyResult
  build.py             # stub: build_catalogue(root, output) -> BuildResult
  self_host.py         # stub: check_self_host(root) / write_self_host(root)
  package.py           # stub: package_catalogue(root, ...) -> PackageResult
  archive.py           # stub: verify_archive(archive, sha256_file=None)
  defaults.py          # stub: check_defaults(root) / write_defaults(root)
```

### `CatalogueConfig` shape

```python
@dataclass
class CatalogueConfig:
    schema: int
    name: str
    display_name: str
    description: str
    minimum_agentbundle_version: str
    paths: CataloguePaths        # packs, profiles, contracts, marketplace, build_output
    build: CatalogueBuild        # recipes, self_host, claude_plugin_branch, marketplace_description
    package: CataloguePackage    # include, required
    distribution: DistributionConfig  # agentbundle sub-config
```

### Validation rules (all in `config.py`)

Performed in order; raise `CatalogueConfigError` on first violation:
1. `schema` is integer 1.
2. `catalogue.name` matches `^[A-Za-z0-9][A-Za-z0-9_\-]*$`.
3. Every path in `[catalogue.paths]` is relative (no leading `/`, no `..`).
4. Every path resolves inside catalogue root (no symlink escapes — use
   `Path(root / p).resolve().is_relative_to(root.resolve())`).
5. `package.required` ⊆ `package.include`.
6. Each recipe is a bundled name (`BUNDLED_RECIPES` frozenset) or a safe
   relative TOML path inside catalogue root.
7. `preferred-adapter` ∈ adapter contract's known adapter names.
8. `default-source` passes `agentbundle.source_defaults.validate_source`.
9. Artifactory fields: if `enabled = true`, `base-url` is https, no
   userinfo, no query params; `repository` and `bundle` match safe name regex.
10. No URL in any field contains `@` with userinfo or credential-shaped
    query params (`token=`, `password=`, `key=`, `secret=`).
11. `minimum-agentbundle-version` is a string comparable with `packaging.version`
    or the stdlib `re`-based semver subset already used in the codebase.
12. Unknown top-level keys → `CatalogueConfigError` unless `[x-*]` extension
    table (future opt-in, not implemented in this spec).

### CLI wiring

Add to `agentbundle/cli.py` after `package-catalogue`:
```python
# agentbundle catalogue <sub>
cat_parser = subparsers.add_parser("catalogue", ...)
cat_subs = cat_parser.add_subparsers(dest="catalogue_sub")
for sub in ("lint", "verify", "build", "self-host", "package", "sync-defaults"):
    p = cat_subs.add_parser(sub, ...)
    p.add_argument("--root", default=".")
    # add --pack, --format, etc. per sub
    p.set_defaults(func=_lazy("catalogue_tooling_stub"))

# agentbundle lint packs
lint_parser = subparsers.add_parser("lint", ...)
lint_subs = lint_parser.add_subparsers(dest="lint_sub")
packs_p = lint_subs.add_parser("packs", ...)
packs_p.add_argument("--root", default=".")
packs_p.set_defaults(func=_lazy("catalogue_tooling_stub"))
```

Stub handler in `agentbundle/commands/catalogue_tooling_stub.py`:
```python
def run(args) -> int:
    print(f"agentbundle catalogue {getattr(args, 'catalogue_sub', '')} not yet implemented", file=sys.stderr)
    return 1
```

---

## Tasks

### T1: Package skeleton + result types

**Verification mode:** TDD

**Tests:**
- `test_catalogue_tooling_imports` — imports all 11 modules with no error
- `test_result_types_structure` — asserts `LintResult` has `ok`, `diagnostics`,
  `schema_version` fields; `Diagnostic` has all 9 fields
- `test_stub_raises_not_implemented` — calls `lint_catalogue(Path("."))`;
  asserts `NotImplementedError`

**Approach:** Create the package directory and all 11 modules. In `results.py`,
define `Severity` (IntEnum), `Diagnostic` (dataclass), `CommandResult`
(dataclass), and the 5 subtypes. In each Wave 2-4 module, write a single stub
function with `raise NotImplementedError(...)`. Write `diagnostics.py` with
placeholder `DiagnosticCode` enum (codes will be filled by Wave 2 specs). Add
tests file at `tests/unit/test_catalogue_tooling_foundation.py`.

**Depends on:** none

---

### T2: `config.py` — catalogue.toml loading and validation

**Verification mode:** TDD

**Tests:**
- `test_config_absent` — assert `load_catalogue_config(tmp_path)` returns `None`
- `test_config_valid_public` — parse minimal valid public config; assert success
- `test_config_valid_enterprise` — parse enterprise config with Artifactory;
  assert success
- One test per validation rule (13 tests): bad schema, unsafe name, absolute
  path, traversal, symlink escape, required⊄include, unknown recipe, unsafe
  recipe path, bad adapter, bad source, bad Artifactory, credential URL, bad
  version, unknown key

**Approach:** Implement `CatalogueConfig` and nested dataclasses. Write
`load_catalogue_config`: use `tomllib.loads` (stdlib 3.11), then validate in
the 12 steps above. Reuse `agentbundle/build/validate.py` for JSON Schema
validation against `catalogue.schema.json`. Test against inline TOML strings
(no filesystem dependency beyond `tmp_path`).

**Depends on:** T1

---

### T3: catalogue.toml + schema copies + drift test

**Verification mode:** Goal-based check

**Tests:**
- `test_schema_copies_byte_equal` — read both schema files; assert equal
- `test_repo_catalogue_toml_valid` — `load_catalogue_config(REPO_ROOT)`;
  assert no error

**Approach:** (1) Write `catalogue.toml` at repo root with all required sections
(shape from Bucket 3, using actual repo values for paths). (2) Write
`docs/contracts/catalogue.schema.json` as a JSON Schema for the TOML structure.
(3) Copy it to `agentbundle/_data/catalogue.schema.json`. (4) Add a Makefile
`check-contract-drift.py`-style check (or add to existing drift check) and a
pytest test. Set `minimum-agentbundle-version = "0.14.0"` as placeholder.

**Depends on:** T2

---

### T4: CLI stub subcommand groups

**Verification mode:** Goal-based check

**Tests:**
- `test_cli_catalogue_group_help` — subprocess `agentbundle catalogue --help`;
  assert exit non-zero (stub); assert `lint`, `verify`, `build` in output
- `test_cli_lint_packs_help` — subprocess `agentbundle lint packs --help`;
  assert `--root` in output

**Approach:** Edit `agentbundle/cli.py` to add the `catalogue` subparser group
and `lint` subparser group. Add `commands/catalogue_tooling_stub.py`. Update
`_PATH_BEARING_ATTRS` if needed for `--root`. Add stub tests. Run full test
suite to confirm no regressions.

**Depends on:** T1

## Changelog
