"""Repository-context seed portability contracts.

Pack-owned half. The assertions that read this checkout's own root guidance
live in `tests/roster/test_repository_context_root_guidance.py`, because a pack
test may not climb above its owning pack.
"""

from __future__ import annotations

from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
CORE_SEEDS = PACK_ROOT / "seeds"
SEED_AGENTS = CORE_SEEDS / "AGENTS.md"
SEED_OVERVIEW = CORE_SEEDS / "docs" / "architecture" / "overview.md"
SEED_CHANGELOG = CORE_SEEDS / "docs" / "product" / "changelog.md"


def _headings(path: Path) -> list[str]:
    return [
        line.removeprefix("## ")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("## ")
    ]


def test_seed_agents_distinguishes_minimum_from_conditional_guidance() -> None:
    text = SEED_AGENTS.read_text(encoding="utf-8")
    headings = _headings(SEED_AGENTS)
    assert headings == [
        "Project overview",
        "Development workflow",
        "Build and test commands",
        "Coding conventions",
    ]
    for optional in (
        "Documentation",
        "Security considerations",
        "Scoped instructions",
        "Repository structure",
    ):
        assert f"`{optional}`" in text
    assert "trigger" in text.lower()
    assert "benefit" in text.lower()
    assert "CONTRIBUTING.md" in text
    assert "optional starting point" in text
    assert "## Source of truth" not in text


def test_seed_architecture_overview_is_responsibility_oriented_and_portable() -> None:
    seed_text = SEED_OVERVIEW.read_text(encoding="utf-8")
    for generic_shape in ("apps/", ".claude/", "<app-name>", "<package-name>"):
        assert generic_shape not in seed_text
    for placeholder in ("<area>", "<responsibility>", "<change guidance>"):
        assert placeholder in seed_text
    assert "Delete this file" in seed_text


def test_adopter_changelog_contains_no_catalogue_release() -> None:
    text = SEED_CHANGELOG.read_text(encoding="utf-8")
    assert "## [core][1.0.0]" not in text
    assert "Phase-1" not in text
    assert "## [pack-name][version]" in text
