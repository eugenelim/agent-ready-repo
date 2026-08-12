"""Construction tests for links rewritten into mirrored technical docs."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "build_site_link_rewrites", _HERE / "build-site.py"
)
assert _SPEC and _SPEC.loader
BUILD_SITE = importlib.util.module_from_spec(_SPEC)
sys.modules["build_site_link_rewrites"] = BUILD_SITE
_SPEC.loader.exec_module(BUILD_SITE)


def test_same_directory_guide_link_is_base_qualified() -> None:
    source = (
        BUILD_SITE.REPO_ROOT
        / "guides/_shared/explanation/pack-catalogue.md"
    )
    rewritten = BUILD_SITE._rewrite_guide(
        "[File safety](file-safety-contract.md#upgrades)", source
    )
    assert rewritten == (
        "[File safety](/agent-ready-repo/docs/guides/_shared/"
        "explanation/file-safety-contract/#upgrades)"
    )


def test_parent_guide_index_link_is_base_qualified() -> None:
    source = (
        BUILD_SITE.REPO_ROOT
        / "guides/_shared/explanation/pack-catalogue.md"
    )
    rewritten = BUILD_SITE._rewrite_guide("[Shared guides](../)", source)
    assert rewritten == "[Shared guides](/agent-ready-repo/docs/guides/_shared/)"


def test_cross_pack_guide_link_is_base_qualified() -> None:
    source = (
        BUILD_SITE.REPO_ROOT
        / "guides/_shared/explanation/pack-catalogue.md"
    )
    rewritten = BUILD_SITE._rewrite_guide("[Core](../../core/)", source)
    assert rewritten == "[Core](/agent-ready-repo/docs/guides/core/)"


def test_contributing_guide_link_escapes_contributing_route() -> None:
    rewritten = BUILD_SITE._rewrite_contributing(
        "[Standards](guides/_shared/reference/"
        "catalogue-authoring-standards.md)"
    )
    assert rewritten == (
        "[Standards](/agent-ready-repo/docs/guides/_shared/reference/"
        "catalogue-authoring-standards/)"
    )


def test_pack_sibling_file_links_to_repository_source() -> None:
    source = BUILD_SITE.REPO_ROOT / "packs/core/README.md"
    rewritten = BUILD_SITE._rewrite_pack_readme("[Design](DESIGN.md)", source)
    assert rewritten == (
        "[Design](https://github.com/eugenelim/agent-ready-repo/"
        "blob/main/packs/core/DESIGN.md)"
    )


def test_changelog_guide_link_escapes_changelog_route() -> None:
    rewritten = BUILD_SITE._rewrite_changelog(
        "[Vision](../guides/product-engineering/how-to/"
        "frame-a-product-vision.md)"
    )
    assert rewritten == (
        "[Vision](/agent-ready-repo/docs/guides/product-engineering/"
        "how-to/frame-a-product-vision/)"
    )


def test_frontmatter_slug_override_is_used_for_guide_links() -> None:
    source = BUILD_SITE.REPO_ROOT / "guides/atlassian/README.md"
    rewritten = BUILD_SITE._rewrite_guide(
        "[Jira](work-with-jira.md)", source
    )
    assert rewritten == (
        "[Jira](/agent-ready-repo/docs/guides/atlassian/"
        "how-to/work-with-jira/)"
    )


def test_guide_slug_normalisation_rejects_route_escapes() -> None:
    assert BUILD_SITE._normalise_guide_slug("guides/core/index") == "guides/core"
    assert BUILD_SITE._normalise_guide_slug("guides/../outside") is None
    assert BUILD_SITE._normalise_guide_slug("../outside") is None
    assert BUILD_SITE._normalise_guide_slug("packs/core") is None
    assert BUILD_SITE._normalise_guide_slug(123) is None


def test_all_projected_guide_links_resolve_to_a_canonical_route() -> None:
    guides_root = (BUILD_SITE.REPO_ROOT / "guides").resolve()
    sources = sorted(guides_root.rglob("*.md"))
    routes = {
        BUILD_SITE._guide_site_url(source.resolve(), guides_root).rstrip("/")
        for source in sources
    }
    failures = []
    for source in (*sources, BUILD_SITE.REPO_ROOT / "CONTRIBUTING.md"):
        content = source.read_text(encoding="utf-8")
        rewritten = (
            BUILD_SITE._rewrite_contributing(content)
            if source.name == "CONTRIBUTING.md"
            else BUILD_SITE._rewrite_guide(content, source.resolve())
        )
        targets = re.findall(
            r"\]\((/agent-ready-repo/docs/guides/[^)#\s]*)(?:#[^)]*)?\)",
            rewritten,
        )
        for target in targets:
            if target.rstrip("/") not in routes:
                failures.append(f"{source.relative_to(BUILD_SITE.REPO_ROOT)} -> {target}")

    assert not failures, "\n".join(failures)


if __name__ == "__main__":
    for name, function in sorted(globals().items()):
        if name.startswith("test_") and callable(function):
            function()
    print("test-build-site-link-rewrites: all cases passed.")
    sys.exit(0)
