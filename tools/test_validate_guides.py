"""Tests for tools/validate_guides.py — TDD suite (17 tests)."""
import sys
from pathlib import Path

import pytest

# Import validate_guides from the same directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_guides  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.resolve()
PACKS_ROOT = REPO_ROOT / "packs"
SCHEMA_PATH = REPO_ROOT / "contracts" / "guide.schema.json"


def _write_guide(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _run(paths: list[Path], packs_root: Path = PACKS_ROOT) -> tuple[int, list[str], list[str]]:
    """Run validate_guides.validate_paths() and return (exit_code, errors, warnings)."""
    return validate_guides.validate_paths(
        [str(p) for p in paths],
        packs_root=str(packs_root),
        schema_path=str(SCHEMA_PATH),
    )


# ---------------------------------------------------------------------------
# 1 — valid required fields
# ---------------------------------------------------------------------------

def test_valid_required_fields(tmp_path):
    guide = _write_guide(tmp_path, "guide.md", """\
---
title: "A Guide"
summary: "Does something useful."
pack: product-documentation
kind: how-to
---

Body text.
""")
    code, errors, warnings = _run([guide])
    assert code == 0, errors
    assert errors == []


# ---------------------------------------------------------------------------
# 2-5 — missing required fields
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field,replacement", [
    ("title", ""),
    ("summary", ""),
    ("pack", ""),
    ("kind", ""),
])
def test_missing_required_field(tmp_path, field, replacement):
    fm_lines = {
        "title": 'title: "A Guide"',
        "summary": 'summary: "Useful."',
        "pack": "pack: product-documentation",
        "kind": "kind: how-to",
    }
    lines = {k: v for k, v in fm_lines.items() if k != field}
    content = "---\n" + "\n".join(lines.values()) + "\n---\n\nBody.\n"
    guide = _write_guide(tmp_path, "guide.md", content)
    code, errors, warnings = _run([guide])
    assert code == 1
    assert any(field in e for e in errors), f"Expected '{field}' in errors: {errors}"


# ---------------------------------------------------------------------------
# 6 — invalid kind value
# ---------------------------------------------------------------------------

def test_invalid_kind_value(tmp_path):
    guide = _write_guide(tmp_path, "guide.md", """\
---
title: "A Guide"
summary: "Useful."
pack: product-documentation
kind: faq
---
""")
    code, errors, warnings = _run([guide])
    assert code == 1
    assert any("kind" in e for e in errors), errors


# ---------------------------------------------------------------------------
# 7 — unknown pack ID
# ---------------------------------------------------------------------------

def test_unknown_pack_id(tmp_path, tmp_path_factory):
    packs_root = tmp_path_factory.mktemp("packs")
    (packs_root / "real-pack").mkdir()
    (packs_root / "real-pack" / "pack.toml").write_text("[pack]\nname = 'real-pack'\n")
    guide = _write_guide(tmp_path, "guide.md", """\
---
title: "A Guide"
summary: "Useful."
pack: nonexistent-pack
kind: how-to
---
""")
    code, errors, warnings = _run([guide], packs_root=packs_root)
    assert code == 1
    assert any("pack" in e for e in errors), errors


# ---------------------------------------------------------------------------
# 8 — _shared pack ID is approved
# ---------------------------------------------------------------------------

def test_shared_pack_id(tmp_path, tmp_path_factory):
    packs_root = tmp_path_factory.mktemp("packs_shared")
    guide = _write_guide(tmp_path, "guide.md", """\
---
title: "A Shared Guide"
summary: "Cross-cutting content."
pack: _shared
kind: explanation
---
""")
    code, errors, warnings = _run([guide], packs_root=packs_root)
    assert code == 0, errors


# ---------------------------------------------------------------------------
# 9 — duplicate slug within pack
# ---------------------------------------------------------------------------

def test_duplicate_slug_within_pack(tmp_path):
    guide_a = _write_guide(tmp_path, "alpha/getting-started.md", """\
---
title: "Getting Started"
summary: "First guide."
pack: product-documentation
kind: tutorial
slug: guides/product-documentation/getting-started
---
""")
    guide_b = _write_guide(tmp_path, "beta/getting-started.md", """\
---
title: "Getting Started"
summary: "Second guide."
pack: product-documentation
kind: tutorial
slug: guides/product-documentation/getting-started
---
""")
    code, errors, warnings = _run([guide_a, guide_b])
    assert code == 1
    assert any("duplicate" in e.lower() for e in errors), errors


# ---------------------------------------------------------------------------
# 10 — alias collides with a canonical slug
# ---------------------------------------------------------------------------

def test_aliases_collision_with_canonical(tmp_path):
    canonical = _write_guide(tmp_path, "new.md", """\
---
title: "New Guide"
summary: "Canonical."
pack: product-documentation
kind: how-to
slug: guides/product-documentation/new-guide
---
""")
    collider = _write_guide(tmp_path, "old.md", """\
---
title: "Old Guide"
summary: "Has alias that matches canonical."
pack: product-documentation
kind: how-to
slug: guides/product-documentation/old-guide
aliases:
  - guides/product-documentation/new-guide
---
""")
    # Both orderings must detect the collision — the check must be order-independent.
    for ordered in ([canonical, collider], [collider, canonical]):
        code, errors, warnings = _run(ordered)
        assert code == 1, f"Expected error regardless of scan order; errors={errors}"
        assert any(
            "alias" in e.lower() or "collision" in e.lower() or "duplicate" in e.lower()
            for e in errors
        ), f"Expected collision error; got errors={errors}"


# ---------------------------------------------------------------------------
# 11 — duplicate alias across two files
# ---------------------------------------------------------------------------

def test_duplicate_alias(tmp_path):
    guide_a = _write_guide(tmp_path, "a.md", """\
---
title: "Guide A"
summary: "First."
pack: product-documentation
kind: how-to
slug: guides/product-documentation/guide-a
aliases:
  - guides/product-documentation/shared-alias
---
""")
    guide_b = _write_guide(tmp_path, "b.md", """\
---
title: "Guide B"
summary: "Second."
pack: product-documentation
kind: how-to
slug: guides/product-documentation/guide-b
aliases:
  - guides/product-documentation/shared-alias
---
""")
    code, errors, warnings = _run([guide_a, guide_b])
    assert code == 1
    assert any("alias" in e.lower() or "duplicate" in e.lower() for e in errors), errors


# ---------------------------------------------------------------------------
# 12 — no frontmatter: warns but does not fail
# ---------------------------------------------------------------------------

def test_no_frontmatter(tmp_path):
    guide = _write_guide(tmp_path, "guide.md", """\
# A Guide Without Frontmatter

Some content.
""")
    code, errors, warnings = _run([guide])
    assert code == 0, errors
    assert errors == []
    assert any("frontmatter" in w.lower() or "migration" in w.lower() for w in warnings), warnings


# ---------------------------------------------------------------------------
# 13 — docs/guides/ not scanned even if passed implicitly via parent
# ---------------------------------------------------------------------------

def test_docs_guides_not_scanned(tmp_path):
    docs_guides = tmp_path / "docs" / "guides"
    docs_guides.mkdir(parents=True)
    bad_guide = docs_guides / "internal.md"
    bad_guide.write_text("---\ntitle: x\nsummary: y\npack: INVALID\nkind: how-to\n---\n")
    # Pass the docs/guides path explicitly — should not validate it
    code, errors, warnings = validate_guides.validate_paths(
        [str(bad_guide)],
        packs_root=str(PACKS_ROOT),
        schema_path=str(SCHEMA_PATH),
        exclude_paths=[str(docs_guides)],
    )
    assert code == 0, f"docs/guides/ should be excluded, but got errors: {errors}"


# ---------------------------------------------------------------------------
# 14 — unknown frontmatter field fails (strict schema)
# ---------------------------------------------------------------------------

def test_unknown_field(tmp_path):
    guide = _write_guide(tmp_path, "guide.md", """\
---
title: "A Guide"
summary: "Useful."
pack: product-documentation
kind: how-to
unknown_field: "should not be here"
---
""")
    code, errors, warnings = _run([guide])
    assert code == 1
    assert any(
        "additional" in e.lower() or "unknown" in e.lower() or "unknown_field" in e
        for e in errors
    ), errors


# ---------------------------------------------------------------------------
# 15 — valid optional fields pass
# ---------------------------------------------------------------------------

def test_valid_optional_fields(tmp_path):
    guide = _write_guide(tmp_path, "guide.md", """\
---
title: "A Guide"
summary: "Useful."
pack: product-documentation
kind: tutorial
slug: guides/product-documentation/a-guide
journey: product-documentation-first-run
order: 1
aliases:
  - guides/product-documentation/old-name
status: stable
---

Body text.
""")
    code, errors, warnings = _run([guide])
    assert code == 0, errors


# ---------------------------------------------------------------------------
# 16 — dangling alias warns but does not fail
# ---------------------------------------------------------------------------

def test_dangling_alias(tmp_path):
    guide = _write_guide(tmp_path, "guide.md", """\
---
title: "A Guide"
summary: "Useful."
pack: product-documentation
kind: how-to
aliases:
  - guides/product-documentation/nonexistent-canonical
---
""")
    # The alias points to a slug that doesn't exist in the scanned set.
    code, errors, warnings = _run([guide])
    assert code == 0, errors
    assert any("alias" in w.lower() or "dangling" in w.lower() for w in warnings), warnings


# ---------------------------------------------------------------------------
# 17 — redirect loop: slug equals own alias
# ---------------------------------------------------------------------------

def test_redirect_loop(tmp_path):
    guide = _write_guide(tmp_path, "guide.md", """\
---
title: "A Guide"
summary: "Useful."
pack: product-documentation
kind: how-to
slug: guides/product-documentation/my-guide
aliases:
  - guides/product-documentation/my-guide
---
""")
    code, errors, warnings = _run([guide])
    assert code == 1
    assert any(
        "loop" in e.lower() or "alias" in e.lower() or "redirect" in e.lower()
        for e in errors
    ), errors


# ---------------------------------------------------------------------------
# 18 — _reference pack ID: warns but does not fail (AC9)
# ---------------------------------------------------------------------------

def test_reference_pack_id_warns_not_fails(tmp_path, tmp_path_factory):
    packs_root = tmp_path_factory.mktemp("packs_ref")
    guide = _write_guide(tmp_path, "guide.md", """\
---
title: "A Reference Guide"
summary: "Useful."
pack: _reference
kind: explanation
---
""")
    code, errors, warnings = _run([guide], packs_root=packs_root)
    assert code == 0, f"Expected exit 0 for _reference pack, got errors: {errors}"
    assert errors == []
    assert any("_reference" in w or "undesignated" in w for w in warnings), (
        f"Expected a warning about _reference pack, got: {warnings}"
    )
