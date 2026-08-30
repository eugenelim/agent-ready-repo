from __future__ import annotations

from pathlib import Path


PACK_ROOT = Path(__file__).resolve().parents[3]
WORK_LOOP_SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
REFERENCES = WORK_LOOP_SKILL.parent / "references"


def _skill_text() -> str:
    return WORK_LOOP_SKILL.read_text(encoding="utf-8")


def test_supervisor_mode_pointer_routes_fan_out_rules() -> None:
    skill = _skill_text()
    assert "[Supervisor and fan-out procedure](references/supervisor-mode.md)" in skill
    reference = (REFERENCES / "supervisor-mode.md").read_text(encoding="utf-8")
    for statement in (
        "single message (one Agent use per target)",
        "Barrier-wait",
        "missing report = `failed`",
        "parallel fan-out",
        "those verbs exit non-zero",
        "wave-complete",
    ):
        assert statement in reference


def test_unattended_loops_pointer_routes_eligibility_rules() -> None:
    skill = _skill_text()
    assert "[Unattended-loop eligibility](references/unattended-loops.md)" in skill
    reference = (REFERENCES / "unattended-loops.md").read_text(encoding="utf-8")
    for statement in (
        "fully mechanical",
        "single-context-window items",
        "verification is reliable",
        "in-session loop at least once",
        "sensitive surface",
        "hard caps",
        "review every commit after",
    ):
        assert statement in reference
