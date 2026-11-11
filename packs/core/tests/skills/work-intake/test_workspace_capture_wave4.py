"""Wave 4 terse workspace-capture contracts for work-intake."""

from __future__ import annotations

import json
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm/skills/work-intake/SKILL.md"
EVALS = PACK_ROOT / ".apm/skills/work-intake/evals/evals.json"


def _text() -> str:
    return " ".join(SKILL.read_text(encoding="utf-8").split())


def test_capture_keeps_artifacts_terse_and_registers_nothing() -> None:
    text = _text()

    assert "Capture without a registry" in text
    assert "nothing is registered" in text
    assert "`Depends on:` header" in text
    for forbidden in (
        "chronology",
        "rationale",
        "procedure",
        "review transcript",
        "raw finding",
        "copied source text",
    ):
        assert forbidden in text
    assert "Terse workspace capture" not in text


def test_follow_on_capture_materializes_owner_artifact() -> None:
    text = _text()

    assert "separated follow-on" in text
    assert "materialize the follow-on's owning artifact." in text
    assert "current state changes in that artifact" in text


def test_work_intake_evals_reject_workspace_narration() -> None:
    evals = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
    by_id = {case["id"]: case for case in evals}

    case = by_id[30]
    assert "canonical artifact first" in case["expected_output"]
    assert "registers no `workspace.toml` entry" in case["expected_output"]
    assert "`Depends on:` header" in case["expected_output"]
    assert "no narrative comments" in case["expected_output"]
