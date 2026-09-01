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
    # A structurally clean report skips adjudication, and the guide has to say so
    # in the same breath as the rule it excepts — a reader who sees only one half
    # acts on the wrong contract. Asserted as adjacency, not mere presence:
    # relocating the exception into a footnote would leave a presence-only check
    # green while breaking exactly that property. The exception is no longer
    # byte-exactness alone; a coverage-disclosure footer always adjudicates.
    exception = (
        "A report that is clean — by exact bytes, or by structure with nothing "
        "but blank lines around the clean sentence — closes the round without an "
        "adjudicator call"
    )
    rule = (
        "A report carrying findings, or `security-reviewer`'s "
        "coverage-disclosure footer, goes through `finding-adjudicator`"
    )
    assert exception in body
    assert rule in body
    gap = body.index(rule) - (body.index(exception) + len(exception))
    assert 0 <= gap <= 40, gap
    assert "Review iterates to direct or adjudicated clean" in body
    assert "Only sustained findings can change the spec or plan" in body
    assert "`draft-origin` or `prior-round-repair`" in body
    assert "unresolved origin stops for your direction" in body
    assert "what that gate proves and one relevant blind spot" in body


def test_core_explanation_places_adjudication_before_repair() -> None:
    body = flattened(CORE_EXPLANATION)
    assert "**`finding-adjudicator`**" in body
    fast_path = "A structurally clean spec-review report closes review mechanically"
    report = "every other completed spec-review report"
    gateway = "passes through `finding-adjudicator` before it can change the spec or plan"
    assert fast_path in body
    assert report in body
    assert gateway in body
    assert body.index(fast_path) < body.index(report) < body.index(gateway)
