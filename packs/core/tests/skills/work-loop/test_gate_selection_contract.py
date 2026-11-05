"""Pins for the work-loop gate-selection rule, its reference section and its eval."""

import json
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
_SKILL = _SKILL_DIR / "SKILL.md"
_MODES = _SKILL_DIR / "references" / "verification-modes.md"
_EVALS = _SKILL_DIR / "evals" / "evals.json"
_HEADING = "## Gate selection for a repository change"
_LINK = "references/verification-modes.md#gate-selection-for-a-repository-change"
_FORBIDDEN = ("packs/", ".apm", "make precheck", "self-host")
_EVAL_ID = "plan-task-omits-declared-precheck"


def _flat(text: str) -> str:
    return " ".join(text.split())


def _rule_paragraph() -> str:
    """Return the SKILL.md lines that carry the gate-selection rule."""
    lines = [ln for ln in _SKILL.read_text(encoding="utf-8").splitlines() if _LINK in ln]
    assert lines, "SKILL.md does not link the gate-selection section"
    return _flat(" ".join(lines))


def _section() -> str:
    text = _MODES.read_text(encoding="utf-8")
    assert text.count(_HEADING) == 1
    return text[text.index(_HEADING) :]


def test_ac0001_plan_step_names_declared_check_in_done_when() -> None:
    rule = _rule_paragraph()
    assert "precheck or projection check" in rule
    assert "`Done when:`" in rule


def test_ac0002_section_follows_measurement_and_is_linked() -> None:
    text = _MODES.read_text(encoding="utf-8")
    assert text.index("\n## Measurement\n") < text.index(_HEADING)
    assert _LINK in _SKILL.read_text(encoding="utf-8")


def test_ac0002_section_content() -> None:
    body = _flat(_section())
    assert "Done when:" in body
    assert "none exists" in body
    assert "rewrites files" in body


def test_ac0005_section_names_declaration_places_apart_from_verify_entry() -> None:
    body = _flat(_section())
    assert "verification entry" not in body
    for place in ("agent-guidance files", "build files", "pipeline definitions"):
        assert place in body, place
    assert "not a verify entry" in body


def test_ac0006_section_bars_naming_undeclared_check_and_keeps_task_zero() -> None:
    body = _flat(_section())
    assert "not named as if declared" in body
    assert "task-zero rule for a missing verification mechanism" in body


def test_ac0003_new_texts_are_portable() -> None:
    for text in (_rule_paragraph(), _section()):
        for term in _FORBIDDEN:
            assert term not in text, term


def test_ac0004_eval_case_names_the_omitted_check() -> None:
    cases = json.loads(_EVALS.read_text(encoding="utf-8"))["evals"]
    case = next(c for c in cases if c["id"] == _EVAL_ID)
    assert {"id", "prompt", "expected_output", "assertions"} <= set(case)
    assert "Done when" in case["prompt"]
    assert any("Done when" in a and "precheck" in a for a in case["assertions"])
