"""Wave 5 unit digests in catalogue-manifest.json (AC-0001, AC-0002)."""

from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path

from agentbundle.catalogue_tooling.package import package_catalogue

from tests.unit.test_catalogue_tooling_package import _make_catalogue


def _manifest(output: Path) -> dict:
    archive = (
        output / "catalogues" / "engineering" / "releases" / "0.1.0"
        / "catalogue-0.1.0.tar.gz"
    )
    with tarfile.open(archive) as tf:
        member = tf.extractfile("catalogue-manifest.json")
        assert member is not None
        return json.loads(member.read().decode("utf-8"))


def _expected(files: dict[str, bytes]) -> str:
    preimage = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {rel}\n"
        for rel, data in sorted(files.items())
    )
    return "sha256:" + hashlib.sha256(preimage.encode("utf-8")).hexdigest()


def test_pack_and_profile_entries_carry_path_and_digest(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    output = tmp_path / "out"
    result = package_catalogue(
        root, "engineering", "0.1.0", "stable", output,
        generated_at="2026-01-01T00:00:00+00:00",
    )
    assert result.ok, result.diagnostics
    manifest = _manifest(output)
    pack_dir = root / "packs" / "core"
    pack_files = {
        p.relative_to(pack_dir).as_posix(): p.read_bytes()
        for p in pack_dir.rglob("*")
        if p.is_file()
    }
    assert manifest["packs"] == [{
        "name": "core",
        "version": "0.1.0",
        "path": "packs/core",
        "digest": _expected(pack_files),
    }]
    profile = root / "profiles" / "default.toml"
    assert manifest["profiles"] == [{
        "name": "default",
        "path": "profiles/default.toml",
        "digest": _expected({"default.toml": profile.read_bytes()}),
    }]


def _package(root: Path, output: Path) -> dict:
    result = package_catalogue(
        root, "engineering", "0.1.0", "stable", output,
        generated_at="2026-01-01T00:00:00+00:00",
    )
    assert result.ok, result.diagnostics
    return _manifest(output)


def _add_sibling_pack(root: Path, name: str) -> None:
    pack = root / "packs" / name
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "0.1.0"\n'
        'description = "Package test fixture."\n'
        '[pack.adapter-contract]\nversion = "0.2"\n'
        '[pack.install]\ndefault-scope = "repo"\nallowed-scopes = ["repo"]\n',
        encoding="utf-8",
        newline="\n",
    )


def test_sibling_packs_digest_only_their_own_files(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    _add_sibling_pack(root, "core2")
    manifest = _package(root, tmp_path / "out")
    by_name = {p["name"]: p for p in manifest["packs"]}
    assert [p["name"] for p in manifest["packs"]] == ["core", "core2"]
    for name in ("core", "core2"):
        pack_dir = root / "packs" / name
        files = {
            p.relative_to(pack_dir).as_posix(): p.read_bytes()
            for p in pack_dir.rglob("*")
            if p.is_file()
        }
        assert by_name[name]["path"] == f"packs/{name}"
        assert by_name[name]["digest"] == _expected(files)
    assert by_name["core"]["digest"] != by_name["core2"]["digest"]


def test_nested_profile_toml_produces_no_entry(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    (root / "profiles" / "sub").mkdir()
    (root / "profiles" / "sub" / "x.toml").write_text(
        'name = "x"\n', encoding="utf-8", newline="\n"
    )
    (root / "profiles" / "alpha.toml").write_text(
        (root / "profiles" / "default.toml").read_text(encoding="utf-8"),
        encoding="utf-8",
        newline="\n",
    )
    manifest = _package(root, tmp_path / "out")
    assert [p["name"] for p in manifest["profiles"]] == ["alpha", "default"]
    assert all(p["path"] == f"profiles/{p['name']}.toml" for p in manifest["profiles"])
    assert "profiles/sub/x.toml" in {f["path"] for f in manifest["files"]}


def test_unit_digest_none_without_member_files() -> None:
    from agentbundle.catalogue_tooling.archive import unit_digest

    digests = {"packs/core/pack.toml": "a" * 64, "packs/core2/pack.toml": "b" * 64}
    assert unit_digest(digests, "packs/missing") is None
    assert unit_digest(digests, "packs/cor") is None
    assert unit_digest({}, "profiles/x.toml") is None


def test_unit_digest_file_and_directory_membership() -> None:
    from agentbundle.catalogue_tooling.archive import unit_digest

    digests = {"profiles/x.toml": "c" * 64, "packs/core/pack.toml": "d" * 64}
    file_pre = f"{'c' * 64}  x.toml\n"
    assert unit_digest(digests, "profiles/x.toml") == (
        "sha256:" + hashlib.sha256(file_pre.encode("utf-8")).hexdigest()
    )
    dir_pre = f"{'d' * 64}  pack.toml\n"
    assert unit_digest(digests, "packs/core") == (
        "sha256:" + hashlib.sha256(dir_pre.encode("utf-8")).hexdigest()
    )


def _digests(manifest: dict) -> dict[str, str]:
    return {
        **{p["path"]: p["digest"] for p in manifest["packs"]},
        **{p["path"]: p["digest"] for p in manifest["profiles"]},
    }


def test_excluded_files_leave_unit_digests_unchanged(tmp_path: Path) -> None:
    (tmp_path / "clean").mkdir()
    (tmp_path / "dirty").mkdir()
    clean_root = _make_catalogue(tmp_path / "clean")
    clean = _digests(_package(clean_root, tmp_path / "clean-out"))
    dirty_root = _make_catalogue(tmp_path / "dirty")
    core = dirty_root / "packs" / "core"
    (core / "__pycache__").mkdir()
    (core / "__pycache__" / "m.pyc").write_bytes(b"\x00junk")
    (core / ".DS_Store").write_bytes(b"junk")
    (dirty_root / "packs" / "_draft").mkdir()
    (dirty_root / "packs" / "_draft" / "pack.toml").write_text(
        "not a pack\n", encoding="utf-8", newline="\n"
    )
    (dirty_root / "profiles" / "_draft").mkdir()
    (dirty_root / "profiles" / "_draft" / "x.toml").write_text(
        'name = "x"\n', encoding="utf-8", newline="\n"
    )
    dirty_manifest = _package(dirty_root, tmp_path / "dirty-out")
    assert _digests(dirty_manifest) == clean
    paths = {f["path"] for f in dirty_manifest["files"]}
    assert not any(
        "__pycache__" in p or ".DS_Store" in p or "_draft" in p for p in paths
    )


def test_manifest_schema_stays_two(tmp_path: Path) -> None:
    manifest = _package(_make_catalogue(tmp_path), tmp_path / "out")
    assert manifest["schema"] == 2
