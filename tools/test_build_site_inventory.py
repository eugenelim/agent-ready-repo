"""Tests for the guide inventory pass in tools/build-site.py.

Covers T2 (inventory derivation) and T3 (slug parity with what mirror_guides
writes) of docs/specs/guides-sidebar-generation.

The inventory is the "predictable translation" layer: every awkward fact about
the source tree becomes a declared field on a record rather than a branch
buried in projection logic.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# build-site.py uses a hyphen, so plain `import build_site` won't work.
_SCRIPT = Path(__file__).resolve().parent / "build-site.py"
_spec = importlib.util.spec_from_file_location("build_site", _SCRIPT)
build_site = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["build_site"] = build_site
_spec.loader.exec_module(build_site)  # type: ignore[union-attr]

REPO_ROOT = Path(__file__).resolve().parent.parent

LAYER1_KEYS = {
    "source_path", "pack", "kind", "order", "title", "slug",
    "is_index", "nav_eligible",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tree(tmp_path: Path, files: dict[str, str]) -> Path:
    """Materialize {relative path: content} under tmp_path/guides."""
    root = tmp_path / "guides"
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root


def _by_path(records: list[dict], rel: str) -> dict:
    return next(r for r in records if r["source_path"].as_posix().endswith(rel))


# ---------------------------------------------------------------------------
# T2 — inventory derivation
# ---------------------------------------------------------------------------

def test_record_has_all_layer1_keys(tmp_path):
    """Every key present — not every value truthy. `order` and `kind` are
    legitimately absent on most pages."""
    root = _tree(tmp_path, {"core/how-to/bug-fix.md": "# Bug fix\n"})
    records = build_site.build_guide_inventory(root)
    assert len(records) == 1
    assert set(records[0]) == LAYER1_KEYS


def test_no_frontmatter_still_yields_record(tmp_path):
    """162 of 182 real files carry no frontmatter; a frontmatter-sourced
    inventory would omit them."""
    root = _tree(tmp_path, {"core/how-to/bug-fix.md": "# Bug fix\n"})
    rec = build_site.build_guide_inventory(root)[0]
    assert rec["pack"] == "core"
    assert rec["kind"] == "how-to"
    assert rec["slug"] == "guides/core/how-to/bug-fix"
    assert rec["title"] is None
    assert rec["nav_eligible"] is True


def test_title_override(tmp_path):
    root = _tree(tmp_path, {
        "core/how-to/x.md": "---\ntitle: Custom Title\nsummary: s\npack: core\nkind: how-to\n---\n",
    })
    assert build_site.build_guide_inventory(root)[0]["title"] == "Custom Title"


def test_shared_and_reference_packs(tmp_path):
    root = _tree(tmp_path, {
        "_shared/explanation/loops.md": "# Loops\n",
        "_reference/catalogue-format.md": "# Format\n",
    })
    records = build_site.build_guide_inventory(root)
    assert _by_path(records, "_shared/explanation/loops.md")["pack"] == "_shared"
    ref = _by_path(records, "_reference/catalogue-format.md")
    assert ref["pack"] == "_reference"
    # kind-less, non-index — the record that falls through every ordering rule
    assert ref["kind"] is None
    assert ref["is_index"] is False


def test_non_md_excluded(tmp_path):
    root = _tree(tmp_path, {"core/how-to/x.md": "# X\n", "core/diagram.png": "notpng"})
    records = build_site.build_guide_inventory(root)
    assert len(records) == 1
    assert records[0]["source_path"].name == "x.md"


def test_agents_md_not_nav_eligible(tmp_path):
    """guides/AGENTS.md is maintainer context. It is still mirrored, so it stays
    reachable by URL — it just never reaches reader navigation."""
    root = _tree(tmp_path, {"AGENTS.md": "# Agents\n", "core/how-to/x.md": "# X\n"})
    records = build_site.build_guide_inventory(root)
    assert _by_path(records, "AGENTS.md")["nav_eligible"] is False
    assert _by_path(records, "core/how-to/x.md")["nav_eligible"] is True


def test_is_index_for_readme_at_any_depth(tmp_path):
    root = _tree(tmp_path, {
        "README.md": "# Guides\n",
        "core/README.md": "# Core\n",
        "_shared/explanation/README.md": "# Explanation\n",
        "core/how-to/x.md": "# X\n",
    })
    records = build_site.build_guide_inventory(root)
    assert _by_path(records, "guides/README.md")["is_index"] is True
    assert _by_path(records, "core/README.md")["is_index"] is True
    assert _by_path(records, "_shared/explanation/README.md")["is_index"] is True
    assert _by_path(records, "core/how-to/x.md")["is_index"] is False


def test_root_readme_has_no_pack(tmp_path):
    """It has no pack path segment, so `pack` resolves to the tree root — not
    the literal string 'README.md'."""
    root = _tree(tmp_path, {"README.md": "# Guides\n"})
    assert build_site.build_guide_inventory(root)[0]["pack"] is None


def test_malformed_frontmatter_falls_back(tmp_path):
    root = _tree(tmp_path, {
        "core/how-to/x.md": "---\ntitle: [unclosed\n  bad: :\n---\n# X\n",
    })
    rec = build_site.build_guide_inventory(root)[0]  # must not raise
    assert rec["pack"] == "core"
    assert rec["slug"] == "guides/core/how-to/x"


def test_non_integer_order_coerced_to_absent(tmp_path):
    """The schema requires an integer, but validate_guides.py is not run over
    guides/ in CI — so the type is not an enforced boundary. A str/int mix
    would raise inside the projection sort."""
    root = _tree(tmp_path, {
        "core/how-to/a.md": '---\ntitle: A\nsummary: s\npack: core\nkind: how-to\norder: "2"\n---\n',
        "core/how-to/b.md": "---\ntitle: B\nsummary: s\npack: core\nkind: how-to\norder: 1\n---\n",
    })
    records = build_site.build_guide_inventory(root)
    assert _by_path(records, "a.md")["order"] is None
    assert _by_path(records, "b.md")["order"] == 1


def test_tutorials_dir_normalizes_to_kind_tutorial(tmp_path):
    """Directory is `tutorials/`; the schema enum is `tutorial`. Without
    normalization the first page to gain frontmatter splits one pack into two
    buckets."""
    root = _tree(tmp_path, {"core/tutorials/start.md": "# Start\n"})
    assert build_site.build_guide_inventory(root)[0]["kind"] == "tutorial"


def test_frontmatter_kind_wins_over_directory(tmp_path):
    """guide-source-model AC3: frontmatter declares kind. The directory is only
    a fallback for pages that carry none."""
    root = _tree(tmp_path, {
        "core/tutorials/x.md": "---\ntitle: X\nsummary: s\npack: core\nkind: reference\n---\n",
    })
    assert build_site.build_guide_inventory(root)[0]["kind"] == "reference"


# ---------------------------------------------------------------------------
# T3 — slug parity with what mirror_guides() writes
# ---------------------------------------------------------------------------

def test_readme_resolves_to_parent(tmp_path):
    """mirror_guides() renames README.md -> index.md, so its canonical_slug is
    `guides/core/index`. Starlight strips the trailing /index off the written
    path — `guides/core` is the slug navigation needs."""
    root = _tree(tmp_path, {"core/README.md": "# Core\n", "README.md": "# Guides\n"})
    records = build_site.build_guide_inventory(root)
    assert _by_path(records, "core/README.md")["slug"] == "guides/core"
    assert _by_path(records, "guides/README.md")["slug"] == "guides"


def test_slug_frontmatter_override(tmp_path):
    root = _tree(tmp_path, {
        "atlassian/work-with-jira.md":
            "---\ntitle: W\nsummary: s\npack: atlassian\nkind: how-to\n"
            "slug: guides/atlassian/how-to/work-with-jira\n---\n",
    })
    rec = build_site.build_guide_inventory(root)[0]
    assert rec["slug"] == "guides/atlassian/how-to/work-with-jira"


def test_slug_matches_what_mirror_guides_actually_writes(tmp_path):
    """The parity guard: navigation must point where the page lands.

    Drives the real ``mirror_guides`` and reads the files it wrote, rather than
    re-deriving its rules in the test body — a re-derivation would keep agreeing
    with itself while both sides drifted away from the site.
    """
    guides_root = REPO_ROOT / "guides"
    site_docs = tmp_path / "docs"
    build_site.mirror_guides(guides_root, site_docs)

    written = set()
    for p in site_docs.rglob("*.md"):
        slug = p.relative_to(site_docs).with_suffix("").as_posix()
        if slug.endswith("/index"):
            slug = slug[: -len("/index")]
        written.add(slug)

    records = build_site.build_guide_inventory(guides_root)
    assert len(records) > 100, "sanity: the real tree should be large"
    missing = sorted({r["slug"] for r in records} - written)
    assert not missing, f"inventory slugs with no page written for them: {missing}"


def test_inventory_accepts_injected_enumerator(tmp_path):
    """The determinism seam: T7 shuffles this input. Without an injectable
    enumerator the test would re-glob and assert nothing."""
    root = _tree(tmp_path, {"core/how-to/a.md": "# A\n", "core/how-to/b.md": "# B\n"})
    paths = sorted(root.rglob("*.md"))
    forward = build_site.build_guide_inventory(root, enumerator=lambda _: paths)
    reverse = build_site.build_guide_inventory(root, enumerator=lambda _: list(reversed(paths)))
    assert [r["slug"] for r in forward] == [r["slug"] for r in reverse]


# ---------------------------------------------------------------------------
# Degradation — adopter-authored frontmatter must never crash the build
# ---------------------------------------------------------------------------

def test_non_string_slug_falls_back_to_derived(tmp_path):
    """`slug: 123` previously raised AttributeError naming no file."""
    root = _tree(tmp_path, {
        "core/how-to/x.md": "---\ntitle: X\nsummary: s\npack: core\nkind: how-to\nslug: 123\n---\n",
    })
    assert build_site.build_guide_inventory(root)[0]["slug"] == "guides/core/how-to/x"


def test_non_string_title_coerced_to_absent(tmp_path):
    """`title: [a, b]` survived the inventory and raised in the bucket sort, or
    landed in sidebar-config.json as a non-string label."""
    root = _tree(tmp_path, {
        "core/how-to/x.md": "---\ntitle: [a, b]\nsummary: s\npack: core\nkind: how-to\n---\n",
    })
    assert build_site.build_guide_inventory(root)[0]["title"] is None


def test_section_index_is_not_nav_eligible(tmp_path):
    """The rule is depth-based, not kind-name-based: any README more than one
    directory below guides/ is a section-authoring template."""
    root = _tree(tmp_path, {
        "core/README.md": "# Core\n",
        "core/how-to/README.md": "# Writing a how-to\n",
        "core/notakind/README.md": "# Deep\n",
    })
    records = build_site.build_guide_inventory(root)
    assert _by_path(records, "core/README.md")["nav_eligible"] is True
    assert _by_path(records, "core/how-to/README.md")["nav_eligible"] is False
    assert _by_path(records, "core/notakind/README.md")["nav_eligible"] is False
