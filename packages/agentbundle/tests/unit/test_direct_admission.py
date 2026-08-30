"""Construction stubs for direct-source admission and normalization."""

from __future__ import annotations

import importlib
import sys

import pytest


def test_classification_contract():
    # STUB: AC1, AC2, AC14, AC15, AC16, AC17, AC25, AC32, AC33, AC34, AC35, AC36
    import agentbundle.direct_source as direct_source

    assert callable(direct_source.classify_direct_source)


def test_normalization_projection_parity():
    # STUB: AC24, AC25
    import agentbundle.direct_source as direct_source

    assert callable(direct_source.normalize_direct_source)


def test_bounded_metadata_characterization(monkeypatch):
    # AC14, AC15, AC16, AC17, AC18, AC19, AC20
    import agentbundle.bounded_metadata as bounded_metadata
    from agentbundle.catalogue_tooling import okf_discovery

    limits = bounded_metadata.MetadataLimits()
    discovery_limits = okf_discovery.DiscoveryLimits()
    valid_frontmatter = b"---\nname: demo\ndescription: concise\nmetadata:\n  boundaries:\n    - filesystem_read\n---\n# Demo\n"

    assert bounded_metadata.parse_bounded_metadata(valid_frontmatter) == {
        "name": "demo",
        "description": "concise",
        "metadata": {"boundaries": ["filesystem_read"]},
    }
    assert bounded_metadata.parse_bounded_toml(b"schema = 1\n[pack]\nname = 'demo'\n") == {
        "schema": 1,
        "pack": {"name": "demo"},
    }
    assert limits.max_skill_bytes == 2 * 1024 * 1024
    assert limits.max_pack_toml_bytes == 1024 * 1024
    assert limits.max_frontmatter_bytes == discovery_limits.max_frontmatter_bytes
    assert limits.max_frontmatter_depth == discovery_limits.max_frontmatter_depth
    assert limits.max_list_items == discovery_limits.max_list_items
    assert limits.max_compatibility_keys == discovery_limits.max_compatibility_keys
    assert bounded_metadata.parse_bounded_metadata(valid_frontmatter) == okf_discovery._parse_frontmatter(
        valid_frontmatter,
        "SKILL.md",
        discovery_limits,
    )
    assert bounded_metadata.parse_bounded_metadata(
        valid_frontmatter + b"x" * (1024 * 1024 + 1)
    )["name"] == "demo"

    for forbidden in (b"description: !tag value", b"description: &anchor value", b"description: *anchor"):
        with pytest.raises(bounded_metadata.BoundedMetadataError):
            bounded_metadata.parse_bounded_metadata(b"---\nname: demo\n" + forbidden + b"\n---\n")
    with pytest.raises(bounded_metadata.BoundedMetadataError):
        bounded_metadata.parse_bounded_metadata(b"---\nname: demo\nunknown: value\n---\n")

    for invalid_toml in (b"[pack\n", b"name = \xff"):
        with pytest.raises(bounded_metadata.BoundedMetadataError):
            bounded_metadata.parse_bounded_toml(invalid_toml)
    with pytest.raises(bounded_metadata.BoundedMetadataError):
        bounded_metadata.parse_bounded_toml(b"x = 1", limits=bounded_metadata.MetadataLimits(max_pack_toml_bytes=0))
    monkeypatch.setattr(
        bounded_metadata.tomllib,
        "loads",
        lambda _: (_ for _ in ()).throw(RuntimeError("parser fault")),
    )
    with pytest.raises(bounded_metadata.BoundedMetadataError):
        bounded_metadata.parse_bounded_toml(b"schema = 1")

    assert bounded_metadata.validate_publisher_value("x" * 4096, "description") == "x" * 4096
    for label in ("name", "description"):
        with pytest.raises(bounded_metadata.BoundedMetadataError):
            bounded_metadata.validate_publisher_value("x" * 4097, label)

    previous_yaml = sys.modules.pop("yaml", None)
    sys.modules.pop("agentbundle.bounded_metadata", None)
    try:
        importlib.import_module("agentbundle.bounded_metadata")
        assert "yaml" not in sys.modules
    finally:
        sys.modules.pop("agentbundle.bounded_metadata", None)
        if previous_yaml is not None:
            sys.modules["yaml"] = previous_yaml


def test_direct_admission_diagnostic_registry():
    # STUB: AC9, AC11, AC14, AC15, AC16, AC17, AC18, AC19, AC20, AC21, AC25, AC27, AC34, AC39
    import agentbundle.direct_source as direct_source

    assert callable(direct_source.admit_direct_source)
