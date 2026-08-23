"""Repository-context scaffold and seed portability contracts."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
ROOT_AGENTS = REPO_ROOT / "AGENTS.md"
CORE_SEEDS = REPO_ROOT / "packs" / "core" / "seeds"
SEED_AGENTS = CORE_SEEDS / "AGENTS.md"
ROOT_OVERVIEW = REPO_ROOT / "docs" / "architecture" / "overview.md"
SEED_OVERVIEW = CORE_SEEDS / "docs" / "architecture" / "overview.md"
SEED_CHANGELOG = CORE_SEEDS / "docs" / "product" / "changelog.md"
ORG_STACK_GUIDE = (
    REPO_ROOT / "guides" / "_shared" / "how-to" / "build-an-org-stack-pack.md"
)


def _headings(path: Path) -> list[str]:
    return [
        line.removeprefix("## ")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("## ")
    ]


def test_root_agents_uses_conventional_repository_guidance_headings() -> None:
    headings = _headings(ROOT_AGENTS)
    assert headings == [
        "Project overview",
        "Documentation",
        "Development workflow",
        "Build and test commands",
        "Coding conventions",
        "Security considerations",
        "Scoped instructions",
    ]
    for legacy in (
        "What this repo is",
        "Source of truth",
        "How we work",
        "Commands you'll need",
        "Check before acting",
        "When this file is wrong",
    ):
        assert legacy not in headings


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


def test_architecture_overviews_are_responsibility_oriented_and_portable() -> None:
    root_text = ROOT_OVERVIEW.read_text(encoding="utf-8")
    assert "packs/<pack>/seeds/" in root_text
    assert "Edit seeds under `packs/<pack>/.apm/" not in root_text
    assert "most recent accepted RFCs" not in root_text

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


def test_org_stack_guide_contributes_deltas_without_a_second_root_scaffold() -> None:
    text = ORG_STACK_GUIDE.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    assert "delta-only" in text
    assert "scoped `AGENTS.md`" in text
    assert "raw concatenation" in normalized
    assert "AGENTS.upstream.md" in text
