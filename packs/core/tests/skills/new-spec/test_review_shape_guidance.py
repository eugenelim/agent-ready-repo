"""Contract tests for new-spec review-shape guidance."""

import json
from pathlib import Path

PACK_ROOT = Path(__file__).parents[3]
NEW_SPEC = PACK_ROOT / ".apm/skills/new-spec/SKILL.md"
EVALS = PACK_ROOT / ".apm/skills/new-spec/evals/evals.json"


def test_review_shape_uses_independent_proof_before_the_size_heuristic() -> None:
    """Reviewability is primary and size remains advisory."""
    body = NEW_SPEC.read_text(encoding="utf-8")

    assert "can this unit be independently" in body
    assert "understood, verified, or reviewed?" in body
    assert "transformation/reproducibility proof" in body
    assert "2,000 reviewable behavior and test lines is a heuristic" in body


def test_review_shape_eval_ships_with_the_skill() -> None:
    """The changed sizing decision remains represented in the eval harness."""
    entries = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]

    assert any(entry["id"] == "plan-review-unit-uses-shape-before-size" for entry in entries)
