"""Repository-roster checks for this checkout's own repository-context anchoring.

The seed half of these contracts is pack-owned and lives in
`packs/core/tests/pack/test_repository_context_seed.py`. The assertions here
read this repository's root guidance and its adopter-facing how-to, which a
pack test may not reach.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT_AGENTS = REPO_ROOT / "AGENTS.md"
ROOT_OVERVIEW = REPO_ROOT / "docs" / "architecture" / "overview.md"
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


def test_root_architecture_overview_is_responsibility_oriented() -> None:
    root_text = ROOT_OVERVIEW.read_text(encoding="utf-8")
    assert "packs/<pack>/seeds/" in root_text
    assert "Edit seeds under `packs/<pack>/.apm/" not in root_text
    assert "most recent accepted RFCs" not in root_text


def test_org_stack_guide_contributes_deltas_without_a_second_root_scaffold() -> None:
    text = ORG_STACK_GUIDE.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    assert "delta-only" in text
    assert "scoped `AGENTS.md`" in text
    assert "raw concatenation" in normalized
    assert "AGENTS.upstream.md" in text
