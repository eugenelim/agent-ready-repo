"""Tests for agentbundle.catalogue_tooling.package.package_source_flavour."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

from agentbundle.catalogue_tooling.package import package_source_flavour

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_source_catalogue(root: Path) -> None:
    """Create a minimal source catalogue tree for testing."""
    (root / "catalogue.toml").write_text(
        '[catalogue]\nname = "test"\n', encoding="utf-8"
    )
    packs = root / "packs" / "core"
    packs.mkdir(parents=True)
    (packs / "pack.toml").write_text(
        '[pack]\nname = "core"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    profiles = root / "profiles"
    profiles.mkdir()
    (profiles / "default.toml").write_text(
        '[profile]\nname = "default"\n', encoding="utf-8"
    )
    plugin_dir = root / ".claude-plugin"
    plugin_dir.mkdir()
    (plugin_dir / "marketplace.json").write_text('{"packs": []}', encoding="utf-8")
    guides = root / "guides" / "_shared" / "how-to"
    guides.mkdir(parents=True)
    (guides / "guide.md").write_text("# Guide\n", encoding="utf-8")
    (root / "README.md").write_text("# Test Catalogue\n", encoding="utf-8")
    (root / "LICENSE-APACHE").write_text("Apache-2.0", encoding="utf-8")
    (root / "LICENSE-MIT").write_text("MIT", encoding="utf-8")


# ---------------------------------------------------------------------------
# package_source_flavour()
# ---------------------------------------------------------------------------

def test_produces_archive_and_manifest(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _make_source_catalogue(root)
    output = tmp_path / "output"

    result = package_source_flavour(
        root=root, bundle="test-bundle", release="1.0.0", output=output
    )
    assert result.ok, result.diagnostics
    assert Path(result.archive_path).exists()
    assert Path(result.manifest_path).exists()


def test_archive_contains_packs(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _make_source_catalogue(root)
    output = tmp_path / "output"

    result = package_source_flavour(
        root=root, bundle="b", release="0.1.0", output=output
    )
    assert result.ok
    with tarfile.open(result.archive_path, "r:gz") as tar:
        members = tar.getnames()
    assert any(m.startswith("packs/") for m in members)
    assert "catalogue.toml" in members


def test_archive_contains_guides(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _make_source_catalogue(root)
    output = tmp_path / "output"

    result = package_source_flavour(
        root=root, bundle="b", release="0.1.0", output=output
    )
    assert result.ok
    with tarfile.open(result.archive_path, "r:gz") as tar:
        members = tar.getnames()
    assert any("guides" in m for m in members)


def test_manifest_has_correct_kind(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _make_source_catalogue(root)
    output = tmp_path / "output"

    result = package_source_flavour(
        root=root, bundle="b", release="1.2.3", output=output
    )
    assert result.ok
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
    assert manifest["kind"] == "agentbundle-self-hosted-source"
    assert manifest["bundle"] == "b"
    assert manifest["release"] == "1.2.3"
    assert "sha256" in manifest
    assert "files" in manifest


def test_sidecar_sha256_matches_archive(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _make_source_catalogue(root)
    output = tmp_path / "output"

    result = package_source_flavour(
        root=root, bundle="b", release="0.1.0", output=output
    )
    assert result.ok
    import hashlib
    archive_bytes = Path(result.archive_path).read_bytes()
    expected = hashlib.sha256(archive_bytes).hexdigest()
    sidecar = Path(result.archive_path + ".sha256").read_text(encoding="utf-8").strip()
    assert sidecar == expected


def test_output_layout(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _make_source_catalogue(root)
    output = tmp_path / "output"

    result = package_source_flavour(
        root=root, bundle="my-bundle", release="2.0.0", output=output
    )
    assert result.ok
    release_dir = output / "catalogue-sources" / "my-bundle" / "releases" / "2.0.0"
    assert release_dir.is_dir()
    assert (release_dir / "catalogue-source-2.0.0.tar.gz").exists()
    assert (release_dir / "self-hosted-source-manifest.json").exists()


def test_bad_bundle_name_returns_error(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _make_source_catalogue(root)
    result = package_source_flavour(
        root=root, bundle="../traversal", release="1.0.0", output=tmp_path / "out"
    )
    assert not result.ok
    assert result.diagnostics


def test_missing_root_returns_error(tmp_path: Path) -> None:
    result = package_source_flavour(
        root=tmp_path / "nonexistent",
        bundle="b",
        release="1.0.0",
        output=tmp_path / "out",
    )
    assert not result.ok
    assert result.diagnostics


def test_source_revision_in_manifest(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _make_source_catalogue(root)
    output = tmp_path / "output"

    result = package_source_flavour(
        root=root, bundle="b", release="1.0.0",
        output=output, source_revision="abc1234",
    )
    assert result.ok
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
    assert manifest["source_revision"] == "abc1234"
