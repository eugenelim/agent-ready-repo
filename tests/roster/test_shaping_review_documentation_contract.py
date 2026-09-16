"""Repository-level contract for shaping-review documentation and seed sync."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_DOCS_MAP_SEED = REPO_ROOT / "packs/core/seeds/docs/README.md"

# Seven documents, not eight. The retired conventions document was the eighth;
# the review-lens distinction it carried moved into core-pack.md § Why the loop,
# which is already in this set, so the entry drops rather than being replaced.
SHAPING_REVIEW_DOCUMENTS = (
    REPO_ROOT / "guides/_shared/explanation/the-three-loops.md",
    REPO_ROOT / "guides/core/explanation/core-pack.md",
    REPO_ROOT / "guides/core/how-to/plan-and-execute-non-trivial-work.md",
    REPO_ROOT / "guides/core/how-to/review-someone-elses-pr.md",
    REPO_ROOT / "packs/core/DESIGN.md",
    REPO_ROOT / "packs/core/docs/index.md",
    REPO_ROOT / "packs/core/JOURNEY.md",
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


def test_core_docs_map_seed_is_shipped() -> None:
    """The scaffold's entry point into its own documentation must exist.

    This replaced a byte-parity assertion between the retired conventions
    document and its seed. `docs/README.md` deliberately diverges — the seed
    carries a placeholder row and the repository's copy names areas no pack
    seeds — so parity is the wrong relation and presence is the right one.
    """
    assert CORE_DOCS_MAP_SEED.is_file()
