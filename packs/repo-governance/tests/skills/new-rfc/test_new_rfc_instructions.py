"""Instruction-text pin for new-rfc's route pointer."""

import pathlib

SKILL = pathlib.Path(__file__).resolve().parents[3] / ".apm/skills/new-rfc/SKILL.md"
TEXT = " ".join(SKILL.read_text(encoding="utf-8").split())


def test_when_to_invoke_points_to_route() -> None:
    section = TEXT.split("## When to invoke", 1)[1].split("## ", 1)[0]
    assert "If the route is unclear, run `navigate-decisions route` first." in section
