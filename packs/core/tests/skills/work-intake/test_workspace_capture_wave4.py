"""Wave 4 terse workspace-capture contracts for work-intake."""

from __future__ import annotations

import json
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm/skills/work-intake/SKILL.md"
EVALS = PACK_ROOT / ".apm/skills/work-intake/evals/evals.json"


def _text() -> str:
    return " ".join(SKILL.read_text(encoding="utf-8").split())


def test_workspace_entries_remain_terse_live_indexes() -> None:
    text = _text()

    assert "Terse workspace capture" in text
    assert "canonical artifact first" in text
    assert "one short present-tense summary" in text
    assert "hard dependencies only" in text
    assert "minimal provenance" in text
    for forbidden in (
        "chronology",
        "rationale",
        "procedure",
        "review transcript",
        "raw finding",
        "copied source text",
    ):
        assert forbidden in text
    assert "`workspace.toml` is the pointer, not the overflow store" in text


def test_follow_on_capture_materializes_owner_before_registration() -> None:
    text = _text()

    assert "separated follow-on" in text
    assert "materialize the follow-on's owning artifact before registration" in text
    assert "Do not leave an open AC behind as the workspace anchor" in text
    assert "current state changes in that artifact" in text


def test_work_intake_evals_reject_workspace_narration() -> None:
    evals = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
    by_id = {case["id"]: case for case in evals}

    case = by_id[30]
    assert "canonical artifact first" in case["expected_output"]
    assert "one short current/next summary" in case["expected_output"]
    assert "hard dependencies" in case["expected_output"]
    assert "no narrative comments" in case["expected_output"]
