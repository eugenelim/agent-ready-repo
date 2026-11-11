"""Same-version refusal (AC-0007)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from agentbundle.commands.catalogue_package import run

from tests.unit.test_catalogue_tooling_package import _make_catalogue


def _make_args(root: Path, output: Path, **overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "root": str(root), "output": str(output), "bundle": "engineering",
        "release": "0.1.0", "channel": "stable", "source_revision": None,
        "minimum_agentbundle_version": None, "published_at": None,
        "flavor": "runtime", "force": False, "compare": None, "format": "table",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_existing_runtime_archive_refuses_with_exit_2(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"
    archive = (
        output / "catalogues" / "engineering" / "releases" / "0.1.0"
        / "catalogue-0.1.0.tar.gz"
    )
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b"existing")
    args = _make_args(
        root, output, flavor="runtime", force=False, compare=None, format="table",
    )
    assert run(args) == 2


# ---------------------------------------------------------------------------
# Remaining T3 tests (AC-0007 .. AC-0009, AC-0019, AC-0020)
# ---------------------------------------------------------------------------

import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import tarfile  # noqa: E402

import pytest  # noqa: E402
from agentbundle import cli  # noqa: E402
from agentbundle.catalogue_tooling import package as package_mod  # noqa: E402
from agentbundle.catalogue_tooling.archive import verify_archive  # noqa: E402
from agentbundle.catalogue_tooling.package import (  # noqa: E402
    ReleaseExistsError,
    _place_archive,
    package_catalogue,
)

_FLAVOURS = ("runtime", "source")


def _archive_path(output: Path, flavor: str) -> Path:
    if flavor == "runtime":
        return (
            output / "catalogues" / "engineering" / "releases" / "0.1.0"
            / "catalogue-0.1.0.tar.gz"
        )
    return (
        output / "catalogue-sources" / "engineering" / "releases" / "0.1.0"
        / "catalogue-source-0.1.0.tar.gz"
    )


def _tree(output: Path) -> list[tuple[str, str]]:
    return sorted(
        (p.relative_to(output).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest())
        for p in output.rglob("*")
        if p.is_file()
    )


def _tmp_files(output: Path) -> list[Path]:
    return sorted(output.rglob("*.tmp"))


def _channel(flavor: str) -> str:
    return "stable" if flavor == "runtime" else ""


def _seed_existing(output: Path, flavor: str) -> Path:
    archive = _archive_path(output, flavor)
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b"existing")
    return archive


@pytest.mark.parametrize("flavor", _FLAVOURS)
def test_refusal_exits_2_and_names_archive(
    tmp_path: Path, flavor: str, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"
    archive = _seed_existing(output, flavor)
    args = _make_args(root, output, flavor=flavor, channel=_channel(flavor))
    assert run(args) == 2
    err = capsys.readouterr().err
    assert str(archive.resolve()) in err
    assert "CAT-PKG-002:" in err


@pytest.mark.parametrize("flavor", _FLAVOURS)
def test_refused_run_leaves_output_tree_unchanged(tmp_path: Path, flavor: str) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"
    _seed_existing(output, flavor)
    (output / "unrelated.txt").write_text("keep\n", encoding="utf-8")
    before = _tree(output)
    assert run(_make_args(root, output, flavor=flavor, channel=_channel(flavor))) == 2
    assert _tree(output) == before
    assert not list(output.rglob("*.tmp"))


@pytest.mark.parametrize("flavor", _FLAVOURS)
def test_force_replaces_existing_release(tmp_path: Path, flavor: str) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"
    archive = _seed_existing(output, flavor)
    edited = "# skill edited by force test\n"
    (root / "packs" / "core" / "SKILL.md").write_text(edited, encoding="utf-8", newline="\n")

    args = _make_args(root, output, flavor=flavor, channel=_channel(flavor), force=True)
    assert run(args) == 0

    data = archive.read_bytes()
    assert data != b"existing"
    sidecar = archive.parent / (archive.name + ".sha256")
    assert sidecar.read_text(encoding="utf-8").strip() == hashlib.sha256(data).hexdigest()
    manifest_member = (
        "catalogue-manifest.json" if flavor == "runtime" else "self-hosted-source-manifest.json"
    )
    with tarfile.open(archive, "r:gz") as tar:
        extracted = tar.extractfile(manifest_member)
        assert extracted is not None
        manifest = json.loads(extracted.read())
    digest = next(f["sha256"] for f in manifest["files"] if f["path"] == "packs/core/SKILL.md")
    assert digest == hashlib.sha256(edited.encode("utf-8")).hexdigest()
    assert not _tmp_files(output)


def test_force_without_existing_archive_is_a_normal_run(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"
    assert run(_make_args(root, output, force=True)) == 0
    assert _archive_path(output, "runtime").is_file()


def test_runtime_race_between_staging_and_placement_refuses(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"
    archive = _archive_path(output, "runtime")

    def racing_verify(staged: Path, **kwargs: object):
        archive.write_bytes(b"racer")
        return verify_archive(staged, **kwargs)

    result = package_catalogue(
        root=root, bundle="engineering", release="0.1.0", channel="stable",
        output=output, _verify_archive_fn=racing_verify,
    )
    assert not result.ok
    assert [d.code for d in result.diagnostics] == ["CAT-PKG-002"]
    assert archive.read_bytes() == b"racer"
    assert not _tmp_files(output)
    assert not (output / "catalogues" / "engineering" / "channels" / "stable.json").exists()


def test_refused_run_leaves_another_runs_staged_files_alone(tmp_path: Path) -> None:
    """A losing run cleans up only its own staged files, never a concurrent winner's."""
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"
    archive = _archive_path(output, "runtime")
    foreign = [
        archive.parent / (archive.name + ".tmp"),
        archive.parent / (archive.name + ".sha256.tmp"),
    ]

    def racing_verify(staged: Path, **kwargs: object):
        assert staged not in foreign
        for path in foreign:
            path.write_bytes(b"winner-staged")
        archive.write_bytes(b"racer")
        return verify_archive(staged, **kwargs)

    result = package_catalogue(
        root=root, bundle="engineering", release="0.1.0", channel="stable",
        output=output, _verify_archive_fn=racing_verify,
    )
    assert [d.code for d in result.diagnostics] == ["CAT-PKG-002"]
    assert all(path.read_bytes() == b"winner-staged" for path in foreign)
    assert sorted(_tmp_files(output)) == sorted(foreign)


def test_staging_paths_differ_between_calls(tmp_path: Path) -> None:
    final = tmp_path / "catalogue-0.1.0.tar.gz"
    first, second = package_mod._staging_path(final), package_mod._staging_path(final)
    assert first != second
    assert first.parent == final.parent and first.name.endswith(".tmp")


def test_runtime_race_maps_to_exit_2_through_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"
    archive = _archive_path(output, "runtime")
    real_place = package_mod._place_archive

    def racing_place(staged: Path, dest: Path, *, force: bool) -> None:
        dest.write_bytes(b"racer")
        real_place(staged, dest, force=force)

    monkeypatch.setattr(package_mod, "_place_archive", racing_place)
    assert run(_make_args(root, output)) == 2
    assert archive.read_bytes() == b"racer"
    assert not _tmp_files(output)


def test_source_race_maps_to_exit_2_through_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"
    archive = _archive_path(output, "source")
    real_place = package_mod._place_archive

    def racing_place(staged: Path, dest: Path, *, force: bool) -> None:
        dest.write_bytes(b"racer")
        real_place(staged, dest, force=force)

    monkeypatch.setattr(package_mod, "_place_archive", racing_place)
    assert run(_make_args(root, output, flavor="source", channel=None)) == 2
    assert archive.read_bytes() == b"racer"
    assert not _tmp_files(output)
    assert not (archive.parent / (archive.name + ".sha256")).exists()


def _staged(tmp_path: Path) -> tuple[Path, Path]:
    staged = tmp_path / "rel.tar.gz.tmp"
    staged.write_bytes(b"new bytes")
    return staged, tmp_path / "rel.tar.gz"


def test_place_archive_refuses_existing_dest(tmp_path: Path) -> None:
    staged, dest = _staged(tmp_path)
    dest.write_bytes(b"old")
    with pytest.raises(ReleaseExistsError):
        _place_archive(staged, dest, force=False)
    assert dest.read_bytes() == b"old"
    assert not staged.exists()


def test_place_archive_places_when_absent(tmp_path: Path) -> None:
    staged, dest = _staged(tmp_path)
    _place_archive(staged, dest, force=False)
    assert dest.read_bytes() == b"new bytes"
    assert not staged.exists()


def test_place_archive_force_replaces(tmp_path: Path) -> None:
    staged, dest = _staged(tmp_path)
    dest.write_bytes(b"old")
    _place_archive(staged, dest, force=True)
    assert dest.read_bytes() == b"new bytes"
    assert not staged.exists()


def _no_links(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*_a: object, **_k: object) -> None:
        raise PermissionError("hard links unsupported")

    monkeypatch.setattr(os, "link", refuse)


def test_place_archive_copy_fallback_places_and_cleans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _no_links(monkeypatch)
    staged, dest = _staged(tmp_path)
    _place_archive(staged, dest, force=False)
    assert dest.read_bytes() == b"new bytes"
    assert not staged.exists()


def test_place_archive_copy_fallback_refuses_existing_dest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _no_links(monkeypatch)
    staged, dest = _staged(tmp_path)
    dest.write_bytes(b"old")
    with pytest.raises(ReleaseExistsError):
        _place_archive(staged, dest, force=False)
    assert dest.read_bytes() == b"old"
    assert not staged.exists()


def test_place_archive_copy_failure_removes_only_created_dest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _no_links(monkeypatch)

    def failing_copy(src: object, dst: object, *a: object, **k: object) -> None:
        dst.write(b"partial")  # type: ignore[attr-defined]
        raise OSError("disk full")

    monkeypatch.setattr(shutil, "copyfileobj", failing_copy)
    staged, dest = _staged(tmp_path)
    with pytest.raises(OSError, match="disk full"):
        _place_archive(staged, dest, force=False)
    assert not dest.exists()


def test_abbreviated_force_is_rejected_by_parser() -> None:
    parser = cli._build_parser()
    base = [
        "catalogue", "package", "--bundle", "b", "--release", "0.1.0",
        "--channel", "stable", "--output", "out",
    ]
    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args([*base, "--forc"])
    assert excinfo.value.code == 2
    assert parser.parse_args([*base, "--force"]).force is True
