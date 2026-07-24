# Plan: Catalogue Tooling — Build and Self-Host

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

## Approach

Five tasks in dependency order: (1) `build_catalogue` wrapper + BuildResult
population; (2) config-driven constant override in `build/main.py`; (3)
`check_self_host` / `write_self_host` wrappers; (4) CLI wiring for the two
subcommands; (5) compat shims with deprecation warnings. Tasks 1 and 3 have
no mutual dependency and may be worked in parallel; T2 depends on T1 being
importable but does not require T1's tests to pass first.

## Constraints

- ini-005 brief Bucket 7.
- Python 3.11 stdlib only; no new runtime dependencies.
- Do not move or rename `agentbundle/build/main.py` or `build/self_host.py`.
- `build check` compat shim must map to `check_self_host` (narrow); broadening
  to `catalogue verify` is explicitly out of scope and must not happen.
- `catalogue.toml` absence must remain a no-op (zero behavioral change).
- No subprocess from agentbundle to agentbundle.

## Construction tests

- `test_build_catalogue_ok`: fixture catalogue; assert `BuildResult.ok is True`.
- `test_build_catalogue_config_branch`: `catalogue.toml` fixture with
  `claude-plugin-branch = "test-branch"`; assert generated JSON references
  `"test-branch"`.
- `test_build_catalogue_config_absent_no_change`: no `catalogue.toml`; assert
  `_DIST_BRANCH` value unchanged in generated output.
- `test_check_self_host_clean`: write then check a fixture tree; assert `ok`.
- `test_check_self_host_drift`: mutate a projected file; assert `ok=False`.
- `test_write_self_host_idempotent`: write twice; assert identical outputs.
- `test_compat_shim_check_narrow`: subprocess `python -m agentbundle.build check`;
  assert deprecation on stderr; assert exit matches `check_self_host` directly.
- `test_compat_shim_self_write`: subprocess `python -m agentbundle.build self`;
  assert deprecation on stderr; assert exit 0 on clean tree.
- `test_recipe_path_rejection`: pass absolute path, `../escape`, and
  out-of-root path to `build_catalogue`; assert `ValueError` each time.

## Design (LLD)

### `build.py`

```python
def build_catalogue(
    root: Path,
    output: Path | None = None,
    pack: str | None = None,
    recipe: str | None = None,
) -> BuildResult:
    """Thin wrapper over agentbundle.build.main.cmd_build."""
    config = load_catalogue_config(root)
    if output is None:
        output = root / (config.paths.build_output if config else "dist")
    if recipe is None and config and config.build.recipes:
        recipe = config.build.recipes[0]   # catalogue.toml default
    _validate_recipe_path(root, recipe)  # defined in catalogue_tooling/build.py
    args = Namespace(
        output_dir=str(output),
        packs_dir=str(root / (config.paths.packs if config else "packs")),
        pack=pack,
        recipe=recipe,
    )
    rc = cmd_build(args)
    return BuildResult(ok=(rc == 0), ...)
```

### `build/main.py` constant override

`build_catalogue` calls `load_catalogue_config` before constructing `args`.
When the config is present, it patches the module-level constants before
delegating (module-level assignment, not monkey-patch via importlib):

```python
import agentbundle.build.main as _build_main
if config and config.build.claude_plugin_branch:
    _build_main._DIST_BRANCH = config.build.claude_plugin_branch
if config and config.build.marketplace_description:
    _build_main._MARKETPLACE_DESCRIPTION = config.build.marketplace_description
```

Restore after the call (try/finally) to avoid cross-test pollution.

### `self_host.py`

```python
def check_self_host(root: Path) -> SelfHostResult:
    args = Namespace(output_dir=str(root), packs_dir=str(root / "packs"),
                     dry_run=True, force=False, no_symlink=False)
    rc = cmd_check(args)
    return SelfHostResult(ok=(rc == 0), ...)

def write_self_host(root: Path, force: bool = False) -> SelfHostResult:
    args = Namespace(output_dir=str(root), packs_dir=str(root / "packs"),
                     dry_run=False, force=force, no_symlink=False)
    rc = cmd_self(args)
    return SelfHostResult(ok=(rc == 0), ...)
```

`SelfHostResult` added to `results.py` as a `CommandResult` subtype.

### CLI wiring (`agentbundle/commands/catalogue_build.py`, `catalogue_self_host.py`)

`catalogue build` handler: parse `--root`, `--output`, `--pack`, `--recipe`,
`--format`; call `build_catalogue`; serialise result per `--format`.

`catalogue self-host` handler: require exactly one of `--check` / `--write`
(mutually exclusive group); pass `--force` only with `--write`; call
`check_self_host` or `write_self_host`; serialise result per `--format`.

### Compat shims (`agentbundle/build/__main__.py`)

```python
_DEPRECATIONS = {
    "build": ("agentbundle catalogue build", build_catalogue),
    "self":  ("agentbundle catalogue self-host --write", write_self_host),
    "check": ("agentbundle catalogue self-host --check", check_self_host),
}
```

For each shim: print `DeprecationWarning: ... use '<new>' instead` to stderr;
forward remaining argv as keyword args; exit with result's `ok` code.

---

## Tasks

### T1: `build_catalogue` wrapper + recipe path validation

**Verification mode:** TDD

**Tests:** `test_build_catalogue_ok`, `test_recipe_path_rejection`

**Approach:** Implement `build_catalogue` in `catalogue_tooling/build.py`.
Write `_validate_recipe_path(root: Path, recipe: str | None) -> None` as a new private function in `catalogue_tooling/build.py`. It raises `ValueError` for: `None` or empty string (if recipe explicitly passed), absolute paths, paths containing `../`, and paths that resolve outside `root`. It does NOT need to be added to `build/main.py`. Add
`tests/unit/test_catalogue_tooling_build.py`. Run `pytest -x` to confirm.

**Depends on:** catalogue-tooling-foundation (stubs must exist)

---

### T2: Config-driven constants (`_DIST_BRANCH`, `_MARKETPLACE_DESCRIPTION`)

**Verification mode:** TDD

**Tests:** `test_build_catalogue_config_branch`,
`test_build_catalogue_config_absent_no_change`

**Approach:** Extend `build_catalogue` to read `catalogue.toml` config and
patch the two module-level constants in `agentbundle.build.main` before
calling `cmd_build`, restoring them in a `try/finally`. Test both paths
(config present with custom values; config absent — assert hardcoded values
unchanged). Confirm all existing build tests pass.

**Depends on:** T1

---

### T3: `check_self_host` and `write_self_host` wrappers

**Verification mode:** TDD

**Tests:** `test_check_self_host_clean`, `test_check_self_host_drift`,
`test_write_self_host_idempotent`

**Approach:** Implement both functions in `catalogue_tooling/self_host.py`.
Add `SelfHostResult` to `results.py`. Construct `Namespace` and delegate to
`cmd_check` / `cmd_self` directly (no subprocess). Add tests in
`tests/unit/test_catalogue_tooling_self_host.py`.

**Depends on:** catalogue-tooling-foundation (stubs must exist)

---

### T4: CLI wiring for `catalogue build` and `catalogue self-host`

**Verification mode:** Goal-based check

**Tests:** subprocess `agentbundle catalogue build --help` — assert flags in
output; subprocess `agentbundle catalogue self-host --check --format json
--root .` against fixture — assert valid JSON with `"ok"` key.

**Approach:** Create `agentbundle/commands/catalogue_build.py` and
`catalogue_self_host.py`. Replace stub handlers registered by the foundation
spec in `cli.py`. Add `--check` / `--write` as a mutually exclusive group for
`self-host`; `--force` allowed only with `--write`. JSON path: serialise
result dataclass via `dataclasses.asdict`; write to stdout; all other lines to
stderr.

**Depends on:** T1, T3

---

### T5: Compat shims with deprecation warnings

**Verification mode:** TDD

**Tests:** `test_compat_shim_check_narrow`, `test_compat_shim_self_write`

**Approach:** Extend `agentbundle/build/main.py`'s existing subcommand
dispatcher with deprecation handlers for `build`, `self`, and `check`. Each
handler prints a deprecation string to `sys.stderr` and delegates to the
`catalogue_tooling` function — not to `cmd_build` / `cmd_check` / `cmd_self`
directly. The `check` shim calls `check_self_host`, NOT any broader verify path.
Add subprocess tests asserting the deprecation string on stderr and the correct
exit code.

> **File-ownership note:** `build/main.py` is also modified by
> spec/catalogue-tooling-lint T4 (the `lint-packs` shim). This T5 must merge
> AFTER lint T4 to avoid a git conflict. Rebase on lint's changes before opening
> the PR. This spec's `build/__main__.py` changes are limited to `build`, `self`,
> and `check` subcommands.

**Depends on:** T1, T3, lint T4 merged

---

## Changelog
