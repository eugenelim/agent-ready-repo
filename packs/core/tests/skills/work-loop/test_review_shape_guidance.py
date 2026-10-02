"""Contract tests for work-loop review-shape guidance."""

import json
from pathlib import Path

PACK_ROOT = Path(__file__).parents[3]
WORK_LOOP = PACK_ROOT / ".apm/skills/work-loop/SKILL.md"
EVALS = PACK_ROOT / ".apm/skills/work-loop/evals/evals.json"


def test_declined_additions_are_material_and_architectural() -> None:
    """Routine alternatives must not create a mandatory declination register."""
    body = WORK_LOOP.read_text(encoding="utf-8")

    assert (
        "record a declined architectural addition only when it materially affects "
        "scope or design"
    ) in body
    assert "name what you were tempted to add and declined" not in body
    assert (
        "an empty register is valid when no declined architectural addition "
        "materially affected scope or design"
    ) in body


def test_review_shape_uses_independent_proof_before_the_size_heuristic() -> None:
    """Reviewability is primary and size remains advisory."""
    body = WORK_LOOP.read_text(encoding="utf-8")

    assert "can this unit be independently" in body
    assert "understood, verified, or reviewed?" in body
    assert "transformation/reproducibility proof" in body
    assert "2,000 reviewable behavior and test lines is a heuristic" in body


def test_review_shape_and_declination_evals_ship_with_the_skill() -> None:
    """The changed decisions remain represented in the skill eval harness."""
    entries = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
    ids = {entry["id"] for entry in entries}

    assert "declined-additions-record-only-material-architecture" in ids
    assert "review-shape-uses-independence-before-size" in ids
