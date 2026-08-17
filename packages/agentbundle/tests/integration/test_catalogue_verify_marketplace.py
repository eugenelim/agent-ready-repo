"""Configured marketplace source checks in verifier step 12."""

from types import SimpleNamespace

import pytest
from agentbundle.catalogue_tooling.verify import _step_marketplace


def test_absent_marketplace_passes(tmp_path):
    assert _step_marketplace(tmp_path, None, None, tmp_path / "tmp") == []


def test_malformed_marketplace_is_reported(tmp_path):
    target = tmp_path / ".claude-plugin" / "marketplace.json"
    target.parent.mkdir()
    target.write_text("{", encoding="utf-8")
    findings = _step_marketplace(tmp_path, None, None, tmp_path / "tmp")
    assert findings and findings[0].code == "CAT-V-012"


def test_valid_marketplace_passes(tmp_path):
    target = tmp_path / ".claude-plugin" / "marketplace.json"
    target.parent.mkdir()
    target.write_text('{"plugins": []}', encoding="utf-8")
    assert _step_marketplace(tmp_path, None, None, tmp_path / "tmp") == []


def test_configured_marketplace_path_is_honoured(tmp_path):
    target = tmp_path / "metadata" / "plugins.json"
    target.parent.mkdir()
    target.write_text("{", encoding="utf-8")
    config = SimpleNamespace(paths=SimpleNamespace(marketplace="metadata/plugins.json"))
    findings = _step_marketplace(tmp_path, config, None, tmp_path / "tmp")
    assert findings[0].code == "CAT-V-012"
    assert findings[0].path == "metadata/plugins.json"


def test_linked_marketplace_is_refused(tmp_path):
    outside = tmp_path / "outside.json"
    outside.write_text('{"plugins": []}', encoding="utf-8")
    target = tmp_path / ".claude-plugin" / "marketplace.json"
    target.parent.mkdir()
    try:
        target.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks not available")
    findings = _step_marketplace(tmp_path, None, None, tmp_path / "tmp")
    assert findings[0].code == "CAT-V-012"
    assert "unsafe" in findings[0].message
