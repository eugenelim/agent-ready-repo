"""Adapter compatibility checks in verifier step 8."""

from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.verify import _step_adapter_compat


def _pack(root: Path, name: str, contract: str, adapter: str) -> None:
    target = root / "packs" / name
    target.mkdir(parents=True)
    target.joinpath("pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "1.0.0"\n'
        f'[pack.adapter-contract]\nversion = "{contract}"\n'
        '[pack.install]\ndefault-scope = "repo"\nallowed-scopes = ["repo"]\n'
        f'allowed-adapters = ["{adapter}"]\n',
        encoding="utf-8",
    )


def test_known_adapter_passes(tmp_path):
    _pack(tmp_path, "alpha", "0.8", "codex")
    assert _step_adapter_compat(tmp_path, None, None, tmp_path / "tmp") == []


def test_unknown_adapter_is_reported(tmp_path):
    _pack(tmp_path, "alpha", "0.8", "unknown-adapter")
    findings = _step_adapter_compat(tmp_path, None, None, tmp_path / "tmp")
    assert any("unknown allowed adapter" in item.message for item in findings)


def test_legacy_contract_skips_allowed_adapter_check(tmp_path):
    _pack(tmp_path, "legacy", "0.1", "unknown-adapter")
    assert _step_adapter_compat(tmp_path, None, None, tmp_path / "tmp") == []


def test_pack_selection_skips_unrelated_pack(tmp_path):
    _pack(tmp_path, "alpha", "0.8", "codex")
    _pack(tmp_path, "broken", "0.8", "unknown-adapter")
    assert _step_adapter_compat(tmp_path, None, "alpha", tmp_path / "tmp") == []


def test_linked_pack_manifest_is_refused(tmp_path):
    pack = tmp_path / "packs" / "alpha"
    pack.mkdir(parents=True)
    outside = tmp_path / "outside.toml"
    outside.write_text("not valid TOML", encoding="utf-8")
    try:
        (pack / "pack.toml").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks not available")
    findings = _step_adapter_compat(tmp_path, None, None, tmp_path / "tmp")
    assert any(item.code == "CAT-V-008" and "safely" in item.message for item in findings)
