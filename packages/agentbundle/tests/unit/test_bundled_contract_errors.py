"""An undecodable or unparsable bundled contract fails closed, naming its file.

Each load site is exercised with the bundled reader patched to return invalid
TOML or to raise a decode error, and the message must name `_data/<name>`.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from agentbundle import version
from agentbundle.build import lint_packs
from agentbundle.catalogue_tooling import verify
from agentbundle.commands import pack_evals, validate

_build_main = importlib.import_module("agentbundle.build.main")


def _bad_toml(name: str) -> str:
    return "this is [[[ not toml\n"


def _bad_bytes(name: str) -> str:
    raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")


READERS = [pytest.param(_bad_toml, id="unparsable"), pytest.param(_bad_bytes, id="undecodable")]


@pytest.fixture
def patch_reader(monkeypatch):
    def apply(reader):
        monkeypatch.setattr(_build_main, "_read_bundled", reader)

    return apply


@pytest.mark.parametrize("reader", READERS)
def test_load_bundled_toml_names_the_file(patch_reader, reader) -> None:
    patch_reader(reader)
    with pytest.raises(ValueError, match="_data/adapter.toml"):
        _build_main._load_bundled_toml("adapter.toml")


@pytest.mark.parametrize("reader", READERS)
def test_validate_sites_name_the_file(patch_reader, reader) -> None:
    patch_reader(reader)
    with pytest.raises(ValueError, match="_data/adapter.toml"):
        validate._kiro_ide_hook_vocabularies()
    with pytest.raises(ValueError, match="_data/adapter.toml"):
        validate._load_adapter_contract()


@pytest.mark.parametrize("reader", READERS)
def test_pack_evals_projection_names_the_file(patch_reader, reader, tmp_path: Path) -> None:
    patch_reader(reader)
    with pytest.raises(ValueError, match="_data/adapter.toml"):
        pack_evals.ClaudeCodeDetector().project(tmp_path / "pack", tmp_path / "out")


@pytest.mark.parametrize("reader", READERS)
def test_target_vocab_error_names_the_file(patch_reader, reader) -> None:
    patch_reader(reader)
    vocab, err = lint_packs._load_target_vocab()
    assert vocab is None
    assert err is not None
    assert "_data/target-vocab.toml" in err


@pytest.mark.parametrize("text", ["this is [[[ not toml\n"])
def test_version_reader_failure_names_the_file(monkeypatch, text: str) -> None:
    monkeypatch.setattr(version, "_read_bundled_adapter_toml_text", lambda: text)
    with pytest.raises(ValueError, match="_data/adapter.toml"):
        version._read_spec_version()


def test_version_reader_undecodable_names_the_file(monkeypatch) -> None:
    def raise_decode() -> str:
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr(version, "_read_bundled_adapter_toml_text", raise_decode)
    with pytest.raises(ValueError, match="_data/adapter.toml"):
        version._read_spec_version()


def _missing(name: str) -> str:
    raise FileNotFoundError(f"bundled contract missing: _data/{name}")


@pytest.mark.parametrize(
    "reader",
    [
        pytest.param(_missing, id="missing"),
        pytest.param(lambda name: "{not json", id="unparsable"),
        pytest.param(_bad_bytes, id="undecodable"),
    ],
)
def test_pack_schema_step_reports_an_error(patch_reader, reader, tmp_path: Path) -> None:
    (tmp_path / "packs").mkdir()
    patch_reader(reader)
    config = SimpleNamespace(paths=SimpleNamespace(packs="packs"))
    diags = verify._step_pack_schema(tmp_path, config, None, tmp_path)
    assert [d.code for d in diags] == ["CAT-V-003"]
    assert diags[0].severity.name == "ERROR"
    assert "_data/pack.schema.json" in diags[0].message
