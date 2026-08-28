"""Construction tests for the portable Agent Plugins route."""

from __future__ import annotations

import json
import math
import os
import tomllib
from importlib import import_module
from importlib.resources import files as resource_files
from pathlib import Path

import pytest
from agentbundle.build.main import (
    Pack,
    _agent_plugin_excluding_primitives,
    _read_agent_plugin_pack_metadata,
    derive_agent_plugin_manifest,
    discover_packs,
    load_recipe,
    run_default_build,
    run_recipe,
)

PLUGIN_SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
REPO_ROOT = Path(__file__).resolve().parents[4]
build_main = import_module("agentbundle.build.main")
file_safety = import_module("agentbundle.catalogue_tooling.file_safety")


# STUB: AC3-AC5, AC9, AC15 — admission and manifest derivation are fail closed.
def test_agent_plugin_admission_and_manifest_contract(tmp_path: Path) -> None:
    """Pin skills-only admission and the privacy-minimal portable manifest."""
    pack_path = tmp_path / "portable-pack"
    (pack_path / ".apm" / "skills" / "example").mkdir(parents=True)
    (pack_path / ".apm" / "skills" / "example" / "SKILL.md").write_text(
        "# Example\n", encoding="utf-8"
    )
    metadata = {
        "pack": {
            "name": "portable-pack",
            "version": "1.2.3",
            "description": "Portable example",
            "license": "Apache-2.0",
            "maintainers": [
                {
                    "name": "Maintainer",
                    "email": "private@example.invalid",
                    "url": "https://example.invalid/private",
                    "username": "private-account",
                }
            ],
            "links": {
                "homepage": "https://example.invalid",
                "repository": "https://github.com/example/portable-pack",
            },
            "keywords": ["portable", "skills"],
        }
    }

    assert _agent_plugin_excluding_primitives(Pack("portable-pack", pack_path)) == []
    assert derive_agent_plugin_manifest(metadata, pack_name="portable-pack") == {
        "$schema": PLUGIN_SCHEMA_ID,
        "name": "portable-pack",
        "version": "1.2.3",
        "description": "Portable example",
        "author": {"name": "Maintainer"},
        "homepage": "https://example.invalid",
        "repository": "https://github.com/example/portable-pack",
        "license": "Apache-2.0",
        "keywords": ["portable", "skills"],
    }

    for primitive, directory in (
        ("agent", "agents"),
        ("command", "commands"),
        ("hook-body", "hooks"),
        ("hook-wiring", "hook-wiring"),
        ("kiro-ide-hook", "kiro-ide-hooks"),
        ("shared-libs", "shared-libs"),
        ("adapter-root-bins", "adapter-root-bins"),
        ("user-libs", "user-libs"),
    ):
        source = pack_path / ".apm" / directory
        source.mkdir()
        assert primitive not in _agent_plugin_excluding_primitives(
            Pack("portable-pack", pack_path)
        )
        (source / "present").write_text("x", encoding="utf-8")
        assert primitive in _agent_plugin_excluding_primitives(
            Pack("portable-pack", pack_path)
        )

    invalid = {"pack": {"name": "Portable_Pack", "version": "1"}}
    with pytest.raises(ValueError, match=r"agent-plugin.*pack-name"):
        derive_agent_plugin_manifest(invalid, pack_name="Portable_Pack")

    non_finite = {"pack": {"name": "portable-pack", "version": math.nan}}
    with pytest.raises(ValueError, match=r"agent-plugin.*strict-json"):
        derive_agent_plugin_manifest(non_finite, pack_name="portable-pack")


@pytest.mark.parametrize(
    "name",
    [
        "",
        "A",
        "portable_pack",
        "-portable",
        "portable-",
        "portable--pack",
        "portable..pack",
        "a" * 65,
        "portable\npack",
        "p\u202eack",
    ],
)
def test_agent_plugin_identity_is_rejected_without_normalization(name: str) -> None:
    """Reject every non-portable identity class and escape its diagnostic."""
    with pytest.raises(ValueError) as refusal:
        derive_agent_plugin_manifest(
            {"pack": {"name": name, "version": "1"}}, pack_name=name
        )
    diagnostic = str(refusal.value)
    assert diagnostic.count("\n") == 0
    assert diagnostic.isascii()
    assert "invalid-identity" in diagnostic


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_agent_plugin_manifest_rejects_non_finite_json(value: float) -> None:
    """Refuse values Python's permissive JSON encoder would otherwise emit."""
    with pytest.raises(ValueError, match="strict-json"):
        derive_agent_plugin_manifest(
            {"pack": {"name": "portable-pack", "version": value}},
            pack_name="portable-pack",
        )


def test_agent_plugin_manifest_sanitizes_deep_unused_metadata() -> None:
    """Deep open metadata must refuse through the route diagnostic boundary."""
    nested: dict = {}
    cursor = nested
    for _ in range(10_000):
        child: dict = {}
        cursor["next"] = child
        cursor = child

    metadata = {
        "pack": {
            "name": "portable-pack",
            "version": "1",
            "metadata": {"unused": nested},
        }
    }
    with pytest.raises(ValueError, match=r"agent-plugin.*manifest.*strict-json"):
        derive_agent_plugin_manifest(metadata, pack_name="portable-pack")


def test_agent_plugin_pack_metadata_uses_confined_single_link_reader(
    tmp_path: Path,
) -> None:
    """Refuse linked and oversized pack metadata before manifest derivation."""
    pack = tmp_path / "portable-pack"
    pack.mkdir()
    pack_toml = pack / "pack.toml"
    pack_toml.write_text('[pack]\nname = "portable-pack"\nversion = "1"\n')
    parsed = _read_agent_plugin_pack_metadata(Pack("portable-pack", pack))
    assert parsed["pack"]["name"] == "portable-pack"

    hardlink = tmp_path / "hardlink.toml"
    try:
        os.link(pack_toml, hardlink)
    except OSError:
        pytest.skip("hard links are unavailable on this filesystem")
    with pytest.raises(ValueError, match=r"agent-plugin.*unsafe-metadata"):
        _read_agent_plugin_pack_metadata(Pack("portable-pack", pack))
    hardlink.unlink()

    pack_toml.write_bytes(b"x" * (1024 * 1024 + 1))
    with pytest.raises(ValueError, match=r"agent-plugin.*unsafe-metadata"):
        _read_agent_plugin_pack_metadata(Pack("portable-pack", pack))


def test_agent_plugin_discovery_refuses_unsafe_pack_roots_and_metadata(
    tmp_path: Path,
) -> None:
    """Reject unsafe metadata before normal build discovery can follow it."""
    packs = tmp_path / "packs"
    real_pack = packs / "real-pack"
    real_pack.mkdir(parents=True)
    pack_toml = real_pack / "pack.toml"
    pack_toml.write_text('[pack]\nname = "real-pack"\nversion = "1"\n')

    linked_pack = packs / "linked-pack"
    try:
        linked_pack.symlink_to(real_pack, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable on this filesystem")
    with pytest.raises(ValueError) as route_refusal:
        discover_packs(packs, diagnostic_route="agent-plugin")
    assert "agent-plugin" in str(route_refusal.value)
    assert "pack-root" in str(route_refusal.value)
    assert str(tmp_path) not in str(route_refusal.value)
    linked_pack.unlink()

    hardlink = tmp_path / "hardlink.toml"
    try:
        os.link(pack_toml, hardlink)
    except OSError:
        pytest.skip("hard links are unavailable on this filesystem")
    assert [pack.name for pack in discover_packs(packs)] == ["real-pack"]
    with pytest.raises(ValueError) as route_refusal:
        discover_packs(packs, diagnostic_route="agent-plugin")
    assert "unsafe-metadata" in str(route_refusal.value)
    assert str(tmp_path) not in str(route_refusal.value)
    hardlink.unlink()

    pack_toml.write_text(
        '[pack]\nname = "real-pack"\nversion = "1"\n#'
        + "x" * (1024 * 1024),
        encoding="utf-8",
    )
    assert [pack.name for pack in discover_packs(packs)] == ["real-pack"]
    with pytest.raises(ValueError, match=r"agent-plugin.*unsafe-metadata"):
        discover_packs(packs, diagnostic_route="agent-plugin")

    pack_toml.write_text('[pack]\nname = 1\nversion = "1"\n', encoding="utf-8")
    with pytest.raises(ValueError) as route_refusal:
        discover_packs(packs, diagnostic_route="agent-plugin")
    assert "invalid-metadata" in str(route_refusal.value)
    assert str(tmp_path) not in str(route_refusal.value)


def test_agent_plugin_current_corpus_has_exact_portable_roster() -> None:
    """Pin the approved 13 eligible and eight excluded catalogue packs."""
    corpus = REPO_ROOT / "packs"
    if not corpus.is_dir():
        # The roster is a repository-checkout invariant: a published sdist or
        # wheel carries the engine without the catalogue corpus it describes.
        return
    packs = discover_packs(corpus)
    exclusions = {
        pack.name: _agent_plugin_excluding_primitives(pack)
        for pack in packs
        if _agent_plugin_excluding_primitives(pack)
    }
    assert {pack.name for pack in packs} - exclusions.keys() == {
        "agent-skill-engineering",
        "atlassian",
        "catalogue-curation",
        "contracts",
        "converters",
        "figma",
        "github",
        "governance-extras",
        "iac-terraform",
        "linear",
        "monorepo-extras",
        "product-documentation",
        "product-strategy",
        "user-guide-diataxis",
    }
    assert exclusions == {
        "architect": ["agent"],
        "core": ["agent", "command", "hook-body", "hook-wiring", "kiro-ide-hook"],
        "credential-brokers": ["adapter-root-bins", "shared-libs", "user-libs"],
        "desk-research": ["agent"],
        "experience-design": ["agent"],
        "frontend-engineering": ["agent"],
        "product-engineering": ["agent"],
        "release-engineering": ["agent"],
    }


def test_agent_plugin_extension_registry_contract_and_bundled_parity() -> None:
    """Pin the reserved allocations and every closed-registry state rule."""
    bundled_text = (
        resource_files("agentbundle")
        .joinpath("_data", "agent-plugin-extension-namespaces.toml")
        .read_text(encoding="utf-8")
    )
    # The authored contract is checkout-only; the bundled twin always ships.
    canonical = REPO_ROOT / "contracts" / "agent-plugin-extension-namespaces.toml"
    if canonical.is_file():
        assert canonical.read_text(encoding="utf-8") == bundled_text
    registry = tomllib.loads(bundled_text)
    assert registry["namespace"] == {
        "com.github.copilot": {
            "owner": "copilot-profile",
            "state": "reserved",
        },
        "dev.kiro": {"owner": "kiro-profile", "state": "reserved"},
    }
    build_main._validate_agent_plugin_extension_registry(registry)

    invalid_allocations = [
        ("com.example.active", {"owner": "owner", "state": "active"}),
        (
            "com.example.reserved",
            {
                "owner": "owner",
                "state": "reserved",
                "schema": "vendor/test/v1/test.schema.json",
            },
        ),
        ("Invalid", {"owner": "owner", "state": "reserved"}),
        (
            "com.example.active",
            {"owner": "owner", "state": "active", "schema": "../schema.json"},
        ),
    ]
    for namespace, allocation in invalid_allocations:
        with pytest.raises(ValueError, match="extension-registry"):
            build_main._validate_agent_plugin_extension_registry(
                {
                    "contract": {"version": "1.0"},
                    "namespace": {namespace: allocation},
                }
            )


def test_agent_plugin_active_extension_schema_rejects_ignored_keywords(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Never activate a schema whose constraints the stdlib validator ignores."""
    original_read = build_main._read_bundled
    registry = (
        '[contract]\nversion = "1.0"\n\n'
        '[namespace."com.example.test"]\n'
        'owner = "test-profile"\n'
        'state = "active"\n'
        'schema = "vendor/test/v1/test.schema.json"\n'
    )

    def read_with_schema(name: str) -> str:
        if name == "agent-plugin-extension-namespaces.toml":
            return registry
        if name == "vendor/test/v1/test.schema.json":
            return json.dumps(
                {
                    "type": "object",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "oneOf": [{"enum": [True]}],
                        }
                    },
                }
            )
        return original_read(name)

    monkeypatch.setattr(build_main, "_read_bundled", read_with_schema)
    with pytest.raises(ValueError, match=r"extension-registry.*invalid-schema"):
        build_main._load_agent_plugin_extension_registry()


def test_agent_plugin_missing_active_extension_schema_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hide bundled filesystem details when an active schema is unavailable."""
    original_read = build_main._read_bundled
    registry = (
        '[contract]\nversion = "1.0"\n\n'
        '[namespace."com.example.test"]\n'
        'owner = "test-profile"\n'
        'state = "active"\n'
        'schema = "vendor/test/v1/test.schema.json"\n'
    )

    def read_with_missing_schema(name: str) -> str:
        if name == "agent-plugin-extension-namespaces.toml":
            return registry
        if name == "vendor/test/v1/test.schema.json":
            raise FileNotFoundError("/private/host/path/test.schema.json")
        return original_read(name)

    monkeypatch.setattr(build_main, "_read_bundled", read_with_missing_schema)
    with pytest.raises(ValueError) as refusal:
        build_main._load_agent_plugin_extension_registry()
    assert str(refusal.value) == (
        "agent-plugin: extension-registry error invalid-schema"
    )
    assert "/private/host/path" not in str(refusal.value)


def _extension_value_with_serialized_size(target: int) -> dict[str, str]:
    """Construct strict JSON at an exact byte size within all other limits."""
    value = {f"k{index:03d}": "x" * (64 * 1024) for index in range(127)}
    serialized = lambda item: json.dumps(  # noqa: E731 - local size oracle
        item,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    empty_tail = {**value, "tail": ""}
    tail_overhead = len(serialized(empty_tail)) - len(serialized(value))
    tail_size = target - len(serialized(value)) - tail_overhead
    assert 0 <= tail_size <= 64 * 1024
    value["tail"] = "x" * tail_size
    assert len(serialized(value)) == target
    return value


def test_agent_plugin_extension_limit_boundaries() -> None:
    """Pin every AC8 equality/plus-one boundary in the limit checker."""
    check = build_main._check_agent_plugin_extension_limits

    exact_json = _extension_value_with_serialized_size(8 * 1024 * 1024)
    check(exact_json, pack_name="portable-pack")
    over_json = dict(exact_json)
    over_json["tail"] += "x"

    depth_20: object = True
    for _ in range(19):
        depth_20 = {"x": depth_20}
    depth_21 = {"x": depth_20}

    boundary_pairs = [
        (exact_json, over_json),
        ({f"k{index}": True for index in range(4096)},
         {f"k{index}": True for index in range(4097)}),
        ({"k" * (64 * 1024): True}, {"k" * (64 * 1024 + 1): True}),
        ({"value": "x" * (64 * 1024)}, {"value": "x" * (64 * 1024 + 1)}),
        ({"items": list(range(256))}, {"items": list(range(257))}),
        (depth_20, depth_21),
    ]
    for boundary, plus_one in boundary_pairs:
        check(boundary, pack_name="portable-pack")
        with pytest.raises(ValueError, match=r"extension.*manifest-limit"):
            check(plus_one, pack_name="portable-pack")

    very_deep: object = True
    for _ in range(2000):
        very_deep = {"x": very_deep}
    with pytest.raises(ValueError, match=r"extension.*manifest-limit"):
        check(very_deep, pack_name="portable-pack")


def test_agent_plugin_extension_limit_refusal_preserves_existing_route(
    tmp_path: Path,
) -> None:
    """Apply extension bounds before allocation lookup or route mutation."""
    pack_path = tmp_path / "packs" / "portable-pack"
    pack_path.mkdir(parents=True)
    items = ", ".join(str(index) for index in range(257))
    (pack_path / "pack.toml").write_text(
        '[pack]\nname = "portable-pack"\nversion = "1"\n\n'
        '[pack.metadata.agent-plugin.extensions."dev.kiro"]\n'
        f"items = [{items}]\n",
        encoding="utf-8",
    )
    output = tmp_path / "dist"
    sentinel = output / "agent-plugins" / "old" / "sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"keep")

    with pytest.raises(ValueError, match=r"extension.*manifest-limit"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            output,
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert sentinel.read_bytes() == b"keep"


# STUB: AC6, AC8-AC10 — unsafe or oversized skills never mutate route output.
def test_agent_plugin_projection_refuses_unsafe_or_oversize_skill_trees(
    tmp_path: Path,
) -> None:
    """Keep prior route bytes intact until every source tree passes preflight."""
    pack_path = tmp_path / "packs" / "portable-pack"
    skill = pack_path / ".apm" / "skills" / "example"
    skill.mkdir(parents=True)
    (pack_path / "pack.toml").write_text(
        '[pack]\nname = "portable-pack"\nversion = "1"\n', encoding="utf-8"
    )
    unsafe = skill / "unsafe"
    unsafe.symlink_to(pack_path / "pack.toml")
    output = tmp_path / "dist"
    sentinel = output / "agent-plugins" / "old" / "sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"keep")

    with pytest.raises(ValueError, match=r"agent-plugin.*skill.*unsafe-source"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            output,
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert sentinel.read_bytes() == b"keep"

    unsafe.unlink()
    (skill / "too-large.bin").write_bytes(b"x" * (2 * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match=r"agent-plugin.*skill.*source-limit"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            output,
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert sentinel.read_bytes() == b"keep"


def test_agent_plugin_projection_refuses_non_directory_skill_root_entries(
    tmp_path: Path,
) -> None:
    """Project only immediate canonical skill directories, never root files."""
    pack_path = tmp_path / "packs" / "portable-pack"
    skills_root = pack_path / ".apm" / "skills"
    skill = skills_root / "example"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Example\n", encoding="utf-8")
    (skills_root / "notes.txt").write_text("not a skill", encoding="utf-8")
    (pack_path / "pack.toml").write_text(
        '[pack]\nname = "portable-pack"\nversion = "1"\n', encoding="utf-8"
    )
    output = tmp_path / "dist"
    sentinel = output / "agent-plugins" / "old" / "sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"keep")

    with pytest.raises(ValueError, match=r"agent-plugin.*skill.*unsafe-source"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            output,
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert sentinel.read_bytes() == b"keep"


def test_agent_plugin_dropped_primitive_roots_are_no_follow(
    tmp_path: Path,
) -> None:
    """Refuse link-like or non-directory admission roots before publication."""
    pack_path = tmp_path / "packs" / "portable-pack"
    skill = _write_minimal_agent_plugin_pack(pack_path)
    (skill / "SKILL.md").write_bytes(b"# Example\n")
    outside = tmp_path / "outside-agents"
    outside.mkdir()
    (outside / "agent.md").write_bytes(b"agent")
    agents = pack_path / ".apm" / "agents"
    try:
        agents.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable on this filesystem")

    output = tmp_path / "dist"
    sentinel = output / "agent-plugins" / "old" / "sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"keep")
    with pytest.raises(ValueError, match=r"agent-plugin.*agent.*unsafe-source"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            output,
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert sentinel.read_bytes() == b"keep"

    agents.unlink()
    agents.write_bytes(b"not a directory")
    with pytest.raises(ValueError, match=r"agent-plugin.*agent.*unsafe-source"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            output,
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert sentinel.read_bytes() == b"keep"


@pytest.mark.parametrize("linked_component", [".apm", ".apm/skills"])
def test_agent_plugin_skill_ancestors_are_no_follow_before_uniqueness(
    tmp_path: Path,
    linked_component: str,
) -> None:
    """Route-local skill checks must precede generic primitive enumeration."""
    pack_path = tmp_path / "packs" / "portable-pack"
    pack_path.mkdir(parents=True)
    (pack_path / "pack.toml").write_text(
        '[pack]\nname = "portable-pack"\nversion = "1"\n', encoding="utf-8"
    )
    outside = tmp_path / "outside"
    (outside / "skills" / "example").mkdir(parents=True)
    (outside / "skills" / "example" / "SKILL.md").write_bytes(b"outside")
    link = pack_path / linked_component
    link.parent.mkdir(parents=True, exist_ok=True)
    target = outside if linked_component == ".apm" else outside / "skills"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable on this filesystem")
    output = tmp_path / "dist"
    sentinel = output / "agent-plugins" / "old" / "sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"keep")

    with pytest.raises(ValueError, match=r"agent-plugin.*skill.*unsafe-source"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            output,
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert sentinel.read_bytes() == b"keep"


def _write_minimal_agent_plugin_pack(pack_path: Path) -> Path:
    """Create a minimal skills-only pack and return its skill directory."""
    skill = pack_path / ".apm" / "skills" / "example"
    skill.mkdir(parents=True)
    (pack_path / "pack.toml").write_text(
        f'[pack]\nname = "{pack_path.name}"\nversion = "1"\n',
        encoding="utf-8",
    )
    return skill


def _assert_route_refusal_keeps_sentinel(pack_path: Path, output: Path) -> None:
    """Run the route and pin its pre-mutation refusal sentinel."""
    sentinel = output / "agent-plugins" / "old" / "sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"keep")
    with pytest.raises(ValueError, match=r"agent-plugin.*skill"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack(pack_path.name, pack_path)],
            output,
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert sentinel.read_bytes() == b"keep"


def test_agent_plugin_source_limit_boundaries_and_plus_one(
    tmp_path: Path,
) -> None:
    """Accept exact AC9 source bounds and refuse each boundary-plus-one."""
    count_pack = tmp_path / "packs" / "count-pack"
    count_skill = _write_minimal_agent_plugin_pack(count_pack)
    for index in range(4096):
        (count_skill / f"f{index:04d}").write_bytes(b"")
    with (tmp_path / "count-spool").open("w+b") as spool:
        build_main._prepare_agent_plugin(Pack("count-pack", count_pack), spool)
    (count_skill / "f4096").write_bytes(b"")
    _assert_route_refusal_keeps_sentinel(count_pack, tmp_path / "count-dist")

    bytes_pack = tmp_path / "packs" / "bytes-pack"
    bytes_skill = _write_minimal_agent_plugin_pack(bytes_pack)
    for index in range(16):
        (bytes_skill / f"f{index:02d}").write_bytes(b"x" * (2 * 1024 * 1024))
    with (tmp_path / "bytes-spool").open("w+b") as spool:
        build_main._prepare_agent_plugin(Pack("bytes-pack", bytes_pack), spool)
    (bytes_skill / "plus-one").write_bytes(b"x")
    _assert_route_refusal_keeps_sentinel(bytes_pack, tmp_path / "bytes-dist")

    depth_pack = tmp_path / "packs" / "depth-pack"
    depth_skill = _write_minimal_agent_plugin_pack(depth_pack)
    depth_20 = depth_skill.joinpath(*(["nested"] * 19))
    depth_20.mkdir(parents=True)
    (depth_20 / "boundary").write_bytes(b"x")
    with (tmp_path / "depth-spool").open("w+b") as spool:
        build_main._prepare_agent_plugin(Pack("depth-pack", depth_pack), spool)
    depth_21 = depth_skill.joinpath(*(["other"] * 20))
    depth_21.mkdir(parents=True)
    (depth_21 / "plus-one").write_bytes(b"x")
    _assert_route_refusal_keeps_sentinel(depth_pack, tmp_path / "depth-dist")

    empty_depth_pack = tmp_path / "packs" / "empty-depth-pack"
    empty_depth_skill = _write_minimal_agent_plugin_pack(empty_depth_pack)
    empty_depth_skill.joinpath(*(["empty"] * 21)).mkdir(parents=True)
    _assert_route_refusal_keeps_sentinel(
        empty_depth_pack, tmp_path / "empty-depth-dist"
    )


def test_agent_plugin_refuses_hard_links_and_fifo_before_route_mutation(
    tmp_path: Path,
) -> None:
    """Exercise single-link and non-regular refusals through the route."""
    pack_path = tmp_path / "packs" / "portable-pack"
    skill = _write_minimal_agent_plugin_pack(pack_path)
    source = skill / "source"
    source.write_bytes(b"source")
    hardlink = skill / "hardlink"
    try:
        os.link(source, hardlink)
    except OSError:
        pytest.skip("hard links are unavailable on this filesystem")
    _assert_route_refusal_keeps_sentinel(pack_path, tmp_path / "hardlink-dist")
    hardlink.unlink()

    fifo = skill / "fifo"
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFOs are unavailable on this platform")
    os.mkfifo(fifo)
    _assert_route_refusal_keeps_sentinel(pack_path, tmp_path / "fifo-dist")


def test_agent_plugin_refuses_source_replacement_before_route_mutation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Replace a skill file between lstat/open and require inode refusal."""
    pack_path = tmp_path / "packs" / "portable-pack"
    skill = _write_minimal_agent_plugin_pack(pack_path)
    source = skill / "SKILL.md"
    source.write_bytes(b"before")
    original_open = file_safety.os.open
    replaced = False
    swapped_inodes: list[int] = []

    def replacing_open(path, flags, *args, **kwargs):
        nonlocal replaced
        if Path(path) == source and not replaced:
            replaced = True
            # Allocate the replacement inode while the original is still
            # linked, then swap atomically. Unlinking first lets Linux hand the
            # just-freed inode number straight back, which would leave the
            # dev/inode guard under test with nothing to observe.
            swapped_inodes.append(source.stat().st_ino)
            swap = source.with_name(source.name + ".swap")
            swap.write_bytes(b"after")
            swap.replace(source)
            swapped_inodes.append(source.stat().st_ino)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(file_safety.os, "open", replacing_open)
    _assert_route_refusal_keeps_sentinel(pack_path, tmp_path / "dist")
    assert replaced
    # Pin the fixture itself: a swap that reuses the inode leaves the guard
    # under test nothing to detect, so it must never pass unnoticed.
    assert swapped_inodes[0] != swapped_inodes[1]


def test_agent_plugin_bytes_and_executable_mode_share_one_confined_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Never combine descriptor-read bytes with a later path-sampled mode."""
    pack_path = tmp_path / "packs" / "portable-pack"
    skill = _write_minimal_agent_plugin_pack(pack_path)
    source = skill / "run.sh"
    source.write_bytes(b"#!/bin/sh\n")
    source.chmod(0o755)
    original_read = build_main.read_confined_regular_file
    replaced = False

    def read_then_replace(root: Path, path: Path, **kwargs):
        nonlocal replaced
        result = original_read(root, path, **kwargs)
        if path == source and not replaced:
            replaced = True
            source.unlink()
            source.write_bytes(b"replacement\n")
            source.chmod(0o644)
        return result

    monkeypatch.setattr(
        build_main, "read_confined_regular_file", read_then_replace
    )
    with (tmp_path / "spool").open("w+b") as spool:
        prepared = build_main._prepare_agent_plugin(
            Pack("portable-pack", pack_path), spool
        )
        projected = next(
            item for item in prepared.files if item.relative_path.name == "run.sh"
        )
        spool.seek(projected.spool_offset)
        assert spool.read(projected.byte_count) == b"#!/bin/sh\n"
        assert projected.executable
    assert replaced


def test_agent_plugin_post_write_audit_failure_is_not_silenced(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Keep the completed-tree audit mandatory at the route boundary."""
    pack_path = tmp_path / "packs" / "portable-pack"
    skill = _write_minimal_agent_plugin_pack(pack_path)
    (skill / "SKILL.md").write_bytes(b"# Example\n")

    def refuse_audit(route_root: Path) -> None:
        raise ValueError("agent-plugin: output error unsafe-output")

    monkeypatch.setattr(build_main, "_audit_agent_plugin_output", refuse_audit)
    with pytest.raises(ValueError, match=r"agent-plugin.*unsafe-output"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            tmp_path / "dist",
            {"adapter": {}},
            aggregate_scope="catalogue",
        )


def test_agent_plugin_refuses_unsafe_existing_route_without_overwrite(
    tmp_path: Path,
) -> None:
    """Treat a non-directory route root as an output collision."""
    pack_path = tmp_path / "packs" / "portable-pack"
    skill = _write_minimal_agent_plugin_pack(pack_path)
    (skill / "SKILL.md").write_bytes(b"# Example\n")
    route_root = tmp_path / "dist" / "agent-plugins"
    route_root.parent.mkdir(parents=True)
    route_root.write_bytes(b"keep")

    with pytest.raises(ValueError, match=r"agent-plugin.*unsafe-output"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            tmp_path / "dist",
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert route_root.read_bytes() == b"keep"


def test_agent_plugin_refuses_reparse_output_root_before_deletion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Apply the Windows reparse guard to stale route roots on every host."""
    pack_path = tmp_path / "packs" / "portable-pack"
    skill = _write_minimal_agent_plugin_pack(pack_path)
    (skill / "SKILL.md").write_bytes(b"# Example\n")
    route_root = tmp_path / "dist" / "agent-plugins"
    sentinel = route_root / "old" / "sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"keep")
    route_inode = route_root.lstat().st_ino
    original_reparse = build_main._is_reparse_point
    monkeypatch.setattr(
        build_main,
        "_is_reparse_point",
        lambda inspected: inspected.st_ino == route_inode
        or original_reparse(inspected),
    )

    with pytest.raises(ValueError, match=r"agent-plugin.*unsafe-output"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            tmp_path / "dist",
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert sentinel.read_bytes() == b"keep"


def test_agent_plugin_refuses_dangling_output_symlink_with_sanitized_error(
    tmp_path: Path,
) -> None:
    """Use lstat so a dangling stale route cannot bypass the output guard."""
    pack_path = tmp_path / "packs" / "portable-pack"
    skill = _write_minimal_agent_plugin_pack(pack_path)
    (skill / "SKILL.md").write_bytes(b"# Example\n")
    route_root = tmp_path / "dist" / "agent-plugins"
    route_root.parent.mkdir(parents=True)
    try:
        route_root.symlink_to(tmp_path / "missing-target", target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable on this filesystem")

    with pytest.raises(ValueError) as refusal:
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            tmp_path / "dist",
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert str(refusal.value) == "agent-plugin: output error unsafe-output"
    assert route_root.is_symlink()


def test_agent_plugin_route_sanitizes_duplicate_primitive_refusals(
    tmp_path: Path,
) -> None:
    """Keep generic uniqueness paths out of agent-plugin diagnostics."""
    pack_path = tmp_path / "packs" / "portable-pack"
    skills_root = pack_path / ".apm" / "skills"
    (skills_root / "duplicate").mkdir(parents=True)
    (skills_root / "duplicate.md").write_text("duplicate", encoding="utf-8")
    (pack_path / "pack.toml").write_text(
        '[pack]\nname = "portable-pack"\nversion = "1"\n', encoding="utf-8"
    )

    with pytest.raises(ValueError) as refusal:
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            tmp_path / "dist",
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    diagnostic = str(refusal.value)
    assert "agent-plugin" in diagnostic
    assert "primitive" in diagnostic
    assert "duplicate" in diagnostic
    assert str(tmp_path) not in diagnostic


def test_agent_plugin_projection_is_deterministic_and_removes_stale_files(
    tmp_path: Path,
) -> None:
    """Preserve skill bytes/modes and rebuild the complete route from empty."""
    pack_path = tmp_path / "packs" / "portable-pack"
    skill = pack_path / ".apm" / "skills" / "example"
    nested = skill / "scripts"
    nested.mkdir(parents=True)
    (pack_path / "pack.toml").write_text(
        '[pack]\nname = "portable-pack"\nversion = "1"\n', encoding="utf-8"
    )
    (skill / "SKILL.md").write_bytes(b"# Example\r\n")
    executable = nested / "run.sh"
    executable.write_bytes(b"#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    output = tmp_path / "dist"

    def build_inventory() -> list[tuple[str, bytes, bool]]:
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            output,
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
        root = output / "agent-plugins"
        return [
            (
                path.relative_to(root).as_posix(),
                path.read_bytes(),
                bool(path.stat().st_mode & 0o111),
            )
            for path in sorted(item for item in root.rglob("*") if item.is_file())
        ]

    first = build_inventory()
    stale = output / "agent-plugins" / "portable-pack" / "stale"
    stale.write_bytes(b"old")
    second = build_inventory()

    assert first == second
    assert not stale.exists()
    assert (
        output
        / "agent-plugins"
        / "portable-pack"
        / "skills"
        / "example"
        / "SKILL.md"
    ).read_bytes() == b"# Example\r\n"
    emitted_executable = (
        output
        / "agent-plugins"
        / "portable-pack"
        / "skills"
        / "example"
        / "scripts"
        / "run.sh"
    )
    assert emitted_executable.stat().st_mode & 0o111


# STUB: AC7-AC8 — extension content requires an active validated allocation.
def test_agent_plugin_extensions_require_active_valid_allocations(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Refuse reserved/unknown namespaces and accept one active schema fixture."""
    metadata = {
        "pack": {
            "name": "portable-pack",
            "version": "1",
            "metadata": {
                "agent-plugin": {
                    "extensions": {"dev.kiro": {"enabled": True}}
                }
            },
        }
    }
    with pytest.raises(ValueError, match=r"agent-plugin.*extension.*inactive"):
        derive_agent_plugin_manifest(metadata, pack_name="portable-pack")

    metadata["pack"]["metadata"]["agent-plugin"]["extensions"] = {
        "com.example.test": {"enabled": True}
    }
    with pytest.raises(ValueError, match=r"agent-plugin.*extension.*unallocated"):
        derive_agent_plugin_manifest(metadata, pack_name="portable-pack")

    registry = {
        "contract": {"version": "1.0"},
        "namespace": {
            "com.example.test": {
                "owner": "test-profile",
                "state": "active",
                "schema": "vendor/test/v1/test.schema.json",
            }
        },
    }
    original_read = build_main._read_bundled
    monkeypatch.setattr(
        build_main, "_load_agent_plugin_extension_registry", lambda: registry
    )
    monkeypatch.setattr(
        build_main,
        "_read_bundled",
        lambda name: json.dumps(
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["enabled"],
                "properties": {"enabled": {"type": "boolean"}},
            }
        )
        if name == "vendor/test/v1/test.schema.json"
        else original_read(name),
    )
    manifest = derive_agent_plugin_manifest(metadata, pack_name="portable-pack")
    assert manifest["extensions"] == {"com.example.test": {"enabled": True}}

    pack_path = tmp_path / "packs" / "portable-pack"
    extension_root = pack_path / "com.example.test"
    extension_root.mkdir(parents=True)
    (extension_root / "config.txt").write_bytes(b"extension-bytes")
    (pack_path / "pack.toml").write_text(
        '[pack]\nname = "portable-pack"\nversion = "1"\n\n'
        '[pack.metadata.agent-plugin.extensions."com.example.test"]\n'
        "enabled = true\n",
        encoding="utf-8",
    )
    output = tmp_path / "dist"

    extension_root.rename(pack_path / "Com.Example.Test")
    sentinel = output / "agent-plugins" / "old" / "sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"keep")
    with pytest.raises(ValueError, match=r"agent-plugin.*extension.*case-collision"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            output,
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert sentinel.read_bytes() == b"keep"
    (pack_path / "Com.Example.Test").rename(extension_root)

    output = tmp_path / "valid-dist"
    run_recipe(
        load_recipe("per-pack-agent-plugin"),
        [Pack("portable-pack", pack_path)],
        output,
        {"adapter": {}},
        aggregate_scope="catalogue",
    )
    assert (
        output
        / "agent-plugins"
        / "portable-pack"
        / "com.example.test"
        / "config.txt"
    ).read_bytes() == b"extension-bytes"

    file_pack = tmp_path / "packs" / "file-pack"
    file_pack.mkdir()
    (file_pack / "com.example.test").write_text("not a directory", encoding="utf-8")
    (file_pack / "pack.toml").write_text(
        '[pack]\nname = "file-pack"\nversion = "1"\n\n'
        '[pack.metadata.agent-plugin.extensions."com.example.test"]\n'
        "enabled = true\n",
        encoding="utf-8",
    )
    sentinel = tmp_path / "file-dist" / "agent-plugins" / "old" / "sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"keep")
    with pytest.raises(ValueError, match=r"agent-plugin.*extension.*unsafe-source"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("file-pack", file_pack)],
            tmp_path / "file-dist",
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert sentinel.read_bytes() == b"keep"

    extension_values = metadata["pack"]["metadata"]["agent-plugin"]["extensions"]
    extension_values["com.example.test"] = {"items": list(range(257))}
    with pytest.raises(ValueError, match=r"agent-plugin.*extension.*manifest-limit"):
        derive_agent_plugin_manifest(metadata, pack_name="portable-pack")

    extension_values["com.example.test"] = {"enabled": math.nan}
    with pytest.raises(ValueError, match=r"agent-plugin.*extension.*strict-json"):
        derive_agent_plugin_manifest(metadata, pack_name="portable-pack")

    extension_values["com.example.test"] = {"enabled": "yes"}
    with pytest.raises(ValueError, match=r"agent-plugin.*extension.*schema-invalid"):
        derive_agent_plugin_manifest(metadata, pack_name="portable-pack")


@pytest.mark.parametrize(
    ("namespace", "error_class"),
    [("com.example.ghost", "undeclared"), ("dev.kiro", "inactive")],
)
def test_agent_plugin_projection_refuses_unadmitted_extension_directories(
    tmp_path: Path,
    namespace: str,
    error_class: str,
) -> None:
    """Reject undeclared and reserved extension content before route mutation."""
    pack_path = tmp_path / "packs" / "portable-pack"
    extension_root = pack_path / namespace
    extension_root.mkdir(parents=True)
    (extension_root / "config.txt").write_text("extension", encoding="utf-8")
    (pack_path / "pack.toml").write_text(
        '[pack]\nname = "portable-pack"\nversion = "1"\n', encoding="utf-8"
    )
    output = tmp_path / "dist"
    sentinel = output / "agent-plugins" / "old" / "sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"keep")

    with pytest.raises(ValueError, match=rf"agent-plugin.*extension.*{error_class}"):
        run_recipe(
            load_recipe("per-pack-agent-plugin"),
            [Pack("portable-pack", pack_path)],
            output,
            {"adapter": {}},
            aggregate_scope="catalogue",
        )
    assert sentinel.read_bytes() == b"keep"


def test_default_build_emits_complete_agent_plugin_roster(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exercise the normal build entry point over the complete catalogue."""
    corpus = REPO_ROOT / "packs"
    if not corpus.is_dir():
        # Checkout-only: a published sdist or wheel ships no catalogue corpus.
        return
    run_default_build(corpus, tmp_path)
    route_root = tmp_path / "agent-plugins"
    expected = {
        "agent-skill-engineering",
        "atlassian",
        "catalogue-curation",
        "contracts",
        "converters",
        "figma",
        "github",
        "governance-extras",
        "iac-terraform",
        "linear",
        "monorepo-extras",
        "product-documentation",
        "product-strategy",
        "user-guide-diataxis",
    }
    assert {path.name for path in route_root.iterdir()} == expected
    assert all((route_root / name / "plugin.json").is_file() for name in expected)

    diagnostics = capsys.readouterr().err.splitlines()
    exclusions = [
        line for line in diagnostics if line.startswith("agent-plugin: pack ")
    ]
    assert set(exclusions) == {
        'agent-plugin: pack "architect" excluded by dropped primitives ["agent"]',
        'agent-plugin: pack "core" excluded by dropped primitives '
        '["agent","command","hook-body","hook-wiring","kiro-ide-hook"]',
        'agent-plugin: pack "credential-brokers" excluded by dropped primitives '
        '["adapter-root-bins","shared-libs","user-libs"]',
        'agent-plugin: pack "desk-research" excluded by dropped primitives ["agent"]',
        'agent-plugin: pack "experience-design" excluded by dropped primitives '
        '["agent"]',
        'agent-plugin: pack "frontend-engineering" excluded by dropped primitives '
        '["agent"]',
        'agent-plugin: pack "product-engineering" excluded by dropped primitives '
        '["agent"]',
        'agent-plugin: pack "release-engineering" excluded by dropped primitives '
        '["agent"]',
    }
