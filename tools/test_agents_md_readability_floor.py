"""Regression floor for the two `AGENTS.md` files that carry the inlined clauses.

Neither meets the shipped 70/8 gate, so neither joins it — that branch was
decided by measurement at T4, not in advance. What guards them instead is a
floor pinned to their own measured scores: the files may not get worse.

Reading level is not a bar here. Some work is irreducibly dense once every
avoidable term is gone, and control replies on one tree spanned 49 to 75 purely
by task. A floor catches regression without asserting that prose which is
naturally hard must read easily.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parent
_ROOT = _TOOLS.parent
_SPEC = importlib.util.spec_from_file_location("_score_cognition", _TOOLS / "score-cognition.py")
scorer = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(scorer)

# Measured on the finished files, 2026-09-13, with tools/score-cognition.py.
# Pre-change they were 47.46/8.74 and 44.48/9.46; inlining the clauses raised
# both. A floor pinned to the pre-change figures could never fire.
#
# Re-measured after T2b re-homed three clauses the retired topic file carried:
# the earlier figures were 65.18/6.29 and 62.70/6.82, so both files improved
# again. A floor left at the earlier numbers would still hold, which is exactly
# why it needs re-recording — a stale floor sits below what the file now does
# and stops detecting the first 1.3 points of regression.
BASELINES = {
    "AGENTS.md": (67.27, 6.05),
    "packs/core/seeds/AGENTS.md": (64.86, 6.57),
}
# Sized per unit, not shared: ease runs 0-100 and grade roughly 0-20, so one
# number cannot mean the same thing on both.
EASE_TOLERANCE = 1.0
GRADE_TOLERANCE = 0.2

# A fixed string whose score depends only on the scorer. If prose extraction or
# syllable estimation changes, this reds first and names itself, instead of
# reding on AGENTS.md and blaming the prose.
FIXTURE = (
    "The cat sat on the mat. The dog ran to the park. Birds sang in the trees. "
    "Rain fell on the roof all night. We walked to the shop and back again. "
    "The bread was warm and the tea was hot. She read a book by the fire.\n"
)
FIXTURE_SCORE = (113.51, -0.87)


def test_the_scorer_itself_has_not_drifted() -> None:
    """Reds before the file floors do, so drift never presents as bad prose."""
    result = scorer.score(FIXTURE)
    assert result["ease"] == pytest.approx(FIXTURE_SCORE[0], abs=0.01), result
    assert result["grade"] == pytest.approx(FIXTURE_SCORE[1], abs=0.01), result


@pytest.mark.parametrize("relative", sorted(BASELINES))
def test_agents_md_does_not_read_worse_than_its_recorded_baseline(relative: str) -> None:
    ease_floor, grade_ceiling = BASELINES[relative]
    result = scorer.score((_ROOT / relative).read_text(encoding="utf-8"))
    assert result["ease"] >= ease_floor - EASE_TOLERANCE, (relative, result)
    assert result["grade"] <= grade_ceiling + GRADE_TOLERANCE, (relative, result)


@pytest.mark.parametrize("relative", sorted(BASELINES))
def test_neither_file_meets_the_shipped_gate_so_neither_joins_it(relative: str) -> None:
    """Pins the branch T4 took, so a later edit that clears 70/8 is noticed."""
    result = scorer.score((_ROOT / relative).read_text(encoding="utf-8"))
    assert result["ease"] < 70, (relative, result, "clears 70 -- move it to the 70/8 gate")
