"""An undecodable or unparsable bundled contract fails closed, naming its file.

Each load site is exercised with the bundled reader patched to return invalid
TOML or to raise a decode error, and the message must name `_data/<name>`.
"""

from __future__ import annotations

import ast
import importlib
import tarfile
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


# ---- every loader site reaches the shared helpers, and each names the file ----

_PACKAGE = Path(__file__).resolve().parents[2] / "agentbundle"


def _is_read_bundled_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_read_bundled"
    )


def test_no_module_parses_the_bundled_reader_output_directly() -> None:
    offenders: list[str] = []
    for path in sorted(_PACKAGE.rglob("*.py")):
        rel = path.relative_to(_PACKAGE)
        if rel.parts[0] == "_data":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        # The two loader helpers are the one place allowed to parse the
        # reader's output directly; exempt their bodies by name.
        exempt = {
            line
            for fn in ast.walk(tree)
            if isinstance(fn, ast.FunctionDef)
            and rel.as_posix() == "build/main.py"
            and fn.name in {"_load_bundled_toml", "_load_bundled_json"}
            for line in range(fn.lineno, (fn.end_lineno or fn.lineno) + 1)
        }
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            owner = node.func.value
            parses = (
                node.func.attr == "loads"
                and isinstance(owner, ast.Name)
                and owner.id in {"tomllib", "_tomllib", "json"}
            )
            if parses and any(_is_read_bundled_call(arg) for arg in node.args):
                if node.lineno in exempt:
                    continue
                offenders.append(f"{rel}:{node.lineno}")
    assert offenders == []


def _site_scope() -> str:
    from agentbundle import scope

    try:
        scope._load_bundled_contract()
    except ValueError as exc:
        return str(exc)
    return ""


def _site_render() -> str:
    from agentbundle import render

    try:
        render._resolve_contract(None)
    except ValueError as exc:
        return str(exc)
    return ""


def _site_install() -> str:
    from agentbundle.commands import install

    try:
        install._enumerate_dropped_primitives(Path(), "claude-code")
    except ValueError as exc:
        return str(exc)
    return ""


def _site_validate_build() -> str:
    from agentbundle.commands import validate as validate_cmd

    try:
        validate_cmd._load_adapter_contract()
    except ValueError as exc:
        return str(exc)
    return ""


@pytest.mark.parametrize(
    ("site", "name"),
    [
        pytest.param(_site_scope, "adapter.toml", id="scope"),
        pytest.param(_site_render, "adapter.toml", id="render"),
        pytest.param(_site_install, "adapter.toml", id="install"),
        pytest.param(_site_validate_build, "adapter.toml", id="validate"),
    ],
)
@pytest.mark.parametrize("reader", READERS)
def test_loader_sites_name_the_file(patch_reader, reader, site, name: str) -> None:
    patch_reader(reader)
    assert f"_data/{name}" in site()


def _patch_only(monkeypatch, target: str, reader) -> None:
    original = _build_main._read_bundled

    def selective(name: str) -> str:
        return reader(name) if name == target else original(name)

    monkeypatch.setattr(_build_main, "_read_bundled", selective)


@pytest.mark.parametrize("reader", [pytest.param(lambda n: "{not json", id="unparsable"), pytest.param(_bad_bytes, id="undecodable")])
def test_verify_plugin_manifest_step_names_the_file(monkeypatch, reader, tmp_path: Path) -> None:
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "marketplace.json").write_text("{}", encoding="utf-8")
    _patch_only(monkeypatch, "plugin-manifest.derived.schema.json", reader)
    diags = verify._step_plugin_manifests(tmp_path, None, None, tmp_path)
    assert [d.code for d in diags] == ["CAT-V-013"]
    assert "_data/plugin-manifest.derived.schema.json" in diags[0].message


@pytest.mark.parametrize("reader", [pytest.param(lambda n: "{not json", id="unparsable"), pytest.param(_bad_bytes, id="undecodable")])
def test_archive_marketplace_check_names_the_file(monkeypatch, reader, tmp_path: Path) -> None:
    from agentbundle.catalogue_tooling import archive

    _patch_only(monkeypatch, "marketplace-entry.schema.json", reader)
    archive_path = tmp_path / "a.tar"
    payload = tmp_path / "marketplace.json"
    payload.write_text('{"plugins": []}', encoding="utf-8")
    with tarfile.open(archive_path, "w") as tf:
        tf.add(payload, arcname=".claude-plugin/marketplace.json")
        tf.add(payload, arcname="README.json")  # no shared prefix
    with tarfile.open(archive_path) as tf:
        diags = archive._check_marketplace_entries(tf, tf.getmembers())
    assert [d.code for d in diags] == ["CAT-V-ARC-017"]
    assert "_data/marketplace-entry.schema.json" in diags[0].message


_JSON_READERS = [
    pytest.param(lambda n: "{not json", id="unparsable"),
    pytest.param(_bad_bytes, id="undecodable"),
]


@pytest.mark.parametrize("reader", _JSON_READERS)
def test_validate_command_names_the_pack_schema(monkeypatch, reader, tmp_path: Path, capsys) -> None:
    from agentbundle.cli import main as cli_main

    pack = tmp_path / "demo"
    pack.mkdir()
    (pack / "pack.toml").write_text(
        '[pack]\nname = "demo"\nversion = "0.1.0"\ndescription = "d"\n',
        encoding="utf-8",
        newline="\n",
    )
    _patch_only(monkeypatch, "pack.schema.json", reader)
    assert cli_main(["validate", str(pack)]) == 1
    assert "_data/pack.schema.json" in capsys.readouterr().err


@pytest.mark.parametrize("reader", _JSON_READERS)
def test_direct_source_pack_schema_names_the_file(monkeypatch, reader) -> None:
    from agentbundle import direct_source

    _patch_only(monkeypatch, "pack.schema.json", reader)
    with pytest.raises(ValueError, match="_data/pack.schema.json"):
        direct_source._load_pack_schema()


@pytest.mark.parametrize("reader", _JSON_READERS)
def test_profile_schema_names_the_file(monkeypatch, reader, tmp_path: Path) -> None:
    from agentbundle.commands import profile

    profile_file = tmp_path / "demo.toml"
    profile_file.write_text('[profile]\nname = "demo"\n', encoding="utf-8", newline="\n")
    _patch_only(monkeypatch, "profile.schema.json", reader)
    with pytest.raises(profile.ProfileError, match="_data/profile.schema.json"):
        profile._parse_and_validate("demo", profile_file)
