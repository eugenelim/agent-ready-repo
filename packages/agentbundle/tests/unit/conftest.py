"""Shared fixtures for catalogue-sync unit tests."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest


def _write_source_catalogue(root: Path, *, pack_version: str) -> None:
    """Create the one-pack source catalogue used by sync tests."""
    root.mkdir()
    (root / "catalogue.toml").write_text(
        '[catalogue]\n'
        'name = "upstream-catalogue"\n'
        'display_name = "Upstream Catalogue"\n'
        'description = "A source catalogue for sync tests."\n',
        encoding="utf-8",
    )
    pack = root / "packs" / "alpha"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\n'
        'name = "alpha"\n'
        f'version = "{pack_version}"\n',
        encoding="utf-8",
    )
    (pack / "README.md").write_text("# Alpha\n", encoding="utf-8")


@pytest.fixture
def self_hosted_source(tmp_path: Path) -> Path:
    """Return a minimal self-hosted source catalogue with one pack."""
    source = tmp_path / "self-hosted-source"
    _write_source_catalogue(source, pack_version="1.0.0")
    return source


@pytest.fixture
def upstream(self_hosted_source: Path) -> Path:
    """Return the upstream catalogue resolved by catalogue sync."""
    return self_hosted_source


@pytest.fixture
def derived_tree(tmp_path: Path, upstream: Path) -> Path:
    """Return a schema-3 derived tree with a local-source null-digest pin."""
    derived = tmp_path / "derived-tree"
    derived.mkdir()
    (derived / "catalogue.toml").write_text(
        '[catalogue]\nname = "derived-catalogue"\n', encoding="utf-8"
    )
    shutil.copytree(upstream / "packs", derived / "packs")

    pack_toml = (derived / "packs" / "alpha" / "pack.toml").read_bytes()
    readme = (derived / "packs" / "alpha" / "README.md").read_bytes()
    state = {
        "schema_version": "3",
        "managed_paths": [
            {
                "path": "packs/alpha/README.md",
                "sha256": hashlib.sha256(readme).hexdigest(),
            },
            {
                "path": "packs/alpha/pack.toml",
                "sha256": hashlib.sha256(pack_toml).hexdigest(),
            },
        ],
        "adapters": [],
        "managed_target_path": "",
        "source_pack_identity": "upstream-catalogue",
        "source_root_kind": "self-hosted-source",
        "recipe": {
            "packs": ["alpha"],
            "profiles": [],
            "guides": "selected",
            "attribution": "white-label",
            "tooling": "external",
            "name": "derived-catalogue",
            "display_name": "Derived Catalogue",
            "description": "A derived catalogue for sync tests.",
            "owner_name": "Example Maintainer",
            "owner_email": "maintainer@example.com",
            "preferred_adapter": "claude-code",
            "repository_url": None,
        },
        "pin": {
            "source_revision": None,
            "archive_sha256": None,
            "synced_at": "2026-09-17T00:00:00Z",
        },
    }
    state_path = derived / ".agentbundle" / "self-host-state.json"
    state_path.parent.mkdir()
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return derived


@pytest.fixture
def upstream_with_bumped_pack(tmp_path: Path, upstream: Path) -> Path:
    """Return an upstream copy whose pack version exceeds the derived version."""
    bumped = tmp_path / "upstream-with-bumped-pack"
    shutil.copytree(upstream, bumped)
    pack_toml = bumped / "packs" / "alpha" / "pack.toml"
    pack_toml.write_text(
        pack_toml.read_text(encoding="utf-8").replace(
            'version = "1.0.0"', 'version = "1.1.0"'
        ),
        encoding="utf-8",
    )
    return bumped
