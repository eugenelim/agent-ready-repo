# Catalogue command migration guide

Command surface changed in AgentBundle 0.14.0 (Wave 2) through 0.16.0 (Wave 4). This table maps
every old invocation to its canonical replacement.

## Command mapping

| Old command | New command | Notes |
|-------------|-------------|-------|
| `python -m agentbundle.build lint-packs --packs-dir packs` | `agentbundle catalogue lint --root .` | `--root` replaces `--packs-dir` |
| `python -m agentbundle.build build --packs-dir packs --output-dir dist` | `agentbundle catalogue build --root . --output dist` | Same semantics; output dir is now `--output` |
| `python -m agentbundle.build check --packs-dir packs` | `agentbundle catalogue self-host --root . --check` | Renamed to self-host; mode flag explicit |
| `python -m agentbundle.build self --packs-dir packs` | `agentbundle catalogue self-host --root . --write` | Renamed to self-host; mode flag explicit |
| `python -m agentbundle.build self --packs-dir packs --force` | `agentbundle catalogue self-host --root . --write --force` | `--force` preserved |
| `python -m agentbundle.build verify --packs-dir packs` | `agentbundle catalogue verify --root .` | Verb unchanged; `--root` replaces `--packs-dir` |
| `make lint-packs` | `agentbundle catalogue lint --root .` | Makefile target still works; now delegates |
| `make build-self` | `agentbundle catalogue self-host --root . --write` | Makefile target still works |
| `make build-self-dry-run` | `agentbundle catalogue self-host --root . --check` | Makefile target still works |
| `python tools/build_gate_chain.py build-self` | `python tools/repo/build_gate_chain.py build-self` | Shim at old path; prefer new path |
| `python tools/build_gate_chain.py build-check` | `python tools/repo/build_gate_chain.py build-check` | Shim at old path; prefer new path |
| `python tools/pre-pr-catalogue.py` | `python tools/catalogue/pre_pr_catalogue.py` | Shim at old path; prefer new path |

## Makefile variables

The following Makefile variables changed meaning or were added:

| Variable | Old behavior | New behavior |
|----------|-------------|--------------|
| `PACKS_DIR` | Passed to build scripts as pack directory | Ignored (use `--root .` instead) |
| `OUTPUT_DIR` | Passed to build scripts | Still used for `catalogue build --output` |
| `PACK` | _(not supported)_ | Limits build to a single pack (`--pack`) |
| `BUNDLE` | _(not supported)_ | Required for `make package` |
| `RELEASE` | _(not supported)_ | Required for `make package` |
| `CHANNEL` | _(not supported)_ | Required for `make package` |

## Minimum version

The `agentbundle catalogue` sub-command group requires AgentBundle ≥ 0.14.0.
