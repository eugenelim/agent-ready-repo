"""`de-risk-intent` authors its own kill condition and dispatches no reviewer."""

from __future__ import annotations

import json
import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILL = PACK_ROOT / ".apm" / "skills" / "de-risk-intent" / "SKILL.md"
EVALS = PACK_ROOT / ".apm" / "skills" / "de-risk-intent" / "evals" / "evals.json"


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def test_de_risk_intent_states_the_no_dispatch_boundary() -> None:
    """The boundary is stated, with the reason it exists.

    A reviewer that emitted a validation hook into this skill would be doing
    the one thing the skill is accountable for, leaving it to mark that
    reviewer's homework instead of taking a verdict.
    """
    body = _flat(SKILL.read_text(encoding="utf-8"))

    assert "This skill never dispatches it." in body
    assert "marking its homework" in body
    assert "input to your own choice, not as the choice" in body


def test_the_boundary_is_stated_once_and_carries_no_dispatch_instruction() -> None:
    """One mention, and the bullet holding it refuses rather than routes.

    An earlier form of this collected only the lines matching the agent name and
    asserted `"never dispatches" in those lines or "Dispatching" in lines[0]`.
    The refusal sits on the line *after* the agent name, so the first disjunct
    was false and the whole assertion rested on the word `Dispatching` -- which
    the sentence "Dispatching `adversarial-reviewer` when the risk is unclear"
    contains just as happily. The test could not fail for the direction its own
    name asserts. It now reads the whole bullet.
    """
    body = SKILL.read_text(encoding="utf-8")
    mentions = [line for line in body.splitlines() if "adversarial-reviewer" in line]
    assert len(mentions) == 1, mentions

    start = body.index(mentions[0])
    following = re.search(r"^- \*\*", body[start + len(mentions[0]) :], re.MULTILINE)
    bullet = _flat(
        body[start : start + len(mentions[0]) + following.start()]
        if following
        else body[start:]
    )

    assert "This skill never dispatches it." in bullet
    for routing in ("dispatch it when", "ask the reviewer to", "have the reviewer"):
        assert routing not in bullet.lower(), routing


def test_the_eval_harness_covers_the_boundary() -> None:
    """A non-cosmetic pack update also updates that pack's eval harness."""
    harness = json.loads(EVALS.read_text(encoding="utf-8"))
    matching = [
        case
        for case in harness["evals"]
        if "adversarial" in json.dumps(case).lower()
    ]
    assert len(matching) == 1, [case["id"] for case in matching]
    assertions = " ".join(matching[0]["assertions"]).lower()
    assert "declines to dispatch" in assertions
    assert "kill condition" in assertions
