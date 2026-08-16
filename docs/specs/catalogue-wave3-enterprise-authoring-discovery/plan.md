# Plan: catalogue-wave3-enterprise-authoring-discovery

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Mode and declined patterns

Mode: full (new public CLI interface + multi-feature).

**PLAN stub tally:** T2, T3, T4, and T6 have compilable red pytest stubs in their
`Tests:` subsections; T1, T5, and T7 record `no stub (mode)`. (Task-ID bookkeeping
belongs to the plan, not the spec's Testing Strategy — the spec is a contract and
should not ride the plan's revision cycle.)

Declined:
- Tempted to implement `contracts check <file> <schema>` (validates a local file against
  a bundled schema); declining — no caller exists yet; tracked as deferred in spec.
- Tempted to add `next_steps: list[str]` to `InitResult` for JSON consistency with
  `SelfHostedInitResult`; declining — changes the stable result schema for a UX-only
  addition; tracked in spec § Deferred. (Since reversed: the asymmetry cost more
  than the schema change: an automation consumer got next steps from one init verb
  and not the other. Landed in agentbundle 0.36.0 via
  `spec/agentbundle-engine-stragglers`.)
- Tempted to auto-discover contract names from the `contracts/` source directory at
  runtime; declining — the inspector must be air-gapped and `importlib.resources` is the
  correct source. A generated positive inventory is packaged beside the contracts and
  build-time parity is enforced by repository tooling, so unknown `_data` files fail closed.
- Tempted to replace the `catalogue_tooling_stub.py` dispatch; declining — the stub only
  handles unregistered subcommands; `contracts` will be fully registered in `cli.py`.

## Pre-EXECUTE self-coverage checks

- Domain claim: `agentbundle catalogue contracts` namespace is unoccupied. Verified:
  current `cli.py` registered catalogue subcommands are lint, verify, build, self-host,
  package, sync-defaults, init. `contracts` is not in this list.
- Domain claim: `oplog` demonstrates three-level subparsers in the existing CLI.
  Verified: `cli.py` lines ~1175–1187 register `oplog show` and `oplog clear` via
  nested `add_subparsers`.
- Domain claim: the canonical `contracts/` scan currently yields 12 public contracts.
  Verified against their byte-identical `_data/` counterparts at HEAD. The count is
  non-normative; the generated inventory remains the runtime membership authority.
- Resolve-vs-surface disposition: OQ1 (RFC-0076) requires a surface-level spec decision
  (check for conflict) before implementing. Verification at PLAN time is sufficient —
  the spec records the resolution in AC1 and in the RFC.
- Anchor-test sweep: existing exact-content coupling is limited to the authoring-scaffold
  sync test/tool and the AgentBundle version lockstep test. T5 runs the scaffold sync;
  T7 updates both version authorities. No other hash, snapshot, or fixed-count anchor was
  found for the files this plan changes.

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

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/cli.py`

**Tests:** no stub (mode); public help invocations in Done-when.

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
- `packages/agentbundle/agentbundle/safety.py`
- `packages/agentbundle/agentbundle/_data/public-contracts.txt` (generated)
- `packages/agentbundle/tests/unit/test_catalogue_wave3_contracts_inspector.py` (new)
- `tools/catalogue/sync_contract_inventory.py` (new)
- `tools/catalogue/check_contract_parity.py`
- `tools/test_contract_parity.py`
- `packages/agentbundle/tests/unit/test_safety.py`
- `packages/agentbundle/agentbundle/build/projection_io.py`

**Depends on:** none

**Tests (write these red first):**

`stub: true`

```python
# test_catalogue_wave3_contracts_inspector.py
# Generated at PLAN; these assertions compile but import a not-yet-present module.

from pathlib import Path
from importlib.resources import files as resource_files
import pytest
from agentbundle.catalogue_tooling.contracts_inspector import (
    ContractInfo, list_bundled_contracts, show_contract, export_contracts,
)

# Derive expected names from contracts/ (canonical authority) rather than a
# frozen set. _data/-only files (install-defaults.toml, install-marker.py) and
# the catalogue-scaffold/ subdirectory are not public contracts.
_DATA_ONLY = {"install-defaults.toml", "install-marker.py"}

def _expected_names() -> set:
    """Return public contract names from the packaged positive inventory.

    Reads `_data/public-contracts.txt`, NOT the checkout's contracts/
    directory: the shipped sdist suite must not depend on checkout files.
    Repo-owned tools/test_contract_parity.py owns the contracts/ comparison.
    """
    inventory = resource_files("agentbundle").joinpath(
        "_data", "public-contracts.txt"
    ).read_text(encoding="utf-8")
    return set(inventory.splitlines())


def _bundled_bytes(name: str) -> bytes:
    return resource_files("agentbundle").joinpath("_data", name).read_bytes()

# STUB: AC6, AC7 — public membership comes from the generated positive inventory
class TestListBundledContracts:
    def test_returns_at_least_one_contract(self):
        result = list_bundled_contracts()
        assert len(result) >= 1

    def test_names_match_contracts_directory(self):
        names = {c.name for c in list_bundled_contracts()}
        assert names == _expected_names()

    def test_unlisted_data_file_remains_private(self, tmp_path, monkeypatch):
        data = tmp_path / "_data"
        data.mkdir()
        names = ["pack.schema.json"]
        (data / "public-contracts.txt").write_text(
            "\n".join(names) + "\n", encoding="utf-8"
        )
        sentinel = '{"sentinel": "bundled-only"}\n'
        (data / "pack.schema.json").write_text(sentinel, encoding="utf-8")
        (data / "skill.schema.json").write_text("{}", encoding="utf-8")
        (data / "future-private.schema.json").write_text("{}", encoding="utf-8")
        monkeypatch.setattr(
            "agentbundle.catalogue_tooling.contracts_inspector._data_dir",
            lambda: data,
        )
        assert [item.name for item in list_bundled_contracts()] == names
        assert show_contract("pack.schema.json") == sentinel
        assert show_contract("skill.schema.json") is None
        out = tmp_path / "export"
        assert export_contracts(out) == names
        assert {path.name for path in out.iterdir()} == set(names)
        assert (out / "pack.schema.json").read_text(encoding="utf-8") == sentinel

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

# STUB: AC8, AC10 — show is inventory-bounded and reads bundled UTF-8 content
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

    def test_every_show_matches_bundled_resource(self):
        for contract in list_bundled_contracts():
            assert show_contract(contract.name) == _bundled_bytes(
                contract.file
            ).decode("utf-8")

# STUB: AC9 — export preflights all names and writes through no-follow primitives
class TestExportContracts:
    def test_creates_output_dir(self, tmp_path):
        out = tmp_path / "exported"
        export_contracts(out)
        assert out.is_dir()

    def test_writes_expected_files(self, tmp_path):
        out = tmp_path / "out"
        written = export_contracts(out)
        expected = [contract.file for contract in list_bundled_contracts()]
        assert written == expected
        assert {path.name for path in out.iterdir()} == set(expected)

    def test_content_matches_show(self, tmp_path):
        out = tmp_path / "out"
        written = export_contracts(out)
        for fname in written:
            disk = (out / fname).read_bytes()
            assert disk == _bundled_bytes(fname)

    def test_no_symlinks_in_output(self, tmp_path):
        out = tmp_path / "out"
        export_contracts(out)
        for f in out.iterdir():
            assert not f.is_symlink()

    def test_raises_on_symlink_target(self, tmp_path):
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        try:
            link.symlink_to(real)
        except OSError:
            pytest.skip("symlink creation unavailable")
        with pytest.raises(ValueError, match="symlink"):
            export_contracts(link)

    def test_refuses_late_symlink_destination_before_writing(self, tmp_path):
        out = tmp_path / "out"
        out.mkdir()
        external = tmp_path / "external"
        external.write_text("unchanged", encoding="utf-8")
        contracts = list_bundled_contracts()
        assert len(contracts) > 1
        unsafe = contracts[-1].file
        try:
            (out / unsafe).symlink_to(external)
        except OSError:
            pytest.skip("symlink creation unavailable")
        with pytest.raises(ValueError, match="symlink"):
            export_contracts(out)
        assert external.read_text(encoding="utf-8") == "unchanged"
        assert {path.name for path in out.iterdir()} == {unsafe}

    def test_refuses_late_directory_destination_before_writing(self, tmp_path):
        out = tmp_path / "out"
        out.mkdir()
        contracts = list_bundled_contracts()
        assert len(contracts) > 1
        unsafe = contracts[-1].file
        (out / unsafe).mkdir()
        with pytest.raises(ValueError, match="regular file"):
            export_contracts(out)
        assert {path.name for path in out.iterdir()} == {unsafe}
```

**Approach:**

Define `ContractInfo` as a `dataclasses.dataclass` with `name: str`, `kind: str`, `file: str`.

Add `tools/catalogue/sync_contract_inventory.py` with `--write` and `--check` modes. It
scans canonical top-level `contracts/*.json` and `contracts/*.toml` files, sorts their
names, and renders newline-terminated `_data/public-contracts.txt`. Extend
`check_contract_parity.py` to fail when this inventory differs from the same source scan,
so the existing build gate enforces both byte parity and inventory parity. The inventory
is generated output, not a second hand-authored list.

Use `importlib.resources.files("agentbundle").joinpath("_data")` to load the inventory
and named resources:

```python
from importlib.resources import files as _res_files

def _data_dir():
    return _res_files("agentbundle").joinpath("_data")
```

`list_bundled_contracts()`: read `public-contracts.txt`; validate that every non-empty
line is a flat safe filename ending in `.json` or `.toml`, reject duplicates, sort by name,
and build `ContractInfo` objects. Do not enumerate `_data/`; unlisted files stay private.

`show_contract(name)`: reject names with `/` or `\` (return None, no ValueError); build
the member set from `list_bundled_contracts()` names; return None if not in that set;
read content via `_data_dir().joinpath(name).read_text(encoding="utf-8")`.

`export_contracts(output_dir)`: load all inventory bytes, then call a new sanctioned
`safety.write_files_no_follow(output_dir, files)` batch primitive. That primitive rejects
an output-directory symlink/reparse point, creates the directory if absent, holds its
descriptor open on POSIX, preflights **every** named destination with no following, and
only then creates sibling temporary files and atomically replaces each destination through
the held descriptor. The portability fallback revalidates components and existing targets
with `lstat`; no direct `Path.write_bytes()` call is allowed. Update `safety.py`'s module
contract to name both sanctioned write primitives.

**Done when:** `python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_wave3_contracts_inspector.py -q` exits 0.

---

## T3 — Implement `agentbundle/commands/catalogue_contracts.py` handler

**Verification mode:** TDD

**Depends on:** T1, T2

**Touches:**
- `packages/agentbundle/agentbundle/commands/catalogue_contracts.py` (new)
- `packages/agentbundle/tests/unit/test_catalogue_wave3_contracts_cli.py` (new)

**Tests (write these red first):**

`stub: true`

```python
# test_catalogue_wave3_contracts_cli.py
# Generated at PLAN; invokes the public parser/dispatch boundary.

import contextlib
import io
import json
from importlib.resources import files as resource_files

import pytest

from agentbundle import cli
from agentbundle.catalogue_tooling.contracts_inspector import list_bundled_contracts


def _run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = cli.main(list(argv))
        except SystemExit as exc:
            code = int(exc.code or 0)
    return code, out.getvalue(), err.getvalue()

# STUB: AC11, AC12 — public list output has exact headers and typed JSON values
class TestListSubcommand:
    def test_table_output_contains_all_public_contracts(self):
        rc, out, err = _run("catalogue", "contracts", "list")
        assert rc == 0
        assert err == ""
        lines = out.splitlines()
        assert lines[0].split() == ["NAME", "KIND", "FILE"]
        actual = [tuple(line.split()) for line in lines[1:] if line.strip()]
        expected = [
            (contract.name, contract.kind, contract.file)
            for contract in list_bundled_contracts()
        ]
        assert actual == expected

    def test_json_output_is_array_of_all_contracts(self):
        rc, out, err = _run(
            "catalogue", "contracts", "list", "--format", "json"
        )
        assert rc == 0
        assert err == ""
        data = json.loads(out)
        assert isinstance(data, list)
        assert all(
            all(isinstance(item[key], str) for key in ("name", "kind", "file"))
            for item in data
        )
        actual = [(item["name"], item["kind"], item["file"]) for item in data]
        expected = [
            (contract.name, contract.kind, contract.file)
            for contract in list_bundled_contracts()
        ]
        assert actual == expected

# STUB: AC13, AC14 — public show emits content or a one-line no-traceback error
class TestShowSubcommand:
    def test_valid_name_exits_0(self):
        rc, out, err = _run(
            "catalogue", "contracts", "show", "pack.schema.json"
        )
        assert rc == 0
        expected = resource_files("agentbundle").joinpath(
            "_data", "pack.schema.json"
        ).read_text(encoding="utf-8")
        assert out == expected
        assert err == ""

    def test_invalid_name_exits_1(self):
        rc, out, err = _run(
            "catalogue", "contracts", "show", "does-not-exist.json"
        )
        assert rc == 1
        assert out == ""
        assert "does-not-exist.json" in err
        assert len(err.splitlines()) == 1
        assert "Traceback" not in err

# STUB: AC15, AC16, AC17 — public export manifests files and contains failures
class TestExportSubcommand:
    def test_creates_files_exits_0(self, tmp_path):
        out_dir = tmp_path / "exported"
        rc, out, err = _run(
            "catalogue", "contracts", "export", "--output", str(out_dir)
        )
        assert rc == 0
        files = list(out_dir.iterdir())
        assert len(files) == len(list_bundled_contracts())
        for f in files:
            assert f.name in out
            assert f.read_bytes() == resource_files("agentbundle").joinpath(
                "_data", f.name
            ).read_bytes()
        assert err == (
            "These are reference copies only. They do not override the contracts "
            "used for validation by this agentbundle version.\n"
        )

    def test_symlink_output_exits_2(self, tmp_path):
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        try:
            link.symlink_to(real)
        except OSError:
            pytest.skip("symlink creation unavailable")
        rc, stdout, err = _run(
            "catalogue", "contracts", "export", "--output", str(link)
        )
        assert rc == 2
        assert stdout == ""
        assert "symlink" in err.lower()
        assert "Traceback" not in err
        assert "agentbundle/_data" not in err
        assert "packages/agentbundle" not in err
        assert list(real.iterdir()) == []

    def test_late_symlink_destination_exits_2_without_writes(self, tmp_path):
        out = tmp_path / "out"
        out.mkdir()
        external = tmp_path / "external"
        external.write_text("unchanged", encoding="utf-8")
        contracts = list_bundled_contracts()
        unsafe = contracts[-1].file
        try:
            (out / unsafe).symlink_to(external)
        except OSError:
            pytest.skip("symlink creation unavailable")
        rc, stdout, err = _run(
            "catalogue", "contracts", "export", "--output", str(out)
        )
        assert rc == 2
        assert stdout == ""
        assert "symlink" in err.lower()
        assert "Traceback" not in err
        assert "agentbundle/_data" not in err
        assert "packages/agentbundle" not in err
        assert external.read_text(encoding="utf-8") == "unchanged"
        assert {path.name for path in out.iterdir()} == {unsafe}

    def test_late_directory_destination_exits_2_without_writes(self, tmp_path):
        out = tmp_path / "out"
        out.mkdir()
        contracts = list_bundled_contracts()
        assert len(contracts) > 1
        unsafe = contracts[-1].file
        (out / unsafe).mkdir()
        rc, stdout, err = _run(
            "catalogue", "contracts", "export", "--output", str(out)
        )
        assert rc == 2
        assert stdout == ""
        assert "regular file" in err.lower()
        assert "Traceback" not in err
        assert "agentbundle/_data" not in err
        assert "packages/agentbundle" not in err
        assert {path.name for path in out.iterdir()} == {unsafe}
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

`_run_list`: call `list_bundled_contracts()`; format as a `NAME KIND FILE` table or JSON array.

`_run_show`: call `show_contract(name)`; use `sys.stdout.write(content)` so the full
bundled text is emitted byte-for-byte without an extra newline; return 0 or 1.

`_run_export`: call `export_contracts(Path(args.output))`, which owns all destination
preflight. Catch `ValueError` and `OSError`, emit one concise error without a traceback,
and return 2. On success, print each returned filename to stdout (the file manifest),
print the reference notice to stderr, and return 0.

**Done when:** the test file above passes and direct `python3 -m agentbundle catalogue
contracts ...` smoke invocations match the same stdout/stderr/exit-code contract.

---

## T4 — Update `catalogue_init.py` plain-init next-step output

**Verification mode:** TDD

**Depends on:** none

**Touches:**
- `packages/agentbundle/agentbundle/commands/catalogue_init.py`
- `packages/agentbundle/tests/unit/test_catalogue_wave3_init_nextsteps.py` (new)

**Tests (write these red first):**

`stub: true`

```python
# test_catalogue_wave3_init_nextsteps.py
# Generated at PLAN; imports the existing handler and asserts the new output contract.

import io, json, sys, argparse
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

def _make_success_result(name="test-cat", target="test-cat"):
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

# STUB: AC18, AC19 — successful plain init gains hints without changing JSON
class TestInitNextSteps:
    def test_success_table_output_contains_next_steps(self, tmp_path, capsys):
        from agentbundle.commands import catalogue_init
        target = tmp_path / "cat"
        target.mkdir()
        with patch("agentbundle.catalogue_tooling.initialise.init_catalogue") as mock:
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
        with patch("agentbundle.catalogue_tooling.initialise.init_catalogue") as mock:
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
        with patch("agentbundle.catalogue_tooling.initialise.init_catalogue") as mock:
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
        with patch("agentbundle.catalogue_tooling.initialise.init_catalogue") as mock:
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
- `packages/agentbundle/agentbundle/_data/catalogue-scaffold/manifest.json` (generated)
- `tools/catalogue/sync_authoring_scaffold.py`

**Tests:** no stub (mode); deterministic sync and content-absence checks in Done-when.

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

Run `python3 tools/catalogue/sync_authoring_scaffold.py --write` to sync the scaffold copy.

**Done when:**
```bash
python3 tools/catalogue/sync_authoring_scaffold.py --check  # exit 0
grep -c "Bundled contract inspection" guides/_shared/reference/catalogue-authoring-standards.md  # 1
# Scope the following absence check to section 12.
! sed -n '/^## 12\. Bundled contract inspection/,$p' guides/_shared/reference/catalogue-authoring-standards.md \
  | grep -E '\.github/workflows|make |RFC-|docs/rfc/|ADR|docs/adr/|docs/specs/'
```

---

## T6 — Offline navigation tests

**Verification mode:** TDD

**Depends on:** T2

**Touches:**
- `packages/agentbundle/tests/unit/test_catalogue_wave3_offline_navigation.py` (new)

**Tests (write these red first):**

`stub: true`

```python
# test_catalogue_wave3_offline_navigation.py
# Generated at PLAN; imports the not-yet-present inspector contract.

import socket, contextlib
from pathlib import Path
import pytest
from agentbundle.catalogue_tooling.contracts_inspector import (
    list_bundled_contracts, show_contract, export_contracts,
)

# STUB: AC23 — every positively inventoried contract is readable without sockets
class TestColdReadPath:
    def test_all_listed_names_can_be_shown(self):
        """Full cold-read: list → show each → non-empty content."""
        contracts = list_bundled_contracts()
        assert len(contracts) >= 1  # count derives from contracts/ authority
        for info in contracts:
            content = show_contract(info.name)
            assert content is not None, f"show_contract({info.name!r}) returned None"
            assert len(content) > 0, f"show_contract({info.name!r}) returned empty string"

    def test_no_network_during_cold_read(self, monkeypatch, tmp_path):
        """List + show + export every contract without opening any socket."""
        def no_socket(*args, **kwargs):
            raise AssertionError("Socket opened during cold-read test")

        monkeypatch.setattr(socket, "socket", no_socket)
        contracts = list_bundled_contracts()
        for info in contracts:
            show_contract(info.name)  # must not open network
        written = export_contracts(tmp_path / "offline-export")
        assert written == [contract.file for contract in contracts]

# STUB: AC24 — export bytes equal show bytes and create no links
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
- `packages/agentbundle/CHANGELOG.md`
- `packages/agentbundle/README-pypi.md`
- `docs/product/changelog.md`

**Tests:** no stub (mode); release-document, footer, and regression checks in Done-when.

**Approach:**

1. Current HEAD is AgentBundle `0.33.3`. Bump `pyproject.toml` `version` and
   `version.py` `CLI_VERSION` to `0.34.0`, the next available minor according to
   repository release policy. Verify that no other branch has claimed that minor before
   opening the PR.
2. Add matching package and product changelog entries and update `README-pypi.md` so
   the published package page documents the new contract-inspection surface.
3. Verify OQ1 compatibility: confirm RFC-0076's OQ1 checkbox is already checked and
   the spec's OQ1 resolution paragraph retains the detailed namespace evidence. No RFC
   mutation is required; the RFC intentionally points to the spec as the resolution record.
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
python3 tools/catalogue/sync_contract_inventory.py --check  # exit 0
grep "0.34.0" packages/agentbundle/pyproject.toml   # 1 match
grep "0.34.0" packages/agentbundle/agentbundle/version.py  # 1 match
grep "0.34.0" packages/agentbundle/CHANGELOG.md   # 1+ match (AC26)
grep "0.34.0" packages/agentbundle/README-pypi.md   # 1+ match (AC26)
grep -F -- '- [x] OQ1 resolved' docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md  # 1 match (already checked; verify unchanged)
grep -F '**OQ1 resolution (RFC-0076):**' docs/specs/catalogue-wave3-enterprise-authoring-discovery/spec.md  # 1 match
grep "init-result-json-next-steps" workspace.toml   # 1+ match (pre-existing; no duplicate)
grep "0.34.0" docs/product/changelog.md   # 1+ match (AC26)
git log --format=%B origin/main..HEAD | grep -F 'Engine-Change-RFC: RFC-0076'  # 1+ match
```

## Changelog

- 2026-08-12: Reconstruction pass after the worktree loss. Replayed the recorded
  `apply_patch` stream, then closed the three reviewers' findings: scoped export link
  refusal to the output directory and its destinations (a symlinked *ancestor* such as
  macOS `/tmp` had made the AC15 flow fail outright), made exports `0o644`, added a
  testable branch seam so the non-POSIX write path executes under CI, snapshotted the
  batch `Mapping` order, taught `sync_authoring_scaffold --check` to validate the
  manifest hashes it writes, gave `check_contract_parity` a single shared contract scan,
  and repaired two `workspace.toml` routing edges. Moved the T2 stub's `_expected_names`
  off the checkout `contracts/` directory and onto the packaged inventory, matching the
  spec's amended Testing Strategy.

- 2026-08-12: Rebased the approved plan on AgentBundle 0.33.3, reserved 0.34.0,
  made the 12-contract inventory dynamic, added package release-document coupling,
  and required destination-symlink preflight for safe export.
- 2026-08-12: Pre-execution review replaced fail-open `_data` discovery with a
  generated positive inventory, required descriptor-held no-follow batch writes and
  late-destination atomic-preflight tests, moved CLI assertions to the public parser,
  materialised the PLAN-time red stubs, and tightened release/footer/hub absence gates.
