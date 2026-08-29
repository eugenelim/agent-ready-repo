"""Source contract for outcome-led catalogue navigation.

The marketing homepage and catalogue import one outcome map. Public Markdown
entry points remain authored for their medium, so this test keeps their labels
aligned without requiring generated prose.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
NAVIGATION_SOURCE = REPO_ROOT / "web/src/lib/catalogue-navigation.ts"
MARKETING_SURFACES = (
    REPO_ROOT / "web/src/components/marketing/PackCatalogue.astro",
    REPO_ROOT / "web/src/pages/catalogue/index.astro",
)
MARKDOWN_SURFACES = (
    REPO_ROOT / "guides/README.md",
    REPO_ROOT / "docs-site/src/content/docs/index.mdx",
)
EXCLUDED_PACKS = {"user-guide-diataxis"}
CATALOGUE_IMPORT = re.compile(
    r"^import\s+\{\s*(?P<bindings>[^}]+?)\s*\}\s+from\s+"
    r"['\"](?P<module>(?:\.\./)+lib/catalogue-navigation(?:\.ts)?)['\"]\s*;?\s*$",
    flags=re.MULTILINE,
)
# This detects only direct `const|let|var outcomes =` declarations; aliased or
# destructured bindings and object-literal `outcomes:` values remain outside regex coverage.
LOCAL_OUTCOMES_DECLARATION = re.compile(
    r"^\s*(?:const|let|var)\s+outcomes\s*=", flags=re.MULTILINE
)


def _navigation_source() -> str:
    return NAVIGATION_SOURCE.read_text(encoding="utf-8")


def _pack_memberships(source: str) -> set[str]:
    blocks = re.findall(r"packs:\s*\[(.*?)\]", source, flags=re.DOTALL)
    return {
        pack
        for block in blocks
        for pack in re.findall(r"['\"]([a-z][a-z0-9-]*)['\"]", block)
    }


def _outcome_titles(source: str) -> set[str]:
    return set(re.findall(r"^\s{4}title: '([^']+)'", source, flags=re.MULTILINE))


def test_all_active_packs_have_an_outcome() -> None:
    active = {
        manifest.parent.name
        for manifest in (REPO_ROOT / "packs").glob("*/pack.toml")
        if not manifest.parent.name.startswith("_")
    } - EXCLUDED_PACKS
    assert _pack_memberships(_navigation_source()) == active


def test_marketing_surfaces_import_the_canonical_map() -> None:
    for surface in MARKETING_SURFACES:
        content = surface.read_text(encoding="utf-8")
        import_match = CATALOGUE_IMPORT.search(content)
        assert import_match is not None, f"{surface}: imports catalogue-navigation"
        bindings = {
            binding.strip()
            for binding in import_match.group("bindings").split(",")
        }
        assert "catalogueOutcomes" in bindings, f"{surface}: imports catalogueOutcomes"
        imported_module = surface.parent / import_match.group("module")
        assert imported_module.with_suffix(".ts").resolve() == NAVIGATION_SOURCE.resolve(), (
            f"{surface}: catalogueOutcomes import resolves to canonical navigation source"
        )
        assert not LOCAL_OUTCOMES_DECLARATION.search(content), (
            f"{surface}: must not declare a local outcomes map"
        )


def test_markdown_entry_points_keep_canonical_outcome_labels() -> None:
    titles = _outcome_titles(_navigation_source())
    assert len(titles) == 7
    for surface in MARKDOWN_SURFACES:
        content = surface.read_text(encoding="utf-8")
        missing = sorted(title for title in titles if title not in content)
        assert not missing, f"{surface.relative_to(REPO_ROOT)}: {missing}"


def test_role_routes_resolve_to_outcomes() -> None:
    source = _navigation_source()
    outcome_ids = set(re.findall(r"^\s{4}id: '([^']+)'", source, flags=re.MULTILINE))
    role_ids = set(re.findall(r"outcomeId: '([^']+)'", source))
    assert role_ids
    assert role_ids <= outcome_ids


if __name__ == "__main__":
    for name, function in sorted(globals().items()):
        if name.startswith("test_") and callable(function):
            function()
    print("test-catalogue-navigation: all cases passed.")
    sys.exit(0)
