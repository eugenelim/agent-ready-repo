"""`intent`'s de-risk mode authors its own kill condition and dispatches no reviewer."""

from __future__ import annotations

import json
import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
INTENT_EVALS = PACK_ROOT / ".apm" / "skills" / "intent" / "evals" / "evals.json"
MODE = PACK_ROOT / ".apm" / "skills" / "intent" / "references" / "de-risk.md"


def _flat(text: str) -> str:
    """Collapse presentation-only whitespace."""
    return re.sub(r"\s+", " ", text)


def test_the_eval_harness_covers_the_boundary() -> None:
    """A non-cosmetic pack update also updates that pack's eval harness."""
    harness = json.loads(INTENT_EVALS.read_text(encoding="utf-8"))
    matching = [
        case
        for case in harness["evals"]
        if "adversarial" in json.dumps(case).lower()
    ]
    assert len(matching) == 1, [case["id"] for case in matching]
    assertions = " ".join(matching[0]["assertions"]).lower()
    assert "declines to dispatch" in assertions
    assert "kill condition" in assertions


def test_de_risk_mode_states_the_no_dispatch_boundary() -> None:
    """The boundary is rescoped from the skill to the mode, reason intact."""
    body = _flat(MODE.read_text(encoding="utf-8"))

    assert "The de-risk mode never dispatches `adversarial-reviewer`." in body
    assert "This skill never dispatches it." not in body
    assert "marking its homework" in body
    assert "input to your own choice, not as the choice" in body


def test_the_mode_boundary_is_stated_once_and_carries_no_dispatch_instruction() -> None:
    """One mention in the anti-pattern bullet, which refuses rather than routes.

    The slice is the whole bullet, not the lines naming the agent. An earlier
    form collected only those lines and asserted `"never dispatches" in those
    lines or "Dispatching" in lines[0]`. The refusal sat on the line after the
    agent name, so the first disjunct was false and the assertion rested on the
    word `Dispatching`, which "Dispatching `adversarial-reviewer` when the risk
    is unclear" contains just as happily. That test could not fail for the
    direction its name asserts.
    """
    body = MODE.read_text(encoding="utf-8")
    mentions = [line for line in body.splitlines() if "adversarial-reviewer" in line]
    assert len(mentions) == 2, mentions  # the bullet's lead, then the refusal

    start = body.index(mentions[0])
    following = re.search(r"^- \*\*", body[start + len(mentions[0]) :], re.MULTILINE)
    bullet = _flat(
        body[start : start + len(mentions[0]) + following.start()]
        if following
        else body[start:]
    )

    assert "The de-risk mode never dispatches `adversarial-reviewer`." in bullet
    for routing in ("dispatch it when", "ask the reviewer to", "have the reviewer"):
        assert routing not in bullet.lower(), routing
