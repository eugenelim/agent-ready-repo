"""Generated-output drift checks in verifier step 14."""

import shutil
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling import verify
from agentbundle.catalogue_tooling.build import build_catalogue
from agentbundle.catalogue_tooling.config import load_catalogue_config
from agentbundle.catalogue_tooling.verify import _step_output_drift

FIXTURE = Path(__file__).parents[1] / "fixtures" / "external_catalogue"


def _built_catalogue(tmp_path: Path) -> tuple[Path, object]:
    root = tmp_path / "catalogue"
    shutil.copytree(FIXTURE, root)
    config = load_catalogue_config(root)
    assert config is not None
    result = build_catalogue(root, output=root / "dist")
    assert result.ok
    return root, config


def test_absent_output_directory_passes(tmp_path):
    assert _step_output_drift(tmp_path, None, None, tmp_path / "tmp") == []


def test_modified_projection_is_reported(tmp_path):
    root, config = _built_catalogue(tmp_path)
    generated = next((root / "dist" / "apm").rglob("SKILL.md"))
    generated.write_text("tampered", encoding="utf-8")
    findings = _step_output_drift(root, config, None, tmp_path / "fresh")
    assert any("generated output differs" in item.message for item in findings)


def test_file_only_in_configured_output_is_reported(tmp_path):
    root, config = _built_catalogue(tmp_path)
    stale = root / "dist" / "apm" / "removed-pack" / "stale.txt"
    stale.parent.mkdir()
    stale.write_text("stale", encoding="utf-8")
    findings = _step_output_drift(root, config, None, tmp_path / "fresh")
    assert any(
        item.path == "dist/apm/removed-pack/stale.txt"
        and "stale generated output" in item.message
        for item in findings
    )


def test_nondefault_configured_output_is_used_and_reported(tmp_path):
    root = tmp_path / "catalogue"
    shutil.copytree(FIXTURE, root)
    config_path = root / "catalogue.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'build-output = "dist"', 'build-output = "custom-dist"'
        ),
        encoding="utf-8",
        newline="\n",
    )
    config = load_catalogue_config(root)
    assert config is not None
    result = build_catalogue(root, output=root / "custom-dist")
    assert result.ok
    stale = root / "custom-dist" / "apm" / "removed-pack" / "stale.txt"
    stale.parent.mkdir()
    stale.write_text("stale", encoding="utf-8")
    ignored = root / "dist" / "apm" / "ignored-pack" / "stale.txt"
    ignored.parent.mkdir(parents=True)
    ignored.write_text("ignored", encoding="utf-8")

    findings = _step_output_drift(root, config, None, tmp_path / "fresh")

    assert any(
        item.path == "custom-dist/apm/removed-pack/stale.txt"
        and "stale generated output" in item.message
        for item in findings
    )
    assert all(not (item.path or "").startswith("dist/") for item in findings)


def test_file_only_in_fresh_output_is_reported(tmp_path):
    root, config = _built_catalogue(tmp_path)
    missing = root / "dist" / "apm" / "alpha" / "pack.toml"
    missing.unlink()
    findings = _step_output_drift(root, config, None, tmp_path / "fresh")
    assert any(
        item.path == "dist/apm/alpha/pack.toml"
        and "missing generated output" in item.message
        for item in findings
    )


def test_pack_selection_ignores_unrelated_output_drift(tmp_path):
    root, config = _built_catalogue(tmp_path)
    unrelated = root / "dist" / "apm" / "beta" / "pack.toml"
    unrelated.write_text("tampered", encoding="utf-8")
    assert _step_output_drift(root, config, "alpha", tmp_path / "fresh") == []


def test_linked_output_root_is_refused(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (tmp_path / "dist").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks not available")
    findings = _step_output_drift(tmp_path, None, None, tmp_path / "fresh")
    assert any("link-like root" in item.message for item in findings)


def test_linked_directory_escape_is_refused_without_exposing_sentinel(tmp_path):
    root, config = _built_catalogue(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel.txt").write_text("outside-secret", encoding="utf-8")
    linked = root / "dist" / "apm" / "escape"
    try:
        linked.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not available")
    findings = _step_output_drift(root, config, None, tmp_path / "fresh")
    assert any(item.path == "dist/apm/escape" for item in findings)
    assert all("outside-secret" not in item.message for item in findings)


def test_linked_directory_loop_terminates_with_finding(tmp_path):
    root, config = _built_catalogue(tmp_path)
    loop = root / "dist" / "apm" / "loop"
    try:
        loop.symlink_to(root / "dist" / "apm", target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not available")
    findings = _step_output_drift(root, config, None, tmp_path / "fresh")
    assert any(item.path == "dist/apm/loop" and "loop" in item.message for item in findings)


def test_junction_like_directory_is_refused(tmp_path, monkeypatch):
    root, config = _built_catalogue(tmp_path)
    junction = root / "dist" / "apm" / "junction"
    junction.mkdir()
    original = verify._path_is_junction
    monkeypatch.setattr(
        verify,
        "_path_is_junction",
        lambda path: path == junction or original(path),
    )
    findings = _step_output_drift(root, config, None, tmp_path / "fresh")
    assert any(item.path == "dist/apm/junction" and "junction" in item.message for item in findings)
