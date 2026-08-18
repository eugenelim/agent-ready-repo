"""Tests for guide-routing additions to tools/build-site.py (7 tests).

Covers: frontmatter parsing, guide-metadata stripping, slug-override routing,
alias redirect-stub generation, docs/guides/ exclusion, and generation's
independence from the marketing design-token file.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

# build-site.py uses a hyphen, so plain `import build_site` won't work.
_SCRIPT = Path(__file__).resolve().parent / "build-site.py"
_spec = importlib.util.spec_from_file_location("build_site", _SCRIPT)
build_site = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["build_site"] = build_site
_spec.loader.exec_module(build_site)  # type: ignore[union-attr]

SITE_BASE = "/agent-ready-repo/docs"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_guide(tmp_path: Path, rel: str, content: str) -> tuple[Path, Path]:
    """Create a guide source file and return (guide_src, guides_root)."""
    guides_root = tmp_path / "guides"
    src = guides_root / rel
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(content, encoding="utf-8")
    return src, guides_root


# ---------------------------------------------------------------------------
# 1 — slug override changes the output path
# ---------------------------------------------------------------------------

def test_slug_override_changes_output_path(tmp_path):
    src, guides_root = _make_guide(tmp_path, "product-documentation/getting-started.md", """\
---
title: "Getting Started"
summary: "Learn the basics."
pack: product-documentation
kind: tutorial
slug: guides/product-documentation/how-to/getting-started
---

Content here.
""")
    site_docs = tmp_path / "docs"
    site_docs.mkdir()

    # Default: site_docs/guides/product-documentation/getting-started.md
    # Slug-override: site_docs/guides/product-documentation/how-to/getting-started.md
    build_site.mirror_guides(guides_root, site_docs, dry_run=False)

    overridden = site_docs / "guides" / "product-documentation" / "how-to" / "getting-started.md"
    default = site_docs / "guides" / "product-documentation" / "getting-started.md"

    assert overridden.exists(), f"Expected file at overridden path {overridden}"
    assert not default.exists(), "Default path should not exist when slug is overridden"


# ---------------------------------------------------------------------------
# 2 — alias generates a meta-refresh redirect stub
# ---------------------------------------------------------------------------

def test_alias_generates_redirect_stub(tmp_path):
    src, guides_root = _make_guide(tmp_path, "product-documentation/new-guide.md", """\
---
title: "New Guide"
summary: "Useful."
pack: product-documentation
kind: how-to
slug: guides/product-documentation/new-guide
aliases:
  - guides/product-documentation/old-guide
---

Content.
""")
    site_docs = tmp_path / "docs"
    site_docs.mkdir()

    build_site.mirror_guides(guides_root, site_docs, dry_run=False)

    stub = site_docs / "guides" / "product-documentation" / "old-guide.md"
    assert stub.exists(), f"Expected redirect stub at {stub}"
    content = stub.read_text(encoding="utf-8")
    assert "meta http-equiv" in content.lower() or "refresh" in content.lower(), \
        "Redirect stub should contain meta-refresh"
    assert "new-guide" in content, "Redirect stub should point to canonical slug"


# ---------------------------------------------------------------------------
# 3 — guide-metadata fields are stripped from output
# ---------------------------------------------------------------------------

def test_guide_metadata_stripped_from_output(tmp_path):
    # Include slug: and aliases: so the test pins that they are also stripped.
    # slug: guides/core/my-guide keeps the output path identical to the default.
    src, guides_root = _make_guide(tmp_path, "core/my-guide.md", """\
---
title: "My Guide"
summary: "Summary text."
pack: core
kind: explanation
journey: core-first-run
order: 3
status: stable
slug: guides/core/my-guide
aliases:
  - guides/core/my-guide-old
---

Body content.
""")
    site_docs = tmp_path / "docs"
    site_docs.mkdir()

    build_site.mirror_guides(guides_root, site_docs, dry_run=False)

    out = site_docs / "guides" / "core" / "my-guide.md"
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    # All guide-specific fields must be absent from the written file
    stripped_fields = (
        "pack:", "kind:", "summary:", "journey:", "order:", "status:", "slug:", "aliases:",
    )
    for field in stripped_fields:
        assert field not in content, (
            f"Field '{field}' should be stripped from output, but was found"
        )
    # title must be preserved
    assert "title:" in content


# ---------------------------------------------------------------------------
# 4 — file without frontmatter: title injected, content unchanged
# ---------------------------------------------------------------------------

def test_no_frontmatter_passthrough_unchanged(tmp_path):
    src, guides_root = _make_guide(tmp_path, "core/legacy.md", """\
# Legacy Guide

Some existing content without frontmatter.
""")
    site_docs = tmp_path / "docs"
    site_docs.mkdir()

    build_site.mirror_guides(guides_root, site_docs, dry_run=False)

    out = site_docs / "guides" / "core" / "legacy.md"
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    # Frontmatter should have been injected
    assert content.startswith("---")
    assert "title:" in content
    # Original body content must be present
    assert "Some existing content without frontmatter." in content


# ---------------------------------------------------------------------------
# 5 — docs/guides/ is not mirrored (integration test against real repo)
# ---------------------------------------------------------------------------

def test_docs_guides_not_mirrored_from_real_guides_root(tmp_path):
    """mirror_guides(real guides/, …) must not include any docs/guides/ content."""
    guides_root = build_site.REPO_ROOT / "guides"
    docs_guides = build_site.REPO_ROOT / "docs" / "guides"

    docs_guide_files = list(docs_guides.glob("*.md"))
    assert docs_guide_files, (
        "Expected at least one .md in docs/guides/ for this assertion to be meaningful"
    )

    site_docs = tmp_path / "site"
    site_docs.mkdir()
    build_site.mirror_guides(guides_root, site_docs, dry_run=False)

    for doc in docs_guide_files:
        assert not (site_docs / "guides" / doc.name).exists(), (
            f"{doc.name} from docs/guides/ must not appear in the mirrored docs site"
        )
    # Sanity: some actual guides/ content was mirrored
    assert any(site_docs.rglob("*.md")), "Expected mirrored guides to produce at least one file"


# --------------------------------------------------------------------------
# spec/docs-site-build-contract-hardening AC1/AC2 — no marketing-token dependency
# --------------------------------------------------------------------------
#
# These two run the generator as a SUBPROCESS inside a temp tree rather than
# calling `main()` in-process. `REPO_ROOT` is module-level and the token copy lived
# inline in `main()`, so an in-process call would read the real
# `web/src/styles/tokens.css` and write into the real
# `docs-site/src/content/docs/` — no isolation, and a dirtied worktree. Copying
# `build-site.py` plus `site.toml` into the fixture makes `REPO_ROOT` the fixture.
#
# Before this change the generator exited 1 with
# `error  web/src/styles/tokens.css missing — docs-site CSS depends on it`. That
# claim was false: `docs-site/src/styles/starlight.css` stopped importing the copied
# file, so the copy was vestigial and the hard failure was a false dependency.


def _generator_fixture(tmp_path):
    """A minimal tree where the generator can run with REPO_ROOT == tmp_path."""
    (tmp_path / "tools").mkdir()
    shutil.copy2(_SCRIPT, tmp_path / "tools" / "build-site.py")
    real_site_toml = _SCRIPT.parent.parent / "site.toml"
    if real_site_toml.is_file():
        shutil.copy2(real_site_toml, tmp_path / "site.toml")
    # The trees the generator reads and writes. Empty is fine: this asserts the
    # token contract, not mirroring behaviour, which the tests above cover.
    for d in ("guides", "packs", "docs-site/src/content/docs", "docs-site/src/styles",
              "web/src/styles"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    return tmp_path


def _run_generator(root):
    return subprocess.run(
        [sys.executable, str(root / "tools" / "build-site.py")],
        cwd=root, capture_output=True, text=True,
    )


def test_generation_succeeds_without_the_marketing_token_file(tmp_path):
    """AC2: no marketing token file present, and generation still succeeds.

    This is the criterion's whole point — the previous contract exited 1 here.
    """
    root = _generator_fixture(tmp_path)
    tokens = root / "web" / "src" / "styles" / "tokens.css"
    assert not tokens.exists(), "fixture must not provide the marketing token file"
    r = _run_generator(root)
    assert r.returncode == 0, (
        "generation must not depend on the marketing token file:\n"
        + r.stdout + r.stderr
    )
    assert "tokens.css missing" not in (r.stdout + r.stderr), r.stdout + r.stderr


def test_generation_writes_no_docs_token_copy(tmp_path):
    """AC1/AC2: even WITH a marketing token file present, no copy is emitted.

    Asserted with the source present, because a test that only removes the source
    cannot distinguish "the copy was deleted" from "the copy was skipped for lack of
    input" — the mutation that reintroduces the copy would then still pass.
    """
    root = _generator_fixture(tmp_path)
    src = root / "web" / "src" / "styles" / "tokens.css"
    src.write_text(":root { --brand: #f59e0b; }\n", encoding="utf-8")
    r = _run_generator(root)
    assert r.returncode == 0, r.stdout + r.stderr
    copied = root / "docs-site" / "src" / "styles" / "tokens.css"
    assert not copied.exists(), (
        "generation must not copy marketing tokens into docs-site: the docs palette "
        "is self-contained per ADR-0085"
    )
    assert "copying design tokens" not in r.stdout, r.stdout
