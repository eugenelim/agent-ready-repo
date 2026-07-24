# Spec: Catalogue Tooling — Build and Self-Host

- **Status:** Draft
- **Owner:** eugenelim
- **Initiative:** ini-005 AgentBundle Portable Catalogue Tooling
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ini-005 brief Bucket 7; [`spec/catalogue-tooling-foundation`](../catalogue-tooling-foundation/spec.md)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The foundation spec created `agentbundle/catalogue_tooling/build.py` and
`agentbundle/catalogue_tooling/self_host.py` as stubs. This spec fills
both modules: thin wrappers over `agentbundle.build.main.cmd_build` and
`agentbundle.build.self_host.{cmd_check,cmd_self}` that expose structured
result types, wire the `catalogue build` and `catalogue self-host` CLI
subcommands, move two hard-coded constants to be config-driven via
`catalogue.toml`, and add compat shims with deprecation warnings for the
`python -m agentbundle.build` entry points.

## Boundaries

### Always do

- Implement `build_catalogue(root, output, pack=None, recipe=None) -> BuildResult`
  in `build.py`. Construct an `argparse.Namespace` and delegate to
  `agentbundle.build.main.cmd_build`; read `catalogue.toml` defaults for
  `output` and `recipe` when those arguments are `None`.
- Make `_DIST_BRANCH` and `_MARKETPLACE_DESCRIPTION` in `build/main.py`
  overridable via `catalogue.toml [catalogue.build]` keys
  `claude-plugin-branch` and `marketplace-description`. When `catalogue.toml`
  is absent or the key is absent, existing hardcoded values are used unchanged
  (zero behavioral change for current callers).
- Implement `check_self_host(root) -> SelfHostResult` and
  `write_self_host(root, force=False) -> SelfHostResult` in `self_host.py`.
  Both delegate to `agentbundle.build.self_host.run_self_host`; `check`
  passes `dry_run=True, force=False`; `write` passes `dry_run=False,
  force=force`. Populate `SelfHostResult` from the return code and any
  captured diagnostic output.
- Wire `agentbundle catalogue build` and `agentbundle catalogue self-host`
  CLI subcommands (filling the stubs from the foundation spec) to call
  `build_catalogue` and `check_self_host` / `write_self_host` respectively.
  `catalogue build` flags: `--root`, `--output`, `--pack`, `--recipe`,
  `--format table|json`. `catalogue self-host` flags: `--root`, `--check`,
  `--write`, `--force`, `--format table|json`.
- `--format json`: write one JSON document to stdout (serialised
  `BuildResult` or `SelfHostResult`); progress and warnings to stderr.
  `--format table` (default): human-readable summary to stdout.
- `FORCE=1` environment variable maps to `--write --force` in the Makefile
  shim; the CLI itself does not read `FORCE` directly.
- Add compat shims in `agentbundle/build/__main__.py` (or equivalent):
  - `python -m agentbundle.build build` → `build_catalogue(...)`, print
    deprecation warning to stderr.
  - `python -m agentbundle.build self` → `write_self_host(...)`, print
    deprecation warning to stderr.
  - `python -m agentbundle.build check` → `check_self_host(...)`, print
    deprecation warning to stderr. **This shim preserves the narrow
    self-host-only semantics of the original `cmd_check`; it does NOT
    broaden to `catalogue verify` (18 steps).**
- All outputs are reproducible: same inputs produce byte-identical output.
- No subprocess call from agentbundle to agentbundle.
- All existing tests pass unmodified.

### Ask first

- Adding a `SelfHostResult` field that requires changes to `results.py`
  beyond what the foundation spec defined.
- Expanding `catalogue self-host --check` to run additional drift gates
  beyond the two phases already in `cmd_check`.
- Reading `FORCE` from the environment inside the CLI (vs. Makefile shim only).

### Never do

- Broaden `check_self_host` or the `build check` compat shim to invoke
  `catalogue verify`. The narrow semantics must be preserved.
- Make `catalogue.toml` absence a hard error; it must remain optional.
- Accept absolute recipe paths, path traversal (`..`), or recipe files
  outside the catalogue root.
- Call `cmd_build` or `cmd_self` / `cmd_check` via subprocess.
- Move or rename `agentbundle/build/main.py` or `agentbundle/build/self_host.py`.

## Testing Strategy

- **TDD** for `build_catalogue`: test with a fixture pack tree that the
  existing build tests already exercise; assert `BuildResult.ok` matches
  `cmd_build` exit-0 path.
- **TDD** for config-driven constants: create a `catalogue.toml` fixture
  with custom `claude-plugin-branch` and `marketplace-description`; assert
  the values propagate into the generated artefacts.
- **TDD** for `check_self_host` / `write_self_host`: run against a temp
  working tree; assert `SelfHostResult.ok` is `True` after write.
- **TDD** for compat shims: invoke via `subprocess.run([sys.executable, "-m",
  "agentbundle.build", "check", ...])` against a fixture; assert deprecation
  warning on stderr and exit 0.
- **Goal-based** for CLI wiring: `agentbundle catalogue build --help` and
  `agentbundle catalogue self-host --help` exit non-zero (stub → wired); flag
  names appear in output.
- **Goal-based** for JSON output: `agentbundle catalogue self-host --check
  --format json` outputs valid JSON with `"ok"` key.

## Acceptance Criteria

- [ ] AC1: `build_catalogue(root, output)` calls through to `cmd_build` and
  returns a `BuildResult` with `ok=True` for a valid fixture catalogue.
- [ ] AC2: When `catalogue.toml` contains `claude-plugin-branch = "custom-branch"`,
  generated artefacts reference `"custom-branch"` not `"claude-plugins-dist"`.
- [ ] AC3: When `catalogue.toml` is absent, `_DIST_BRANCH` and
  `_MARKETPLACE_DESCRIPTION` default to existing hardcoded values; all
  existing build tests pass unmodified.
- [ ] AC4: `check_self_host(root)` returns a `SelfHostResult`; `ok` is
  `False` on drift, `True` on clean working tree.
- [ ] AC5: `write_self_host(root)` returns a `SelfHostResult`; subsequent
  `check_self_host` returns `ok=True`.
- [ ] AC6: `agentbundle catalogue build --root . --output dist/` produces the
  same artefacts as the existing `make build` pipeline for the same inputs.
- [ ] AC7: `agentbundle catalogue self-host --check` exits non-zero on a
  drifted tree; `--write` exits 0 after projection; re-running `--check`
  exits 0.
- [ ] AC8: `--format json` outputs a single valid JSON document to stdout;
  all progress lines go to stderr only.
- [ ] AC9: `python -m agentbundle.build check` prints a deprecation warning to
  stderr, delegates to `check_self_host` (NOT `catalogue verify`), and exits
  with the same code as the direct call.
- [ ] AC10: `python -m agentbundle.build self` and `python -m agentbundle.build
  build` each print a deprecation warning to stderr and delegate correctly.
- [ ] AC11: Absolute recipe paths, `../` traversal, and recipe files outside
  the catalogue root are rejected with a clear error message and non-zero exit.
- [ ] AC12: All existing AgentBundle tests pass unmodified.

## Assumptions

1. `SelfHostResult` can be added to `results.py` without changes to the
   foundation spec's exported types (it is a new `CommandResult` subtype).
2. `agentbundle.build.self_host.run_self_host` is importable directly;
   the wrapper does not need to go through `cmd_self` / `cmd_check`.
3. The Makefile already passes `FORCE=1` via `args.force`; the shim does
   not need to parse the environment variable itself.
4. Recipe security (reject absolute paths, traversal, out-of-root files)
   reuses the existing validation logic already present in `build/main.py`.
