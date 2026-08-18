"""Index generation semantics independent of the CLI writer."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from agentbundle.build.validate import validate
from agentbundle.catalogue_tooling.index_generator import CatalogueIndexError, generate_index

ROOT = Path(__file__).parents[4]
FIXTURE = Path(__file__).parent.parent / "fixtures" / "catalogue_wave4"
SCHEMA = json.loads(
    (ROOT / "contracts" / "catalogue-index.schema.json").read_text(encoding="utf-8")
)


def _copy_fixture(tmp_path: Path) -> Path:
    destination = tmp_path / "catalogue"
    shutil.copytree(FIXTURE, destination)
    return destination


def _pack(index: dict[str, object], name: str) -> dict[str, object]:
    return next(item for item in index["packs"] if item["name"] == name)  # type: ignore[index,union-attr]


def test_two_pack_fixture_produces_valid_index(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    index = generate_index(root)

    assert validate(index, SCHEMA) == []
    with_journey = _pack(index, "pack-with-journey")
    without_journey = _pack(index, "pack-without-journey")
    assert with_journey["journeys"]
    assert without_journey["journeys"] == []
    assert [profile["name"] for profile in index["profiles"]] == ["test-profile"]  # type: ignore[index]
    assert len(with_journey["digest"]) == 64
    assert with_journey["content"]["skills"] == ["example-skill"]  # type: ignore[index]
    assert "example.json" in with_journey["execution"]  # type: ignore[operator]


def test_journey_effects_are_exact(tmp_path: Path) -> None:
    index = generate_index(_copy_fixture(tmp_path))
    assert _pack(index, "pack-with-journey")["effects"] == [
        {
            "kind": "file-write",
            "description": "Writes a validated JSON index when not in dry-run mode.",
        }
    ]


def test_forward_and_inverse_integrations_are_exact(tmp_path: Path) -> None:
    index = generate_index(_copy_fixture(tmp_path))
    assert _pack(index, "pack-with-journey")["integrations"] == [
        {
            "id": "fixture-companion",
            "pack": "pack-without-journey",
            "kind": "augment",
            "role": "provider",
        }
    ]
    assert _pack(index, "pack-without-journey")["integrations_inverse"] == [
        {
            "id": "fixture-companion",
            "pack": "pack-with-journey",
            "kind": "augment",
            "role": "provider",
        }
    ]


def test_deterministic_without_timestamp(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    first = generate_index(root)
    second = generate_index(root)
    assert first == second
    assert "generated_at" not in first


def test_generated_at_is_included_when_supplied(tmp_path: Path) -> None:
    index = generate_index(_copy_fixture(tmp_path), "2026-08-01T00:00:00Z")
    assert index["generated_at"] == "2026-08-01T00:00:00Z"


def test_pack_and_profile_arrays_sorted_by_name(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    shutil.copytree(root / "packs" / "pack-without-journey", root / "packs" / "a-pack")
    (root / "packs" / "a-pack" / "pack.toml").write_text(
        '[pack]\nname = "a-pack"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    (root / "profiles" / "a-profile.toml").write_text('scope = "repo"\n', encoding="utf-8")

    index = generate_index(root)

    assert [pack["name"] for pack in index["packs"]] == sorted(  # type: ignore[index]
        pack["name"] for pack in index["packs"]  # type: ignore[index]
    )
    assert [profile["name"] for profile in index["profiles"]] == sorted(  # type: ignore[index]
        profile["name"] for profile in index["profiles"]  # type: ignore[index]
    )


def test_cache_artifacts_do_not_change_digest(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    pack_root = root / "packs" / "pack-with-journey"
    before = _pack(generate_index(root), "pack-with-journey")["digest"]
    cache = pack_root / ".apm" / "skills" / "example-skill" / "scripts" / "__pycache__"
    cache.mkdir()
    (cache / "run.pyc").write_bytes(b"cache")
    (pack_root / ".cache").mkdir()
    (pack_root / ".cache" / "result").write_bytes(b"cache")
    (pack_root / ".apm" / "skills" / "example-skill" / "scripts" / "native.pyd").write_bytes(
        b"cache"
    )
    after = _pack(generate_index(root), "pack-with-journey")["digest"]
    assert before == after


def test_authored_dotfiles_and_direct_libraries_are_indexed(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    pack = root / "packs" / "pack-with-journey"
    seeds = pack / "seeds"
    seeds.mkdir()
    (seeds / ".gitignore").write_text("generated/\n", encoding="utf-8")
    shared = pack / ".apm" / "shared-libs"
    shared.mkdir()
    (shared / "credentials_shim.py").write_text("VALUE = 1\n", encoding="utf-8")
    user = pack / ".apm" / "user-libs"
    user.mkdir()
    (user / "user_helper.py").write_text("VALUE = 1\n", encoding="utf-8")

    content = _pack(generate_index(root), "pack-with-journey")["content"]

    assert ".gitignore" in content["seeds"]  # type: ignore[index,operator]
    assert content["shared-libs"] == ["credentials_shim.py"]  # type: ignore[index]
    assert content["user-libs"] == ["user_helper.py"]  # type: ignore[index]


def test_adapter_root_bins_exclude_private_modules(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    bins = root / "packs" / "pack-with-journey" / ".apm" / "adapter-root-bins"
    bins.mkdir()
    (bins / "sso-broker.py").write_text("VALUE = 1\n", encoding="utf-8")
    (bins / "_helper.py").write_text("VALUE = 1\n", encoding="utf-8")
    (bins / "__init__.py").write_text("", encoding="utf-8")
    (bins / ".gitkeep").write_text("", encoding="utf-8")
    (bins / "README.md").write_text("Not executable.\n", encoding="utf-8")

    execution = _pack(generate_index(root), "pack-with-journey")["execution"]

    assert "sso-broker.py" in execution  # type: ignore[operator]
    assert "_helper.py" not in execution  # type: ignore[operator]
    assert "__init__.py" not in execution  # type: ignore[operator]
    assert ".gitkeep" not in execution  # type: ignore[operator]
    assert "README.md" not in execution  # type: ignore[operator]


def test_script_inventory_only_reads_immediate_skill_scripts(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    skill = root / "packs" / "pack-with-journey" / ".apm" / "skills" / "example-skill"
    misleading = skill / "references" / "scripts" / "example.md"
    misleading.parent.mkdir(parents=True)
    misleading.write_text("Not a runtime script.\n", encoding="utf-8")

    scripts = _pack(generate_index(root), "pack-with-journey")["content"]["scripts"]  # type: ignore[index]

    assert ".apm/skills/example-skill/scripts/run.py" in scripts
    assert ".apm/skills/example-skill/references/scripts/example.md" not in scripts


def test_unreadable_manifest_reports_confined_input_location(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _copy_fixture(tmp_path)
    manifest = root / "packs" / "pack-with-journey" / "pack.toml"
    real_stat = Path.stat
    real_lstat = Path.lstat

    def deny_stat(path: Path, *args: object, **kwargs: object):
        if path == manifest:
            raise PermissionError("denied")
        return real_stat(path, *args, **kwargs)

    def deny_lstat(path: Path, *args: object, **kwargs: object):
        if path == manifest:
            raise PermissionError("denied")
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", deny_stat)
    monkeypatch.setattr(Path, "lstat", deny_lstat)

    with pytest.raises(CatalogueIndexError) as caught:
        generate_index(root)

    assert caught.value.code == "unreadable-pack"
    assert caught.value.location == "packs/pack-with-journey/pack.toml"
    assert str(root) not in caught.value.message


def test_uninspectable_pack_directory_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _copy_fixture(tmp_path)
    pack_root = root / "packs" / "pack-with-journey"
    real_lstat = Path.lstat

    def deny_pack(path: Path, *args: object, **kwargs: object):
        if path == pack_root:
            raise PermissionError("denied")
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", deny_pack)

    with pytest.raises(CatalogueIndexError) as caught:
        generate_index(root)

    assert caught.value.code == "unreadable-pack"
    assert caught.value.location == "packs/pack-with-journey"


def test_digest_matches_exact_sorted_relative_path_algorithm(tmp_path: Path) -> None:
    root = tmp_path / "catalogue"
    pack = root / "packs" / "digest-pack"
    source = pack / ".apm" / "skills" / "sample" / "SKILL.md"
    source.parent.mkdir(parents=True)
    (root / "catalogue.toml").write_text('[catalogue]\nname = "digest"\n', encoding="utf-8")
    manifest = pack / "pack.toml"
    manifest.write_text('[pack]\nname = "digest-pack"\nversion = "1.0.0"\n', encoding="utf-8")
    source.write_text("source bytes\n", encoding="utf-8")
    entries = []
    for path in sorted((manifest, source), key=lambda item: item.relative_to(pack).as_posix()):
        relative = path.relative_to(pack).as_posix()
        entries.append(f"{relative}:{hashlib.sha256(path.read_bytes()).hexdigest()}\n")
    expected = hashlib.sha256("".join(entries).encode("utf-8")).hexdigest()

    index = generate_index(root)

    assert _pack(index, "digest-pack")["digest"] == expected


def test_legacy_pack_uses_full_adapter_set(tmp_path: Path) -> None:
    index = generate_index(_copy_fixture(tmp_path))
    legacy = _pack(index, "pack-without-journey")
    assert "claude-code" in legacy["adapters"]  # type: ignore[operator]
    assert len(legacy["adapters"]) > 1  # type: ignore[arg-type]


def test_nonlegacy_pack_uses_allowed_adapter_subset(tmp_path: Path) -> None:
    index = generate_index(_copy_fixture(tmp_path))
    assert _pack(index, "pack-with-journey")["adapters"] == ["claude-code"]


def test_live_catalogue_indexes_every_manifest_pack() -> None:
    index = generate_index(ROOT)
    expected = {
        path.parent.name
        for path in (ROOT / "packs").glob("*/pack.toml")
        if not path.parent.name.startswith("_")
    }
    assert {pack["name"] for pack in index["packs"]} == expected  # type: ignore[index]
    with_journeys = {
        pack["name"] for pack in index["packs"] if pack["journeys"]  # type: ignore[index]
    }
    expected_journeys = {
        path.parent.name
        for path in (ROOT / "packs").glob("*/JOURNEY.md")
        if not path.parent.name.startswith("_")
    }
    assert expected_journeys
    assert with_journeys == expected_journeys
