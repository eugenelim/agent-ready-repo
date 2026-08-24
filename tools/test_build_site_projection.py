"""Tests for guide sidebar projection in tools/build-site.py.

Covers T6 of docs/specs/guides-sidebar-generation: inventory records become
Starlight sidebar groups.

Emission order within a pack group is fixed by spec § Layer 2:
    is_index -> order-declaring -> kind-less non-index -> kind buckets
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent / "build-site.py"
_spec = importlib.util.spec_from_file_location("build_site", _SCRIPT)
build_site = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["build_site"] = build_site
_spec.loader.exec_module(build_site)  # type: ignore[union-attr]

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rec(slug, *, pack=None, kind=None, order=None, title=None,
         is_index=False, nav_eligible=True):
    return {
        "source_path": Path(slug + ".md"), "pack": pack, "kind": kind,
        "order": order, "title": title, "slug": slug,
        "is_index": is_index, "nav_eligible": nav_eligible,
    }


def _group(projected, label):
    return next(g for g in projected["items"] if g.get("label") == label)


def _labels(items):
    return [i.get("label") for i in items]


def _slugs(node):
    """Flatten every slug under a node, depth-first."""
    out = []
    for item in node.get("items", []):
        if "slug" in item:
            out.append(item["slug"])
        else:
            out.extend(_slugs(item))
    return out


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------

def test_order_sorts_across_kinds():
    """The atlassian shape: one ordered run spanning four different kinds.
    Grouping by kind first would scatter 1/2/3/4 one per bucket."""
    records = [
        _rec("guides/a/tutorials/one", pack="a", kind="tutorial", order=1),
        _rec("guides/a/how-to/two", pack="a", kind="how-to", order=2),
        _rec("guides/a/reference/three", pack="a", kind="reference", order=3),
        _rec("guides/a/explanation/four", pack="a", kind="explanation", order=4),
    ]
    out = build_site.project_guide_sidebar(records, [{"dir": "a", "label": "A"}], {})
    assert _slugs(_group(out, "A")) == [
        "guides/a/tutorials/one", "guides/a/how-to/two",
        "guides/a/reference/three", "guides/a/explanation/four",
    ]


def test_index_records_are_direct_group_items():
    records = [
        _rec("guides/a/how-to/x", pack="a", kind="how-to"),
        _rec("guides/a", pack="a", is_index=True),
    ]
    out = build_site.project_guide_sidebar(records, [{"dir": "a", "label": "A"}], {})
    items = _group(out, "A")["items"]
    assert "slug" in items[0] and items[0]["slug"] == "guides/a"


def test_root_readme_is_direct_item_of_guides_group():
    """It has no pack segment, so it belongs to the tree, not to a pack."""
    records = [
        _rec("guides", pack=None, is_index=True),
        _rec("guides/a/how-to/x", pack="a", kind="how-to"),
    ]
    out = build_site.project_guide_sidebar(records, [{"dir": "a", "label": "A"}], {})
    assert out["items"][0].get("slug") == "guides"


def test_kind_buckets_use_canonical_sequence():
    records = [
        _rec("guides/a/explanation/e", pack="a", kind="explanation"),
        _rec("guides/a/reference/r", pack="a", kind="reference"),
        _rec("guides/a/tutorials/t", pack="a", kind="tutorial"),
        _rec("guides/a/how-to/h", pack="a", kind="how-to"),
    ]
    out = build_site.project_guide_sidebar(records, [{"dir": "a", "label": "A"}], {})
    assert _labels(_group(out, "A")["items"]) == [
        "Tutorials", "How-to", "Reference", "Explanation",
    ]


def test_kindless_non_index_record_precedes_kind_buckets():
    """A record that is neither an index nor kind-bearing falls through into a
    bucket that does not exist and is silently dropped without an explicit rule.

    `guides/_reference/catalogue-format` was the one real file in that shape, which
    is why this case is written with its path. spec/guide-metadata-completion moved
    it to `guides/_shared/reference/catalogue-format.md` and gave it
    `kind: reference`, so no real file is kind-less today. The rule is retained
    deliberately: the shape can recur the moment a guide lands without a kind, and
    the record below is synthetic precisely so the rule outlives its motivating
    file."""
    records = [
        _rec("guides/_reference/catalogue-format", pack="_reference"),
        _rec("guides/_reference/how-to/x", pack="_reference", kind="how-to"),
    ]
    out = build_site.project_guide_sidebar(
        records, [{"dir": "_reference", "label": "Ref"}], {})
    items = _group(out, "Ref")["items"]
    assert items[0].get("slug") == "guides/_reference/catalogue-format"
    assert _labels(items[1:]) == ["How-to"]


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

def test_label_precedence_baseline_then_title_then_derived():
    """Baseline first. 13 real pages carry a `title:` differing from their nav
    label, so title-first would silently rewrite them."""
    records = [
        _rec("guides/a/how-to/one", pack="a", kind="how-to", title="Frontmatter Title"),
        _rec("guides/a/how-to/two", pack="a", kind="how-to", title="Only Title"),
        _rec("guides/a/how-to/three-word-slug", pack="a", kind="how-to"),
    ]
    baseline = {"guides/a/how-to/one": "Baseline Label"}
    out = build_site.project_guide_sidebar(records, [{"dir": "a", "label": "A"}], baseline)
    bucket = _group(out, "A")["items"][0]
    assert _labels(bucket["items"]) == ["Baseline Label", "Only Title", "Three Word Slug"]


def test_no_frontmatter_page_is_projected():
    records = [_rec("guides/a/how-to/bug-fix", pack="a", kind="how-to")]
    out = build_site.project_guide_sidebar(records, [{"dir": "a", "label": "A"}], {})
    assert _slugs(_group(out, "A")) == ["guides/a/how-to/bug-fix"]


def test_index_without_baseline_is_labelled_overview():
    """Filename derivation would give 'Readme'. Every existing index entry says
    'Overview', so a new group must not read differently."""
    records = [_rec("guides/a", pack="a", is_index=True)]
    out = build_site.project_guide_sidebar(records, [{"dir": "a", "label": "A"}], {})
    assert _group(out, "A")["items"][0]["label"] == "Overview"


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------

def test_guide_groups_labels_and_order_applied():
    records = [
        _rec("guides/b/how-to/x", pack="b", kind="how-to"),
        _rec("guides/a/how-to/y", pack="a", kind="how-to"),
    ]
    groups = [{"dir": "b", "label": "Bee"}, {"dir": "a", "label": "Ay"}]
    out = build_site.project_guide_sidebar(records, groups, {})
    assert _labels(out["items"]) == ["Bee", "Ay"]


def test_undeclared_dir_gets_titlecased_group_appended_last():
    records = [
        _rec("guides/a/how-to/x", pack="a", kind="how-to"),
        _rec("guides/zz-new/how-to/y", pack="zz-new", kind="how-to"),
    ]
    out = build_site.project_guide_sidebar(records, [{"dir": "a", "label": "Ay"}], {})
    assert _labels(out["items"]) == ["Ay", "Zz New"]


def test_nav_ineligible_records_are_excluded():
    records = [
        _rec("guides/a/how-to/x", pack="a", kind="how-to"),
        _rec("guides/AGENTS", pack=None, nav_eligible=False),
    ]
    out = build_site.project_guide_sidebar(records, [{"dir": "a", "label": "A"}], {})
    assert "guides/AGENTS" not in _slugs(out)


# ---------------------------------------------------------------------------
# Live integration — the real tree
# ---------------------------------------------------------------------------

def test_iac_arc_orders_1_2_3():
    """The live test: real content, authored to read as a sequence."""
    import tomllib
    records = build_site.build_guide_inventory(REPO_ROOT / "guides")
    groups = tomllib.load((REPO_ROOT / "site.toml").open("rb"))["guide_groups"]
    baseline = {
        e["slug"]: e["label"]
        for e in tomllib.load((REPO_ROOT / "guide-nav-baseline.toml").open("rb"))["entry"]
    }
    out = build_site.project_guide_sidebar(records, groups, baseline)
    arc = _slugs(_group(out, "Terraform and OpenTofu"))
    assert arc[:4] == [
        "guides/iac-terraform",
        "guides/iac-terraform/explanation/infrastructure-in-the-release-loop",
        "guides/iac-terraform/explanation/deciding-before-generating",
        "guides/iac-terraform/explanation/what-the-preview-cannot-tell-you",
    ]


# ---------------------------------------------------------------------------
# Synthetic cases — fixtures only, no real tree
# ---------------------------------------------------------------------------

def test_no_two_siblings_in_a_group_share_a_label():
    """Pages AND buckets are siblings. An earlier fix compared only page
    labels, so it could not see a page colliding with a bucket of the same
    name — which is exactly what happened."""
    records = [
        _rec("guides/a", pack="a", is_index=True),
        _rec("guides/a/how-to/x", pack="a", kind="how-to"),
        _rec("guides/a/tutorials/y", pack="a", kind="tutorial"),
    ]
    out = build_site.project_guide_sidebar(records, [{"dir": "a", "label": "A"}], {})
    labels = _labels(_group(out, "A")["items"])  # pages and buckets alike
    assert len(labels) == len(set(labels)), f"sibling label collision: {labels}"


def test_slug_override_ending_in_index_is_stripped(tmp_path):
    """mirror_guides writes the override verbatim; Starlight serves .../index
    at ..., so an unstripped override points navigation at a 404."""
    root = tmp_path / "guides"
    p = root / "a" / "x.md"
    p.parent.mkdir(parents=True)
    p.write_text("---\ntitle: X\nsummary: s\npack: a\nkind: how-to\n"
                 "slug: guides/a/deep/index\n---\n", encoding="utf-8")
    rec = build_site.build_guide_inventory(root)[0]
    assert rec["slug"] == "guides/a/deep"


def test_malformed_guide_group_entry_is_skipped_not_raised():
    """A missing `dir` or `label` previously raised a bare KeyError mid-build,
    after packs had already been mirrored. discover_packs() warns and skips on
    the sibling table; this matches it."""
    records = [_rec("guides/a/how-to/x", pack="a", kind="how-to")]
    groups = [{"label": "no dir"}, {"dir": "a", "label": "Ay"}, {"dir": "b"}]
    out = build_site.project_guide_sidebar(records, groups, {})
    assert [i["label"] for i in out["items"]] == ["Ay"]
