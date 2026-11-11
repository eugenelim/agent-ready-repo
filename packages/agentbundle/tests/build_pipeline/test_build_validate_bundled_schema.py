"""`build validate` fails closed when the bundled adapter schema is missing or unparsable."""

from __future__ import annotations

import importlib
from pathlib import Path

import agentbundle.build as build_pkg
import pytest


def test_missing_bundled_adapter_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    contract = tmp_path / "adapter.toml"
    contract.write_text("[contract]\nversion = \"0.1\"\n", encoding="utf-8", newline="\n")

    def _missing(name: str) -> str:
        raise FileNotFoundError(f"bundled contract missing: _data/{name}")

    build_main = importlib.import_module("agentbundle.build.main")
    monkeypatch.setattr(build_main, "_read_bundled", _missing)
    rc = build_pkg.main(["validate", str(contract)])
    err = capsys.readouterr().err
    assert rc == 1
    assert "_data/adapter.schema.json" in err
    assert "repository" not in err.lower()


def test_unparsable_bundled_adapter_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    contract = tmp_path / "adapter.toml"
    contract.write_text("[contract]\nversion = \"0.1\"\n", encoding="utf-8", newline="\n")
    build_main = importlib.import_module("agentbundle.build.main")
    monkeypatch.setattr(build_main, "_read_bundled", lambda name: "{not json")
    rc = build_pkg.main(["validate", str(contract)])
    err = capsys.readouterr().err
    assert rc == 1
    assert "_data/adapter.schema.json" in err
    assert "Traceback" not in err
