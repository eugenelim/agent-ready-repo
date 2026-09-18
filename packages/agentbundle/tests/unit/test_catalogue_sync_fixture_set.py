"""Smoke coverage for the shared catalogue-sync fixture set."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path


def test_catalogue_sync_fixture_set_composes(
    self_hosted_source: Path,
    upstream: Path,
    derived_tree: Path,
    upstream_with_bumped_pack: Path,
) -> None:
    """Each fixture provides the state later catalogue-sync tests consume."""
    source_pack = tomllib.loads(
        (self_hosted_source / "packs" / "alpha" / "pack.toml").read_text(
            encoding="utf-8"
        )
    )
    assert list((self_hosted_source / "packs").iterdir()) == [
        self_hosted_source / "packs" / "alpha"
    ]
    assert upstream == self_hosted_source
    assert source_pack["pack"]["name"] == "alpha"

    state = json.loads(
        (derived_tree / ".agentbundle" / "self-host-state.json").read_text(
            encoding="utf-8"
        )
    )
    assert state["schema_version"] == "3"
    assert state["recipe"]["packs"] == ["alpha"]
    assert state["pin"]["archive_sha256"] is None

    derived_pack = tomllib.loads(
        (derived_tree / "packs" / "alpha" / "pack.toml").read_text(encoding="utf-8")
    )
    bumped_pack = tomllib.loads(
        (
            upstream_with_bumped_pack / "packs" / "alpha" / "pack.toml"
        ).read_text(encoding="utf-8")
    )
    assert bumped_pack["pack"]["version"] > derived_pack["pack"]["version"]
