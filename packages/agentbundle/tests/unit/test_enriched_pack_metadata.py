"""enriched-pack-manifest T8: every shipped pack carries the enriched floor.

AC8: every shipped pack declares, at minimum, `readme`, `license`,
`[pack.links].repository`, `categories`, and `keywords`, plus a maintainer —
and `agentbundle validate` accepts the schema. This pins the *real* shipped
manifests (not a synthetic fixture), so a pack silently losing its metadata —
or a botched bump — trips here rather than slipping through.

Parametrized over the packs actually present (not a hardcoded list/count), so a
newly-added pack is automatically held to the same floor.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
PACKS_DIR = REPO_ROOT / "packs"


def _all_packs() -> list[str]:
    return sorted(
        p.name for p in PACKS_DIR.iterdir()
        if p.is_dir() and (p / "pack.toml").exists()
    )


def _load(pack: str) -> dict:
    return tomllib.loads((PACKS_DIR / pack / "pack.toml").read_text("utf-8"))["pack"]


def test_at_least_the_known_packs_are_present():
    """A floor, not a count — guards against the glob silently returning [] (a
    broken REPO_ROOT) without breaking when a 13th pack is added."""
    present = set(_all_packs())
    assert {"core", "desk-research", "product-engineering"} <= present
    assert len(present) >= 12


@pytest.mark.parametrize("pack", _all_packs())
def test_pack_declares_enriched_floor(pack):
    p = _load(pack)

    assert p.get("readme") == "README.md", f"{pack}: readme must be 'README.md'"
    assert (PACKS_DIR / pack / "README.md").is_file(), f"{pack}: README.md missing"

    assert isinstance(p.get("license"), str) and p["license"], f"{pack}: license"

    links = p.get("links")
    assert isinstance(links, dict), f"{pack}: [pack.links] missing"
    assert isinstance(links.get("repository"), str) and links["repository"], (
        f"{pack}: [pack.links].repository missing"
    )

    cats = p.get("categories")
    assert isinstance(cats, list) and cats, f"{pack}: categories must be non-empty"
    assert len(cats) <= 5, f"{pack}: categories capped at 5"

    kws = p.get("keywords")
    assert isinstance(kws, list) and kws, f"{pack}: keywords must be non-empty"
    assert len(kws) <= 5, f"{pack}: keywords capped at 5"

    maints = p.get("maintainers")
    assert isinstance(maints, list) and maints, f"{pack}: maintainers must be present"
    assert isinstance(maints[0].get("name"), str) and maints[0]["name"], (
        f"{pack}: first maintainer needs a name"
    )


@pytest.mark.parametrize("pack", _all_packs())
def test_pack_toml_version_matches_plugin_json(pack):
    """The hand-authored plugin.json version stays in lockstep with pack.toml
    (the marketplace entry carries plugin.json's version)."""
    pack_version = _load(pack)["version"]
    plugin_path = PACKS_DIR / pack / ".claude-plugin" / "plugin.json"
    if plugin_path.exists():
        manifest = json.loads(plugin_path.read_text("utf-8"))
        assert manifest.get("version") == pack_version, (
            f"{pack}: plugin.json version {manifest.get('version')!r} != "
            f"pack.toml version {pack_version!r}"
        )
