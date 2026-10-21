"""Wave 5 unit digest verification in verify_archive (AC-0005)."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

from agentbundle.catalogue_tooling.archive import verify_archive


def _archive(tmp_path: Path, digest: str) -> Path:
    files = {
        "AGENTS.md": b"# AGENTS\n",
        "packs/core/pack.toml": b'[pack]\nname = "core"\nversion = "0.1.0"\n',
    }
    manifest = {
        "schema": 2,
        "bundle": "test",
        "release": "0.1.0",
        "generated_at": "2026-07-24T00:00:00Z",
        "source_revision": None,
        "files": [
            {"path": k, "sha256": hashlib.sha256(v).hexdigest()}
            for k, v in sorted(files.items())
        ],
        "packs": [{
            "name": "core", "version": "0.1.0", "path": "packs/core", "digest": digest,
        }],
        "profiles": [],
    }
    members = {**files, "catalogue-manifest.json": json.dumps(manifest).encode("utf-8")}
    path = tmp_path / "test.tar.gz"
    with tarfile.open(path, "w:gz") as tf:
        for name, data in sorted(members.items()):
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return path


def test_mismatched_pack_digest_reports_cat_v_arc_018(tmp_path: Path) -> None:
    result = verify_archive(_archive(tmp_path, "sha256:" + "0" * 64))
    assert not result.ok
    assert "CAT-V-ARC-018" in {d.code for d in result.diagnostics}


# --- Remaining T2 tests (AC-0005, AC-0006, AC-0018) ---

import copy  # noqa: E402
from typing import Any  # noqa: E402

import pytest  # noqa: E402
from agentbundle.catalogue_tooling.archive import unit_digest  # noqa: E402
from agentbundle.catalogue_tooling.package import package_catalogue  # noqa: E402

from tests.unit.test_catalogue_tooling_package import _make_catalogue  # noqa: E402

_FILES = {
    "AGENTS.md": b"# AGENTS\n",
    "packs/core/pack.toml": b'[pack]\nname = "core"\nversion = "0.1.0"\n',
    "profiles/default.toml": b'name = "default"\n',
}


def _file_digests() -> dict[str, str]:
    return {k: hashlib.sha256(v).hexdigest() for k, v in _FILES.items()}


def _base_manifest() -> dict[str, Any]:
    digests = _file_digests()
    pack = unit_digest(digests, "packs/core")
    profile = unit_digest(digests, "profiles/default.toml")
    return {
        "schema": 2,
        "bundle": "test",
        "release": "0.1.0",
        "generated_at": "2026-07-24T00:00:00Z",
        "source_revision": None,
        "files": [{"path": k, "sha256": v} for k, v in sorted(digests.items())],
        "packs": [{
            "name": "core", "version": "0.1.0", "path": "packs/core", "digest": pack,
        }],
        "profiles": [{
            "name": "default", "path": "profiles/default.toml", "digest": profile,
        }],
    }


def _write(tmp_path: Path, manifest: object) -> Path:
    members = {**_FILES, "catalogue-manifest.json": json.dumps(manifest).encode("utf-8")}
    path = tmp_path / "test.tar.gz"
    with tarfile.open(path, "w:gz") as tf:
        for name, data in sorted(members.items()):
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return path


def _codes(result: Any) -> list[str]:
    return [d.code for d in result.diagnostics]


def test_matching_digests_verify_clean(tmp_path: Path) -> None:
    result = verify_archive(_write(tmp_path, _base_manifest()))
    assert result.ok, result.diagnostics


def test_mismatched_profile_digest_reports_one_cat_v_arc_018(tmp_path: Path) -> None:
    manifest = _base_manifest()
    manifest["profiles"][0]["digest"] = "sha256:" + "0" * 64
    result = verify_archive(_write(tmp_path, manifest))
    assert _codes(result) == ["CAT-V-ARC-018"]
    assert "'default'" in result.diagnostics[0].message


def test_pack_path_naming_no_file_reports_one_cat_v_arc_018(tmp_path: Path) -> None:
    manifest = _base_manifest()
    manifest["packs"][0]["path"] = "packs/missing"
    result = verify_archive(_write(tmp_path, manifest))
    assert _codes(result) == ["CAT-V-ARC-018"]


def test_legacy_schema_two_manifest_without_digests_verifies_clean(tmp_path: Path) -> None:
    manifest = _base_manifest()
    manifest["packs"] = [{"name": "core", "version": "0.1.0"}]
    manifest["profiles"] = ["default"]
    result = verify_archive(_write(tmp_path, manifest))
    assert result.ok, result.diagnostics
    assert not {"CAT-V-ARC-018", "CAT-V-ARC-019"} & set(_codes(result))


def test_legacy_schema_one_manifest_without_profiles_verifies_clean(tmp_path: Path) -> None:
    manifest = _base_manifest()
    manifest["schema"] = 1
    manifest["packs"] = [{"name": "core", "version": "0.1.0"}]
    del manifest["profiles"]
    result = verify_archive(_write(tmp_path, manifest))
    assert result.ok, result.diagnostics


def test_packaged_archive_verifies_clean(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"
    packaged = package_catalogue(
        root, "engineering", "0.1.0", "stable", output,
        generated_at="2026-01-01T00:00:00+00:00",
    )
    assert packaged.ok, packaged.diagnostics
    archive = (
        output / "catalogues" / "engineering" / "releases" / "0.1.0"
        / "catalogue-0.1.0.tar.gz"
    )
    result = verify_archive(archive)
    assert result.ok, result.diagnostics


def _mut(fn: Any) -> Any:
    def apply(manifest: dict[str, Any]) -> Any:
        fn(manifest)
        return manifest

    return apply


_SHAPES: dict[str, Any] = {
    "top-level-list": lambda m: [m],
    "top-level-null": lambda m: None,
    "top-level-string": lambda m: "manifest",
    "files-item-string": _mut(lambda m: m["files"].__setitem__(0, "AGENTS.md")),
    "files-sha256-number": _mut(lambda m: m["files"][0].__setitem__("sha256", 7)),
    "profiles-object": _mut(lambda m: m.__setitem__("profiles", {"default": {}})),
    "packs-item-string": _mut(lambda m: m["packs"].__setitem__(0, "core")),
    "packs-object-without-name": _mut(lambda m: m["packs"][0].pop("name")),
    "pack-version-number": _mut(lambda m: m["packs"][0].__setitem__("version", 1)),
    "profiles-item-number": _mut(lambda m: m["profiles"].__setitem__(0, 5)),
    "profile-object-without-name": _mut(lambda m: m["profiles"][0].pop("name")),
    "path-number": _mut(lambda m: m["packs"][0].__setitem__("path", 3)),
    "digest-number": _mut(lambda m: m["packs"][0].__setitem__("digest", 3)),
    "digest-without-path": _mut(lambda m: m["packs"][0].pop("path")),
    "profile-digest-without-path": _mut(lambda m: m["profiles"][0].pop("path")),
}


@pytest.mark.parametrize("shape", sorted(_SHAPES))
def test_malformed_manifest_shape_reports_cat_v_arc_019(tmp_path: Path, shape: str) -> None:
    manifest = _SHAPES[shape](copy.deepcopy(_base_manifest()))
    result = verify_archive(_write(tmp_path, manifest))
    assert not result.ok
    # One diagnostic, and verify returned before any digest check read the entries.
    assert _codes(result) == ["CAT-V-ARC-019"]
