"""Tests for the package-catalogue subcommand.

Covers all ACs from spec/package-catalogue-command/spec.md.
Uses example.test placeholders only — no real credentials or external URIs.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Generator
from unittest import mock

import tomllib

import pytest

from agentbundle import cli
from agentbundle.commands import package_catalogue
from agentbundle.commands.package_catalogue import (
    _build_archive,
    _compute_file_digests,
    _generate_manifest,
    _read_content_files,
    _scan_content,
    _validate_content,
    _write_channel_descriptor,
    run,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_fixture_catalogue(tmp_path: Path, *, with_profiles: bool = True, with_contracts: bool = True, with_readme: bool = True, with_license: bool = True, extra_dirs: list[str] | None = None) -> Path:
    """Create a minimal valid catalogue root under tmp_path."""
    root = tmp_path / "catalogue"
    root.mkdir()

    # One pack
    pack_dir = root / "packs" / "core"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.toml").write_text(
        '[pack]\nname = "core"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (pack_dir / "SKILL.md").write_text("# skill\n", encoding="utf-8")

    if with_profiles:
        profiles_dir = root / "profiles"
        profiles_dir.mkdir()
        (profiles_dir / "default.toml").write_text('[profile]\nname = "default"\n', encoding="utf-8")

    if with_contracts:
        contracts_dir = root / "docs" / "contracts"
        contracts_dir.mkdir(parents=True)
        (contracts_dir / "adapter.toml").write_text('[contract]\nversion = "1"\n', encoding="utf-8")

    if with_readme:
        (root / "README.md").write_text("# Test Catalogue\n", encoding="utf-8")

    if with_license:
        (root / "LICENSE").write_text("MIT\n", encoding="utf-8")

    for extra in extra_dirs or []:
        extra_dir = root / extra
        extra_dir.mkdir(parents=True, exist_ok=True)
        (extra_dir / "file.txt").write_text("excluded\n", encoding="utf-8")

    return root


def _make_args(
    root: str | Path,
    *,
    bundle: str = "engineering",
    release: str = "0.1.0",
    channel: str = "stable",
    output: str | Path | None = None,
    source_revision: str | None = None,
    minimum_agentbundle_version: str | None = None,
    published_at: str | None = None,
    tmp_path: Path | None = None,
) -> mock.Namespace:
    if output is None:
        assert tmp_path is not None, "tmp_path required when output is not given"
        output = tmp_path / "output"
    ns = mock.MagicMock()
    ns.root = str(root)
    ns.bundle = bundle
    ns.release = release
    ns.channel = channel
    ns.output = str(output)
    ns.source_revision = source_revision
    ns.minimum_agentbundle_version = minimum_agentbundle_version
    ns.published_at = published_at
    return ns


# ---------------------------------------------------------------------------
# T1: _scan_content tests
# ---------------------------------------------------------------------------


def test_scan_content_includes_allowlisted_files(tmp_path: Path) -> None:
    root = _make_fixture_catalogue(
        tmp_path, extra_dirs=["build", "tests", ".git"]
    )
    paths = _scan_content(root)
    posix = [p.relative_to(root).as_posix() for p in paths]
    # Allowlisted entries present
    assert "packs/core/pack.toml" in posix
    assert "packs/core/SKILL.md" in posix
    assert "profiles/default.toml" in posix
    assert "docs/contracts/adapter.toml" in posix
    assert "README.md" in posix
    assert "LICENSE" in posix
    # Excluded directories absent
    for p in posix:
        assert not p.startswith("build/")
        assert not p.startswith("tests/")
        assert not p.startswith(".git/")


def test_scan_content_excludes_symlinks(tmp_path: Path) -> None:
    root = _make_fixture_catalogue(tmp_path)
    # Create a symlink inside packs/core/
    target = root / "packs" / "core" / "real.md"
    target.write_text("real\n", encoding="utf-8")
    symlink = root / "packs" / "core" / "link.md"
    symlink.symlink_to(target)

    paths = _scan_content(root)
    posix = [p.relative_to(root).as_posix() for p in paths]
    assert "packs/core/link.md" not in posix
    assert "packs/core/real.md" in posix


def test_scan_content_returns_sorted_paths(tmp_path: Path) -> None:
    root = _make_fixture_catalogue(tmp_path)
    paths = _scan_content(root)
    posix = [p.relative_to(root).as_posix() for p in paths]
    assert posix == sorted(posix)


def test_scan_content_absent_optional_dir(tmp_path: Path) -> None:
    root = _make_fixture_catalogue(
        tmp_path, with_profiles=False, with_contracts=False, with_readme=False, with_license=False
    )
    paths = _scan_content(root)
    posix = [p.relative_to(root).as_posix() for p in paths]
    assert "packs/core/pack.toml" in posix
    # No profiles or docs/contracts entries
    for p in posix:
        assert not p.startswith("profiles/")
        assert not p.startswith("docs/")


# ---------------------------------------------------------------------------
# T1: _validate_content tests
# ---------------------------------------------------------------------------


def test_validate_content_valid_catalogue_returns_none(tmp_path: Path) -> None:
    root = _make_fixture_catalogue(tmp_path)
    paths = _scan_content(root)
    assert _validate_content(root, paths) is None


def test_validate_content_missing_packs_dir_rejected(tmp_path: Path) -> None:
    root = tmp_path / "no_packs"
    root.mkdir()
    (root / "README.md").write_text("hi\n", encoding="utf-8")
    err = _validate_content(root, [])
    assert err is not None
    assert "packs" in err


def test_validate_content_symlink_file_rejected(tmp_path: Path) -> None:
    root = _make_fixture_catalogue(tmp_path)
    target = root / "packs" / "core" / "real.md"
    target.write_text("real\n", encoding="utf-8")
    symlink = root / "packs" / "core" / "link.md"
    symlink.symlink_to(target)
    # _scan_content skips symlinks, but _validate_content must still catch them
    paths = _scan_content(root)
    err = _validate_content(root, paths)
    assert err is not None
    assert "link.md" in err


def test_validate_content_symlink_dir_rejected(tmp_path: Path) -> None:
    root = _make_fixture_catalogue(tmp_path)
    real_dir = tmp_path / "real_subdir"
    real_dir.mkdir()
    (real_dir / "file.md").write_text("content\n", encoding="utf-8")
    symlink_dir = root / "packs" / "core" / "subdir"
    symlink_dir.symlink_to(real_dir)
    paths = _scan_content(root)
    err = _validate_content(root, paths)
    assert err is not None


def test_validate_content_top_level_dir_symlink_rejected(tmp_path: Path) -> None:
    """packs/ at --root that is a symlink to a real directory is rejected."""
    real_packs = tmp_path / "real_packs"
    real_packs.mkdir()
    pack_dir = real_packs / "core"
    pack_dir.mkdir()
    (pack_dir / "pack.toml").write_text('[pack]\nname = "core"\nversion = "0.1.0"\n', encoding="utf-8")

    root = tmp_path / "cat"
    root.mkdir()
    symlink_packs = root / "packs"
    symlink_packs.symlink_to(real_packs)

    err = _validate_content(root, [])
    assert err is not None
    assert "packs" in err


def test_validate_content_intermediate_dir_symlink_rejected(tmp_path: Path) -> None:
    """docs/ symlink containing a contracts/ subdir is rejected."""
    real_docs = tmp_path / "real_docs"
    contracts = real_docs / "contracts"
    contracts.mkdir(parents=True)
    (contracts / "adapter.toml").write_text('[contract]\nversion = "1"\n', encoding="utf-8")

    root = tmp_path / "cat"
    root.mkdir()
    # packs/ must exist for packs-dir check not to fire first
    pack_dir = root / "packs" / "core"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.toml").write_text('[pack]\nname = "core"\nversion = "0.1.0"\n', encoding="utf-8")

    symlink_docs = root / "docs"
    symlink_docs.symlink_to(real_docs)

    err = _validate_content(root, [])
    assert err is not None
    assert "docs" in err


def test_validate_content_root_file_symlink_rejected(tmp_path: Path) -> None:
    """README.md that is a symlink at root is rejected."""
    root = _make_fixture_catalogue(tmp_path, with_readme=False)
    real_readme = tmp_path / "real_readme.md"
    real_readme.write_text("# real\n", encoding="utf-8")
    (root / "README.md").symlink_to(real_readme)
    paths = _scan_content(root)
    err = _validate_content(root, paths)
    assert err is not None
    assert "README.md" in err


@pytest.mark.skipif(sys.platform == "win32", reason="st_nlink hard-link detection is POSIX-only")
def test_validate_content_hardlink_rejected(tmp_path: Path) -> None:
    root = _make_fixture_catalogue(tmp_path)
    original = root / "packs" / "core" / "pack.toml"
    hardlink = root / "packs" / "core" / "hardlink.toml"
    os.link(str(original), str(hardlink))
    paths = _scan_content(root)
    err = _validate_content(root, paths)
    assert err is not None
    assert "hardlink" in str(err)


def test_validate_content_traversal_rejected(tmp_path: Path) -> None:
    """Path that resolves outside root triggers traversal error (synthetic mock)."""
    root = tmp_path / "root"
    root.mkdir()
    (root / "packs").mkdir()
    pack_dir = root / "packs" / "core"
    pack_dir.mkdir()
    (pack_dir / "pack.toml").write_text('[pack]\nname = "core"\nversion = "0.1.0"\n', encoding="utf-8")

    outside = tmp_path / "outside.txt"
    outside.write_text("evil\n", encoding="utf-8")

    # Patch .resolve() on a path to return a location outside root
    fake_path = mock.MagicMock(spec=Path)
    fake_path.stat.return_value = mock.MagicMock(st_nlink=1)
    fake_path.resolve.return_value = outside.resolve()

    err = _validate_content(root, [fake_path])
    assert err is not None
    assert "traversal" in err.lower() or "outside" in err.lower()


def test_validate_content_invalid_pack_toml_rejected(tmp_path: Path) -> None:
    root = tmp_path / "cat"
    root.mkdir()
    bad_pack = root / "packs" / "bad"
    bad_pack.mkdir(parents=True)
    (bad_pack / "pack.toml").write_text("not valid toml ][", encoding="utf-8")
    err = _validate_content(root, [])
    assert err is not None
    assert "bad" in err or "pack.toml" in err


def test_validate_content_pack_toml_missing_version_rejected(tmp_path: Path) -> None:
    root = tmp_path / "cat"
    root.mkdir()
    pack_dir = root / "packs" / "core"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.toml").write_text('[pack]\nname = "core"\n', encoding="utf-8")
    err = _validate_content(root, [])
    assert err is not None
    assert "version" in err


def test_validate_content_invalid_profile_toml_rejected(tmp_path: Path) -> None:
    root = _make_fixture_catalogue(tmp_path, with_profiles=False)
    profiles_dir = root / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "bad.toml").write_text("not valid toml ][", encoding="utf-8")
    paths = _scan_content(root)
    err = _validate_content(root, paths)
    assert err is not None
    assert "bad.toml" in err


# ---------------------------------------------------------------------------
# T2: _compute_file_digests, _generate_manifest, _build_archive
# ---------------------------------------------------------------------------


def test_compute_file_digests_values() -> None:
    data = {
        "packs/core/pack.toml": b"[pack]\nname = 'core'\n",
        "profiles/default.toml": b"[profile]\n",
    }
    digests = _compute_file_digests(data)
    for key, raw in data.items():
        assert digests[key] == hashlib.sha256(raw).hexdigest()


def test_compute_file_digests_keys_are_posix_relative() -> None:
    data = {"packs/core/pack.toml": b"x"}
    digests = _compute_file_digests(data)
    for key in digests:
        assert not key.startswith("/")
        assert "\\" not in key


def test_read_content_files_single_read(tmp_path: Path) -> None:
    root = _make_fixture_catalogue(tmp_path)
    paths = _scan_content(root)
    file_bytes = _read_content_files(root, paths)
    posix_keys = {p.relative_to(root).as_posix() for p in paths}
    assert set(file_bytes.keys()) == posix_keys
    for key, data in file_bytes.items():
        assert isinstance(data, bytes)
        assert len(data) > 0


def test_generate_manifest_required_fields() -> None:
    manifest_bytes = _generate_manifest(
        bundle="engineering",
        release="0.1.0",
        source_revision="abc123",
        generated_at="2023-11-14T22:13:20+00:00",
        file_digests={"packs/core/pack.toml": "a" * 64},
        packs_metadata=[{"name": "core", "version": "0.1.0"}],
    )
    manifest = json.loads(manifest_bytes)
    assert manifest["schema"] == 1
    assert manifest["bundle"] == "engineering"
    assert manifest["release"] == "0.1.0"
    assert "source_revision" in manifest
    assert "generated_at" in manifest
    assert "files" in manifest
    assert "packs" in manifest


def test_generate_manifest_source_revision_null() -> None:
    manifest_bytes = _generate_manifest(
        bundle="b", release="r", source_revision=None,
        generated_at="2023-11-14T22:13:20+00:00",
        file_digests={}, packs_metadata=[],
    )
    assert json.loads(manifest_bytes)["source_revision"] is None


def test_generate_manifest_source_revision_string() -> None:
    manifest_bytes = _generate_manifest(
        bundle="b", release="r", source_revision="abc123",
        generated_at="2023-11-14T22:13:20+00:00",
        file_digests={}, packs_metadata=[],
    )
    assert json.loads(manifest_bytes)["source_revision"] == "abc123"


def test_generate_manifest_files_sorted() -> None:
    digests = {"z/file.txt": "a" * 64, "a/file.txt": "b" * 64}
    manifest_bytes = _generate_manifest(
        bundle="b", release="r", source_revision=None,
        generated_at="2023-11-14T22:13:20+00:00",
        file_digests=digests, packs_metadata=[],
    )
    files = json.loads(manifest_bytes)["files"]
    paths = [f["path"] for f in files]
    assert paths == sorted(paths)


def test_generate_manifest_packs_sorted() -> None:
    packs = [{"name": "zzz", "version": "1.0.0"}, {"name": "aaa", "version": "2.0.0"}]
    manifest_bytes = _generate_manifest(
        bundle="b", release="r", source_revision=None,
        generated_at="2023-11-14T22:13:20+00:00",
        file_digests={}, packs_metadata=packs,
    )
    pack_names = [p["name"] for p in json.loads(manifest_bytes)["packs"]]
    assert pack_names == sorted(pack_names)


def test_generate_manifest_no_self_reference() -> None:
    manifest_bytes = _generate_manifest(
        bundle="b", release="r", source_revision=None,
        generated_at="2023-11-14T22:13:20+00:00",
        file_digests={"packs/core/pack.toml": "a" * 64}, packs_metadata=[],
    )
    paths = [f["path"] for f in json.loads(manifest_bytes)["files"]]
    assert "catalogue-manifest.json" not in paths


def test_generate_manifest_accepts_fixed_generated_at() -> None:
    ts = "2023-11-14T22:13:20+00:00"
    manifest_bytes = _generate_manifest(
        bundle="b", release="r", source_revision=None,
        generated_at=ts,
        file_digests={}, packs_metadata=[],
    )
    assert json.loads(manifest_bytes)["generated_at"] == ts


def test_build_archive_deterministic() -> None:
    file_bytes = {"packs/core/pack.toml": b"[pack]\nname='core'\nversion='0.1.0'\n"}
    manifest = b'{"schema": 1}'
    a1 = _build_archive(file_bytes, manifest)
    a2 = _build_archive(file_bytes, manifest)
    assert hashlib.sha256(a1).digest() == hashlib.sha256(a2).digest()


def test_build_archive_gzip_mtime_zero() -> None:
    archive_bytes = _build_archive({"a.txt": b"hello"}, b"{}")
    # gzip header bytes 4-7 are the modification time field
    assert archive_bytes[4:8] == b"\x00\x00\x00\x00"


def test_build_archive_members_sorted() -> None:
    file_bytes = {
        "z/last.txt": b"last",
        "a/first.txt": b"first",
        "m/middle.txt": b"middle",
    }
    archive_bytes = _build_archive(file_bytes, b"{}")
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tf:
        names = tf.getnames()
    # catalogue-manifest.json sorts between 'a' and 'd' ('c' = 0x63)
    assert names == sorted(names)


def test_build_archive_member_metadata_files() -> None:
    archive_bytes = _build_archive({"test.txt": b"data"}, b"{}")
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tf:
        for member in tf.getmembers():
            assert member.uid == 0
            assert member.gid == 0
            assert member.mtime == 0
            assert member.mode == 0o644


def test_build_archive_contains_manifest() -> None:
    manifest_content = b'{"schema": 1, "bundle": "test"}'
    archive_bytes = _build_archive({}, manifest_content)
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tf:
        names = tf.getnames()
        assert "catalogue-manifest.json" in names
        f = tf.extractfile("catalogue-manifest.json")
        assert f is not None
        data = json.loads(f.read())
        assert data["schema"] == 1


def test_build_archive_rejects_traversal_member_name() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        _build_archive({"../evil": b"x"}, b"{}")


def test_build_archive_rejects_absolute_member_name() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        _build_archive({"/etc/passwd": b"x"}, b"{}")


def test_build_archive_rejects_drive_letter_member_name() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        _build_archive({"C:evil": b"x"}, b"{}")


# ---------------------------------------------------------------------------
# T3: _write_channel_descriptor tests
# ---------------------------------------------------------------------------


def test_write_channel_descriptor_required_fields(tmp_path: Path) -> None:
    path = tmp_path / "channels" / "stable.json"
    _write_channel_descriptor(
        path,
        bundle="engineering",
        channel="stable",
        release="0.1.0",
        sha256_hex="a" * 64,
        published_at="2023-11-14T22:13:20+00:00",
        source_revision=None,
        minimum_agentbundle_version=None,
    )
    descriptor = json.loads(path.read_text(encoding="utf-8"))
    assert descriptor["schema"] == 1
    assert descriptor["kind"] == "agentbundle-catalogue"
    assert descriptor["bundle"] == "engineering"
    assert descriptor["channel"] == "stable"
    assert descriptor["release"] == "0.1.0"
    assert descriptor["sha256"] == "a" * 64
    assert descriptor["published_at"] == "2023-11-14T22:13:20+00:00"


def test_write_channel_descriptor_relative_artifact_url(tmp_path: Path) -> None:
    path = tmp_path / "channels" / "stable.json"
    _write_channel_descriptor(
        path,
        bundle="engineering",
        channel="stable",
        release="0.13.0",
        sha256_hex="b" * 64,
        published_at="2023-01-01T00:00:00+00:00",
        source_revision=None,
        minimum_agentbundle_version=None,
    )
    descriptor = json.loads(path.read_text(encoding="utf-8"))
    assert descriptor["artifact"] == "../releases/0.13.0/catalogue-0.13.0.tar.gz"


def test_write_channel_descriptor_optional_fields_absent(tmp_path: Path) -> None:
    path = tmp_path / "channels" / "stable.json"
    _write_channel_descriptor(
        path,
        bundle="engineering",
        channel="stable",
        release="0.1.0",
        sha256_hex="c" * 64,
        published_at="2023-01-01T00:00:00+00:00",
        source_revision=None,
        minimum_agentbundle_version=None,
    )
    descriptor = json.loads(path.read_text(encoding="utf-8"))
    assert "source_revision" not in descriptor
    assert "minimum_agentbundle_version" not in descriptor


def test_write_channel_descriptor_optional_fields_present(tmp_path: Path) -> None:
    path = tmp_path / "channels" / "stable.json"
    _write_channel_descriptor(
        path,
        bundle="engineering",
        channel="stable",
        release="0.1.0",
        sha256_hex="d" * 64,
        published_at="2023-01-01T00:00:00+00:00",
        source_revision="abc123",
        minimum_agentbundle_version="0.12.0",
    )
    descriptor = json.loads(path.read_text(encoding="utf-8"))
    assert descriptor["source_revision"] == "abc123"
    assert descriptor["minimum_agentbundle_version"] == "0.12.0"


def test_write_channel_descriptor_creates_parent_dirs(tmp_path: Path) -> None:
    nested = tmp_path / "deep" / "nested" / "channels" / "stable.json"
    _write_channel_descriptor(
        nested,
        bundle="engineering",
        channel="stable",
        release="0.1.0",
        sha256_hex="e" * 64,
        published_at="2023-01-01T00:00:00+00:00",
        source_revision=None,
        minimum_agentbundle_version=None,
    )
    assert nested.exists()


def test_write_channel_descriptor_sha256_matches_sidecar(tmp_path: Path) -> None:
    sha = "f" * 64
    path = tmp_path / "channels" / "stable.json"
    _write_channel_descriptor(
        path,
        bundle="engineering",
        channel="stable",
        release="0.1.0",
        sha256_hex=sha,
        published_at="2023-01-01T00:00:00+00:00",
        source_revision=None,
        minimum_agentbundle_version=None,
    )
    descriptor = json.loads(path.read_text(encoding="utf-8"))
    assert descriptor["sha256"] == sha


# ---------------------------------------------------------------------------
# T4: run() and CLI integration tests
# ---------------------------------------------------------------------------


def test_package_catalogue_end_to_end(tmp_path: Path) -> None:
    """AC3, AC4, AC11, AC19, AC20."""
    root = _make_fixture_catalogue(
        tmp_path,
        extra_dirs=["build", "tests", ".git"],
    )
    output = tmp_path / "output"
    args = _make_args(root, output=output, source_revision="deadbeef")

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = run(args)

    assert result == 0

    # AC3: exactly three output files
    archive_path = output / "catalogues" / "engineering" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    sidecar_path = output / "catalogues" / "engineering" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz.sha256"
    descriptor_path = output / "catalogues" / "engineering" / "channels" / "stable.json"

    assert archive_path.exists()
    assert sidecar_path.exists()
    assert descriptor_path.exists()

    all_files = [p for p in output.rglob("*") if p.is_file()]
    assert len(all_files) == 3

    # AC4: only allowlisted entries in archive
    archive_bytes = archive_path.read_bytes()
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tf:
        names = set(tf.getnames())
    assert "packs/core/pack.toml" in names
    assert "packs/core/SKILL.md" in names
    assert "profiles/default.toml" in names
    assert "docs/contracts/adapter.toml" in names
    assert "README.md" in names
    assert "LICENSE" in names
    assert "catalogue-manifest.json" in names
    for n in names:
        assert not n.startswith("build/")
        assert not n.startswith("tests/")
        assert not n.startswith(".git/")

    # AC11: catalogue-manifest.json schema
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tf:
        mf = tf.extractfile("catalogue-manifest.json")
        assert mf is not None
        manifest = json.loads(mf.read())
    assert manifest["schema"] == 1
    assert manifest["bundle"] == "engineering"
    assert manifest["release"] == "0.1.0"
    assert manifest["source_revision"] == "deadbeef"
    assert "generated_at" in manifest
    assert "files" in manifest
    assert "packs" in manifest

    # AC19/AC20: channel descriptor
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    assert descriptor["schema"] == 1
    assert descriptor["kind"] == "agentbundle-catalogue"
    assert descriptor["artifact"] == "../releases/0.1.0/catalogue-0.1.0.tar.gz"
    assert "published_at" in descriptor


def test_package_catalogue_refuse_overwrite(tmp_path: Path) -> None:
    """AC18: refuse to overwrite existing archive."""
    root = _make_fixture_catalogue(tmp_path)
    output = tmp_path / "output"
    args = _make_args(root, output=output)

    # Pre-create the archive path with known content
    archive_path = output / "catalogues" / "engineering" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(b"existing_content")

    result = run(args)
    assert result == 1
    # Archive content unchanged
    assert archive_path.read_bytes() == b"existing_content"
    # No other files written
    sidecar = archive_path.parent / "catalogue-0.1.0.tar.gz.sha256"
    descriptor = output / "catalogues" / "engineering" / "channels" / "stable.json"
    assert not sidecar.exists()
    assert not descriptor.exists()


def test_package_catalogue_archive_reproducible(tmp_path: Path) -> None:
    """AC8: identical inputs produce byte-identical archives."""
    root = _make_fixture_catalogue(tmp_path)
    output1 = tmp_path / "out1"
    output2 = tmp_path / "out2"

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        r1 = run(_make_args(root, output=output1))
        r2 = run(_make_args(root, output=output2))

    assert r1 == 0
    assert r2 == 0

    a1 = (output1 / "catalogues" / "engineering" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz").read_bytes()
    a2 = (output2 / "catalogues" / "engineering" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz").read_bytes()
    assert hashlib.sha256(a1).digest() == hashlib.sha256(a2).digest()


def test_package_catalogue_sidecar_format(tmp_path: Path) -> None:
    """AC10: sidecar is sha256_hex + newline."""
    root = _make_fixture_catalogue(tmp_path)
    output = tmp_path / "output"

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        run(_make_args(root, output=output))

    archive_path = output / "catalogues" / "engineering" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    sidecar_path = archive_path.parent / "catalogue-0.1.0.tar.gz.sha256"

    archive_bytes = archive_path.read_bytes()
    sidecar_content = sidecar_path.read_text(encoding="utf-8")
    expected = hashlib.sha256(archive_bytes).hexdigest() + "\n"
    assert sidecar_content == expected


def test_package_catalogue_source_date_epoch_in_manifest(tmp_path: Path) -> None:
    """AC9: SOURCE_DATE_EPOCH=1700000000 => generated_at == 2023-11-14T22:13:20+00:00."""
    root = _make_fixture_catalogue(tmp_path)
    output = tmp_path / "output"

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        run(_make_args(root, output=output))

    archive_path = output / "catalogues" / "engineering" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(fileobj=io.BytesIO(archive_path.read_bytes()), mode="r:gz") as tf:
        mf = tf.extractfile("catalogue-manifest.json")
        assert mf is not None
        manifest = json.loads(mf.read())

    assert manifest["generated_at"] == "2023-11-14T22:13:20+00:00"


def test_package_catalogue_generated_at_no_microseconds(tmp_path: Path) -> None:
    """AC9 format: generated_at must not contain a microsecond component."""
    root = _make_fixture_catalogue(tmp_path)
    output = tmp_path / "output"

    env = {k: v for k, v in os.environ.items() if k != "SOURCE_DATE_EPOCH"}
    with mock.patch.dict(os.environ, env, clear=True):
        run(_make_args(root, output=output))

    archive_path = output / "catalogues" / "engineering" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(fileobj=io.BytesIO(archive_path.read_bytes()), mode="r:gz") as tf:
        mf = tf.extractfile("catalogue-manifest.json")
        assert mf is not None
        manifest = json.loads(mf.read())

    assert "." not in manifest["generated_at"]


def test_package_catalogue_cli_help() -> None:
    """AC1: --help exits 0 and lists all flags."""
    stdout_buf = io.StringIO()
    with pytest.raises(SystemExit) as exc_info:
        with contextlib.redirect_stdout(stdout_buf):
            cli.main(["package-catalogue", "--help"])
    assert exc_info.value.code == 0
    help_text = stdout_buf.getvalue()
    for flag in [
        "--root",
        "--bundle",
        "--release",
        "--channel",
        "--output",
        "--source-revision",
        "--minimum-agentbundle-version",
        "--published-at",
    ]:
        assert flag in help_text, f"expected {flag!r} in help text"


@pytest.mark.parametrize(
    "missing_flag,remaining",
    [
        ("--root", ["--bundle", "b", "--release", "r", "--channel", "c", "--output", "."]),
        ("--bundle", ["--root", ".", "--release", "r", "--channel", "c", "--output", "."]),
        ("--release", ["--root", ".", "--bundle", "b", "--channel", "c", "--output", "."]),
        ("--channel", ["--root", ".", "--bundle", "b", "--release", "r", "--output", "."]),
        ("--output", ["--root", ".", "--bundle", "b", "--release", "r", "--channel", "c"]),
    ],
)
def test_package_catalogue_missing_required_flag(missing_flag: str, remaining: list[str]) -> None:
    """AC2: each missing required flag causes non-zero exit."""
    stderr_buf = io.StringIO()
    with pytest.raises(SystemExit) as exc_info:
        with contextlib.redirect_stderr(stderr_buf):
            cli.main(["package-catalogue"] + remaining)
    assert exc_info.value.code != 0
    stderr_text = stderr_buf.getvalue()
    # argparse includes the flag name or an error about it
    assert missing_flag.lstrip("-").replace("-", "_") in stderr_text or missing_flag in stderr_text


@pytest.mark.parametrize(
    "extra_flags",
    [
        ["--scope", "repo"],
        ["--force"],
        ["--adapter", "claude-code"],
    ],
)
def test_package_catalogue_install_flags_rejected(extra_flags: list[str], tmp_path: Path) -> None:
    """AC25: --scope, --force, --adapter are rejected by package-catalogue."""
    with pytest.raises(SystemExit) as exc_info:
        cli.main(
            [
                "package-catalogue",
                "--root", ".",
                "--bundle", "b",
                "--release", "r",
                "--channel", "c",
                "--output", ".",
            ] + extra_flags
        )
    assert exc_info.value.code != 0


def test_package_catalogue_sha256_in_descriptor_matches_sidecar(tmp_path: Path) -> None:
    """AC21: descriptor sha256 == sidecar content (without newline)."""
    root = _make_fixture_catalogue(tmp_path)
    output = tmp_path / "output"

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        run(_make_args(root, output=output))

    archive_path = output / "catalogues" / "engineering" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    sidecar_path = archive_path.parent / "catalogue-0.1.0.tar.gz.sha256"
    descriptor_path = output / "catalogues" / "engineering" / "channels" / "stable.json"

    sidecar_hex = sidecar_path.read_text(encoding="utf-8").strip()
    descriptor_hex = json.loads(descriptor_path.read_text(encoding="utf-8"))["sha256"]
    assert descriptor_hex == sidecar_hex


def test_package_catalogue_malformed_source_date_epoch(tmp_path: Path) -> None:
    """AC30: non-integer SOURCE_DATE_EPOCH => exit 1 with error."""
    root = _make_fixture_catalogue(tmp_path)
    output = tmp_path / "output"
    args = _make_args(root, output=output)

    stderr_buf = io.StringIO()
    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "not-an-integer"}):
        with contextlib.redirect_stderr(stderr_buf):
            result = run(args)

    assert result == 1
    err = stderr_buf.getvalue()
    assert "SOURCE_DATE_EPOCH" in err
    assert "not-an-integer" in err


def test_package_catalogue_empty_source_date_epoch_treated_as_unset(tmp_path: Path) -> None:
    """AC30: empty SOURCE_DATE_EPOCH is treated as unset, not an error."""
    root = _make_fixture_catalogue(tmp_path)
    output = tmp_path / "output"
    args = _make_args(root, output=output)

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": ""}):
        result = run(args)

    assert result == 0


def test_package_catalogue_published_at_default(tmp_path: Path) -> None:
    """AC19 default: published_at is a valid ISO-8601 UTC timestamp without microseconds."""
    root = _make_fixture_catalogue(tmp_path)
    output = tmp_path / "output"
    args = _make_args(root, output=output, published_at=None)

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        run(args)

    descriptor_path = output / "catalogues" / "engineering" / "channels" / "stable.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    assert "published_at" in descriptor
    assert "." not in descriptor["published_at"]
    # Must be parseable as an ISO-8601 datetime
    from datetime import datetime
    dt = datetime.fromisoformat(descriptor["published_at"])
    assert dt is not None


def test_package_catalogue_manifest_digest_matches_archived_bytes(tmp_path: Path) -> None:
    """AC12: sha256 in manifest files[] matches bytes actually stored in archive."""
    root = _make_fixture_catalogue(tmp_path)
    output = tmp_path / "output"

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        run(_make_args(root, output=output))

    archive_path = output / "catalogues" / "engineering" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    archive_bytes = archive_path.read_bytes()

    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tf:
        mf = tf.extractfile("catalogue-manifest.json")
        assert mf is not None
        manifest = json.loads(mf.read())

        # Check a known file
        pack_toml_entry = next(
            (f for f in manifest["files"] if f["path"] == "packs/core/pack.toml"),
            None,
        )
        assert pack_toml_entry is not None

        member_bytes_f = tf.extractfile("packs/core/pack.toml")
        assert member_bytes_f is not None
        member_bytes = member_bytes_f.read()

    assert hashlib.sha256(member_bytes).hexdigest() == pack_toml_entry["sha256"]


def test_package_catalogue_packs_version_matches_archived_pack_toml(tmp_path: Path) -> None:
    """AC14: packs[].version in manifest == version in archived pack.toml bytes."""
    root = _make_fixture_catalogue(tmp_path)
    output = tmp_path / "output"

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        run(_make_args(root, output=output))

    archive_path = output / "catalogues" / "engineering" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    archive_bytes = archive_path.read_bytes()

    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tf:
        mf = tf.extractfile("catalogue-manifest.json")
        assert mf is not None
        manifest = json.loads(mf.read())

        pack_entry = next((p for p in manifest["packs"] if p["name"] == "core"), None)
        assert pack_entry is not None

        pack_toml_f = tf.extractfile("packs/core/pack.toml")
        assert pack_toml_f is not None
        pack_data = tomllib.loads(pack_toml_f.read().decode("utf-8"))

    assert pack_entry["version"] == pack_data["pack"]["version"]


@pytest.mark.skipif(sys.platform == "win32", reason="st_nlink hard-link detection is POSIX-only")
def test_package_catalogue_hardlink_rejected(tmp_path: Path) -> None:
    """AC29: hard link inside packs/ causes non-zero exit."""
    root = _make_fixture_catalogue(tmp_path)
    original = root / "packs" / "core" / "pack.toml"
    hardlink = root / "packs" / "core" / "hardlink.toml"
    os.link(str(original), str(hardlink))

    output = tmp_path / "output"
    args = _make_args(root, output=output)

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = run(args)

    assert result == 1


@pytest.mark.parametrize(
    "flag,value",
    [
        ("bundle", "../../x"),
        ("bundle", ".."),
        ("release", "../../x"),
        ("release", ".."),
        ("channel", "../../x"),
        ("channel", ".."),
    ],
)
def test_package_catalogue_flag_traversal_rejected(flag: str, value: str, tmp_path: Path) -> None:
    """AC32: --bundle/--release/--channel with traversal values cause exit 1."""
    root = _make_fixture_catalogue(tmp_path)
    output = tmp_path / "output"
    kwargs: dict = {"bundle": "engineering", "release": "0.1.0", "channel": "stable"}
    kwargs[flag] = value
    args = _make_args(root, output=output, **kwargs)

    result = run(args)
    assert result == 1


# ---------------------------------------------------------------------------
# T5: Goal-based checks
# ---------------------------------------------------------------------------


def test_no_git_shell_out_in_package_catalogue() -> None:
    """AC23: no subprocess/git shell-out in package_catalogue.py."""
    import re
    source_path = Path(package_catalogue.__file__)
    content = source_path.read_text(encoding="utf-8")
    patterns = [
        r"import subprocess",
        r"subprocess\.",
        r"os\.system\(",
        r"\.Popen\(",
        r"import shlex",
        r"shlex\.",
        r'\["git"',
    ]
    for pat in patterns:
        assert not re.search(pat, content), f"Found disallowed pattern {pat!r} in package_catalogue.py"


def test_no_new_runtime_dependency() -> None:
    """AC27: package_catalogue.py imports only stdlib and agentbundle."""
    import ast
    source_path = Path(package_catalogue.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    stdlib_modules = {
        "gzip", "hashlib", "io", "json", "os", "re", "sys", "tarfile", "tomllib",
        "datetime", "pathlib", "typing", "contextlib", "collections", "__future__",
        "abc", "argparse", "functools", "itertools", "math", "shutil", "string",
        "time", "types", "warnings", "copy",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                assert top in stdlib_modules or top == "agentbundle", (
                    f"Non-stdlib/agentbundle import: {alias.name}"
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                assert top in stdlib_modules or top == "agentbundle" or node.level > 0, (
                    f"Non-stdlib/agentbundle import from: {node.module}"
                )
