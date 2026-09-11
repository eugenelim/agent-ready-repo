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
    """One mention, and it is the refusal -- not a route into the reviewer."""
    lines = [
        line
        for line in SKILL.read_text(encoding="utf-8").splitlines()
        if "adversarial-reviewer" in line
    ]
    assert len(lines) == 1, lines
    assert "never dispatches" in _flat(" ".join(lines)) or "Dispatching" in lines[0]


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
