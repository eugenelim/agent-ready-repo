"""Contract-inspector and safe-export tests for bundled public contracts."""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from importlib.resources import files as resource_files
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.contracts_inspector import (
    ContractInfo,
    ContractResourceError,
    export_contracts,
    list_bundled_contracts,
    show_contract,
)


def _expected_names() -> set[str]:
    """Return names from the packaged positive-membership inventory."""
    inventory = resource_files("agentbundle").joinpath(
        "_data", "public-contracts.txt"
    ).read_text(encoding="utf-8")
    return set(inventory.splitlines())


def _bundled_bytes(name: str) -> bytes:
    return resource_files("agentbundle").joinpath("_data", name).read_bytes()


class TestListBundledContracts:
    def test_names_match_packaged_inventory(self) -> None:
        assert {item.name for item in list_bundled_contracts()} == _expected_names()

    def test_contract_info_is_the_promised_string_dataclass(self) -> None:
        assert is_dataclass(ContractInfo)
        assert [(field.name, field.type) for field in fields(ContractInfo)] == [
            ("name", "str"),
            ("kind", "str"),
            ("file", "str"),
        ]

    def test_unlisted_data_file_remains_private(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        data = tmp_path / "_data"
        data.mkdir()
        (data / "public-contracts.txt").write_text(
            "pack.schema.json\n", encoding="utf-8"
        )
        sentinel = '{"sentinel": "bundled-only"}\n'
        (data / "pack.schema.json").write_text(sentinel, encoding="utf-8")
        (data / "skill.schema.json").write_text("{}", encoding="utf-8")
        (data / "future-private.schema.json").write_text("{}", encoding="utf-8")
        monkeypatch.setattr(
            "agentbundle.catalogue_tooling.contracts_inspector._data_dir",
            lambda: data,
        )

        assert [item.name for item in list_bundled_contracts()] == [
            "pack.schema.json"
        ]
        assert show_contract("pack.schema.json") == sentinel
        assert show_contract("skill.schema.json") is None
        output = tmp_path / "export"
        assert export_contracts(output) == ["pack.schema.json"]
        assert {path.name for path in output.iterdir()} == {"pack.schema.json"}
        assert (output / "pack.schema.json").read_text(encoding="utf-8") == sentinel

    def test_kind_mapping_and_order_are_stable(self) -> None:
        contracts = list_bundled_contracts()
        assert [item.name for item in contracts] == sorted(_expected_names())
        # Assert an exhaustive mapping rather than if/elif: an unmatched name
        # would otherwise be silently unasserted, and the `json` fallback for a
        # non-schema `.json` contract is a real third kind (AC7).
        for contract in contracts:
            if contract.name.endswith(".schema.json"):
                expected = "json-schema"
            elif contract.name.endswith(".toml"):
                expected = "toml"
            elif contract.name.endswith(".json"):
                expected = "json"
            else:
                raise AssertionError(f"unclassifiable contract name: {contract.name}")
            assert contract.kind == expected

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("pack.schema.json", "json-schema"),
            ("adapter.toml", "toml"),
            ("plain.json", "json"),
        ],
    )
    def test_kind_covers_every_declared_branch(self, name: str, expected: str) -> None:
        from agentbundle.catalogue_tooling.contracts_inspector import _kind

        assert _kind(name) == expected

    def test_data_only_members_are_not_included(self) -> None:
        names = {item.name for item in list_bundled_contracts()}
        assert "install-defaults.toml" not in names
        assert "install-marker.py" not in names


class TestShowContract:
    def test_returns_content_for_valid_name(self) -> None:
        content = show_contract("pack.schema.json")
        assert content
        json.loads(content)

    @pytest.mark.parametrize(
        "name",
        ["does-not-exist.json", "subdir/pack.schema.json", "subdir\\pack.schema.json"],
    )
    def test_returns_none_for_unknown_or_nested_name(self, name: str) -> None:
        assert show_contract(name) is None

    def test_every_show_matches_bundled_resource(self) -> None:
        for contract in list_bundled_contracts():
            assert show_contract(contract.name) == _bundled_bytes(
                contract.file
            ).decode("utf-8")


class TestExportContracts:
    def test_creates_output_with_ordered_matching_files(self, tmp_path: Path) -> None:
        output = tmp_path / "exported"
        written = export_contracts(output)
        expected = [contract.file for contract in list_bundled_contracts()]
        assert written == expected
        assert {path.name for path in output.iterdir()} == set(expected)
        for filename in written:
            assert (output / filename).read_bytes() == _bundled_bytes(filename)
            assert not (output / filename).is_symlink()

    def test_raises_on_symlink_output(self, tmp_path: Path) -> None:
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        try:
            link.symlink_to(real)
        except OSError:
            pytest.skip("symlink creation unavailable")
        with pytest.raises(ValueError, match="symlink|reparse"):
            export_contracts(link)

    @pytest.mark.parametrize("target_kind", ["dangling", "file"])
    def test_raises_on_non_directory_symlink_output(
        self, tmp_path: Path, target_kind: str
    ) -> None:
        target = tmp_path / "target"
        if target_kind == "file":
            target.write_text("unchanged", encoding="utf-8")
        link = tmp_path / "link"
        try:
            link.symlink_to(target)
        except OSError:
            pytest.skip("symlink creation unavailable")
        with pytest.raises(ValueError, match="symlink|reparse"):
            export_contracts(link)

    def test_accepts_symlinked_ancestor(self, tmp_path: Path) -> None:
        """A symlinked *ancestor* must not block export.

        AC9 scopes link refusal to the output directory itself and to
        existing destinations. Refusing ancestors too breaks ordinary
        paths: /tmp is a symlink to private/tmp on macOS, and a symlinked
        $HOME or checkout does the same on Linux.
        """
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        try:
            link.symlink_to(real, target_is_directory=True)
        except OSError:
            pytest.skip("symlink creation unavailable")

        written = export_contracts(link / "nested")

        assert written == [item.file for item in list_bundled_contracts()]
        for filename in written:
            assert (real / "nested" / filename).read_bytes() == _bundled_bytes(filename)

    def test_exported_files_are_readable(self, tmp_path: Path) -> None:
        """Reference copies must be usable from a shared directory."""
        output = tmp_path / "out"
        export_contracts(output)
        for child in output.iterdir():
            assert child.stat().st_mode & 0o444, f"{child.name} is not readable"

    def test_refuses_late_symlink_destination_before_writing(
        self, tmp_path: Path
    ) -> None:
        output = tmp_path / "out"
        output.mkdir()
        external = tmp_path / "external"
        external.write_text("unchanged", encoding="utf-8")
        contracts = list_bundled_contracts()
        unsafe = contracts[-1].file
        try:
            (output / unsafe).symlink_to(external)
        except OSError:
            pytest.skip("symlink creation unavailable")

        with pytest.raises(ValueError, match="symlink|reparse"):
            export_contracts(output)

        assert external.read_text(encoding="utf-8") == "unchanged"
        assert {path.name for path in output.iterdir()} == {unsafe}

    def test_refuses_late_directory_destination_before_writing(
        self, tmp_path: Path
    ) -> None:
        output = tmp_path / "out"
        output.mkdir()
        contracts = list_bundled_contracts()
        unsafe = contracts[-1].file
        (output / unsafe).mkdir()

        with pytest.raises(ValueError, match="regular file"):
            export_contracts(output)

        assert {path.name for path in output.iterdir()} == {unsafe}


class TestInventoryValidation:
    """The bundled inventory is a parsed input with a parses-or-rejects contract.

    Every rejection branch needs a test: a malformed inventory that slips
    through reaches `Traversable.joinpath` and surfaces as an uncaught
    exception rather than a clean CLI error.
    """

    @staticmethod
    def _install(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, inventory: str
    ) -> None:
        data = tmp_path / "data"
        data.mkdir(exist_ok=True)
        (data / "public-contracts.txt").write_text(inventory, encoding="utf-8")
        monkeypatch.setattr(
            "agentbundle.catalogue_tooling.contracts_inspector._data_dir",
            lambda: data,
        )

    @pytest.mark.parametrize(
        ("label", "inventory"),
        [
            ("unsorted", "b.json\na.json\n"),
            ("duplicate", "a.json\na.json\n"),
            ("nested", "subdir/x.json\n"),
            ("backslash", "subdir\\x.json\n"),
            ("parent", "..\n"),
            ("dot", ".\n"),
            ("wrong-extension", "x.md\n"),
            ("control-character", "a\x01.json\n"),
            ("windows-reserved", "CON.json\n"),
        ],
    )
    def test_rejects_malformed_inventory(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        label: str,
        inventory: str,
    ) -> None:
        self._install(monkeypatch, tmp_path, inventory)
        with pytest.raises(ContractResourceError):
            list_bundled_contracts()

    def test_rejects_empty_inventory(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An empty inventory means a truncated wheel, not zero contracts."""
        self._install(monkeypatch, tmp_path, "")
        with pytest.raises(ContractResourceError):
            list_bundled_contracts()

    def test_nul_in_name_does_not_escape_as_valueerror(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install(monkeypatch, tmp_path, "a\x00.json\n")
        with pytest.raises(ContractResourceError):
            show_contract("a\x00.json")
