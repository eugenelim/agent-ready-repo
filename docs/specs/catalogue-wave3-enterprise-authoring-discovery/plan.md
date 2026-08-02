# Plan: catalogue-wave3-enterprise-authoring-discovery

- **Status:** Drafting
- **Spec:** [`spec.md`](spec.md)

## Mode and declined patterns

Mode: full (new public CLI interface + multi-feature).

Declined:
- Tempted to implement `contracts check <file> <schema>` (validates a local file against
  a bundled schema); declining — no caller exists yet; tracked as deferred in spec.
- Tempted to add `next_steps: list[str]` to `InitResult` for JSON consistency with
  `SelfHostedInitResult`; declining — changes the stable result schema for a UX-only
  addition; tracked as `(deferred: init-result-json-next-steps)` in spec.
- Tempted to auto-discover contract names from the `contracts/` source directory at
  runtime; declining — the inspector must be air-gapped and `importlib.resources` is the
  correct source; build-time parity is enforced by `check_contract_parity.py`.
- Tempted to replace the `catalogue_tooling_stub.py` dispatch; declining — the stub only
  handles unregistered subcommands; `contracts` will be fully registered in `cli.py`.

## Pre-EXECUTE self-coverage checks

- Domain claim: `agentbundle catalogue contracts` namespace is unoccupied. Verified:
  current `cli.py` registered catalogue subcommands are lint, verify, build, self-host,
  package, sync-defaults, init. `contracts` is not in this list.
- Domain claim: `oplog` demonstrates three-level subparsers in the existing CLI.
  Verified: `cli.py` lines ~1175–1187 register `oplog show` and `oplog clear` via
  nested `add_subparsers`.
- Domain claim: 11 public contracts. Verified by comparing `contracts/*.schema.json`,
  `contracts/*.toml` against `_data/*.schema.json`, `_data/*.toml` at HEAD.
  `install-defaults.toml` is `_data/`-only; excluded.
- Resolve-vs-surface disposition: OQ1 (RFC-0076) requires a surface-level spec decision
  (check for conflict) before implementing. Verification at PLAN time is sufficient —
  the spec records the resolution in AC1 and in the RFC.

## Task list

```
T1  CLI registration          Depends on: none
T2  contracts_inspector.py    Depends on: none
T3  catalogue_contracts.py    Depends on: T1, T2
T4  Init next-step output     Depends on: none
T5  Hub section 12            Depends on: none
T6  Offline navigation tests  Depends on: T2
T7  Version + OQ1 + closeout  Depends on: T1–T6
```

Parallel opportunities on first wave: T1, T2, T4, T5 (all independent).

---

## T1 — Register `agentbundle catalogue contracts` CLI subcommand group

**Verification mode:** goal-based

**Touches:** `packages/agentbundle/agentbundle/cli.py`

**Tests:** none (goal-based)

**Approach:**

Within the existing `# --- catalogue <sub> ---` block in `_build_parser()`, add a `contracts`
subcommand after `init`. Wire it as a sub-parser with its own `dest="contracts_sub"` group:

```
contracts_p = cat_subs.add_parser("contracts", help="Inspect contracts bundled with this agentbundle version.")
contracts_subs = contracts_p.add_subparsers(dest="contracts_sub", metavar="<sub>")
contracts_p.set_defaults(func=_lazy("catalogue_contracts"))

# list
_cl_p = contracts_subs.add_parser("list", help="List all bundled contracts.")
_cl_p.add_argument("--format", choices=["table", "json"], default="table")
_cl_p.set_defaults(func=_lazy("catalogue_contracts"))

# show
_cs_p = contracts_subs.add_parser("show", help="Show content of a bundled contract.")
_cs_p.add_argument("name", metavar="<name>", help="Contract name (from 'contracts list').")
_cs_p.set_defaults(func=_lazy("catalogue_contracts"))

# export
_ce_p = contracts_subs.add_parser("export", help="Export all bundled contracts to a directory.")
_ce_p.add_argument("--output", required=True, metavar="<dir>", help="Output directory.")
_ce_p.set_defaults(func=_lazy("catalogue_contracts"))
```

Add `"output"` to `_PATH_BEARING_ATTRS` if not already present (it is: confirmed at line 50).

**Done when:**
```bash
agentbundle catalogue contracts --help  # exit 0, shows list/show/export
agentbundle catalogue contracts list --help  # exit 0, shows --format
agentbundle catalogue contracts show --help  # exit 0, shows <name>
agentbundle catalogue contracts export --help  # exit 0, shows --output
```

---

## T2 — Implement `agentbundle/catalogue_tooling/contracts_inspector.py`

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/agentbundle/catalogue_tooling/contracts_inspector.py` (new)
- `packages/agentbundle/tests/unit/test_catalogue_wave3_contracts_inspector.py` (new)

**Tests (write these red first):**

```python
# test_catalogue_wave3_contracts_inspector.py

from pathlib import Path
import pytest
from agentbundle.catalogue_tooling.contracts_inspector import (
    ContractInfo, list_bundled_contracts, show_contract, export_contracts,
)

# Derive expected names from contracts/ (canonical authority) rather than a
# frozen set. _data/-only files (install-defaults.toml, install-marker.py) and
# the catalogue-scaffold/ subdirectory are not public contracts.
_DATA_ONLY = {"install-defaults.toml", "install-marker.py"}

def _expected_names() -> set:
    """Return the set of public contract names from the contracts/ directory.

    Matches the parity tool: only .json and .toml files (excludes README.md etc.)
    and excludes _data/-only internals.
    """
    contracts_dir = Path(__file__).parent.parent.parent.parent.parent / "contracts"
    return {
        p.name for p in contracts_dir.iterdir()
        if p.is_file()
        and p.suffix in {".json", ".toml"}
        and p.name not in _DATA_ONLY
    }

class TestListBundledContracts:
    def test_returns_at_least_one_contract(self):
        result = list_bundled_contracts()
        assert len(result) >= 1

    def test_names_match_contracts_directory(self):
        names = {c.name for c in list_bundled_contracts()}
        assert names == _expected_names()

    def test_kind_json_schema_for_schema_files(self):
        for c in list_bundled_contracts():
            if c.name.endswith(".schema.json"):
                assert c.kind == "json-schema"

    def test_kind_toml_for_toml_files(self):
        for c in list_bundled_contracts():
            if c.name.endswith(".toml"):
                assert c.kind == "toml"

    def test_install_defaults_not_included(self):
        names = {c.name for c in list_bundled_contracts()}
        assert "install-defaults.toml" not in names

    def test_install_marker_not_included(self):
        names = {c.name for c in list_bundled_contracts()}
        assert "install-marker.py" not in names

class TestShowContract:
    def test_returns_content_for_valid_name(self):
        content = show_contract("pack.schema.json")
        assert content is not None and len(content) > 0

    def test_returns_none_for_unknown_name(self):
        assert show_contract("does-not-exist.json") is None

    def test_returns_none_for_name_with_slash(self):
        assert show_contract("subdir/pack.schema.json") is None

    def test_returns_none_for_name_with_backslash(self):
        assert show_contract("subdir\\pack.schema.json") is None

    def test_pack_schema_is_valid_json(self):
        import json
        content = show_contract("pack.schema.json")
        assert content is not None
        json.loads(content)  # must not raise

class TestExportContracts:
    def test_creates_output_dir(self, tmp_path):
        out = tmp_path / "exported"
        export_contracts(out)
        assert out.is_dir()

    def test_writes_expected_files(self, tmp_path):
        out = tmp_path / "out"
        written = export_contracts(out)
        assert len(written) == len(_expected_names())

    def test_content_matches_show(self, tmp_path):
        out = tmp_path / "out"
        written = export_contracts(out)
        for fname in written:
            disk = (out / fname).read_bytes()
            shown = show_contract(fname)
            assert shown is not None
            assert disk == shown.encode("utf-8")

    def test_no_symlinks_in_output(self, tmp_path):
        out = tmp_path / "out"
        export_contracts(out)
        for f in out.iterdir():
            assert not f.is_symlink()

    def test_raises_on_symlink_target(self, tmp_path):
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real)
        with pytest.raises(ValueError, match="symlink"):
            export_contracts(link)
```

**Approach:**

Define `ContractInfo` as a `dataclasses.dataclass` with `name: str`, `kind: str`, `file: str`.

Derive public contract membership by scanning the bundled `_data/` package directory via
`importlib.resources` and excluding `_data/`-only internals (`install-defaults.toml`,
`install-marker.py`) and the `catalogue-scaffold/` subtree. Do not maintain a second
manually synchronized frozenset — use `contracts/` (via parity tool) as the canonical
authority; the runtime scan of `_data/` (which mirrors `contracts/`) is the air-gapped
equivalent. The explicit exclusion list prevents internal defaults from surfacing as public
contracts when new `_data/`-only files are added.

Define the internal exclusions as a module-level frozenset:
```python
_DATA_ONLY_NAMES: frozenset[str] = frozenset({"install-defaults.toml", "install-marker.py"})
```

Do **not** define a `_PUBLIC_CONTRACTS` frozenset — contract membership is derived at
runtime from the `_data/` bundle so it stays correct when new public contracts are added.

Use `importlib.resources.files("agentbundle").joinpath("_data")` to enumerate and load:

```python
from importlib.resources import files as _res_files

def _data_dir():
    return _res_files("agentbundle").joinpath("_data")
```

`list_bundled_contracts()`: iterate the `_data/` package directory contents; include only
entries whose name ends in `.json` or `.toml`, is not in `_DATA_ONLY_NAMES`, and is not
inside the `catalogue-scaffold/` subtree; sort by name; build and return `ContractInfo` list.

`show_contract(name)`: reject names with `/` or `\` (return None, no ValueError); build
the member set from `list_bundled_contracts()` names; return None if not in that set;
read content via `_data_dir().joinpath(name).read_text(encoding="utf-8")`.

`export_contracts(output_dir)`: check for symlink via `output_dir.is_symlink()` (lstat,
does **not** call `.resolve()` first — `.resolve().is_symlink()` always returns False after
following the symlink); create dir; write each contract; return list of filenames.

**Done when:** `python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_wave3_contracts_inspector.py -q` exits 0.

---

## T3 — Implement `agentbundle/commands/catalogue_contracts.py` handler

**Verification mode:** TDD

**Depends on:** T1, T2

**Touches:**
- `packages/agentbundle/agentbundle/commands/catalogue_contracts.py` (new)
- `packages/agentbundle/tests/unit/test_catalogue_wave3_contracts_cli.py` (new)

**Tests (write these red first):**

```python
# test_catalogue_wave3_contracts_cli.py

import argparse, io, json, sys
from pathlib import Path
from unittest.mock import patch
import pytest

def _make_ns(**kwargs):
    ns = argparse.Namespace()
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns

class TestListSubcommand:
    def test_table_output_contains_all_public_contracts(self, capsys):
        from agentbundle.commands.catalogue_contracts import run
        from agentbundle.catalogue_tooling.contracts_inspector import list_bundled_contracts
        ns = _make_ns(contracts_sub="list", format="table")
        rc = run(ns)
        out = capsys.readouterr().out
        assert rc == 0
        assert "pack.schema.json" in out
        assert out.count("\n") >= 1 + len(list_bundled_contracts())  # header + N data rows

    def test_json_output_is_array_of_all_contracts(self, capsys):
        from agentbundle.commands.catalogue_contracts import run
        from agentbundle.catalogue_tooling.contracts_inspector import list_bundled_contracts
        ns = _make_ns(contracts_sub="list", format="json")
        rc = run(ns)
        out = capsys.readouterr().out
        assert rc == 0
        data = json.loads(out)
        assert isinstance(data, list)
        assert len(data) == len(list_bundled_contracts())
        assert all("name" in item and "kind" in item and "file" in item for item in data)

class TestShowSubcommand:
    def test_valid_name_exits_0(self, capsys):
        from agentbundle.commands.catalogue_contracts import run
        ns = _make_ns(contracts_sub="show", name="pack.schema.json")
        rc = run(ns)
        out = capsys.readouterr().out
        assert rc == 0
        assert len(out) > 0

    def test_invalid_name_exits_1(self, capsys):
        from agentbundle.commands.catalogue_contracts import run
        ns = _make_ns(contracts_sub="show", name="does-not-exist.json")
        rc = run(ns)
        err = capsys.readouterr().err
        assert rc == 1
        assert "does-not-exist.json" in err or "not found" in err.lower()

class TestExportSubcommand:
    def test_creates_files_exits_0(self, tmp_path, capsys):
        from agentbundle.commands.catalogue_contracts import run
        from agentbundle.catalogue_tooling.contracts_inspector import list_bundled_contracts
        out_dir = tmp_path / "exported"
        ns = _make_ns(contracts_sub="export", output=str(out_dir))
        rc = run(ns)
        captured = capsys.readouterr()
        assert rc == 0
        files = list(out_dir.iterdir())
        expected_count = len(list_bundled_contracts())
        assert len(files) == expected_count
        # Each written filename must appear in stdout manifest (AC15)
        for f in files:
            assert f.name in captured.out, f"{f.name!r} missing from stdout manifest"

    def test_prints_reference_notice(self, tmp_path, capsys):
        from agentbundle.commands.catalogue_contracts import run
        ns = _make_ns(contracts_sub="export", output=str(tmp_path / "out"))
        run(ns)
        err = capsys.readouterr().err
        assert "reference copies only" in err.lower()

    def test_symlink_output_exits_2(self, tmp_path, capsys):
        from agentbundle.commands.catalogue_contracts import run
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real)
        ns = _make_ns(contracts_sub="export", output=str(link))
        rc = run(ns)
        assert rc == 2
```

**Approach:**

```python
def run(args: argparse.Namespace) -> int:
    sub = getattr(args, "contracts_sub", None)
    if sub == "list":
        return _run_list(args)
    elif sub == "show":
        return _run_show(args)
    elif sub == "export":
        return _run_export(args)
    else:
        print("agentbundle catalogue contracts: specify a subcommand (list, show, export)", file=sys.stderr)
        return 1
```

`_run_list`: call `list_bundled_contracts()`; format as table (left-padded columns) or JSON array.

`_run_show`: call `show_contract(name)`; print to stdout; return 0 or 1.

`_run_export`: check symlink via `Path(args.output).is_symlink()` (lstat — do **not**
call `.resolve()` first, as `.resolve().is_symlink()` is always False); exit 2 if symlink.
Otherwise call `export_contracts(Path(args.output))`; print each returned filename to
stdout (the file manifest); print reference notice to stderr; return 0.

**Done when:** `python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_wave3_contracts_cli.py -q` exits 0.

---

## T4 — Update `catalogue_init.py` plain-init next-step output

**Verification mode:** TDD

**Depends on:** none

**Touches:**
- `packages/agentbundle/agentbundle/commands/catalogue_init.py`
- `packages/agentbundle/tests/unit/test_catalogue_wave3_init_nextsteps.py` (new)

**Tests (write these red first):**

```python
# test_catalogue_wave3_init_nextsteps.py

import io, json, sys, argparse
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

def _make_success_result(name="test-cat", target="/tmp/test-cat"):
    from agentbundle.catalogue_tooling.results import (
        InitResult, InitCatalogueMeta, InitSummary, InitVerification
    )
    return InitResult(
        ok=True,
        diagnostics=[],
        schema_version=1,
        command="catalogue init",
        operation="init",
        agentbundle_version="9.9.9-test",
        catalogue_schema_version=1,
        dry_run=False,
        target=target,
        catalogue=InitCatalogueMeta(
            name=name, display_name=name, description="",
            owner_name=name, preferred_adapter="claude-code",
            minimum_agentbundle_version="9.9.9-test",
        ),
        files=[],
        verification=InitVerification(ok=True, diagnostic_count=0),
        summary=InitSummary(create=3, already_present=0, conflict=0, total=3),
    )

class TestInitNextSteps:
    def test_success_table_output_contains_next_steps(self, tmp_path, capsys):
        from agentbundle.commands import catalogue_init
        target = tmp_path / "cat"
        target.mkdir()
        with patch("agentbundle.commands.catalogue_init.init_catalogue") as mock:
            mock.return_value = _make_success_result(target=str(target))
            ns = argparse.Namespace(
                preset=None, target=str(target),
                dry_run=False, name=None, display_name=None,
                description=None, owner_name=None, preferred_adapter=None,
                format="table",
            )
            for attr, _ in catalogue_init._SELF_HOSTED_ONLY_FLAGS:
                setattr(ns, attr, None)
            catalogue_init.run(ns)
        err = capsys.readouterr().err
        assert "Next steps" in err

    def test_success_table_mentions_authoring_hub(self, tmp_path, capsys):
        from agentbundle.commands import catalogue_init
        target = tmp_path / "cat"
        target.mkdir()
        with patch("agentbundle.commands.catalogue_init.init_catalogue") as mock:
            mock.return_value = _make_success_result(target=str(target))
            ns = argparse.Namespace(
                preset=None, target=str(target),
                dry_run=False, name=None, display_name=None,
                description=None, owner_name=None, preferred_adapter=None,
                format="table",
            )
            for attr, _ in catalogue_init._SELF_HOSTED_ONLY_FLAGS:
                setattr(ns, attr, None)
            catalogue_init.run(ns)
        err = capsys.readouterr().err
        assert "catalogue-authoring-standards.md" in err

    def test_success_table_mentions_contracts_list(self, tmp_path, capsys):
        from agentbundle.commands import catalogue_init
        target = tmp_path / "cat"
        target.mkdir()
        with patch("agentbundle.commands.catalogue_init.init_catalogue") as mock:
            mock.return_value = _make_success_result(target=str(target))
            ns = argparse.Namespace(
                preset=None, target=str(target),
                dry_run=False, name=None, display_name=None,
                description=None, owner_name=None, preferred_adapter=None,
                format="table",
            )
            for attr, _ in catalogue_init._SELF_HOSTED_ONLY_FLAGS:
                setattr(ns, attr, None)
            catalogue_init.run(ns)
        err = capsys.readouterr().err
        assert "catalogue contracts list" in err

    def test_json_output_unchanged(self, tmp_path, capsys):
        from agentbundle.commands import catalogue_init
        target = tmp_path / "cat"
        target.mkdir()
        with patch("agentbundle.commands.catalogue_init.init_catalogue") as mock:
            mock.return_value = _make_success_result(target=str(target))
            ns = argparse.Namespace(
                preset=None, target=str(target),
                dry_run=False, name=None, display_name=None,
                description=None, owner_name=None, preferred_adapter=None,
                format="json",
            )
            for attr, _ in catalogue_init._SELF_HOSTED_ONLY_FLAGS:
                setattr(ns, attr, None)
            catalogue_init.run(ns)
        out = capsys.readouterr().out
        doc = json.loads(out)
        assert "next_steps" not in doc  # JSON schema unchanged
```

**Approach:**

In `_run_plain` in `catalogue_init.py`, after the `result.ok` branch prints the success
line, add:

```python
if result.ok and not result.dry_run:
    print("", file=sys.stderr)
    print("  Next steps:", file=sys.stderr)
    print("    • See guides/_shared/reference/catalogue-authoring-standards.md "
          "for authoring standards.", file=sys.stderr)
    print("    • Run 'agentbundle catalogue contracts list' to view bundled "
          "contract schemas.", file=sys.stderr)
    print("    • Run 'agentbundle catalogue verify --root .' to validate your "
          "catalogue.", file=sys.stderr)
```

Emit nothing extra in the dry-run success path (dry-run is a preview, not a completed init).

**Done when:** `python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_wave3_init_nextsteps.py -q` exits 0.

---

## T5 — Add section 12 to `catalogue-authoring-standards.md` + scaffold sync

**Verification mode:** goal-based

**Depends on:** none

**Touches:**
- `guides/_shared/reference/catalogue-authoring-standards.md`
- `packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/reference/catalogue-authoring-standards.md`

**Tests:** none (goal-based)

**Approach:**

Append section 12 to `guides/_shared/reference/catalogue-authoring-standards.md` after section 11:

```markdown
---

## 12. Bundled contract inspection

All contracts bundled in the running agentbundle version can be listed, inspected,
and exported without network access.

```bash
agentbundle catalogue contracts list              # list all bundled contracts
agentbundle catalogue contracts show <name>       # print content of a contract
agentbundle catalogue contracts export --output <dir>  # copy all contracts to a directory
```

Exported files are reference copies only — they do not override the contracts used
for validation by this agentbundle version.
```

Run `python3 tools/catalogue/sync_authoring_scaffold.py` to sync the scaffold copy.

**Done when:**
```bash
python3 tools/catalogue/sync_authoring_scaffold.py --check  # exit 0
grep -c "Bundled contract inspection" guides/_shared/reference/catalogue-authoring-standards.md  # 1
```

---

## T6 — Offline navigation tests

**Verification mode:** TDD

**Depends on:** T2

**Touches:**
- `packages/agentbundle/tests/unit/test_catalogue_wave3_offline_navigation.py` (new)

**Tests (write these red first):**

```python
# test_catalogue_wave3_offline_navigation.py

import socket, contextlib
from pathlib import Path
import pytest
from agentbundle.catalogue_tooling.contracts_inspector import (
    list_bundled_contracts, show_contract, export_contracts,
)

class TestColdReadPath:
    def test_all_listed_names_can_be_shown(self):
        """Full cold-read: list → show each → non-empty content."""
        contracts = list_bundled_contracts()
        assert len(contracts) >= 1  # count derives from contracts/ authority
        for info in contracts:
            content = show_contract(info.name)
            assert content is not None, f"show_contract({info.name!r}) returned None"
            assert len(content) > 0, f"show_contract({info.name!r}) returned empty string"

    def test_no_network_during_cold_read(self, monkeypatch):
        """List + show every contract without opening any socket."""
        original_connect = socket.socket.connect

        def no_connect(self, *args, **kwargs):
            raise AssertionError("Network call made during cold-read test")

        monkeypatch.setattr(socket.socket, "connect", no_connect)
        contracts = list_bundled_contracts()
        for info in contracts:
            show_contract(info.name)  # must not open network

class TestExportMatchesShow:
    def test_exported_files_match_show_content(self, tmp_path):
        """Each exported file's bytes match show_contract() for the same name."""
        written = export_contracts(tmp_path)
        assert len(written) >= 1  # count derives from contracts/ authority
        for fname in written:
            disk_bytes = (tmp_path / fname).read_bytes()
            shown = show_contract(fname)
            assert shown is not None
            assert disk_bytes == shown.encode("utf-8"), (
                f"Exported {fname!r} differs from show_contract result"
            )

    def test_no_symlinks_created(self, tmp_path):
        out = tmp_path / "contracts"
        export_contracts(out)
        for f in out.iterdir():
            assert not f.is_symlink(), f"Symlink created in export output: {f}"
```

**Done when:** `python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_wave3_offline_navigation.py -q` exits 0.

---

## T7 — Engine change, version, OQ1 resolution, changelog, regression

**Verification mode:** goal-based

**Depends on:** T1, T2, T3, T4, T5, T6

**Touches:**
- `packages/agentbundle/pyproject.toml`
- `packages/agentbundle/agentbundle/version.py`
- `docs/product/changelog.md`

**Tests:** none (goal-based)

**Approach:**

1. Inspect current HEAD version: `grep '^version' packages/agentbundle/pyproject.toml`.
   Bump `pyproject.toml` `version` and `version.py` `CLI_VERSION` to the next available
   AgentBundle minor version according to repository release policy. Verify that no other
   branch has already claimed that minor before opening the PR.
2. Add changelog entry (match 0.27.0 shape).
3. Verify OQ1 compatibility: confirm RFC-0076 OQ1 checkbox is already checked
   (`- [x] OQ1 resolved in Wave 3 spec`) and that the accepted resolution remains
   compatible with the Wave 3 implementation. No RFC mutation is required — OQ1 was
   resolved at spec approval time.
4. Verify `init-result-json-next-steps` already exists in `workspace.toml [backlog].open`
   (present as of Phase 0 reconciliation, 2026-07-31). Do NOT create a duplicate entry.
   Reference: `{slug = "init-result-json-next-steps", source = "spec/catalogue-wave3-enterprise-authoring-discovery"}`.
5. Commit the new CLI subcommand commits with footer `Engine-Change-RFC: RFC-0076`.
6. Run full regression gates:

**Done when:**
```bash
SKIP_SAST=1 make build-check   # exit 0
python3 -m pytest packages/agentbundle/tests/ -q   # exit 0
python3 tools/catalogue/check_contract_parity.py   # exit 0
python3 tools/catalogue/sync_authoring_scaffold.py --check  # exit 0
# Replace <VER> with the actual version selected
grep "<VER>" packages/agentbundle/pyproject.toml   # 1 match
grep "<VER>" packages/agentbundle/agentbundle/version.py  # 1 match
grep -F '- [x] OQ1 resolved' docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md  # 1 match (already checked; verify unchanged)
grep "init-result-json-next-steps" workspace.toml   # 1+ match (pre-existing; no duplicate)
grep -E "<VER>|\[Unreleased\]" docs/product/changelog.md   # 1+ match (AC26)
```
