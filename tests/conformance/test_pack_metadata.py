"""Portable catalogue manifest and marketplace rules."""

from __future__ import annotations

import json
import tomllib
from importlib.resources import files
from pathlib import Path

import pytest

CATALOGUE_ROOT = Path(__file__).resolve().parents[2]
PACKS_DIR = CATALOGUE_ROOT / "packs"
MARKETPLACE_PATH = CATALOGUE_ROOT / ".claude-plugin" / "marketplace.json"


def _bundled_schema(name: str) -> dict:
    """Load a runtime schema without requiring a source-checkout contract tree."""
    resource = files("agentbundle").joinpath("_data", name)
    return json.loads(resource.read_text(encoding="utf-8"))


def _pack_dirs() -> list[Path]:
    return sorted(
        path
        for path in PACKS_DIR.iterdir()
        if path.is_dir()
        and not path.name.startswith("_")
        and (path / "pack.toml").is_file()
    )


def _pack_data(pack_dir: Path) -> dict:
    return tomllib.loads((pack_dir / "pack.toml").read_text(encoding="utf-8"))[
        "pack"
    ]


@pytest.mark.parametrize("pack_dir", _pack_dirs(), ids=lambda path: path.name)
def test_pack_declares_enriched_metadata(pack_dir: Path) -> None:
    pack = _pack_data(pack_dir)
    assert pack.get("readme") == "README.md", f"{pack_dir.name}: readme"
    assert (pack_dir / "README.md").is_file(), f"{pack_dir.name}: README.md"
    assert isinstance(pack.get("license"), str) and pack["license"]
    links = pack.get("links")
    assert isinstance(links, dict)
    assert isinstance(links.get("repository"), str) and links["repository"]
    for field in ("categories", "keywords"):
        values = pack.get(field)
        assert isinstance(values, list) and values, f"{pack_dir.name}: {field}"
        assert len(values) <= 5, f"{pack_dir.name}: {field} capped at 5"
    maintainers = pack.get("maintainers")
    assert isinstance(maintainers, list) and maintainers
    assert isinstance(maintainers[0].get("name"), str) and maintainers[0]["name"]


@pytest.mark.parametrize("pack_dir", _pack_dirs(), ids=lambda path: path.name)
def test_pack_and_plugin_versions_match(pack_dir: Path) -> None:
    plugin_path = pack_dir / ".claude-plugin" / "plugin.json"
    if not plugin_path.exists():
        return
    plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    assert plugin.get("version") == _pack_data(pack_dir)["version"]


def test_source_plugin_manifests_obey_schema() -> None:
    from agentbundle.build.validate import validate

    manifests = sorted(
        path
        for pack_dir in _pack_dirs()
        if (path := pack_dir / ".claude-plugin" / "plugin.json").is_file()
    )
    if not manifests:
        return
    schema = _bundled_schema("plugin-manifest.schema.json")
    for path in manifests:
        content = json.loads(path.read_text(encoding="utf-8"))
        assert "hooks" not in content, f"{path.relative_to(CATALOGUE_ROOT)}: hooks"
        errors = validate(content, schema)
        assert not errors, f"{path.relative_to(CATALOGUE_ROOT)}: {errors}"


def test_root_marketplace_entries_obey_schema() -> None:
    from agentbundle.build.validate import validate

    if not MARKETPLACE_PATH.is_file():
        return
    marketplace = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    entries = marketplace.get("plugins", [])
    if not entries:
        return
    schema = _bundled_schema("marketplace-entry.schema.json")
    for entry in entries:
        assert not validate(entry, schema), entry.get("name", "<unnamed>")


def test_root_marketplace_has_portable_metadata_shapes() -> None:
    if not MARKETPLACE_PATH.is_file():
        return
    marketplace = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    assert "name" in marketplace
    assert isinstance(marketplace.get("owner"), dict)
    for plugin in marketplace.get("plugins", []):
        assert isinstance(plugin.get("author"), dict), plugin.get("name")
        source = plugin.get("source")
        if source is None:
            continue
        assert isinstance(source, dict), plugin.get("name")
        assert source.get("source") == "git-subdir", plugin.get("name")
        assert isinstance(source.get("url"), str) and source["url"].startswith(
            "https://github.com/"
        )
        assert source.get("path")
        assert source.get("ref") or source.get("sha")
        assert "branch" not in source and "directory" not in source
