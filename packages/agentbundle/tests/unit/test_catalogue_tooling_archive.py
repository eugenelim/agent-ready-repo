"""Unit tests for agentbundle.catalogue_tooling.archive (Wave 3, ini-005).

Coverage:
  - check_members() — safety primitive checks (T1, exported for unit tests)
  - verify_archive() — full pipeline (T2)

Test archive construction uses tarfile directly (in-memory via io.BytesIO
or written to tmp_path).  No external fixtures required.

AC17 (verify_catalogue round-trip after extraction) is exercised only in
test_archive_valid_passes_all; other pipeline tests stop before AC17 fires
because they trigger safety errors that cause early return.
"""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

from agentbundle.catalogue_tooling.archive import check_members, verify_archive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add_member(tf: tarfile.TarFile, name: str, data: bytes) -> None:
    """Add a regular file member to an open TarFile."""
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    tf.addfile(info, io.BytesIO(data))


def _make_manifest_bytes(files: dict[str, bytes]) -> bytes:
    """Return a valid catalogue-manifest.json payload with correct sha256 hashes."""
    file_entries = [
        {"path": name, "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in files.items()
    ]
    return json.dumps(
        {
            "schema": 1,
            "bundle": "test",
            "release": "0.1.0",
            "generated_at": "2026-07-24T00:00:00Z",
            "source_revision": None,
            "files": file_entries,
            "packs": [],
        }
    ).encode("utf-8")


def _make_valid_archive(tmp_path: Path, extra_data_files: dict[str, bytes] | None = None) -> Path:
    """Create a minimal, fully-valid catalogue .tar.gz at tmp_path/test.tar.gz.

    Uses AGENTS.md as the catalogue marker so that the AC17 round-trip
    (verify_catalogue on the extracted dir) passes without a catalogue.toml
    or any packs — all verify steps that require config skip gracefully.
    """
    catalogue_marker = b"# AGENTS\n"
    files: dict[str, bytes] = {"AGENTS.md": catalogue_marker}
    if extra_data_files:
        files.update(extra_data_files)

    manifest = _make_manifest_bytes(files)
    archive_path = tmp_path / "test.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tf:
        for name, data in files.items():
            _add_member(tf, name, data)
        _add_member(tf, "catalogue-manifest.json", manifest)
    return archive_path


# ---------------------------------------------------------------------------
# T1 — check_members safety primitives
# ---------------------------------------------------------------------------


def test_no_absolute_paths_detected():
    """TarInfo with absolute path → CAT-V-ARC-004."""
    m = tarfile.TarInfo(name="/etc/passwd")
    diags = check_members([m])
    codes = [d.code for d in diags]
    assert "CAT-V-ARC-004" in codes


def test_traversal_detected():
    """TarInfo with traversal path (../escape) → CAT-V-ARC-005."""
    m = tarfile.TarInfo(name="../escape")
    diags = check_members([m])
    codes = [d.code for d in diags]
    assert "CAT-V-ARC-005" in codes


def test_symlink_in_archive_detected():
    """TarInfo with type=SYMTYPE → CAT-V-ARC-006."""
    m = tarfile.TarInfo(name="link")
    m.type = tarfile.SYMTYPE
    diags = check_members([m])
    codes = [d.code for d in diags]
    assert "CAT-V-ARC-006" in codes


def test_hard_link_detected():
    """TarInfo with type=LNKTYPE → CAT-V-ARC-006."""
    m = tarfile.TarInfo(name="hardlink")
    m.type = tarfile.LNKTYPE
    diags = check_members([m])
    codes = [d.code for d in diags]
    assert "CAT-V-ARC-006" in codes


def test_duplicate_members_detected():
    """Two TarInfo objects with identical name → CAT-V-ARC-008."""
    m1 = tarfile.TarInfo(name="file.txt")
    m2 = tarfile.TarInfo(name="file.txt")
    diags = check_members([m1, m2])
    codes = [d.code for d in diags]
    assert "CAT-V-ARC-008" in codes


def test_case_collision_detected():
    """'README.md' and 'readme.md' differ only by case → CAT-V-ARC-009."""
    m1 = tarfile.TarInfo(name="README.md")
    m2 = tarfile.TarInfo(name="readme.md")
    diags = check_members([m1, m2])
    codes = [d.code for d in diags]
    assert "CAT-V-ARC-009" in codes


def test_clean_members_no_diags():
    """Regular file members with distinct names → no diagnostics."""
    m1 = tarfile.TarInfo(name="catalogue.toml")
    m2 = tarfile.TarInfo(name="README.md")
    diags = check_members([m1, m2])
    assert diags == []


# ---------------------------------------------------------------------------
# T2 — verify_archive pipeline
# ---------------------------------------------------------------------------


def test_archive_valid_passes_all(tmp_path):
    """A minimal valid .tar.gz with correct manifest → ok=True.

    Uses AGENTS.md as the catalogue marker.  The AC17 round-trip succeeds
    because verify_catalogue on a dir with only AGENTS.md (no catalogue.toml)
    skips all config-dependent steps and returns ok=True.
    """
    archive_path = _make_valid_archive(tmp_path)
    result = verify_archive(archive_path)
    assert result.ok, [d.message for d in result.diagnostics]


def test_archive_digest_mismatch_fails(tmp_path):
    """Manifest with wrong sha256 for a file → CAT-V-ARC-012."""
    catalogue_marker = b"# AGENTS\n"
    bad_manifest = json.dumps(
        {
            "schema": 1,
            "bundle": "test",
            "release": "0.1.0",
            "generated_at": "2026-07-24T00:00:00Z",
            "source_revision": None,
            "files": [{"path": "AGENTS.md", "sha256": "deadbeef" * 8}],
            "packs": [],
        }
    ).encode("utf-8")

    archive_path = tmp_path / "bad_digest.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tf:
        _add_member(tf, "AGENTS.md", catalogue_marker)
        _add_member(tf, "catalogue-manifest.json", bad_manifest)

    result = verify_archive(archive_path)
    assert not result.ok
    codes = [d.code for d in result.diagnostics]
    assert "CAT-V-ARC-012" in codes


def test_archive_undeclared_member_fails(tmp_path):
    """Archive member not listed in manifest → CAT-V-ARC-013."""
    catalogue_marker = b"# AGENTS\n"
    extra = b"extra content"
    # Manifest declares only AGENTS.md, not extra.txt
    manifest = _make_manifest_bytes({"AGENTS.md": catalogue_marker})

    archive_path = tmp_path / "undeclared.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tf:
        _add_member(tf, "AGENTS.md", catalogue_marker)
        _add_member(tf, "extra.txt", extra)
        _add_member(tf, "catalogue-manifest.json", manifest)

    result = verify_archive(archive_path)
    assert not result.ok
    codes = [d.code for d in result.diagnostics]
    assert "CAT-V-ARC-013" in codes


def test_archive_sidecar_mismatch_early_exit(tmp_path):
    """Sidecar .sha256 file with wrong hash → CAT-V-ARC-001, early return."""
    archive_path = _make_valid_archive(tmp_path)
    sidecar = tmp_path / "test.tar.gz.sha256"
    sidecar.write_text("0000000000000000000000000000000000000000000000000000000000000000  test.tar.gz\n", encoding="utf-8", newline="\n")  # noqa: E501

    result = verify_archive(archive_path, sha256_file=sidecar)
    assert not result.ok
    codes = [d.code for d in result.diagnostics]
    assert "CAT-V-ARC-001" in codes
    # Early-exit: only the sidecar diagnostic should be present
    assert len(result.diagnostics) == 1


def test_archive_traversal_rejected(tmp_path):
    """Archive member path '../secret' → CAT-V-ARC-005, safety early return."""
    archive_path = tmp_path / "traversal.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tf:
        info = tarfile.TarInfo(name="../secret")
        info.size = 5
        tf.addfile(info, io.BytesIO(b"oops!"))

    result = verify_archive(archive_path)
    assert not result.ok
    codes = [d.code for d in result.diagnostics]
    assert "CAT-V-ARC-005" in codes


def test_archive_symlink_rejected(tmp_path):
    """Archive member that is a symlink → CAT-V-ARC-006, safety early return."""
    archive_path = tmp_path / "symlink.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tf:
        info = tarfile.TarInfo(name="link_to_etc")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        info.size = 0
        tf.addfile(info)

    result = verify_archive(archive_path)
    assert not result.ok
    codes = [d.code for d in result.diagnostics]
    assert "CAT-V-ARC-006" in codes


def test_archive_not_gzip(tmp_path):
    """Non-gzip file → CAT-V-ARC-002."""
    bad_file = tmp_path / "notgzip.tar.gz"
    bad_file.write_bytes(b"this is not a gzip file at all\n")

    result = verify_archive(bad_file)
    assert not result.ok
    codes = [d.code for d in result.diagnostics]
    assert "CAT-V-ARC-002" in codes


def _make_source_archive(path: Path, *, prefixed: bool = False) -> None:
    """Write a minimal source-distribution tar.gz containing self-hosted-source-manifest.json."""
    import gzip

    manifest_name = (
        "catalogue-source-1.0.0/self-hosted-source-manifest.json"
        if prefixed
        else "self-hosted-source-manifest.json"
    )
    buf = io.BytesIO()
    with (
        gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz,
        tarfile.open(fileobj=gz, mode="w") as tar,  # type: ignore[arg-type]
    ):
        _add_member(tar, manifest_name, b'{"kind":"agentbundle-self-hosted-source"}')
    path.write_bytes(buf.getvalue())


def test_verify_archive_refuses_source_distribution_no_prefix(tmp_path):
    """verify_archive() on a source archive (flat manifest) → CAT-V-ARC-016."""
    archive = tmp_path / "source.tar.gz"
    _make_source_archive(archive, prefixed=False)

    result = verify_archive(archive)
    assert not result.ok
    codes = [d.code for d in result.diagnostics]
    assert "CAT-V-ARC-016" in codes


def test_verify_archive_refuses_source_distribution_prefixed(tmp_path):
    """verify_archive() on a source archive (prefixed manifest) → CAT-V-ARC-016."""
    archive = tmp_path / "source.tar.gz"
    _make_source_archive(archive, prefixed=True)

    result = verify_archive(archive)
    assert not result.ok
    codes = [d.code for d in result.diagnostics]
    assert "CAT-V-ARC-016" in codes
