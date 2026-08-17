"""Plugin-manifest path resolution in `catalogue verify` steps 4 and 5.

Covers `spec/catalogue-verifier-correctness` AC1 and AC2 (plan T1). Both steps
used to probe `<pack>/plugin.json`, but every pack — first-party and scaffolded
alike — keeps the manifest at `<pack>/.claude-plugin/plugin.json`, so the probes
missed on every pack and CAT-V-004 / CAT-V-005 never fired.

Each test that asserts a diagnostic also plants a decoy at the legacy top-level
path, so a regression to the old probe reds the test rather than passing on a
lucky miss.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.verify import (
    _step_plugin_validation,
    _step_version_parity,
)

PACK_TOML = '[pack]\nname = "my-pack"\nversion = "1.0.0"\n'


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _make_pack(
    root: Path,
    *,
    pack_toml: str = PACK_TOML,
    plugin_json: str | None = None,
    legacy_plugin_json: str | None = None,
) -> None:
    """Lay out one pack under `root/packs/my-pack`.

    `plugin_json` lands at the real `.claude-plugin/` location; `legacy_plugin_json`
    at the abandoned top-level path the probes used to read.
    """
    pack_dir = root / "packs" / "my-pack"
    _write(pack_dir / "pack.toml", pack_toml)
    if plugin_json is not None:
        _write(pack_dir / ".claude-plugin" / "plugin.json", plugin_json)
    if legacy_plugin_json is not None:
        _write(pack_dir / "plugin.json", legacy_plugin_json)


def _manifest(name: str = "my-pack", version: str = "1.0.0") -> str:
    return json.dumps({"name": name, "version": version})


# ---------------------------------------------------------------------------
# AC1 — step 4 resolves .claude-plugin/plugin.json
# ---------------------------------------------------------------------------


def test_step4_accepts_manifest_at_claude_plugin_path(tmp_path):
    """A pack with only `.claude-plugin/plugin.json` passes step 4."""
    _make_pack(tmp_path, plugin_json=_manifest())

    assert _step_plugin_validation(tmp_path, None, None, tmp_path) == []


def test_step4_reports_manifest_only_at_legacy_path(tmp_path):
    """A pack with only the abandoned top-level `plugin.json` is a finding."""
    _make_pack(tmp_path, legacy_plugin_json=_manifest())

    result = _step_plugin_validation(tmp_path, None, None, tmp_path)

    assert [d.code for d in result] == ["CAT-V-004"]
    assert result[0].pack == "my-pack"
    assert ".claude-plugin" in result[0].message


def test_step4_allows_pack_with_no_manifest_anywhere(tmp_path):
    """A manifest is optional; only one at the pack root is a finding.

    Verify runs against adopter catalogues, not just this repo's packs, and an
    unconditional missing-manifest error would fail every manifest-less pack —
    including the packaging suite's own fixtures. See AC1.
    """
    _make_pack(tmp_path)

    assert _step_plugin_validation(tmp_path, None, None, tmp_path) == []


def test_step4_reports_stale_root_manifest_beside_a_correct_one(tmp_path):
    """A root copy is a finding even when the canonical manifest is present."""
    _make_pack(
        tmp_path,
        plugin_json=_manifest(),
        legacy_plugin_json=_manifest(name="other-pack", version="9.9.9"),
    )

    result = _step_plugin_validation(tmp_path, None, None, tmp_path)

    assert [d.code for d in result] == ["CAT-V-004"]
    assert "pack root" in result[0].message


def test_step4_reports_malformed_manifest(tmp_path):
    """Unparseable `.claude-plugin/plugin.json` is a finding.

    The decoy at the legacy path is valid JSON: reading it instead would hide
    the parse error, so only the misplacement finding would survive.
    """
    _make_pack(tmp_path, plugin_json="{not json", legacy_plugin_json=_manifest())

    result = _step_plugin_validation(tmp_path, None, None, tmp_path)

    assert [d.code for d in result] == ["CAT-V-004", "CAT-V-004"]
    assert any("pack root" in d.message for d in result)
    assert any("parse error" in d.message for d in result)


def test_step4_refuses_linked_manifest(tmp_path):
    """Step 4 never follows a plugin manifest link outside its pack."""
    _make_pack(tmp_path)
    pack_dir = tmp_path / "packs" / "my-pack"
    outside = tmp_path / "outside.json"
    _write(outside, _manifest())
    plugin_json = pack_dir / ".claude-plugin" / "plugin.json"
    plugin_json.parent.mkdir(parents=True)
    try:
        plugin_json.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks not available")

    result = _step_plugin_validation(tmp_path, None, None, tmp_path)

    assert [diagnostic.code for diagnostic in result] == ["CAT-V-004"]
    assert "source entry is not a regular file" in result[0].message


# ---------------------------------------------------------------------------
# AC2 — step 5 resolves the same path and detects mismatches
# ---------------------------------------------------------------------------


def test_step5_reports_version_mismatch(tmp_path):
    """pack.toml version != manifest version is a finding."""
    _make_pack(
        tmp_path,
        pack_toml='[pack]\nname = "my-pack"\nversion = "2.0.0"\n',
        plugin_json=_manifest(version="1.0.0"),
        legacy_plugin_json=_manifest(version="2.0.0"),
    )

    result = _step_version_parity(tmp_path, None, None, tmp_path)

    assert [d.code for d in result] == ["CAT-V-005"]
    assert "2.0.0" in result[0].message and "1.0.0" in result[0].message


def test_step5_reports_name_mismatch(tmp_path):
    """pack.toml name != manifest name is a finding."""
    _make_pack(
        tmp_path,
        plugin_json=_manifest(name="other-pack"),
        legacy_plugin_json=_manifest(),
    )

    result = _step_version_parity(tmp_path, None, None, tmp_path)

    assert [d.code for d in result] == ["CAT-V-005"]
    assert "other-pack" in result[0].message


def test_step5_clean_when_pair_agrees(tmp_path):
    """Matching name and version yields no diagnostics.

    The decoy at the legacy path disagrees, so reading it would red this test.
    """
    _make_pack(
        tmp_path,
        plugin_json=_manifest(),
        legacy_plugin_json=_manifest(name="other-pack", version="9.9.9"),
    )

    assert _step_version_parity(tmp_path, None, None, tmp_path) == []


@pytest.mark.parametrize("linked_manifest", ["pack.toml", "plugin.json"])
def test_step5_refuses_linked_parity_input(tmp_path, linked_manifest):
    """Step 5 refuses links for both files in the parity comparison."""
    _make_pack(tmp_path, plugin_json=_manifest())
    pack_dir = tmp_path / "packs" / "my-pack"
    if linked_manifest == "pack.toml":
        linked_path = pack_dir / "pack.toml"
        outside = tmp_path / "outside.toml"
        _write(outside, PACK_TOML)
    else:
        linked_path = pack_dir / ".claude-plugin" / "plugin.json"
        outside = tmp_path / "outside.json"
        _write(outside, _manifest())
    linked_path.unlink()
    try:
        linked_path.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks not available")

    result = _step_version_parity(tmp_path, None, None, tmp_path)

    assert [diagnostic.code for diagnostic in result] == ["CAT-V-005"]
    assert "source entry is not a regular file" in result[0].message
