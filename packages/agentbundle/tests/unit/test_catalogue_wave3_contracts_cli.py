"""Public CLI tests for bundled-contract inspection and export."""

from __future__ import annotations

import contextlib
import io
import json
from importlib.resources import files as resource_files
from pathlib import Path

import pytest
from agentbundle import cli
from agentbundle.catalogue_tooling.contracts_inspector import list_bundled_contracts


def _run(*argv: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            code = cli.main(list(argv))
        except SystemExit as exc:
            code = int(exc.code or 0)
    return code, stdout.getvalue(), stderr.getvalue()


@pytest.fixture
def fake_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Install a narrow sentinel inventory that cannot come from source discovery."""
    data = tmp_path / "_data"
    data.mkdir()
    (data / "public-contracts.txt").write_text(
        "pack.schema.json\n", encoding="utf-8"
    )
    (data / "pack.schema.json").write_text(
        '{"sentinel": "bundled-only"}', encoding="utf-8"
    )
    (data / "skill.schema.json").write_text("source-like-private", encoding="utf-8")
    monkeypatch.setattr(
        "agentbundle.catalogue_tooling.contracts_inspector._data_dir",
        lambda: data,
    )
    return data


@pytest.fixture
def missing_listed_resource(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Install a valid inventory whose listed contract resource is absent."""
    data = tmp_path / "incomplete-data"
    data.mkdir()
    (data / "public-contracts.txt").write_text(
        "pack.schema.json\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        "agentbundle.catalogue_tooling.contracts_inspector._data_dir",
        lambda: data,
    )
    return data


@pytest.fixture
def missing_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the inspector at an absent package-data directory."""
    data = tmp_path / "missing-data"
    monkeypatch.setattr(
        "agentbundle.catalogue_tooling.contracts_inspector._data_dir",
        lambda: data,
    )
    return data


class TestListSubcommand:
    def test_table_output_exactly_matches_ordered_contract_triples(self) -> None:
        code, stdout, stderr = _run("catalogue", "contracts", "list")
        assert code == 0
        assert stderr == ""
        lines = stdout.splitlines()
        assert lines[0].split() == ["NAME", "KIND", "FILE"]
        assert [tuple(line.split()) for line in lines[1:] if line.strip()] == [
            (contract.name, contract.kind, contract.file)
            for contract in list_bundled_contracts()
        ]

    def test_json_output_exactly_matches_ordered_contract_triples(self) -> None:
        code, stdout, stderr = _run(
            "catalogue", "contracts", "list", "--format", "json"
        )
        assert code == 0
        assert stderr == ""
        document = json.loads(stdout)
        assert [
            (item["name"], item["kind"], item["file"]) for item in document
        ] == [
            (contract.name, contract.kind, contract.file)
            for contract in list_bundled_contracts()
        ]
        assert all(
            all(isinstance(item[key], str) for key in ("name", "kind", "file"))
            for item in document
        )

    def test_fake_inventory_controls_list_membership(self, fake_data: Path) -> None:
        code, stdout, stderr = _run("catalogue", "contracts", "list")
        assert code == 0
        assert stderr == ""
        assert fake_data.is_dir()
        assert stdout.splitlines()[1].split() == [
            "pack.schema.json",
            "json-schema",
            "pack.schema.json",
        ]


class TestShowSubcommand:
    def test_valid_name_emits_exact_bundled_content(self) -> None:
        code, stdout, stderr = _run(
            "catalogue", "contracts", "show", "pack.schema.json"
        )
        expected = resource_files("agentbundle").joinpath(
            "_data", "pack.schema.json"
        ).read_text(encoding="utf-8")
        assert (code, stdout, stderr) == (0, expected, "")

    def test_fake_inventory_controls_show_bytes(self, fake_data: Path) -> None:
        code, stdout, stderr = _run(
            "catalogue", "contracts", "show", "pack.schema.json"
        )
        assert (code, stdout, stderr) == (0, '{"sentinel": "bundled-only"}', "")
        assert fake_data.is_dir()

    def test_invalid_name_is_one_line_error_without_traceback(self) -> None:
        code, stdout, stderr = _run(
            "catalogue", "contracts", "show", "does-not-exist.json"
        )
        assert code == 1
        assert stdout == ""
        assert "does-not-exist.json" in stderr
        assert len(stderr.splitlines()) == 1
        assert "Traceback" not in stderr


class TestExportSubcommand:
    def test_creates_matching_files_and_exact_notice(self, tmp_path: Path) -> None:
        output = tmp_path / "exported"
        code, stdout, stderr = _run(
            "catalogue", "contracts", "export", "--output", str(output)
        )
        contracts = list_bundled_contracts()
        assert code == 0
        assert stdout.splitlines() == [contract.file for contract in contracts]
        assert stderr == (
            "These are reference copies only. They do not override the contracts "
            "used for validation by this agentbundle version.\n"
        )
        for contract in contracts:
            assert (output / contract.file).read_bytes() == resource_files(
                "agentbundle"
            ).joinpath("_data", contract.file).read_bytes()

    def test_fake_inventory_controls_export(self, tmp_path: Path, fake_data: Path) -> None:
        output = tmp_path / "exported"
        code, stdout, _stderr = _run(
            "catalogue", "contracts", "export", "--output", str(output)
        )
        assert code == 0
        assert stdout == "pack.schema.json\n"
        assert {path.name for path in output.iterdir()} == {"pack.schema.json"}
        assert (output / "pack.schema.json").read_bytes() == (
            fake_data / "pack.schema.json"
        ).read_bytes()

    def test_symlink_output_is_contained(self, tmp_path: Path) -> None:
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        try:
            link.symlink_to(real)
        except OSError:
            pytest.skip("symlink creation unavailable")
        code, stdout, stderr = _run(
            "catalogue", "contracts", "export", "--output", str(link)
        )
        assert code == 2
        assert stdout == ""
        assert "symlink" in stderr.lower() or "reparse" in stderr.lower()
        assert "Traceback" not in stderr
        assert "agentbundle/_data" not in stderr
        assert "packages/agentbundle" not in stderr
        assert list(real.iterdir()) == []

    @pytest.mark.parametrize("unsafe_kind", ["symlink", "directory"])
    def test_late_unsafe_destination_causes_zero_writes(
        self, tmp_path: Path, unsafe_kind: str
    ) -> None:
        output = tmp_path / "out"
        output.mkdir()
        contracts = list_bundled_contracts()
        unsafe = contracts[-1].file
        external = tmp_path / "external"
        if unsafe_kind == "symlink":
            external.write_text("unchanged", encoding="utf-8")
            try:
                (output / unsafe).symlink_to(external)
            except OSError:
                pytest.skip("symlink creation unavailable")
        else:
            (output / unsafe).mkdir()

        code, stdout, stderr = _run(
            "catalogue", "contracts", "export", "--output", str(output)
        )
        assert code == 2
        assert stdout == ""
        assert "Traceback" not in stderr
        assert "agentbundle/_data" not in stderr
        assert "packages/agentbundle" not in stderr
        assert {path.name for path in output.iterdir()} == {unsafe}
        if unsafe_kind == "symlink":
            assert external.read_text(encoding="utf-8") == "unchanged"


@pytest.mark.parametrize(
    ("argv", "expected_code"),
    [
        (("catalogue", "contracts", "list"), 1),
        (("catalogue", "contracts", "show", "pack.schema.json"), 1),
        (
            (
                "catalogue",
                "contracts",
                "export",
                "--output",
                "unused-output",
            ),
            2,
        ),
    ],
)
def test_missing_bundled_resources_are_contained(
    argv: tuple[str, ...], expected_code: int, missing_data: Path, tmp_path: Path
) -> None:
    # Anchor the relative placeholder under tmp_path: it is only safe today
    # because listing raises before any directory is created, so a change in
    # evaluation order would write into the process CWD.
    argv = tuple(
        str(tmp_path / part) if part == "unused-output" else part for part in argv
    )
    code, stdout, stderr = _run(*argv)
    assert missing_data.name not in stderr
    assert code == expected_code
    assert stdout == ""
    assert stderr == "error: bundled contract resources are unavailable\n"
    assert "Traceback" not in stderr


def test_missing_listed_resource_is_contained_for_show_and_export(
    tmp_path: Path, missing_listed_resource: Path
) -> None:
    invocations = [
        (1, ("catalogue", "contracts", "show", "pack.schema.json")),
        (
            2,
            (
                "catalogue",
                "contracts",
                "export",
                "--output",
                str(tmp_path / "exported"),
            ),
        ),
    ]
    for expected_code, argv in invocations:
        code, stdout, stderr = _run(*argv)
        assert code == expected_code
        assert stdout == ""
        assert stderr == "error: bundled contract resources are unavailable\n"
        assert "Traceback" not in stderr
        assert str(missing_listed_resource) not in stderr
