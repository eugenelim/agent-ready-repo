"""§ Next-actions picks nothing by its position in a registry list.

Verification mode: goal-based check. The skill is prose with no executable
path, so these tests read the source `SKILL.md` and pin what its Next-actions
section must and must not say.
"""
from __future__ import annotations

from pathlib import Path

_SKILL = Path(__file__).resolve().parents[3] / ".apm/skills/workspace-status/SKILL.md"


def _text() -> str:
    return _SKILL.read_text(encoding="utf-8")


def _next_actions() -> str:
    """Return the section from `### Next-actions` up to the next `## ` line."""
    lines = _text().splitlines()
    start = lines.index("### Next-actions")
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def test_ac0001_no_first_in_list_suggestions() -> None:
    """AC-0001: neither suggestion nor either of their choices remains."""
    assert "next_queue" not in _text()
    assert "next_shape" not in _text()
    section = _next_actions()
    assert "Next queue item" not in section
    assert "First shaping item" not in section


def test_ac0002_one_choice_per_active_spec() -> None:
    """AC-0002: the active-spec choice covers every active spec, picking none."""
    section = _next_actions()
    assert any(
        "for each entry in" in line and "dispatch.py" in line and "`active` list" in line
        for line in section.splitlines()
    )
    assert "first entry in" not in section


def test_ac0003_graph_offer_and_final_choice_remain() -> None:
    """AC-0003: steps 5b to 5d and the final `work-intake` choice stay."""
    section = _next_actions()
    for step in ("**5b.", "**5c.", "**5d."):
        assert step in section
    assert "`work-intake`" in section


def test_start_and_resume_choices_name_dispatch_py() -> None:
    """AC-0025: the start and resume lines name `dispatch.py`, not the status lists."""
    section = _next_actions()
    for label in ("**Start a ready spec:**", "**Active spec:**"):
        line = next(ln for ln in section.splitlines() if label in ln)
        assert "dispatch.py" in line, label
        assert "canonical.ready" not in line and "canonical.active" not in line, label
    assert "first entry in" not in section
