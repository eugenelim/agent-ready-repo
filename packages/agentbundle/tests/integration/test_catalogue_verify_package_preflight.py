"""Pack preflight checks in verifier step 17."""

from types import SimpleNamespace

import pytest
from agentbundle.catalogue_tooling.verify import _step_package_preflight


def test_missing_pack_manifest_is_reported(tmp_path):
    (tmp_path / "packs" / "alpha").mkdir(parents=True)
    findings = _step_package_preflight(tmp_path, None, None, tmp_path / "tmp")
    assert any("pack.toml is missing" in item.message for item in findings)


def test_malformed_pack_manifest_is_reported(tmp_path):
    pack = tmp_path / "packs" / "alpha"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text("[pack", encoding="utf-8")
    assert _step_package_preflight(tmp_path, None, None, tmp_path / "tmp")


def test_schema_invalid_pack_manifest_is_reported(tmp_path):
    pack = tmp_path / "packs" / "alpha"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "alpha"\nversion = "1.0.0"\nunexpected = true\n',
        encoding="utf-8",
    )
    findings = _step_package_preflight(tmp_path, None, None, tmp_path / "tmp")
    assert any(item.code == "CAT-V-017" and "pack schema" in item.message for item in findings)


def test_minimal_valid_pack_without_readme_passes(tmp_path):
    pack = tmp_path / "packs" / "alpha"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "alpha"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    assert _step_package_preflight(tmp_path, None, None, tmp_path / "tmp") == []


def test_pack_selection_skips_unrelated_missing_manifest(tmp_path):
    (tmp_path / "packs" / "broken").mkdir(parents=True)
    selected = tmp_path / "packs" / "alpha"
    selected.mkdir()
    (selected / "pack.toml").write_text(
        '[pack]\nname = "alpha"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    assert _step_package_preflight(tmp_path, None, "alpha", tmp_path / "tmp") == []


def test_configured_pack_path_is_honoured(tmp_path):
    pack = tmp_path / "custom-packs" / "alpha"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "alpha"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    config = SimpleNamespace(paths=SimpleNamespace(packs="custom-packs"))
    assert _step_package_preflight(tmp_path, config, None, tmp_path / "tmp") == []


def test_linked_pack_manifest_is_refused(tmp_path):
    pack = tmp_path / "packs" / "alpha"
    pack.mkdir(parents=True)
    outside = tmp_path / "outside.toml"
    outside.write_text(
        '[pack]\nname = "alpha"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    try:
        (pack / "pack.toml").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks not available")
    findings = _step_package_preflight(tmp_path, None, None, tmp_path / "tmp")
    assert any(item.code == "CAT-V-017" and "parse error" in item.message for item in findings)
