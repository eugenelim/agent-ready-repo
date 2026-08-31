"""Repository-level contract for spec-review adjudication documentation.

`packs/core/tests/` may not reach above its own pack, so the published-guide
half of the `new-spec` adjudication contract lives here. The skill-local half
stays in `packs/core/tests/skills/new-spec/`.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLANNING_GUIDE = REPO_ROOT / "guides/core/how-to/plan-and-execute-non-trivial-work.md"
CORE_EXPLANATION = REPO_ROOT / "guides/core/explanation/core-pack.md"


def flattened(path: Path) -> str:
    """Read a source file while making wrapped prose assertion-stable."""
    return " ".join(path.read_text(encoding="utf-8").split())


def test_planning_guide_explains_spec_review_triage() -> None:
    body = flattened(PLANNING_GUIDE)
    assert (
        "Every completed `adversarial-reviewer` report, including a clean claim, "
        "goes through `finding-adjudicator`"
    ) in body
    assert "Only sustained findings can change the spec or plan" in body
    assert "`draft-origin` or `prior-round-repair`" in body
    assert "unresolved origin stops for your direction" in body
    assert "what that gate proves and one relevant blind spot" in body


def test_core_explanation_places_adjudication_before_repair() -> None:
    body = flattened(CORE_EXPLANATION)
    assert "**`finding-adjudicator`**" in body
    report = "Every completed spec-review report, including a clean claim"
    gateway = "passes through `finding-adjudicator` before it can change the spec or plan"
    assert report in body
    assert gateway in body
    assert body.index(report) < body.index(gateway)
