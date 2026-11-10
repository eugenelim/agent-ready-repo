"""Absence pin: the work-loop skill requests no capture at its approval gates.

The G-plan step runs the parked `spec-approved` and `plan-approved` approvals and
then `start`. It asks for no `project-knowledge` capture around them, and the
project-knowledge integration subsection holds only the two enquiries. The
parked approval gate named `spec-approved` stays; only a capture step naming it,
or the removed `plan-locked` gate, fails here.
"""

from __future__ import annotations

import re

from knowledge_test_support import PACK_ROOT

SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
REMOVED_GATES = ("spec-approved", "plan-locked")


def _text() -> str:
    return SKILL.read_text(encoding="utf-8")


def _step_12() -> str:
    """The G-plan step, up to its project-knowledge subsection."""
    text = _text()
    start = text.index("12. **Full mode:** the **G-plan sequence**")
    return text[start : text.index("### Project-knowledge integration", start)]


def _integration() -> str:
    return _text().split("### Project-knowledge integration", 1)[1].split("For durable work", 1)[0]


def _sub_steps(step: str) -> list[str]:
    return re.split(r"\n    \d\. ", step)[1:]


def test_the_g_plan_steps_are_park_then_start_with_no_capture_request() -> None:
    items = _sub_steps(_step_12())
    assert len(items) == 2
    assert items[0].startswith("Park each gate")
    assert "work-supervisor.py' start" in items[1]
    assert not any(re.match(r"Request the `[a-z-]+` capture", item) for item in items)


def test_no_capture_step_names_a_removed_gate() -> None:
    assert "plan-locked" not in _text()
    assert not re.search(r"--semantic-gate[ =](spec-approved|plan-locked)", _text())
    assert not re.search(r"(?i)\bcapture\b[^\n]*`(spec-approved|plan-locked)`", _text())
    assert not re.search(r"(?i)`(spec-approved|plan-locked)`[^\n]*\bcapture\b", _step_12())


def test_the_integration_subsection_holds_only_the_two_enquiries() -> None:
    section = _integration()
    bullets = [line for line in section.splitlines() if line.startswith("    - ")]
    assert len(bullets) == 2
    assert "`CQ-CHANGE`" in bullets[0] and "`CQ-VERIFY`" in bullets[1]
    assert not any(gate in section for gate in REMOVED_GATES)
    assert "project-knowledge unavailable" in section
