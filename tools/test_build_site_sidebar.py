"""Tests for generated sidebar assembly in tools/build-site.py.

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
with (REPO_ROOT / "site.toml").open("rb") as _f:
    # Read rather than hand-copy: a seventh super-group must not leave the
    # AC8 nesting guard silently blind to it.
    SUPER_GROUP_LABELS = {g["label"] for g in tomllib.load(_f).get("groups", [])}


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
    # No count assertion: guides/AGENTS.md documents the registry as
    # shrinking as pages adopt `title:`, so pinning its size would forbid
    # the workflow. The pair loop below is the actual guard.
    assert baseline
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


# ---------------------------------------------------------------------------
# Real-tree invariants.
#
# The synthetic fixtures below/elsewhere document intent; these constrain it.
# Two reviewers independently showed that deleting the nav-eligibility rule or
# the duplicate-slug tie-break left every other test green while the published
# sidebar regressed — a test that only moves with the code cannot catch the
# code being wrong.
# ---------------------------------------------------------------------------

def _all_groups(node):
    """Yield every group node (anything carrying `items`), depth-first."""
    for item in node.get("items", []):
        if "items" in item:
            yield item
            yield from _all_groups(item)


def test_nav_ineligible_set_is_exactly_the_declared_exceptions():
    """Pinned against an independent expectation, not against the projection —
    AC2's set equality compares the generator with itself, so it moves with an
    eligibility bug rather than catching one."""
    records = build_site.build_guide_inventory(REPO_ROOT / "guides")
    ineligible = {
        r["source_path"].relative_to(REPO_ROOT / "guides").as_posix()
        for r in records if not r["nav_eligible"]
    }
    assert ineligible == {
        "AGENTS.md",
        "_shared/explanation/README.md",
        "_shared/how-to/README.md",
        "_shared/reference/README.md",
        "_shared/tutorials/README.md",
    }, "the reader-facing carve-out changed — update spec § Intent in the same PR"


def test_no_sibling_label_collision_anywhere_in_the_real_tree():
    """The collision that shipped twice was a kind-index page named "How-to"
    sitting beside the "How-to" bucket. It only arises in the real tree, so a
    synthetic fixture cannot reproduce it."""
    guides = _guides_group()
    for group in [guides, *_all_groups(guides)]:
        labels = [i["label"] for i in group.get("items", [])]
        assert len(labels) == len(set(labels)), (
            f"sibling label collision in {group.get('label')!r}: {labels}")


def test_every_guides_directory_is_declared_in_site_toml():
    """AC8. An undeclared directory silently takes the title-cased fallback and
    is appended last — `iac-terraform` would read "Iac Terraform" rather than
    its curated "IaC (Terraform)"."""
    dirs = {p.name for p in (REPO_ROOT / "guides").iterdir() if p.is_dir()}
    with (REPO_ROOT / "site.toml").open("rb") as f:
        declared = {g["dir"] for g in tomllib.load(f).get("guide_groups", [])}
    assert dirs == declared, (
        f"undeclared: {sorted(dirs - declared)}; "
        f"stale: {sorted(declared - dirs)}")


def test_atlassian_cross_kind_run_survives():
    """The independent regression witness — a threaded sequence this PR did not
    author, so it cannot be tautological with the arc it added."""
    guides = _guides_group()
    atlassian = next(g for g in guides["items"] if g.get("label") == "Atlassian")
    direct = [i["slug"] for i in atlassian["items"] if "slug" in i]
    assert direct[:5] == [
        "guides/atlassian",
        "guides/atlassian/tutorials/review-your-team-backlog",
        "guides/atlassian/how-to/work-with-jira",
        "guides/atlassian/reference/atlassian-skills",
        "guides/atlassian/explanation/atlassian-pack",
    ], "the ordered run must stay flat and ahead of the kind buckets"


def test_duplicate_slug_resolves_deterministically(tmp_path):
    """The tie-break AC10 depends on. The real tree has no duplicates, so the
    shuffled-enumerator test exercises nothing about it."""
    root = tmp_path / "guides"
    for name, title in (("a.md", "A"), ("b.md", "B")):
        p = root / "pack" / "how-to" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"---\ntitle: {title}\nsummary: s\npack: pack\nkind: how-to\n"
                     f"slug: guides/pack/how-to/same\n---\n", encoding="utf-8")

    paths = sorted(root.rglob("*.md"))
    forward = build_site.build_guide_inventory(root, enumerator=lambda _r: paths)
    reverse = build_site.build_guide_inventory(
        root, enumerator=lambda _r: list(reversed(paths)))
    assert [r["title"] for r in forward] == [r["title"] for r in reverse]


def test_malformed_guide_group_entry_is_skipped_not_raised():
    """A missing `dir` or `label` previously raised a bare KeyError mid-build,
    after packs had already been mirrored. discover_packs() warns and skips on
    the sibling table; this matches it."""
    records = [{"source_path": Path("x.md"), "pack": "a", "kind": "how-to",
                "order": None, "title": None, "slug": "guides/a/how-to/x",
                "is_index": False, "nav_eligible": True}]
    groups = [{"label": "no dir"}, {"dir": "a", "label": "Ay"}, {"dir": "b"}]
    out = build_site.project_guide_sidebar(records, groups, {})
    assert [i["label"] for i in out["items"]] == ["Ay"]


def test_malformed_baseline_entry_is_skipped_not_raised(tmp_path):
    p = tmp_path / "baseline.toml"
    p.write_text('[[entry]]\nslug = "guides/a"\n\n'
                 '[[entry]]\nslug = "guides/b"\nlabel = "Bee"\n', encoding="utf-8")
    assert build_site.load_guide_baseline(p) == {"guides/b": "Bee"}
