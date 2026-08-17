"""Dependency grammar, resolution, and cycle checks in verifier step 7."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from agentbundle.catalogue_tooling import verify
from agentbundle.catalogue_tooling.verify import _step_dependencies


def _config():
    return SimpleNamespace(name="example", paths=SimpleNamespace(packs="packs"))


def _pack(root: Path, name: str, version: str = "1.0.0", dependency: str = "") -> None:
    target = root / "packs" / name
    target.mkdir(parents=True)
    target.joinpath("pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "{version}"\n{dependency}',
        encoding="utf-8",
    )


def _required(name: str, version: str) -> str:
    return _dependency("required", name, version)


def _dependency(
    kind: str, name: str, version: str, *, catalogue: str = "example"
) -> str:
    return (
        f"[[pack.dependencies.{kind}]]\n"
        f'catalogue = "{catalogue}"\n'
        f'pack = "{name}"\n'
        f'version = "{version}"\n'
    )


def test_valid_dependency_and_supported_ranges_pass(tmp_path):
    _pack(tmp_path, "base", "1.2.3")
    for index, expression in enumerate(("^1.0", "~1.2", ">=1.0 <2.0", ">=1.2.3")):
        _pack(tmp_path, f"owner-{index}", dependency=_required("base", expression))
    assert _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp") == []


def test_missing_required_dependency_is_reported(tmp_path):
    _pack(tmp_path, "owner", dependency=_required("missing", "^1.0"))
    findings = _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp")
    assert any("missing required" in item.message for item in findings)


def test_required_version_mismatch_is_reported(tmp_path):
    _pack(tmp_path, "base", "2.0.0")
    _pack(tmp_path, "owner", dependency=_required("base", "^1.0"))
    findings = _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp")
    assert any("does not satisfy" in item.message for item in findings)


def test_zero_minor_caret_rejects_next_minor(tmp_path):
    _pack(tmp_path, "base", "0.2.0")
    _pack(tmp_path, "owner", dependency=_required("base", "^0.1"))
    findings = _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp")
    assert any("does not satisfy" in item.message for item in findings)


def test_recommended_absence_and_version_mismatch_are_informational(tmp_path):
    _pack(tmp_path, "base", "2.0.0")
    _pack(
        tmp_path,
        "owner",
        dependency=(
            _dependency("recommended", "missing", "^1.0")
            + _dependency("recommended", "base", "^1.0")
        ),
    )
    assert _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp") == []


def test_conflicts_validate_shape_without_treating_source_presence_as_installed(
    tmp_path,
):
    _pack(tmp_path, "present")
    _pack(
        tmp_path,
        "owner",
        dependency=(
            _dependency("conflicts", "present", "^1.0")
            + _dependency("conflicts", "absent", "^1.0")
        ),
    )
    assert _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp") == []


def test_valid_cross_catalogue_dependency_skips_local_lookup(tmp_path):
    _pack(
        tmp_path,
        "owner",
        dependency=_dependency(
            "required", "remote", ">=1.0 <2.0", catalogue="other"
        ),
    )
    assert _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp") == []


def test_malformed_range_is_reported_for_external_dependency(tmp_path):
    dependency = (
        "[[pack.dependencies.required]]\n"
        'catalogue = "other"\npack = "remote"\nversion = "not-a-version"\n'
    )
    _pack(tmp_path, "owner", dependency=dependency)
    assert any(
        "invalid version range" in item.message
        for item in _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp")
    )


def test_required_cycle_is_reported(tmp_path):
    _pack(tmp_path, "alpha", dependency=_required("beta", "^1.0"))
    _pack(tmp_path, "beta", dependency=_required("alpha", "^1.0"))
    findings = _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp")
    assert any("circular required dependency" in item.message for item in findings)


def test_invalid_and_traversing_local_pack_references_are_refused(tmp_path):
    for index, name in enumerate(("Not_Canonical", "../outside", "/absolute")):
        _pack(tmp_path, f"owner-{index}", dependency=_required(name, "^1.0"))
    findings = _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp")
    assert len(findings) == 3
    assert all("pack reference" in item.message for item in findings)
    assert all(item.path == "packs/<invalid-pack-reference>" for item in findings)


def test_linked_local_pack_reference_is_refused_without_reading_target(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "pack.toml").write_text("not valid TOML", encoding="utf-8")
    packs = tmp_path / "packs"
    packs.mkdir()
    try:
        (packs / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not available")
    _pack(tmp_path, "owner", dependency=_required("linked", "^1.0"))
    findings = _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp")
    assert len(findings) == 1
    assert "pack reference refused" in findings[0].message
    assert findings[0].path == "packs/linked"


def test_junction_local_pack_reference_is_refused(tmp_path, monkeypatch):
    _pack(tmp_path, "junction")
    _pack(tmp_path, "owner", dependency=_required("junction", "^1.0"))
    junction = tmp_path / "packs" / "junction"
    original = verify._path_is_junction
    monkeypatch.setattr(
        verify,
        "_path_is_junction",
        lambda path: path == junction or original(path),
    )

    findings = _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp")

    assert any(
        item.code == "CAT-V-007"
        and item.path == "packs/junction"
        and "pack reference refused" in item.message
        for item in findings
    )


def test_linked_pack_manifest_is_refused(tmp_path):
    base = tmp_path / "packs" / "base"
    base.mkdir(parents=True)
    outside = tmp_path / "outside.toml"
    outside.write_text('[pack]\nname = "base"\nversion = "1.0.0"\n', encoding="utf-8")
    try:
        (base / "pack.toml").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks not available")
    _pack(tmp_path, "owner", dependency=_required("base", "^1.0"))
    findings = _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp")
    assert any(
        item.code == "CAT-V-007" and "cannot be read safely" in item.message
        for item in findings
    )


def test_linked_packs_root_is_refused(tmp_path):
    outside = tmp_path / "outside-packs"
    outside.mkdir()
    try:
        (tmp_path / "packs").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not available")
    findings = _step_dependencies(tmp_path, _config(), None, tmp_path / "tmp")
    assert findings[0].code == "CAT-V-007"
    assert "packs directory" in findings[0].message


def test_unknown_catalogue_identity_skips_local_classification_with_info(tmp_path):
    _pack(tmp_path, "owner", dependency=_required("missing", "^1.0"))
    findings = _step_dependencies(tmp_path, None, None, tmp_path / "tmp")
    assert len(findings) == 1
    assert "catalogue identity unknown" in findings[0].message


def test_pack_selection_does_not_scan_unrelated_pack(tmp_path):
    _pack(tmp_path, "alpha")
    _pack(tmp_path, "broken", dependency=_required("missing", "^1.0"))
    assert _step_dependencies(tmp_path, _config(), "alpha", tmp_path / "tmp") == []
