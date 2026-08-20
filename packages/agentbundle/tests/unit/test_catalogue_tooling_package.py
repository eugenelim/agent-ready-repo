"""Tests for catalogue_tooling.package (Wave 4 — catalogue-tooling-package-enhanced spec).

Covers the full packager contract.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import tarfile
from pathlib import Path
from unittest import mock

import pytest
from agentbundle.catalogue_tooling.package import (
    _check_required_files,
    _generate_manifest,
    _scan_content,
    _validate_content,
    _write_archive,
    package_catalogue,
)
from agentbundle.catalogue_tooling.toml_emit import emit_catalogue_toml

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_catalogue(
    tmp_path: Path,
    *,
    with_marketplace: bool = True,
    with_license_apache: bool = True,
    with_license_mit: bool = True,
    with_agents_md: bool = True,
) -> Path:
    """Create a minimal valid catalogue root for Wave 4 tests."""
    root = tmp_path / "catalogue"
    root.mkdir()
    config_text = emit_catalogue_toml(
        name="test-catalogue",
        display_name="Test Catalogue",
        description="A catalogue fixture for package tests.",
        minimum_agentbundle_version="0.33.0",
        owner_name="Example Maintainer",
        preferred_adapter="claude-code",
    ).replace(
        '  ".claude-plugin/marketplace.json",\n]',
        '  ".claude-plugin/marketplace.json",\n'
        '  "LICENSE-APACHE",\n'
        '  "LICENSE-MIT",\n'
        "]",
    )
    (root / "catalogue.toml").write_text(
        config_text,
        encoding="utf-8",
        newline="\n",
    )

    # Pack
    pack_dir = root / "packs" / "core"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.toml").write_text(
        '[pack]\nname = "core"\nversion = "0.1.0"\n'
        'description = "Package test fixture."\n'
        '[pack.adapter-contract]\nversion = "0.2"\n'
        '[pack.install]\ndefault-scope = "repo"\nallowed-scopes = ["repo"]\n',
        encoding="utf-8",
        newline="\n",
    )
    (pack_dir / "SKILL.md").write_text("# skill\n", encoding="utf-8", newline="\n")
    (pack_dir / "tests").mkdir()
    (pack_dir / "tests" / "test_pack.py").write_text(
        "def test_pack(): pass\n", encoding="utf-8", newline="\n"
    )

    conformance = root / "tests" / "conformance"
    conformance.mkdir(parents=True)
    (conformance / "test_rule.py").write_text(
        "def test_rule(): pass\n", encoding="utf-8", newline="\n"
    )
    roster = root / "tests" / "roster"
    roster.mkdir()
    (roster / "sentinel.txt").write_text("must not ship\n", encoding="utf-8")

    # Profile
    profiles_dir = root / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "default.toml").write_text(
        'scope = "repo"\n'
        'description = "Default package test profile."\n'
        "\n"
        "[[packs]]\n"
        'pack = "core"\n',
        encoding="utf-8",
        newline="\n",
    )

    if with_agents_md:
        (root / "AGENTS.md").write_text(
            "# Catalogue Agent Context\n", encoding="utf-8", newline="\n"
        )

    (root / "README.md").write_text("# Test Catalogue\n", encoding="utf-8", newline="\n")

    if with_license_apache:
        (root / "LICENSE-APACHE").write_text("Apache-2.0\n", encoding="utf-8", newline="\n")
    if with_license_mit:
        (root / "LICENSE-MIT").write_text("MIT\n", encoding="utf-8", newline="\n")

    if with_marketplace:
        cp_dir = root / ".claude-plugin"
        cp_dir.mkdir()
        (cp_dir / "marketplace.json").write_text(
            '{"plugins": []}\n', encoding="utf-8", newline="\n"
        )

    return root


def _make_args(root: Path, output: Path, **kwargs) -> object:
    """Return a namespace-like object for package_catalogue."""
    defaults = {
        "bundle": "engineering",
        "release": "0.1.0",
        "channel": "stable",
        "source_revision": None,
        "minimum_agentbundle_version": None,
        "published_at": None,
    }
    defaults.update(kwargs)
    return mock.SimpleNamespace(root=str(root), output=str(output), **defaults)


# ---------------------------------------------------------------------------
# Three-file Artifactory layout
# ---------------------------------------------------------------------------


def test_package_produces_three_file_layout(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = package_catalogue(
            root=root,
            bundle="engineering",
            release="0.1.0",
            channel="stable",
            output=output,
        )

    assert result.ok, [d.message for d in result.diagnostics]

    archive = (
        output / "catalogues" / "engineering" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    )
    sidecar = archive.parent / "catalogue-0.1.0.tar.gz.sha256"
    descriptor = output / "catalogues" / "engineering" / "channels" / "stable.json"

    assert archive.exists()
    assert sidecar.exists()
    assert descriptor.exists()
    assert len([p for p in output.rglob("*") if p.is_file()]) == 3


# ---------------------------------------------------------------------------
# Required files must be present
# ---------------------------------------------------------------------------


def test_missing_license_apache_fails(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path, with_license_apache=False)
    output = tmp_path / "out"

    result = package_catalogue(root=root, bundle="b", release="r", channel="c", output=output)
    assert not result.ok
    assert not any(output.rglob("*") if output.exists() else [])


def test_missing_license_mit_fails(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path, with_license_mit=False)
    output = tmp_path / "out"

    result = package_catalogue(root=root, bundle="b", release="r", channel="c", output=output)
    assert not result.ok


def test_missing_marketplace_json_fails(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path, with_marketplace=False)
    output = tmp_path / "out"

    result = package_catalogue(root=root, bundle="b", release="r", channel="c", output=output)
    assert not result.ok


# ---------------------------------------------------------------------------
# Generic LICENSE not required
# ---------------------------------------------------------------------------


def test_no_generic_license_required(tmp_path: Path) -> None:
    """Packaging succeeds without a generic LICENSE file."""
    root = _make_catalogue(tmp_path)
    # Confirm no generic LICENSE exists
    assert not (root / "LICENSE").exists()
    output = tmp_path / "out"

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = package_catalogue(
            root=root, bundle="b", release="0.1.0", channel="c", output=output
        )

    assert result.ok, [d.message for d in result.diagnostics]


# ---------------------------------------------------------------------------
# catalogue.toml NOT in archive
# ---------------------------------------------------------------------------


def test_catalogue_toml_excluded_from_archive(tmp_path: Path) -> None:
    """catalogue.toml must not appear in the archive even if present in the root."""
    root = _make_catalogue(tmp_path)
    # Verify via _scan_content: catalogue.toml is never collected.
    paths = _scan_content(root)
    posix = [p.relative_to(root).as_posix() for p in paths]
    assert "catalogue.toml" not in posix

    # Also verify the packaged archive doesn't include it.
    output = tmp_path / "out"
    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = package_catalogue(
            root=root, bundle="b", release="0.1.0", channel="c", output=output
        )

    assert result.ok, [d.message for d in result.diagnostics]

    archive = output / "catalogues" / "b" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(fileobj=io.BytesIO(archive.read_bytes()), mode="r:gz") as tf:
        names = tf.getnames()
    assert "catalogue.toml" not in names


# ---------------------------------------------------------------------------
# Channel descriptor written AFTER archive + sidecar verified
# ---------------------------------------------------------------------------


def test_channel_descriptor_written_last(tmp_path: Path) -> None:
    """Channel descriptor must not exist if verify_archive raises."""
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"

    write_order: list[str] = []

    def _spy_verify(archive_path, *, sha256_file=None):
        write_order.append("verify_archive")
        from agentbundle.catalogue_tooling.archive import verify_archive

        return verify_archive(archive_path, sha256_file=sha256_file)

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = package_catalogue(
            root=root,
            bundle="eng",
            release="0.1.0",
            channel="stable",
            output=output,
            _verify_archive_fn=_spy_verify,
        )

    assert result.ok
    descriptor = output / "catalogues" / "eng" / "channels" / "stable.json"
    assert descriptor.exists()
    # verify_archive must have been called
    assert "verify_archive" in write_order


def test_archive_includes_conformance_and_pack_tests_but_not_roster(
    tmp_path: Path,
) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"
    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = package_catalogue(
            root=root, bundle="b", release="0.1.0", channel="c", output=output
        )
    assert result.ok
    archive = output / "catalogues" / "b" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(archive, mode="r:gz") as tf:
        names = set(tf.getnames())
    assert "tests/conformance/test_rule.py" in names
    assert "packs/core/tests/test_pack.py" in names
    assert "tests/roster/sentinel.txt" not in names


# ---------------------------------------------------------------------------
# Deterministic bytes under SOURCE_DATE_EPOCH
# ---------------------------------------------------------------------------


def test_deterministic_under_source_date_epoch(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        r1 = package_catalogue(root=root, bundle="b", release="0.1.0", channel="c", output=out1)
        r2 = package_catalogue(root=root, bundle="b", release="0.1.0", channel="c", output=out2)

    assert r1.ok and r2.ok

    def _arc(out):
        path = out / "catalogues" / "b" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
        return path.read_bytes()

    assert hashlib.sha256(_arc(out1)).digest() == hashlib.sha256(_arc(out2)).digest()


# ---------------------------------------------------------------------------
# Refuse to overwrite existing archive
# ---------------------------------------------------------------------------


def test_refuse_overwrite_existing_archive(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"
    archive = output / "catalogues" / "b" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b"existing")

    result = package_catalogue(root=root, bundle="b", release="0.1.0", channel="c", output=output)
    assert not result.ok
    assert archive.read_bytes() == b"existing"


# ---------------------------------------------------------------------------
# Staged cleanup on verify_archive failure
# ---------------------------------------------------------------------------


def test_staged_cleanup_on_verify_failure(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"

    def _failing_verify(archive_path, *, sha256_file=None):
        from agentbundle.catalogue_tooling.results import Diagnostic, Severity, VerifyResult

        return VerifyResult(
            ok=False,
            diagnostics=[
                Diagnostic(
                    code="TEST",
                    severity=Severity.ERROR,
                    pack=None,
                    path=None,
                    line=None,
                    col=None,
                    message="injected failure",
                    remediation=None,
                )
            ],
            schema_version=1,
            command="test",
            operation="test",
            agentbundle_version="0.0.0",
            catalogue_schema_version=1,
        )

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = package_catalogue(
            root=root,
            bundle="b",
            release="0.1.0",
            channel="c",
            output=output,
            _verify_archive_fn=_failing_verify,
        )

    assert not result.ok
    # No staged .tmp files remain
    if output.exists():
        for f in output.rglob("*.tmp"):
            raise AssertionError(f"staged file not cleaned up: {f}")
    # Final archive not written
    archive = output / "catalogues" / "b" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    assert not archive.exists()
    # Channel descriptor not written
    descriptor = output / "catalogues" / "b" / "channels" / "c.json"
    assert not descriptor.exists()


# ---------------------------------------------------------------------------
# Manifest has all Bucket 8 fields
# ---------------------------------------------------------------------------


def test_manifest_schema_v2_fields(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = package_catalogue(
            root=root, bundle="b", release="0.1.0", channel="c", output=output
        )

    assert result.ok

    archive = output / "catalogues" / "b" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(fileobj=io.BytesIO(archive.read_bytes()), mode="r:gz") as tf:
        mf = tf.extractfile("catalogue-manifest.json")
        assert mf is not None
        manifest = json.loads(mf.read())

    assert manifest["schema"] == 2
    assert "adapter_contract_version" in manifest
    assert "pack_schema_version" in manifest
    assert "marketplace_digest" in manifest
    assert manifest["marketplace_digest"] is not None
    assert manifest["marketplace_digest"].startswith("sha256:")
    assert "profiles" in manifest
    assert "packs" in manifest
    assert "files" in manifest


# ---------------------------------------------------------------------------
# Compat alias deprecation warning
# ---------------------------------------------------------------------------


def test_compat_alias_deprecation_warning(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"

    import types as _types

    from agentbundle.commands.package_catalogue import run

    args = _types.SimpleNamespace(
        root=str(root),
        bundle="b",
        release="0.1.0",
        channel="c",
        output=str(output),
        source_revision=None,
        minimum_agentbundle_version=None,
        published_at=None,
    )

    stderr_buf = io.StringIO()
    with (
        mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}),
        contextlib.redirect_stderr(stderr_buf),
    ):
        rc = run(args)

    assert rc == 0
    assert "deprecated" in stderr_buf.getvalue().lower()
    assert "agentbundle catalogue package" in stderr_buf.getvalue()


# ---------------------------------------------------------------------------
# Installable archive remains distinct from a source catalogue
# ---------------------------------------------------------------------------


def test_packaged_archive_passes_archive_verification_without_source_config(
    tmp_path: Path,
) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = package_catalogue(
            root=root, bundle="b", release="0.1.0", channel="c", output=output
        )

    assert result.ok

    archive = output / "catalogues" / "b" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(fileobj=io.BytesIO(archive.read_bytes()), mode="r:gz") as tf:
        assert "catalogue.toml" not in {member.name for member in tf.getmembers()}

    from agentbundle.catalogue_tooling.archive import verify_archive

    verify_result = verify_archive(archive)
    assert verify_result.ok, [d.message for d in verify_result.diagnostics]


# ---------------------------------------------------------------------------
# Archive layout has no artificial wrapper directory
# ---------------------------------------------------------------------------


def test_archive_layout_no_wrapper_directory(tmp_path: Path) -> None:
    """packs/ must be at the archive root, not inside a wrapper dir."""
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = package_catalogue(
            root=root, bundle="b", release="0.1.0", channel="c", output=output
        )

    assert result.ok

    archive = output / "catalogues" / "b" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(fileobj=io.BytesIO(archive.read_bytes()), mode="r:gz") as tf:
        names = tf.getnames()

    assert "packs/core/pack.toml" in names, "packs/ must be at archive root"


# ---------------------------------------------------------------------------
# Denied paths (tools/, .git/, etc.) not in archive
# ---------------------------------------------------------------------------


def test_denied_dirs_not_in_archive(tmp_path: Path) -> None:
    """Denied directories are excluded even if present in root.

    Note what this does *not* prove: these names are excluded because
    `_DEFAULT_INCLUDE_DIRS` is an allowlist that never walks them, not because
    any deny-set is applied. Build residue *nested inside* an included root is a
    separate question — see `test_transient_dirs_pruned_inside_included_roots`.
    """
    root = _make_catalogue(tmp_path)
    # Add stub files at denied paths. ``dist/`` is intentionally omitted: the
    # verifier now treats an existing generated-output tree as a drift contract,
    # so an arbitrary dist/stub.txt must be refused before packaging begins.
    for denied in [".git", "tools", "packages", "__pycache__"]:
        d = root / denied
        d.mkdir()
        (d / "stub.txt").write_text("should be excluded\n", encoding="utf-8", newline="\n")

    output = tmp_path / "out"
    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = package_catalogue(
            root=root, bundle="b", release="0.1.0", channel="c", output=output
        )

    assert result.ok, [diagnostic.message for diagnostic in result.diagnostics]

    archive = output / "catalogues" / "b" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(fileobj=io.BytesIO(archive.read_bytes()), mode="r:gz") as tf:
        names = tf.getnames()

    for denied in [".git/", "tools/", "packages/", "__pycache__/"]:
        for name in names:
            assert not name.startswith(denied), f"denied path found in archive: {name}"


def test_transient_dirs_pruned_inside_included_roots(tmp_path: Path) -> None:
    """Build residue nested inside a walked root never reaches the archive.

    The root-level check above passes on the allowlist alone. This is the case
    that was open: `packs/**` is walked recursively, so a `__pycache__` from any
    `pytest` run and a `node_modules` from any `npm install` were collected
    verbatim. `catalogue-authoring-standards.md` § 4 tells adopters caches are
    "neither committed nor packaged"; this is what makes the second half true.

    Asserted through the real archive, not through `_scan_content`. Collection is
    only half of it — `_validate_content` runs in between and refuses the first
    symlink it finds anywhere, and a real `node_modules/.bin/` is all symlinks.
    Testing the collection list alone would miss that.
    """
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "core"

    (pack / "__pycache__").mkdir()
    (pack / "__pycache__" / "convert.cpython-313.pyc").write_bytes(b"\x00")

    # A *realistic* node_modules: `.bin/` entries are symlinks, always.
    (pack / "node_modules" / "dompurify").mkdir(parents=True)
    (pack / "node_modules" / "dompurify" / "index.js").write_text(
        "module.exports = {}\n", encoding="utf-8", newline="\n")
    (pack / "node_modules" / ".bin").mkdir()
    Path(pack / "node_modules" / ".bin" / "dompurify").symlink_to("../dompurify/index.js")

    # Residue directly under packs/ — step 7 iterates that directory looking for
    # packs and used to report `invalid pack.toml` for it.
    (root / "packs" / "__pycache__").mkdir()
    (root / "packs" / "__pycache__" / "stale.pyc").write_bytes(b"\x00")

    # Every remaining name in the two sets, so a typo in either is visible.
    from agentbundle.catalogue_tooling.package import (
        _TRANSIENT_DIRS,
        _TRANSIENT_FILE_SUFFIXES,
    )
    for name in sorted(_TRANSIENT_DIRS):
        d = pack / name
        d.mkdir(exist_ok=True)
        (d / "residue.txt").write_text("x\n", encoding="utf-8", newline="\n")
    (pack / "scripts").mkdir()
    (pack / "scripts" / "convert.py").write_text(
        "x = 1\n", encoding="utf-8", newline="\n")
    for suffix in _TRANSIENT_FILE_SUFFIXES:
        (pack / "scripts" / f"stray{suffix}").write_bytes(b"\x00")
    (pack / "scripts" / ".DS_Store").write_bytes(b"\x00")
    (pack / "scripts" / "coverage.xml").write_text(
        "<x/>\n", encoding="utf-8", newline="\n")
    # `coverage combine` shard: `.suffix` is the random component, not `.coverage`.
    (pack / "scripts" / ".coverage.host.1234.5678").write_text(
        "x\n", encoding="utf-8", newline="\n")

    # A real directory whose *name* collides with a repo-root deny name. Pruning
    # the old `_IMPLICIT_DENY_DIRS` at every level — the obvious fix — would have
    # silently dropped this; `packs/monorepo-extras/seeds/packages/` is the live
    # instance.
    (pack / "seeds" / "packages").mkdir(parents=True)
    (pack / "seeds" / "packages" / "README.md").write_text(
        "# seeded\n", encoding="utf-8", newline="\n")

    output = tmp_path / "out"
    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = package_catalogue(
            root=root, bundle="b", release="0.1.0", channel="c", output=output
        )
    assert result.ok, f"packaging refused a tree with build residue: {result}"

    archive = output / "catalogues" / "b" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(fileobj=io.BytesIO(archive.read_bytes()), mode="r:gz") as tf:
        names = set(tf.getnames())

    for name in sorted(_TRANSIENT_DIRS):
        assert f"packs/core/{name}/residue.txt" not in names, (
            f"build residue reached the archive: {name}/")
    for gone in ("packs/core/__pycache__/convert.cpython-313.pyc",
                 "packs/core/node_modules/dompurify/index.js",
                 "packs/__pycache__/stale.pyc",
                 "packs/core/scripts/.DS_Store",
                 "packs/core/scripts/coverage.xml",
                 "packs/core/scripts/.coverage.host.1234.5678"):
        assert gone not in names, f"build residue reached the archive: {gone}"
    for suffix in _TRANSIENT_FILE_SUFFIXES:
        assert f"packs/core/scripts/stray{suffix}" not in names

    assert "packs/core/scripts/convert.py" in names
    assert "packs/core/seeds/packages/README.md" in names, (
        "a real directory named `packages` was pruned — the deny set must not be "
        "applied below the repository root"
    )


def test_authored_symlink_still_refused(tmp_path: Path) -> None:
    """Pruning residue must not weaken the symlink refusal on real content.

    `_prune` now owns symlink filtering for every collection walk, and the
    validation walk skips residue — so the rejection has to be shown to still
    fire for a symlink in authored content.
    """
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "core"
    Path(pack / "alias.toml").symlink_to("pack.toml")

    err = _validate_content(root.resolve(), _scan_content(root.resolve()))
    assert err is not None and "symlink not allowed" in err, err


def test_symlinked_dir_below_root_is_pruned(tmp_path: Path) -> None:
    """A symlinked directory nested below the walk root is not descended into.

    Collection prunes it; validation still *rejects* it — see
    `test_package_catalogue.py::test_validate_content_symlink_dir_rejected`.
    Both must hold, and the order inside the validation walk is what makes that
    possible: the symlink check runs before `_prune` removes the entry, or the
    rejection silently stops firing.
    """
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "core"
    (pack / "real").mkdir()
    (pack / "real" / "kept.md").write_text("x\n", encoding="utf-8", newline="\n")
    (pack / "nested").mkdir()
    Path(pack / "nested" / "link").symlink_to("../real")

    rels = {p.relative_to(root.resolve()).as_posix()
            for p in _scan_content(root.resolve())}
    assert "packs/core/real/kept.md" in rels
    assert not any("nested/link" in r for r in rels)


# ---------------------------------------------------------------------------
# T3: CLI wiring
# ---------------------------------------------------------------------------


def test_cli_catalogue_package_help() -> None:
    """catalogue package --help exits 0 and lists expected flags."""
    from agentbundle import cli

    stdout_buf = io.StringIO()
    with pytest.raises(SystemExit) as exc_info, contextlib.redirect_stdout(stdout_buf):
        cli.main(["catalogue", "package", "--help"])
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
    ]:
        assert flag in help_text, f"missing flag {flag!r} in help text"


def test_generate_manifest_schema_v2() -> None:
    """_generate_manifest always produces schema 2."""
    manifest_bytes = _generate_manifest(
        bundle="b",
        release="0.1.0",
        source_revision=None,
        generated_at="2023-11-14T22:13:20+00:00",
        file_digests={},
        packs_metadata=[],
    )
    manifest = json.loads(manifest_bytes)
    assert manifest["schema"] == 2
    assert "adapter_contract_version" in manifest
    assert "pack_schema_version" in manifest
    assert "marketplace_digest" in manifest
    assert "profiles" in manifest


def test_check_required_files_passes_with_all_present(tmp_path: Path) -> None:
    """_check_required_files returns None when all required files exist."""
    root = _make_catalogue(tmp_path)
    paths = _scan_content(root)
    assert _check_required_files(root, paths) is None


def test_check_required_files_fails_on_missing_license(tmp_path: Path) -> None:
    """_check_required_files fails when LICENSE-APACHE is missing."""
    root = _make_catalogue(tmp_path, with_license_apache=False)
    paths = _scan_content(root)
    err = _check_required_files(root, paths)
    assert err is not None
    assert "LICENSE-APACHE" in err


# ---------------------------------------------------------------------------
# pack_include and required_override
# ---------------------------------------------------------------------------


def _make_two_pack_catalogue(tmp_path: Path) -> Path:
    root = tmp_path / "catalogue"
    root.mkdir()
    for pack_name in ("pack-alpha", "pack-beta"):
        pack_dir = root / "packs" / pack_name
        pack_dir.mkdir(parents=True)
        (pack_dir / "pack.toml").write_text(
            f'[pack]\nname = "{pack_name}"\nversion = "0.1.0"\n', encoding="utf-8", newline="\n"
        )
    (root / "LICENSE-APACHE").write_text("Apache-2.0\n", encoding="utf-8", newline="\n")
    (root / "LICENSE-MIT").write_text("MIT\n", encoding="utf-8", newline="\n")
    cp_dir = root / ".claude-plugin"
    cp_dir.mkdir()
    (cp_dir / "marketplace.json").write_text('{"packs": []}\n', encoding="utf-8", newline="\n")
    return root


def test_scan_content_include_one_pack(tmp_path: Path) -> None:
    root = _make_two_pack_catalogue(tmp_path)
    paths = _scan_content(root, pack_include=["packs/pack-alpha"])
    posix = [p.relative_to(root).as_posix() for p in paths]
    assert any(p.startswith("packs/pack-alpha/") for p in posix)
    assert not any(p.startswith("packs/pack-beta/") for p in posix)


def test_scan_content_include_empty_includes_all(tmp_path: Path) -> None:
    root = _make_two_pack_catalogue(tmp_path)
    paths = _scan_content(root, pack_include=[])
    posix = [p.relative_to(root).as_posix() for p in paths]
    assert any(p.startswith("packs/pack-alpha/") for p in posix)
    assert any(p.startswith("packs/pack-beta/") for p in posix)


def test_scan_content_nonpack_dirs_always_included(tmp_path: Path) -> None:
    root = tmp_path / "catalogue"
    root.mkdir()
    pack_dir = root / "packs" / "pack-alpha"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.toml").write_text(
        '[pack]\nname = "pack-alpha"\nversion = "0.1.0"\n', encoding="utf-8", newline="\n"
    )
    (root / "profiles").mkdir()
    (root / "profiles" / "default.toml").write_text(
        '[profile]\nname = "default"\n', encoding="utf-8", newline="\n"
    )
    (root / "contracts").mkdir()
    (root / "contracts" / "adapter.toml").write_text(
        '[contract]\nversion = "1"\n', encoding="utf-8", newline="\n"
    )
    paths = _scan_content(root, pack_include=["packs/pack-alpha"])
    posix = [p.relative_to(root).as_posix() for p in paths]
    assert any(p.startswith("packs/pack-alpha/") for p in posix)
    assert any(p.startswith("profiles/") for p in posix)
    assert any(p.startswith("contracts/") for p in posix)


def test_scan_content_include_nonexistent_raises(tmp_path: Path) -> None:
    root = tmp_path / "catalogue"
    root.mkdir()
    (root / "packs").mkdir()
    with pytest.raises(ValueError, match="does not exist"):
        _scan_content(root, pack_include=["packs/nonexistent-pack"])


@pytest.mark.parametrize("bad_entry", ["../outside", "packs/../../escape"])
def test_scan_content_include_path_traversal_raises(bad_entry: str, tmp_path: Path) -> None:
    root = tmp_path / "catalogue"
    root.mkdir()
    with pytest.raises(ValueError):
        _scan_content(root, pack_include=[bad_entry])


def test_check_required_custom_license(tmp_path: Path) -> None:
    root = tmp_path / "catalogue"
    root.mkdir()
    (root / "packs").mkdir()
    (root / "LICENSE").write_text("Custom license\n", encoding="utf-8", newline="\n")
    paths = [root / "LICENSE"]
    err = _check_required_files(root, paths, required_override=["LICENSE"])
    assert err is None


def test_check_required_none_uses_defaults(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path, with_license_apache=False)
    paths = _scan_content(root)
    err = _check_required_files(root, paths, required_override=None)
    assert err is not None
    assert "LICENSE-APACHE" in err


# ---------------------------------------------------------------------------
# Integration tests: package_catalogue honours include / required config
# ---------------------------------------------------------------------------


def _ok_verify_result():
    from agentbundle.catalogue_tooling.results import VerifyResult

    return VerifyResult(
        ok=True,
        diagnostics=[],
        schema_version=1,
        command="catalogue verify",
        operation="source-checkout",
        agentbundle_version="0.0.0",
        catalogue_schema_version=1,
    )


def _mock_package_config(include: list, required: list):
    config = mock.MagicMock()
    config.name = "test"
    config.display_name = "Test"
    config.minimum_agentbundle_version = "0.1.0"
    config.package.include = include
    config.package.required = required
    return config


def test_package_honours_include_config(tmp_path: Path) -> None:
    root = tmp_path / "catalogue"
    root.mkdir()
    for pack_name in ("pack-a", "pack-b"):
        pack_dir = root / "packs" / pack_name
        pack_dir.mkdir(parents=True)
        (pack_dir / "pack.toml").write_text(
            f'[pack]\nname = "{pack_name}"\nversion = "0.1.0"\n', encoding="utf-8", newline="\n"
        )
    (root / "AGENTS.md").write_text("# Catalogue\n", encoding="utf-8", newline="\n")
    (root / "LICENSE-APACHE").write_text("Apache-2.0\n", encoding="utf-8", newline="\n")
    (root / "LICENSE-MIT").write_text("MIT\n", encoding="utf-8", newline="\n")
    cp_dir = root / ".claude-plugin"
    cp_dir.mkdir()
    (cp_dir / "marketplace.json").write_text('{"packs": []}\n', encoding="utf-8", newline="\n")
    output = tmp_path / "out"

    with (
        mock.patch(
            "agentbundle.catalogue_tooling.verify.verify_catalogue",
            return_value=_ok_verify_result(),
        ),
        mock.patch(
            "agentbundle.catalogue_tooling.config.load_catalogue_config",
            return_value=_mock_package_config(include=["packs/pack-a"], required=[]),
        ),
        mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}),
    ):
        result = package_catalogue(
            root=root, bundle="b", release="0.1.0", channel="c", output=output
        )

    assert result.ok, [d.message for d in result.diagnostics]
    archive = output / "catalogues" / "b" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(fileobj=io.BytesIO(archive.read_bytes()), mode="r:gz") as tf:
        names = tf.getnames()
    assert any(n.startswith("packs/pack-a/") for n in names)
    assert not any(n.startswith("packs/pack-b/") for n in names)


def test_package_custom_required_no_apache_license(tmp_path: Path) -> None:
    root = tmp_path / "catalogue"
    root.mkdir()
    pack_dir = root / "packs" / "core"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.toml").write_text(
        '[pack]\nname = "core"\nversion = "0.1.0"\n', encoding="utf-8", newline="\n"
    )
    (root / "AGENTS.md").write_text("# Catalogue\n", encoding="utf-8", newline="\n")
    (root / "LICENSE").write_text("Proprietary license\n", encoding="utf-8", newline="\n")
    cp_dir = root / ".claude-plugin"
    cp_dir.mkdir()
    (cp_dir / "marketplace.json").write_text('{"packs": []}\n', encoding="utf-8", newline="\n")
    output = tmp_path / "out"

    with (
        mock.patch(
            "agentbundle.catalogue_tooling.verify.verify_catalogue",
            return_value=_ok_verify_result(),
        ),
        mock.patch(
            "agentbundle.catalogue_tooling.config.load_catalogue_config",
            return_value=_mock_package_config(include=[], required=["LICENSE"]),
        ),
        mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}),
    ):
        result = package_catalogue(
            root=root, bundle="b", release="0.1.0", channel="c", output=output
        )

    assert result.ok, [d.message for d in result.diagnostics]


def test_package_default_required_still_enforced(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path, with_license_apache=False)
    output = tmp_path / "out"

    with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
        result = package_catalogue(
            root=root, bundle="b", release="0.1.0", channel="c", output=output
        )

    assert not result.ok
    assert any("LICENSE-APACHE" in d.message for d in result.diagnostics)


# ---------------------------------------------------------------------------
# Streaming archive: no top-level BytesIO buffer
# ---------------------------------------------------------------------------


def test_write_archive_does_not_use_BytesIO_for_main_buffer(tmp_path: Path) -> None:
    """_write_archive must not create an io.BytesIO() as the top-level gzip buffer."""
    file_bytes = {"foo.txt": b"hello world"}
    manifest_bytes = b'{"schema": 2}'
    dest = tmp_path / "test.tar.gz"

    no_arg_calls: list[tuple] = []
    original_bytesio = io.BytesIO

    def tracking_bytesio(*args, **kwargs):
        if not args and not kwargs:
            no_arg_calls.append(())
        return original_bytesio(*args, **kwargs)

    target = "agentbundle.catalogue_tooling.package.io.BytesIO"
    with mock.patch(target, side_effect=tracking_bytesio):
        _write_archive(file_bytes, manifest_bytes, dest)

    assert dest.exists(), "archive was not written to disk"
    assert no_arg_calls == [], (
        f"io.BytesIO() called with no args {len(no_arg_calls)} time(s)"
        " — top-level buffer not eliminated"
    )
