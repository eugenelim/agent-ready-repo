"""Tests for generated sidebar assembly in tools/build-site.py (6 tests).

Covers T7 of docs/specs/guides-sidebar-generation. These are the criteria that
actually deliver the feature, asserted against the real tree:

- AC2  set equality, not a subset — a subset check passes while dropping pages
- AC9  (slug, label) pair equality — a slug-only check is blind to the 90
       label regressions filename derivation would cause
- AC10 determinism under a shuffled enumerator
"""
from __future__ import annotations

import importlib.util
import json
import random
import sys
import tomllib
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent / "build-site.py"
_spec = importlib.util.spec_from_file_location("build_site", _SCRIPT)
build_site = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["build_site"] = build_site
_spec.loader.exec_module(build_site)  # type: ignore[union-attr]

REPO_ROOT = Path(__file__).resolve().parent.parent
SUPER_GROUP_LABELS = {"Foundation", "Agent workflows", "Engineering",
                      "Integrations", "Content and design", "Catalogue operations"}


def _pairs(node) -> list[tuple[str, str]]:
    out = []
    for item in node.get("items", []):
        if "slug" in item:
            out.append((item["slug"], item["label"]))
        else:
            out.extend(_pairs(item))
    return out


def _guides_group() -> dict:
    return build_site.build_guides_sidebar_group(REPO_ROOT, REPO_ROOT / "site.toml")


# ---------------------------------------------------------------------------

def test_sidebar_includes_pack_catalogue_and_guides(tmp_path):
    packs = [{"slug": "core", "display_name": "Core", "group": "Foundation"}]
    out = tmp_path / "sidebar-config.json"
    build_site.generate_sidebar_config(packs, out, guides_group=_guides_group())
    sidebar = json.loads(out.read_text(encoding="utf-8"))
    labels = [g["label"] for g in sidebar]
    assert "Pack Catalogue" in labels
    assert "Foundation" in labels
    assert labels[-1] == "Guides"


def test_guides_group_slugs_equal_eligible_slugs():
    """Set equality over the Guides groups only — pack-catalogue and top-level
    slugs are outside this set."""
    records = build_site.build_guide_inventory(REPO_ROOT / "guides")
    eligible = {r["slug"] for r in records if r["nav_eligible"]}
    projected = {slug for slug, _ in _pairs(_guides_group())}
    assert projected == eligible
    assert "guides/AGENTS" not in projected


def test_no_baseline_pair_regressed():
    """Every frozen (slug, label) pair survives generation unchanged."""
    baseline = build_site.load_guide_baseline(REPO_ROOT / "guide-nav-baseline.toml")
    assert len(baseline) == 119, "baseline should carry the full pre-change tree"
    projected = dict(_pairs(_guides_group()))
    regressed = {
        slug: (label, projected.get(slug, "<ABSENT>"))
        for slug, label in baseline.items()
        if projected.get(slug) != label
    }
    assert not regressed, f"labels or pages regressed: {regressed}"


def test_guides_nesting_is_one_group_level():
    """Pack groups sit directly under Guides; the six site.toml super-group
    labels are not inherited, which would push nesting to five levels."""
    guides = _guides_group()
    for item in guides["items"]:
        assert item.get("label") not in SUPER_GROUP_LABELS
        for child in item.get("items", []):
            # A pack group's children are pages or kind buckets — never groups
            # of groups.
            for grandchild in child.get("items", []):
                assert "slug" in grandchild, "kind buckets must contain pages only"


def test_shuffled_enumerator_is_byte_identical():
    """Shuffle the injected enumerator, not a re-glob — otherwise the test
    passes because sorted() is stable, having exercised nothing."""
    guides_root = REPO_ROOT / "guides"
    paths = list(guides_root.rglob("*.md"))
    rng = random.Random(1234)

    renders = []
    for _ in range(2):
        shuffled = list(paths)
        rng.shuffle(shuffled)
        records = build_site.build_guide_inventory(
            guides_root, enumerator=lambda _root, p=shuffled: p)
        with (REPO_ROOT / "site.toml").open("rb") as f:
            groups = tomllib.load(f).get("guide_groups", [])
        baseline = build_site.load_guide_baseline(REPO_ROOT / "guide-nav-baseline.toml")
        renders.append(json.dumps(
            build_site.project_guide_sidebar(records, groups, baseline), indent=2))

    assert renders[0] == renders[1]


def test_missing_baseline_degrades_without_raising(tmp_path):
    assert build_site.load_guide_baseline(tmp_path / "absent.toml") == {}
