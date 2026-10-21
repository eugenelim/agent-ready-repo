# Plan: Catalogue specification manifest and bundled-only contract loading

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** RFC-0109 D1 and S1; `tools/catalogue/sync_contract_inventory.py` and `tools/catalogue/check_contract_parity.py` (the generator and gate being re-based; the gate already loads the generator by explicit path); `build/main.py::_read_bundled` (the shared bundled reader most sites already use); `catalogue_tooling/index_generator.py::_bundled_toml` (an existing bundled-only, fail-closed loader to match); `tools/test_contract_parity.py` (the PR-gated suite the tool tests join); `tests/roster/` plus `tests/AGENTS.md` (roster placement obligations)

## Approach

The manifest loader lives in `sync_contract_inventory.py`, the module the parity
gate already loads by explicit path. Membership then has one definition, and
`tools/test_contract_parity.py`'s staged copy of the two tools keeps working.
The README is restructured into role sections the gate checks. Every contract
load site in the package loses its `contracts/` fallback and fails closed
through `_read_bundled` or its own bundled-only read. The riskiest part is the
relocated-package test, which must import the copy rather than the editable
install.

## Constraints

- RFC-0109 D1: three roles; the manifest is repository-only and not bundled; vendored rows carry their upstream URL for S3.
- RFC-0109 D4: no contract moves on disk.
- RFC-0109 S1 load-path rule and RFC-0076 D1: no catalogue-local file overrides the running CLI.
- `contracts_inspector._inventory_names` rejects a `/` in an inventory name, so `_data/` names for member and bundled rows stay flat.
- `tools/AGENTS.md`: tools stay pure stdlib.
- `tests/AGENTS.md`: a new roster file needs a named build-check step above the bulk step and a `STEP_DISPOSITION` entry.
- `tests/roster/test_agentbundle_governance_markers.py`: shipped package source, messages and package tests cite no RFC, ADR or spec identifiers.
- `packages/AGENTS.md`: package tests must not read repository paths. They copy the installed package from `agentbundle.__file__`, which the sdist re-run also has.
- `tests/roster/test_contract_backward_registry.py` pins the README's three-cell `REGISTRY.md` row and the registry's pair set.

## Construction tests

The roster test in T4 spans T1–T3: it reads the manifest (T1) and drives the
load sites T3 changes.

## Durable-output map

| Spec durable output | Task |
| --- | --- |
| `contracts/catalogue-spec.toml`, `contracts/REGISTRY.md` | T1 |
| `contracts/README.md`, `ARCHITECTURE.md` § 7, `docs/architecture/agentbundle.md` | T2, T3 |
| the six release files in `cut-a-package-release.md`, including a `docs/product/changelog.d/` fragment | T5 |

## Design (LLD)

### Data & schema

```toml
# contracts/catalogue-spec.toml
release = []                       # top level, before any table; append-only from S4

[spec]
name = "agentbundle catalogue specification"

[[contract]]
path = "pack.schema.json"          # relative to contracts/
role = "member"                    # member | bundled | vendored

[[contract]]
path = "vendor/agent-plugins/1.0.0/plugin.schema.json"
role = "vendored"
upstream = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
```

A `member` or `bundled` row's `_data/` copy is `_data/<basename>`. A `vendored`
row's copy is `_data/<path>`, already checked by
`test_distribution_route_contract.py`. The two upstream URLs equal each vendored
file's `$id`.

### Interfaces & contracts

In `sync_contract_inventory.py`:

- `ManifestError(Exception)`.
- `ContractRow(path: str, role: str, upstream: str | None)`, a frozen dataclass with a `data_name` property.
- `load_manifest(contracts_dir: Path) -> list[ContractRow]`, which raises `ManifestError` naming the row index and path, or the `release` key.
- `_render(contracts_dir: Path = _CONTRACTS) -> str`.
- `main(argv, *, contracts_dir=_CONTRACTS, inventory=_INVENTORY)`. Tests pass tmp paths.

In `check_contract_parity.py`: `main(*, contracts_dir, data_dir, readme)` with
repository defaults. It loads `load_manifest` and `_render` by explicit path,
as `_load_render` does today. It adds two rule functions returning failure
strings, `_unlisted_top_level` and `_readme_role_mismatches`.

### Behavior & rules

`contracts/README.md` keeps one three-column table shape (`File | What it pins |
CLI data`) under five `###` headings inside `## Files`:

| Heading | Rows |
| --- | --- |
| `Specification members` | exactly the `member` rows |
| `Bundled, not members` | exactly the `bundled` rows |
| `Vendored` | exactly the `vendored` rows |
| `Vendored notices` | `vendor/agent-plugins/1.0.0/LICENSE.md` and `PROVENANCE.md` |
| `Repository only` | everything else, including `catalogue-spec.toml`, `REGISTRY.md`, `delivery/*` and every `jsonschema/*` file except the bundled `jsonschema/knowledge-captured-observation.schema.json` |

The gate reads the first backticked cell of each table row under the first
three headings. For each role it requires that set to equal the manifest's rows
of that role. It also requires that no `Repository only` or `Vendored notices`
path is a manifest row.

### Load-site inventory (RFC-0109 S1)

Every place `agentbundle` loads a contract, and its rule after S1. Paths are under `packages/agentbundle/agentbundle/`.

| Site | Contract | Rule after S1 |
| --- | --- | --- |
| `build/main.py::_read_bundled` | any | importlib `_data/<name>`. Missing → `FileNotFoundError` naming `_data/<name>`. Repository fallback removed |
| `build/main.py::_bundled_or_repo`, renamed `_bundled_path`, and constants `CONTRACT_PATH`, `ROUTE_CONTRACT_PATH`, `ROUTE_SCHEMA_PATH`, `PACK_SCHEMA_PATH`, `PLUGIN_MANIFEST_SCHEMA_PATH` (used by `build/self_host.py:1466`) | adapter.toml, distribution-routes.\*, pack.schema.json, plugin-manifest.schema.json | the `_data/` path only. Repository fallback removed |
| `_read_bundled` callers: `build/main.py` 277, 851–868, 1043, 1353, 1479, 1529, 1584–1585, 1824, 1836, 2625, 2663; `build/lint_packs.py:503`; `render.py:60`; `scope.py:257–259`; `commands/validate.py:616`; `commands/install.py` (13 calls); `catalogue_tooling/verify.py` 118–122 and 1294–1318; `catalogue_tooling/archive.py:436` | adapter.toml and schemas, the vendored plugin schema | unchanged; inherits the reader's rule |
| `build/__init__.py:46–52` (`build validate`) | adapter.schema.json | `_cmd_validate` runs `from agentbundle.build.main import _read_bundled` at call time instead of using the package-level name bound at `build/__init__.py:29`, so a patch of `agentbundle.build.main._read_bundled` reaches it. Its error message names `_data/adapter.schema.json` and no longer mentions repository contracts |
| `version.py::_read_bundled_adapter_toml_text` | adapter.toml | importlib only. Fallback removed |
| `commands/validate.py::_schema_path` | pack.schema.json | `_data/` path only. Fallback removed |
| `commands/validate.py::_kiro_ide_hook_vocabularies`, `_load_adapter_contract` | adapter.toml | `tomllib.loads(_read_bundled("adapter.toml"))`. The `(None, None)` and `{}` returns for a missing file are removed |
| `catalogue_tooling/config.py::_load_adapter_names` | adapter.toml | `_read_bundled`, with any failure raised as `CatalogueConfigError` naming the file. `except Exception: pass` and the fallback are removed |
| `catalogue_tooling/initialise.py::_load_adapter_names` | adapter.toml | same as above, raised as `ValueError` |
| `catalogue_tooling/lint.py::_load_pack_schema` and `_check_pack_schema_validation` | pack.schema.json | the loader returns the schema or raises, through `_read_bundled`. The check catches the failure and emits CAT-L006 **ERROR** naming `_data/pack.schema.json`; the old `None` → WARN skip is removed. Of the 59 tests in `tests/unit/test_catalogue_tooling_lint.py` that stub the loader with `lambda: None`, the absent-schema test near line 700 stubs a raising loader, and the other 58 stub `lambda: {}` (an empty schema accepts every manifest). That module's docstring (lines 12–15) and the `diagnostics.py:20` comment change with it |
| `build/lint_packs.py::_load_target_vocab` and its caller `cmd_lint_packs` (line 600) | target-vocab.toml | the loader takes no argument and runs `from agentbundle.build.main import _read_bundled` inside the function body, as `catalogue_tooling/verify.py:120` does, so the name is looked up at call time and a patch of `agentbundle.build.main._read_bundled` reaches it. `from agentbundle.build import main` is not used: `build/__init__.py:231` rebinds that package attribute to the `main()` function. A parse failure still returns its closed `(None, error)` naming the file. The ancestor walk and `_VOCAB_RELPATH` are removed |
| `commands/pack_evals.py::ClaudeCodeDetector.project` | adapter.toml | `tomllib.loads(_read_bundled("adapter.toml"))`. The `catalogue_root` parameter stays for its callers |
| `direct_source.py:1009`, `commands/profile.py:69–77`, `catalogue_tooling/index_generator.py:92–110`, `catalogue_tooling/contracts_inspector.py` | pack, profile, catalogue and index schemas; the inventory | already bundled-only; unchanged |
| `catalogue_tooling/config.py::_load_schema` | catalogue.schema.json | importlib read; a missing or unparsable copy raises `CatalogueConfigError` naming `_data/catalogue.schema.json`. The `except Exception: pass` and second `__file__`-relative read are removed |
| `catalogue_tooling/verify.py:1306–1315` (CAT-V-013), `catalogue_tooling/archive.py:436–446` (CAT-V-ARC-017) | plugin and marketplace schemas | unchanged: they turn a `_read_bundled` failure into an ERROR diagnostic that carries the exception text, which now names `_data/<name>` |
| `_data/workspace_status_engine.py:1655–1663, 1825` | adapter.toml digest | excluded by owner decision: hashes for cache identity and applies no rule |
| Not loads: `catalogue_tooling/package.py:55, 276` (archives a catalogue's own folder), `catalogue_tooling/config.py:341` and `lint.py:1536–1546` (config key names), `cli.py:1310` (subcommand name), `build/self_host.py:631` (self-host input glob) | — | — |

### Failure, edge cases & resilience

- The manifest missing or unparsable: both tools exit 1 with the error. There is no fallback to folder position.
- Relocated-package bootstrap: `python -c` (no `-I`, `PYTHONPATH` removed from the environment) inserts `<tmp>/cat/x/y` at `sys.path[0]`, asserts `agentbundle.__file__` is inside the copy, sets `sys.argv`, and calls `runpy.run_module("agentbundle", run_name="__main__")`. Setuptools appends its editable finder after the path finder, so the copy wins. Kill condition: if the assertion fails, the test instead builds a zipapp from the copied package with stdlib `zipapp.create_archive` into `<tmp>/cat/bin/agentbundle.pyz`, which puts four parents above `build/` on `<tmp>/cat`, and runs that.
- Recorder: an audit hook (`sys.addaudithook`) records every `open` event's path resolved against the working directory, and a wrapper on `os.open` records the real path of each returned descriptor (`/proc/self/fd/<n>` on Linux, `fcntl.F_GETPATH` on macOS). Discovery predicate: if `catalogue lint`, `verify` or `index` opens the planted catalogue-root `contracts/` folder for a non-rule purpose, record the site and its purpose in the verification ledger and stop for an owner decision rather than widening the exclusion table.

## Tasks

### T1: Manifest, loader and registry row

**Depends on:** none

**Tests:** in `tools/test_contract_parity.py`
- The repository manifest loads, and its rows equal the spec's 20-row table with an empty `release` (AC 1).
- One parametrized case per AC 2 rejection: missing `release`, non-array `release`, unknown role, duplicate path, absolute path, `..`, backslash, drive letter, a symlink row resolving outside `contracts/` (skipped where symlinks are unavailable), a missing file, a vendored row without an `https://` upstream, a vendored upstream that differs from its `$id`, and colliding basenames. Each asserts the message names the row or key (AC 2).
- `main(["--write"], contracts_dir=tmp, inventory=tmp_inventory)` writes the exact fixture names and omits vendored rows. The real inventory's bytes are unchanged afterwards (AC 3).

```python
# stub: true — red until load_manifest exists
def test_repository_manifest_rows() -> None:
    module = _load_tool(GENERATOR_TOOL)
    rows = module.load_manifest(REPO_ROOT / "contracts")
    assert sum(row.role == "member" for row in rows) == 9
```

**Approach:** add a `contracts/REGISTRY.md` row pairing `contracts/catalogue-spec.toml` with `docs/specs/catalogue-spec-manifest/`.

**Done when:** `python -m pytest tools/test_contract_parity.py -k "manifest or inventory_write" tests/roster/test_contract_backward_registry.py -q` passes. The real-tree gate test in that file stays red until T2 teaches the gate to skip the unbundled manifest; T1 and T2 land in one commit, so no committed state has a red gate.

### T2: Parity gate from the manifest; README by role

**Depends on:** T1

**Tests:** in `tools/test_contract_parity.py`, each building a tmp `contracts/`, `_data/` and README and calling `main(contracts_dir=..., data_dir=..., readme=...)`:
- a missing `_data/` copy fails (AC 5);
- a one-byte difference fails (AC 6);
- a stale inventory fails (AC 7);
- an unlisted top-level contract fails (AC 8);
- a manifest row under the wrong role section, a row missing from its section, and a non-manifest path under `Specification members` each fail (AC 9).
- The existing staged-gate test still passes unchanged.

**Done when:** `python -m pytest tools/test_contract_parity.py tests/roster/test_contract_backward_registry.py -q` passes. Goal-based, once for this PR (AC 4): both tools exit 0 on the tree, and `git diff --exit-code origin/main -- packages/agentbundle/agentbundle/_data/public-contracts.txt` exits 0, recorded in the verification ledger.

### T3: Bundled-only loading at every site

**Depends on:** none

**Tests:**
- `packages/agentbundle/tests/build_pipeline/test_lint_packs.py`:
  - A new test copies the bundled `target-vocab.toml`, changes only every target's `name-max-length` to 4, and plants it as `contracts/target-vocab.toml` in the tmp catalogue and in its parent. `cmd_lint_packs` on a pack whose skill name has 10 characters exits 0 with no finding (AC 10). It is red today, because the ancestor walk picks the planted cap.
  - The six bad-vocab tests (five through `_run_with_bad_vocab`, plus `test_inconsistent_name_pattern_fails_loud`) patch `agentbundle.build.main._read_bundled` to return the bad body for `target-vocab.toml`, and keep their refusal assertions. `test_missing_vocab_file_fails_loud` patches it to raise `FileNotFoundError` naming `_data/target-vocab.toml`. `test_loader_bundled_fallback_succeeds` calls the zero-argument loader and keeps its kiro `name-max-length == 64` check.
- `packages/agentbundle/tests/unit/test_pack_evals_bundled_contract.py` (new): a tmp catalogue root holds a non-TOML `contracts/adapter.toml`. `ClaudeCodeDetector().project(pack, out, catalogue_root=root)` writes the projected skill under `out` (AC 11).
- `packages/agentbundle/tests/integration/test_bundled_contracts_fail_closed.py` (new): copy the installed package to `<tmp>/cat/x/y/agentbundle`, so four parents above `build/` is `<tmp>/cat`. Plant invalid `contracts/adapter.toml`, `contracts/target-vocab.toml` and `contracts/pack.schema.json` in `<tmp>/cat`. Three cases, each removing one `_data/` file from the copy and running the bootstrap in *Failure, edge cases & resilience*. Each exits non-zero with output naming `_data/<name>`: `--version` for `adapter.toml`; a `cmd_lint_packs` call for `target-vocab.toml`; `validate <pack>` for `pack.schema.json`, which exercises the removed `commands/validate.py::_schema_path` fallback (AC 12).
- `packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py`: the absent-schema test asserts CAT-L006 at ERROR naming `_data/pack.schema.json` and `ok is False`. A second case gives an unparsable schema text through a patched `_read_bundled` (AC 13).
- `packages/agentbundle/tests/build_pipeline/test_build_validate_bundled_schema.py` (new): with `agentbundle.build.main._read_bundled` raising for `adapter.schema.json`, `agentbundle.build.main(["validate", <contract>])` exits 1, and stderr names `_data/adapter.schema.json` without the word `repository` (AC 14).
- `packages/agentbundle/tests/unit/test_no_contracts_fallback.py` (new): parse every `.py` under the package except `_data/` with `ast`. Collect every `ast.Constant` string, including f-string parts, that equals `contracts`, starts with `contracts/` or contains `/contracts/`, skipping module, class and function docstrings. Compare against a fixed allow-list of `(file, string, count, reason)`: `catalogue_tooling/package.py` archive inclusion (2), `catalogue_tooling/config.py` configuration key (1), `catalogue_tooling/lint.py` configuration keys (2), `cli.py` subcommand name (1), and `build/self_host.py` input glob (1). The occurrence count per file and string must equal the allow-list exactly, so a second use of an allowed string in the same file fails (AC 15). Red first: before the load-site edits, the scan reports `build/lint_packs.py:50`, `version.py:40`, `commands/validate.py:67, 519, 558`, `catalogue_tooling/config.py:187` (as a count of 2 against an allowance of 1), `catalogue_tooling/initialise.py:106`, `build/main.py:150, 170` and `commands/pack_evals.py:173`.

**Done when:** `python -m pytest packages/agentbundle/tests/build_pipeline/test_lint_packs.py packages/agentbundle/tests/unit/test_pack_evals_bundled_contract.py packages/agentbundle/tests/integration/test_bundled_contracts_fail_closed.py packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py packages/agentbundle/tests/build_pipeline/test_build_validate_bundled_schema.py packages/agentbundle/tests/unit/test_no_contracts_fallback.py -q` passes, and so does the full `packages/agentbundle/tests/` suite.

### T4: Roster load-inventory test

**Depends on:** T1, T3

**Tests:** `tests/roster/test_catalogue_spec_contract_loads.py` (new)
- Run `python -m agentbundle catalogue init` into `<tmp>/parent/cat`. Plant an invalid copy of every manifest contract name under `<tmp>/parent/contracts/` (vendored rows at their `vendor/...` path), and the same under `<tmp>/parent/cat/contracts/` for every command except `package`.
- Run `lint`, `verify`, `package` and `index --dry-run`, each in a fresh subprocess, so no in-process cache hides a load. Each subprocess runs the recorder bootstrap from *Failure, edge cases & resilience*, calls `agentbundle.cli.main`, and writes the recorded real paths as JSON to a file named in its environment.
- A recorded path is a contract read when its basename is a `member` or `bundled` row's `data_name`, or it ends with a `vendored` row's `path`.
- Assert every contract read resolves under the package's `_data/` (AC 16).
- Assert every contract read is a `member` row, or a key of `EXCLUSIONS: dict[str, str]` whose keys are `bundled` or `vendored` manifest rows and whose values come only from `{"host projection", "engine setting", "other record"}` (AC 17). Initial entries: `marketplace-entry.schema.json`, `plugin-manifest.derived.schema.json` and `vendor/agent-plugins/1.0.0/plugin.schema.json` as host projection; `distribution-routes.toml` and `distribution-routes.schema.json` as engine setting.
- Assert each command recorded at least one contract read.

**Approach:** add a named step above the bulk roster step in `.github/workflows/build-check.yml`'s `gate-main` job. In `tools/lint-ci-parity.py`, add its `STEP_DISPOSITION` entry `LOCAL("test-after-build-check")` and add the step name to `_GATE_MAIN_CHECKS`.

**Done when:** the roster file passes, and `python3 tools/lint-ci-parity.py` passes.

### T5: Release files and architecture bullets

**Depends on:** T3

**Tests:** goal-based: `python -m agentbundle --version` prints `agentbundle 0.54.0 (spec 0.18)` (AC 18).

**Done when:**
- The six files in `docs/guides/how-to/cut-a-package-release.md` § Files that move together move from 0.53.2 to 0.54.0: `version.py`, `pyproject.toml`, a `packages/agentbundle/CHANGELOG.md` top entry, a first `README-pypi.md` heading, a `docs/product/changelog.d/` fragment made with `tools/changelog.py new`, and the `expected` pin in `tests/roster/test_okf_catalogue_discovery.py`. That roster test passes.
- The entries name the manifest, the bundled-only load rule, and CAT-L006 becoming an error.
- The `ARCHITECTURE.md` § 7 and `docs/architecture/agentbundle.md` parity bullets name the manifest and the bundled-only rule.
- `tests/roster/test_agentbundle_governance_markers.py` passes.

## Rollout

One PR, reversible. No contract bytes change, `public-contracts.txt` is
unchanged, and nothing is published. A complete install behaves as before,
because every site already resolved to `_data/`. The visible changes are for a
catalogue that planted its own `target-vocab.toml` or `adapter.toml`, which now
has no effect, and for an incomplete install, which now stops with a named
error. The version bump does not imply a release tag.

## Risks

- A test elsewhere may rely on a removed fallback by deleting or patching a `_data/` file. T3's full package-suite run catches it.
- The roster recorder depends on platform descriptor-path lookup. CI runs Linux, where `/proc/self/fd` is available.

## Changelog

- 2026-10-21: spec approved by eugenelim
- 2026-10-21: plan approved by eugenelim
