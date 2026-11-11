"""The plan's Changelog and `delivery/approvals.jsonl` each hold one half of an approval.

The plan template's Changelog note keeps the human half: one dated entry per gate
with the approver's handle. The supervisor's `start` writes the machine half to
`delivery/approvals.jsonl`. The template names both and says neither replaces the
other; the supervisor side writes only that file and the work-loop reference
names it. Each half is pinned here so removing either one fails a test.
"""

from __future__ import annotations

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
PLAN_TEMPLATE = PACK_ROOT / ".apm" / "skills" / "new-spec" / "assets" / "plan.md"
WORK_LOOP = PACK_ROOT / ".apm" / "skills" / "work-loop"
SUPERVISOR_REFERENCE = WORK_LOOP / "references" / "supervisor.md"
STATE_SCHEMA = WORK_LOOP / "references" / "state-schema.md"
ADMISSION = WORK_LOOP / "scripts" / "_supervisor_admission.py"


def _changelog_note() -> str:
    text = PLAN_TEMPLATE.read_text(encoding="utf-8")
    note = text.split("## Changelog", 1)[1]
    return " ".join(note.split())


HUMAN_HALF = (
    "- YYYY-MM-DD: spec approved by <handle>",
    "- YYYY-MM-DD: plan approved by <handle>",
    "The entry is the human half of the record",
)
MACHINE_HALF = (
    "`start` appends the approval pair to `delivery/approvals.jsonl`",
    "nothing else writes that file",
    "never stands in for that record",
    "that record never stands in for the entry",
)


def _missing(note: str, required: tuple[str, ...]) -> list[str]:
    return [phrase for phrase in required if phrase not in note]


def test_the_changelog_keeps_the_human_half_as_two_dated_entries() -> None:
    assert _missing(_changelog_note(), HUMAN_HALF) == []


def test_the_changelog_names_the_machine_half_and_keeps_the_two_apart() -> None:
    assert _missing(_changelog_note(), MACHINE_HALF) == []


def test_the_supervisor_side_of_the_split_is_real() -> None:
    reference = " ".join(SUPERVISOR_REFERENCE.read_text(encoding="utf-8").split())
    assert "appends the approval pair in one commit" in reference
    schema = STATE_SCHEMA.read_text(encoding="utf-8")
    assert "delivery/approvals.jsonl" in schema
    assert re.search(r"approvals\.jsonl", ADMISSION.read_text(encoding="utf-8"))


def test_the_split_check_fails_when_either_half_is_removed() -> None:
    note = _changelog_note()
    no_machine = note.replace("`delivery/approvals.jsonl`", "the approvals record")
    assert _missing(no_machine, MACHINE_HALF)
    no_human = note.replace("- YYYY-MM-DD: plan approved by <handle>", "")
    assert _missing(no_human, HUMAN_HALF)
