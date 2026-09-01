"""The adopter guides name the flag and what a matching id guarantees.

A pack test may not read above its own pack, so the `guides/` assertions live
here rather than beside the work-loop suite.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOW_TO = ROOT / "guides/core/how-to/plan-and-execute-non-trivial-work.md"
EXPLANATION = ROOT / "guides/core/explanation/core-pack.md"


def test_the_how_to_names_the_flag_and_its_guarantee() -> None:
    text = HOW_TO.read_text(encoding="utf-8")
    assert "--operation-id" in text
    assert "no-op" in text or "not written twice" in text or "second round" in text


def test_the_explanation_names_the_flag() -> None:
    assert "--operation-id" in EXPLANATION.read_text(encoding="utf-8")


def test_the_how_to_describes_the_resuming_comparison() -> None:
    assert "last_review_record_operation_id" in HOW_TO.read_text(encoding="utf-8")
