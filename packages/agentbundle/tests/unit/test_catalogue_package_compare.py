"""Wave 5 release comparison (AC-0013)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
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


def test_compare_json_reports_changed_pack(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _make_catalogue(tmp_path)
    prior_out = tmp_path / "prior"
    first = _make_args(
        root, prior_out, flavor="runtime", force=False, compare=None, format="table",
    )
    assert run(first) == 0
    prior = (
        prior_out / "catalogues" / "engineering" / "releases" / "0.1.0"
        / "catalogue-0.1.0.tar.gz"
    )
    (root / "packs" / "core" / "SKILL.md").write_text(
        "# skill changed\n", encoding="utf-8", newline="\n"
    )
    capsys.readouterr()
    second = _make_args(
        root, tmp_path / "next", release="0.2.0", flavor="runtime",
        force=False, compare=str(prior), format="json",
    )
    assert run(second) == 0
    payload = json.loads(capsys.readouterr().out)
    changed = payload["comparison"]["packs"]["changed"]
    assert [item["name"] for item in changed] == ["core"]
    assert changed[0]["version"] == {"from": "0.1.0", "to": "0.1.0"}


# ---------------------------------------------------------------------------
# Remaining T4 tests. Helpers and imports follow the stub unchanged.
# ---------------------------------------------------------------------------

import hashlib  # noqa: E402
import shutil  # noqa: E402
import tarfile  # noqa: E402
from typing import Any  # noqa: E402

from agentbundle.catalogue_tooling import package as package_module  # noqa: E402
from agentbundle.catalogue_tooling.package import _write_archive  # noqa: E402

_PLANT = "\x1b[2J\nPLANT"
_PLANT_ESCAPED = "\\x1b[2J\\x0aPLANT"


def _release_archive(output: Path, release: str = "0.1.0") -> Path:
    return (
        output / "catalogues" / "engineering" / "releases" / release
        / f"catalogue-{release}.tar.gz"
    )


def _package(root: Path, output: Path, release: str = "0.1.0") -> Path:
    assert run(_make_args(root, output, release=release)) == 0
    return _release_archive(output, release)


def _members(archive: Path) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Return (content files, manifest) read from a real archive."""
    files: dict[str, bytes] = {}
    manifest: dict[str, Any] = {}
    with tarfile.open(archive) as tf:
        for member in tf.getmembers():
            fobj = tf.extractfile(member)
            assert fobj is not None
            if member.name == "catalogue-manifest.json":
                manifest = json.loads(fobj.read().decode("utf-8"))
            else:
                files[member.name] = fobj.read()
    return files, manifest


def _build(
    dest: Path, files: dict[str, bytes], manifest: dict[str, Any]
) -> Path:
    """Write an archive whose files[] matches ``files`` and whose other fields are ``manifest``."""
    manifest = dict(manifest)
    manifest["files"] = [
        {"path": k, "sha256": hashlib.sha256(v).hexdigest()} for k, v in sorted(files.items())
    ]
    _write_archive(files, json.dumps(manifest).encode("utf-8"), dest)
    return dest


def _legacy_prior(
    tmp_path: Path,
    files: dict[str, bytes],
    packs: list[Any],
    profiles: list[Any] | None,
    *,
    bundle: str = "engineering",
    schema: int = 1,
) -> Path:
    manifest: dict[str, Any] = {
        "schema": schema, "bundle": bundle, "release": "0.1.0",
        "generated_at": "2026-01-01T00:00:00+00:00", "source_revision": None,
        "packs": packs,
    }
    if profiles is not None:
        manifest["profiles"] = profiles
    return _build(tmp_path / "prior.tar.gz", files, manifest)


def _compare_args(root: Path, output: Path, prior: Path | str, **kw: object) -> SimpleNamespace:
    return _make_args(root, output, release="0.2.0", compare=str(prior), **kw)


def _clone_pack(root: Path, name: str) -> None:
    dest = root / "packs" / name
    shutil.copytree(root / "packs" / "core", dest)
    toml = dest / "pack.toml"
    toml.write_text(
        toml.read_text(encoding="utf-8").replace('name = "core"', f'name = "{name}"'),
        encoding="utf-8", newline="\n",
    )


def _two_release_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Return (root edited for the new release, prior archive of the old release)."""
    root = _make_catalogue(tmp_path)
    _clone_pack(root, "stable")
    _clone_pack(root, "gone")
    prior = _package(root, tmp_path / "prior")
    (root / "packs" / "core" / "SKILL.md").write_text(
        "# skill changed\n", encoding="utf-8", newline="\n"
    )
    shutil.rmtree(root / "packs" / "gone")
    _clone_pack(root, "fresh")
    profiles = root / "profiles"
    default_text = (profiles / "default.toml").read_text(encoding="utf-8")
    (profiles / "newer.toml").write_text(default_text, encoding="utf-8", newline="\n")
    (profiles / "default.toml").write_text(
        default_text.replace("Default package", "Edited package"),
        encoding="utf-8", newline="\n",
    )
    return root, prior


def _digest_of(archive: Path, kind: str, name: str) -> str:
    _, manifest = _members(archive)
    return next(e["digest"] for e in manifest[kind] if e["name"] == name)


def test_compare_json_full_comparison_object(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, prior = _two_release_fixture(tmp_path)
    out = tmp_path / "next"
    capsys.readouterr()
    assert run(_compare_args(root, out, prior, format="json")) == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    new_files, new_manifest = _members(_release_archive(out, "0.2.0"))
    assert set(payload) == {
        "schema_version", "command", "operation", "agentbundle_version",
        "catalogue_schema_version", "ok", "diagnostics", "comparison",
    }
    assert payload["command"] == "catalogue"
    assert payload["operation"] == "package"
    assert payload["ok"] is True
    assert payload["diagnostics"] == []
    new_pack = {e["name"]: e["digest"] for e in new_manifest["packs"]}
    new_profile = {e["name"]: e["digest"] for e in new_manifest["profiles"]}
    old_core = _digest_of(prior, "packs", "core")
    old_default = _digest_of(prior, "profiles", "default")
    assert payload["comparison"] == {
        "prior": {"archive": str(prior), "bundle": "engineering", "release": "0.1.0"},
        "packs": {
            "added": [{"name": "fresh", "version": "0.1.0", "digest": new_pack["fresh"]}],
            "removed": [{
                "name": "gone", "version": "0.1.0",
                "digest": _digest_of(prior, "packs", "gone"),
            }],
            "changed": [{
                "name": "core",
                "version": {"from": "0.1.0", "to": "0.1.0"},
                "digest": {"from": old_core, "to": new_pack["core"]},
            }],
            "unchanged": 1,
        },
        "profiles": {
            "added": [{"name": "newer", "digest": new_profile["newer"]}],
            "removed": [],
            "changed": [{
                "name": "default",
                "digest": {"from": old_default, "to": new_profile["default"]},
            }],
            "unchanged": 0,
        },
    }
    assert new_files  # the new archive was written


def test_compare_digests_come_from_prior_files_not_declared(tmp_path: Path) -> None:
    """A prior that declares a lying digest fails verification instead of being trusted."""
    root, prior = _two_release_fixture(tmp_path)
    files, manifest = _members(prior)
    for entry in manifest["packs"]:
        entry["digest"] = "sha256:" + "0" * 64
    lying = _build(tmp_path / "lying.tar.gz", files, manifest)
    out = tmp_path / "next"
    assert run(_compare_args(root, out, lying)) == 1
    assert not out.exists()


def test_json_without_compare_is_one_object_without_comparison(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _make_catalogue(tmp_path)
    assert run(_make_args(root, tmp_path / "out", format="json")) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert "comparison" not in payload


def test_human_comparison_lists_every_unit_and_counts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, prior = _two_release_fixture(tmp_path)
    capsys.readouterr()
    assert run(_compare_args(root, tmp_path / "next", prior)) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    lines = captured.err.splitlines()
    packs_at = lines.index("Packs:")
    profiles_at = lines.index("Profiles:")
    packs, profiles = lines[packs_at:profiles_at], lines[profiles_at:]
    assert any(line.startswith("  added: fresh") for line in packs)
    assert any(line.startswith("  removed: gone") for line in packs)
    assert any(line.startswith("  changed: core") for line in packs)
    assert "  unchanged: 1" in packs
    assert any(line.startswith("  added: newer") for line in profiles)
    assert any(line.startswith("  changed: default") for line in profiles)
    assert "  unchanged: 0" in profiles
    assert any("bundle engineering release 0.1.0" in line for line in lines[:packs_at])


def test_changed_pack_with_same_version_carries_marker(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, prior = _two_release_fixture(tmp_path)
    capsys.readouterr()
    assert run(_compare_args(root, tmp_path / "next", prior)) == 0
    err = capsys.readouterr().err
    core_line = next(line for line in err.splitlines() if line.startswith("  changed: core"))
    assert "content changed, version unchanged" in core_line
    # A version bump drops the marker.
    pack_toml = root / "packs" / "core" / "pack.toml"
    pack_toml.write_text(
        pack_toml.read_text(encoding="utf-8").replace('version = "0.1.0"', 'version = "0.2.0"'),
        encoding="utf-8", newline="\n",
    )
    capsys.readouterr()
    assert run(_compare_args(root, tmp_path / "next2", prior)) == 0
    err = capsys.readouterr().err
    core_line = next(line for line in err.splitlines() if line.startswith("  changed: core"))
    assert "0.1.0 -> 0.2.0" in core_line
    assert "version unchanged" not in core_line


def test_prior_with_flipped_file_digest_exits_1_without_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _make_catalogue(tmp_path)
    prior = _package(root, tmp_path / "prior")
    files, manifest = _members(prior)
    manifest["files"][0]["sha256"] = "0" * 64
    bad = tmp_path / "bad.tar.gz"
    _write_archive(files, json.dumps(manifest).encode("utf-8"), bad)
    capsys.readouterr()
    out = tmp_path / "next"
    assert run(_compare_args(root, out, bad)) == 1
    assert any(
        line.startswith("CAT-V-ARC-") for line in capsys.readouterr().err.splitlines()
    )
    assert not out.exists()


def test_legacy_prior_with_identical_content_reports_units_unchanged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _make_catalogue(tmp_path)
    files, _ = _members(_package(root, tmp_path / "first"))
    prior = _legacy_prior(tmp_path, files, [{"name": "core", "version": "0.1.0"}], ["default"])
    capsys.readouterr()
    assert run(_compare_args(root, tmp_path / "next", prior, format="json")) == 0
    comparison = json.loads(capsys.readouterr().out)["comparison"]
    for kind in ("packs", "profiles"):
        assert comparison[kind] == {"added": [], "removed": [], "changed": [], "unchanged": 1}


def _unit_remap_prior(tmp_path: Path, name: str = "core") -> tuple[Path, Path]:
    root = _make_catalogue(tmp_path)
    files, _ = _members(_package(root, tmp_path / "first"))
    moved = {
        (k.replace("packs/core/", "packs/other/") if k.startswith("packs/core/") else k): v
        for k, v in files.items()
    }
    prior = _legacy_prior(tmp_path, moved, [{"name": name, "version": "0.1.0"}], ["default"])
    return root, prior


def test_legacy_prior_with_underivable_unit_exits_1_naming_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, prior = _unit_remap_prior(tmp_path)
    capsys.readouterr()
    out = tmp_path / "next"
    assert run(_compare_args(root, out, prior)) == 1
    err = capsys.readouterr().err
    assert '"core"' in err
    assert not out.exists()


@pytest.mark.parametrize("extra", [{"compare": "x"}, {"format": "json"}])
def test_source_flavor_with_compare_or_json_is_usage_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], extra: dict[str, object]
) -> None:
    root = _make_catalogue(tmp_path)
    out = tmp_path / "out"
    args = _make_args(root, out, flavor="source", channel=None, **extra)
    assert run(args) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err
    assert not out.exists()


def _json_run(args: SimpleNamespace, capsys: pytest.CaptureFixture[str]) -> tuple[int, Any]:
    capsys.readouterr()
    code = run(args)
    return code, json.loads(capsys.readouterr().out)


def test_json_envelope_on_failures_has_no_comparison(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _make_catalogue(tmp_path)
    prior = _package(root, tmp_path / "prior")

    # Refusal (exit 2): the release archive already exists.
    code, payload = _json_run(
        _make_args(root, tmp_path / "prior", format="json", compare=str(prior)), capsys
    )
    assert code == 2
    assert payload["ok"] is False
    assert [d["code"] for d in payload["diagnostics"]] == ["CAT-PKG-002"]
    assert "comparison" not in payload

    # Flipped digest in the prior (exit 1).
    files, manifest = _members(prior)
    manifest["files"][0]["sha256"] = "0" * 64
    bad = tmp_path / "bad.tar.gz"
    _write_archive(files, json.dumps(manifest).encode("utf-8"), bad)
    code, payload = _json_run(_compare_args(root, tmp_path / "n1", bad, format="json"), capsys)
    assert code == 1
    assert payload["ok"] is False
    assert any(d["code"].startswith("CAT-V-ARC-") for d in payload["diagnostics"])
    assert "comparison" not in payload

    # Underivable prior unit (exit 1).
    (tmp_path / "second").mkdir()
    root2, remapped = _unit_remap_prior(tmp_path / "second")
    code, payload = _json_run(
        _compare_args(root2, tmp_path / "n2", remapped, format="json"), capsys
    )
    assert code == 1
    assert payload["ok"] is False
    assert [d["code"] for d in payload["diagnostics"]] == ["CAT-PKG-001"]
    assert "comparison" not in payload


def _assert_escaped(err: str) -> None:
    assert "\x1b" not in err
    assert _PLANT_ESCAPED in err


def test_escapes_prior_pack_name_in_comparison(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _make_catalogue(tmp_path)
    files, manifest = _members(_package(root, tmp_path / "first"))
    manifest["packs"][0]["name"] = _PLANT  # path stays packs/core, so the prior verifies
    prior = _build(tmp_path / "planted.tar.gz", files, manifest)
    capsys.readouterr()
    assert run(_compare_args(root, tmp_path / "next", prior)) == 0
    _assert_escaped(capsys.readouterr().err)


def test_escapes_prior_bundle_in_comparison_header(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _make_catalogue(tmp_path)
    files, manifest = _members(_package(root, tmp_path / "first"))
    manifest["bundle"] = _PLANT
    prior = _build(tmp_path / "planted.tar.gz", files, manifest)
    capsys.readouterr()
    assert run(_compare_args(root, tmp_path / "next", prior)) == 0
    _assert_escaped(capsys.readouterr().err)


def test_escapes_pack_name_in_digest_mismatch_diagnostic(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Regression check: the verifier already formats entry names with !r."""
    root = _make_catalogue(tmp_path)
    files, manifest = _members(_package(root, tmp_path / "first"))
    manifest["packs"][0]["name"] = _PLANT
    manifest["packs"][0]["digest"] = "sha256:" + "0" * 64
    prior = _build(tmp_path / "planted.tar.gz", files, manifest)
    capsys.readouterr()
    out = tmp_path / "next"
    assert run(_compare_args(root, out, prior)) == 1
    err = capsys.readouterr().err
    assert "CAT-V-ARC-018" in err
    assert "\x1b" not in err
    assert "\\x1b" in err
    assert not out.exists()


def test_escapes_underivable_unit_name(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, prior = _unit_remap_prior(tmp_path, name=_PLANT)
    capsys.readouterr()
    assert run(_compare_args(root, tmp_path / "next", prior)) == 1
    _assert_escaped(capsys.readouterr().err)


def test_exception_deriving_prior_digests_is_a_diagnostic(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, prior = _two_release_fixture(tmp_path)
    _, prior_manifest = _members(prior)
    prior_skill = next(
        f["sha256"] for f in prior_manifest["files"] if f["path"] == "packs/core/SKILL.md"
    )
    real = package_module.unit_digest

    def failing_on_prior(file_digests: Any, unit_path: str) -> str | None:
        # Only the prior side holds the old SKILL.md digest; the producer's calls pass.
        if file_digests.get("packs/core/SKILL.md") == prior_skill:
            raise RuntimeError("boom")
        return real(file_digests, unit_path)

    monkeypatch.setattr(package_module, "unit_digest", failing_on_prior)
    capsys.readouterr()
    out = tmp_path / "next"
    assert run(_compare_args(root, out, prior)) == 1
    assert "RuntimeError" in capsys.readouterr().err
    assert not out.exists()


def test_unreadable_prior_paths_exit_1_without_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _make_catalogue(tmp_path)
    garbage = tmp_path / "garbage.tar.gz"
    garbage.write_bytes(bytes(range(256)) * 4)
    directory = tmp_path / "adir"
    directory.mkdir()
    for index, target in enumerate((tmp_path / "missing.tar.gz", directory, garbage)):
        out = tmp_path / f"next{index}"
        capsys.readouterr()
        assert run(_compare_args(root, out, target)) == 1
        assert capsys.readouterr().err
        assert not out.exists()


def test_schema_1_prior_without_profiles_reports_every_profile_added(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _make_catalogue(tmp_path)
    files, _ = _members(_package(root, tmp_path / "first"))
    prior = _legacy_prior(tmp_path, files, [{"name": "core", "version": "0.1.0"}], None)
    capsys.readouterr()
    assert run(_compare_args(root, tmp_path / "next", prior, format="json")) == 0
    profiles = json.loads(capsys.readouterr().out)["comparison"]["profiles"]
    assert [item["name"] for item in profiles["added"]] == ["default"]
    assert profiles["unchanged"] == 0


def test_comparison_ignores_a_declared_prior_digest(tmp_path: Path) -> None:
    """Defence in depth under verify_archive: the comparison derives, never reads, digests."""
    root = _make_catalogue(tmp_path)
    files, manifest = _members(_package(root, tmp_path / "first"))
    lying = json.loads(json.dumps(manifest))
    for kind in ("packs", "profiles"):
        for entry in lying[kind]:
            entry["digest"] = "sha256:" + "f" * 64
    comparison = package_module._compare_releases(
        lying, "prior.tar.gz", manifest["packs"], manifest["profiles"]
    )
    assert comparison["packs"]["unchanged"] == 1
    assert comparison["profiles"]["unchanged"] == 1
    assert comparison["packs"]["changed"] == []
    assert files
