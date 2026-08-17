"""Profile schema and reference checks in verifier step 6."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from agentbundle.catalogue_tooling import verify
from agentbundle.catalogue_tooling.verify import _step_profiles


def _profile(root: Path, body: str) -> None:
    (root / "profiles").mkdir(exist_ok=True)
    (root / "profiles" / "example.toml").write_text(body, encoding="utf-8")


def _config(*, profiles: str = "profiles", packs: str = "packs"):
    return SimpleNamespace(paths=SimpleNamespace(profiles=profiles, packs=packs))


def test_valid_profile_passes(tmp_path):
    (tmp_path / "packs" / "alpha").mkdir(parents=True)
    _profile(
        tmp_path,
        'scope = "repo"\ndescription = "Example"\n[[packs]]\npack = "alpha"\n',
    )
    assert _step_profiles(tmp_path, None, None, tmp_path / "tmp") == []


def test_configured_profile_and_pack_paths_are_honoured(tmp_path):
    (tmp_path / "custom-packs" / "alpha").mkdir(parents=True)
    profiles = tmp_path / "custom-profiles"
    profiles.mkdir()
    profiles.joinpath("example.toml").write_text(
        'scope = "repo"\ndescription = "Example"\n[[packs]]\npack = "alpha"\n',
        encoding="utf-8",
    )
    assert (
        _step_profiles(
            tmp_path,
            _config(profiles="custom-profiles", packs="custom-packs"),
            None,
            tmp_path / "tmp",
        )
        == []
    )


def test_schema_violation_is_reported(tmp_path):
    _profile(tmp_path, 'description = "Missing scope"\npacks = []\n')
    assert _step_profiles(tmp_path, None, None, tmp_path / "tmp")


def test_missing_pack_reference_is_reported_without_config(tmp_path):
    (tmp_path / "packs").mkdir()
    _profile(
        tmp_path,
        'scope = "repo"\ndescription = "Example"\n[[packs]]\npack = "missing"\n',
    )
    findings = _step_profiles(tmp_path, None, None, tmp_path / "tmp")
    assert any("missing" in item.message for item in findings)


def test_traversing_pack_reference_is_reported(tmp_path):
    (tmp_path / "packs").mkdir()
    _profile(
        tmp_path,
        'scope = "repo"\ndescription = "Example"\n[[packs]]\npack = "../escape"\n',
    )
    assert _step_profiles(tmp_path, None, None, tmp_path / "tmp")


def test_linked_pack_reference_is_refused_without_reading_target(tmp_path):
    packs = tmp_path / "packs"
    packs.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "pack.toml").write_text("not valid TOML", encoding="utf-8")
    try:
        (packs / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not available")
    _profile(
        tmp_path,
        'scope = "repo"\ndescription = "Example"\n[[packs]]\npack = "linked"\n',
    )
    findings = _step_profiles(tmp_path, None, None, tmp_path / "tmp")
    assert len(findings) == 1
    assert "pack reference refused" in findings[0].message
    assert findings[0].path == "profiles/example.toml"


def test_junction_pack_reference_is_refused(tmp_path, monkeypatch):
    packs = tmp_path / "packs"
    junction = packs / "junction"
    junction.mkdir(parents=True)
    _profile(
        tmp_path,
        'scope = "repo"\ndescription = "Example"\n[[packs]]\npack = "junction"\n',
    )
    original = verify._path_is_junction
    monkeypatch.setattr(
        verify,
        "_path_is_junction",
        lambda path: path == junction or original(path),
    )

    findings = _step_profiles(tmp_path, None, None, tmp_path / "tmp")

    assert len(findings) == 1
    assert findings[0].code == "CAT-V-006"
    assert "pack reference refused" in findings[0].message


def test_linked_profile_file_is_refused(tmp_path):
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    outside = tmp_path / "outside.toml"
    outside.write_text(
        'scope = "repo"\ndescription = "Outside"\npacks = []\n', encoding="utf-8"
    )
    try:
        profiles.joinpath("example.toml").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks not available")
    findings = _step_profiles(tmp_path, None, None, tmp_path / "tmp")
    assert findings[0].code == "CAT-V-006"
    assert "unsafe" in findings[0].message


def test_linked_profiles_root_is_refused(tmp_path):
    outside = tmp_path / "outside-profiles"
    outside.mkdir()
    try:
        (tmp_path / "profiles").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not available")
    findings = _step_profiles(tmp_path, None, None, tmp_path / "tmp")
    assert findings[0].code == "CAT-V-006"
    assert "profiles directory" in findings[0].message
