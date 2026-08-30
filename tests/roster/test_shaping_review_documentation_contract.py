"""Repository-level contract for shaping-review documentation and seed sync."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_CONVENTIONS_SEED = REPO_ROOT / "packs/core/seeds/docs/CONVENTIONS.md"
ROOT_CONVENTIONS = REPO_ROOT / "docs/CONVENTIONS.md"

SHAPING_REVIEW_DOCUMENTS = (
    REPO_ROOT / "guides/_shared/explanation/the-three-loops.md",
    REPO_ROOT / "guides/core/explanation/core-pack.md",
    REPO_ROOT / "guides/core/how-to/plan-and-execute-non-trivial-work.md",
    REPO_ROOT / "guides/core/how-to/review-someone-elses-pr.md",
    REPO_ROOT / "packs/core/DESIGN.md",
    REPO_ROOT / "packs/core/docs/index.md",
    REPO_ROOT / "packs/core/JOURNEY.md",
    CORE_CONVENTIONS_SEED,
)


def _paragraphs(path: Path) -> tuple[str, ...]:
    """Return whitespace-insensitive paragraphs for local prose checks."""
    return tuple(
        " ".join(paragraph.lower().split())
        for paragraph in re.split(r"\n\s*\n", path.read_text(encoding="utf-8"))
    )


def test_closed_document_set_distinguishes_shaping_from_code_review_lenses() -> None:
    """Keep the accepted eight-document set explicit and independently useful."""
    for path in SHAPING_REVIEW_DOCUMENTS:
        assert any(
            all(term in paragraph for term in ("shaping", "adversarial", "security", "quality"))
            for paragraph in _paragraphs(path)
        ), path


def test_core_index_keeps_shaping_reviewer_outside_code_review_subagent_list() -> None:
    """The shaping reviewer remains distinct from the three code-review lenses."""
    index = REPO_ROOT / "packs/core/docs/index.md"
    subagents_line = next(
        line for line in index.read_text(encoding="utf-8").splitlines()
        if line.startswith("**Subagents:**")
    )
    assert "shaping-reviewer" not in subagents_line


def test_core_conventions_projection_matches_its_seed() -> None:
    """Require scaffold sync after a portable Core conventions change."""
    assert ROOT_CONVENTIONS.read_text(encoding="utf-8") == CORE_CONVENTIONS_SEED.read_text(
        encoding="utf-8"
    )
