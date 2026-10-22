"""The catalogue manifest schema agrees with what packaging writes and verify accepts."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

import pytest
from agentbundle.build.main import _load_bundled_json
from agentbundle.build.validate import validate
from agentbundle.catalogue_tooling.archive import _check_manifest_schema, verify_archive

from tests.unit.test_catalogue_archive_unit_digests import _SHAPES, _base_manifest, _write

SCHEMA = _load_bundled_json("catalogue-manifest.schema.json")


def _legacy_cases() -> dict[str, dict]:
    """The four legacy shapes the verifier has always accepted."""
    schema_two = _base_manifest()
    schema_two["packs"] = [{"name": "core", "version": "0.1.0"}]
    schema_two["profiles"] = ["default"]
    schema_one = _base_manifest()
    schema_one["schema"] = 1
    schema_one["packs"] = [{"name": "core", "version": "0.1.0"}]
    del schema_one["profiles"]
    no_digests = _base_manifest()
    for entry in no_digests["packs"] + no_digests["profiles"]:
        del entry["digest"]
    string_profiles = _base_manifest()
    string_profiles["profiles"] = ["default"]
    return {
        "legacy-schema-2-no-digests-string-profiles": schema_two,
        "legacy-schema-1-no-profiles": schema_one,
        "legacy-no-digests": no_digests,
        "legacy-string-profiles": string_profiles,
    }


def _build_cases() -> dict[str, dict]:
    cases = _legacy_cases()
    for name, mutate in _SHAPES.items():
        cases[f"shape-{name}"] = mutate(copy.deepcopy(_base_manifest()))
    for name, mutate in {
        "missing-schema": lambda m: m.pop("schema"),
        "schema-3": lambda m: m.__setitem__("schema", 3),
        "schema-string": lambda m: m.__setitem__("schema", "2"),
        "bundle-number": lambda m: m.__setitem__("bundle", 1),
        "release-missing": lambda m: m.pop("release"),
        "generated-at-null": lambda m: m.__setitem__("generated_at", None),
        "files-object": lambda m: m.__setitem__("files", {}),
        "packs-missing": lambda m: m.pop("packs"),
    }.items():
        manifest = copy.deepcopy(_base_manifest())
        mutate(manifest)
        cases[f"arc011-{name}"] = manifest
    for label, value in (("true", True), ("1.0", 1.0), ("3", 3)):
        manifest = copy.deepcopy(_base_manifest())
        manifest["schema"] = value
        cases[f"schema-{label}"] = manifest
    return cases


AGREEMENT_CASES: dict[str, dict] = _build_cases()
LEGACY_NAMES = sorted(_legacy_cases())
REJECTED_NAMES = sorted(n for n in AGREEMENT_CASES if n not in LEGACY_NAMES and n != "schema-1.0")


def _schema_errors(manifest: Any) -> list[str]:
    return validate(manifest, SCHEMA)


def _verifier_rejects(manifest: Any) -> bool:
    return any(
        d.code in {"CAT-V-ARC-011", "CAT-V-ARC-019"} for d in _check_manifest_schema(manifest)
    )


def test_bundled_schema_loads() -> None:
    assert SCHEMA["type"] == "object"


# --- AC 2: manifests that `catalogue package` really writes ---


def _cli(*args: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "agentbundle", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr[:400]


def _package_manifest(root: Path, out: Path) -> dict:
    _cli(
        "catalogue",
        "package",
        "--root",
        str(root),
        "--bundle",
        "demo",
        "--release",
        "0.1.0",
        "--channel",
        "stable",
        "--output",
        str(out),
    )
    archive = out / "catalogues" / "demo" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(archive) as tf:
        name = next(n for n in tf.getnames() if n.rsplit("/", 1)[-1] == "catalogue-manifest.json")
        member = tf.extractfile(name)
        assert member is not None
        return json.loads(member.read())


def test_packaged_starter_and_extended_manifests_validate(tmp_path: Path) -> None:
    root = tmp_path / "catalogue"
    _cli("catalogue", "init", str(root), "--name", "demo")
    starter = _package_manifest(root, tmp_path / "out-starter")
    assert _schema_errors(starter) == []

    shutil.copytree(root / "packs" / "_example", root / "packs" / "extra-pack")
    for name in ("pack.toml", ".claude-plugin/plugin.json"):
        path = root / "packs" / "extra-pack" / name
        path.write_text(
            path.read_text(encoding="utf-8").replace("example-pack", "extra-pack"),
            encoding="utf-8",
        )
    (root / "profiles" / "extra.toml").write_text(
        'scope = "repo"\ndescription = "An extra profile."\n\n[[packs]]\npack = "extra-pack"\n',
        encoding="utf-8",
    )
    extended = _package_manifest(root, tmp_path / "out-extended")
    assert _schema_errors(extended) == []
    assert extended["packs"] and extended["profiles"]


# --- AC 3, AC 4: legacy shapes validate, malformed shapes do not ---


@pytest.mark.parametrize("name", LEGACY_NAMES)
def test_legacy_shape_validates(name: str) -> None:
    assert _schema_errors(AGREEMENT_CASES[name]) == []


@pytest.mark.parametrize("name", REJECTED_NAMES)
def test_malformed_manifest_fails_schema(name: str) -> None:
    assert _schema_errors(AGREEMENT_CASES[name]) != []


# --- AC 6: the package validator agrees with the verifier ---


@pytest.mark.parametrize("name", sorted(n for n in AGREEMENT_CASES if n != "schema-1.0"))
def test_package_validator_matches_verifier(name: str) -> None:
    manifest = AGREEMENT_CASES[name]
    assert bool(_schema_errors(manifest)) == _verifier_rejects(manifest)


def test_schema_1_0_is_the_pinned_disagreement() -> None:
    manifest = AGREEMENT_CASES["schema-1.0"]
    assert _schema_errors(manifest) != []
    assert not _verifier_rejects(manifest)


# --- AC 7: verify_archive on the boolean and float schema values ---


def test_verify_archive_rejects_boolean_schema(tmp_path: Path) -> None:
    result = verify_archive(_write(tmp_path, AGREEMENT_CASES["schema-true"]))
    assert "CAT-V-ARC-011" in [d.code for d in result.diagnostics]


def test_verify_archive_accepts_float_schema_1_0(tmp_path: Path) -> None:
    result = verify_archive(_write(tmp_path, AGREEMENT_CASES["schema-1.0"]))
    assert "CAT-V-ARC-011" not in [d.code for d in result.diagnostics]


# --- AC 8: the description's statements ---


def test_description_states_limits() -> None:
    text = " ".join(SCHEMA["description"].lower().split())
    assert "shape only" in text
    assert "neither archive verification" in text
    assert "nor evidence of who published" in text
    assert "separately authenticated channel" in text


# --- AC 9: objects stay open ---


def test_extra_keys_validate() -> None:
    manifest = copy.deepcopy(_base_manifest())
    manifest["extra_top"] = {"any": 1}
    manifest["files"][0]["extra"] = 1
    manifest["packs"][0]["extra"] = 1
    manifest["profiles"][0]["extra"] = 1
    assert _schema_errors(manifest) == []
