# Plan: Catalogue Tooling — Lint

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

## Approach

Four tasks, sequential: (1) implement `LintRunner` — wraps `lint_packs`
portability checks and adds the new portable catalogue-level rules, returns
`LintResult`; (2) implement JSON and table renderers; (3) wire the CLI stubs
from the foundation spec; (4) add the deprecation shim for the legacy
`python -m agentbundle.build lint-packs` entry point. Each task is
independently testable; T3 and T4 both depend on T1 + T2 being complete.

## Constraints

- ini-005 brief Bucket 5.
- Python 3.11 stdlib only — no new dependencies.
- Must not duplicate portability logic from `agentbundle/build/lint_packs.py`;
  call `lint_pack` / `lint_all_packs` and translate string findings.
- Must not write any file during a lint run (read-only).
- Must not spawn a subprocess to call `agentbundle` from within `agentbundle`.
- Foundation spec must be merged before this spec begins (stubs must exist).
- All existing `lint_packs` tests must continue to pass unmodified.

## Construction tests

Tests live at `packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py`.

- `test_lint_clean_catalogue` — fixture with two packs, no violations; assert
  `result.ok is True` and `result.diagnostics == []`.
- `test_lint_filters_by_pack` — two packs, one dirty; assert pack-filtered
  result contains only the dirty pack's diagnostics.
- One test per AC3 rule (27 tests): fixture that triggers exactly that
  violation; assert `result.diagnostics[0].code == "CAT-Lxxx"`.
- `test_render_json_valid` — call `render_json` on a fixture result; assert
  `json.loads(output)` succeeds and top-level keys match AC4.
- `test_render_json_deterministic` — call `render_json` twice on identical
  input; assert identical strings.
- `test_render_table_groups_by_pack` — dirty result with two packs; assert
  both pack names appear as section headers in output.
- `test_cli_catalogue_lint_clean` — subprocess `agentbundle catalogue lint
  --root <clean-fixture>`; assert exit 0.
- `test_cli_lint_packs_same_result` — subprocess both commands on same dirty
  fixture; assert identical exit code and identical JSON output
  (`--format json`).
- `test_deprecation_shim_stderr` — subprocess `python -m agentbundle.build
  lint-packs --packs-dir <dir>`; assert "deprecated" in stderr.

## Design (LLD)

### `lint_catalogue` entry point

```python
# agentbundle/catalogue_tooling/lint.py

def lint_catalogue(
    root: Path,
    pack: str | None = None,
) -> LintResult:
    """Run all portable catalogue lint rules against `root`.

    When `pack` is given, only diagnostics for that pack are collected;
    catalogue-level rules (CAT-L001, CAT-L002) still run against the full
    catalogue.
    """
```

Internal flow:
1. Load `catalogue.toml` via `config.load_catalogue_config(root)`; on error
   emit `CAT-L001` and return early with `ok=False`.
2. Resolve the packs directory from config (or default `root / "packs"`).
3. Run `_CatalogueRules(root, config).collect()` → catalogue-level diagnostics
   (CAT-L002 through CAT-L021).
4. For each pack dir (or the one named pack): call
   `lint_packs.lint_all_packs(packs_dir)` and translate string findings into
   diagnostics (CAT-L022 through CAT-L027).
5. Run `_PackRules(pack_dir).collect()` for new portable pack-level rules
   (CAT-L003 through CAT-L021 where applicable).
6. Collect, sort by (pack, path, line, col, code), return `LintResult`.

### `_CatalogueRules` (internal class)

Checks that do not require iterating pack directories:
- Validate presence of packs dir and marketplace.json → CAT-L002.
- Scan all pack dirs for `[pack].name` collisions → CAT-L003.
- Validate all `catalogue.toml` configured paths stay inside root → CAT-L021.

### `_PackRules` (internal class)

One instance per pack dir. Methods for each rule (CAT-L004 through CAT-L020):
- `check_dir_name_vs_pack_toml()` → CAT-L004
- `check_pack_toml_parseable()` → CAT-L005
- `check_pack_schema_validation()` → CAT-L006
- `check_plugin_json_parseable()` → CAT-L007
- `check_plugin_json_schema()` → CAT-L008
- `check_name_version_parity()` → CAT-L009
- `check_skills()` → CAT-L010, CAT-L011
- `check_agents()` → CAT-L012
- `check_commands()` → CAT-L013
- `check_hooks()` → CAT-L014
- `check_profiles()` → CAT-L015
- `check_safe_paths()` → CAT-L016
- `check_case_collisions()` → CAT-L017
- `check_primitive_uniqueness()` → CAT-L018
- `check_adapter_names()` → CAT-L019
- `check_scope_values()` → CAT-L020

### `DiagnosticCode` additions (in `diagnostics.py`)

Add `CAT_L001` through `CAT_L027` to the enum with string values
`"CAT-L001"` … `"CAT-L027"`. The foundation spec created the enum with
placeholder codes; this spec fills in the lint codes.

### Renderers

```python
def render_json(result: LintResult) -> str:
    """Return a single valid JSON document. Emits to caller; never prints."""

def render_table(result: LintResult) -> str:
    """Return a grouped plain-text table. Emits to caller; never prints."""
```

`render_json` uses `json.dumps` with `sort_keys=True` for determinism.
Top-level keys: `schema_version` (int 1), `command`, `operation`,
`agentbundle_version`, `catalogue_schema_version`, `ok`, `diagnostics`.

### CLI wiring

In `agentbundle/commands/catalogue_lint.py` (new file; replaces stub):

```python
def run(args) -> int:
    from agentbundle.catalogue_tooling.lint import lint_catalogue, render_json, render_table
    result = lint_catalogue(Path(args.root), pack=getattr(args, "pack", None))
    if getattr(args, "format", "table") == "json":
        print(render_json(result))
    else:
        print(render_table(result), file=sys.stderr)
    return 0 if result.ok else 1
```

Register this handler for both `agentbundle catalogue lint` and
`agentbundle lint packs` in `cli.py`, replacing the stub `set_defaults`.

### Deprecation shim

Add `agentbundle/build/__main__.py`:

```python
import sys, warnings
warnings.warn(
    "agentbundle.build lint-packs is deprecated; use "
    "agentbundle catalogue lint --root <root> instead",
    DeprecationWarning, stacklevel=1,
)
# Print the same string to stderr for non-warnings-aware callers.
print("agentbundle.build lint-packs is deprecated; ...", file=sys.stderr)
# Delegate: reconstruct --root from --packs-dir parent.
...
```

---

## Tasks

### T1: `LintRunner` — diagnostic collection core

**Verification mode:** TDD

**Tests:**
- `test_lint_clean_catalogue`
- `test_lint_filters_by_pack`
- One test per CAT-L001 through CAT-L027 violation (27 tests)

**Approach:** Implement `lint_catalogue`, `_CatalogueRules`, `_PackRules`,
and the `DiagnosticCode` additions. Use `tomllib.loads` for TOML parsing,
`json.loads` for JSON parsing, and the existing `build/validate.py` JSON
Schema validator for schema checks. Translate string findings from
`lint_packs.lint_pack` / `lint_all_packs` into `Diagnostic` objects using a
`_translate_legacy_finding(s: str) -> Diagnostic` helper that pattern-matches
the known finding formats and assigns stable codes. Tests use in-memory fixture
directories built with `tmp_path`.

**Depends on:** catalogue-tooling-foundation merged

---

### T2: JSON and table renderers

**Verification mode:** TDD

**Tests:**
- `test_render_json_valid`
- `test_render_json_deterministic`
- `test_render_table_groups_by_pack`

**Approach:** Implement `render_json` and `render_table` in `lint.py` (or
`_render.py` if the file grows past ~200 lines). `render_json` uses
`json.dumps(data, sort_keys=True, indent=2)`. `render_table` iterates
diagnostics grouped by `diagnostic.pack or "(catalogue)"`, formats each
finding as `[CODE] severity path:line message` under the pack header.

**Depends on:** T1

---

### T3: CLI wiring

**Verification mode:** Goal-based check

**Tests:**
- `test_cli_catalogue_lint_clean`
- `test_cli_lint_packs_same_result`
- `test_cli_format_json_stdout_only` — assert nothing on stdout in table mode;
  one JSON object on stdout in json mode

**Approach:** Create `agentbundle/commands/catalogue_lint.py` with the `run`
function. Edit `agentbundle/cli.py` to replace the `catalogue lint` and `lint
packs` stub `set_defaults` with `catalogue_lint.run`. Add `--pack` argument to
`catalogue lint` subparser. Update `_PATH_BEARING_ATTRS` if needed.

**Depends on:** T2

---

### T4: Deprecation shim

**Verification mode:** Goal-based check

**Tests:**
- `test_deprecation_shim_stderr`
- `test_deprecation_shim_exit_code` — assert exit code matches `catalogue lint`
  on identical packs dir

**Approach:** Add a `lint-packs` deprecation handler to `agentbundle/build/main.py`'s
existing subcommand dispatcher. Parse legacy `--packs-dir`; derive `--root` as
the packs dir's parent. Call `lint_catalogue` directly (no subprocess). Print
deprecation string to stderr before running.

> **File-ownership note:** `build/main.py` is also modified by
> spec/catalogue-tooling-build-self T5 (`build`, `self`, `check` shims). These
> touch different subcommand branches and produce no semantic conflict, but the
> PRs must merge sequentially to avoid a git conflict. lint T4 must merge BEFORE
> build-self T5 when run in parallel development. Build-self T5 is responsible
> for rebasing on top of lint's `build/main.py` changes.

**Depends on:** T3

---

## Changelog
