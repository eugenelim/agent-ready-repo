#!/usr/bin/env python3
"""Instruction roster for the captured-item-files feature (AC-0040).

AC-0040: in ``work-loop``'s SKILL.md, the paragraph beginning ``Then apply the
**Shaping-item guard**`` names ``captured.items``, ``routes_to``, ``invalid``,
and ``unreadable``, and names neither ``[shaping_queue]`` nor ``[backlog].open``.
Standard library only; the check reads one file and writes nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_WORK_LOOP = _REPO / "packs/core/.apm/skills/work-loop/SKILL.md"
_OPENING = "Then apply the **Shaping-item guard**"

_REQUIRED = ("captured.items", "routes_to", "invalid", "unreadable")
_FORBIDDEN = ("[shaping_queue]", "[backlog].open")


def _guard_paragraph() -> str:
    """The paragraph that begins with the guard's opening phrase."""
    paragraphs = _WORK_LOOP.read_text(encoding="utf-8").split("\n\n")
    matches = [p for p in paragraphs if p.startswith(_OPENING)]
    assert len(matches) == 1, f"expected one paragraph opening {_OPENING!r}"
    return matches[0]


@pytest.mark.parametrize("phrase", _REQUIRED)
def test_guard_paragraph_names_the_captured_item_listing(phrase: str) -> None:
    assert phrase in _guard_paragraph()


@pytest.mark.parametrize("phrase", _FORBIDDEN)
def test_guard_paragraph_names_no_registry_collection(phrase: str) -> None:
    assert phrase not in _guard_paragraph()
